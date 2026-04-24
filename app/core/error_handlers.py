
import logging
from functools import wraps
from datetime import date, datetime
from flask import jsonify
from werkzeug.exceptions import HTTPException
from bson import ObjectId

from app.core.exceptions import APIException


logger = logging.getLogger(__name__)


def _json_safe(value):
    """
    Recursively convert common MongoDB / datetime values into JSON-safe types.
    """
    if isinstance(value, ObjectId):
        return str(value)

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]

    return value


def handle_api_exceptions(f):
    """
    Decorator to catch APIException and HTTPException and return proper JSON responses.
    
    Usage:
        @app.route('/api/v1/images/<image_id>')
        @handle_api_exceptions
        def get_image(image_id):
            image = image_service.get_image_by_id(image_id)
            return jsonify(image), 200
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        
        except APIException as e:
            # Custom API exception - return structured error response
            logger.warning(f"{e.error_code}: {e.message}")
            return jsonify(e.to_dict()), e.status_code
        
        except HTTPException as e:
            # Flask/Werkzeug HTTP exception
            logger.warning(f"HTTP Exception {e.code}: {e.description}")
            return jsonify({
                "status": "error",
                "status_code": e.code,
                "error_code": "HTTP_ERROR",
                "message": e.description or "An error occurred",
                "details": {}
            }), e.code
        
        except Exception as e:
            # Unexpected error - don't expose details in production
            logger.error(f"Unexpected error: {type(e).__name__}: {str(e)}", exc_info=True)
            return jsonify({
                "status": "error",
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {}
            }), 500
    
    return decorated_function


def error_response(status_code: int, error_code: str, message: str, details: dict = None):
    """
    Helper function to create a consistent error response.
    
    Args:
        status_code: HTTP status code
        error_code: Machine-readable error identifier
        message: User-friendly error message
        details: Additional error context
    
    Returns:
        Tuple of (Flask response, status code)
    
    Usage:
        if not user:
            return error_response(404, "USER_NOT_FOUND", "User not found", {"user_id": user_id})
    """
    return jsonify(_json_safe({
        "status": "error",
        "status_code": status_code,
        "error_code": error_code,
        "message": message,
        "details": details or {}
    })), status_code


def success_response(data: dict = None, status_code: int = 200, message: str = "Success"):
    """
    Helper function to create a consistent success response.
    
    Args:
        data: Response payload
        status_code: HTTP status code (usually 200, 201)
        message: Status message
    
    Returns:
        Tuple of (Flask response, status code)
    
    Usage:
        image = image_service.get_image_by_id(image_id)
        return success_response(image, 200, "Image retrieved successfully")
    """
    return jsonify(_json_safe({
        "status": "success",
        "status_code": status_code,
        "message": message,
        "data": data or {}
    })), status_code
