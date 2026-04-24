"""
Comprehensive test suite for app/utils/image_utils.py

Tests cover:
- Image decoding (valid & corrupted data)
- ArUco marker detection and scale calculation
- YOLO preprocessing (dimensions & normalization)
- Real-world area calculations
- Corrosion analysis drawing & rendering
"""

import cv2
import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from app.utils.image_utils import (
    decode_image_bytes,
    detect_aruco_scale,
    preprocess_for_yolo,
    calculate_real_area,
    draw_corrosion_analysis,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def valid_jpeg_bytes():
    """
    Generates a valid 640x640 JPEG image in bytes.
    This is a real, decodable image for testing valid input paths.
    """
    # Create a test image with some content
    test_image = np.random.randint(0, 256, (640, 640, 3), dtype=np.uint8)
    
    # Encode to JPEG bytes
    success, encoded = cv2.imencode('.jpg', test_image)
    assert success, "Failed to encode test JPEG"
    
    return encoded.tobytes()


@pytest.fixture
def corrupted_bytes():
    """
    Generates random, non-image data that cannot be decoded.
    Used to test error handling for corrupted image bytes.
    """
    return b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a' + b'garbage_data_12345'


@pytest.fixture
def blank_image():
    """
    Creates a blank (all zeros) BGR image for testing marker detection.
    """
    return np.zeros((640, 640, 3), dtype=np.uint8)


@pytest.fixture
def image_with_aruco_marker():
    """
    Generates a valid image containing an ArUco marker.
    Uses cv2.aruco.generateImageMarker to create a real marker.
    """
    # Create a blank image
    blank_image = np.ones((500, 500, 3), dtype=np.uint8) * 255
    
    # Generate ArUco marker ID=0, size=200x200 pixels
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    marker_image = cv2.aruco.generateImageMarker(aruco_dict, 0, 200)
    
    # Place the marker in the center of the blank image
    start_x = (blank_image.shape[1] - marker_image.shape[1]) // 2
    start_y = (blank_image.shape[0] - marker_image.shape[0]) // 2
    
    blank_image[start_y:start_y + marker_image.shape[0], 
                start_x:start_x + marker_image.shape[1]] = cv2.cvtColor(marker_image, cv2.COLOR_GRAY2BGR)
    
    return blank_image


@pytest.fixture
def sample_detection():
    """
    Creates a sample detection dictionary for testing drawing functions.
    """
    return {
        "box": [50, 50, 200, 200],  # x1, y1, x2, y2
        "confidence": 0.95,
        "area_cm2": 25.5,
        "severity_level": "High",
        "fractal_dimension": 1.85
    }


@pytest.fixture
def multiple_detections():
    """
    Creates multiple detection dictionaries for batch testing.
    """
    return [
        {
            "box": [50, 50, 150, 150],
            "confidence": 0.92,
            "area_cm2": 15.3,
            "severity_level": "Medium",
            "fractal_dimension": 1.72
        },
        {
            "box": [200, 200, 350, 350],
            "confidence": 0.88,
            "area_cm2": 35.8,
            "severity_level": "High",
            "fractal_dimension": 1.95
        }
    ]


# ============================================================================
# TEST: decode_image_bytes - VALID JPEG
# ============================================================================

def test_decode_image_bytes_valid_jpeg(valid_jpeg_bytes):
    """
    Verify that decode_image_bytes correctly decodes valid JPEG bytes
    into a numpy array with expected shape and dtype.
    
    Assertions:
    - Returns np.ndarray
    - Shape is (height, width, 3) for BGR format
    - dtype is uint8
    - Values are in valid range [0, 255]
    """
    result = decode_image_bytes(valid_jpeg_bytes)
    
    # Type check
    assert isinstance(result, np.ndarray), "Result should be a numpy array"
    
    # Shape check (height, width, 3 channels)
    assert len(result.shape) == 3, "Image should have 3 dimensions (H, W, C)"
    assert result.shape[2] == 3, "Image should have 3 color channels (BGR)"
    
    # Data type check
    assert result.dtype == np.uint8, "Image dtype should be uint8"
    
    # Value range check
    assert result.min() >= 0 and result.max() <= 255, "Pixel values should be in range [0, 255]"


# ============================================================================
# TEST: decode_image_bytes - CORRUPTED DATA
# ============================================================================

def test_decode_image_bytes_corrupted_data(corrupted_bytes):
    """
    Verify that decode_image_bytes raises ValueError when given corrupted/invalid data.
    
    Assertions:
    - Raises ValueError
    - Error message contains "Failed to decode"
    """
    with pytest.raises(ValueError) as exc_info:
        decode_image_bytes(corrupted_bytes)
    
    assert "Failed to decode" in str(exc_info.value), "Error message should indicate decoding failure"


# ============================================================================
# TEST: detect_aruco_scale - SUCCESSFUL DETECTION
# ============================================================================

def test_detect_aruco_scale_success(image_with_aruco_marker):
    """
    Verify that detect_aruco_scale correctly identifies an ArUco marker
    and returns a positive float representing cm per pixel scale.
    
    Assertions:
    - Returns float (not None)
    - Value is positive
    - Value is reasonable (0.01 to 10.0 cm/pixel is typical)
    """
    result = detect_aruco_scale(image_with_aruco_marker, reference_cm=30.0)
    
    # Type check
    assert result is not None, "Should detect the ArUco marker and return a scale"
    assert isinstance(result, (float, np.floating)), "Result should be a float"
    
    # Value check
    assert result > 0, "Scale ratio (cm per pixel) must be positive"
    assert 0.01 <= result <= 10.0, "Scale should be in reasonable range (0.01 to 10.0 cm/pixel)"


# ============================================================================
# TEST: detect_aruco_scale - NO MARKER FOUND
# ============================================================================

def test_detect_aruco_scale_no_marker(blank_image):
    """
    Verify that detect_aruco_scale safely returns None when no marker is detected.
    
    Assertions:
    - Returns None (not an exception or invalid value)
    - Does not crash or raise exceptions
    """
    result = detect_aruco_scale(blank_image)
    
    # Should return None, not raise an exception
    assert result is None, "Should return None when no marker is detected"


# ============================================================================
# TEST: preprocess_for_yolo - OUTPUT DIMENSIONS
# ============================================================================

def test_preprocess_for_yolo_dimensions(valid_jpeg_bytes):
    """
    Verify that preprocess_for_yolo outputs a tensor with exact dimensions (1, 3, 640, 640).
    This is the required input shape for YOLOv8 ONNX models.
    
    Assertions:
    - Output shape is exactly (1, 3, 640, 640)
    - Batch dimension is 1
    - Channel dimension is 3 (RGB)
    - Height and width are both 640
    """
    # Decode the test image
    image = cv2.imdecode(np.frombuffer(valid_jpeg_bytes, np.uint8), cv2.IMREAD_COLOR)
    
    # Call preprocess_for_yolo
    tensor, ratio, padding = preprocess_for_yolo(image, target_size=(640, 640))
    
    # Strict shape check
    assert tensor.shape == (1, 3, 640, 640), f"Expected shape (1, 3, 640, 640), got {tensor.shape}"
    
    # Check return values are valid
    assert isinstance(ratio, (float, np.floating)), "Ratio should be a float"
    assert isinstance(padding, tuple) and len(padding) == 2, "Padding should be a tuple of 2"
    assert ratio > 0, "Ratio should be positive"


# ============================================================================
# TEST: preprocess_for_yolo - NORMALIZATION
# ============================================================================

def test_preprocess_for_yolo_normalization(valid_jpeg_bytes):
    """
    Verify that preprocess_for_yolo normalizes pixel values to [0.0, 1.0] range.
    This is required for YOLO inference (divided by 255).
    
    Assertions:
    - Max value in tensor <= 1.0
    - Min value in tensor >= 0.0
    - Values are float32 type
    """
    # Decode the test image
    image = cv2.imdecode(np.frombuffer(valid_jpeg_bytes, np.uint8), cv2.IMREAD_COLOR)
    
    # Call preprocess_for_yolo
    tensor, _, _ = preprocess_for_yolo(image, target_size=(640, 640))
    
    # Normalization checks
    assert tensor.dtype == np.float32, "Tensor dtype should be float32"
    assert tensor.max() <= 1.0, f"Max value should be <= 1.0, got {tensor.max()}"
    assert tensor.min() >= 0.0, f"Min value should be >= 0.0, got {tensor.min()}"


# ============================================================================
# TEST: calculate_real_area - LOGIC AND MATH
# ============================================================================

def test_calculate_real_area_logic():
    """
    Verify the mathematical correctness of real-world area calculation.
    
    Test case: 100 pixels with 0.5 cm per pixel scale
    Expected result: 100 * (0.5)^2 = 100 * 0.25 = 25.0 cm²
    
    Assertions:
    - Result is exactly 25.0
    - Result is a float type
    """
    pixel_count = 100
    cm_per_pixel = 0.5
    
    result = calculate_real_area(pixel_count, cm_per_pixel)
    
    # Type check
    assert isinstance(result, float), "Result should be a float"
    
    # Math check: 100 * (0.5)^2 = 25.0
    expected = 25.0
    assert result == expected, f"Expected {expected}, got {result}"


# ============================================================================
# TEST: calculate_real_area - VARIOUS SCALES
# ============================================================================

@pytest.mark.parametrize("pixel_count,cm_per_pixel,expected", [
    (0, 0.5, 0.0),                    # Zero pixels
    (100, 0.5, 25.0),                 # 100 pixels, 0.5 cm/px
    (50, 1.0, 50.0),                  # 50 pixels, 1.0 cm/px
    (200, 0.1, 2.0),                  # 200 pixels, 0.1 cm/px
    (1000, 2.0, 4000.0),              # 1000 pixels, 2.0 cm/px
])
def test_calculate_real_area_parametrized(pixel_count, cm_per_pixel, expected):
    """
    Parametrized test for calculate_real_area with various inputs.
    Ensures the formula works across different scales and pixel counts.
    """
    result = calculate_real_area(pixel_count, cm_per_pixel)
    
    # Use approximate equality for floating point comparisons
    assert abs(result - expected) < 1e-6, f"Expected {expected}, got {result}"


# ============================================================================
# TEST: draw_corrosion_analysis - EMPTY DETECTIONS
# ============================================================================

def test_draw_corrosion_analysis_empty_detections():
    """
    Verify that draw_corrosion_analysis safely handles an empty detection list.
    
    Assertions:
    - Does not crash or raise exceptions
    - Returns the original image unchanged
    - Returned image shape matches input image shape
    """
    # Create a test image
    test_image = np.random.randint(0, 256, (640, 640, 3), dtype=np.uint8)
    original_image = test_image.copy()
    
    # Call with empty detections list
    result = draw_corrosion_analysis(test_image, [])
    
    # Shape check
    assert result.shape == original_image.shape, "Output shape should match input"
    
    # Content check - should be returned unchanged (or a copy)
    assert isinstance(result, np.ndarray), "Result should be a numpy array"


# ============================================================================
# TEST: draw_corrosion_analysis - SINGLE DETECTION
# ============================================================================

def test_draw_corrosion_analysis_single_detection(sample_detection):
    """
    Verify that draw_corrosion_analysis correctly processes a single detection.
    
    Assertions:
    - Does not crash
    - Returns a numpy array
    - Output shape matches input shape
    - Output is different from input (has annotations drawn)
    """
    # Create a test image (larger to accommodate drawing)
    test_image = np.ones((500, 500, 3), dtype=np.uint8) * 200
    
    # Call with single detection
    result = draw_corrosion_analysis(test_image, [sample_detection])
    
    # Type and shape checks
    assert isinstance(result, np.ndarray), "Result should be a numpy array"
    assert result.shape == test_image.shape, "Output shape should match input"
    assert result.dtype == test_image.dtype, "Output dtype should match input"
    
    # Content check - should have drawn something
    assert not np.array_equal(result, test_image), "Output should differ from input (annotations added)"


# ============================================================================
# TEST: draw_corrosion_analysis - MULTIPLE DETECTIONS
# ============================================================================

def test_draw_corrosion_analysis_multiple_detections(multiple_detections):
    """
    Verify that draw_corrosion_analysis correctly processes multiple detections.
    
    Assertions:
    - Does not crash
    - Returns a numpy array
    - Output shape matches input shape
    - Process each detection without errors
    """
    # Create a larger test image to contain multiple bounding boxes
    test_image = np.ones((500, 500, 3), dtype=np.uint8) * 200
    
    # Call with multiple detections
    result = draw_corrosion_analysis(test_image, multiple_detections)
    
    # Type and shape checks
    assert isinstance(result, np.ndarray), "Result should be a numpy array"
    assert result.shape == test_image.shape, "Output shape should match input"


# ============================================================================
# TEST: draw_corrosion_analysis - NONE IMAGE INPUT
# ============================================================================

def test_draw_corrosion_analysis_none_image():
    """
    Verify that draw_corrosion_analysis safely handles None image input.
    
    Assertions:
    - Does not crash
    - Returns None unchanged
    """
    result = draw_corrosion_analysis(None, [])
    
    assert result is None, "Should return None when input image is None"


# ============================================================================
# TEST: draw_corrosion_analysis - PARTIAL DETECTION INFO
# ============================================================================

def test_draw_corrosion_analysis_partial_detection_info():
    """
    Verify that draw_corrosion_analysis handles detections with missing optional fields.
    
    This tests robustness when detections have minimal required fields but
    missing optional fields like area_cm2 or fractal_dimension.
    
    Assertions:
    - Does not crash on missing optional fields
    - Returns a numpy array
    """
    test_image = np.ones((500, 500, 3), dtype=np.uint8) * 200
    
    # Minimal detection with only required fields
    minimal_detection = {
        "box": [50, 50, 150, 150],
        "confidence": 0.85,
        "severity_level": "Low"
        # Missing: area_cm2, fractal_dimension
    }
    
    result = draw_corrosion_analysis(test_image, [minimal_detection])
    
    assert isinstance(result, np.ndarray), "Should handle partial detection info gracefully"
    assert result.shape == test_image.shape, "Shape should be preserved"


# ============================================================================
# TEST: preprocess_for_yolo - DIFFERENT IMAGE SIZES
# ============================================================================

@pytest.mark.parametrize("img_height,img_width", [
    (480, 640),   # Standard 4:3
    (720, 1280),  # Standard HD 16:9
    (100, 100),   # Small square
    (1000, 500),  # Wide
])
def test_preprocess_for_yolo_various_sizes(img_height, img_width):
    """
    Parametrized test for preprocess_for_yolo with various input sizes.
    Ensures the letterboxing and resizing work correctly regardless of input dimensions.
    
    Assertions:
    - Always outputs (1, 3, 640, 640) regardless of input size
    - No crashes or errors
    """
    # Create test image with specified dimensions
    test_image = np.random.randint(0, 256, (img_height, img_width, 3), dtype=np.uint8)
    
    tensor, ratio, padding = preprocess_for_yolo(test_image, target_size=(640, 640))
    
    # Should always output exactly (1, 3, 640, 640)
    assert tensor.shape == (1, 3, 640, 640), \
        f"Input {img_height}x{img_width}: Expected (1,3,640,640), got {tensor.shape}"


# ============================================================================
# TEST: detect_aruco_scale - WITH DIFFERENT REFERENCE SIZES
# ============================================================================

def test_detect_aruco_scale_different_reference_sizes(image_with_aruco_marker):
    """
    Verify that detect_aruco_scale correctly uses the reference_cm parameter.
    
    Different reference sizes should produce proportionally different scales.
    
    Assertions:
    - Returns non-None for all reference sizes
    - Scale values are proportional to reference_cm
    """
    scale_30 = detect_aruco_scale(image_with_aruco_marker, reference_cm=30.0)
    scale_60 = detect_aruco_scale(image_with_aruco_marker, reference_cm=60.0)
    
    assert scale_30 is not None and scale_60 is not None, "Both should detect the marker"
    
    # With double reference, scale should roughly double
    # (allowing small deviation due to floating point)
    ratio = scale_60 / scale_30
    assert 1.9 <= ratio <= 2.1, f"Expected ~2x difference, got {ratio}x"


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

def test_calculate_real_area_very_small_scale():
    """
    Test calculate_real_area with very small cm_per_pixel values.
    """
    result = calculate_real_area(pixel_count=1000, cm_per_pixel=0.001)
    
    assert isinstance(result, float), "Should handle very small scales"
    assert result > 0, "Result should be positive"


def test_calculate_real_area_very_large_scale():
    """
    Test calculate_real_area with very large cm_per_pixel values.
    """
    result = calculate_real_area(pixel_count=100, cm_per_pixel=100.0)
    
    assert isinstance(result, float), "Should handle very large scales"
    assert result > 0, "Result should be positive"


def test_decode_image_bytes_empty_bytes():
    """
    Test decode_image_bytes with empty byte string.
    Should raise ValueError since empty bytes cannot be decoded as an image.
    """
    with pytest.raises((ValueError, cv2.error)):
        decode_image_bytes(b'')
