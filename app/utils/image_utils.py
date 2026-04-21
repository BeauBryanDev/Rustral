import cv2
import numpy as np
from typing import Tuple, Optional, List


# Standard configuration for the physical ArUco marker
ARUCO_DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
ARUCO_PARAMS = cv2.aruco.DetectorParameters()
DEFAULT_REFERENCE_CM = 30.0


def decode_image_bytes(image_bytes: bytes) -> np.ndarray:
    """
    Decodes a raw byte stream into an OpenCV BGR numpy array.
    
    Args:
        image_bytes (bytes): The raw image data received from the HTTP request.
        
    Returns:
        np.ndarray: The decoded image array in BGR format.
        
    Raises:
        ValueError: If the image stream cannot be decoded.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        
        raise ValueError("Failed to decode image bytes into a valid array.")
        
    return img


def detect_aruco_scale(image: np.ndarray, reference_cm: float = DEFAULT_REFERENCE_CM) -> Optional[float]:
    """
    Detects an ArUco marker in the image and calculates the spatial scale ratio.
    
    Args:
        image (np.ndarray): The input image in BGR format.
        reference_cm (float): The known real-world width of the marker in centimeters.
        
    Returns:
        Optional[float]: The scale ratio (cm per pixel) if a marker is found, None otherwise.
    """
    detector = cv2.aruco.ArucoDetector(ARUCO_DICT, ARUCO_PARAMS)
    corners, ids, _ = detector.detectMarkers(image)
    
    if not corners or len(corners) == 0:
        
        return None
        
    # Extract the four corners of the first detected marker
    marker_corners = corners[0][0]
    
    # Calculate the perimeter of the marker in pixels
    perimeter = cv2.arcLength(marker_corners, closed=True)  # Closed polygon
    
    # Calculate the average side length in pixels (perimeter / 4)
    avg_side_pixels = perimeter / 4.0
    
    if avg_side_pixels <= 0:
        
        return None
        
    # Return the ratio: centimeters per pixel
    cm_per_pixel = reference_cm / avg_side_pixels
    
    
    return cm_per_pixel


def preprocess_for_yolo(
    image: np.ndarray,
    target_size: Tuple[int, int] = (640, 640)
    ) -> Tuple[np.ndarray, float, Tuple[int, int]]:
    """
    Preprocesses an image for YOLOv8 ONNX inference via letterboxing.
    Maintains the aspect ratio and pads the remaining space.
    
    Args:
        image (np.ndarray): The original BGR image.
        target_size (Tuple[int, int]): The required input dimensions for the ONNX model.
        
    Returns:
        Tuple[np.ndarray, float, Tuple[int, int]]: 
            - The normalized, reshaped image tensor (1, C, H, W).
            - The scaling ratio applied to the original image.
            - The padding (pad_w, pad_h) applied to the scaled image.
    """
    original_height, original_width = image.shape[:2]
    target_width, target_height = target_size
    
    # Calculate scaling ratio
    ratio = min(target_width / original_width, target_height / original_height)
    new_unpad_width = int(round(original_width * ratio))
    new_unpad_height = int(round(original_height * ratio))
    
    # Calculate padding
    pad_w = (target_width - new_unpad_width) / 2
    pad_h = (target_height - new_unpad_height) / 2
    
    # Resize image maintaining aspect ratio
    if (original_width, original_height) != (new_unpad_width, new_unpad_height):
        resized_img = cv2.resize(image, (new_unpad_width, new_unpad_height), interpolation=cv2.INTER_LINEAR)
    else:
        resized_img = image.copy()
        
    # Apply padding to reach target_size
    top, bottom = int(round(pad_h - 0.1)), int(round(pad_h + 0.1))
    left, right = int(round(pad_w - 0.1)), int(round(pad_w + 0.1))
    
    padded_img = cv2.copyMakeBorder(
        resized_img, 
        top, 
        bottom, 
        left, 
        right, 
        cv2.BORDER_CONSTANT, 
        value=(114, 114, 114)
        )
    
    # Convert BGR to RGB, transpose to Channel-Height-Width, and normalize to [0, 1]
    rgb_img = cv2.cvtColor(padded_img, cv2.COLOR_BGR2RGB)
    tensor_img = rgb_img.transpose((2, 0, 1))[::-1]
    tensor_img = np.ascontiguousarray(tensor_img, dtype=np.float32)
    tensor_img /= 255.0
    
    # Add batch dimension
    tensor_img = np.expand_dims(tensor_img, axis=0)
    
    return tensor_img, ratio, (left, top)


def calculate_real_area(pixel_count: int, cm_per_pixel: float) -> float:
    """
    Converts a pixel area count into real-world square centimeters.
    
    Args:
        pixel_count (int): The number of pixels in the segmentation mask.
        cm_per_pixel (float): The spatial scale ratio.
        
    Returns:
        float: The physical area in square centimeters.
    """
    return float(pixel_count * (cm_per_pixel ** 2))

