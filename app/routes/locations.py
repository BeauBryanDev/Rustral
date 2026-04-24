import logging
from flask import Blueprint, request, g

from app.core.error_handlers import handle_api_exceptions, success_response
from app.core.exceptions import BadRequestException, ForbiddenException
from app.services.location_CRUD_service import location_service
from app.routes.dependencies import jwt_required
"""
Flask Blueprint for Location Management Routes

Provides RESTful endpoints for all location CRUD operations:
- POST /api/v1/locations - Create a new location
- GET /api/v1/locations/<location_id> - Retrieve a location
- GET /api/v1/locations/user/me - Get locations for the authenticated user
- PUT /api/v1/locations/<location_id> - Full update
- PATCH /api/v1/locations/<location_id> - Partial update
- DELETE /api/v1/locations/<location_id> - Delete a location
"""

logger = logging.getLogger(__name__)

locations_bp = Blueprint(
    'locations',
    __name__,
    url_prefix='/api/v1/locations'
)


@locations_bp.route('/', methods=['POST'])
@jwt_required
@handle_api_exceptions
def create_location():
    """
    Create a new location.
    
    Request Body:
        {
            "name": "Factory A",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "address": "New York, NY, USA"
        }
    
    Returns:
        201 Created:
            {
                "status": "success",
                "status_code": 201,
                "message": "Location created successfully",
                "data": {
                    "location_id": "507f1f77bcf86cd799439014"
                }
            }
    
    Raises:
        400 Bad Request: Missing fields or invalid payload
        500 Internal Server Error: Database errors
    """
    data = request.get_json()
    
    if not data:
        
        raise BadRequestException(
            message="Request body cannot be empty",
            error_code="EMPTY_BODY"
        )
    
    data["user_id"] = g.user_id

    location_id = location_service.create_location(data)
    
    return success_response(
        data={"location_id": location_id},
        status_code=201,
        message="Location created successfully"
    )


@locations_bp.route('/<location_id>', methods=['GET'])
@jwt_required
@handle_api_exceptions
def get_location(location_id):
    """
    Retrieve a location by its unique ID.
    
    URL Parameters:
        location_id (str): MongoDB ObjectId of the location
    
    Returns:
        200 OK:
            {
                "status": "success",
                "status_code": 200,
                "message": "Location retrieved successfully",
                "data": {
                    "_id": "507f1f77bcf86cd799439014",
                    "user_id": "507f1f77bcf86cd799439011",
                    "name": "Factory A",
                    "latitude": 40.7128,
                    "longitude": -74.0060,
                    "address": "New York, NY, USA",
                    "created_at": "2026-04-23T10:30:00",
                    "updated_at": "2026-04-23T10:30:00"
                }
            }
    
    Raises:
        400 Bad Request: If location_id is not a valid ObjectId
        403 Forbidden: If the location does not belong to the authenticated user
        404 Not Found: If location does not exist
        500 Internal Server Error: Database errors
    """
    location = location_service.get_location_by_id(location_id)

    if str(location.get("user_id")) != str(g.user_id):
        
        raise ForbiddenException(
            message="You do not have permission to access this location",
            error_code="LOCATION_ACCESS_DENIED",
            details={"location_id": location_id}
        )
    
    return success_response(
        data=location,
        status_code=200,
        message="Location retrieved successfully"
    )


@locations_bp.route('/user/me', methods=['GET'])
@jwt_required
@handle_api_exceptions
def get_user_locations():
    """
    Get all locations belonging to the authenticated user.
    
    Returns:
        200 OK:
            {
                "status": "success",
                "status_code": 200,
                "message": "User locations retrieved successfully",
                "data": {
                    "locations": [...],
                    "count": 2
                }
            }
    
    Raises:
        500 Internal Server Error: Database errors
    """
    authenticated_user_id = str(g.user_id)

    locations = location_service.get_locations_by_user(authenticated_user_id)
    
    return success_response(
        data={"locations": locations, "count": len(locations)},
        status_code=200,
        message="User locations retrieved successfully"
    )


