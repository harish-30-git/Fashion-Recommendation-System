"""
Collaborative Filtering Recommender for StyleSense.

ALGORITHM: Item-Item Collaborative Filtering

WHAT IS COLLABORATIVE FILTERING?
  Unlike content-based filtering (which uses product attributes),
  collaborative filtering says: "Products that were liked by the same
  users tend to be similar, regardless of their attributes."

  Example: If users who buy running shoes also tend to buy sports socks,
  then running shoes and sports socks are "collaboratively similar" —
  even though they are very different products by content.

HOW ITEM-ITEM CF WORKS:
  1. Build a user-item interaction matrix M where:
       M[user_id][product_id] = total_interaction_weight
     e.g., user A: {P001: 2.5, P042: 3.0}, user B: {P001: 1.5, P099: 2.0}

  2. For each pair of products (i, j), compute their similarity as the
     cosine similarity of their interaction columns:
       sim(i, j) = (col_i · col_j) / (||col_i|| × ||col_j||)

  3. To find similar items for product X:
     Return the top-K products with highest sim(X, _).

LIMITATION — COLD START PROBLEM:
  Collaborative filtering requires interaction data. Without it, we
  cannot compute meaningful item similarities. In our system:
  - New products (0 interactions): CF returns nothing → fallback to content-based.
  - Products with few interactions: CF signal is weak → blend with content-based.
  - Dense interaction data: CF is most powerful here.

  For our synthetic dataset with NO real interaction data, CF will
  gracefully return empty results and the hybrid recommender will
  rely entirely on content-based signals.

COMPARISON: Item-Item vs User-User CF
  We use item-item (not user-user) because:
  - Item similarities are more stable over time than user preferences.
  - Much fewer items (1k) than users (potentially millions) — efficient.
  - Amazon pioneered item-item CF in 2003 for exactly this reason.

INTERVIEW TALKING POINTS:
  - Why not matrix factorization (SVD/ALS)? Would require more data and
    offline training. Item-item CF is interpretable and works online.
  - Sparsity problem: Most user-item matrices are 99%+ sparse.
    We use scipy sparse matrices to handle this efficiently.
"""

import logging

import numpy as np
from scipy.sparse import csr_matrix

logger = logging.getLogger(__name__)

# Minimum number of users who must have interacted with a product
# for it to be considered in collaborative filtering.
MIN_INTERACTIONS_THRESHOLD = 2


