"""
Model Evaluation Pipeline for StyleSense Recommendation Engine.

METRICS IMPLEMENTED & EXPLAINED:
  1. Precision@K:
     Formula: |Recommended@K intersect Relevant| / K
     Meaning: Fraction of recommended items in top-K that the user actually liked.
     Limitation: Assumes unobserved items are irrelevant (false negative penalty).

  2. Recall@K:
     Formula: |Recommended@K intersect Relevant| / |Relevant|
     Meaning: Fraction of all relevant items successfully retrieved in top-K.
     Limitation: Sensitive to test set size |Relevant|.

  3. NDCG@K (Normalized Discounted Cumulative Gain):
     Formula: DCG@K / IDCG@K where DCG@K = sum_{i=1}^K rel_i / log2(i + 1)
     Meaning: Position-aware metric. Highly penalizes relevant items that appear
              near the bottom of the top-K list rather than at rank 1 or 2.
     Limitation: Assumes logarithmic discount function mirrors user attention.

  4. Catalog Coverage:
     Formula: |Unique items recommended across all users| / |Catalog|
     Meaning: Proportion of inventory that ever gets recommended.
     Why critical: High precision on only 5 popular items has near-zero coverage.

  5. Intra-List Diversity (ILD):
     Formula: (2 / (K*(K-1))) * sum_{i < j} [ 1 - CosineSim(p_i, p_j) ]
     Meaning: Average pairwise distance between recommended products.
     Higher is more diverse (prevents recommendation echo chambers).

TRAIN/TEST EVALUATION PROTOCOL:
  - Uses Leave-K-Out or temporal hold-out split per user without leakage.
  - Compares:
      1. Popularity Baseline (most interacted / highest rated)
      2. Content-Based Filtering
      3. Collaborative Filtering (if sufficient interactions)
      4. Hybrid Recommender
"""

import math
import logging
from typing import Any
import numpy as np

logger = logging.getLogger(__name__)


def compute_precision_at_k(recommended_ids: list[str], ground_truth_ids: set[str], k: int = 10) -> float:
    """Compute Precision@K."""
    if k <= 0 or not recommended_ids or not ground_truth_ids:
        return 0.0
    rec_k = recommended_ids[:k]
    hits = sum(1 for pid in rec_k if pid in ground_truth_ids)
    return hits / float(k)


def compute_recall_at_k(recommended_ids: list[str], ground_truth_ids: set[str], k: int = 10) -> float:
    """Compute Recall@K."""
    if not ground_truth_ids or not recommended_ids or k <= 0:
        return 0.0
    rec_k = recommended_ids[:k]
    hits = sum(1 for pid in rec_k if pid in ground_truth_ids)
    return hits / float(len(ground_truth_ids))


def compute_ndcg_at_k(recommended_ids: list[str], ground_truth_ids: set[str], k: int = 10) -> float:
    """
    Compute Normalized Discounted Cumulative Gain (NDCG@K) with binary relevance.
    """
    if not ground_truth_ids or not recommended_ids or k <= 0:
        return 0.0

    rec_k = recommended_ids[:k]
    dcg = 0.0
    for idx, pid in enumerate(rec_k):
        if pid in ground_truth_ids:
            # Rank is 1-indexed (idx + 1)
            dcg += 1.0 / math.log2((idx + 1) + 1)

    # Ideal DCG (all hits positioned at top ranks)
    ideal_hits = min(k, len(ground_truth_ids))
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_hits + 1))

    if idcg <= 0.0:
        return 0.0
    return dcg / idcg


def compute_intra_list_diversity(
    recommended_ids: list[str],
    similarity_fn,
    k: int = 10,
) -> float:
    """
    Compute Intra-List Diversity (ILD) as the average pairwise distance
    (1 - cosine_similarity) between recommended items.
    """
    rec_k = recommended_ids[:k]
    n = len(rec_k)
    if n < 2:
        return 0.0

    total_dist = 0.0
    pairs_count = 0

    for i in range(n):
        for j in range(i + 1, n):
            sim = similarity_fn(rec_k[i], rec_k[j])
            dist = max(0.0, 1.0 - sim)
            total_dist += dist
            pairs_count += 1

    return total_dist / float(pairs_count) if pairs_count > 0 else 0.0


def compute_catalog_coverage(all_recommended_ids: list[list[str]], total_catalog_size: int, k: int = 10) -> float:
    """Compute the fraction of catalog items recommended at least once."""
    if total_catalog_size <= 0:
        return 0.0
    unique_recs = set()
    for rec_list in all_recommended_ids:
        unique_recs.update(rec_list[:k])
    return len(unique_recs) / float(total_catalog_size)