@locations_bp.route('/<location_id>', methods=['PUT'])
@jwt_required
@handle_api_exceptions
def update_location_put(location_id):
    """
    Perform a full replacement update (PUT) on a location.
    
    URL Parameters:
        location_id (str): MongoDB ObjectId of the location
    
    Request Body:
        {
            "name": "Factory A Updated",
            "latitude": 40.7200,
            "longitude": -74.0100,
            "address": "Updated Address"
        }
    
    Returns:
        200 OK:
            {
                "status": "success",
                "status_code": 200,
                "message": "Location updated successfully",
                "data": {}
            }
    
    Raises:
        400 Bad Request: If location_id is invalid or no valid fields provided
        403 Forbidden: If the location does not belong to the authenticated user
        404 Not Found: If location does not exist
        500 Internal Server Error: Database errors
    """
    data = request.get_json()
    
    if not data:
        raise BadRequestException(
            message="Request body cannot be empty",
            error_code="EMPTY_BODY"
        )
    
    location = location_service.get_location_by_id(location_id)

    if str(location.get("user_id")) != str(g.user_id):
        raise ForbiddenException(
            message="You do not have permission to update this location",
            error_code="LOCATION_UPDATE_DENIED",
            details={"location_id": location_id}
        )

    location_service.update_location_put(location_id, data)
    
    return success_response(
        data={},
        status_code=200,
        message="Location updated successfully"
    )


@locations_bp.route('/<location_id>', methods=['PATCH'])
@jwt_required
@handle_api_exceptions
def update_location_patch(location_id):
    """
    Perform a partial update (PATCH) on a location.
    
    URL Parameters:
        location_id (str): MongoDB ObjectId of the location
    
    Request Body:
        {
            "name": "Factory A Renamed"
        }
    
    Returns:
        200 OK:
            {
                "status": "success",
                "status_code": 200,
                "message": "Location updated successfully",
                "data": {}
            }
    
    Raises:
        400 Bad Request: If location_id is invalid or no valid fields provided
        403 Forbidden: If the location does not belong to the authenticated user
        404 Not Found: If location does not exist
        500 Internal Server Error: Database errors
    
    Note:
        Only provided fields are updated, others remain unchanged.
    """
    data = request.get_json()
    
    if not data:
        raise BadRequestException(
            message="Request body cannot be empty",
            error_code="EMPTY_BODY"
        )
    
    location = location_service.get_location_by_id(location_id)

    if str(location.get("user_id")) != str(g.user_id):
        raise ForbiddenException(
            message="You do not have permission to update this location",
            error_code="LOCATION_UPDATE_DENIED",
            details={"location_id": location_id}
        )

    location_service.update_location_patch(location_id, data)
    
    return success_response(
        data={},
        status_code=200,
        message="Location updated successfully"
    )


@locations_bp.route('/<location_id>', methods=['DELETE'])
@jwt_required
@handle_api_exceptions
def delete_location(location_id):
    """
    Delete a location by its ID.
    
    URL Parameters:
        location_id (str): MongoDB ObjectId of the location
    
    Returns:
        200 OK:
            {
                "status": "success",
                "status_code": 200,
                "message": "Location deleted successfully",
                "data": {}
            }
    
    Raises:
        400 Bad Request: If location_id is not a valid ObjectId
        403 Forbidden: If the location does not belong to the authenticated user
        404 Not Found: If location does not exist
        500 Internal Server Error: Database errors
    
    Warning:
        This operation is permanent and cannot be undone.
    """
    location = location_service.get_location_by_id(location_id)

    if str(location.get("user_id")) != str(g.user_id):
        raise ForbiddenException(
            message="You do not have permission to delete this location",
            error_code="LOCATION_DELETE_DENIED",
            details={"location_id": location_id}
        )

    location_service.delete_location(location_id)
    
    return success_response(
        data={},
        status_code=200,
        message="Location deleted successfully"
    )
