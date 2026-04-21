import datetime
from typing import Optional, Dict, Any
from bson.objectid import ObjectId


class ImageDocument:
    """
    Data model representing an uploaded inspection image in MongoDB.
    Maintains references to the user who uploaded it and the physical location.
    """

    def __init__(
        self,
        user_id: ObjectId,
        location_id: ObjectId,
        stored_filename: str,
        stored_path: str,
        mime_type: str,
        size_bytes: int,
        width_px: int,
        height_px: int,
        total_detections: int = 0,
        _id: Optional[ObjectId] = None,
        created_at: Optional[datetime.datetime] = None,
    ):
        """
        Initializes a new ImageDocument instance.

        Args:
            user_id (ObjectId): Reference to the owner user.
            location_id (ObjectId): Reference to the inspection location.
            stored_filename (str): Name of the file as saved on disk or S3.
            stored_path (str): Relative or absolute path to the file.
            mime_type (str): Media type of the image (e.g., 'image/jpeg').
            size_bytes (int): File size in bytes.
            width_px (int): Image width in pixels.
            height_px (int): Image height in pixels.
            total_detections (int): Number of corrosion instances found. Defaults to 0.
            _id (Optional[ObjectId]): MongoDB document identifier.
            created_at (Optional[datetime.datetime]): Record creation timestamp.
        """
        self._id = _id
        self.user_id = user_id
        self.location_id = location_id
        self.stored_filename = stored_filename
        self.stored_path = stored_path
        self.mime_type = mime_type
        self.size_bytes = size_bytes
        self.width_px = width_px
        self.height_px = height_px
        self.total_detections = total_detections
        self.created_at = created_at or datetime.datetime.utcnow()


    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the ImageDocument instance into a BSON-compatible dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation for MongoDB storage.
        """
        document = {
            "user_id": self.user_id,
            "location_id": self.location_id,
            "stored_filename": self.stored_filename,
            "stored_path": self.stored_path,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "width_px": self.width_px,
            "height_px": self.height_px,
            "total_detections": self.total_detections,
            "created_at": self.created_at
        }

        if self._id:
            document["_id"] = self._id

        return document


    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImageDocument":
        """
        Creates an ImageDocument instance from a MongoDB dictionary.

        Args:
            data (Dict[str, Any]): The raw data retrieved from MongoDB.

        Returns:
            ImageDocument: A populated instance of the model.
        """
        return cls(
            _id=data.get("_id"),
            user_id=data.get("user_id"),
            location_id=data.get("location_id"),
            stored_filename=data.get("stored_filename", ""),
            stored_path=data.get("stored_path", ""),
            mime_type=data.get("mime_type", ""),
            size_bytes=data.get("size_bytes", 0),
            width_px=data.get("width_px", 0),
            height_px=data.get("height_px", 0),
            total_detections=data.get("total_detections", 0),
            created_at=data.get("created_at")
        )
        