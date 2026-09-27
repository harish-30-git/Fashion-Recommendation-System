"""
TF-IDF Training Script for StyleSense.

PURPOSE:
  Load all products from MongoDB → build TF-IDF feature matrix →
  save artifacts to disk for use by the content recommender at runtime.

USAGE:
  python scripts/train_recommender.py

WHEN TO RUN:
  - After importing products for the first time.
  - After adding new products to the catalog.
  - The recommender loads pre-trained artifacts from disk, so this
    script must be re-run whenever the product catalog changes.

OUTPUT:
  backend/data/ml_artifacts/
    tfidf_matrix.npz      — Sparse TF-IDF matrix (n_products × n_features)
    tfidf_vectorizer.pkl  — Fitted TfidfVectorizer
    product_ids.pkl       — Ordered list of product_id strings
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import os
import pandas as pd
from pymongo import MongoClient

from app.ml.feature_engineering import train_tfidf

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    mongo_uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB_NAME", "stylesense")

    if not mongo_uri:
        logger.error("MONGODB_URI not set. Check your .env file.")
        sys.exit(1)

    logger.info("Connecting to MongoDB...")
    client = MongoClient(mongo_uri)
    db = client[db_name]

    # Load all products from MongoDB into a DataFrame
    logger.info("Loading products from MongoDB...")
    cursor = db.products.find(
        {},
        {
            "product_id": 1, "name": 1, "description": 1,
            "category": 1, "subcategory": 1, "brand": 1,
            "gender": 1, "colors": 1, "tags": 1,
        },
    )
    df = pd.DataFrame(list(cursor))

    if df.empty:
        logger.error(
            "No products found in MongoDB. "
            "Run import_products.py first."
        )
        sys.exit(1)

    logger.info("Loaded %d products from MongoDB.", len(df))
    client.close()

    # Train and save TF-IDF artifacts
    tfidf_matrix, vectorizer, product_ids = train_tfidf(df)

    logger.info(
        "\n===== Training Complete =====\n"
        "  Products:      %d\n"
        "  Vocabulary:    %d\n"
        "  Matrix shape:  %s\n"
        "  Non-zeros:     %d (%.2f%%)\n"
        "  Artifacts at:  backend/data/ml_artifacts/\n"
        "=============================",
        len(product_ids),
        len(vectorizer.vocabulary_),
        tfidf_matrix.shape,
        tfidf_matrix.nnz,
        100 * tfidf_matrix.nnz / (tfidf_matrix.shape[0] * tfidf_matrix.shape[1]),
    )


if __name__ == "__main__":
    main()
