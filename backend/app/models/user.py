"""
User document schema for MongoDB.

In MongoDB, documents are just dictionaries. We use Python dataclasses
to define the expected structure, provide defaults, and convert to/from
dict for database operations. This is much lighter than SQLAlchemy ORM.

What's NOT stored here: password_hash is written to the DB but stripped
from any public representation via the to_public_dict() method.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone


@dataclass
class User:
    email: str
    username: str
    password_hash: str
    full_name: str
    gender: str = "Unisex"
    profile_image: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        """Convert to dict for MongoDB insertion (includes password_hash)."""
        return asdict(self)

    def to_public_dict(self) -> dict:
        """
        Serializable representation safe to return in API responses.
        NEVER includes password_hash.
        """
        d = asdict(self)
        d.pop("password_hash", None)
        # Convert datetimes to ISO strings for JSON serialization
        d["created_at"] = self.created_at.isoformat()
        d["updated_at"] = self.updated_at.isoformat()
        return d

    @staticmethod
    def from_mongo(doc: dict) -> dict:
        """
        Convert a raw MongoDB document to a public-safe dict.
        Converts _id ObjectId to string and removes password_hash.
        """
        if doc is None:
            return None
        result = {k: v for k, v in doc.items() if k != "password_hash"}
        result["id"] = str(doc["_id"])
        result.pop("_id", None)
        # Serialize datetimes
        for key in ("created_at", "updated_at"):
            if key in result and isinstance(result[key], datetime):
                result[key] = result[key].isoformat()
        return result
