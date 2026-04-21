import logging
from functools import wraps
from flask import request, jsonify, g

from app.core.security import decode_access_token


logger = logging.getLogger(__name__)

def jwt_required(func):
    """
    Decorator to protect Flask endpoints with JWT authentication.
    Validates the 'Authorization: Bearer <token>' header.
    If valid, injects the user ID into Flask's 'g' context object.
    
    Args:
        func: The Flask route function to be decorated.
        
    Returns:
        The decorated function if authentication succeeds, 
        or a 401 Unauthorized JSON response if it fails.
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            
            logger.warning("Authentication failed: Missing Authorization header.")
            
            return jsonify({"error": "Authorization token is missing"}), 401
            
        parts = auth_header.split()
        
        if len(parts) != 2 or parts[0].lower() != "bearer":
            
            logger.warning("Authentication failed: Invalid header format. Expected 'Bearer <token>'.")
            
            return jsonify({"error": "Invalid token format"}), 401
            
        token = parts[1]
        
        decoded_payload = decode_access_token(token)
        
        if not decoded_payload:
            
            logger.warning("Authentication failed: Invalid or expired JWT token.")
            
            return jsonify({"error": "Invalid or expired token"}), 401
            
        # Safely store the extracted user ID for the duration of the request
        g.user_id = decoded_payload.get("sub")
        
        return func(*args, **kwargs)
        
        
    return decorated_function

