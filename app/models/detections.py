
import datetime
from typing import Optional, Dict, Any, List
from bson.objectid import ObjectId


class DetectionDocument:
    """
    Data model representing a corrosion detection analysis result in MongoDB.
    Encapsulates YOLO inference metrics, ArUco scaling data, and fractal severity.
    """

    def __init__(
        self,
        user_id: ObjectId,
        location_id: ObjectId,
        image_id: ObjectId,
        detections: List[Dict[str, Any]],
        aruco_metadata: Dict[str, Any],
        inference_time_ms: float,
        _id: Optional[ObjectId] = None,
        detected_at: Optional[datetime.datetime] = None,
    ):
        """
        Initializes a new DetectionDocument instance.

        Args:
            user_id (ObjectId): Reference to the owner user.
            location_id (ObjectId): Reference to the physical location.
            image_id (ObjectId): Reference to the analyzed original image.
            detections (List[Dict[str, Any]]): List of individual corrosion patches found.
                Expected keys: box, confidence, area_px, area_cm2, fractal_dimension, severity_level.
            aruco_metadata (Dict[str, Any]): Data regarding the physical scale marker.
                Expected keys: detected (bool), marker_id (int), reference_scale_cm (float).
            inference_time_ms (float): Time taken by the ONNX model to process the image.
            _id (Optional[ObjectId]): MongoDB document identifier.
            detected_at (Optional[datetime.datetime]): Timestamp of the analysis.
        """
        self._id = _id
        self.user_id = user_id
        self.location_id = location_id
        self.image_id = image_id
        self.detections = detections
        self.aruco_metadata = aruco_metadata
        self.inference_time_ms = inference_time_ms
        self.detected_at = detected_at or datetime.datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the DetectionDocument instance into a BSON-compatible dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation for MongoDB storage.
        """
        document = {
            "user_id": self.user_id,
            "location_id": self.location_id,
            "image_id": self.image_id,
            "detections": self.detections,
            "aruco_metadata": self.aruco_metadata,
            "inference_time_ms": self.inference_time_ms,
            "detected_at": self.detected_at
        }

        if self._id:
            document["_id"] = self._id

        return document

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DetectionDocument":
        """
        Creates a DetectionDocument instance from a MongoDB dictionary.

        Args:
            data (Dict[str, Any]): The raw data retrieved from MongoDB.

        Returns:
            DetectionDocument: A populated instance of the model.
        """
        return cls(
            _id=data.get("_id"),
            user_id=data.get("user_id"),
            location_id=data.get("location_id"),
            image_id=data.get("image_id"),
            detections=data.get("detections", []),
            aruco_metadata=data.get("aruco_metadata", {}),
            inference_time_ms=data.get("inference_time_ms", 0.0),
            detected_at=data.get("detected_at")
        )
        
        