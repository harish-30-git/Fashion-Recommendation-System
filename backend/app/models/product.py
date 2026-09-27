"""
Product document schema for MongoDB.

Products are ingested from the dataset via scripts/import_products.py.
This module defines the canonical shape of a product document and provides
a serialization helper used by the product repository.
"""

from datetime import datetime, timezone


def serialize_product(doc: dict) -> dict:
    """
    Convert a raw MongoDB product document to a JSON-safe dict.

    - Converts _id ObjectId to string.
    - Converts datetime objects to ISO strings.
    - Ensures all expected fields have safe defaults.
    """
    if doc is None:
        return None

    result = dict(doc)
    result["id"] = str(doc["_id"])
    result.pop("_id", None)

    if isinstance(result.get("created_at"), datetime):
        result["created_at"] = result["created_at"].isoformat()

    # Guarantee fields always present in API responses
    result.setdefault("additional_images", [])
    result.setdefault("tags", [])
    result.setdefault("sizes", [])
    result.setdefault("colors", [])
    result.setdefault("review_count", 0)
    result.setdefault("rating", 0.0)
    result.setdefault("discount_percent", 0)
    result.setdefault("is_available", True)

    return result


# -------------------------------------------------------------------
# Expected MongoDB document shape (for documentation and import scripts)
# -------------------------------------------------------------------
PRODUCT_SCHEMA = {
    "product_id": str,           # Stable ID: "P000001"
    "name": str,                 # "Men Slim Fit Cotton T-Shirt"
    "brand": str,                # "H&M"
    "category": str,             # "Topwear"
    "subcategory": str,          # "T-Shirts"
    "description": str,          # Free-text product description
    "price": float,              # Original price in INR
    "discounted_price": float,   # Actual selling price
    "discount_percent": int,     # 0–40
    "sizes": list,               # ["S", "M", "L", "XL"]
    "colors": list,              # ["Black", "White"]
    "gender": str,               # "Men" | "Women" | "Unisex"
    "image_url": str,            # Primary product image URL
    "additional_images": list,   # Extra image URLs
    "stock": int,                # Units available
    "rating": float,             # 0.0–5.0
    "review_count": int,         # Total review count
    "tags": list,                # ["casual", "cotton", "summer"]
    "is_available": bool,        # False when stock == 0
    "created_at": datetime,
}
