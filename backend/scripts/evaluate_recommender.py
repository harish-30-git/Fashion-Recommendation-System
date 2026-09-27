"""
Recommendation Evaluation Runner for StyleSense.

USAGE:
    python scripts/evaluate_recommender.py

PURPOSE:
    Benchmarks Popularity Baseline vs. Content-Based vs. Hybrid Recommender
    on an 80/20 train/test interaction split.
    Outputs real measured values for Precision@10, Recall@10, NDCG@10,
    Catalog Coverage, and Intra-List Diversity.
"""

import os
import sys
import json
import random
import logging
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from pymongo import MongoClient

from app.ml.content_recommender import ContentRecommender
from app.ml.collaborative_recommender import CollaborativeRecommender
from app.ml.hybrid_recommender import HybridRecommender
from app.ml.evaluation import EvaluationEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def generate_benchmark_test_users(
    catalog_products: list[dict], num_users: int = 50, seed: int = 42
) -> list[dict]:
    """
    Generate test users with realistic clustered preferences across fashion categories.
    For each user, interactions are split 80% train / 20% test (strict holdout).
    """
    rng = random.Random(seed)
    categories = sorted(list({p["category"] for p in catalog_products if p.get("category")}))
    by_category = {cat: [p["product_id"] for p in catalog_products if p.get("category") == cat] for cat in categories}

    test_users = []
    for uid in range(1, num_users + 1):
        # Pick 1 primary category and 1 secondary category for this user's taste persona
        fav_cats = rng.sample(categories, k=min(2, len(categories)))
        user_pool = by_category[fav_cats[0]] * 3 + (by_category[fav_cats[1]] if len(fav_cats) > 1 else [])
        
        # User interacts with 10 to 18 products
        interaction_count = rng.randint(10, 18)
        selected_pids = rng.sample(user_pool, min(interaction_count, len(user_pool)))
        
        # 80/20 train/test split
        split_idx = int(len(selected_pids) * 0.8)
        train_pids = selected_pids[:split_idx]
        test_pids = selected_pids[split_idx:]

        if not test_pids or not train_pids:
            continue

        train_interactions = {
            pid: rng.choice([0.5, 1.5, 2.0, 3.0]) for pid in train_pids
        }

        test_users.append({
            "user_id": f"eval_user_{uid}",
            "train_interactions": train_interactions,
            "test_relevant_ids": set(test_pids),
        })

    return test_users


def main():
    mongo_uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB_NAME", "stylesense")

    logger.info("Connecting to MongoDB Atlas to fetch catalog...")
    client = MongoClient(mongo_uri)
    db = client[db_name]

    cursor = db.products.find(
        {},
        {
            "product_id": 1, "name": 1, "brand": 1, "category": 1,
            "subcategory": 1, "price": 1, "rating": 1, "review_count": 1,
            "is_available": 1, "stock": 1,
        }
    )
    catalog = list(cursor)
    client.close()

    if not catalog:
        logger.error("No products found in database. Run import_products.py first.")
        sys.exit(1)

    logger.info("Catalog loaded: %d products", len(catalog))

    # Initialize Recommenders
    content_rec = ContentRecommender.get_instance()
    if not content_rec.load():
        logger.error("Failed to load TF-IDF artifacts. Run train_recommender.py first.")
        sys.exit(1)

    collab_rec = CollaborativeRecommender()
    hybrid_rec = HybridRecommender(content_recommender=content_rec, collab_recommender=collab_rec)

    # Generate synthetic benchmark user cohort
    logger.info("Synthesizing 50 evaluation user personas (80/20 train-test split)...")
    test_cohort = generate_benchmark_test_users(catalog, num_users=50, seed=42)
    logger.info("Prepared %d valid test users for evaluation.", len(test_cohort))

    # Run Benchmark
    eval_engine = EvaluationEngine(
        content_rec=content_rec,
        hybrid_rec=hybrid_rec,
        catalog_products=catalog,
    )

    logger.info("Running evaluation benchmark for K=10...")
    report = eval_engine.evaluate_test_users(test_cohort, k=10)

    # Print formatted output
    print("\n" + "=" * 80)
    print("           STYLESENSE RECOMMENDATION ENGINE EVALUATION REPORT           ")
    print("=" * 80)
    print(f"Catalog Size: {report['catalog_size']} items | Evaluated Users: {report['test_users_count']} | Cutoff: Top-{report['eval_cutoff_k']}\n")

    header = f"{'Strategy':<24} | {'Prec@10':<9} | {'Recall@10':<9} | {'NDCG@10':<9} | {'Coverage':<9} | {'ILD (Div)':<9}"
    print(header)
    print("-" * len(header))

    for strat, res in report["results"].items():
        print(
            f"{strat:<24} | "
            f"{res['Precision@10']:<9.4f} | "
            f"{res['Recall@10']:<9.4f} | "
            f"{res['NDCG@10']:<9.4f} | "
            f"{res['Coverage']:<9.4f} | "
            f"{res['Intra-List Diversity']:<9.4f}"
        )
    print("=" * 80)

    # Save report JSON
    out_dir = Path(__file__).parent.parent / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "evaluation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport written to: {report_path.resolve()}\n")


if __name__ == "__main__":
    main()
