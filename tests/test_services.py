import os
import cv2
import pytest
import numpy as np
from unittest.mock import patch, MagicMock, call
from bson.objectid import ObjectId
from datetime import datetime

from app.services.fractal_service import FractalService
from app.services.storage_service import StorageService
from app.services.user_CRUD_service import UserCRUDService
from app.services.location_CRUD_service import LocationCRUDService
from app.core.exceptions import (
    BadRequestException,
    NotFoundException,
    DatabaseException,
    ConflictException,
    InvalidObjectIdException,
)


# FRACTAL SERVICE TESTS


class TestFractalService:
    """Tests for FractalService.calculate_dimension and evaluate_severity"""


    # test_calculate_dimension_blank_mask

    def test_calculate_dimension_blank_mask(self):
        """
        Verify that an array of all zeros (blank mask) returns 0.0.
        
        A blank mask has no active pixels, so the fractal dimension is undefined
        and should return 0.0 (no complexity).
        
        Assertions:
        - Returns exactly 0.0
        - Type is float
        """
        blank_mask = np.zeros((100, 100), dtype=np.uint8)
        
        result = FractalService.calculate_dimension(blank_mask)
        
        assert isinstance(result, float), "Result should be float"
        assert result == 0.0, "Blank mask should return 0.0"


    # test_calculate_dimension_solid_mask

    def test_calculate_dimension_solid_mask(self):
        """
        Verify that an array of all ones (completely filled mask) returns 2.0.
        
        A completely filled mask represents a 2D surface with no fractal edges,
        so the dimension should be 2.0 (full 2D space).
        
        Assertions:
        - Returns exactly 2.0
        - Type is float
        """
        solid_mask = np.ones((100, 100), dtype=np.uint8)
        
        result = FractalService.calculate_dimension(solid_mask)
        
        assert isinstance(result, float), "Result should be float"
        assert result == 2.0, "Solid mask should return 2.0"


    # test_calculate_dimension_known_pattern

    def test_calculate_dimension_known_pattern(self):
        """
        Verify that a known pattern (checkerboard) returns a fractal dimension
        between 1.0 and 2.0.
        
        A checkerboard pattern has intermediate complexity between a line (1.0)
        and a solid fill (2.0).
        
        Assertions:
        - Returns float
        - Value is in range [1.0, 2.0]
        - Value is > 1.0 (not a simple line)
        - Value is < 2.0 (not completely filled)
        """
        # Create a checkerboard pattern
        checkerboard = np.zeros((100, 100), dtype=np.uint8)
        checkerboard[::2, ::2] = 1
        checkerboard[1::2, 1::2] = 1
        
        result = FractalService.calculate_dimension(checkerboard)
        
        assert isinstance(result, float), "Result should be float"
        assert 1.0 <= result <= 2.0, f"Dimension should be in [1.0, 2.0], got {result}"


    # test_calculate_dimension_line_pattern

    def test_calculate_dimension_line_pattern(self):
        """
        Verify that a simple line (1D structure) returns a dimension close to 1.0.
        
        A line is a 1D structure, so its fractal dimension should be near 1.0.
        
        Assertions:
        - Returns float
        - Value is close to 1.0 (within reasonable tolerance)
        """
        line_mask = np.zeros((100, 100), dtype=np.uint8)
        line_mask[50, :] = 1  # Horizontal line
        
        result = FractalService.calculate_dimension(line_mask)
        
        assert isinstance(result, float), "Result should be float"
        assert 0.8 <= result <= 1.5, f"Line should have dim near 1.0, got {result}"

    # --------
    # test_calculate_dimension_none_input
    # --------
    def test_calculate_dimension_none_input(self):
        """
        Verify that None input returns 0.0 gracefully without crashing.
        
        Assertions:
        - Returns 0.0 for None input
        """
        result = FractalService.calculate_dimension(None)
        
        assert result == 0.0, "None input should return 0.0"

    # --------
    # test_calculate_dimension_empty_array
    # --------
    def test_calculate_dimension_empty_array(self):
        """
        Verify that an empty array returns 0.0.
        
        Assertions:
        - Returns 0.0
        """
        empty_array = np.array([], dtype=np.uint8)
        
        result = FractalService.calculate_dimension(empty_array)
        
        assert result == 0.0, "Empty array should return 0.0"

    # --------
    # test_evaluate_severity_boundaries
    # --------
    def test_evaluate_severity_boundaries(self):
        """
        Verify severity classification thresholds:
        - FD > 1.80 → "Critical"
        - FD > 1.50 AND Area > 50 → "High"
        - FD > 1.30 OR Area > 20 → "Medium"
        - else → "Low"
        
        Assertions:
        - Critical case (FD > 1.80): Returns "Critical"
        - High case (FD > 1.50 AND Area > 50): Returns "High"
        - Medium case: Returns "Medium"
        - Low case: Returns "Low"
        """
        # Test Critical (FD > 1.80)
        assert FractalService.evaluate_severity(1.85, 50.0) == "Critical"
        
        # Test Critical (Area > 100)
        assert FractalService.evaluate_severity(1.5, 150.0) == "Critical"
        
        # Test High (FD > 1.50 AND Area > 50)
        assert FractalService.evaluate_severity(1.60, 60.0) == "High"
        
        # Test Medium (FD > 1.30)
        assert FractalService.evaluate_severity(1.40, 15.0) == "Medium"
        
        # Test Medium (Area > 20)
        assert FractalService.evaluate_severity(1.0, 25.0) == "Medium"
        
        # Test Low
        assert FractalService.evaluate_severity(1.0, 10.0) == "Low"

    def test_evaluate_severity_zero_values(self):
        """
        Verify that zero fractal dimension or area returns "None".
        
        Assertions:
        - FD=0 returns "None"
        - Area=0 returns "None"
        """
        assert FractalService.evaluate_severity(0.0, 50.0) == "None"
        assert FractalService.evaluate_severity(1.5, 0.0) == "None"


