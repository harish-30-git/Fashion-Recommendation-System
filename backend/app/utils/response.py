"""
Standardized JSON response helpers for StyleSense API.

All API responses use the same envelope format:
{
    "success": true,
    "data": { ... },
    "message": "optional",
    "pagination": { ... }   # only on paginated endpoints
}

Centralizing response construction here means:
  - Consistent format across all endpoints.
  - Easy to add fields (e.g., a request_id) in one place.
  - Route handlers stay thin and readable.
"""

from flask import jsonify
from typing import Any


def success_response(
    data: Any = None,
    message: str | None = None,
    status_code: int = 200,
    pagination: dict | None = None,
) -> tuple:
    """Build a successful JSON response."""
    body: dict = {"success": True}
    if data is not None:
        body["data"] = data
    if message:
        body["message"] = message
    if pagination:
        body["pagination"] = pagination
    return jsonify(body), status_code


def error_response(
    error_code: str,
    message: str,
    status_code: int = 400,
    details: dict | None = None,
) -> tuple:
    """
    Build an error JSON response.

    Args:
        error_code: Machine-readable uppercase error code (e.g., "PRODUCT_NOT_FOUND").
        message:    Human-readable description shown to the user / developer.
        status_code: HTTP status code.
        details:    Optional additional fields (e.g., validation field errors).
    """
    body: dict = {
        "success": False,
        "error": error_code,
        "message": message,
    }
    if details:
        body["details"] = details
    return jsonify(body), status_code
