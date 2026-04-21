import datetime
from typing import Optional, Dict, Any
from bson.objectid import ObjectId


class LocationDocument:
    """
    Data model representing a physical inspection location in MongoDB.
    Provides methods for dictionary serialization and instantiation from BSON data.
    """

    def __init__(
        self,
        user_id: ObjectId,
        name: str,
        city: str,
        country: str,
        address: Optional[str] = None,
        description: Optional[str] = None,
        _id: Optional[ObjectId] = None,
        created_at: Optional[datetime.datetime] = None,
        updated_at: Optional[datetime.datetime] = None,
    ):
        """
        Initializes a new LocationDocument instance.

        Args:
            user_id (ObjectId): Reference to the owner user.
            name (str): Name of the location.
            city (str): City or municipality name.
            country (str): Country name.
            address (Optional[str]): Physical street address.
            description (Optional[str]): Additional notes about the location.
            _id (Optional[ObjectId]): MongoDB document identifier.
            created_at (Optional[datetime.datetime]): Record creation timestamp.
            updated_at (Optional[datetime.datetime]): Record last update timestamp.
        """
        self._id = _id
        self.user_id = user_id
        self.name = name
        self.city = city
        self.country = country
        self.address = address
        self.description = description
        self.created_at = created_at or datetime.datetime.utcnow()
        self.updated_at = updated_at or datetime.datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the LocationDocument instance into a BSON-compatible dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation for MongoDB storage.
        """
        document = {
            "user_id": self.user_id,
            "name": self.name,
            "city": self.city,
            "country": self.country,
            "address": self.address,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

        if self._id:
            document["_id"] = self._id

        return document

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LocationDocument":
        """
        Creates a LocationDocument instance from a MongoDB dictionary.

        Args:
            data (Dict[str, Any]): The raw data retrieved from MongoDB.

        Returns:
            LocationDocument: A populated instance of the model.
        """
        return cls(
            _id=data.get("_id"),
            user_id=data.get("user_id"),
            name=data.get("name", ""),
            city=data.get("city", ""),
            country=data.get("country", ""),
            address=data.get("address"),
            description=data.get("description"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
        
        