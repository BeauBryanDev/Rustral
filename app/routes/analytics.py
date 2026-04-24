import logging
from typing import Any, Dict, List, Optional

from bson.errors import InvalidId
from bson.objectid import ObjectId
from flask import Blueprint, g, request

from app.core.database import db_instance
from app.core.error_handlers import handle_api_exceptions, success_response
from app.core.exceptions import BadRequestException, ForbiddenException
from app.routes.dependencies import jwt_required
from app.services.location_CRUD_service import location_service
from app.services.user_CRUD_service import user_service

"""
Flask Blueprint for Analytics Endpoints

Provides authenticated dashboard data derived from the detections collection:
- GET /api/v1/analytics/summary - Admin dashboard summary
- GET /api/v1/analytics/user/me - Current user analytics
- GET /api/v1/analytics/location/<location_id> - Location analytics
- GET /api/v1/analytics/severity-distribution - Severity statistics
- GET /api/v1/analytics/detections/fractal-dimension - Detections filtered by fractal dimension
- GET /api/v1/analytics/last-detections - Recent detections for the authenticated user
- GET /api/v1/analytics/admin/recent-detections - Recent detection documents
"""

logger = logging.getLogger(__name__)

analytics_bp = Blueprint(
    "analytics",
    __name__,
    url_prefix="/api/v1/analytics",
)


def _user_object_id() -> ObjectId:
    try:
        return ObjectId(str(g.user_id))
    except InvalidId:
        raise BadRequestException(
            message="Invalid authenticated user identity",
            error_code="INVALID_USER_ID",
        )


def _is_admin_user() -> bool:
    current_user = user_service.get_user_by_id(str(g.user_id))
    return bool(current_user.get("is_admin", False))


def _require_admin_user() -> None:
    if not _is_admin_user():
        raise ForbiddenException(
            message="Admin access required",
            error_code="ADMIN_REQUIRED",
        )


def _location_object_id(location_id: str) -> ObjectId:
    try:
        return ObjectId(location_id)
    except InvalidId:
        raise BadRequestException(
            message="Invalid location_id ObjectId format",
            error_code="INVALID_LOCATION_ID",
        )


def _ensure_location_ownership(location_id: str) -> ObjectId:
    location = location_service.get_location_by_id(location_id)

    if str(location.get("user_id")) != str(g.user_id):
        raise ForbiddenException(
            message="You do not have permission to access analytics for this location",
            error_code="LOCATION_ANALYTICS_ACCESS_DENIED",
            details={"location_id": location_id},
        )

    return _location_object_id(location_id)


def _get_collections():
    db = db_instance.db
    return db.users, db.locations, db.images, db.detections


def _base_match(user_id: ObjectId, location_id: Optional[ObjectId] = None) -> Dict[str, Any]:
    query: Dict[str, Any] = {"user_id": user_id}
    if location_id is not None:
        query["location_id"] = location_id
    return query


def _severity_distribution(match: Dict[str, Any]) -> Dict[str, int]:
    _, _, _, detections_collection = _get_collections()

    pipeline = [
        {"$match": match},
        {"$unwind": {"path": "$detections", "preserveNullAndEmptyArrays": False}},
        {
            "$group": {
                "_id": {
                    "$toLower": {
                        "$ifNull": ["$detections.severity_level", ""]
                    }
                },
                "count": {"$sum": 1},
            }
        },
    ]

    result = detections_collection.aggregate(pipeline)
    distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0, "none": 0}

    for row in result:
        severity = row.get("_id") or "none"
        if severity not in distribution:
            distribution[severity] = 0
        distribution[severity] = row.get("count", 0)

    return distribution


def _detection_stats(match: Dict[str, Any]) -> Dict[str, Any]:
    _, _, _, detections_collection = _get_collections()

    doc_count = detections_collection.count_documents(match)

    pipeline = [
        {"$match": match},
        {"$unwind": {"path": "$detections", "preserveNullAndEmptyArrays": False}},
        {
            "$group": {
                "_id": None,
                "total_instances": {"$sum": 1},
                "average_fractal_dimension": {"$avg": "$detections.fractal_dimension"},
                "max_fractal_dimension": {"$max": "$detections.fractal_dimension"},
                "min_fractal_dimension": {"$min": "$detections.fractal_dimension"},
                "average_inference_time_ms": {"$avg": "$inference_time_ms"},
                "latest_detected_at": {"$max": "$detected_at"},
            }
        },
    ]

    rows = list(detections_collection.aggregate(pipeline))
    if rows:
        row = rows[0]
    else:
        row = {}

    return {
        "detection_documents": doc_count,
        "total_instances": row.get("total_instances", 0),
        "average_fractal_dimension": round(row.get("average_fractal_dimension") or 0.0, 4),
        "max_fractal_dimension": round(row.get("max_fractal_dimension") or 0.0, 4),
        "min_fractal_dimension": round(row.get("min_fractal_dimension") or 0.0, 4),
        "average_inference_time_ms": round(row.get("average_inference_time_ms") or 0.0, 2),
        "latest_detected_at": row.get("latest_detected_at"),
    }


