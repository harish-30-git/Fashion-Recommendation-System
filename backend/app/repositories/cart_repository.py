"""
Cart repository — all MongoDB queries for the carts collection.

One cart document per user. Items are embedded as an array.
We use MongoDB's $push, $set, and $pull operators for atomic updates.
"""

from pymongo.collection import Collection
from bson import ObjectId
from datetime import datetime, timezone

from app.models.cart import build_cart_item, serialize_cart


class CartRepository:
    def __init__(self, db):
        self.collection: Collection = db.carts

    def get_by_user(self, user_id) -> dict:
        """Fetch the cart for a user. Returns an empty cart if none exists."""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        doc = self.collection.find_one({"user_id": user_id})
        return serialize_cart(doc)

    def add_item(
        self,
        user_id,
        product_id: str,
        quantity: int,
        size: str,
        color: str,
        unit_price: float,
    ) -> dict:
        """
        Add an item to the cart or increase its quantity if it already exists.

        Uses $push to append to the items array. If a cart doesn't exist,
        upsert=True creates one automatically.

        Note: If the same product+size+color combination is added again,
        we increment quantity instead of duplicating the item.
        """
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        # Check if this product+size+color combination already exists
        existing = self.collection.find_one(
            {
                "user_id": user_id,
                "items": {
                    "$elemMatch": {
                        "product_id": product_id,
                        "size": size,
                        "color": color,
                    }
                },
            }
        )

        if existing:
            # Increment quantity of the existing item
            self.collection.update_one(
                {
                    "user_id": user_id,
                    "items.product_id": product_id,
                    "items.size": size,
                    "items.color": color,
                },
                {
                    "$inc": {"items.$.quantity": quantity},
                    "$set": {"updated_at": datetime.now(timezone.utc)},
                },
            )
        else:
            # Add new item to the cart
            item = build_cart_item(product_id, quantity, size, color, unit_price)
            self.collection.update_one(
                {"user_id": user_id},
                {
                    "$push": {"items": item},
                    "$set": {"updated_at": datetime.now(timezone.utc)},
                    "$setOnInsert": {"user_id": user_id},
                },
                upsert=True,
            )

        return self.get_by_user(user_id)

    def update_item_quantity(self, user_id, product_id: str, quantity: int) -> dict:
        """Update the quantity of a specific cart item."""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        self.collection.update_one(
            {"user_id": user_id, "items.product_id": product_id},
            {
                "$set": {
                    "items.$.quantity": quantity,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        return self.get_by_user(user_id)

    def remove_item(self, user_id, product_id: str) -> dict:
        """Remove an item from the cart using $pull."""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        self.collection.update_one(
            {"user_id": user_id},
            {
                "$pull": {"items": {"product_id": product_id}},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
        )
        return self.get_by_user(user_id)

    def clear(self, user_id) -> dict:
        """Remove all items from the cart (used after checkout)."""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        self.collection.update_one(
            {"user_id": user_id},
            {"$set": {"items": [], "updated_at": datetime.now(timezone.utc)}},
        )
        return self.get_by_user(user_id)
