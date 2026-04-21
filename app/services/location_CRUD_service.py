import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from bson.objectid import ObjectId
from bson.errors import InvalidId

from app.core.database import db_instance
from app.models.locations import LocationDocument


logger = logging.getLogger(__name__)


class LocationCRUDService:
    """
    Service class handling all CRUD operations for the Locations collection.
    Enforces business rules, such as the immutability of the 'address' field during updates.
    """

    def __init__(self):
        """
        Initializes the service and sets the target MongoDB collection.
        """
        self.collection = db_instance.db.locations

    def create_location(self, location_data: Dict[str, Any]) -> Optional[str]:
        """
        Creates a new location document in the database.

        Args:
            location_data (Dict[str, Any]): The raw dictionary containing location attributes.

        Returns:
            Optional[str]: The string representation of the inserted ObjectId, or None if failed.
        """
        try:
            # Ensure user_id is properly cast to ObjectId if provided as string
            if isinstance(location_data.get("user_id"), str):
                
                location_data["user_id"] = ObjectId(location_data["user_id"])

            location_model = LocationDocument(**location_data)
            
            document_dict = location_model.to_dict()
            
            result = self.collection.insert_one(document_dict)
            
            logger.info(f"Successfully created location with ID: {result.inserted_id}")
            
            return str(result.inserted_id)
            
        except Exception as error:
            
            logger.error(f"Failed to create location. Error: {error}")
            return None


    def get_location_by_id(self, location_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single location document by its unique identifier.

        Args:
            location_id (str): The string representation of the document ObjectId.

        Returns:
            Optional[Dict[str, Any]]: The serialized location document, or None if not found.
        """
        try:
            object_id = ObjectId(location_id)
            
            document = self.collection.find_one({"_id": object_id})
            
            if document:
                # Convert to model and back to dict to ensure standard serialization
                return LocationDocument.from_dict(document).to_dict()
            
            return None
            
        except InvalidId:
            
            logger.warning(f"Invalid ObjectId format provided: {location_id}")
            
            return None


    def get_locations_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all location documents associated with a specific user.

        Args:
            user_id (str): The string representation of the user's ObjectId.

        Returns:
            List[Dict[str, Any]]: A list of serialized location documents.
        """
        try:
            query = {"user_id": ObjectId(user_id)}
            cursor = self.collection.find(query)
            
            locations = []
            
            for document in cursor:
                
                locations.append(LocationDocument.from_dict(document).to_dict())
                
            return locations
            
        except InvalidId:
            
            logger.warning(f"Invalid User ObjectId format provided: {user_id}")
            
            return []

    def update_location_put(self, location_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Performs a full replacement update (PUT) on a location document.
        Strictly excludes the 'address' field from being modified.

        Args:
            location_id (str): The string representation of the document ObjectId.
            update_data (Dict[str, Any]): The complete payload to replace the existing record.

        Returns:
            bool: True if the update was successful and modified a document, False otherwise.
        """
        try:
            object_id = ObjectId(location_id)
            
            # Strip the immutable 'address' field
            if "address" in update_data:
                
                update_data.pop("address")
                
                logger.debug(f"Stripped immutable 'address' field from PUT payload for ID: {location_id}")

            # Force the updated_at timestamp
            update_data["updated_at"] = datetime.utcnow()

            # Apply the full replacement logic (excluding _id, address, and created_at)
            # To simulate a PUT without destroying immutable fields, we use $set with the full payload
            # rather than replacing the entire document which would wipe the address completely.
            result = self.collection.update_one(
                
                {"_id": object_id},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except InvalidId:
            
            logger.warning(f"Invalid ObjectId format provided for PUT update: {location_id}")
            
            return False


    def update_location_patch(self, location_id: str, patch_data: Dict[str, Any]) -> bool:
        """
        Performs a partial update (PATCH) on a location document.
        Strictly excludes the 'address' field from being modified.

        Args:
            location_id (str): The string representation of the document ObjectId.
            patch_data (Dict[str, Any]): The subset of fields to update.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        try:
            object_id = ObjectId(location_id)
            
            #  Strip the immutable 'address' field
            if "address" in patch_data:
                
                patch_data.pop("address")
                
                logger.debug(f"Stripped immutable 'address' field from PATCH payload for ID: {location_id}")

            if not patch_data:
                
                logger.warning("PATCH payload is empty after stripping protected fields.")
                
                return False

            #  Force the updated_at timestamp
            patch_data["updated_at"] = datetime.utcnow()

            #  Apply the partial update
            result = self.collection.update_one(
                {"_id": object_id},
                {"$set": patch_data}
            )
            
            return result.modified_count > 0
            
        except InvalidId:
            
            logger.warning(f"Invalid ObjectId format provided for PATCH update: {location_id}")
            
            return False

    def delete_location(self, location_id: str) -> bool:
        """
        Permanently removes a location document from the database.

        Args:
            location_id (str): The string representation of the document ObjectId.

        Returns:
            bool: True if the document was successfully deleted, False otherwise.
        """
        try:
            object_id = ObjectId(location_id)
            
            result = self.collection.delete_one({"_id": object_id})
            
            if result.deleted_count > 0:
                
                logger.info(f"Successfully deleted location with ID: {location_id}")
                
                return True
            
            return False
            
        except InvalidId:
            
            logger.warning(f"Invalid ObjectId format provided for deletion: {location_id}")
            
            return False


# Singleton instantiation for route injection
location_service = LocationCRUDService()

