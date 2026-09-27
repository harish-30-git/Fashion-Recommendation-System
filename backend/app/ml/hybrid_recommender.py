"""
Hybrid Recommendation Engine for StyleSense.

PURPOSE:
  Combine Content-Based Filtering, Collaborative Filtering, and User Interaction
  Signals into a unified, high-accuracy recommendation score.

ALGORITHM DESIGN & MATHEMATICAL FORMULATION:
  1. User Preference Vector Construction:
     Given user interactions with products p_i having interaction weights w_i:
       U_vec = sum(w_i * V(p_i)) / sum(w_i)
     where V(p_i) is the L2-normalized TF-IDF vector of product p_i.
     U_vec represents the centroid of user preferences in TF-IDF latent space.

  2. Candidate Generation:
     - For active users: Products similar to user preference vector + top interacted categories.
     - For cold-start users (0 interactions): Fall back to trending/popular items.

  3. Multi-Signal Scoring:
     For each candidate product c:
       - S_content(c) = CosineSimilarity(U_vec, V(c))
       - S_collab(c)  = Max or Average CF similarity between c and user's high-weight items
       - S_pref(c)    = Category & Brand affinity match score (0.0 to 1.0)

  4. Score Normalization:
     Before weighted combination, scores are normalized to [0, 1] using min-max scaling:
       S_norm = (S - min(S)) / (max(S) - min(S) + 1e-9)
     This prevents one signal from dominating simply due to differing numerical ranges.

  5. Weighted Combination:
     FinalScore(c) = w1 * S_content_norm(c) + w2 * S_collab_norm(c) + w3 * S_pref_norm(c)
     where w1 + w2 + w3 = 1.0 (configurable via config/env).

  6. Cold-Start Strategy:
     - 0 interactions: Popularity baseline / trending items.
     - 1-3 interactions: Pure content-based similarity to the interacted items.
     - 4+ interactions: Full hybrid model (content + collaborative + preference).
"""

import logging
from typing import Any
import numpy as np
from scipy.sparse import csr_matrix

from app.ml.content_recommender import ContentRecommender
from app.ml.collaborative_recommender import CollaborativeRecommender

logger = logging.getLogger(__name__)


def min_max_scale(scores: dict[str, float]) -> dict[str, float]:
    """
    Normalize a dictionary of {item_id: score} to the range [0.0, 1.0].
    Prevents any single score component from dominating purely due to scale.
    """
    if not scores:
        return {}
    vals = list(scores.values())
    min_v, max_v = min(vals), max(vals)
    denom = max_v - min_v
    if denom <= 1e-9:
        # All items have approximately the same score
        return {k: 1.0 if max_v > 0 else 0.0 for k in scores}
    return {k: float((v - min_v) / denom) for k, v in scores.items()}


