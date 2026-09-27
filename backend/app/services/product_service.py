"""
Product Service for StyleSense.

Orchestrates catalog queries, filters, search, and pagination.
"""

from typing import Any
from app.repositories.product_repository import ProductRepository
from app.utils.pagination import build_pagination_meta


class ProductService:
    def __init__(self, product_repo: ProductRepository):
        self.product_repo = product_repo

    def get_products(
        self,
        page: int = 1,
        per_page: int = 20,
        category: str | None = None,
        brand: str | None = None,
        gender: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        size: str | None = None,
        color: str | None = None,
        sort_by: str | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """
        Fetch filtered, sorted, paginated products.

        Returns:
            (items_list, pagination_metadata_dict)
        """
        items, total = self.product_repo.find_all(
            page=page,
            per_page=per_page,
            category=category,
            brand=brand,
            gender=gender,
            min_price=min_price,
            max_price=max_price,
            size=size,
            color=color,
            sort_by=sort_by,
            available_only=True,
        )
        pagination = build_pagination_meta(page, per_page, total)
        return items, pagination

    def get_product_by_id(self, product_id: str) -> dict[str, Any] | None:
        """Fetch full details for a product by its product_id string."""
        return self.product_repo.find_by_id(product_id)

    def search_products(
        self,
        query: str,
        page: int = 1,
        per_page: int = 20,
        category: str | None = None,
        gender: str | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """
        Full-text catalog search.

        Returns:
            (items_list, pagination_metadata_dict)
        """
        clean_q = query.strip()
        if not clean_q:
            return self.get_products(page=page, per_page=per_page, category=category, gender=gender)

        items, total = self.product_repo.search(
            query=clean_q,
            page=page,
            per_page=per_page,
            category=category,
            gender=gender,
        )
        pagination = build_pagination_meta(page, per_page, total)
        return items, pagination

    def get_categories(self) -> list[str]:
        """Fetch distinct categories for filter UI."""
        return self.product_repo.get_categories()

    def get_brands(self, category: str | None = None) -> list[str]:
        """Fetch distinct brands for filter UI."""
        return self.product_repo.get_brands(category=category)