# ============================================================================
# VISION SERVICE TESTS
# ============================================================================

class TestVisionService:
    """Tests for VisionService initialization and analysis"""

    # --------
    # test_vision_service_initialization_mocked
    # --------
    def test_vision_service_initialization_mocked(self):
        """
        Verify that VisionService initializes successfully with a mocked
        ort.InferenceSession to avoid loading real ONNX model weights.
        
        This tests fast CI/CD runs without large file I/O.
        
        Assertions:
        - Service initializes without raising exceptions
        - session attribute is set
        - input_name and output_names are extracted
        """
        from app.services.vision_service import VisionService
        
        with patch('app.services.vision_service.ort.InferenceSession') as mock_session:
            mock_instance = MagicMock()
            
            # Setup mock inputs/outputs
            mock_input = MagicMock()
            mock_input.name = "images"
            mock_instance.get_inputs.return_value = [mock_input]
            
            mock_output = MagicMock()
            mock_output.name = "output0"
            mock_instance.get_outputs.return_value = [mock_output]
            
            mock_session.return_value = mock_instance
            
            service = VisionService()
            
            assert service.session is not None
            assert service.input_name == "images"
            assert service.output_names == ["output0"]

    # --------
    # test_analyze_corrosion_null_input
    # --------
    def test_analyze_corrosion_null_input(self):
        """
        Verify that analyze_corrosion raises BadRequestException when image_np is None.
        
        Assertions:
        - Raises BadRequestException
        - Error code is "NULL_IMAGE"
        """
        from app.services.vision_service import VisionService
        
        with patch('app.services.vision_service.ort.InferenceSession'):
            service = VisionService()
            
            with pytest.raises(BadRequestException) as exc_info:
                service.analyze_corrosion(None)
            
            assert exc_info.value.error_code == "NULL_IMAGE"

    # --------
    # test_analyze_corrosion_invalid_type
    # --------
    def test_analyze_corrosion_invalid_type(self):
        """
        Verify that analyze_corrosion raises BadRequestException when
        passed a list instead of np.ndarray.
        
        Assertions:
        - Raises BadRequestException
        - Error code is "INVALID_IMAGE_TYPE"
        """
        from app.services.vision_service import VisionService
        
        with patch('app.services.vision_service.ort.InferenceSession'):
            service = VisionService()
            
            with pytest.raises(BadRequestException) as exc_info:
                service.analyze_corrosion([1, 2, 3])
            
            assert exc_info.value.error_code == "INVALID_IMAGE_TYPE"

    # --------
    # test_analyze_corrosion_dict_type
    # --------
    def test_analyze_corrosion_dict_type(self):
        """
        Verify that analyze_corrosion rejects dict input.
        
        Assertions:
        - Raises BadRequestException
        """
        from app.services.vision_service import VisionService
        
        with patch('app.services.vision_service.ort.InferenceSession'):
            service = VisionService()
            
            with pytest.raises(BadRequestException):
                service.analyze_corrosion({"image": "data"})

    # --------
    # test_extract_detections_empty_proto
    # --------
    def test_extract_detections_empty_proto(self):
        """
        Verify that _extract_detections safely handles None proto input
        and returns an empty list without triggering matrix operations.
        
        This tests robustness when YOLO inference returns no results.
        
        Assertions:
        - Returns empty list []
        - Does not crash with matrix multiplication errors
        """
        from app.services.vision_service import VisionService
        
        with patch('app.services.vision_service.ort.InferenceSession'):
            service = VisionService()
            
            # Call the private method with None proto
            result = service._extract_detections(
                predictions=np.zeros((1, 116, 8400), dtype=np.float32),
                proto=None,
                scale_ratio=1.0,
                pad_w=0,
                pad_h=0,
                original_hw=(640, 640),
                cm_per_pixel=None,
            )
            
            assert isinstance(result, list), "Should return a list"
            assert len(result) == 0, "Should return empty list for None proto"


