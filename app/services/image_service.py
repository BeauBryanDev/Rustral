import logging
from typing import List, Optional, Dict, Any
from bson.objectid import ObjectId
from bson.errors import InvalidId

from app.core.database import db_instance
from app.models.images import ImageDocument # Assuming ImageDocument exists in app/models/images


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
        """
        try:
            query = {"user_id": ObjectId(user_id)}
            
            cursor = self.collection.find(query)
            
            images = []
            
            for document in cursor:
                
                images.append(ImageDocument.from_dict(document).to_dict())
                
            return images
        
        except InvalidId:
            
            logger.warning(f"Invalid User ObjectId format provided: {user_id}")
            
            return []
        
        except Exception as e:
            
            logger.error(f"Error fetching images by user {user_id}: {e}")
            
            return []

    def get_all_images(self) -> List[Dict[str, Any]]:
        """
        Retrieves all image documents. This method should typically be restricted to admin users.

        Returns:
            List[Dict[str, Any]]: A list of all serialized image documents.
        """
        try:
            cursor = self.collection.find({})
            
            images = []
            
            for document in cursor:
                
                images.append(ImageDocument.from_dict(document).to_dict())
                
            return images
        
        except Exception as e:
            
            logger.error(f"Error fetching all images: {e}")
            
            return []
        

    def get_image_by_id(self, image_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single image document by its unique identifier.

        Args:
            image_id (str): The string representation of the document ObjectId.

        Returns:
            Optional[Dict[str, Any]]: The serialized image document, or None if not found.
        """
        try:
            object_id = ObjectId(image_id)
            
            document = self.collection.find_one({"_id": object_id})
            
            if document:
                
                return ImageDocument.from_dict(document).to_dict()
            
            return None
        
        except InvalidId:
            
            logger.warning(f"Invalid ObjectId format provided: {image_id}")
            
            return None
        
        except Exception as e:
            
            logger.error(f"Error fetching image by ID {image_id}: {e}")
            
            return None

    def get_image_by_location(self, location_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all image documents associated with a specific location.

        Args:
            location_id (str): The string representation of the location's ObjectId.

        Returns:
            List[Dict[str, Any]]: A list of serialized image documents.
        """
        try:
            
            query = {"location_id": ObjectId(location_id)}
            
            cursor = self.collection.find(query)
            
            images = []
            
            for document in cursor:     
                
                images.append(ImageDocument.from_dict(document).to_dict())
                
            return images
        
        except InvalidId:
            
            logger.warning(f"Invalid Location ObjectId format provided: {location_id}")
            
            return []
        
        except Exception as e:
            
            logger.error(f"Error fetching images by location {location_id}: {e}")
            
            return []


    def delete_image(self, image_id: str) -> bool:
        """
        Permanently removes an image document from the database.

        Args:
            image_id (str): The string representation of the document ObjectId.

        Returns:
            bool: True if the document was successfully deleted, False otherwise.
        """
        try:
            object_id = ObjectId(image_id)
            
            result = self.collection.delete_one({"_id": object_id})
            
            if result.deleted_count > 0:
                
                logger.info(f"Successfully deleted image with ID: {image_id}")
                
                return True
            
            return False
        
        except InvalidId:
            
            logger.warning(f"Invalid ObjectId format provided for deletion: {image_id}")
            
            return False
        
        except Exception as e:
            
            logger.error(f"Error deleting image with ID {image_id}: {e}")
            
            return False


# Singleton instantiation for route injection
image_service = ImageService()
