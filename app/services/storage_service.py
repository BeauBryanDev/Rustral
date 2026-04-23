import os
import cv2
import uuid
import logging
import numpy as np
from datetime import datetime
from typing import Optional

from app.core.exceptions import (
    NotFoundException,
    InternalServerException,
    DatabaseException,
    BadRequestException,
)

from app.config import Config

logger = logging.getLogger(__name__)


class StorageService:
    """
    Service responsible for managing local file storage operations.
    Handles the safe writing and deletion of post-processed inference images.
    """
    def __init__(self):
        """
        Initializes the storage service and ensures the base directory exists.
        Defaults to 'outputs/' if not explicitly set in the application configuration.
        """
        self.base_directory = getattr(Config, 'UPLOAD_FOLDER', 'outputs/')
        self._ensure_directory_exists()


    def _ensure_directory_exists(self) -> None:
        """
        Creates the target storage directory if it is not present on the filesystem.
        Raises an exception if the application lacks file system permissions.
        """
        if not os.path.exists(self.base_directory):
            
            try:
                os.makedirs(self.base_directory)
                
                logger.info(f"Storage directory initialized at: {self.base_directory}")
                
            except OSError as error:
                
                logger.critical(f"Failed to create storage directory {self.base_directory}. Error: {error}")
                
                raise InternalServerException(
                    message="Failed to initialize storage directory",
                    error_code="STORAGE_INIT_FAILED"
                )
                

    def save_masked_image(self, image_array: np.ndarray, location_id: str) -> str:
        """
        Saves a post-processed OpenCV image array to the disk with a unique filename.

        Args:
            image_array (np.ndarray): The BGR image array containing the drawn corrosion masks.
            location_id (str): The string identifier of the location, used for prefixing.

        Returns:
            str: The relative file path where the image was successfully saved.

        Raises:
            IOError: If the underlying OpenCV write operation fails.
        """
        if image_array is None or image_array.size == 0:
            
            raise ValueError("Provided image array is empty or invalid.")

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        unique_suffix = str(uuid.uuid4())[:8]
        
        filename = f"mask_loc_{location_id}_{timestamp}_{unique_suffix}.jpg"
        
        file_path = os.path.join(self.base_directory, filename)

        # OpenCV imwrite returns True on success, False otherwise
        write_success = cv2.imwrite(file_path, image_array)
        
        if not write_success:
            
            logger.error(f"cv2.imwrite failed for path: {file_path}")
            
            raise IOError(f"Could not write image data to {file_path}")

        logger.info(f"Post-processed mask image saved successfully: {file_path}")
        
        return file_path


    def delete_image(self, file_path: str) -> bool:
        """
        Safely removes an image file from the storage directory.

        Args:
            file_path (str): The relative or absolute path to the file.

        Returns:
            bool: True if deleted successfully, False if the file did not exist or failed.
        """
        if not file_path:
            
            return False

        try:
            if os.path.exists(file_path):
                
                os.remove(file_path)
                
                logger.info(f"Successfully deleted image file: {file_path}")
                
                return True
            
            else:
                
                logger.warning(f"Attempted to delete non-existent file: {file_path}")
                
                return False
            
        except OSError as error:
            
            logger.error(f"Failed to delete file {file_path}. Error: {error}")
            
            return False
        
        
# Singleton instantiation for service injection
storage_service = StorageService()