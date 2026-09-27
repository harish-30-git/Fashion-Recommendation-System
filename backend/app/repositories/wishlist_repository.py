"""
Wishlist repository — all MongoDB queries for the wishlists collection.

The compound unique index on (user_id, product_id) is created in app/__init__.py.
This guarantees at the database level that a user cannot wishlist the same
product twice, even under concurrent requests. The insert_one() call will
raise DuplicateKeyError if the pair already exists.
"""

from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError
from bson import ObjectId

from app.models.wishlist import build_wishlist_entry


class WishlistRepository:
    def __init__(self, db):
        self.collection: Collection = db.wishlists

    def get_by_user(self, user_id) -> list[str]:
        """
        Return a list of product_id strings in the user's wishlist.
        Ordered by most recently added.
        """
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        cursor = self.collection.find(
            {"user_id": user_id}, {"product_id": 1}
        ).sort("added_at", -1)

        return [doc["product_id"] for doc in cursor]

    def add(self, user_id, product_id: str) -> tuple[bool, bool]:
        """
        Add a product to the wishlist.

        Returns:
            (success: bool, already_existed: bool)
            success=True, already_existed=False → newly added
            success=True, already_existed=True  → was already in wishlist
        """
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        entry = build_wishlist_entry(user_id, product_id)
        try:
            self.collection.insert_one(entry)
            return True, False
        except DuplicateKeyError:
            return True, True

    def remove(self, user_id, product_id: str) -> bool:
        """
        Remove a product from the wishlist.

        Returns:
            True if the item existed and was removed, False if it wasn't there.
        """
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        result = self.collection.delete_one(
            {"user_id": user_id, "product_id": product_id}
        )
        return result.deleted_count > 0

    def exists(self, user_id, product_id: str) -> bool:
        """Check if a product is already in the user's wishlist."""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        return (
            self.collection.count_documents(
                {"user_id": user_id, "product_id": product_id}, limit=1
            )
            > 0
        )
