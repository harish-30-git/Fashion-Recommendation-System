"""
Interaction Tracking Service for StyleSense.

Records user interactions (views, wishlists, carts, purchases) and feeds
signal into the recommendation models.
"""

from typing import Any
from app.repositories.interaction_repository import InteractionRepository
from app.repositories.product_repository import ProductRepository
from app.utils.validators import validate_interaction
from app.utils.pagination import build_pagination_meta


class InteractionService:
    def __init__(
        self,
        interaction_repo: InteractionRepository,
        product_repo: ProductRepository,
        weights: dict[str, float] | None = None,
    ):
        self.interaction_repo = interaction_repo
        self.product_repo = product_repo
        self.weights = weights or {"view": 0.5, "wishlist": 1.5, "cart": 2.0, "purchase": 3.0}

    def log(
        self,
        user_id: str,
        product_id: str,
        interaction_type: str,
        session_id: str | None = None,
    ) -> tuple[dict[str, Any] | None, str | None]:
        """
        Log an explicit user action.

        Returns:
            (logged_doc, error_message)
        """
        is_valid, error = validate_interaction(
            {"product_id": product_id, "interaction_type": interaction_type}
        )
        if not is_valid:
            return None, error

        # Verify product exists
        product = self.product_repo.find_by_id(product_id)
        if not product:
            return None, "Product not found."

        doc = self.interaction_repo.log(
            user_id=user_id,
            product_id=product_id,
            interaction_type=interaction_type,
            weights=self.weights,
            session_id=session_id,
        )
        return doc, None

    def get_history(
        self,
        user_id: str,
        interaction_type: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """
        Retrieve paginated interaction history for the user.
        """
        items, total = self.interaction_repo.find_by_user(
            user_id=user_id,
            interaction_type=interaction_type,
            page=page,
            per_page=per_page,
        )
        pagination = build_pagination_meta(page, per_page, total)
        return items, pagination
