from datetime import datetime, timedelta, timezone
from io import BytesIO

import pytest
from bson.objectid import ObjectId
from unittest.mock import patch

from app.core.database import db_instance
from app.core.security import create_access_token
from app.services.detection_service import detection_service
from app.services.image_service import image_service
from app.services.location_CRUD_service import location_service
from app.services.user_CRUD_service import user_service


ADMIN_ID = ObjectId("60d5ec49f1b2c8b1f8e4b5a2")
USER_ID = ObjectId("60d5ec49f1b2c8b1f8e4b5a1")
OTHER_USER_ID = ObjectId("60d5ec49f1b2c8b1f8e4b5a3")

USER_LOCATION_1 = ObjectId("60d5ec49f1b2c8b1f8e4b5b1")
USER_LOCATION_2 = ObjectId("60d5ec49f1b2c8b1f8e4b5b2")
OTHER_LOCATION = ObjectId("60d5ec49f1b2c8b1f8e4b5b3")

USER_IMAGE_1 = ObjectId("60d5ec49f1b2c8b1f8e4b5c1")
USER_IMAGE_2 = ObjectId("60d5ec49f1b2c8b1f8e4b5c2")
OTHER_IMAGE = ObjectId("60d5ec49f1b2c8b1f8e4b5c3")


