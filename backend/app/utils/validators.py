"""
Request validation helpers for StyleSense.

These are simple, reusable validators used inside route handlers.
They raise no exceptions — they return a (is_valid, error_message) tuple
so the calling route can decide how to respond.
"""

import re
from typing import Any


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
VALID_INTERACTION_TYPES = {"view", "wishlist", "cart", "purchase"}
VALID_SORT_FIELDS = {"price_asc", "price_desc", "rating", "popularity"}
VALID_GENDERS = {"Men", "Women", "Unisex"}


def validate_register(data: dict) -> tuple[bool, str | None]:
    """Validate user registration payload."""
    required = ["email", "username", "password", "full_name"]
    for field in required:
        if not data.get(field):
            return False, f"'{field}' is required."

    if not EMAIL_REGEX.match(data["email"]):
        return False, "Invalid email address."

    if len(data["password"]) < 8:
        return False, "Password must be at least 8 characters."

    username = data["username"]
    if not (3 <= len(username) <= 30):
        return False, "Username must be 3–30 characters."

    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "Username may only contain letters, digits, and underscores."

    return True, None


def validate_login(data: dict) -> tuple[bool, str | None]:
    """Validate login payload."""
    if not data.get("email") or not data.get("password"):
        return False, "Email and password are required."
    return True, None


def validate_interaction(data: dict) -> tuple[bool, str | None]:
    """Validate interaction log payload."""
    if not data.get("product_id"):
        return False, "'product_id' is required."
    interaction_type = data.get("interaction_type")
    if interaction_type not in VALID_INTERACTION_TYPES:
        return False, (
            f"'interaction_type' must be one of: "
            f"{', '.join(sorted(VALID_INTERACTION_TYPES))}."
        )
    return True, None


def validate_cart_item(data: dict) -> tuple[bool, str | None]:
    """Validate add-to-cart payload."""
    if not data.get("product_id"):
        return False, "'product_id' is required."
    quantity = data.get("quantity", 1)
    if not isinstance(quantity, int) or quantity < 1:
        return False, "'quantity' must be a positive integer."
    return True, None


def validate_positive_int(value: Any, field_name: str) -> tuple[bool, str | None]:
    """Generic positive integer validator."""
    try:
        v = int(value)
        if v < 1:
            raise ValueError
        return True, None
    except (TypeError, ValueError):
        return False, f"'{field_name}' must be a positive integer."