def _flatten_fractal_detections(
    match: Dict[str, Any],
    min_fractal: Optional[float],
    max_fractal: Optional[float],
    limit: int,
) -> List[Dict[str, Any]]:
    _, _, _, detections_collection = _get_collections()

    pipeline: List[Dict[str, Any]] = [
        {"$match": match},
        {"$unwind": {"path": "$detections", "preserveNullAndEmptyArrays": False}},
    ]

    fractal_filter: Dict[str, Any] = {}
    if min_fractal is not None:
        fractal_filter["$gte"] = min_fractal
    if max_fractal is not None:
        fractal_filter["$lte"] = max_fractal

    if fractal_filter:
        pipeline.append({"$match": {"detections.fractal_dimension": fractal_filter}})

    pipeline.extend(
        [
            {"$sort": {"detections.fractal_dimension": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "_id": 0,
                    "detection_document_id": {"$toString": "$_id"},
                    "user_id": {"$toString": "$user_id"},
                    "location_id": {"$toString": "$location_id"},
                    "image_id": {
                        "$cond": [
                            {"$ifNull": ["$image_id", False]},
                            {"$toString": "$image_id"},
                            None,
                        ]
                    },
                    "detected_at": 1,
                    "inference_time_ms": 1,
                    "box": "$detections.box",
                    "confidence": "$detections.confidence",
                    "area_px": "$detections.area_px",
                    "area_cm2": "$detections.area_cm2",
                    "fractal_dimension": "$detections.fractal_dimension",
                    "severity_level": {
                        "$toLower": {
                            "$ifNull": ["$detections.severity_level", ""]
                        }
                    },
                }
            },
        ]
    )

    return list(detections_collection.aggregate(pipeline))