def _auth_headers_for(user_id: ObjectId) -> dict:
    token = create_access_token(subject=str(user_id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_auth_headers():
    return _auth_headers_for(OTHER_USER_ID)


@pytest.fixture
def seeded_dataset():
    db = db_instance.db
    db.users.delete_many({})
    db.locations.delete_many({})
    db.images.delete_many({})
    db.detections.delete_many({})

    user_service.collection = db.users
    location_service.collection = db.locations
    image_service.collection = db.images
    detection_service.collection = db.detections

    now = datetime.now(timezone.utc)

    db.users.insert_many(
        [
            {
                "_id": ADMIN_ID,
                "full_name": "Admin User",
                "email": "admin@example.com",
                "hash_password": "admin-hash",
                "is_active": True,
                "is_admin": True,
                "created_at": now - timedelta(days=3),
                "updated_at": now - timedelta(days=1),
            },
            {
                "_id": USER_ID,
                "full_name": "Primary User",
                "email": "user@example.com",
                "hash_password": "user-hash",
                "is_active": True,
                "is_admin": False,
                "created_at": now - timedelta(days=3),
                "updated_at": now - timedelta(days=1),
            },
            {
                "_id": OTHER_USER_ID,
                "full_name": "Other User",
                "email": "other@example.com",
                "hash_password": "other-hash",
                "is_active": True,
                "is_admin": False,
                "created_at": now - timedelta(days=3),
                "updated_at": now - timedelta(days=1),
            },
        ]
    )

    db.locations.insert_many(
        [
            {
                "_id": USER_LOCATION_1,
                "user_id": USER_ID,
                "name": "Primary Factory",
                "city": "Austin",
                "country": "USA",
                "address": "100 Industrial Way",
                "description": "Main inspection site",
                "created_at": now - timedelta(days=2),
                "updated_at": now - timedelta(days=1),
            },
            {
                "_id": USER_LOCATION_2,
                "user_id": USER_ID,
                "name": "Secondary Plant",
                "city": "Dallas",
                "country": "USA",
                "address": "200 Plant Road",
                "description": "Secondary inspection site",
                "created_at": now - timedelta(days=2),
                "updated_at": now - timedelta(days=1),
            },
            {
                "_id": OTHER_LOCATION,
                "user_id": OTHER_USER_ID,
                "name": "Other Factory",
                "city": "Houston",
                "country": "USA",
                "address": "300 Other Road",
                "description": "Other user's location",
                "created_at": now - timedelta(days=2),
                "updated_at": now - timedelta(days=1),
            },
        ]
    )

    db.images.insert_many(
        [
            {
                "_id": USER_IMAGE_1,
                "user_id": USER_ID,
                "location_id": USER_LOCATION_1,
                "stored_filename": "primary-1.jpg",
                "stored_path": "/tmp/primary-1.jpg",
                "mime_type": "image/jpeg",
                "size_bytes": 1024,
                "width_px": 640,
                "height_px": 640,
                "total_detections": 2,
                "created_at": now - timedelta(hours=6),
            },
            {
                "_id": USER_IMAGE_2,
                "user_id": USER_ID,
                "location_id": USER_LOCATION_2,
                "stored_filename": "primary-2.jpg",
                "stored_path": "/tmp/primary-2.jpg",
                "mime_type": "image/jpeg",
                "size_bytes": 2048,
                "width_px": 640,
                "height_px": 640,
                "total_detections": 1,
                "created_at": now - timedelta(hours=4),
            },
            {
                "_id": OTHER_IMAGE,
                "user_id": OTHER_USER_ID,
                "location_id": OTHER_LOCATION,
                "stored_filename": "other.jpg",
                "stored_path": "/tmp/other.jpg",
                "mime_type": "image/jpeg",
                "size_bytes": 3072,
                "width_px": 640,
                "height_px": 640,
                "total_detections": 1,
                "created_at": now - timedelta(hours=2),
            },
        ]
    )

    db.detections.insert_many(
        [
            {
                "_id": ObjectId(),
                "user_id": USER_ID,
                "location_id": USER_LOCATION_1,
                "image_id": USER_IMAGE_1,
                "detections": [
                    {
                        "box": [10, 20, 120, 160],
                        "confidence": 0.97,
                        "area_px": 150.0,
                        "area_cm2": 12.5,
                        "fractal_dimension": 1.91,
                        "severity_level": "High",
                    },
                    {
                        "box": [200, 210, 280, 300],
                        "confidence": 0.81,
                        "area_px": 75.0,
                        "area_cm2": 6.0,
                        "fractal_dimension": 1.18,
                        "severity_level": "Low",
                    },
                ],
                "aruco_metadata": {"detected": True, "marker_id": 0, "reference_scale_cm": 30.0},
                "inference_time_ms": 18.5,
                "detected_at": now - timedelta(hours=3),
            },
            {
                "_id": ObjectId(),
                "user_id": USER_ID,
                "location_id": USER_LOCATION_1,
                "image_id": USER_IMAGE_2,
                "detections": [
                    {
                        "box": [30, 40, 90, 120],
                        "confidence": 0.88,
                        "area_px": 95.0,
                        "area_cm2": 8.4,
                        "fractal_dimension": 1.45,
                        "severity_level": "Medium",
                    }
                ],
                "aruco_metadata": {"detected": True, "marker_id": 1, "reference_scale_cm": 30.0},
                "inference_time_ms": 14.2,
                "detected_at": now - timedelta(hours=2),
            },
            {
                "_id": ObjectId(),
                "user_id": USER_ID,
                "location_id": USER_LOCATION_2,
                "image_id": USER_IMAGE_2,
                "detections": [
                    {
                        "box": [15, 25, 80, 110],
                        "confidence": 0.94,
                        "area_px": 110.0,
                        "area_cm2": 9.1,
                        "fractal_dimension": 1.82,
                        "severity_level": "Critical",
                    }
                ],
                "aruco_metadata": {"detected": False, "marker_id": None, "reference_scale_cm": 30.0},
                "inference_time_ms": 21.7,
                "detected_at": now - timedelta(hours=1),
            },
            {
                "_id": ObjectId(),
                "user_id": OTHER_USER_ID,
                "location_id": OTHER_LOCATION,
                "image_id": OTHER_IMAGE,
                "detections": [
                    {
                        "box": [50, 60, 140, 190],
                        "confidence": 0.79,
                        "area_px": 130.0,
                        "area_cm2": 10.2,
                        "fractal_dimension": 1.33,
                        "severity_level": "Low",
                    }
                ],
                "aruco_metadata": {"detected": True, "marker_id": 2, "reference_scale_cm": 30.0},
                "inference_time_ms": 11.1,
                "detected_at": now,
            },
        ]
    )

    return {
        "now": now,
        "admin_id": ADMIN_ID,
        "user_id": USER_ID,
        "other_user_id": OTHER_USER_ID,
        "user_location_1": USER_LOCATION_1,
        "user_location_2": USER_LOCATION_2,
        "other_location": OTHER_LOCATION,
        "user_image_1": USER_IMAGE_1,
        "user_image_2": USER_IMAGE_2,
        "other_image": OTHER_IMAGE,
    }


def test_analytics_summary_admin_returns_system_counts(app_client, admin_auth_headers, seeded_dataset):
    response = app_client.get("/api/v1/analytics/summary", headers=admin_auth_headers)

    assert response.status_code == 200
    payload = response.get_json()
    data = payload["data"]

    assert data["total_users"] == 3
    assert data["total_locations"] == 3
    assert data["total_images"] == 3
    assert data["total_detection_documents"] == 4
    assert data["total_instances"] == 5
    assert data["severity_distribution"]["low"] == 2
    assert data["severity_distribution"]["medium"] == 1
    assert data["severity_distribution"]["high"] == 1
    assert data["severity_distribution"]["critical"] == 1


def test_analytics_user_me_returns_user_scoped_counts(app_client, auth_headers, seeded_dataset):
    response = app_client.get("/api/v1/analytics/user/me", headers=auth_headers)

    assert response.status_code == 200
    payload = response.get_json()["data"]

    assert payload["user_id"] == str(seeded_dataset["user_id"])
    assert payload["locations_monitored"] == 2
    assert payload["images_uploaded"] == 2
    assert payload["detection_documents"] == 3
    assert payload["total_instances"] == 4
    assert payload["severity_distribution"]["low"] == 1
    assert payload["severity_distribution"]["medium"] == 1
    assert payload["severity_distribution"]["high"] == 1
    assert payload["severity_distribution"]["critical"] == 1


def test_analytics_last_detections_returns_recent_user_rows(app_client, auth_headers, seeded_dataset):
    response = app_client.get("/api/v1/analytics/last-detections?limit=2", headers=auth_headers)

    assert response.status_code == 200
    payload = response.get_json()["data"]

    assert payload["limit"] == 2
    assert payload["user_id"] == str(seeded_dataset["user_id"])
    assert payload["count"] == 2
    assert payload["detections"][0]["location_id"] == str(seeded_dataset["user_location_2"])
    assert payload["detections"][1]["location_id"] == str(seeded_dataset["user_location_1"])


def test_analytics_admin_recent_detections_returns_latest_rows(app_client, admin_auth_headers, seeded_dataset):
    response = app_client.get("/api/v1/analytics/admin/recent-detections?limit=2", headers=admin_auth_headers)

    assert response.status_code == 200
    payload = response.get_json()["data"]

    assert payload["limit"] == 2
    assert payload["count"] == 2
    assert payload["detections"][0]["user_id"] == str(seeded_dataset["other_user_id"])
    assert payload["detections"][1]["user_id"] == str(seeded_dataset["user_id"])


def test_users_create_user_success(app_client, seeded_dataset):
    payload = {
        "full_name": "Created Endpoint User",
        "email": "created@example.com",
        "hash_password": "StrongPass123!",
    }

    with patch("app.services.user_CRUD_service.get_password_hash", return_value="hashed-password"):
        response = app_client.post("/api/v1/users/", json=payload)

    assert response.status_code == 201
    body = response.get_json()
    assert ObjectId(body["data"]["user_id"])
    stored = db_instance.db.users.find_one({"email": payload["email"]})
    assert stored is not None
    assert stored["full_name"] == payload["full_name"]
    assert stored["hash_password"] != payload["hash_password"]


def test_users_create_user_duplicate_email_conflict(app_client, seeded_dataset):
    payload = {
        "full_name": "Created Endpoint User",
        "email": "duplicate@example.com",
        "hash_password": "StrongPass123!",
    }

    with patch("app.services.user_CRUD_service.get_password_hash", return_value="hashed-password"):
        first = app_client.post("/api/v1/users/", json=payload)
        second = app_client.post("/api/v1/users/", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.get_json()["error_code"] == "EMAIL_EXISTS"


def test_users_get_by_email_returns_user(app_client, seeded_dataset):
    response = app_client.get("/api/v1/users/email/user@example.com")

    assert response.status_code == 200
    payload = response.get_json()["data"]

    assert payload["email"] == "user@example.com"
    assert payload["full_name"] == "Primary User"
    assert payload["is_admin"] is False


def test_users_patch_updates_full_name(app_client, seeded_dataset):
    response = app_client.patch(
        f"/api/v1/users/{seeded_dataset['user_id']}",
        json={"full_name": "Primary User Updated"},
    )

    assert response.status_code == 200
    updated = db_instance.db.users.find_one({"_id": seeded_dataset["user_id"]})
    assert updated["full_name"] == "Primary User Updated"


def test_locations_create_ignores_body_user_id(app_client, auth_headers, seeded_dataset):
    response = app_client.post(
        "/api/v1/locations/",
        headers=auth_headers,
        json={
            "name": "New User Location",
            "city": "Baton Rouge",
            "country": "USA",
            "address": "1 Example Ave",
            "description": "Created by endpoint",
            "user_id": str(seeded_dataset["other_user_id"]),
        },
    )

    assert response.status_code == 201
    location_id = ObjectId(response.get_json()["data"]["location_id"])
    stored = db_instance.db.locations.find_one({"_id": location_id})

    assert stored is not None
    assert stored["user_id"] == seeded_dataset["user_id"]
    assert stored["name"] == "New User Location"


def test_locations_user_me_returns_owned_locations(app_client, auth_headers, seeded_dataset):
    response = app_client.get("/api/v1/locations/user/me", headers=auth_headers)

    assert response.status_code == 200
    payload = response.get_json()["data"]

    assert payload["count"] == 2
    assert {item["user_id"] for item in payload["locations"]} == {str(seeded_dataset["user_id"])}


def test_locations_get_location_blocks_other_user(app_client, auth_headers, seeded_dataset):
    response = app_client.get(
        f"/api/v1/locations/{seeded_dataset['other_location']}",
        headers=auth_headers,
    )

    assert response.status_code == 403
    assert response.get_json()["error_code"] == "LOCATION_ACCESS_DENIED"


def test_locations_delete_owned_location(app_client, auth_headers, seeded_dataset):
    response = app_client.delete(
        f"/api/v1/locations/{seeded_dataset['user_location_2']}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert db_instance.db.locations.find_one({"_id": seeded_dataset["user_location_2"]}) is None


def test_images_user_me_returns_owned_images(app_client, auth_headers, seeded_dataset):
    response = app_client.get("/api/v1/images/user/me", headers=auth_headers)

    assert response.status_code == 200
    payload = response.get_json()["data"]

    assert payload["count"] == 2
    assert {item["user_id"] for item in payload["images"]} == {str(seeded_dataset["user_id"])}


def test_images_get_image_blocks_other_user(app_client, auth_headers, seeded_dataset):
    response = app_client.get(
        f"/api/v1/images/{seeded_dataset['other_image']}",
        headers=auth_headers,
    )

    assert response.status_code == 403
    assert response.get_json()["error_code"] == "IMAGE_ACCESS_DENIED"


def test_images_location_images_returns_owned_rows(app_client, auth_headers, seeded_dataset):
    response = app_client.get(
        f"/api/v1/images/location/{seeded_dataset['user_location_1']}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    payload = response.get_json()["data"]

    assert payload["count"] == 1
    assert payload["images"][0]["location_id"] == str(seeded_dataset["user_location_1"])


def test_images_admin_get_all_returns_system_images(app_client, admin_auth_headers, seeded_dataset):
    response = app_client.get("/api/v1/images/?limit=2", headers=admin_auth_headers)

    assert response.status_code == 200
    payload = response.get_json()["data"]

    assert payload["count"] == 3
    assert payload["page"] == 1
    assert payload["limit"] == 2


def test_detections_analyze_creates_document(app_client, auth_headers, seeded_dataset, valid_image_bytes):
    analysis_result = {
        "detections": [
            {
                "box": [10, 20, 120, 160],
                "confidence": 0.93,
                "area_px": 150.0,
                "area_cm2": 12.5,
                "fractal_dimension": 1.76,
                "severity_level": "High",
            }
        ],
        "aruco_metadata": {"detected": True, "marker_id": 7, "reference_scale_cm": 30.0},
        "inference_time_ms": 19.4,
    }

    with patch("app.routes.detections.vision_service_instance.analyze_corrosion", return_value=analysis_result), patch(
        "app.routes.detections.storage_service.save_masked_image",
        return_value="/tmp/annotated.jpg",
    ):
        response = app_client.post(
            "/api/v1/detections/analyze",
            headers=auth_headers,
            data={
                "location_id": str(seeded_dataset["user_location_1"]),
                "image": (BytesIO(valid_image_bytes), "analysis.jpg"),
            },
            content_type="multipart/form-data",
        )

    assert response.status_code == 201
    payload = response.get_json()
    stored = db_instance.db.detections.find_one({"_id": ObjectId(payload["detection_id"])})

    assert stored is not None
    assert stored["user_id"] == str(seeded_dataset["user_id"])
    assert stored["location_id"] == str(seeded_dataset["user_location_1"])
    assert stored["detections"][0]["severity_level"] == "High"


def test_detections_get_detection_returns_owned_row(app_client, auth_headers, seeded_dataset):
    detection = db_instance.db.detections.find_one({"user_id": seeded_dataset["user_id"]})

    response = app_client.get(f"/api/v1/detections/{detection['_id']}", headers=auth_headers)

    assert response.status_code == 200
    payload = response.get_json()["data"]

    assert payload["_id"] == str(detection["_id"])
    assert payload["user_id"] == str(seeded_dataset["user_id"])


def test_detections_user_route_blocks_url_spoofing(app_client, auth_headers, seeded_dataset):
    response = app_client.get(
        f"/api/v1/detections/user/{seeded_dataset['other_user_id']}",
        headers=auth_headers,
    )

    assert response.status_code == 403
    assert response.get_json()["error_code"] == "USER_DETECTIONS_ACCESS_DENIED"


def test_detections_location_route_blocks_other_user(app_client, auth_headers, seeded_dataset):
    response = app_client.get(
        f"/api/v1/detections/location/{seeded_dataset['other_location']}",
        headers=auth_headers,
    )

    assert response.status_code == 403
    assert response.get_json()["error_code"] == "LOCATION_ACCESS_DENIED"
