import time
import logging
import numpy as np
import onnxruntime as ort
from typing import Dict, Any, List

from app.config import Config
from app.utils.image_utils import (
    detect_aruco_scale,
    preprocess_for_yolo,
    calculate_real_area,
    DEFAULT_REFERENCE_CM
)

logger = logging.getLogger(__name__)

# Inference thresholds
CONFIDENCE_THRESHOLD = 0.25
NMS_IOU_THRESHOLD    = 0.45
MASK_BINARY_THRESHOLD = 0.5


class VisionService:
    """
    Core service orchestrating ArUco metrology and YOLOv8-seg ONNX inference.
    Handles the end-to-end pipeline from raw image array to structured detection data.
    """

    def __init__(self):
        """
        Initializes the ONNX Runtime session and loads the model into memory.
        Configures execution providers to prioritize GPU if available, falling back to CPU.
        """
        try:
            # Try to use CUDA if available, otherwise fallback to CPU
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
            self.session = ort.InferenceSession(Config.ONNX_MODEL_PATH, providers=providers)
            
            # Extract input/output metadata from the ONNX graph
            self.input_name = self.session.get_inputs()[0].name
            self.output_names = [output.name for output in self.session.get_outputs()]
            
            logger.info(f"Successfully initialized ONNX session with model: {Config.ONNX_MODEL_PATH}")
        except Exception as error:
            logger.critical(f"Failed to load ONNX model. Ensure the path is correct. Error: {error}")
            raise

    # Entry point for image analysis
    def analyze_corrosion(self, image_np: np.ndarray) -> Dict[str, Any]:
        """
        Executes the complete vision pipeline: Metrology -> Preprocessing -> Inference -> Postprocessing.

        Args:
            image_np (np.ndarray): The raw BGR image array.

        Returns:
            Dict[str, Any]: A structured dictionary containing inference time, ArUco metadata, 
                            and a list of individual corrosion detections.
        """
        start_time = time.perf_counter()

        #  Metrology: Detect spatial scale using ArUco
        cm_per_pixel = detect_aruco_scale(image_np, reference_cm=DEFAULT_REFERENCE_CM)
        aruco_detected = cm_per_pixel is not None

        #  Preprocessing: Format image for YOLOv8 (1, 3, 640, 640)
        tensor_img, scale_ratio, (pad_w, pad_h) = preprocess_for_yolo(image_np)

        # Inference: Execute ONNX graph
        # (boxes + mask weights) and proto (mask prototypes)
        inference_start = time.perf_counter()
        outputs = self.session.run(self.output_names, {self.input_name: tensor_img})
        inference_end = time.perf_counter()

        inference_time_ms = (inference_end - inference_start) * 1000.0

        # Postprocessing: Decode YOLO outputs to extract bounding boxes and masks
        raw_predictions = outputs[0]
        mask_prototypes = outputs[1] if len(outputs) > 1 else None
        # outputs[0] -> (1, 116, 8400)  boxes + confidence + 32 mask coefficients
        # outputs[1] -> (1,  32, 160, 160) mask prototypes
        original_hw = image_np.shape[:2]  # (H, W) before letterboxing
        detections  = self._extract_detections(
            raw_predictions,
            mask_prototypes,
            scale_ratio,
            pad_w,
            pad_h,
            original_hw,
            cm_per_pixel
        )
        total_time_ms = (time.perf_counter() - start_time) * 1000
        
        logger.info(f"Image analysis completed in {total_time_ms:.2f}ms (Inference: {inference_time_ms:.2f}ms)")

        #  Structure the final payload
        return {
            "inference_time_ms": round(inference_time_ms, 2),
            "aruco_metadata": {
                "detected": aruco_detected,
                "marker_id": 42 if aruco_detected else None,
                "reference_scale_cm": DEFAULT_REFERENCE_CM if aruco_detected else None,
                "cm_per_pixel": cm_per_pixel
            },
            "detections": detections
        }


    def _extract_detections(
        self,
        predictions:  np.ndarray,
        proto:        np.ndarray,
        scale_ratio:  float,
        pad_w:        int,
        pad_h:        int,
        original_hw:  Tuple[int, int],
        cm_per_pixel: float = None
    ) -> List[Dict[str, Any]]:
        """
        Decodes the raw ONNX output tensors into structured detection metrics.
        Applies Non-Maximum Suppression (NMS) and calculates segmentation areas.

        Args:
            predictions (np.ndarray): The primary output tensor (boxes, scores, mask weights).
            proto (np.ndarray): The secondary output tensor (mask prototypes).
            scale_ratio (float): Ratio used during preprocessing letterboxing.
            pad_w (int): Horizontal padding applied during preprocessing.
            pad_h (int): Vertical padding applied during preprocessing.
            cm_per_pixel (float): Real-world scale factor from ArUco metrology.

        Returns:
            List[Dict[str, Any]]: List of processed detections ready for database insertion.
        """
        #YOLOv8-seg raw output layout per anchor:
        #   [cx, cy, w, h,  conf,  mc_0 .. mc_31]
        #     0   1   2  3    4      5 ..      36
        
        parsed_detections: List[Dict[str, Any]] = []
 
        if proto is None:
            logger.warning("No prototype tensor found in ONNX output — skipping mask reconstruction.")
            
            return parsed_detections
        
        
        # (1, 116, 8400) -> (8400, 116)
        preds = predictions[0].T            # (8400, 116)
        protos = proto[0]           
        
        
        # Layout: [cx, cy, w, h, conf, mc_0..mc_31]
        boxes_cxcywh  = preds[:, 0:4]      # (8400, 4)
        confidences   = preds[:, 4]        # (8400,)
        mask_coefs    = preds[:, 5:37]     # (8400, 32)
        
        keep_mask = confidences >= CONFIDENCE_THRESHOLD
        
        if not np.any(keep_mask):
            
            logger.info("No detections above confidence threshold %.2f", CONFIDENCE_THRESHOLD)
            
            return parsed_detections
 
        boxes_cxcywh = boxes_cxcywh[keep_mask]
        confidences  = confidences[keep_mask]
        mask_coefs   = mask_coefs[keep_mask]
        
        # cx/cy/w/h --> x1/y1 x2/y2
        boxes_xyxy = _cxcywh_to_xyxy(boxes_cxcywh)
        # NMS IoU 0.45
        nms_indices = _nms(boxes_xyxy, confidences, iou_threshold=NMS_IOU_THRESHOLD)
        
        if len(nms_indices) == 0:
            
            logger.info("All detections suppressed by NMS.")
            
            return parsed_detections
 
        boxes_xyxy   = boxes_xyxy[nms_indices]          # (M, 4)
        confidences  = confidences[nms_indices]         # (M,)
        mask_coefs   = mask_coefs[nms_indices]          # (M, 32)
 
        orig_h, orig_w = original_hw
        
        
        for i in range(len(nms_indices)):
            
            box_lb   = boxes_xyxy[i]          # coords in letterboxed 640x640 space
            conf     = float(confidences[i])
            coefs    = mask_coefs[i]           # (32,)
 
            #  Linear combination of prototypes -> raw mask (160x160)
            #     coefs: (32,)   protos: (32, 160*160)
            proto_flat  = protos.reshape(32, -1)                        # (32, 25600)
            raw_mask    = (coefs @ proto_flat).reshape(160, 160)        # (160, 160)
            raw_mask    = _sigmoid(raw_mask)
            
            raw_mask = _crop_mask_to_box(raw_mask, box_lb, scale=160 / 640.0)
            
            import cv2
            mask_640 = cv2.resize(
                raw_mask, (640, 640), interpolation=cv2.INTER_LINEAR
            )
            
            binary_mask_640 = (mask_640 >= MASK_BINARY_THRESHOLD).astype(np.uint8)
            
            box_orig = _remap_box(box_lb, pad_w, pad_h, scale_ratio, orig_w, orig_h)
            
            binary_mask_orig = _remap_mask(
                binary_mask_640, pad_w, pad_h, scale_ratio, orig_w, orig_h
            )
            
            # PX Count to Real Area
            area_px   = int(np.sum(binary_mask_orig))
            area_cm2  = calculate_real_area(area_px, cm_per_pixel) if cm_per_pixel else None
            
            x1, y1, x2, y2 = (int(v) for v in box_orig)
            
            detection_entry = {
                "box":              [x1, y1, x2, y2],
                "confidence":       round(conf, 4),
                "area_px":          area_px,
                "area_cm2":         round(area_cm2, 4) if area_cm2 is not None else None,
                "fractal_dimension": None,    # Will be calculated by FractalService later
                "severity_level":   "Pending"
            }
            
            parsed_detections.append(detection_entry)
 
        logger.info(
            "Postprocessing complete: %d corrosion instance(s) detected.", len(parsed_detections)
        )
        
        return parsed_detections
    
    