def _recent_detections(match: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
    _, _, _, detections_collection = _get_collections()

    pipeline = [
        {"$match": match},
        {"$sort": {"detected_at": -1}},
        {"$limit": limit},
        {
            "$project": {
                "_id": 0,
                "detection_document_id": {"$toString": "$_id"},
                "user_id": {"$toString": "$user_id"},
                "location_id": {"$toString": "$location_id"},
                "image_id": {
                    "$cond": [
                        {"$ifNull": ["$image_id", False]},
                        {"$toString": "$image_id"},
                        None,
                    ]
                },
                "detected_at": 1,
                "inference_time_ms": 1,
                "detections_count": {
                    "$size": {"$ifNull": ["$detections", []]}
                },
                "detections": 1,
                "aruco_metadata": 1,
            }
        },
    ]

    return list(detections_collection.aggregate(pipeline))


@analytics_bp.route("/summary", methods=["GET"])
@jwt_required
@handle_api_exceptions
def get_summary():
    """
    Get a real dashboard summary for the authenticated admin user.
    """
    _require_admin_user()
    users_collection, locations_collection, images_collection, detections_collection = _get_collections()

    match: Dict[str, Any] = {}

    summary = {
        "admin_user_id": str(g.user_id),
        "total_locations": locations_collection.count_documents({}),
        "total_images": images_collection.count_documents({}),
        "total_detection_documents": detections_collection.count_documents(match),
    }
    summary.update(_detection_stats(match))
    summary["severity_distribution"] = _severity_distribution(match)
    summary["total_users"] = users_collection.count_documents({})

    return success_response(
        data=summary,
        status_code=200,
        message="System summary retrieved successfully",
    )


@analytics_bp.route("/user/me", methods=["GET"])
@jwt_required
@handle_api_exceptions
def get_user_analytics():
    """
    Get analytics for the authenticated user.
    """
    user_id = _user_object_id()
    _, locations_collection, images_collection, detections_collection = _get_collections()

    match = _base_match(user_id)
    analytics = {
        "user_id": str(user_id),
        "locations_monitored": locations_collection.count_documents({"user_id": user_id}),
        "images_uploaded": images_collection.count_documents({"user_id": user_id}),
        "detection_documents": detections_collection.count_documents(match),
    }
    analytics.update(_detection_stats(match))
    analytics["severity_distribution"] = _severity_distribution(match)

    return success_response(
        data=analytics,
        status_code=200,
        message="User analytics retrieved successfully",
    )


@analytics_bp.route("/location/<location_id>", methods=["GET"])
@jwt_required
@handle_api_exceptions
def get_location_analytics(location_id):
    """
    Get analytics for a specific location owned by the authenticated user.
    """
    user_id = _user_object_id()
    location_oid = _ensure_location_ownership(location_id)
    _, _, images_collection, detections_collection = _get_collections()

    match = _base_match(user_id, location_oid)
    analytics = {
        "location_id": str(location_oid),
        "total_images": images_collection.count_documents({"user_id": user_id, "location_id": location_oid}),
        "total_detection_documents": detections_collection.count_documents(match),
    }
    analytics.update(_detection_stats(match))
    analytics["severity_distribution"] = _severity_distribution(match)

    return success_response(
        data=analytics,
        status_code=200,
        message="Location analytics retrieved successfully",
    )


@analytics_bp.route("/severity-distribution", methods=["GET"])
@jwt_required
@handle_api_exceptions
def get_severity_distribution():
    """
    Get a real severity distribution for the authenticated user's detections.
    Optional query param:
        location_id: restrict to one owned location
    """
    user_id = _user_object_id()
    location_id = request.args.get("location_id")
    match = _base_match(user_id)

    if location_id:
        match["location_id"] = _ensure_location_ownership(location_id)

    distribution = _severity_distribution(match)
    total = sum(distribution.values())
    distribution["total"] = total

    return success_response(
        data=distribution,
        status_code=200,
        message="Severity distribution retrieved successfully",
    )


@analytics_bp.route("/admin/recent-detections", methods=["GET"])
@analytics_bp.route("/recent-detections", methods=["GET"])
@jwt_required
@handle_api_exceptions
def get_recent_detections():
    """
    Return recent detection documents for the admin dashboard.

    Query params:
        limit: maximum rows returned, default 10
    """
    _require_admin_user()

    limit_raw = request.args.get("limit", default="10")

    try:
        limit = int(limit_raw)
    except ValueError:
        raise BadRequestException(
            message="Query parameter 'limit' must be an integer",
            error_code="INVALID_LIMIT",
        )

    if limit < 1:
        raise BadRequestException(
            message="Query parameter 'limit' must be greater than zero",
            error_code="INVALID_LIMIT",
        )

    recent_detections = _recent_detections({}, limit)

    return success_response(
        data={
            "limit": limit,
            "count": len(recent_detections),
            "detections": recent_detections,
        },
        status_code=200,
        message="Recent detections retrieved successfully",
    )


@analytics_bp.route("/last-detections", methods=["GET"])
@jwt_required
@handle_api_exceptions
def get_last_detections():
    """
    Return the authenticated user's last detections.

    Query params:
        limit: maximum rows returned, default 10
    """
    user_id = _user_object_id()

    limit_raw = request.args.get("limit", default="10")

    try:
        limit = int(limit_raw)
    except ValueError:
        raise BadRequestException(
            message="Query parameter 'limit' must be an integer",
            error_code="INVALID_LIMIT",
        )

    if limit < 1:
        raise BadRequestException(
            message="Query parameter 'limit' must be greater than zero",
            error_code="INVALID_LIMIT",
        )

    recent_detections = _recent_detections({"user_id": user_id}, limit)

    return success_response(
        data={
            "limit": limit,
            "user_id": str(user_id),
            "count": len(recent_detections),
            "detections": recent_detections,
        },
        status_code=200,
        message="Last detections retrieved successfully",
    )


@analytics_bp.route("/detections/fractal-dimension", methods=["GET"])
@jwt_required
@handle_api_exceptions
def get_detections_by_fractal_dimension():
    """
    Return flattened detection entries filtered by fractal dimension.

    Query params:
        min: minimum fractal dimension, default 0.0
        max: maximum fractal dimension, optional
        limit: maximum rows returned, default 50
        location_id: optional owned location filter
    """
    user_id = _user_object_id()

    min_raw = request.args.get("min", default="0.0")
    max_raw = request.args.get("max")
    limit_raw = request.args.get("limit", default="50")
    location_id = request.args.get("location_id")

    try:
        min_fractal = float(min_raw)
    except ValueError:
        raise BadRequestException(
            message="Query parameter 'min' must be a number",
            error_code="INVALID_MIN_FRACTAL",
        )

    max_fractal: Optional[float] = None
    if max_raw not in (None, ""):
        try:
            max_fractal = float(max_raw)
        except ValueError:
            raise BadRequestException(
                message="Query parameter 'max' must be a number",
                error_code="INVALID_MAX_FRACTAL",
            )

    try:
        limit = int(limit_raw)
    except ValueError:
        raise BadRequestException(
            message="Query parameter 'limit' must be an integer",
            error_code="INVALID_LIMIT",
        )

    if limit < 1:
        raise BadRequestException(
            message="Query parameter 'limit' must be greater than zero",
            error_code="INVALID_LIMIT",
        )

    match = _base_match(user_id)
    if location_id:
        match["location_id"] = _ensure_location_ownership(location_id)

    detections = _flatten_fractal_detections(match, min_fractal, max_fractal, limit)

    return success_response(
        data={
            "filters": {
                "min": min_fractal,
                "max": max_fractal,
                "limit": limit,
                "location_id": location_id,
            },
            "count": len(detections),
            "detections": detections,
        },
        status_code=200,
        message="Detections filtered by fractal dimension retrieved successfully",
    )