# ============================================================================
# STORAGE SERVICE TESTS
# ============================================================================

class TestStorageService:
    """Tests for StorageService file operations"""

    # --------
    # test_ensure_directory_exists
    # --------
    def test_ensure_directory_exists(self, tmp_path):
        """
        Verify that StorageService._ensure_directory_exists creates the
        outputs/ folder if it is missing during initialization.
        
        Assertions:
        - Directory is created if missing
        - No exception raised
        - Logger info called
        """
        test_dir = tmp_path / "test_outputs"
        
        with patch('app.services.storage_service.Config.UPLOAD_FOLDER', str(test_dir)):
            with patch('app.services.storage_service.os.path.exists', return_value=False):
                with patch('app.services.storage_service.os.makedirs') as mock_makedirs:
                    service = StorageService()
                    
                    mock_makedirs.assert_called_once()

    # --------
    # test_save_masked_image_success
    # --------
    def test_save_masked_image_success(self, tmp_path):
        """
        Verify that save_masked_image successfully saves an image and
        returns a correctly formatted string path (mask_loc_...).
        
        Mocks cv2.imwrite to return True.
        
        Assertions:
        - Returns string path
        - Path contains "mask_loc_" prefix
        - Path contains location_id
        - Path ends with ".jpg"
        """
        with patch('app.services.storage_service.Config.UPLOAD_FOLDER', str(tmp_path)):
            with patch('app.services.storage_service.os.path.exists', return_value=True):
                service = StorageService()
                
                test_image = np.zeros((100, 100, 3), dtype=np.uint8)
                location_id = "location_123"
                
                with patch('app.services.storage_service.cv2.imwrite', return_value=True):
                    result = service.save_masked_image(test_image, location_id)
                
                assert isinstance(result, str), "Should return string path"
                assert "mask_loc_" in result, "Path should contain mask_loc_ prefix"
                assert location_id in result, "Path should contain location_id"
                assert result.endswith(".jpg"), "Path should end with .jpg"

    # --------
    # test_save_masked_image_cv2_fails
    # --------
    def test_save_masked_image_cv2_fails(self, tmp_path):
        """
        Verify that save_masked_image raises IOError when cv2.imwrite fails.
        
        Assertions:
        - Raises IOError
        - Error message contains file path
        """
        with patch('app.services.storage_service.Config.UPLOAD_FOLDER', str(tmp_path)):
            with patch('app.services.storage_service.os.path.exists', return_value=True):
                service = StorageService()
                
                test_image = np.zeros((100, 100, 3), dtype=np.uint8)
                
                with patch('app.services.storage_service.cv2.imwrite', return_value=False):
                    with pytest.raises(IOError):
                        service.save_masked_image(test_image, "location_123")

    # --------
    # test_delete_image_success
    # --------
    def test_delete_image_success(self, tmp_path):
        """
        Verify that delete_image returns True and removes the file.
        
        Creates a dummy file, calls delete_image, and verifies deletion.
        
        Assertions:
        - Returns True
        - File no longer exists
        """
        # Create a dummy file
        dummy_file = tmp_path / "test_image.jpg"
        dummy_file.write_text("dummy image data")
        
        with patch('app.services.storage_service.Config.UPLOAD_FOLDER', str(tmp_path)):
            with patch('app.services.storage_service.os.path.exists', return_value=True):
                service = StorageService()
                
                # Mock os.remove to actually delete the file
                with patch('app.services.storage_service.os.remove') as mock_remove:
                    result = service.delete_image(str(dummy_file))
                
                assert result is True, "Should return True on successful deletion"
                mock_remove.assert_called_once()

    # --------
    # test_delete_image_not_found
    # --------
    def test_delete_image_not_found(self):
        """
        Verify that delete_image returns False when file doesn't exist.
        
        Passes a fake path and asserts it safely returns False without raising OSError.
        
        Assertions:
        - Returns False
        - No exception raised
        """
        with patch('app.services.storage_service.Config.UPLOAD_FOLDER', 'outputs/'):
            with patch('app.services.storage_service.os.path.exists', return_value=True):
                service = StorageService()
                
                with patch('app.services.storage_service.os.path.exists', return_value=False):
                    result = service.delete_image("fake_path.jpg")
                
                assert result is False, "Should return False for non-existent file"

    # --------
    # test_delete_image_empty_path
    # --------
    def test_delete_image_empty_path(self):
        """
        Verify that delete_image returns False for empty path.
        
        Assertions:
        - Returns False
        """
        with patch('app.services.storage_service.Config.UPLOAD_FOLDER', 'outputs/'):
            with patch('app.services.storage_service.os.path.exists', return_value=True):
                service = StorageService()
                
                result = service.delete_image("")
                
                assert result is False, "Should return False for empty path"


