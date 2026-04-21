import logging
from typing import List, Optional, Dict, Any
from bson.objectid import ObjectId
from bson.errors import InvalidId

from app.core.database import db_instance
from app.models.detections import DetectionDocument


logger = logging.getLogger(__name__)


class DetectionService:
    """
    Service class handling CRUD operations for the Detections collection.
    All database interactions are synchronous using pymongo.
    """

    def __init__(self):
        """
        Initializes the service and sets the target MongoDB collection.
        """
        self.collection = db_instance.db.detections

    def get_detection_by_id(self, detection_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single detection document by its unique identifier.

        Args:
            detection_id (str): The string representation of the document ObjectId.

        Returns:
            Optional[Dict[str, Any]]: The serialized detection document, or None if not found.
        """
        try:
            object_id = ObjectId(detection_id)
            document = self.collection.find_one({"_id": object_id})
            if document:
                return DetectionDocument.from_dict(document).to_dict()
            return None
        except InvalidId:
            logger.warning(f"Invalid ObjectId format provided: {detection_id}")
            return None
        except Exception as e:
            logger.error(f"Error fetching detection by ID {detection_id}: {e}")
            return None

    def get_all_detection_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all detection documents associated with a specific user.

        Args:
            user_id (str): The string representation of the user's ObjectId.

        Returns:
            List[Dict[str, Any]]: A list of serialized detection documents.
        """
        try:
            query = {"user_id": ObjectId(user_id)}
            cursor = self.collection.find(query)
            detections = []
            for document in cursor:
                detections.append(DetectionDocument.from_dict(document).to_dict())
            return detections
        except InvalidId:
            logger.warning(f"Invalid User ObjectId format provided: {user_id}")
            return []
        except Exception as e:
            logger.error(f"Error fetching detections by user {user_id}: {e}")
            return []

    def get_detections_by_location(self, user_id: str, location_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all detection documents for a specific user and location.

        Args:
            user_id (str): The string representation of the user's ObjectId.
            location_id (str): The string representation of the location's ObjectId.

        Returns:
            List[Dict[str, Any]]: A list of serialized detection documents.
        """
        try:
            query = {"user_id": ObjectId(user_id), "location_id": ObjectId(location_id)}
            cursor = self.collection.find(query)
            detections = []
            for document in cursor:
                detections.append(DetectionDocument.from_dict(document).to_dict())
            return detections
        except InvalidId:
            logger.warning(f"Invalid ObjectId format provided for user_id: {user_id} or location_id: {location_id}")
            return []
        except Exception as e:
            logger.error(f"Error fetching detections by user {user_id} and location {location_id}: {e}")
            return []

    def get_all_detection_by_severity(self, severity_level: str) -> List[Dict[str, Any]]:
        """
        Retrieves all detection documents that contain at least one detection
        matching the specified severity level.

        Args:
            severity_level (str): The severity level to filter by (e.g., "High", "Medium", "Low").

        Returns:
            List[Dict[str, Any]]: A list of serialized detection documents.
        """
        try:
            # This query looks for documents where any element in the 'detections' array
            # has a 'severity_level' field matching the provided value.
            query = {"detections.severity_level": severity_level}
            cursor = self.collection.find(query)
            detections = []
            for document in cursor:
                detections.append(DetectionDocument.from_dict(document).to_dict())
            return detections
        except Exception as e:
            logger.error(f"Error fetching detections by severity level {severity_level}: {e}")
            return []

    def get_detections_by_image(self, image_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all detection documents associated with a specific image.

        Args:
            image_id (str): The string representation of the image's ObjectId.

        Returns:
            List[Dict[str, Any]]: A list of serialized detection documents.
        """
        try:
            query = {"image_id": ObjectId(image_id)}
            cursor = self.collection.find(query)
            detections = []
            for document in cursor:
                detections.append(DetectionDocument.from_dict(document).to_dict())
            return detections
        except InvalidId:
            logger.warning(f"Invalid Image ObjectId format provided: {image_id}")
            return []
        except Exception as e:
            logger.error(f"Error fetching detections by image {image_id}: {e}")
            return []

    def delete_detection(self, detection_id: str) -> bool:
        """
        Permanently removes a detection document from the database.

        Args:
            detection_id (str): The string representation of the document ObjectId.

        Returns:
            bool: True if the document was successfully deleted, False otherwise.
        """
        try:
            object_id = ObjectId(detection_id)
            result = self.collection.delete_one({"_id": object_id})
            if result.deleted_count > 0:
                logger.info(f"Successfully deleted detection with ID: {detection_id}")
                return True
            return False
        except InvalidId:
            logger.warning(f"Invalid ObjectId format provided for deletion: {detection_id}")
            return False
        except Exception as e:
            logger.error(f"Error deleting detection with ID {detection_id}: {e}")
            return False

# Singleton instantiation for route injection
detection_service = DetectionService()
