"""
Content-Based Recommender for StyleSense.

ALGORITHM: TF-IDF + Cosine Similarity

HOW IT WORKS (step by step):
  1. At startup, load the pre-trained TF-IDF sparse matrix from disk.
     - Shape: (n_products, n_features) e.g. (1000, 2161)
     - Each row is a unit L2-normalized vector for one product.
     - Built from: name + description + category + subcategory + brand + color + tags

  2. For a query product at index i:
     - Extract row vector: query = tfidf_matrix[i]  → shape (1, n_features)
     - Compute dot product against all rows: sims = tfidf_matrix @ query.T
     - Because TF-IDF applies L2-norm by default, dot product = cosine similarity.
     - Result: vector of length n_products, values in [-1, 1] (always ≥0 for TF-IDF)

  3. Sort by similarity descending, take top-K (excluding the query product itself).

TIME COMPLEXITY per query:
  - Sparse dot product: O(n × d_nnz) where d_nnz ≈ average non-zeros per row
  - For our 1000×2161 matrix (1.87% non-zero): ~38 non-zeros/row
  - ≈ 1000 × 38 = 38,000 multiplications per query → effectively instant

SPACE COMPLEXITY:
  - Sparse matrix: O(nnz) = O(40,500) floats ≈ 316 KB
  - Dense equivalent: 1000 × 2161 × 4 bytes ≈ 8.2 MB (not bad at 1k products,
    but grows to ~1.5 GB at 44k products → sparse is critical for real catalogs)

CACHING:
  - The TF-IDF matrix and product_id→index mapping are loaded ONCE into memory
  - Subsequent calls reuse the same in-memory objects (no disk I/O per request)
  - This is implemented via a singleton ContentRecommender instance
"""

import logging
from functools import lru_cache

import numpy as np

from app.ml.feature_engineering import load_tfidf_artifacts

logger = logging.getLogger(__name__)


class ContentRecommender:
    """
    Singleton class that holds the TF-IDF matrix in memory and
    answers similarity queries without recomputing from scratch.

    Usage:
        rec = ContentRecommender.get_instance()
        rec.load()  # Called once at app startup
        similar = rec.get_similar_products("P000042", top_k=10)
    """

    _instance = None

    def __init__(self):
        self.tfidf_matrix = None      # scipy sparse matrix (n_products × n_features)
        self.vectorizer = None        # fitted TfidfVectorizer (for query-time transforms)
        self.product_ids: list[str] = []
        self.product_id_to_idx: dict[str, int] = {}
        self._loaded: bool = False

    @classmethod
    def get_instance(cls) -> "ContentRecommender":
        """Return the singleton instance, creating it if necessary."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load(self) -> bool:
        """
        Load pre-trained TF-IDF artifacts from disk into memory.

        Returns:
            True if artifacts were loaded successfully, False otherwise.
            (False means train_recommender.py hasn't been run yet.)
        """
        if self._loaded:
            return True

        artifacts = load_tfidf_artifacts()
        if artifacts is None:
            logger.warning(
                "TF-IDF artifacts not found. Similarity recommendations unavailable. "
                "Run: python scripts/train_recommender.py"
            )
            return False

        self.tfidf_matrix, self.vectorizer, self.product_ids = artifacts
        # Build reverse lookup: product_id string → row index in matrix
        self.product_id_to_idx = {pid: i for i, pid in enumerate(self.product_ids)}
        self._loaded = True

        logger.info(
            "ContentRecommender loaded: %d products, matrix %s",
            len(self.product_ids),
            self.tfidf_matrix.shape,
        )
        return True

    def get_similar_products(
        self,
        product_id: str,
        top_k: int = 10,
        exclude_ids: set[str] | None = None,
    ) -> list[tuple[str, float]]:
        """
        Find the top-K most similar products to the given product.

        Algorithm:
          1. Look up the product's row index in the TF-IDF matrix.
          2. Compute cosine similarity against all other products via sparse dot product.
          3. Zero out excluded products (self + already-seen).
          4. Return top-K (product_id, similarity_score) pairs.

        Args:
            product_id:  Stable product ID string (e.g. "P000042").
            top_k:       Maximum number of results to return.
            exclude_ids: Set of product IDs to exclude from results.

        Returns:
            List of (product_id, similarity_score) tuples, sorted by score descending.
            Returns empty list if product not found or artifacts not loaded.
        """
        if not self._loaded:
            logger.warning("ContentRecommender not loaded. Call .load() first.")
            return []

        idx = self.product_id_to_idx.get(product_id)
        if idx is None:
            logger.warning("Product '%s' not found in TF-IDF index.", product_id)
            return []

        # --- Core similarity computation ---
        # tfidf_matrix[idx] is a (1, n_features) sparse row vector
        # @ tfidf_matrix.T gives a (1, n_products) sparse result
        # .toarray().flatten() converts to a dense numpy array
        query_vec = self.tfidf_matrix[idx]  # shape: (1, n_features)
        similarities = (self.tfidf_matrix @ query_vec.T).toarray().flatten()
        # similarities[i] = cosine_similarity(product_id, products[i])

        # Zero out the query product itself (we never recommend a product to itself)
        similarities[idx] = -1.0

        # Zero out explicitly excluded products (e.g., purchased items)
        if exclude_ids:
            for eid in exclude_ids:
                eidx = self.product_id_to_idx.get(eid)
                if eidx is not None:
                    similarities[eidx] = -1.0

        # Get top-K indices by descending similarity score
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for i in top_indices:
            score = float(similarities[i])
            if score <= 0:
                break  # No more positive similarities
            results.append((self.product_ids[i], round(score, 6)))

        return results

    def get_product_vector(self, product_id: str):
        """
        Return the TF-IDF row vector for a product.
        Used by the hybrid recommender to build user preference vectors.

        Returns:
            scipy sparse matrix row (1, n_features) or None if not found.
        """
        if not self._loaded:
            return None
        idx = self.product_id_to_idx.get(product_id)
        if idx is None:
            return None
        return self.tfidf_matrix[idx]

    def compute_scores_for_products(
        self, query_vector, candidate_ids: list[str]
    ) -> dict[str, float]:
        """
        Compute similarity scores between a query vector and a list of products.

        Args:
            query_vector: A (1, n_features) scipy sparse vector (user preference vector).
            candidate_ids: List of product_id strings to score.

        Returns:
            Dict mapping product_id → cosine similarity score.
        """
        if not self._loaded or query_vector is None:
            return {}

        # Build index list for the candidates
        candidate_indices = []
        valid_ids = []
        for pid in candidate_ids:
            idx = self.product_id_to_idx.get(pid)
            if idx is not None:
                candidate_indices.append(idx)
                valid_ids.append(pid)

        if not candidate_indices:
            return {}

        # Extract the candidate rows as a sub-matrix
        candidate_matrix = self.tfidf_matrix[candidate_indices]
        # Compute similarities: (n_candidates, n_features) @ (n_features, 1)
        scores = (candidate_matrix @ query_vector.T).toarray().flatten()

        return {pid: round(float(s), 6) for pid, s in zip(valid_ids, scores)}

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def catalog_size(self) -> int:
        return len(self.product_ids)
