"""
Wishlist Service for StyleSense.

Supports:
  - Add / remove saved products with duplicate prevention.
  - Hydrated product display for wishlist screen.
  - Wishlist-driven recommendation discovery (recommend similar items based on wishlist).
"""

from typing import Any
from app.repositories.wishlist_repository import WishlistRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.interaction_repository import InteractionRepository
from app.ml.content_recommender import ContentRecommender


class WishlistService:
    def __init__(
        self,
        wishlist_repo: WishlistRepository,
        product_repo: ProductRepository,
        interaction_repo: InteractionRepository | None = None,
        interaction_weights: dict[str, float] | None = None,
    ):
        self.wishlist_repo = wishlist_repo
        self.product_repo = product_repo
        self.interaction_repo = interaction_repo
        self.weights = interaction_weights or {"wishlist": 1.5}
        self.content_rec = ContentRecommender.get_instance()

    def get_wishlist(self, user_id: str) -> list[dict[str, Any]]:
        """Fetch all products in the user's wishlist."""
        pids = self.wishlist_repo.get_by_user(user_id)
        if not pids:
            return []
        return self.product_repo.find_by_ids(pids)

    def add_to_wishlist(self, user_id: str, product_id: str) -> tuple[bool, str | None]:
        """
        Add a product to the user's wishlist.
        Guaranteed idempotent by compound unique index on (user_id, product_id).
        """
        product = self.product_repo.find_by_id(product_id)
        if not product:
            return False, "Product not found."

        success, already_existed = self.wishlist_repo.add(user_id, product_id)

        # Log wishlist interaction for personalized ML recommendations
        if success and not already_existed and self.interaction_repo:
            try:
                self.interaction_repo.log(
                    user_id=user_id,
                    product_id=product_id,
                    interaction_type="wishlist",
                    weights=self.weights,
                )
            except Exception:
                pass

        return True, None

    def remove_from_wishlist(self, user_id: str, product_id: str) -> bool:
        """Remove product from wishlist."""
        return self.wishlist_repo.remove(user_id, product_id)

    def get_similar_from_wishlist(self, user_id: str, top_k: int = 10) -> list[dict[str, Any]]:
        """
        Generate recommendations inspired specifically by items currently in the user's wishlist.
        """
        wishlist_pids = self.wishlist_repo.get_by_user(user_id)
        if not wishlist_pids:
            return []

        # Find similar items for each wishlist product, excluding items already in wishlist
        wishlist_set = set(wishlist_pids)
        accum_scores: dict[str, float] = {}

        for seed_pid in wishlist_pids[:5]:
            similars = self.content_rec.get_similar_products(
                seed_pid, top_k=top_k, exclude_ids=wishlist_set
            )
            for cand_id, score in similars:
                accum_scores[cand_id] = max(accum_scores.get(cand_id, 0.0), score)

        if not accum_scores:
            return []

        sorted_cand_ids = sorted(accum_scores.keys(), key=lambda x: accum_scores[x], reverse=True)[:top_k]
        products = self.product_repo.find_by_ids(sorted_cand_ids)

        for p in products:
            p["similarity_score"] = accum_scores.get(p["product_id"], 0.0)
            p["recommendation_reason"] = "Similar to items in your wishlist"

        return products
