"""
Feature Engineering for StyleSense Content-Based Recommender.

PURPOSE:
  Convert the cleaned product catalog into a numerical representation
  that can be used to measure how similar two products are.

METHOD: TF-IDF Vectorization + Cosine Similarity

  1. Build a "combined text" string for each product by concatenating:
       name + description + category + subcategory + brand + color + tags
     
     Why multiple fields? Each field captures a different aspect of the
     product. "category" ensures that shirts stay similar to shirts.
     "brand" clusters brand-specific recommendations. "color" helps with
     outfit matching.

  2. Apply TfidfVectorizer to convert these strings to sparse vectors.
     
     TF-IDF (Term Frequency–Inverse Document Frequency):
       - TF(t, d)  = how often term t appears in document d
       - IDF(t)    = log(N / df(t)) where N=total docs, df=docs containing t
       - TF-IDF    = TF × IDF
       
     This downweights common words like "product", "available" (high IDF
     denominator) and upweights distinctive terms like "denim", "ethnic".

  3. Store the result as a scipy sparse matrix.
     
     MEMORY: Dense matrix for 44k products × 10k vocabulary = 44M floats
             ≈ 176 MB. Most entries are 0 (sparse).
             Sparse matrix stores only non-zeros ≈ ~1–5 MB.

  4. Compute cosine similarity at query time using a dot product:
     
       sim(a, b) = (a · b) / (||a|| × ||b||)
       
     Since TF-IDF vectors are L2-normalized, this simplifies to:
       sim(a, b) = a · b   (dot product of unit vectors)
       
     Time complexity per query: O(d) where d = vocabulary size (sparse dot).
     We do NOT precompute an N×N similarity matrix — that would be O(N²)
     space (44k² ≈ 2 billion entries), which is infeasible.

CACHING:
  The fitted TfidfVectorizer and tfidf_matrix are saved to disk as
  .pkl files after training. They are loaded on first use in the
  content recommender and reused for all subsequent requests.
  This means the expensive vectorization only happens once.
"""

import pickle
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import csr_matrix, save_npz, load_npz

logger = logging.getLogger(__name__)

# Paths where trained artifacts are saved
ARTIFACTS_DIR = Path(__file__).parent.parent.parent / "data" / "ml_artifacts"
TFIDF_MATRIX_PATH = ARTIFACTS_DIR / "tfidf_matrix.npz"
VECTORIZER_PATH = ARTIFACTS_DIR / "tfidf_vectorizer.pkl"
PRODUCT_IDS_PATH = ARTIFACTS_DIR / "product_ids.pkl"


def build_combined_text(row: pd.Series) -> str:
    """
    Concatenate product attributes into a single string for TF-IDF.

    Field weights are controlled by repetition:
      - Category and subcategory appear twice to give them more influence.
      - Tags appear at the end, providing additional keyword coverage.

    Args:
        row: A single row from the cleaned products DataFrame.

    Returns:
        A space-separated string of all relevant product tokens.
    """
    parts = [
        str(row.get("name", "")),
        str(row.get("description", "")),
        str(row.get("category", "")),
        str(row.get("category", "")),        # Repeated for weight
        str(row.get("subcategory", "")),
        str(row.get("subcategory", "")),     # Repeated for weight
        str(row.get("brand", "")),
        str(row.get("gender", "")),
        " ".join(row.get("colors", []) if isinstance(row.get("colors"), list) else []),
        " ".join(row.get("tags", []) if isinstance(row.get("tags"), list) else []),
    ]
    combined = " ".join(p for p in parts if p and p.lower() not in ("nan", "none", ""))
    return combined.lower().strip()


def train_tfidf(df: pd.DataFrame) -> tuple[csr_matrix, TfidfVectorizer, list[str]]:
    """
    Build and save the TF-IDF matrix from the product DataFrame.

    Args:
        df: Cleaned product DataFrame with canonical columns.

    Returns:
        (tfidf_matrix, vectorizer, product_ids_list)
        - tfidf_matrix: scipy sparse matrix of shape (n_products, n_features)
        - vectorizer: fitted TfidfVectorizer (used later for query vectorization)
        - product_ids_list: ordered list of product_id strings matching matrix rows
    """
    logger.info("Building TF-IDF feature matrix for %d products...", len(df))

    # Ensure artifacts directory exists
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    # Build the combined text column
    df = df.copy()
    df["combined_text"] = df.apply(build_combined_text, axis=1)

    # Filter out rows with empty combined text (shouldn't happen after preprocessing)
    df = df[df["combined_text"].str.len() > 0]
    product_ids = df["product_id"].tolist()

    # Fit TF-IDF
    # - max_features=10000: vocabulary cap prevents memory explosion
    # - ngram_range=(1,2): includes bigrams ("slim fit", "t shirt")
    # - min_df=2: ignores terms appearing in only 1 document (likely noise)
    # - sublinear_tf=True: uses log(1+tf) which dampens very common terms
    vectorizer = TfidfVectorizer(
        max_features=10_000,
        ngram_range=(1, 2),
        min_df=2,
        sublinear_tf=True,
        strip_accents="unicode",
        analyzer="word",
    )
    tfidf_matrix: csr_matrix = vectorizer.fit_transform(df["combined_text"])

    logger.info(
        "TF-IDF matrix shape: %d products × %d features (%.1f%% non-zero)",
        tfidf_matrix.shape[0],
        tfidf_matrix.shape[1],
        100 * tfidf_matrix.nnz / (tfidf_matrix.shape[0] * tfidf_matrix.shape[1]),
    )

    # Save artifacts to disk
    save_npz(TFIDF_MATRIX_PATH, tfidf_matrix)
    with open(VECTORIZER_PATH, "wb") as f:
        pickle.dump(vectorizer, f)
    with open(PRODUCT_IDS_PATH, "wb") as f:
        pickle.dump(product_ids, f)

    logger.info("Saved TF-IDF artifacts to %s", ARTIFACTS_DIR)
    return tfidf_matrix, vectorizer, product_ids


def load_tfidf_artifacts() -> tuple[csr_matrix, TfidfVectorizer, list[str]] | None:
    """
    Load pre-trained TF-IDF artifacts from disk.

    Returns:
        (tfidf_matrix, vectorizer, product_ids) if artifacts exist.
        None if artifacts have not been trained yet.
    """
    if not (TFIDF_MATRIX_PATH.exists() and VECTORIZER_PATH.exists() and PRODUCT_IDS_PATH.exists()):
        logger.warning(
            "TF-IDF artifacts not found. Run: python scripts/train_recommender.py"
        )
        return None

    tfidf_matrix = load_npz(TFIDF_MATRIX_PATH)

    with open(VECTORIZER_PATH, "rb") as f:
        vectorizer = pickle.load(f)

    with open(PRODUCT_IDS_PATH, "rb") as f:
        product_ids = pickle.load(f)

    logger.info("Loaded TF-IDF artifacts: %d products", len(product_ids))
    return tfidf_matrix, vectorizer, product_ids
