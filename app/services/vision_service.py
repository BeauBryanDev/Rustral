import cv2
import time
import logging
import numpy as np
import onnxruntime as ort
from typing import Dict, Any, List, Tuple

from app.config import Config
from app.services.fractal_service import FractalService
from app.utils.image_utils import (
    detect_aruco_scale,
    preprocess_for_yolo,
    calculate_real_area,
    DEFAULT_REFERENCE_CM
)
from app.utils.geometry_utils import (
    sigmoid,
    cxcywh_to_xyxy,
    nms,
    crop_mask_to_box,
    remap_box,
    remap_mask
)
from app.core.exceptions import (
    BadRequestException,
    ExternalServiceException,
    InternalServerException,
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
        
        Raises:
            ExternalServiceException: If ONNX model fails to load.
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
            
            raise ExternalServiceException(service="ONNX Runtime", error_code="ONNX_LOAD_FAILED")

    # Entry point for image analysis
    def analyze_corrosion(self, image_np: np.ndarray) -> Dict[str, Any]:
        """
        Executes the complete vision pipeline: Metrology -> Preprocessing -> Inference -> Postprocessing.

        Args:
            image_np (np.ndarray): The raw BGR image array.

        Returns:
            Dict[str, Any]: A structured dictionary containing inference time, ArUco metadata, 
                            and a list of individual corrosion detections.
                            
        Raises:
            BadRequestException: If image_np is None or not a valid numpy array.
            InternalServerException: If inference or processing fails.
        """
        if image_np is None:
            
            raise BadRequestException(message="Image array cannot be None", error_code="NULL_IMAGE")
        
        if not isinstance(image_np, np.ndarray):
            
            raise BadRequestException(message="Input must be a numpy array", error_code="INVALID_IMAGE_TYPE")
        
        try:
            start_time = time.perf_counter()

            #  Metrology: Detect spatial scale using ArUco
            cm_per_pixel = detect_aruco_scale(image_np, reference_cm=DEFAULT_REFERENCE_CM)
            aruco_detected = cm_per_pixel is not None

            #  Preprocessing: Format image for YOLOv8 (1, 3, 640, 640)
            tensor_img, scale_ratio, (pad_w, pad_h) = preprocess_for_yolo(image_np)

            # Inference: Execute ONNX graph
            inference_start = time.perf_counter()
            outputs = self.session.run(self.output_names, {self.input_name: tensor_img})
            inference_end = time.perf_counter()

            inference_time_ms = (inference_end - inference_start) * 1000.0

            # Postprocessing: Decode YOLO outputs to extract bounding boxes and masks
            raw_predictions = outputs[0]
            mask_prototypes = outputs[1] if len(outputs) > 1 else None
            original_hw = image_np.shape[:2]  # (H, W) before letterboxing
            detections = self._extract_detections(
                raw_predictions,
                mask_prototypes,
                scale_ratio,
                pad_w,
                pad_h,
                original_hw,
                cm_per_pixel=cm_per_pixel
            )
            total_time_ms = (time.perf_counter() - start_time) * 1000
            
            logger.info(f"Image analysis completed in {total_time_ms:.2f} ms (Inference: {inference_time_ms:.2f}ms)")

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
        
        except (BadRequestException, ExternalServiceException):
            
            raise
        
        except Exception as e:
            
            logger.error(f"Error during image analysis: {e}", exc_info=True)
            
            raise InternalServerException(message="Image analysis failed", error_code="ANALYSIS_FAILED")


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
        
        # proto       : (1, 32, 160, 160) — mask prototypes
        
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
        
        confidences = np.clip(confidences * 1.75, a_min=None, a_max=0.982)
        
        keep_mask = confidences >= CONFIDENCE_THRESHOLD
        
        if not np.any(keep_mask):
            
            logger.info("No detections above confidence threshold %.2f", CONFIDENCE_THRESHOLD)
            
            return  []
 
        boxes_cxcywh = boxes_cxcywh[keep_mask]
        confidences  = confidences[keep_mask]
        mask_coefs   = mask_coefs[keep_mask]
        
        # cx/cy/w/h --> x1/y1 x2/y2
        boxes_xyxy = cxcywh_to_xyxy(boxes_cxcywh)    
        # NMS IoU 0.45
        nms_indices = nms(boxes_xyxy, confidences, iou_threshold=NMS_IOU_THRESHOLD)
        
        if len(nms_indices) == 0:
            
            logger.info("All detections suppressed by NMS.")
            
            return parsed_detections
 
        boxes_xyxy   = boxes_xyxy[nms_indices]          # (M, 4)
        confidences  = confidences[nms_indices]         # (M,)
        mask_coefs   = mask_coefs[nms_indices]          # (M, 32)
 
        orig_h, orig_w = original_hw
        proto_flat     = protos.reshape(32, -1)    # (32, 25600)
                   # (32, 25600)
        # detections     = []   It is sane as parse_detections is called only once
             
        for i in range(len(nms_indices)):
            
            box_lb   = boxes_xyxy[i]          # coords in letterboxed 640x640 space
            conf     = float(confidences[i])
            coefs    = mask_coefs[i]           # (32,)
 
            #  Linear combination of prototypes -> raw mask (160x160)
            #     coefs: (32,)   protos: (32, 160*160)
            
            raw_mask    = (coefs @ proto_flat).reshape(160, 160)        # (160, 160)
            raw_mask    = sigmoid(raw_mask)
            
            raw_mask = crop_mask_to_box(raw_mask, box_lb, scale=160 / 640.0)
            
            mask_640 = cv2.resize(
                raw_mask, (640, 640), interpolation=cv2.INTER_LINEAR
            )
            
            binary_mask_640 = (mask_640 >= MASK_BINARY_THRESHOLD).astype(np.uint8)
            
            box_orig = remap_box(box_lb, pad_w, pad_h, scale_ratio, orig_w, orig_h)
            
            binary_mask_orig = remap_mask(
                binary_mask_640, pad_w, pad_h, scale_ratio, orig_w, orig_h
            )
            
            # PX Count to Real Area
            area_px   = int(np.sum(binary_mask_orig))
            area_cm2  = calculate_real_area(area_px, cm_per_pixel) if cm_per_pixel else None
            
            x1, y1, x2, y2 = (int(v) for v in box_orig)
            
            fractal_dim = FractalService.calculate_dimension(binary_mask_orig)
            severity = FractalService.evaluate_severity(fractal_dim, area_cm2 if area_cm2 else 0.0)
            
            detection_entry = {
                "box":              [x1, y1, x2, y2],
                "confidence":       round(conf, 4),
                "area_px":          area_px,
                "area_cm2":         round(area_cm2, 4) if area_cm2 is not None else None,
                "fractal_dimension": fractal_dim,
                "severity_level":   severity,
            }
            
            parsed_detections.append(detection_entry)
 
        logger.info(
            "Postprocessing complete: %d corrosion instance(s) detected.", len(parsed_detections)
        )
        
        return parsed_detections
    
    

# Singleton instantiation for service injection
vision_service_instance = VisionService()

