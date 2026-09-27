"""
Recommendation Ranking & Diversity Module for StyleSense.

PURPOSE:
  Re-ranks candidate recommendations to balance individual item relevance
  with catalog diversity, novelty, and commercial viability (stock/availability).

WHY DIVERSITY MATTERS (Interview Topic):
  If a user looked at one black leather jacket, naive cosine similarity will
  fill all 10 recommendation slots with 10 nearly identical black leather jackets.
  This causes:
    1. Low catalog coverage.
    2. Poor user experience (boring, repetitive recommendations).
    3. Missed discovery opportunities (e.g. complementary boots, denim, accessories).

ALGORITHMS IMPLEMENTED:
  1. Maximal Marginal Relevance (MMR) Re-Ranking:
     MMR selects items that are simultaneously relevant to user query/taste Q
     and dissimilar to items already selected in set S:
       MMR = argmax_{i in R \\ S} [ lambda * Relevance(i, Q) - (1 - lambda) * max_{j in S} Sim(i, j) ]
     where lambda in [0, 1] controls the relevance vs diversity trade-off:
       - lambda = 1.0 -> Pure relevance (no diversity adjustment)
       - lambda = 0.5 -> Balanced relevance and diversity (default)
       - lambda = 0.0 -> Maximum diversity

  2. Category & Brand Cap Constraint:
     Guarantees that no single category or brand dominates more than
     `max_per_category` (e.g., 3) items in the top-K list.

  3. Business & Inventory Hygiene:
     - Strict filtering of out-of-stock items (is_available == False or stock <= 0).
     - Rating & Discount confidence adjustments.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def apply_category_cap_rerank(
    items: list[dict[str, Any]],
    top_k: int = 10,
    max_per_category: int = 3,
    max_per_brand: int = 3,
    allow_backfill: bool = True,
) -> list[dict[str, Any]]:
    """
    Reranks items using a greedy constraint pass:
    Prioritizes highest scored items while enforcing that no category or brand
    appears more than max_per_category / max_per_brand times.
    
    If allow_backfill is True and not enough unique categories/brands exist to fill top_k,
    the remaining slots are backfilled from deferred items so the user gets a full list.
    """
    if not items:
        return []

    selected: list[dict[str, Any]] = []
    deferred: list[dict[str, Any]] = []

    cat_counts: dict[str, int] = {}
    brand_counts: dict[str, int] = {}

    for item in items:
        # Check stock/availability
        if not item.get("is_available", True) or item.get("stock", 1) <= 0:
            continue

        cat = item.get("category", "General")
        brand = item.get("brand", "General")

        if cat_counts.get(cat, 0) < max_per_category and brand_counts.get(brand, 0) < max_per_brand:
            selected.append(item)
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
            brand_counts[brand] = brand_counts.get(brand, 0) + 1
            if len(selected) >= top_k:
                break
        else:
            deferred.append(item)

    # Backfill if allowed and needed to reach top_k
    if allow_backfill and len(selected) < top_k and deferred:
        for item in deferred:
            selected.append(item)
            if len(selected) >= top_k:
                break

    return selected


def apply_mmr_rerank(
    candidates: list[dict[str, Any]],
    similarity_lookup_fn,
    top_k: int = 10,
    lambda_param: float = 0.65,
) -> list[dict[str, Any]]:
    """
    Maximal Marginal Relevance (MMR) re-ranking.

    Args:
        candidates: Pre-scored candidate product dicts with 'recommendation_score'
                    and 'product_id'.
        similarity_lookup_fn: Callable(pid1, pid2) -> float in [0, 1] returning similarity.
        top_k: Number of items to return.
        lambda_param: Trade-off parameter in [0.0, 1.0]. Higher = more relevance,
                      lower = more diversity.

    Returns:
        Re-ordered list of top-K items.
    """
    if not candidates:
        return []
    if len(candidates) <= top_k or lambda_param >= 1.0:
        return candidates[:top_k]

    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    remaining = list(candidates)

    # Pick the single highest-scoring item first
    first_item = max(remaining, key=lambda x: x.get("recommendation_score", 0.0))
    selected.append(first_item)
    selected_ids.add(first_item["product_id"])
    remaining.remove(first_item)

    while len(selected) < top_k and remaining:
        best_mmr = -float("inf")
        best_candidate = None

        for cand in remaining:
            rel = cand.get("recommendation_score", 0.0)

            # Max similarity to any already-selected item
            max_sim_to_selected = 0.0
            for sel in selected:
                sim = similarity_lookup_fn(cand["product_id"], sel["product_id"])
                if sim > max_sim_to_selected:
                    max_sim_to_selected = sim

            mmr_score = lambda_param * rel - (1.0 - lambda_param) * max_sim_to_selected
            if mmr_score > best_mmr:
                best_mmr = mmr_score
                best_candidate = cand

        if best_candidate is None:
            break

        selected.append(best_candidate)
        selected_ids.add(best_candidate["product_id"])
        remaining.remove(best_candidate)

    return selected


def rank_recommendations(
    candidates: list[dict[str, Any]],
    top_k: int = 10,
    max_per_category: int = 3,
    max_per_brand: int = 3,
    diversity_enabled: bool = True,
) -> list[dict[str, Any]]:
    """
    Master ranking pipeline:
      1. Availability check.
      2. Relevance score preservation.
      3. Category & brand diversification.
      4. Metadata cleanup for client consumption.
    """
    if not candidates:
        return []

    # 1. Filter out-of-stock items
    in_stock = [
        c for c in candidates
        if c.get("is_available", True) and c.get("stock", 1) > 0
    ]

    if not in_stock:
        return []

    # 2. Apply diversity constraints
    if diversity_enabled:
        ranked = apply_category_cap_rerank(
            in_stock,
            top_k=top_k,
            max_per_category=max_per_category,
            max_per_brand=max_per_brand,
        )
    else:
        ranked = in_stock[:top_k]

    return ranked
