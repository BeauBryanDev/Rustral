"""
Example route handlers for Image endpoints.
Demonstrates proper error handling with the custom exception system.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.image_service import image_service
from app.core.error_handlers import handle_api_exceptions, success_response, error_response
from app.core.exceptions import BadRequestException, UnauthorizedException


# Create Blueprint
images_bp = Blueprint('images', __name__, url_prefix='/api/v1/images')


@images_bp.route('/<image_id>', methods=['GET'])
@jwt_required()
@handle_api_exceptions
def get_image(image_id):
    """
    Retrieve a single image by ID.
    
    Path Parameters:
        image_id (str): The MongoDB ObjectId of the image
    
    Returns:
        200: Image document with metadata
        400: Invalid ObjectId format
        401: Unauthorized (missing/invalid JWT token)
        404: Image not found
        500: Server error
    
    Example Response (200):
        {
            "status": "success",
            "status_code": 200,
            "message": "Image retrieved successfully",
            "data": {
                "_id": "507f1f77bcf86cd799439011",
                "filename": "inspection_001.jpg",
                "user_id": "507f1f77bcf86cd799439012",
                ...
            }
        }
    
    Example Response (404):
        {
            "status": "error",
            "status_code": 404,
            "error_code": "NOT_FOUND",
            "message": "Image not found (ID: invalid_id)",
            "details": {}
        }
    
    Example Response (400):
        {
            "status": "error",
            "status_code": 400,
            "error_code": "INVALID_OBJECT_ID",
            "message": "Invalid ObjectId format for field 'image_id': abc123",
            "details": {
                "field": "image_id",
                "value": "abc123"
            }
        }
    """
    # The service raises exceptions if there are errors
    # The decorator catches them and returns proper JSON responses
    image = image_service.get_image_by_id(image_id)
    return success_response(image, 200, "Image retrieved successfully")


@images_bp.route('', methods=['GET'])
@jwt_required()
@handle_api_exceptions
def list_images():
    """
    Retrieve all images (optionally filtered by user or location).
    
    Query Parameters:
        user_id (optional): Filter by user
        location_id (optional): Filter by location
    
    Returns:
        200: List of image documents
        400: Invalid query parameters
        500: Server error
    
    Example Response (200):
        {
            "status": "success",
            "status_code": 200,
            "message": "Images retrieved successfully",
            "data": [
                { "image": 1 },
                { "image": 2 }
            ]
        }
    """
    user_id = request.args.get('user_id')
    location_id = request.args.get('location_id')
    
    if user_id:
        images = image_service.get_image_by_user(user_id)
    elif location_id:
        images = image_service.get_image_by_location(location_id)
    else:
        images = image_service.get_all_images()
    
    return success_response(images, 200, f"Retrieved {len(images)} images")


@images_bp.route('/<image_id>', methods=['DELETE'])
@jwt_required()
@handle_api_exceptions
def delete_image(image_id):
    """
    Delete an image by ID.
    
    Path Parameters:
        image_id (str): The MongoDB ObjectId of the image
    
    Returns:
        200: Image successfully deleted
        400: Invalid ObjectId format
        404: Image not found
        500: Server error
    
    Example Response (200):
        {
            "status": "success",
            "status_code": 200,
            "message": "Image deleted successfully",
            "data": {}
        }
    
    Example Response (404):
        {
            "status": "error",
            "status_code": 404,
            "error_code": "NOT_FOUND",
            "message": "Image not found (ID: 507f1f77bcf86cd799439011)",
            "details": {}
        }
    """
    # Verify image exists first (will raise NotFoundException if not)
    image_service.get_image_by_id(image_id)
    
    # Delete the image
    success = image_service.delete_image(image_id)
    
    if success:
        return success_response({}, 200, "Image deleted successfully")
    else:
        # This shouldn't happen since get_image_by_id validates first
        return error_response(500, "DELETE_FAILED", "Failed to delete image")


# Error handler for this blueprint (optional, overrides global handlers)
@images_bp.errorhandler(400)
def handle_bad_request(error):
    """Handle 400 errors specific to images routes."""
    return error_response(400, "BAD_REQUEST", str(error.description or "Invalid request"))


@images_bp.errorhandler(404)
def handle_not_found(error):
    """Handle 404 errors specific to images routes."""
    return error_response(404, "NOT_FOUND", str(error.description or "Resource not found"))