class EvaluationEngine:
    """
    Orchestrates the evaluation of recommendation strategies on held-out interaction data.
    """

    def __init__(self, content_rec, hybrid_rec, catalog_products: list[dict[str, Any]]):
        self.content_rec = content_rec
        self.hybrid_rec = hybrid_rec
        self.catalog_products = catalog_products
        self.catalog_ids = [p["product_id"] for p in catalog_products]
        self.prod_map = {p["product_id"]: p for p in catalog_products}

    def _sim_lookup(self, pid1: str, pid2: str) -> float:
        """Lookup pairwise cosine similarity between two products."""
        v1 = self.content_rec.get_product_vector(pid1)
        v2 = self.content_rec.get_product_vector(pid2)
        if v1 is None or v2 is None:
            return 0.0
        return float((v1 @ v2.T).toarray()[0, 0])

    def evaluate_test_users(
        self,
        test_user_profiles: list[dict[str, Any]],
        k: int = 10,
    ) -> dict[str, Any]:
        """
        Runs full comparative benchmark across:
          1. Popularity Baseline
          2. Content-Based
          3. Hybrid Recommender

        Args:
            test_user_profiles: List of dicts, each having:
                - 'train_interactions': dict of {product_id: weight}
                - 'test_relevant_ids': set of product_ids held out for testing
            k: Top-K evaluation cutoff.

        Returns:
            Dict containing detailed metric comparisons and explanations.
        """
        strategies = ["Popularity Baseline", "Content-Based", "Hybrid Recommender"]
        metrics = {
            strat: {
                "precision": [],
                "recall": [],
                "ndcg": [],
                "ild": [],
                "all_recs": [],
            }
            for strat in strategies
        }

        # Popularity baseline items sorted by rating and review count
        pop_sorted = sorted(
            self.catalog_products,
            key=lambda x: (x.get("rating", 0) * math.log(x.get("review_count", 0) + 1)),
            reverse=True,
        )
        pop_ids = [p["product_id"] for p in pop_sorted]

        for user in test_user_profiles:
            train_history = user["train_interactions"]
            ground_truth = set(user["test_relevant_ids"])

            if not ground_truth:
                continue

            # 1. Popularity Baseline
            rec_pop = [pid for pid in pop_ids if pid not in train_history][:k]
            metrics["Popularity Baseline"]["precision"].append(compute_precision_at_k(rec_pop, ground_truth, k))
            metrics["Popularity Baseline"]["recall"].append(compute_recall_at_k(rec_pop, ground_truth, k))
            metrics["Popularity Baseline"]["ndcg"].append(compute_ndcg_at_k(rec_pop, ground_truth, k))
            metrics["Popularity Baseline"]["ild"].append(compute_intra_list_diversity(rec_pop, self._sim_lookup, k))
            metrics["Popularity Baseline"]["all_recs"].append(rec_pop)

            # 2. Content-Based Recommender (using top train item as seed)
            if train_history:
                top_seed = max(train_history.items(), key=lambda x: x[1])[0]
                similar_tuples = self.content_rec.get_similar_products(top_seed, top_k=k, exclude_ids=set(train_history.keys()))
                rec_cb = [pid for pid, _ in similar_tuples]
            else:
                rec_cb = rec_pop

            metrics["Content-Based"]["precision"].append(compute_precision_at_k(rec_cb, ground_truth, k))
            metrics["Content-Based"]["recall"].append(compute_recall_at_k(rec_cb, ground_truth, k))
            metrics["Content-Based"]["ndcg"].append(compute_ndcg_at_k(rec_cb, ground_truth, k))
            metrics["Content-Based"]["ild"].append(compute_intra_list_diversity(rec_cb, self._sim_lookup, k))
            metrics["Content-Based"]["all_recs"].append(rec_cb)

            # 3. Hybrid Recommender
            hybrid_recs = self.hybrid_rec.recommend_for_user(
                user_interactions=train_history,
                candidate_products=self.catalog_products,
                fallback_products=pop_sorted,
                top_k=k,
                exclude_interacted=True,
            )
            rec_hybrid = [p["product_id"] for p in hybrid_recs]
            metrics["Hybrid Recommender"]["precision"].append(compute_precision_at_k(rec_hybrid, ground_truth, k))
            metrics["Hybrid Recommender"]["recall"].append(compute_recall_at_k(rec_hybrid, ground_truth, k))
            metrics["Hybrid Recommender"]["ndcg"].append(compute_ndcg_at_k(rec_hybrid, ground_truth, k))
            metrics["Hybrid Recommender"]["ild"].append(compute_intra_list_diversity(rec_hybrid, self._sim_lookup, k))
            metrics["Hybrid Recommender"]["all_recs"].append(rec_hybrid)

        # Aggregate averages
        report = {
            "eval_cutoff_k": k,
            "test_users_count": len(test_user_profiles),
            "catalog_size": len(self.catalog_products),
            "results": {},
        }

        for strat in strategies:
            p_mean = float(np.mean(metrics[strat]["precision"])) if metrics[strat]["precision"] else 0.0
            r_mean = float(np.mean(metrics[strat]["recall"])) if metrics[strat]["recall"] else 0.0
            ndcg_mean = float(np.mean(metrics[strat]["ndcg"])) if metrics[strat]["ndcg"] else 0.0
            ild_mean = float(np.mean(metrics[strat]["ild"])) if metrics[strat]["ild"] else 0.0
            coverage = compute_catalog_coverage(metrics[strat]["all_recs"], len(self.catalog_products), k)

            report["results"][strat] = {
                f"Precision@{k}": round(p_mean, 4),
                f"Recall@{k}": round(r_mean, 4),
                f"NDCG@{k}": round(ndcg_mean, 4),
                f"Coverage": round(coverage, 4),
                f"Intra-List Diversity": round(ild_mean, 4),
            }

        return report
