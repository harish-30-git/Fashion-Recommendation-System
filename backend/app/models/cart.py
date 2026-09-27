"""
Cart document schema for MongoDB.

Design decisions:
  - One cart document per user (user_id is the unique key).
  - Items are embedded as an array inside the cart document.
    This makes reading the full cart a single document fetch (O(1)).
  - unit_price is snapshotted at add-to-cart time.
    If the product price changes later, the cart reflects the price
    at the time the item was added. The final total is always
    recomputed on the backend from stored unit_prices — never from
    a price submitted by the frontend.

Interview note: In a production system you might also record a
price_validity_timestamp and warn users if a price has changed
significantly since they added the item.
"""

from datetime import datetime, timezone


def build_cart_item(
    product_id: str,
    quantity: int,
    size: str,
    color: str,
    unit_price: float,
) -> dict:
    """Build a single cart item dict to embed in the cart document."""
    return {
        "product_id": product_id,
        "quantity": quantity,
        "size": size,
        "color": color,
        "unit_price": round(unit_price, 2),  # Price snapshotted at add time
        "added_at": datetime.now(timezone.utc),
    }


def compute_cart_total(items: list[dict]) -> float:
    """
    Calculate cart total from stored unit prices.

    This is called on the backend and never trusts prices from the client.
    """
    return round(sum(item["unit_price"] * item["quantity"] for item in items), 2)


def serialize_cart(doc: dict) -> dict:
    """Convert raw MongoDB cart document to JSON-safe dict."""
    if doc is None:
        return {"items": [], "total": 0.0}

    items = doc.get("items", [])
    serialized_items = []
    for item in items:
        i = dict(item)
        if isinstance(i.get("added_at"), datetime):
            i["added_at"] = i["added_at"].isoformat()
        serialized_items.append(i)

    return {
        "id": str(doc["_id"]),
        "user_id": str(doc["user_id"]),
        "items": serialized_items,
        "total": compute_cart_total(items),
        "item_count": sum(i.get("quantity", 1) for i in items),
    }
