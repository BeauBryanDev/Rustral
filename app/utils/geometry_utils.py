# Module-level geometry / NMS utilities
import cv2
import numpy as np
import math
from typing import List, Optional


def sigmoid(x: np.ndarray) -> np.ndarray:
    """Numerically stable sigmoid."""
    return np.where(
        x >= 0, 1.0 / (1.0 + np.exp(-x)), 
        np.exp(x) / (1.0 + np.exp(x))
        )
 

def cxcywh_to_xyxy(boxes: np.ndarray) -> np.ndarray:
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

     
def compute_iou(box: np.ndarray, boxes: np.ndarray) -> np.ndarray:
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
 

def nms(
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
        iou_vals  = compute_iou(boxes[idx], boxes[remaining])
        suppress  = iou_vals >= iou_threshold
        order     = remaining[~suppress]
 
    return kept
 

# Mask manipulation Helper Functions
def crop_mask_to_box(
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


def remap_box(
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
    
 
def remap_mask(
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
 