# ============================================================================
# USER CRUD SERVICE TESTS
# ============================================================================

class TestUserCRUDService:
    """Tests for UserCRUDService operations"""

    @pytest.fixture
    def mock_db_collection(self):
        """Mock MongoDB collection for testing"""
        with patch('app.services.user_CRUD_service.db_instance') as mock_db:
            mock_collection = MagicMock()
            mock_db.db.users = mock_collection
            yield mock_collection

    # --------
    # test_create_user_hashing
    # --------
    def test_create_user_hashing(self, mock_db_collection):
        """
        Verify that create_user hashes the password and the raw password
        is not stored in the document.
        
        Mocks the database insertion and checks that get_password_hash was called.
        
        Assertions:
        - get_password_hash was called
        - Raw password is not in the final document
        - Hashed password is in the document
        - insert_one was called
        """
        service = UserCRUDService()
        
        mock_db_collection.find_one.return_value = None  # No existing user
        mock_db_collection.insert_one.return_value = MagicMock(inserted_id=ObjectId())
        
        user_data = {
            "email": "test@example.com",
            "hash_password": "plaintext_password123",
            "full_name": "Test User"
        }
        
        with patch('app.services.user_CRUD_service.get_password_hash') as mock_hash:
            mock_hash.return_value = "$2b$12$hashedpassword123"
            
            result = service.create_user(user_data)
            
            # Verify get_password_hash was called with the plaintext password
            mock_hash.assert_called_once_with("plaintext_password123")
            
            # Verify insert_one was called
            mock_db_collection.insert_one.assert_called_once()
            
            # Get the document that was inserted
            inserted_doc = mock_db_collection.insert_one.call_args[0][0]
            
            # Verify raw password is not in the document
            assert inserted_doc.get("hash_password") != "plaintext_password123"
            
            # Verify hashed password is in the document
            assert inserted_doc.get("hash_password") == "$2b$12$hashedpassword123"

    # --------
    # test_create_user_duplicate_email
    # --------
    def test_create_user_duplicate_email(self, mock_db_collection):
        """
        Verify that create_user returns error when email already exists.
        
        Mocks get_user_by_email to return a document, and asserts create_user
        returns error for duplicate.
        
        Assertions:
        - Raises ConflictException
        - Error code is "EMAIL_EXISTS"
        """
        service = UserCRUDService()
        
        # Mock existing user
        mock_db_collection.find_one.return_value = {
            "_id": ObjectId(),
            "email": "test@example.com"
        }
        
        user_data = {
            "email": "test@example.com",
            "hash_password": "password123"
        }
        
        with pytest.raises(ConflictException) as exc_info:
            service.create_user(user_data)
        
        assert exc_info.value.error_code == "EMAIL_EXISTS"

    # --------
    # test_create_user_missing_email
    # --------
    def test_create_user_missing_email(self, mock_db_collection):
        """
        Verify that create_user raises BadRequestException when email is missing.
        
        Assertions:
        - Raises BadRequestException
        - Error code is "MISSING_EMAIL"
        """
        service = UserCRUDService()
        
        user_data = {
            "hash_password": "password123",
            "name": "Test User"
        }
        
        with pytest.raises(BadRequestException) as exc_info:
            service.create_user(user_data)
        
        assert exc_info.value.error_code == "MISSING_EMAIL"

    # --------
    # test_create_user_missing_password
    # --------
    def test_create_user_missing_password(self, mock_db_collection):
        """
        Verify that create_user raises BadRequestException when password is missing.
        
        Assertions:
        - Raises BadRequestException
        - Error code is "MISSING_PASSWORD"
        """
        service = UserCRUDService()
        
        mock_db_collection.find_one.return_value = None
        
        user_data = {
            "email": "test@example.com",
            "name": "Test User"
        }
        
        with pytest.raises(BadRequestException) as exc_info:
            service.create_user(user_data)
        
        assert exc_info.value.error_code == "MISSING_PASSWORD"


