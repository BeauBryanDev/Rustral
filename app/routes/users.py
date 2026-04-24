
import logging
from flask import Blueprint, request

from app.core.error_handlers import handle_api_exceptions, success_response
from app.services.user_CRUD_service import user_service


logger = logging.getLogger(__name__)


# Create Blueprint with URL prefix for all user routes
users_bp = Blueprint(
    'users',
    __name__,
    url_prefix='/api/v1/users'
)
"""
Flask Blueprint for User Management Routes

Provides RESTful endpoints for all user CRUD operations:
- POST /api/v1/users - Create a new user
- GET /api/v1/users/<user_id> - Retrieve a user by ID
- GET /api/v1/users/email/<email> - Retrieve a user by email
- PUT /api/v1/users/<user_id> - Full user update (PUT)
- PATCH /api/v1/users/<user_id> - Partial user update (PATCH)
- DELETE /api/v1/users/<user_id> - Delete a user

All endpoints use proper HTTP status codes and structured error responses.
"""

@users_bp.route('/', methods=['POST'])
@handle_api_exceptions
def create_user():
    """
    Create a new user account.
    
    Request Body (JSON):
        {
            "email": "user@example.com",
            "hash_password": "SecurePassword123",
            "full_name": "John Doe",
            "role": "user"  # optional, defaults to "user"
        }
    
    Returns:
        201 Created:
            {
                "status": "success",
                "status_code": 201,
                "message": "User created successfully",
                "data": {
                    "user_id": "507f1f77bcf86cd799439011"
                }
            }
    
    Raises:
        400 Bad Request: If email or password is missing
        409 Conflict: If email already exists
        500 Internal Server Error: Database errors
    """
    data = request.get_json()
    
    if not data:
        from app.core.exceptions import BadRequestException
        raise BadRequestException(
            message="Request body cannot be empty",
            error_code="EMPTY_BODY"
        )
    
    # Create the user and get the ID
    user_id = user_service.create_user(data)
    
    return success_response(
        data={"user_id": user_id},
        status_code=201,
        message="User created successfully"
    )


@users_bp.route('/<user_id>', methods=['GET'])
@handle_api_exceptions
def get_user(user_id):
    """
    Retrieve a user by their unique ID.
    
    URL Parameters:
        user_id (str): MongoDB ObjectId of the user
    
    Returns:
        200 OK:
            {
                "status": "success",
                "status_code": 200,
                "message": "User retrieved successfully",
                "data": {
                    "_id": "507f1f77bcf86cd799439011",
                    "email": "user@example.com",
                    "full_name": "John Doe",
                    "role": "user",
                    "created_at": "2026-04-23T10:30:00",
                    "updated_at": "2026-04-23T10:30:00"
                }
            }
    
    Raises:
        400 Bad Request: If user_id is not a valid ObjectId
        404 Not Found: If user does not exist
        500 Internal Server Error: Database errors
    """
    user = user_service.get_user_by_id(user_id)
    
    return success_response(
        data=user,
        status_code=200,
        message="User retrieved successfully"
    )


@users_bp.route('/email/<email>', methods=['GET'])
@handle_api_exceptions
def get_user_by_email(email):
    """
    Retrieve a user by their email address.
    
    URL Parameters:
        email (str): User's email address
    
    Returns:
        200 OK:
            {
                "status": "success",
                "status_code": 200,
                "message": "User retrieved successfully",
                "data": {
                    "_id": "507f1f77bcf86cd799439011",
                    "email": "user@example.com",
                    "full_name": "John Doe",
                    "role": "user",
                    "created_at": "2026-04-23T10:30:00",
                    "updated_at": "2026-04-23T10:30:00"
                }
            }
    
    Raises:
        400 Bad Request: If email is not provided
        404 Not Found: If user does not exist
        500 Internal Server Error: Database errors
    """
    user = user_service.get_user_by_email(email)
    
    return success_response(
        data=user,
        status_code=200,
        message="User retrieved successfully"
    )


@users_bp.route('/<user_id>', methods=['PUT'])
@handle_api_exceptions
def update_user_put(user_id):
    """
    Perform a full replacement update (PUT) on a user.
    
    URL Parameters:
        user_id (str): MongoDB ObjectId of the user
    
    Request Body (JSON):
        {
            "full_name": "Jane Doe",
            "hash_password": "NewPassword456",  # optional
            "role": "admin"  # optional
            # 'email' field is immutable and will be ignored if provided
        }
    
    Returns:
        200 OK:
            {
                "status": "success",
                "status_code": 200,
                "message": "User updated successfully",
                "data": {}
            }
    
    Raises:
        400 Bad Request: If user_id is invalid or no valid fields provided
        404 Not Found: If user does not exist
        500 Internal Server Error: Database errors
    
    Important Notes:
        - The 'email' field is immutable and cannot be changed
        - Password will be automatically hashed
        - 'updated_at' is automatically set to current time
    """
    data = request.get_json()
    
    if not data:
        from app.core.exceptions import BadRequestException
        raise BadRequestException(
            message="Request body cannot be empty",
            error_code="EMPTY_BODY"
        )
    
    user_service.update_user_put(user_id, data)
    
    return success_response(
        data={},
        status_code=200,
        message="User updated successfully"
    )


@users_bp.route('/<user_id>', methods=['PATCH'])
@handle_api_exceptions
def update_user_patch(user_id):
    """
    Perform a partial update (PATCH) on a user.
    
    URL Parameters:
        user_id (str): MongoDB ObjectId of the user
    
    Request Body (JSON):
        {
            "full_name": "Jane Doe"  # Update only the fields you need
            # NOTE: 'email' field is immutable and will be ignored if provided
        }
    
    Returns:
        200 OK:
            {
                "status": "success",
                "status_code": 200,
                "message": "User updated successfully",
                "data": {}
            }
    
    Raises:
        400 Bad Request: If user_id is invalid or no valid fields provided
        404 Not Found: If user does not exist
        500 Internal Server Error: Database errors
    
    Important Notes:
        - The 'email' field is immutable and cannot be changed
        - Password will be automatically hashed if provided
        - 'updated_at' is automatically set to current time
        - Only provided fields are updated, others remain unchanged
    """
    data = request.get_json()
    
    if not data:
        from app.core.exceptions import BadRequestException
        raise BadRequestException(
            message="Request body cannot be empty",
            error_code="EMPTY_BODY"
        )
    
    user_service.update_user_patch(user_id, data)
    
    return success_response(
        data={},
        status_code=200,
        message="User updated successfully"
    )


@users_bp.route('/<user_id>', methods=['DELETE'])
@handle_api_exceptions
def delete_user(user_id):
    """
    Permanently delete a user account.
    
    URL Parameters:
        user_id (str): MongoDB ObjectId of the user
    
    Returns:
        200 OK:
            {
                "status": "success",
                "status_code": 200,
                "message": "User deleted successfully",
                "data": {}
            }
    
    Raises:
        400 Bad Request: If user_id is not a valid ObjectId
        404 Not Found: If user does not exist
        500 Internal Server Error: Database errors
    
    Warning:
        This operation is permanent and cannot be undone.
    """
    user_service.delete_user(user_id)
    
    return success_response(
        data={},
        status_code=200,
        message="User deleted successfully"
    )
