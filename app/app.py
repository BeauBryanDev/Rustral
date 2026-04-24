import os
import sys
import logging
from typing import Optional, Dict, Any
from flask import Flask, jsonify, request
from flask_cors import CORS

from app.config import Config
from app.core.logging import setup_logging
from app.core.database import db_instance
from app.core.error_handlers import handle_api_exceptions
from app.core.exceptions import APIException

# Import Blueprints
from app.routes.auth import auth_bp
from app.routes.detections import detections_bp
from app.routes.users import users_bp
from app.routes.images import images_bp
from app.routes.analytics import analytics_bp
from app.routes.health import health_bp
from app.routes.locations import locations_bp

def _validate_required_config(config: Dict[str, Any], logger: logging.Logger) -> None:
    """
    Validate that all required configuration values are set.
    
    Args:
        config: Flask config object
        logger: Logger instance
        
    Raises:
        ValueError: If critical config values are missing
    """
    required_keys = [
        "SECRET_KEY",
        "JWT_SECRET_KEY",
        "MONGODB_URI",
        "MONGODB_DB",
    ]
    
    missing_keys = [key for key in required_keys if not config.get(key)]
    
    if missing_keys:
        
        logger.error(f"Missing required configuration: {', '.join(missing_keys)}")
        raise ValueError(f"Missing required environment variables: {', '.join(missing_keys)}")


def _register_blueprints(app: Flask, logger: logging.Logger) -> None:
    """
    Register all API blueprints with the Flask app.
    
    Args:
        app: Flask application instance
        logger: Logger instance
    """
    blueprints = [
        ("Auth", auth_bp),
        ("Detections", detections_bp),
        ("Users", users_bp),
        ("Images", images_bp),
        ("Analytics", analytics_bp),
        ("Health", health_bp),
        ("Locations", locations_bp),
    ]
    
    for name, blueprint in blueprints:
        
        app.register_blueprint(blueprint)
        logger.info(f"✓ {name} blueprint registered")
    
    logger.info("All blueprints registered successfully")


def _register_error_handlers(app: Flask, logger: logging.Logger) -> None:
    """
    Register global error handlers for the Flask app.
    Uses the APIException structure for consistent error responses.
    
    Args:
        app: Flask application instance
        logger: Logger instance
    """
    
    @app.errorhandler(APIException)
    def handle_custom_api_exception(error):
        """Handle custom API exceptions with structured response."""
        logger.warning(f"{error.error_code}: {error.message}")
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(404)
    def resource_not_found(error):
        """Handle 404 Not Found errors."""
        return jsonify({
            "status": "error",
            "status_code": 404,
            "error_code": "RESOURCE_NOT_FOUND",
            "message": "The requested resource was not found",
            "details": {"path": request.path}
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 Method Not Allowed errors."""
        return jsonify({
            "status": "error",
            "status_code": 405,
            "error_code": "METHOD_NOT_ALLOWED",
            "message": f"The {request.method} method is not allowed for this resource",
            "details": {"path": request.path, "method": request.method}
        }), 405

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors."""
        logger.error(f"Internal server error: {error}", exc_info=True)
        return jsonify({
            "status": "error",
            "status_code": 500,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred on the server",
            "details": {}
        }), 500

    logger.info("✓ Global error handlers registered")


def _setup_request_logging(app: Flask, logger: logging.Logger) -> None:
    """
    Setup request/response logging middleware.
    
    Args:
        app: Flask application instance
        logger: Logger instance
    """
    
    @app.before_request
    def log_request():
        """Log incoming requests."""
        logger.debug(f"{request.method} {request.path} - IP: {request.remote_addr}")

    @app.after_request
    def log_response(response):
        """Log outgoing responses."""
        logger.debug(f"{response.status_code} {request.method} {request.path}")
        return response

    logger.info("✓ Request logging middleware configured")


def create_app(test_config: Optional[Dict[str, Any]] = None) -> Flask:
    """
    Application Factory pattern for the Flask backend.
    
    Initializes configurations, logging, database connections, 
    registers blueprints, and configures error handling.
    
    Args:
        test_config (dict, optional): Configuration dictionary for testing environments.
        
    Returns:
        Flask: The fully initialized Flask application instance.
        
    Raises:
        ValueError: If required configuration values are missing.
    """
    #  Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Initializing FractoRust-AI Backend Application")
    logger.info("=" * 60)

    #  Create Flask app instance
    app = Flask(__name__)
    
    #  Load configuration
    if test_config is None:
        app.config.from_object(Config)
    else:
        app.config.update(test_config)
    
    #  Validate required configuration
    try:
        _validate_required_config(app.config, logger)
        
        logger.info("✓ Configuration validation passed")
        
    except ValueError as e:
        
        logger.critical(str(e))
        
        sys.exit(1)

    # Setup CORS for ReactJS frontend integration
    # In production, restrict to specific origins
    cors_origins = app.config.get("CORS_ORIGINS", "*")
    CORS(app, resources={r"/api/*": {"origins": cors_origins}})
    logger.info(f"✓ CORS configured for origins: {cors_origins}")
    
    #  Verify database connection
    try:
        _ = db_instance.db
        logger.info("✓ Database instance verified")
        
    except Exception as error:
        
        logger.critical(f"Failed to verify database connection: {error}")
        
        sys.exit(1)

    #  Register blueprints
    _register_blueprints(app, logger)

    #  Register error handlers
    _register_error_handlers(app, logger)
    
    #  Setup request/response logging
    _setup_request_logging(app, logger)
    
    @app.errorhandler(404)
    def resource_not_found(error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500

    logger.info("=" * 60)
    logger.info("Application initialization completed successfully")
    logger.info("=" * 60)

    return app

# Development Server Execution
if __name__ == "__main__":
    # This block only executes if the script is run directly (e.g., python app.py)
    # It will not execute when running via Gunicorn in production
    
    fractal_app = create_app()
    
    # Extract port from environment or default to 5000
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")
    
    # Start the built-in Werkzeug development server
    fractal_app.run(host=host, port=port, debug=True)