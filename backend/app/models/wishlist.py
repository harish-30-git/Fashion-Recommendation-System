"""
Wishlist document schema for MongoDB.

Design: Each user-product pair is a separate document.
This makes add/remove O(1) and lets us use a compound unique index
at the database level to guarantee no duplicates, even under
concurrent requests.

Alternative design: Embed wishlist items as an array in the user document.
We chose separate documents because:
  - Wishlists can grow large; embedding would bloat the user document.
  - Index-level uniqueness enforcement is cleaner with separate documents.
  - Easier to query "all users who wishlisted product X" (for analytics).
"""

from datetime import datetime, timezone


def build_wishlist_entry(user_id, product_id: str) -> dict:
    """Build a wishlist document for MongoDB insertion."""
    return {
        "user_id": user_id,
        "product_id": product_id,
        "added_at": datetime.now(timezone.utc),
    }


def serialize_wishlist_entry(doc: dict) -> dict:
    """Convert raw MongoDB wishlist document to JSON-safe dict."""
    if doc is None:
        return None
    result = dict(doc)
    result["id"] = str(doc["_id"])
    result.pop("_id", None)
    result["user_id"] = str(doc["user_id"])
    if isinstance(result.get("added_at"), datetime):
        result["added_at"] = result["added_at"].isoformat()
    return result
