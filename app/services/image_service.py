import logging
from typing import List, Optional, Dict, Any
from bson.objectid import ObjectId
from bson.errors import InvalidId

from app.core.database import db_instance
from app.models.images import ImageDocument # Assuming ImageDocument exists in app/models/images
from app.core.exceptions import (
    NotFoundException,
    InvalidObjectIdException,
    DatabaseException,
    BadRequestException,
)

logger = logging.getLogger(__name__)


class ImageService:
    """
    Service class handling CRUD operations for the Images collection.
    """

    def __init__(self):
        """
        Initializes the service and sets the target MongoDB collection.
        """
        self.collection = db_instance.db.images

    def get_image_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all image documents associated with a specific user.

        Args:
            user_id (str): The string representation of the user's ObjectId.

        Returns:
            List[Dict[str, Any]]: A list of serialized image documents.
            
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
            images = [ImageDocument.from_dict(document).to_dict() for document in cursor]
            return images
        
        except Exception as e:
            logger.error(f"Error fetching images by user {user_id}: {e}")
            raise DatabaseException(operation="get_image_by_user")

    def get_all_images(self) -> List[Dict[str, Any]]:
        """
        Retrieves all image documents. This method should  be restricted only to the admin user.

        Returns:
            List[Dict[str, Any]]: A list of all serialized image documents.
            
        Raises:
            DatabaseException: If a database error occurs.
        """
        try:
            cursor = self.collection.find({})
            images = [ImageDocument.from_dict(document).to_dict() for document in cursor]
            return images
        
        except Exception as e:
            logger.error(f"Error fetching all images: {e}")
            raise DatabaseException(operation="get_all_images")
        

    def get_image_by_id(self, image_id: str) -> Dict[str, Any]:
        """
        Retrieves a single image document by its unique identifier.

        Args:
            image_id (str): The string representation of the document ObjectId.

        Returns:
            Dict[str, Any]: The serialized image document.
            
        Raises:
            InvalidObjectIdException: If image_id is not a valid ObjectId format.
            NotFoundException: If no image exists with the given ID.
            DatabaseException: If a database error occurs.
        """
        try:
            # Validate ObjectId format
            object_id = ObjectId(image_id)
            
        except InvalidId:
            logger.warning(f"Invalid ObjectId format provided: {image_id}")
            raise InvalidObjectIdException(field="image_id", value=image_id)
        
        try:
            document = self.collection.find_one({"_id": object_id})
            
            if not document:
                logger.info(f"Image not found with ID: {image_id}")
                raise NotFoundException(resource="Image", identifier=image_id)
            
            return ImageDocument.from_dict(document).to_dict()
        
        except NotFoundException:
            # Re-raise NotFoundException as-is
            raise
        
        except Exception as e:
            logger.error(f"Error fetching image by ID {image_id}: {e}")
            raise DatabaseException(operation="get_image_by_id")

    def get_image_by_location(self, location_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all image documents associated with a specific location.

        Args:
            location_id (str): The string representation of the location's ObjectId.

        Returns:
            List[Dict[str, Any]]: A list of serialized image documents.
            
        Raises:
            InvalidObjectIdException: If location_id is not a valid ObjectId format.
            DatabaseException: If a database error occurs.
        """
        try:
            object_id = ObjectId(location_id)
        except InvalidId:
            
            logger.warning(f"Invalid Location ObjectId format provided: {location_id}")
            raise InvalidObjectIdException(field="location_id", value=location_id)
        
        try:
            query = {"location_id": object_id}
            cursor = self.collection.find(query)
            images = [ImageDocument.from_dict(document).to_dict() for document in cursor]
            return images
        
        except Exception as e:
            logger.error(f"Error fetching images by location {location_id}: {e}")
            raise DatabaseException(operation="get_image_by_location")


    def create_image(
        self,
        user_id: str,
        location_id: str,
        stored_filename: str,
        stored_path: str,
        mime_type: str,
        size_bytes: int,
        width_px: int,
        height_px: int,
        total_detections: int = 0,
    ) -> str:
        """
        Creates and persists a new ImageDocument in the images collection.

        Returns:
            str: The string representation of the inserted document's ObjectId.

        Raises:
            InvalidObjectIdException: If user_id or location_id is not a valid ObjectId.
            DatabaseException: If the insert operation fails.
        """
        try:
            image_doc = ImageDocument(
                user_id=ObjectId(user_id),
                location_id=ObjectId(location_id),
                stored_filename=stored_filename,
                stored_path=stored_path,
                mime_type=mime_type,
                size_bytes=size_bytes,
                width_px=width_px,
                height_px=height_px,
                total_detections=total_detections,
            )
            result = self.collection.insert_one(image_doc.to_dict())
            logger.info(f"Image document created with ID: {result.inserted_id}")
            return str(result.inserted_id)

        except InvalidId:
            raise InvalidObjectIdException(field="user_id or location_id", value=f"{user_id}, {location_id}")

        except Exception as e:
            logger.error(f"Error creating image document: {e}")
            raise DatabaseException(operation="create_image")

    def delete_image(self, image_id: str) -> None:
        """
        Permanently removes an image document from the database.

        Args:
            image_id (str): The string representation of the document ObjectId.
            
        Raises:
            InvalidObjectIdException: If image_id is not a valid ObjectId format.
            NotFoundException: If no image exists with the given ID.
            DatabaseException: If a database error occurs.
        """
        try:
            object_id = ObjectId(image_id)
        except InvalidId:
            logger.warning(f"Invalid ObjectId format provided for deletion: {image_id}")
            raise InvalidObjectIdException(field="image_id", value=image_id)
        
        try:
            result = self.collection.delete_one({"_id": object_id})
            
            if result.deleted_count == 0:
                logger.info(f"Image not found with ID: {image_id}")
                raise NotFoundException(resource="Image", identifier=image_id)
            
            logger.info(f"Successfully deleted image with ID: {image_id}")
        
        except NotFoundException:
            raise
        
        except Exception as e:
            logger.error(f"Error deleting image with ID {image_id}: {e}")
            raise DatabaseException(operation="delete_image")


# Singleton instantiation for route injection
image_service = ImageService()
