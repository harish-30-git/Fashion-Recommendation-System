"""
Interaction document schema for MongoDB.

Interactions are the raw signal that powers personalized recommendations.
Every time a user views, wishlists, carts, or purchases a product,
we log an interaction with a configurable weight.

Interview note: Interaction weights are a design decision, not a
measured result. They should be tuned with A/B testing in production.
"""

from datetime import datetime, timezone


# Default weights — overridden by app.config["INTERACTION_WEIGHTS"]
DEFAULT_WEIGHTS = {
    "view": 0.5,
    "wishlist": 1.5,
    "cart": 2.0,
    "purchase": 3.0,
}


def build_interaction(
    user_id,         # MongoDB ObjectId of the user
    product_id: str, # product_id string (e.g., "P000042")
    interaction_type: str,
    weights: dict | None = None,
    session_id: str | None = None,
) -> dict:
    """
    Build an interaction document ready for MongoDB insertion.

    Args:
        user_id:          MongoDB ObjectId of the authenticated user.
        product_id:       Stable product identifier.
        interaction_type: One of 'view', 'wishlist', 'cart', 'purchase'.
        weights:          Dict mapping interaction_type → float weight.
                          Defaults to DEFAULT_WEIGHTS.
        session_id:       Optional session identifier for anonymous grouping.

    Returns:
        Dict representing the MongoDB interaction document.
    """
    w = weights or DEFAULT_WEIGHTS
    return {
        "user_id": user_id,
        "product_id": product_id,
        "interaction_type": interaction_type,
        "weight": w.get(interaction_type, 0.5),
        "timestamp": datetime.now(timezone.utc),
        "session_id": session_id,
    }


def serialize_interaction(doc: dict) -> dict:
    """Convert raw MongoDB interaction document to JSON-safe dict."""
    if doc is None:
        return None
    result = dict(doc)
    result["id"] = str(doc["_id"])
    result.pop("_id", None)
    result["user_id"] = str(doc["user_id"])
    if isinstance(result.get("timestamp"), datetime):
        result["timestamp"] = result["timestamp"].isoformat()
    return result