class HybridRecommender:
    """
    Combines Content-based, Collaborative, and Interaction-based recommendations.
    """

    def __init__(
        self,
        content_recommender: ContentRecommender | None = None,
        collab_recommender: CollaborativeRecommender | None = None,
        w1: float = 0.5,
        w2: float = 0.3,
        w3: float = 0.2,
    ):
        """
        Args:
            content_recommender: Singleton content recommender instance.
            collab_recommender: Collaborative recommender instance.
            w1: Weight for content-based score (default 0.5)
            w2: Weight for collaborative filtering score (default 0.3)
            w3: Weight for user category/brand preference match (default 0.2)
        """
        self.content_rec = content_recommender or ContentRecommender.get_instance()
        self.collab_rec = collab_recommender or CollaborativeRecommender()
        self.w1 = w1
        self.w2 = w2
        self.w3 = w3

    def build_user_profile(
        self, user_interactions: dict[str, float]
    ) -> tuple[csr_matrix | None, set[str]]:
        """
        Construct a synthetic user preference vector in the TF-IDF feature space
        as the weighted average of vectors of products the user interacted with.

        Args:
            user_interactions: Dict mapping product_id -> interaction weight
                              e.g., {"P000001": 2.0, "P000015": 0.5}

        Returns:
            (user_preference_vector, set_of_interacted_product_ids)
        """
        if not user_interactions or not self.content_rec.is_loaded:
            return None, set()

        weighted_vecs = []
        total_weight = 0.0
        interacted_ids = set()

        for pid, weight in user_interactions.items():
            vec = self.content_rec.get_product_vector(pid)
            if vec is not None:
                weighted_vecs.append(vec.multiply(weight))
                total_weight += weight
                interacted_ids.add(pid)

        if not weighted_vecs or total_weight <= 0:
            return None, interacted_ids

        # Sum vectors and normalize by total interaction weight
        summed_vec = weighted_vecs[0]
        for v in weighted_vecs[1:]:
            summed_vec = summed_vec + v
        user_vec = summed_vec.multiply(1.0 / total_weight)

        # L2-normalize user preference vector
        norm = np.sqrt(user_vec.multiply(user_vec).sum())
        if norm > 0:
            user_vec = user_vec.multiply(1.0 / norm)

        return user_vec, interacted_ids

    def recommend_for_user(
        self,
        user_interactions: dict[str, float],
        candidate_products: list[dict[str, Any]],
        fallback_products: list[dict[str, Any]] | None = None,
        top_k: int = 10,
        exclude_interacted: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Generate ranked personalized recommendations for a user.

        Args:
            user_interactions: Dict of product_id -> total interaction weight.
            candidate_products: List of product dicts from product catalog/repository.
            fallback_products: Popular/trending products to return if user is cold-start.
            top_k: Number of recommendations requested.
            exclude_interacted: Whether to filter out products user already interacted with.

        Returns:
            List of candidate_products ranked with an added 'recommendation_score'
            and 'recommendation_reason'.
        """
        fallback_products = fallback_products or []
        interacted_ids = set(user_interactions.keys()) if user_interactions else set()

        # ---------------------------------------------------------
        # Cold-Start Check: No history
        # ---------------------------------------------------------
        if not user_interactions or len(interacted_ids) == 0:
            logger.info("Cold-start user (0 interactions): returning trending fallback.")
            results = []
            for p in fallback_products[:top_k]:
                p_copy = dict(p)
                p_copy["recommendation_score"] = float(p_copy.get("rating", 4.0)) / 5.0
                p_copy["recommendation_reason"] = "Trending popular item"
                results.append(p_copy)
            return results

        # ---------------------------------------------------------
        # Build User Profile Vector
        # ---------------------------------------------------------
        user_vec, valid_interacted = self.build_user_profile(user_interactions)
        if user_vec is None:
            # Fallback if none of the interacted products are in the ML catalog
            return fallback_products[:top_k]

        # Filter candidates (exclude unavailable & optionally exclude already interacted)
        filtered_candidates = []
        for p in candidate_products:
            pid = p.get("product_id")
            if not pid or not p.get("is_available", True):
                continue
            if exclude_interacted and pid in valid_interacted:
                continue
            filtered_candidates.append(p)

        if not filtered_candidates:
            return []

        candidate_ids = [p["product_id"] for p in filtered_candidates]

        # ---------------------------------------------------------
        # 1. Content-based Score: Cosine similarity to user profile
        # ---------------------------------------------------------
        content_raw_scores = self.content_rec.compute_scores_for_products(
            user_vec, candidate_ids
        )
        content_scores = min_max_scale(content_raw_scores)

        # ---------------------------------------------------------
        # 2. Collaborative Filtering Score
        # ---------------------------------------------------------
        collab_scores: dict[str, float] = {}
        if self.collab_rec.is_fitted:
            # Aggregate CF similarity from top-interacted products
            top_interacted = sorted(
                user_interactions.items(), key=lambda x: x[1], reverse=True
            )[:5]
            collab_accum: dict[str, float] = {pid: 0.0 for pid in candidate_ids}
            for seed_pid, weight in top_interacted:
                sims = self.collab_rec.get_scores_for_candidates(seed_pid, candidate_ids)
                for c_pid, s in sims.items():
                    collab_accum[c_pid] += s * weight
            collab_scores = min_max_scale(collab_accum)
        else:
            collab_scores = {pid: 0.0 for pid in candidate_ids}

        # ---------------------------------------------------------
        # 3. Preference Match Score (Category & Brand Affinity)
        # ---------------------------------------------------------
        # Compute category and brand frequency weights from interactions
        prod_map = {p["product_id"]: p for p in candidate_products}
        cat_weights: dict[str, float] = {}
        brand_weights: dict[str, float] = {}
        for pid, w in user_interactions.items():
            if pid in prod_map:
                cat = prod_map[pid].get("category")
                brand = prod_map[pid].get("brand")
                if cat:
                    cat_weights[cat] = cat_weights.get(cat, 0.0) + w
                if brand:
                    brand_weights[brand] = brand_weights.get(brand, 0.0) + w

        pref_scores: dict[str, float] = {}
        for p in filtered_candidates:
            pid = p["product_id"]
            cat_match = cat_weights.get(p.get("category"), 0.0)
            brand_match = brand_weights.get(p.get("brand"), 0.0)
            pref_scores[pid] = cat_match * 0.7 + brand_match * 0.3
        pref_scores = min_max_scale(pref_scores)

        # ---------------------------------------------------------
        # 4. Weighted Combination
        # ---------------------------------------------------------
        # If CF is not fitted, rebalance weights between content and pref
        if not self.collab_rec.is_fitted or all(v == 0.0 for v in collab_scores.values()):
            effective_w1 = self.w1 / (self.w1 + self.w3)
            effective_w2 = 0.0
            effective_w3 = self.w3 / (self.w1 + self.w3)
        else:
            effective_w1 = self.w1
            effective_w2 = self.w2
            effective_w3 = self.w3

        ranked_items = []
        for p in filtered_candidates:
            pid = p["product_id"]
            s_c = content_scores.get(pid, 0.0)
            s_cf = collab_scores.get(pid, 0.0)
            s_p = pref_scores.get(pid, 0.0)

            final_score = (
                effective_w1 * s_c
                + effective_w2 * s_cf
                + effective_w3 * s_p
            )

            # Generate explainability reason
            reasons = []
            if s_c > 0.5:
                reasons.append("matches your style taste")
            if s_cf > 0.4:
                reasons.append("frequently loved with items you viewed")
            if s_p > 0.4:
                reasons.append(f"from your preferred brand or category ({p.get('category')})")
            
            reason = "Recommended because it " + (" and ".join(reasons) if reasons else "fits your fashion profile")

            p_copy = dict(p)
            p_copy["recommendation_score"] = round(float(final_score), 4)
            p_copy["recommendation_reason"] = reason
            ranked_items.append(p_copy)

        # Sort descending by final score
        ranked_items.sort(key=lambda x: x["recommendation_score"], reverse=True)
        return ranked_items[:top_k]
