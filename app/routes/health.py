
import logging
from flask import Blueprint

from app.core.database import db_instance
from app.core.error_handlers import handle_api_exceptions, success_response

"""
Flask Blueprint for Health Check and Status Endpoints

Provides endpoints for application health monitoring:
- GET /api/v1/health - Application health status
- GET /api/v1/health/db - Database connection status
- GET /api/v1/version - API version information
"""

logger = logging.getLogger(__name__)

health_bp = Blueprint(
    'health',
    __name__,
    url_prefix='/api/v1'
)


@health_bp.route('/health', methods=['GET'])
@handle_api_exceptions
def health_check():
    """
    Basic health check endpoint.
    
    Returns:
        200 OK:
            {
                "status": "success",
                "status_code": 200,
                "message": "Service is healthy",
                "data": {
                    "status": "healthy",
                    "service": "FractoRust-AI Backend",
                    "version": "1.0.0"
                }
            }
    """
    return success_response(
        data={
            "status": "healthy",
            "service": "FractoRust-AI Backend",
            "version": "1.0.0"
        },
        status_code=200,
        message="Service is healthy"
    )


@health_bp.route('/health/db', methods=['GET'])
@handle_api_exceptions
def database_health():
    """
    Check database connection status.
    
    Returns:
        200 OK if database is connected:
            {
                "status": "success",
                "status_code": 200,
                "message": "Database connection is healthy",
                "data": {
                    "database": "connected"
                }
            }
        
        500 Internal Server Error if database is unavailable:
            {
                "status": "error",
                "status_code": 500,
                "error_code": "DATABASE_ERROR",
                "message": "Database connection failed",
                "details": {}
            }
    """
    try:
        # Simple ping to check database
        db_instance.db.command('ping')
        
        return success_response(
            data={"database": "connected"},
            status_code=200,
            message="Database connection is healthy"
        )
    
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        
        return success_response(
            data={"database": "disconnected"},
            status_code=500,
            message="Database connection failed"
        )


@health_bp.route('/version', methods=['GET'])
@handle_api_exceptions
def get_version():
    """
    Get API version information.
    
    Returns:
        200 OK:
            {
                "status": "success",
                "status_code": 200,
                "message": "Version information retrieved successfully",
                "data": {
                    "api_version": "1.0.0",
                    "python_version": "3.11+",
                    "framework": "Flask 3.0+",
                    "release_date": "2026-04-23"
                }
            }
    """
    return success_response(
        data={
            "api_version": "1.0.0",
            "python_version": "3.11+",
            "framework": "Flask 3.0+",
            "release_date": "2026-04-23"
        },
        status_code=200,
        message="Version information retrieved successfully"
    )
