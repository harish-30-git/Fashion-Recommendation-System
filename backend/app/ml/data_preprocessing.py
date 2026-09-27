"""
Data Preprocessing Pipeline for StyleSense.

PURPOSE:
  This script reads a raw fashion product CSV (from Kaggle or synthetic),
  cleans and normalizes it, and outputs a clean DataFrame ready for:
    1. MongoDB ingestion (via scripts/import_products.py)
    2. ML feature engineering (via feature_engineering.py)

DATASET EXPECTED:
  The Kaggle "Fashion Product Images (Small)" dataset has these columns:
    id, gender, masterCategory, subCategory, articleType,
    baseColour, season, year, usage, productDisplayName

  If you have the real dataset, place the CSV at:
    backend/data/styles.csv

  This script also supports the synthetic dataset at:
    backend/data/products_sample.csv

  The synthetic dataset has the same column structure, labeled [SYNTHETIC].

INTERVIEW NOTES:
  - Why normalize category names? Inconsistent casing ("topwear" vs "Topwear")
    would create duplicate categories in filters and break recommendation
    grouping. Normalization is applied in title_case consistently.
  - Why fill missing descriptions? TF-IDF requires text input. Missing
    descriptions produce zero vectors, making products invisible to
    content-based similarity. A structured fallback ensures every product
    participates in the similarity calculation.
  - Time complexity: O(n) for a single pass through the DataFrame.
    All operations are vectorized with pandas — no Python-level loops.
"""

import pandas as pd
import numpy as np
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Price configuration by category (INR ranges for synthetic price assignment) #
# The Kaggle dataset does not include prices, so we assign realistic ones.    #
# --------------------------------------------------------------------------- #
PRICE_RANGES: dict[str, tuple[int, int]] = {
    "Topwear": (299, 3499),
    "Bottomwear": (499, 4499),
    "Footwear": (699, 8999),
    "Bags": (799, 12999),
    "Accessories": (199, 4999),
    "Watches": (999, 24999),
    "Innerwear": (199, 1499),
    "Sportswear": (599, 5999),
    "Ethnic": (699, 9999),
    "Default": (299, 2999),
}

# Discount range: 0% to 40%
DISCOUNT_RANGE = (0, 40)

# Mapping from Kaggle masterCategory to our normalized categories
CATEGORY_MAP: dict[str, str] = {
    "Apparel": "Topwear",  # Will be refined by subCategory
    "Footwear": "Footwear",
    "Accessories": "Accessories",
    "Personal Care": "Accessories",
    "Sporting Goods": "Sportswear",
    "Home": "Accessories",
    "Free Items": "Accessories",
}

# Subcategory → our category refinement
SUBCATEGORY_TO_CATEGORY: dict[str, str] = {
    "Topwear": "Topwear",
    "Bottomwear": "Bottomwear",
    "Innerwear": "Innerwear",
    "Dress": "Topwear",
    "Saree": "Ethnic",
    "Kurtas": "Ethnic",
    "Ethnic Dress": "Ethnic",
    "Bags": "Bags",
    "Wallets": "Bags",
    "Backpacks": "Bags",
    "Watches": "Watches",
    "Socks": "Accessories",
    "Belts": "Accessories",
    "Scarves": "Accessories",
    "Caps": "Accessories",
    "Sports Equipment": "Sportswear",
}

# Representative Indian fashion brands for synthetic price assignment
BRAND_LIST = [
    "H&M", "Zara", "Mango", "Forever 21", "Only", "Vero Moda",
    "Jack & Jones", "Roadster", "HRX", "Puma", "Nike", "Adidas",
    "Peter England", "Van Heusen", "Allen Solly", "Louis Philippe",
    "W", "Biba", "Fabindia", "Aurelia", "Libas", "Ethnix",
    "Reebok", "Skechers", "Woodland", "Red Tape", "Bata",
    "Fastrack", "Titan", "Casio", "Fossil",
]

