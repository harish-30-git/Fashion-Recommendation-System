"""
User repository — all MongoDB queries for the users collection.

The repository pattern means:
  - Services never touch the database directly.
  - If we ever switch databases, only this file changes.
  - Every query is in one place, easy to review and test.
"""

from datetime import datetime, timezone
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError
from bson import ObjectId

from app.models.user import User


class UserRepository:
    def __init__(self, db):
        self.collection: Collection = db.users

    def create(self, user: User) -> dict | None:
        """
        Insert a new user document.

        Returns:
            The inserted document with _id, or None if email/username taken.
        """
        try:
            result = self.collection.insert_one(user.to_dict())
            return self.find_by_id(result.inserted_id)
        except DuplicateKeyError:
            return None

    def find_by_email(self, email: str) -> dict | None:
        """Find a user document by email (used for login)."""
        return self.collection.find_one({"email": email.lower().strip()})

    def find_by_username(self, username: str) -> dict | None:
        """Find a user document by username (for uniqueness check)."""
        return self.collection.find_one({"username": username})

    def find_by_id(self, user_id) -> dict | None:
        """Find a user document by MongoDB ObjectId."""
        if isinstance(user_id, str):
            try:
                user_id = ObjectId(user_id)
            except Exception:
                return None
        return self.collection.find_one({"_id": user_id})

    def update(self, user_id, updates: dict) -> dict | None:
        """
        Update allowed profile fields.
        Only permits safe fields — never updates password_hash this way.
        """
        allowed_fields = {"full_name", "gender", "profile_image"}
        safe_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        if not safe_updates:
            return self.find_by_id(user_id)

        safe_updates["updated_at"] = datetime.now(timezone.utc)

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        self.collection.update_one({"_id": user_id}, {"$set": safe_updates})
        return self.find_by_id(user_id)

    def email_exists(self, email: str) -> bool:
        """Check if an email is already registered."""
        return self.collection.count_documents({"email": email.lower().strip()}, limit=1) > 0

    def username_exists(self, username: str) -> bool:
        """Check if a username is already taken."""
        return self.collection.count_documents({"username": username}, limit=1) > 0
