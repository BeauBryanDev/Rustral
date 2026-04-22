import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from bson.objectid import ObjectId
from bson.errors import InvalidId

from app.core.database import db_instance
from app.models.locations import LocationDocument
from app.core.exceptions import (
    NotFoundException,
    InvalidObjectIdException,
    DatabaseException,
    BadRequestException,
    ConflictException,
)

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

    def create_location(self, location_data: Dict[str, Any]) -> str:
        """
        Creates a new location document in the database.

        Args:
            location_data (Dict[str, Any]): The raw dictionary containing location attributes.

        Returns:
            str: The string representation of the inserted ObjectId.
            
        Raises:
            BadRequestException: If required fields are missing.
            DatabaseException: If a database error occurs.
        """
        try:
            # Ensure user_id is properly cast to ObjectId if provided as string
            if isinstance(location_data.get("user_id"), str):
                try:
                    location_data["user_id"] = ObjectId(location_data["user_id"])
                except InvalidId:
                    raise BadRequestException(message="Invalid user_id ObjectId format", error_code="INVALID_USER_ID")

            location_model = LocationDocument(**location_data)
            document_dict = location_model.to_dict()
            
            result = self.collection.insert_one(document_dict)
            logger.info(f"Successfully created location with ID: {result.inserted_id}")
            
            return str(result.inserted_id)
            
        except BadRequestException:
            raise
        except Exception as error:
            logger.error(f"Failed to create location. Error: {error}")
            raise DatabaseException(operation="create_location")


    def get_location_by_id(self, location_id: str) -> Dict[str, Any]:
        """
        Retrieves a single location document by its unique identifier.

        Args:
            location_id (str): The string representation of the document ObjectId.

        Returns:
            Dict[str, Any]: The serialized location document.
            
        Raises:
            InvalidObjectIdException: If location_id is not a valid ObjectId format.
            NotFoundException: If no location exists with the given ID.
            DatabaseException: If a database error occurs.
        """
        try:
            object_id = ObjectId(location_id)
        except InvalidId:
            logger.warning(f"Invalid ObjectId format provided: {location_id}")
            raise InvalidObjectIdException(field="location_id", value=location_id)
        
        try:
            document = self.collection.find_one({"_id": object_id})
            
            if not document:
                logger.info(f"Location not found with ID: {location_id}")
                raise NotFoundException(resource="Location", identifier=location_id)
            
            return LocationDocument.from_dict(document).to_dict()
        
        except NotFoundException:
            raise
        
        except Exception as e:
            logger.error(f"Error fetching location by ID {location_id}: {e}")
            raise DatabaseException(operation="get_location_by_id") 


    def get_locations_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all location documents associated with a specific user.

        Args:
            user_id (str): The string representation of the user's ObjectId.

        Returns:
            List[Dict[str, Any]]: A list of serialized location documents.
            
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
            locations = [LocationDocument.from_dict(document).to_dict() for document in cursor]
            return locations
        
        except Exception as e:
            logger.error(f"Error fetching locations by user {user_id}: {e}")
            raise DatabaseException(operation="get_locations_by_user")

    def update_location_put(self, location_id: str, update_data: Dict[str, Any]) -> None:
        """
        Performs a full replacement update (PUT) on a location document.
        Strictly excludes the 'address' field from being modified.

        Args:
            location_id (str): The string representation of the document ObjectId.
            update_data (Dict[str, Any]): The complete payload to replace the existing record.

        Raises:
            InvalidObjectIdException: If location_id is not a valid ObjectId format.
            NotFoundException: If no location exists with the given ID.
            BadRequestException: If update_data is empty after stripping protected fields.
            DatabaseException: If a database error occurs.
        """
        try:
            object_id = ObjectId(location_id)
        except InvalidId:
            logger.warning(f"Invalid ObjectId format provided for PUT update: {location_id}")
            raise InvalidObjectIdException(field="location_id", value=location_id)
        
        try:
            # Strip the immutable 'address' field
            if "address" in update_data:
                update_data.pop("address")
                logger.debug(f"Stripped immutable 'address' field from PUT payload for ID: {location_id}")

            if not update_data:
                raise BadRequestException(message="No valid fields provided for update", error_code="EMPTY_UPDATE")

            # Force the updated_at timestamp
            update_data["updated_at"] = datetime.utcnow()

            result = self.collection.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                logger.info(f"Location not found with ID: {location_id}")
                raise NotFoundException(resource="Location", identifier=location_id)
            
            logger.info(f"Successfully updated location with ID: {location_id}")
            
        except (InvalidObjectIdException, NotFoundException, BadRequestException):
            raise
        except Exception as e:
            logger.error(f"Error updating location with ID {location_id}: {e}")
            raise DatabaseException(operation="update_location_put")


    def update_location_patch(self, location_id: str, patch_data: Dict[str, Any]) -> None:
        """
        Performs a partial update (PATCH) on a location document.
        Strictly excludes the 'address' field from being modified.

        Args:
            location_id (str): The string representation of the document ObjectId.
            patch_data (Dict[str, Any]): The subset of fields to update.

        Raises:
            InvalidObjectIdException: If location_id is not a valid ObjectId format.
            NotFoundException: If no location exists with the given ID.
            BadRequestException: If patch_data is empty after stripping protected fields.
            DatabaseException: If a database error occurs.
        """
        try:
            object_id = ObjectId(location_id)
        except InvalidId:
            logger.warning(f"Invalid ObjectId format provided for PATCH update: {location_id}")
            raise InvalidObjectIdException(field="location_id", value=location_id)
        
        try:
            # Strip the immutable 'address' field
            if "address" in patch_data:
                patch_data.pop("address")
                logger.debug(f"Stripped immutable 'address' field from PATCH payload for ID: {location_id}")

            if not patch_data:
                raise BadRequestException(message="No valid fields provided for update", error_code="EMPTY_UPDATE")

            # Force the updated_at timestamp
            patch_data["updated_at"] = datetime.utcnow()

            result = self.collection.update_one(
                {"_id": object_id},
                {"$set": patch_data}
            )
            
            if result.matched_count == 0:
                logger.info(f"Location not found with ID: {location_id}")
                raise NotFoundException(resource="Location", identifier=location_id)
            
            logger.info(f"Successfully patched location with ID: {location_id}")
            
        except (InvalidObjectIdException, NotFoundException, BadRequestException):
            raise
        except Exception as e:
            logger.error(f"Error patching location with ID {location_id}: {e}")
            raise DatabaseException(operation="update_location_patch")

    def delete_location(self, location_id: str) -> None:
        """
        Permanently removes a location document from the database.

        Args:
            location_id (str): The string representation of the document ObjectId.

        Raises:
            InvalidObjectIdException: If location_id is not a valid ObjectId format.
            NotFoundException: If no location exists with the given ID.
            DatabaseException: If a database error occurs.
        """
        try:
            object_id = ObjectId(location_id)
        except InvalidId:
            logger.warning(f"Invalid ObjectId format provided for deletion: {location_id}")
            raise InvalidObjectIdException(field="location_id", value=location_id)
        
        try:
            result = self.collection.delete_one({"_id": object_id})
            
            if result.deleted_count == 0:
                logger.info(f"Location not found with ID: {location_id}")
                raise NotFoundException(resource="Location", identifier=location_id)
            
            logger.info(f"Successfully deleted location with ID: {location_id}")
        
        except NotFoundException:
            raise
        
        except Exception as e:
            logger.error(f"Error deleting location with ID {location_id}: {e}")
            raise DatabaseException(operation="delete_location")


# Singleton instantiation for route injection
location_service = LocationCRUDService()