class CollaborativeRecommender:
    """
    Item-item collaborative filtering recommender.

    Builds an item similarity model from the user-product interaction matrix.
    Must be retrained (via .fit()) whenever interactions change significantly.
    """

    def __init__(self):
        self.item_similarity: dict[str, list[tuple[str, float]]] = {}
        # Maps product_id → [(similar_product_id, score), ...]
        self._fitted = False
        self._interaction_count = 0

    def fit(self, interaction_matrix: dict[str, dict[str, float]]) -> None:
        """
        Build the item-item similarity model from the interaction matrix.

        Args:
            interaction_matrix: Dict mapping user_id_str → {product_id → weight}
                                 Fetched from InteractionRepository.get_all_interactions_matrix()

        Algorithm:
          1. Extract unique product IDs and user IDs.
          2. Build a sparse product × user matrix P where P[i][j] = weight.
          3. Compute item-item similarity: S = normalize(P) × normalize(P).T
             (This is the cosine similarity matrix of all product pairs.)
          4. Store the top-N most similar items for each product.
        """
        if not interaction_matrix:
            logger.warning(
                "CollaborativeRecommender.fit() called with empty interaction matrix. "
                "No real user data yet. CF will return empty results. "
                "This is expected for a new system — accumulate user interactions first."
            )
            self._fitted = False
            return

        self._interaction_count = sum(len(v) for v in interaction_matrix.values())
        logger.info(
            "Fitting collaborative recommender: %d users, %d total interactions",
            len(interaction_matrix),
            self._interaction_count,
        )

        # --- Build user and product index mappings ---
        all_products: list[str] = sorted(
            {pid for user_data in interaction_matrix.values() for pid in user_data}
        )
        all_users: list[str] = sorted(interaction_matrix.keys())

        if len(all_products) < 2 or len(all_users) < MIN_INTERACTIONS_THRESHOLD:
            logger.warning(
                "Insufficient interaction data for CF (%d products, %d users). "
                "Need at least %d users. CF disabled.",
                len(all_products),
                len(all_users),
                MIN_INTERACTIONS_THRESHOLD,
            )
            self._fitted = False
            return

        product_to_idx = {pid: i for i, pid in enumerate(all_products)}
        user_to_idx = {uid: j for j, uid in enumerate(all_users)}

        # --- Build sparse product × user weight matrix ---
        rows, cols, data = [], [], []
        for uid, products in interaction_matrix.items():
            j = user_to_idx[uid]
            for pid, weight in products.items():
                i = product_to_idx[pid]
                rows.append(i)
                cols.append(j)
                data.append(weight)

        n_products = len(all_products)
        n_users = len(all_users)
        P = csr_matrix((data, (rows, cols)), shape=(n_products, n_users))

        # --- L2-normalize each product row ---
        # After normalization: P[i] · P[j] = cosine_similarity(i, j)
        norms = np.sqrt(P.multiply(P).sum(axis=1)).A1  # Row norms
        norms[norms == 0] = 1  # Prevent division by zero
        from scipy.sparse import diags
        normalizer = diags(1.0 / norms)
        P_norm = normalizer @ P  # Normalized product-user matrix

        # --- Compute item-item cosine similarity ---
        # S = P_norm × P_norm.T  →  shape: (n_products, n_products)
        # S[i][j] = cosine similarity between product i and product j
        # NOTE: For large catalogs (44k products), this matrix is 44k² = 2B entries.
        # We only store the top-N per product to manage memory.
        S = (P_norm @ P_norm.T).toarray()

        # --- Store top-N similar items per product ---
        TOP_N_PER_ITEM = 20  # Store more than we return, for flexible queries
        self.item_similarity = {}

        for i, pid in enumerate(all_products):
            sim_row = S[i].copy()
            sim_row[i] = 0  # Exclude self-similarity
            top_indices = np.argsort(sim_row)[::-1][:TOP_N_PER_ITEM]
            self.item_similarity[pid] = [
                (all_products[j], float(sim_row[j]))
                for j in top_indices
                if sim_row[j] > 0
            ]

        self._fitted = True
        logger.info(
            "CollaborativeRecommender fitted: %d products with CF similarities.",
            len(self.item_similarity),
        )

    def get_similar_items(
        self,
        product_id: str,
        top_k: int = 10,
        exclude_ids: set[str] | None = None,
    ) -> list[tuple[str, float]]:
        """
        Return top-K items similar to product_id based on interaction patterns.

        Returns:
            List of (product_id, similarity_score) or empty list if CF unavailable.
        """
        if not self._fitted:
            return []

        similar = self.item_similarity.get(product_id, [])

        if exclude_ids:
            similar = [(pid, s) for pid, s in similar if pid not in exclude_ids]

        return similar[:top_k]

    def get_scores_for_candidates(
        self, product_id: str, candidate_ids: list[str]
    ) -> dict[str, float]:
        """
        Return CF similarity scores for a list of candidate products
        relative to a given product.

        Used by the hybrid ranker to blend CF scores with content scores.
        """
        if not self._fitted:
            return {pid: 0.0 for pid in candidate_ids}

        all_similar = {pid: score for pid, score in self.item_similarity.get(product_id, [])}
        return {pid: all_similar.get(pid, 0.0) for pid in candidate_ids}

    @property
    def is_fitted(self) -> bool:
        return self._fitted

    @property
    def interaction_count(self) -> int:
        return self._interaction_count
