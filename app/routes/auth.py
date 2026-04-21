import logging
from flask import Blueprint, request, jsonify

from app.services.user_CRUD_service import user_service
from app.core.security import verify_password, create_access_token


logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@auth_bp.route("/register", methods=["POST"])
def register_user():
    """
    Endpoint to register a new user in the system.
    Expects a JSON payload with user details including 'email' and 'hash_password' (raw text here).
    
    Returns:
        JSON response with the new user ID and status 201 on success.
        JSON response with an error message and status 400 on failure.
    """
    try:
        payload = request.get_json()
        
        if not payload:
            
            return jsonify({"error": "Invalid or missing JSON payload"}), 400

        # Required fields validation
        if "email" not in payload or "hash_password" not in payload:
            
            return jsonify({"error": "Fields 'email' and 'hash_password' are required"}), 400

        # The service handles password hashing and duplicate email checks
        user_id = user_service.create_user(payload)
        
        if not user_id:
            
            return jsonify({"error": "Registration failed. Email might already exist."}), 400

        logger.info(f"New user registered successfully via API. ID: {user_id}")
        
        return jsonify({
            "message": "User registered successfully",
            "user_id": user_id
        }), 201

    except Exception as error:
        
        logger.error(f"Unexpected error during registration: {error}")
        
        return jsonify({"error": "Internal server error"}), 500
    
    
    
@auth_bp.route('/login', methods=['POST'])
def login_user():
    """
    Endpoint to authenticate a user and generate a JWT access token.
    Expects a JSON payload with 'email' and 'password'.
    
    Returns:
        JSON response containing the JWT access token and status 200 on success.
        JSON response with an error message and status 401 on unauthorized access.
    """
    try:
        
        payload = request.get_json()
        
        if not payload:
            
            return jsonify({"error": "Invalid or missing JSON payload"}), 400

        email = payload.get("email")
        password = payload.get("password")

        if not email or not password:
            
            return jsonify({"error": "Missing email or password"}), 400

        # Retrieve user document from the database
        user_document = user_service.get_user_by_email(email)
        
        if not user_document:
            
            logger.warning(f"Failed login attempt: User not found for email {email}")
            
            return jsonify({"error": "Invalid credentials"}), 401

        # Verify the provided password against the stored bcrypt hash
        stored_hash = user_document.get("hash_password")
        
        if not verify_password(password, stored_hash):
            
            logger.warning(f"Failed login attempt: Incorrect password for email {email}")
            
            return jsonify({"error": "Invalid credentials"}), 401

        # Generate the JWT token using the string representation of the user's ObjectId
        user_id_str = str(user_document.get("_id"))
        access_token = create_access_token(subject=user_id_str)

        logger.info(f"User authenticated successfully via API. ID: {user_id_str}")
        
        return jsonify({
            
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user_id_str
        }), 200

    except Exception as error:
        
        logger.error(f"Unexpected error during login: {error}")
        
        return jsonify({"error": "Internal server error"}), 500
    
    