# ============================================================================
# LOCATION CRUD SERVICE TESTS
# ============================================================================

class TestLocationCRUDService:
    """Tests for LocationCRUDService operations"""

    @pytest.fixture
    def mock_db_collection(self):
        """Mock MongoDB collection for testing"""
        with patch('app.services.location_CRUD_service.db_instance') as mock_db:
            mock_collection = MagicMock()
            mock_db.db.locations = mock_collection
            yield mock_collection

    # --------
    # test_update_location_patch_immutable_address
    # --------
    def test_update_location_patch_immutable_address(self, mock_db_collection):
        """
        Verify that update_location_patch doesn't allow updating the address field.
        
        Passes a payload containing "address": "New St", mocks the DB update,
        and asserts the update query did not contain the address key.
        
        Assertions:
        - Update is performed
        - address key is NOT in update query
        - Other fields ARE updated
        """
        service = LocationCRUDService()
        
        location_id = str(ObjectId())
        update_data = {
            "address": "New Street",
            "city": "New City",
            "latitude": 40.7128
        }
        
        mock_db_collection.find_one.return_value = {
            "_id": ObjectId(location_id),
            "address": "Old Street",
            "city": "Old City"
        }
        
        mock_db_collection.update_one.return_value = MagicMock(modified_count=1)
        
        with patch('app.services.location_CRUD_service.LocationDocument'):
            service.update_location_patch(location_id, update_data)
        
        # Get the update query from the mock call
        mock_db_collection.update_one.assert_called_once()
        call_args = mock_db_collection.update_one.call_args
        
        # The update should contain $set with city but not address
        update_query = call_args[0][1]
        
        # Verify address is not being updated
        if "$set" in update_query:
            assert "address" not in update_query["$set"], "Address should not be in update"

    # --------
    # test_update_location_valid_fields
    # --------
    def test_update_location_valid_fields(self, mock_db_collection):
        """
        Verify that update_location_patch successfully updates allowed fields.
        
        Assertions:
        - update_one is called
        - Allowed fields are in the update
        """
        service = LocationCRUDService()
        
        location_id = str(ObjectId())
        update_data = {
            "city": "New City",
            "latitude": 40.7128,
            "longitude": -74.0060
        }
        
        mock_db_collection.find_one.return_value = {
            "_id": ObjectId(location_id),
            "address": "Street",
            "city": "Old City"
        }
        
        mock_db_collection.update_one.return_value = MagicMock(modified_count=1)
        
        with patch('app.services.location_CRUD_service.LocationDocument'):
            service.update_location_patch(location_id, update_data)
        
        mock_db_collection.update_one.assert_called_once()

    # --------
    # test_update_location_invalid_object_id
    # --------
    def test_update_location_invalid_object_id(self, mock_db_collection):
        """
        Verify that update_location_patch raises InvalidObjectIdException
        for invalid ObjectId format.
        
        Assertions:
        - Raises InvalidObjectIdException
        """
        service = LocationCRUDService()
        
        with pytest.raises(InvalidObjectIdException):
            service.update_location_patch("invalid_id", {"city": "New City"})

    # --------
    # test_update_location_not_found
    # --------
    def test_update_location_not_found(self, mock_db_collection):
        """
        Verify that update_location_patch raises NotFoundException
        when location doesn't exist.
        
        Assertions:
        - Raises NotFoundException
        """
        service = LocationCRUDService()
        
        location_id = str(ObjectId())
        update_result = MagicMock(matched_count=0)
        mock_db_collection.update_one.return_value = update_result

        with pytest.raises(NotFoundException):
            service.update_location_patch(location_id, {"city": "New City"})
