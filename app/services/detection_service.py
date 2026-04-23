import logging
from typing import List, Optional, Dict, Any
from bson.objectid import ObjectId
from bson.errors import InvalidId

from app.core.database import db_instance
from app.models.detections import DetectionDocument
from app.core.exceptions import (
    NotFoundException,
    InvalidObjectIdException,
    DatabaseException,
    BadRequestException,
    ValidationException,
)

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


    def get_detection_by_id(self, detection_id: str) -> Dict[str, Any]:
        """
        Retrieves a single detection document by its unique identifier.

        Args:
            detection_id (str): The string representation of the document ObjectId.

        Returns:
            Dict[str, Any]: The serialized detection document.
            
        Raises:
            InvalidObjectIdException: If detection_id is not a valid ObjectId format.
            NotFoundException: If no detection exists with the given ID.
            DatabaseException: If a database error occurs.
        """
        try:
            object_id = ObjectId(detection_id)
            
        except InvalidId:
            
            logger.warning(f"Invalid ObjectId format provided: {detection_id}")
            raise InvalidObjectIdException(field="detection_id", value=detection_id)
        
        try:
            document = self.collection.find_one({"_id": object_id})
            
            if not document:
                logger.info(f"Detection not found with ID: {detection_id}")
                raise NotFoundException(resource="Detection", identifier=detection_id)
            
            return DetectionDocument.from_dict(document).to_dict()
        
        except NotFoundException:
            raise
        
        except Exception as e:
            logger.error(f"Error fetching detection by ID {detection_id}: {e}")
            raise DatabaseException(operation="get_detection_by_id")


    def get_all_detection_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all detection documents associated with a specific user.

        Args:
            user_id (str): The string representation of the user's ObjectId.

        Returns:
            List[Dict[str, Any]]: A list of serialized detection documents.
            
        Raises:
            InvalidObjectIdException: If user_id is not a valid ObjectId format.
            DatabaseException: If a database error occurs.
        """
        try:
            object_id = ObjectId(user_id)
            
        except InvalidId:
            
            logger.warning(f"Invalid User ObjectId format provided: {user_id}")
            raise InvalidObjectIdException(field="user_id", value=user_id)
        
        try:
            query = {"user_id": object_id}
            cursor = self.collection.find(query)
            detections = [DetectionDocument.from_dict(document).to_dict() for document in cursor]
            return detections
        
        except Exception as e:
            logger.error(f"Error fetching detections by user {user_id}: {e}")
            raise DatabaseException(operation="get_all_detection_by_user")


    def get_detections_by_location(self, user_id: str, location_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all detection documents for a specific user and location.

        Args:
            user_id (str): The string representation of the user's ObjectId.
            location_id (str): The string representation of the location's ObjectId.

        Returns:
            List[Dict[str, Any]]: A list of serialized detection documents.
            
        Raises:
            InvalidObjectIdException: If user_id or location_id is not a valid ObjectId format.
            DatabaseException: If a database error occurs.
        """
        try:
            user_obj_id = ObjectId(user_id)
            location_obj_id = ObjectId(location_id)
            
        except InvalidId as e:
            
            invalid_id = user_id if "user_id" in str(e) else location_id
            field = "user_id" if invalid_id == user_id else "location_id"
            
            logger.warning(f"Invalid ObjectId format provided for {field}: {invalid_id}")
            raise InvalidObjectIdException(field=field, value=invalid_id)
        
        try:
            query = {"user_id": user_obj_id, "location_id": location_obj_id}
            cursor = self.collection.find(query)
            detections = [DetectionDocument.from_dict(document).to_dict() for document in cursor]
            return detections
        
        except Exception as e:
            
            logger.error(f"Error fetching detections by user {user_id} and location {location_id}: {e}")
            raise DatabaseException(operation="get_detections_by_location")


    def get_all_detection_by_severity(self, severity_level: str) -> List[Dict[str, Any]]:
        """
        Retrieves all detection documents that contain at least one detection
        matching the specified severity level.

        Args:
            severity_level (str): The severity level to filter by (e.g., "High", "Medium", "Low").

        Returns:
            List[Dict[str, Any]]: A list of serialized detection documents.
            
        Raises:
            ValidationException: If severity_level is not provided.
            DatabaseException: If a database error occurs.
        """
        if not severity_level:
            
            raise ValidationException(field="severity_level", reason="Severity level is required")
        
        try:
            # This query looks for documents where any element in the 'detections' array has a severity level of 'severity_level'
            query = {"detections.severity_level": severity_level}
            cursor = self.collection.find(query)
            detections = [DetectionDocument.from_dict(document).to_dict() for document in cursor]
            
            return detections
        
        except Exception as e:
            
            logger.error(f"Error fetching detections by severity level {severity_level}: {e}")
            raise DatabaseException(operation="get_all_detection_by_severity")


    def get_detections_by_image(self, image_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all detection documents associated with a specific image.

        Args:
            image_id (str): The string representation of the image's ObjectId.

        Returns:
            List[Dict[str, Any]]: A list of serialized detection documents.
            
        Raises:
            InvalidObjectIdException: If image_id is not a valid ObjectId format.
            DatabaseException: If a database error occurs.
        """
        try:
            object_id = ObjectId(image_id)
            
        except InvalidId:
            logger.warning(f"Invalid Image ObjectId format provided: {image_id}")
            
            raise InvalidObjectIdException(field="image_id", value=image_id)
        
        try:
            query = {"image_id": object_id}
            cursor = self.collection.find(query)
            detections = [DetectionDocument.from_dict(document).to_dict() for document in cursor]
            return detections
        
        except Exception as e:
            logger.error(f"Error fetching detections by image {image_id}: {e}")
            raise DatabaseException(operation="get_detections_by_image")


    def delete_detection(self, detection_id: str) -> None:
        """
        Permanently removes a detection document from the database.

        Args:
            detection_id (str): The string representation of the document ObjectId.

        Raises:
            InvalidObjectIdException: If detection_id is not a valid ObjectId format.
            NotFoundException: If no detection exists with the given ID.
            DatabaseException: If a database error occurs.
        """
        try:
            object_id = ObjectId(detection_id)
            
        except InvalidId:
            logger.warning(f"Invalid ObjectId format provided for deletion: {detection_id}")
            
            raise InvalidObjectIdException(field="detection_id", value=detection_id)
        
        try:
            result = self.collection.delete_one({"_id": object_id})
            
            if result.deleted_count == 0:
                logger.info(f"Detection not found with ID: {detection_id}")
                raise NotFoundException(resource="Detection", identifier=detection_id)
            
            logger.info(f"Successfully deleted detection with ID: {detection_id}")
        
        except NotFoundException:
            raise
        
        except Exception as e:
            logger.error(f"Error deleting detection with ID {detection_id}: {e}")
            raise DatabaseException(operation="delete_detection")


# Singleton instantiation for route injection
detection_service = DetectionService()
