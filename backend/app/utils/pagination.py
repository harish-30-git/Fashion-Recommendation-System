"""
Pagination helpers for StyleSense API.

We use offset-based pagination (page + per_page) because:
  - Simple to implement and explain.
  - Works well with MongoDB .skip() and .limit().
  - Sufficient for catalog sizes up to ~100k products.

For very large datasets, cursor-based pagination would be more efficient.
"""

from flask import Request


MAX_PER_PAGE = 100  # Hard cap — prevents clients from requesting huge pages
DEFAULT_PER_PAGE = 20


def get_pagination_params(request: Request) -> tuple[int, int]:
    """
    Extract and validate page and per_page from request query params.

    Args:
        request: Flask request object.

    Returns:
        (page, per_page) — both guaranteed to be positive integers.
    """
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    try:
        per_page = min(
            MAX_PER_PAGE,
            max(1, int(request.args.get("per_page", DEFAULT_PER_PAGE))),
        )
    except (ValueError, TypeError):
        per_page = DEFAULT_PER_PAGE

    return page, per_page


def build_pagination_meta(page: int, per_page: int, total: int) -> dict:
    """
    Build the pagination metadata dict included in list responses.

    Args:
        page:     Current page (1-indexed).
        per_page: Items per page.
        total:    Total number of matching documents.

    Returns:
        Dict with page, per_page, total, pages, has_next, has_prev.
    """
    pages = max(1, -(-total // per_page))  # Ceiling division
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
        "has_next": page < pages,
        "has_prev": page > 1,
    }


def get_skip(page: int, per_page: int) -> int:
    """Calculate MongoDB .skip() value from page number."""
    return (page - 1) * per_page
