import logging
from flask import Blueprint, request

from app.services.user_CRUD_service import user_service
from app.core.security import verify_password, create_access_token
from app.core.error_handlers import handle_api_exceptions, success_response
from app.core.exceptions import BadRequestException, UnauthorizedException, NotFoundException


logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@auth_bp.route("/register", methods=["POST"])
@handle_api_exceptions
def register_user():
    """
    Endpoint to register a new user in the system.
    Expects a JSON payload with user details including 'email' and 'hash_password' (raw text here).
    
    Returns:
        JSON response with the new user ID and status 201 on success.
        JSON response with an error message and status 400 on failure.
    """
    payload = request.get_json()

    if not payload:
        raise BadRequestException(
            message="Invalid or missing JSON payload",
            error_code="EMPTY_BODY"
        )

    if "email" not in payload or "hash_password" not in payload:
        raise BadRequestException(
            message="Fields 'email' and 'hash_password' are required",
            error_code="MISSING_REQUIRED_FIELDS"
        )

    user_id = user_service.create_user(payload)

    logger.info(f"New user registered successfully via API. ID: {user_id}")

    return success_response(
        data={"user_id": user_id},
        status_code=201,
        message="User registered successfully"
    )
    
    
    
@auth_bp.route('/login', methods=['POST'])
@handle_api_exceptions
def login_user():
    """
    Endpoint to authenticate a user and generate a JWT access token.
    Expects a JSON payload with 'email' and 'password'.
    
    Returns:
        JSON response containing the JWT access token and status 200 on success.
        JSON response with an error message and status 401 on unauthorized access.
    """
    payload = request.get_json()

    if not payload:
        raise BadRequestException(
            message="Invalid or missing JSON payload",
            error_code="EMPTY_BODY"
        )

    email = payload.get("email")
    password = payload.get("password")

    if not email or not password:
        raise BadRequestException(
            message="Missing email or password",
            error_code="MISSING_CREDENTIALS"
        )

    try:
        user_document = user_service.get_user_by_email(email)
    except NotFoundException:
        logger.warning(f"Failed login attempt: User not found for email {email}")
        raise UnauthorizedException(
            message="Invalid credentials",
            error_code="INVALID_CREDENTIALS"
        )

    stored_hash = user_document.get("hash_password")

    if not verify_password(password, stored_hash):
        logger.warning(f"Failed login attempt: Incorrect password for email {email}")
        raise UnauthorizedException(
            message="Invalid credentials",
            error_code="INVALID_CREDENTIALS"
        )

    user_id_str = str(user_document.get("_id"))
    access_token = create_access_token(subject=user_id_str)

    logger.info(f"User authenticated successfully via API. ID: {user_id_str}")

    return success_response(
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user_id_str
        },
        status_code=200,
        message="Login successful"
    )
    
    
