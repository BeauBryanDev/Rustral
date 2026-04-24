"""
Flask Blueprint for Image Management Routes

Provides RESTful endpoints for image access with JWT-based ownership checks:
- GET /api/v1/images/<image_id> - Retrieve an image by ID
- GET /api/v1/images/user/me - Get all images for the authenticated user
- GET /api/v1/images/location/<location_id> - Get images by owned location
- GET /api/v1/images - Get all images (admin only)
- DELETE /api/v1/images/<image_id> - Delete an image
"""

import logging
from flask import Blueprint, request, g

from app.core.error_handlers import handle_api_exceptions, success_response
from app.core.exceptions import ForbiddenException
from app.routes.dependencies import jwt_required
from app.services.image_service import image_service
from app.services.location_CRUD_service import location_service
from app.services.user_CRUD_service import user_service


logger = logging.getLogger(__name__)

images_bp = Blueprint(
    "images",
    __name__,
    url_prefix="/api/v1/images",
)


def _require_admin_user() -> None:
    current_user = user_service.get_user_by_id(str(g.user_id))
    if not current_user.get("is_admin", False):
        raise ForbiddenException(
            message="Admin access required",
            error_code="ADMIN_REQUIRED",
        )


def _require_image_ownership(image_id: str) -> dict:
    image = image_service.get_image_by_id(image_id)
    if str(image.get("user_id")) != str(g.user_id):
        raise ForbiddenException(
            message="You do not have permission to access this image",
            error_code="IMAGE_ACCESS_DENIED",
            details={"image_id": image_id},
        )
    return image


def _require_location_ownership(location_id: str) -> None:
    location = location_service.get_location_by_id(location_id)
    if str(location.get("user_id")) != str(g.user_id):
        raise ForbiddenException(
            message="You do not have permission to access images for this location",
            error_code="LOCATION_IMAGES_ACCESS_DENIED",
            details={"location_id": location_id},
        )


@images_bp.route("/<image_id>", methods=["GET"])
@jwt_required
@handle_api_exceptions
def get_image(image_id):
    """
    Retrieve an image by its unique ID.
    """
    image = _require_image_ownership(image_id)

    return success_response(
        data=image,
        status_code=200,
        message="Image retrieved successfully",
    )


@images_bp.route("/user/me", methods=["GET"])
@jwt_required
@handle_api_exceptions
def get_user_images():
    """
    Get all images belonging to the authenticated user.
    """
    images = image_service.get_image_by_user(str(g.user_id))

    return success_response(
        data={"images": images, "count": len(images)},
        status_code=200,
        message="User images retrieved successfully",
    )


@images_bp.route("/location/<location_id>", methods=["GET"])
@jwt_required
@handle_api_exceptions
def get_location_images(location_id):
    """
    Get all images for a specific location owned by the authenticated user.
    """
    _require_location_ownership(location_id)
    images = image_service.get_image_by_location(location_id)

    return success_response(
        data={"images": images, "count": len(images)},
        status_code=200,
        message="Location images retrieved successfully",
    )


@images_bp.route("/", methods=["GET"])
@jwt_required
@handle_api_exceptions
def get_all_images():
    """
    Get all images in the system.

    This endpoint is restricted to admin users.
    """
    _require_admin_user()

    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 20, type=int)
    images = image_service.get_all_images()

    return success_response(
        data={"images": images, "count": len(images), "page": page, "limit": limit},
        status_code=200,
        message="All images retrieved successfully",
    )


@images_bp.route("/<image_id>", methods=["DELETE"])
@jwt_required
@handle_api_exceptions
def delete_image(image_id):
    """
    Delete an image by its ID.
    """
    _require_image_ownership(image_id)
    image_service.delete_image(image_id)

    return success_response(
        data={},
        status_code=200,
        message="Image deleted successfully",
    )