# Module-level geometry / NMS utilities

def _sigmoid(x: np.ndarray) -> np.ndarray:
    """Numerically stable sigmoid."""
    return np.where(x >= 0, 1.0 / (1.0 + np.exp(-x)), np.exp(x) / (1.0 + np.exp(x)))
 

def _cxcywh_to_xyxy(boxes: np.ndarray) -> np.ndarray:
    """
    Converts bounding boxes from center format to corner format.
 
    Args:
        boxes (np.ndarray): Shape (N, 4) with columns [cx, cy, w, h].
 
    Returns:
        np.ndarray: Shape (N, 4) with columns [x1, y1, x2, y2].
    """
    out = np.empty_like(boxes)
    out[:, 0] = boxes[:, 0] - boxes[:, 2] / 2.0   # x1
    out[:, 1] = boxes[:, 1] - boxes[:, 3] / 2.0   # y1
    out[:, 2] = boxes[:, 0] + boxes[:, 2] / 2.0   # x2
    out[:, 3] = boxes[:, 1] + boxes[:, 3] / 2.0   # y2
    
    return out

     
def _compute_iou(box: np.ndarray, boxes: np.ndarray) -> np.ndarray:
    """
    Computes IoU between one box and an array of boxes.
 
    Args:
        box   (np.ndarray): Shape (4,)   — [x1, y1, x2, y2].
        boxes (np.ndarray): Shape (N, 4) — [x1, y1, x2, y2].
 
    Returns:
        np.ndarray: Shape (N,) IoU values in [0, 1].
    """
    inter_x1 = np.maximum(box[0], boxes[:, 0])
    inter_y1 = np.maximum(box[1], boxes[:, 1])
    inter_x2 = np.minimum(box[2], boxes[:, 2])
    inter_y2 = np.minimum(box[3], boxes[:, 3])
 
    inter_w = np.maximum(0.0, inter_x2 - inter_x1)
    inter_h = np.maximum(0.0, inter_y2 - inter_y1)
    
    inter_area = inter_w * inter_h
 
    area_box   = (box[2]   - box[0])   * (box[3]   - box[1])
    area_boxes = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    
    union_area  = area_box + area_boxes - inter_area
 
    return np.where(union_area > 0.0, inter_area / union_area, 0.0)
 

