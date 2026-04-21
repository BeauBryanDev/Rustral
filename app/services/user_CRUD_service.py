import logging
from datetime import datetime
from typing import Optional, Dict, Any
from bson.objectid import ObjectId
from bson.errors import InvalidId

from app.core.database import db_instance
from app.models.users import UserDocument
from app.core.security import get_password_hash


logger = logging.getLogger(__name__)


class UserCRUDService:
    """
    Service class handling all CRUD operations for the Users collection.
    Integrates password hashing and enforces business rules such as email immutability.
    """

    def __init__(self):
        """
        Initializes the service and sets the target MongoDB collection.
        """
        self.collection = db_instance.db.users

    def create_user(self, user_data: Dict[str, Any]) -> Optional[str]:
        """
        Creates a new user document in the database after hashing the password.
        Checks for email duplication before insertion.

        Args:
            user_data (Dict[str, Any]): The raw dictionary containing user attributes.

        Returns:
            Optional[str]: The string representation of the inserted ObjectId, or None if failed.
        """
        try:
            
            email = user_data.get("email")
            
            if not email:
                
                logger.error("User creation failed: Email is required.")
                
                return None

            # Check for existing user to prevent duplicate emails
            existing_user = self.get_user_by_email(email)
            
            if existing_user:
                
                logger.warning(f"User creation failed: Email {email} already exists.")
                
                return None
            

            # Hash the raw password before instantiating the model
            raw_password = user_data.get("hash_password")
            
            if raw_password:
                
                user_data["hash_password"] = get_password_hash(raw_password)
                
            else:
                
                logger.error("User creation failed: Password is required.")
                
                return None

            user_model = UserDocument(**user_data)
            document_dict = user_model.to_dict()
            
            result = self.collection.insert_one(document_dict)
            
            logger.info(f"Successfully created user with ID: {result.inserted_id}")
            
            return str(result.inserted_id)
            
        except Exception as error:
            
            logger.error(f"Failed to create user. Error: {error}")
            
            return None


    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single user document by its unique identifier.

        Args:
            user_id (str): The string representation of the document ObjectId.

        Returns:
            Optional[Dict[str, Any]]: The serialized user document, or None if not found.
        """
        try:
            object_id = ObjectId(user_id)
            
            document = self.collection.find_one({"_id": object_id})
            
            if document:
                
                return UserDocument.from_dict(document).to_dict()
            
            return None
            
        except InvalidId:
            
            logger.warning(f"Invalid ObjectId format provided: {user_id}")
            
            return None


    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single user document by their email address.
        Highly useful for login and authentication workflows.

        Args:
            email (str): The exact email address of the user.

        Returns:
            Optional[Dict[str, Any]]: The serialized user document, or None if not found.
        """
        document = self.collection.find_one({"email": email})
        
        if document:
            
            return UserDocument.from_dict(document).to_dict()
        
        return None


    def update_user_put(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Performs a full replacement update (PUT) on a user document.
        Strictly excludes the 'email' field. Hashes password if provided.

        Args:
            user_id (str): The string representation of the document ObjectId.
            update_data (Dict[str, Any]): The complete payload to replace the existing record.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        try:
            object_id = ObjectId(user_id)
            
            # Protect the primary identity field
            if "email" in update_data:
                
                update_data.pop("email")
                
                logger.debug(f"Stripped immutable 'email' field from PUT payload for ID: {user_id}")

            # Hash password if a new one is being set during the update
            if "hash_password" in update_data:
                update_data["hash_password"] = get_password_hash(update_data["hash_password"])

            update_data["updated_at"] = datetime.utcnow()

            result = self.collection.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except InvalidId:
            
            logger.warning(f"Invalid ObjectId format provided for PUT update: {user_id}")
            
            return False


    def update_user_patch(self, user_id: str, patch_data: Dict[str, Any]) -> bool:
        """
        Performs a partial update (PATCH) on a user document.
        Strictly excludes the 'email' field. Hashes password if provided.

        Args:
            user_id (str): The string representation of the document ObjectId.
            patch_data (Dict[str, Any]): The subset of fields to update.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        try:
            object_id = ObjectId(user_id)
            
            if "email" in patch_data:
                
                patch_data.pop("email")
                
                logger.debug(f"Stripped immutable 'email' field from PATCH payload for ID: {user_id}")

            if "hash_password" in patch_data:
                
                patch_data["hash_password"] = get_password_hash(patch_data["hash_password"])

            if not patch_data:
                
                logger.warning("PATCH payload is empty after stripping protected fields.")
                
                return False

            patch_data["updated_at"] = datetime.utcnow()

            result = self.collection.update_one(
                {"_id": object_id},
                {"$set": patch_data}
            )
            
            return result.modified_count > 0
            
        except InvalidId:
            
            logger.warning(f"Invalid ObjectId format provided for PATCH update: {user_id}")
            
            return False

    def delete_user(self, user_id: str) -> bool:
        """
        Permanently removes a user document from the database.

        Args:
            user_id (str): The string representation of the document ObjectId.

        Returns:
            bool: True if the document was successfully deleted, False otherwise.
        """
        try:
            object_id = ObjectId(user_id)
            result = self.collection.delete_one({"_id": object_id})
            
            if result.deleted_count > 0:
                
                logger.info(f"Successfully deleted user with ID: {user_id}")
                
                return True
            
            return False
        
            
        except InvalidId:
            
            logger.warning(f"Invalid ObjectId format provided for deletion: {user_id}")
            
            return False


# Singleton instantiation for route injection
user_service = UserCRUDService()

