import logging
from datetime import datetime
from typing import Optional, Dict, Any
from bson.objectid import ObjectId
from bson.errors import InvalidId

from app.core.database import db_instance
from app.models.users import UserDocument
from app.core.security import get_password_hash
from app.core.exceptions import (
    NotFoundException,
    InvalidObjectIdException,
    DatabaseException,
    BadRequestException,
    ConflictException,
    InternalServerException,
)

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

    def create_user(self, user_data: Dict[str, Any]) -> str:
        """
        Creates a new user document in the database after hashing the password.
        Checks for email duplication before insertion.

        Args:
            user_data (Dict[str, Any]): The raw dictionary containing user attributes.

        Returns:
            str: The string representation of the inserted ObjectId.
            
        Raises:
            BadRequestException: If email is missing or already exists.
            InternalServerException: If password is missing.
            DatabaseException: If a database error occurs.
        """
        try:
            email = user_data.get("email")
            
            if not email:
                logger.error("User creation failed: Email is required.")
                raise BadRequestException(message="Email is required", error_code="MISSING_EMAIL")

            # Check for existing user to prevent duplicate emails
            existing_user = self.collection.find_one({"email": email})
            if existing_user:
                logger.warning(f"User creation failed: Email {email} already exists.")
                raise ConflictException(message=f"Email {email} is already registered", error_code="EMAIL_EXISTS")

            # Hash the raw password before instantiating the model
            raw_password = user_data.get("hash_password")
            if not raw_password:
                logger.error("User creation failed: Password is required.")
                raise BadRequestException(message="Password is required", error_code="MISSING_PASSWORD")
            
            user_data["hash_password"] = get_password_hash(raw_password)

            user_model = UserDocument(**user_data)
            document_dict = user_model.to_dict()
            
            result = self.collection.insert_one(document_dict)
            logger.info(f"Successfully created user with ID: {result.inserted_id}")
            
            return str(result.inserted_id)
            
        except (BadRequestException, ConflictException):
            raise
        except Exception as error:
            logger.error(f"Failed to create user. Error: {error}")
            raise DatabaseException(operation="create_user")


    def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieves a single user document by its unique identifier.

        Args:
            user_id (str): The string representation of the document ObjectId.

        Returns:
            Dict[str, Any]: The serialized user document.
            
        Raises:
            InvalidObjectIdException: If user_id is not a valid ObjectId format.
            NotFoundException: If no user exists with the given ID.
            DatabaseException: If a database error occurs.
        """
        try:
            object_id = ObjectId(user_id)
        except InvalidId:
            logger.warning(f"Invalid ObjectId format provided: {user_id}")
            raise InvalidObjectIdException(field="user_id", value=user_id)
        
        try:
            document = self.collection.find_one({"_id": object_id})
            
            if not document:
                logger.info(f"User not found with ID: {user_id}")
                raise NotFoundException(resource="User", identifier=user_id)
            
            return UserDocument.from_dict(document).to_dict()
        
        except NotFoundException:
            raise
        
        except Exception as e:
            logger.error(f"Error fetching user by ID {user_id}: {e}")
            raise DatabaseException(operation="get_user_by_id")


    def get_user_by_email(self, email: str) -> Dict[str, Any]:
        """
        Retrieves a single user document by their email address.
        Highly useful for login and authentication workflows.

        Args:
            email (str): The exact email address of the user.

        Returns:
            Dict[str, Any]: The serialized user document.
            
        Raises:
            NotFoundException: If no user exists with the given email.
            BadRequestException: If email is not provided.
            DatabaseException: If a database error occurs.
        """
        if not email:
            raise BadRequestException(message="Email is required", error_code="MISSING_EMAIL")
        
        try:
            document = self.collection.find_one({"email": email})
            
            if not document:
                logger.info(f"User not found with email: {email}")
                raise NotFoundException(resource="User", identifier=email)
            
            return UserDocument.from_dict(document).to_dict()
        
        except NotFoundException:
            raise
        
        except Exception as e:
            logger.error(f"Error fetching user by email {email}: {e}")
            raise DatabaseException(operation="get_user_by_email")


    def update_user_put(self, user_id: str, update_data: Dict[str, Any]) -> None:
        """
        Performs a full replacement update (PUT) on a user document.
        Strictly excludes the 'email' field. Hashes password if provided.

        Args:
            user_id (str): The string representation of the document ObjectId.
            update_data (Dict[str, Any]): The complete payload to replace the existing record.

        Raises:
            InvalidObjectIdException: If user_id is not a valid ObjectId format.
            NotFoundException: If no user exists with the given ID.
            BadRequestException: If update_data is empty after stripping protected fields.
            DatabaseException: If a database error occurs.
        """
        try:
            object_id = ObjectId(user_id)
            
        except InvalidId:
            logger.warning(f"Invalid ObjectId format provided for PUT update: {user_id}")
            raise InvalidObjectIdException(field="user_id", value=user_id)
        
        try:
            # Protect the primary identity field
            if "email" in update_data:
                
                update_data.pop("email")
                logger.debug(f"Stripped immutable 'email' field from PUT payload for ID: {user_id}")

            # Hash password if a new one is being set during the update
            if "hash_password" in update_data:
                update_data["hash_password"] = get_password_hash(update_data["hash_password"])

            if not update_data:
                raise BadRequestException(message="No valid fields provided for update", error_code="EMPTY_UPDATE")

            update_data["updated_at"] = datetime.utcnow()

            result = self.collection.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                logger.info(f"User not found with ID: {user_id}")
                raise NotFoundException(resource="User", identifier=user_id)
            
            logger.info(f"Successfully updated user with ID: {user_id}")
            
        except (InvalidObjectIdException, NotFoundException, BadRequestException):
            raise
        except Exception as e:
            logger.error(f"Error updating user with ID {user_id}: {e}")
            raise DatabaseException(operation="update_user_put")


    def update_user_patch(self, user_id: str, patch_data: Dict[str, Any]) -> None:
        """
        Performs a partial update (PATCH) on a user document.
        Strictly excludes the 'email' field. Hashes password if provided.

        Args:
            user_id (str): The string representation of the document ObjectId.
            patch_data (Dict[str, Any]): The subset of fields to update.

        Raises:
            InvalidObjectIdException: If user_id is not a valid ObjectId format.
            NotFoundException: If no user exists with the given ID.
            BadRequestException: If patch_data is empty after stripping protected fields.
            DatabaseException: If a database error occurs.
        """
        try:
            object_id = ObjectId(user_id)
        except InvalidId:
            logger.warning(f"Invalid ObjectId format provided for PATCH update: {user_id}")
            raise InvalidObjectIdException(field="user_id", value=user_id)
        
        try:
            if "email" in patch_data:
                patch_data.pop("email")
                logger.debug(f"Stripped immutable 'email' field from PATCH payload for ID: {user_id}")

            if "hash_password" in patch_data:
                patch_data["hash_password"] = get_password_hash(patch_data["hash_password"])

            if not patch_data:
                raise BadRequestException(message="No valid fields provided for update", error_code="EMPTY_UPDATE")

            patch_data["updated_at"] = datetime.utcnow()

            result = self.collection.update_one(
                {"_id": object_id},
                {"$set": patch_data}
            )
            
            if result.matched_count == 0:
                logger.info(f"User not found with ID: {user_id}")
                raise NotFoundException(resource="User", identifier=user_id)
            
            logger.info(f"Successfully patched user with ID: {user_id}")
            
        except (InvalidObjectIdException, NotFoundException, BadRequestException):
            raise
        except Exception as e:
            logger.error(f"Error patching user with ID {user_id}: {e}")
            raise DatabaseException(operation="update_user_patch")

    def delete_user(self, user_id: str) -> None:
        """
        Permanently removes a user document from the database.

        Args:
            user_id (str): The string representation of the document ObjectId.

        Raises:
            InvalidObjectIdException: If user_id is not a valid ObjectId format.
            NotFoundException: If no user exists with the given ID.
            DatabaseException: If a database error occurs.
        """
        try:
            object_id = ObjectId(user_id)
        except InvalidId:
            logger.warning(f"Invalid ObjectId format provided for deletion: {user_id}")
            raise InvalidObjectIdException(field="user_id", value=user_id)
        
        try:
            result = self.collection.delete_one({"_id": object_id})
            
            if result.deleted_count == 0:
                logger.info(f"User not found with ID: {user_id}")
                raise NotFoundException(resource="User", identifier=user_id)
            
            logger.info(f"Successfully deleted user with ID: {user_id}")
        
        except NotFoundException:
            raise
        
        except Exception as e:
            logger.error(f"Error deleting user with ID {user_id}: {e}")
            raise DatabaseException(operation="delete_user")


# Singleton instantiation for route injection
user_service = UserCRUDService()