def _nms(
    boxes:         np.ndarray,
    scores:        np.ndarray,
    iou_threshold: float = 0.45
) -> List[int]:
    """
    Greedy IoU-based Non-Maximum Suppression.
 
    Args:
        boxes         (np.ndarray): Shape (N, 4) — [x1, y1, x2, y2].
        scores        (np.ndarray): Shape (N,)   — confidence scores.
        iou_threshold (float):      Detections with IoU >= this value are suppressed.
 
    Returns:
        List[int]: Indices of surviving detections, ordered by descending score.
    """
    order   = scores.argsort()[::-1]    # highest confidence first
    kept    = []
 
    while order.size > 0:
        idx = order[0]
        kept.append(int(idx))
 
        if order.size == 1:
            break
 
        remaining = order[1:]
        iou_vals  = _compute_iou(boxes[idx], boxes[remaining])
        suppress  = iou_vals >= iou_threshold
        order     = remaining[~suppress]
 
    return kept
 
 
def _crop_mask_to_box(
    mask:  np.ndarray,
    box:   np.ndarray,
    scale: float = 160 / 640.0
) -> np.ndarray:
    """
    Zeros out mask values outside the bounding box region.
    Prevents mask bleed from adjacent corrosion instances.
 
    Args:
        mask  (np.ndarray): Shape (H, W) float mask in prototype space.
        box   (np.ndarray): Shape (4,)   [x1, y1, x2, y2] in letterboxed 640x640 space.
        scale (float):      Ratio between prototype resolution and letterbox resolution
                            (default 160/640 = 0.25).
 
    Returns:
        np.ndarray: Cropped mask of the same shape.
    """
    h, w   = mask.shape
    
    x1, y1, x2, y2 = (int(v * scale) for v in box)
 
    x1 = max(0, x1);  y1 = max(0, y1)
    x2 = min(w, x2);  y2 = min(h, y2)
 
    cropped = np.zeros_like(mask)
    
    if x2 > x1 and y2 > y1:
        
        cropped[y1:y2, x1:x2] = mask[y1:y2, x1:x2]
        
    return cropped


def _remap_box(
    box:        np.ndarray,
    pad_w:      int,
    pad_h:      int,
    scale_ratio: float,
    orig_w:     int,
    orig_h:     int
) -> np.ndarray:
    """ 
    Converts a bounding box from letterboxed 640x640 coordinates
    back to the original image coordinate space. 
    """
    remapped = box.copy().astype(np.float32)
 
    # Remove padding
    remapped[0] -= pad_w
    remapped[2] -= pad_w
    remapped[1] -= pad_h
    remapped[3] -= pad_h
 
    # Revert scaling
    remapped /= scale_ratio
 
    # Clip to image boundaries
    remapped[0] = np.clip(remapped[0], 0, orig_w)
    remapped[2] = np.clip(remapped[2], 0, orig_w)
    remapped[1] = np.clip(remapped[1], 0, orig_h)
    remapped[3] = np.clip(remapped[3], 0, orig_h)
    
 
    return remapped
    
 
def _remap_mask(
    binary_mask_640: np.ndarray,
    pad_w:           int,
    pad_h:           int,
    scale_ratio:     float,
    orig_w:          int,
    orig_h:          int
) -> np.ndarray:
    """
    Removes letterbox padding from a 640x640 binary mask and resizes
    it back to the original image dimensions.
    """
    import cv2
 
    # Compute the unpadded region inside the 640x640 canvas
    unpad_w = int(round(orig_w * scale_ratio))
    unpad_h = int(round(orig_h * scale_ratio))
 
    # Crop out the padding
    cropped = binary_mask_640[pad_h: pad_h + unpad_h, pad_w: pad_w + unpad_w]
 
    # Resize to original image dimensions using nearest-neighbour to preserve binary values
    remapped = cv2.resize(cropped, (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)
 
    return remapped.astype(np.uint8)
 


# Singleton instantiation for service injection
vision_service_instance = VisionService()

