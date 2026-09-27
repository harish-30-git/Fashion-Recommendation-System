"""
Recommendation Service for StyleSense.

Bridges Flask routes with the ML Recommendation Engine, database repositories,
and business ranking rules.
"""

from typing import Any
import logging

from app.ml.content_recommender import ContentRecommender
from app.ml.collaborative_recommender import CollaborativeRecommender
from app.ml.hybrid_recommender import HybridRecommender
from app.ml.ranking import rank_recommendations
from app.repositories.product_repository import ProductRepository
from app.repositories.interaction_repository import InteractionRepository

logger = logging.getLogger(__name__)

# Category complementary pairings map for fashion outfit suggestions
COMPLEMENTARY_CATEGORY_MAP: dict[str, list[str]] = {
    "Topwear": ["Bottomwear", "Footwear", "Accessories", "Watches"],
    "Bottomwear": ["Topwear", "Footwear", "Accessories", "Bags"],
    "Footwear": ["Topwear", "Bottomwear", "Accessories", "Bags"],
    "Ethnic": ["Accessories", "Footwear", "Bags"],
    "Bags": ["Topwear", "Bottomwear", "Footwear"],
    "Accessories": ["Topwear", "Bottomwear", "Footwear"],
    "Watches": ["Topwear", "Bottomwear", "Accessories"],
    "Sportswear": ["Footwear", "Accessories"],
    "Innerwear": ["Topwear", "Bottomwear"],
}


class RecommendationService:
    def __init__(
        self,
        product_repo: ProductRepository,
        interaction_repo: InteractionRepository,
        hybrid_w1: float = 0.5,
        hybrid_w2: float = 0.3,
        hybrid_w3: float = 0.2,
    ):
        self.product_repo = product_repo
        self.interaction_repo = interaction_repo

        # Initialize ML recommenders
        self.content_rec = ContentRecommender.get_instance()
        self.content_rec.load()

        self.collab_rec = CollaborativeRecommender()
        # Lazily fit CF if interaction matrix exists
        try:
            interaction_matrix = self.interaction_repo.get_all_interactions_matrix()
            if interaction_matrix:
                self.collab_rec.fit(interaction_matrix)
        except Exception as e:
            logger.warning("Could not pre-fit CollaborativeRecommender: %s", e)

        self.hybrid_rec = HybridRecommender(
            content_recommender=self.content_rec,
            collab_recommender=self.collab_rec,
            w1=hybrid_w1,
            w2=hybrid_w2,
            w3=hybrid_w3,
        )

    def get_personalized(self, user_id: str | None, top_k: int = 10) -> list[dict[str, Any]]:
        """
        Personalized recommendations for user using Hybrid Recommender + Diversity Ranking.
        Falls back to trending if user is anonymous or has 0 interactions.
        """
        trending_fallback = self.product_repo.get_trending(top_k=top_k * 2)
        for item in trending_fallback:
            item.setdefault("recommendation_reason", "Trending popular item")
            item.setdefault("recommendation_score", round(float(item.get("rating", 4.0)) / 5.0, 4))

        if not user_id:
            return trending_fallback[:top_k]

        user_weights = self.interaction_repo.get_user_product_weights(user_id)
        if not user_weights:
            # Cold-start user
            return trending_fallback[:top_k]

        # Fetch candidate products (up to 300 available products for real-time ranking)
        candidates, _ = self.product_repo.find_all(per_page=300, available_only=True)

        hybrid_ranked = self.hybrid_rec.recommend_for_user(
            user_interactions=user_weights,
            candidate_products=candidates,
            fallback_products=trending_fallback,
            top_k=top_k * 2,
            exclude_interacted=True,
        )

        # Apply category and brand diversity re-ranking
        final_ranked = rank_recommendations(
            candidates=hybrid_ranked,
            top_k=top_k,
            max_per_category=3,
            max_per_brand=3,
            diversity_enabled=True,
        )

        return final_ranked

    def get_similar(self, product_id: str, top_k: int = 10) -> list[dict[str, Any]]:
        """
        Content-based similar items for product detail pages.
        """
        similar_tuples = self.content_rec.get_similar_products(product_id, top_k=top_k)
        if not similar_tuples:
            return []

        pids = [pid for pid, _ in similar_tuples]
        score_map = {pid: score for pid, score in similar_tuples}

        products = self.product_repo.find_by_ids(pids)
        for p in products:
            p["similarity_score"] = score_map.get(p["product_id"], 0.0)

        # Preserve descending score order
        products.sort(key=lambda x: x.get("similarity_score", 0.0), reverse=True)
        return products

    def get_trending(self, category: str | None = None, top_k: int = 20) -> list[dict[str, Any]]:
        """Fetch trending popular products."""
        return self.product_repo.get_trending(category=category, top_k=top_k)

    def get_complementary(self, product_id: str, top_k: int = 6) -> list[dict[str, Any]]:
        """
        Recommend complementary items to build a complete outfit / fashion ensemble.
        Example: Seed product is a Topwear Shirt -> Recommends Bottomwear Trousers, Shoes, Watch.
        """
        seed_product = self.product_repo.find_by_id(product_id)
        if not seed_product:
            return []

        seed_cat = seed_product.get("category", "")
        seed_gender = seed_product.get("gender", "Unisex")
        comp_cats = COMPLEMENTARY_CATEGORY_MAP.get(seed_cat, ["Accessories", "Footwear"])

        # Fetch candidate products in complementary categories with matching target gender
        results = []
        for cat in comp_cats:
            items, _ = self.product_repo.find_all(
                category=cat,
                gender=seed_gender if seed_gender in ("Men", "Women") else None,
                per_page=top_k,
                sort_by="popularity",
                available_only=True,
            )
            if items:
                # Pick the best matching complementary item from this category
                results.append(items[0])
            if len(results) >= top_k:
                break

        return results[:top_k]
