"""
Product Import Script for StyleSense.

PURPOSE:
  Read the cleaned/synthetic fashion product CSV → preprocess it →
  batch-insert into MongoDB Atlas.

USAGE:
  # Synthetic dataset (default):
  python scripts/import_products.py

  # Real Kaggle dataset:
  python scripts/import_products.py --kaggle --csv data/styles.csv

SAFETY:
  - Uses ordered=False in bulk_write so that duplicate products are skipped
    without aborting the entire batch.
  - Idempotent: safe to run multiple times. Existing documents with the same
    product_id are NOT overwritten (they are skipped due to the unique index).
  - Prints a summary of inserted vs skipped (duplicate) products.

PREREQUISITES:
  1. Python virtual environment activated with all requirements installed.
  2. .env file with valid MONGODB_URI.
  3. Synthetic CSV generated (run generate_synthetic_data.py first),
     OR the real Kaggle styles.csv placed at backend/data/styles.csv.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add the backend root to sys.path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import os
from datetime import datetime, timezone

import pandas as pd
from pymongo import MongoClient, InsertOne
from pymongo.errors import BulkWriteError

from app.ml.data_preprocessing import load_dataset, clean_dataset

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

BATCH_SIZE = 500  # Insert in batches to avoid hitting MongoDB document size limits


def dataframe_to_mongo_docs(df: pd.DataFrame) -> list[dict]:
    """
    Convert a cleaned DataFrame to a list of MongoDB-ready dicts.

    Converts Python lists/arrays to plain Python lists for MongoDB
    serialization. Pandas types like numpy int64 are not directly
    serializable by pymongo.
    """
    docs = []
    for _, row in df.iterrows():
        doc = {
            "product_id": str(row["product_id"]),
            "name": str(row["name"]),
            "brand": str(row.get("brand", "Unknown")),
            "category": str(row["category"]),
            "subcategory": str(row.get("subcategory", "")),
            "description": str(row["description"]),
            "price": float(row["price"]),
            "discounted_price": float(row["discounted_price"]),
            "discount_percent": int(row["discount_percent"]),
            "sizes": list(row["sizes"]) if hasattr(row["sizes"], "__iter__") and not isinstance(row["sizes"], str) else [],
            "colors": list(row["colors"]) if hasattr(row["colors"], "__iter__") and not isinstance(row["colors"], str) else [],
            "gender": str(row.get("gender", "Unisex")),
            "image_url": str(row["image_url"]),
            "additional_images": list(row.get("additional_images", [])),
            "stock": int(row["stock"]),
            "is_available": bool(row["is_available"]),
            "rating": float(row["rating"]),
            "review_count": int(row["review_count"]),
            "tags": list(row.get("tags", [])),
            "created_at": datetime.now(timezone.utc),
        }
        docs.append(doc)
    return docs


def batch_insert(collection, docs: list[dict]) -> tuple[int, int]:
    """
    Insert documents in batches using ordered=False bulk operations.

    ordered=False means: if one document fails (e.g., duplicate product_id),
    MongoDB continues with the remaining documents instead of stopping.
    This is the correct behavior for idempotent import scripts.

    Returns:
        (inserted_count, skipped_count)
    """
    inserted = 0
    skipped = 0

    for i in range(0, len(docs), BATCH_SIZE):
        batch = docs[i : i + BATCH_SIZE]
        operations = [InsertOne(doc) for doc in batch]

        try:
            result = collection.bulk_write(operations, ordered=False)
            inserted += result.inserted_count
        except BulkWriteError as e:
            # Some documents were inserted, some were skipped (duplicates)
            inserted += e.details.get("nInserted", 0)
            skipped += len(e.details.get("writeErrors", []))

        logger.info(
            "Batch %d/%d: inserted=%d, skipped=%d so far",
            i // BATCH_SIZE + 1,
            (len(docs) + BATCH_SIZE - 1) // BATCH_SIZE,
            inserted,
            skipped,
        )

    return inserted, skipped


def main():
    parser = argparse.ArgumentParser(description="Import fashion products into MongoDB.")
    parser.add_argument(
        "--csv",
        type=str,
        default=str(Path(__file__).parent.parent / "data" / "products_sample.csv"),
        help="Path to the input CSV file.",
    )
    parser.add_argument(
        "--kaggle",
        action="store_true",
        help="Set this flag if the CSV is the raw Kaggle styles.csv (enables column renaming).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of products to import (for testing).",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------ #
    # 1. Connect to MongoDB                                                #
    # ------------------------------------------------------------------ #
    mongo_uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB_NAME", "stylesense")

    if not mongo_uri:
        logger.error(
            "MONGODB_URI not found in environment. "
            "Copy .env.example to .env and fill in your MongoDB Atlas connection string."
        )
        sys.exit(1)

    logger.info("Connecting to MongoDB: %s", db_name)
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db.products

    # Ensure unique index exists before importing
    collection.create_index("product_id", unique=True)

    # ------------------------------------------------------------------ #
    # 2. Load and clean the dataset                                        #
    # ------------------------------------------------------------------ #
    logger.info("Loading CSV: %s", args.csv)
    try:
        df = load_dataset(args.csv)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    if args.limit:
        df = df.head(args.limit)
        logger.info("Limiting to %d rows for testing.", args.limit)

    logger.info("Preprocessing %d raw rows...", len(df))
    df = clean_dataset(df, is_kaggle=args.kaggle)
    logger.info("After cleaning: %d products ready for import.", len(df))

    # ------------------------------------------------------------------ #
    # 3. Convert to MongoDB documents and insert                           #
    # ------------------------------------------------------------------ #
    docs = dataframe_to_mongo_docs(df)
    logger.info("Starting batch import into '%s.products'...", db_name)

    inserted, skipped = batch_insert(collection, docs)

    # ------------------------------------------------------------------ #
    # 4. Summary                                                           #
    # ------------------------------------------------------------------ #
    total_in_db = collection.count_documents({})
    logger.info(
        "\n===== Import Complete =====\n"
        "  Rows in CSV:       %d\n"
        "  Inserted (new):    %d\n"
        "  Skipped (dupes):   %d\n"
        "  Total in MongoDB:  %d\n"
        "===========================",
        len(df),
        inserted,
        skipped,
        total_in_db,
    )

    client.close()


if __name__ == "__main__":
    main()
