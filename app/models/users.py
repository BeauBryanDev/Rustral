import datetime
from typing import Optional, Dict, Any
from bson.objectid import ObjectId

class UserDocument:
    """
    Data model representation for a User in MongoDB.
    Handles schema definition and serialization to/from Python dictionaries.
    """

    def __init__(
        self,
        full_name: str,
        email: str,
        hash_password: str,
        gender: Optional[str] = None,
        phone_number: Optional[str] = None,
        country: Optional[str] = None,
        city: Optional[str] = None,
        is_active: bool = True,
        is_admin: bool = False,
        _id: Optional[ObjectId] = None,
        created_at: Optional[datetime.datetime] = None,
        updated_at: Optional[datetime.datetime] = None,
    ):
        self._id = _id
        self.full_name = full_name
        self.email = email
        self.hash_password = hash_password
        self.gender = gender
        self.phone_number = phone_number
        self.country = country
        self.city = city
        self.is_active = is_active
        self.is_admin = is_admin
        self.created_at = created_at or datetime.datetime.utcnow()
        self.updated_at = updated_at or datetime.datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the UserDocument instance into a dictionary suitable for MongoDB insertion.
        
        Returns:
            Dict[str, Any]: The BSON-compatible dictionary representing the user.
        """
        document = {
            "full_name": self.full_name,
            "email": self.email,
            "hash_password": self.hash_password,
            "gender": self.gender,
            "phone_number": self.phone_number,
            "country": self.country,
            "city": self.city,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
        if self._id:
            document["_id"] = self._id
            
        return document

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserDocument":
        """
        Instantiates a UserDocument from a MongoDB dictionary.
        
        Args:
            data (Dict[str, Any]): The dictionary retrieved from MongoDB.
            
        Returns:
            UserDocument: The populated user model instance.
        """
        return cls(
            _id=data.get("_id"),
            full_name=data.get("full_name", ""),
            email=data.get("email", ""),
            hash_password=data.get("hash_password", ""),
            gender=data.get("gender"),
            phone_number=data.get("phone_number"),
            country=data.get("country"),
            city=data.get("city"),
            is_active=data.get("is_active", True),
            is_admin=data.get("is_admin", False),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
        
        
        