SIZE_MAP: dict[str, list[str]] = {
    "Topwear": ["XS", "S", "M", "L", "XL", "XXL"],
    "Bottomwear": ["28", "30", "32", "34", "36", "38"],
    "Footwear": ["6", "7", "8", "9", "10", "11"],
    "Ethnic": ["XS", "S", "M", "L", "XL", "XXL"],
    "Innerwear": ["S", "M", "L", "XL"],
    "Default": ["Free Size"],
}


def load_dataset(csv_path: str) -> pd.DataFrame:
    """
    Load a CSV dataset file into a DataFrame.

    Args:
        csv_path: Absolute or relative path to the CSV file.

    Returns:
        Raw DataFrame.

    Raises:
        FileNotFoundError if the CSV does not exist.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found at: {path.resolve()}\n"
            f"Run: python scripts/generate_synthetic_data.py"
        )

    df = pd.read_csv(csv_path, on_bad_lines="skip")
    logger.info("Loaded %d raw rows from %s", len(df), csv_path)
    return df


def clean_dataset(df: pd.DataFrame, is_kaggle: bool = False) -> pd.DataFrame:
    """
    Main cleaning and normalization pipeline.

    Steps (in order):
      1. Rename columns to our internal schema.
      2. Drop duplicates on the ID column.
      3. Drop rows missing critical fields.
      4. Normalize text fields (strip, title case).
      5. Map external categories to our internal category names.
      6. Fill missing descriptions.
      7. Assign prices (Kaggle dataset has none).
      8. Assign sizes and colors if missing.
      9. Build tags from available attributes.
      10. Assign product_id and is_available.

    Args:
        df:         Raw DataFrame from load_dataset().
        is_kaggle:  True if the CSV is the raw Kaggle fashion dataset.
                    False for synthetic or pre-processed datasets.

    Returns:
        Cleaned DataFrame with our canonical column names.
    """
    rng = np.random.default_rng(seed=42)  # Reproducible random number generator

    # Always rename Kaggle-format columns (both synthetic and real data use the same format)
    df = _rename_kaggle_columns(df)
    
    # Step 1: Drop exact duplicates on the raw ID column
    original_count = len(df)
    df = df.drop_duplicates(subset=["raw_id"])
    logger.info("Dropped %d duplicates; %d rows remain.", original_count - len(df), len(df))

    # Step 2: Drop rows without a name or category (unusable for recommendations)
    df = df.dropna(subset=["name", "raw_category"])
    df = df[df["name"].str.strip().ne("")]

    # Step 3: Normalize text fields
    for col in ["name", "brand", "raw_category", "subcategory", "color", "gender"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()

    # Step 4: Map to internal category names
    df["category"] = df.apply(_map_category, axis=1)

    # Step 5: Fill missing descriptions with structured fallback
    df["description"] = df.apply(_fill_description, axis=1)

    # Step 6: Assign prices
    df["price"] = df.apply(
        lambda row: _assign_price(row["category"], rng), axis=1
    )
    df["discount_percent"] = rng.integers(
        DISCOUNT_RANGE[0], DISCOUNT_RANGE[1] + 1, size=len(df)
    )
    df["discounted_price"] = (
        df["price"] * (1 - df["discount_percent"] / 100)
    ).round(2)

    # Step 7: Assign sizes
    df["sizes"] = df["category"].apply(
        lambda cat: SIZE_MAP.get(cat, SIZE_MAP["Default"])
    )

    # Step 8: Colors — clean up or assign from color column
    df["colors"] = df["color"].apply(
        lambda c: [c] if isinstance(c, str) and c not in ("Nan", "Na", "") else ["Multicolor"]
    )

    # Step 9: Assign stock, rating, brand
    df["stock"] = rng.integers(0, 101, size=len(df)).tolist()
    df["is_available"] = df["stock"] > 0
    df["rating"] = rng.uniform(2.5, 5.0, size=len(df)).round(1).tolist()
    df["review_count"] = rng.integers(0, 5001, size=len(df)).tolist()

    if "brand" not in df.columns or df["brand"].isna().all():
        df["brand"] = rng.choice(BRAND_LIST, size=len(df)).tolist()

    # Step 10: Build tags
    df["tags"] = df.apply(_build_tags, axis=1)

    # Step 11: Assign stable product_id
    df = df.reset_index(drop=True)
    df["product_id"] = df["raw_id"].apply(lambda x: f"P{int(x):06d}")

    # Step 12: Image URL — use Picsum placeholder keyed to product_id for consistency
    # In production, replace with real CDN or local image file paths.
    df["image_url"] = df["raw_id"].apply(
        lambda x: f"https://picsum.photos/seed/{int(x)}/400/500"
    )
    df["additional_images"] = df["raw_id"].apply(
        lambda x: [
            f"https://picsum.photos/seed/{int(x)+1000}/400/500",
            f"https://picsum.photos/seed/{int(x)+2000}/400/500",
        ]
    )

    # Step 13: Timestamps
    df["created_at"] = pd.Timestamp.now(tz="UTC")

    logger.info("Cleaning complete. Final dataset: %d products.", len(df))
    return df


def _rename_kaggle_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map Kaggle column names to internal schema names."""
    rename_map = {
        "id": "raw_id",
        "productDisplayName": "name",
        "masterCategory": "raw_category",
        "subCategory": "subcategory",
        "articleType": "article_type",
        "baseColour": "color",
        "gender": "gender",
        "season": "season",
        "year": "year",
        "usage": "usage",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    # If 'brand' is not in Kaggle data, leave it missing (assigned later)
    return df


def _map_category(row: pd.Series) -> str:
    """Map raw dataset category + subcategory to internal category."""
    sub = str(row.get("subcategory", "")).title()
    raw = str(row.get("raw_category", "")).title()

    # Subcategory takes priority for precise mapping
    if sub in SUBCATEGORY_TO_CATEGORY:
        return SUBCATEGORY_TO_CATEGORY[sub]

    return CATEGORY_MAP.get(raw, "Accessories")


def _fill_description(row: pd.Series) -> str:
    """
    Generate a description if none exists.

    Every product must have a non-empty description for TF-IDF to work.
    We build a structured sentence from available metadata fields.
    """
    desc = row.get("description", "")
    if isinstance(desc, str) and len(desc.strip()) > 10:
        return _clean_text(desc)

    parts = [
        row.get("name", ""),
        f"by {row.get('brand', '')}" if row.get("brand") else "",
        f"for {row.get('gender', 'everyone')}",
        f"in {row.get('color', '')}" if row.get("color") else "",
        f"Category: {row.get('subcategory', row.get('category', ''))}",
        f"Occasion: {row.get('usage', '')}" if row.get("usage") else "",
        f"Season: {row.get('season', '')}" if row.get("season") else "",
    ]
    return " ".join(p for p in parts if p).strip()


def _clean_text(text: str) -> str:
    """Remove excessive whitespace and non-printable characters."""
    text = re.sub(r"\s+", " ", text)
    text = text.encode("ascii", errors="ignore").decode("ascii")
    return text.strip()


def _assign_price(category: str, rng: np.random.Generator) -> float:
    """Assign a realistic price in INR based on product category."""
    low, high = PRICE_RANGES.get(category, PRICE_RANGES["Default"])
    return float(rng.integers(low, high + 1))


def _build_tags(row: pd.Series) -> list[str]:
    """
    Build a list of searchable tags from product attributes.

    Tags are used as additional input for TF-IDF feature engineering.
    They capture attributes that might not appear in the description.
    """
    tag_fields = ["gender", "color", "subcategory", "season", "usage", "article_type"]
    tags = []
    for field in tag_fields:
        val = row.get(field, "")
        if isinstance(val, str) and val.strip() and val.lower() not in ("nan", "na", ""):
            tags.append(val.strip().lower())
    return tags


def get_canonical_columns() -> list[str]:
    """Return the list of columns expected in the clean DataFrame."""
    return [
        "product_id", "name", "brand", "category", "subcategory",
        "description", "price", "discounted_price", "discount_percent",
        "sizes", "colors", "gender", "image_url", "additional_images",
        "stock", "is_available", "rating", "review_count", "tags",
        "created_at",
    ]
