"""
Synthetic Fashion Product Dataset Generator for StyleSense.

PURPOSE:
  Generate a realistic synthetic fashion product CSV that:
  1. Has the SAME column structure as the Kaggle Fashion Product dataset.
  2. Can be replaced by the real Kaggle dataset without code changes.
  3. Is clearly labeled as [SYNTHETIC] — never presented as real data.

OUTPUT:
  backend/data/products_sample.csv

USAGE:
  python scripts/generate_synthetic_data.py

Kaggle dataset format (for replacement):
  Download: https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-small
  File: styles.csv
  Place at: backend/data/styles.csv
  Then run import_products.py with --kaggle flag.
"""

import csv
import random
import sys
from pathlib import Path

# Make sure we can import from backend root
sys.path.insert(0, str(Path(__file__).parent.parent))

OUTPUT_PATH = Path(__file__).parent.parent / "data" / "products_sample.csv"

# -----------------------------------------------------------------------
# Product catalog definition
# Each entry: (articleType, masterCategory, subCategory, usage, season)
# -----------------------------------------------------------------------
PRODUCT_TYPES = [
    # Topwear
    ("T-Shirts", "Apparel", "Topwear", "Casual", "Summer"),
    ("Shirts", "Apparel", "Topwear", "Formal", "Winter"),
    ("Casual Shirts", "Apparel", "Topwear", "Casual", "Summer"),
    ("Sweatshirts", "Apparel", "Topwear", "Casual", "Winter"),
    ("Jackets", "Apparel", "Topwear", "Casual", "Winter"),
    ("Sweaters", "Apparel", "Topwear", "Casual", "Winter"),
    ("Tops", "Apparel", "Topwear", "Casual", "Summer"),
    ("Blazers", "Apparel", "Topwear", "Formal", "Winter"),
    ("Kurtas", "Apparel", "Kurtas", "Ethnic", "Summer"),
    # Bottomwear
    ("Jeans", "Apparel", "Bottomwear", "Casual", "Winter"),
    ("Trousers", "Apparel", "Bottomwear", "Formal", "Summer"),
    ("Shorts", "Apparel", "Bottomwear", "Casual", "Summer"),
    ("Track Pants", "Apparel", "Bottomwear", "Sports", "Summer"),
    ("Skirts", "Apparel", "Bottomwear", "Casual", "Summer"),
    # Ethnic
    ("Sarees", "Apparel", "Saree", "Ethnic", "Summer"),
    ("Ethnic Dress", "Apparel", "Ethnic Dress", "Ethnic", "Summer"),
    ("Lehenga Choli", "Apparel", "Ethnic Dress", "Party", "Summer"),
    # Footwear
    ("Casual Shoes", "Footwear", "Shoes", "Casual", "Summer"),
    ("Sports Shoes", "Footwear", "Shoes", "Sports", "Summer"),
    ("Formal Shoes", "Footwear", "Shoes", "Formal", "Winter"),
    ("Sneakers", "Footwear", "Shoes", "Casual", "Summer"),
    ("Sandals", "Footwear", "Flip Flops", "Casual", "Summer"),
    ("Heels", "Footwear", "Shoes", "Party", "Summer"),
    ("Boots", "Footwear", "Shoes", "Casual", "Winter"),
    # Bags
    ("Backpacks", "Accessories", "Backpacks", "Casual", "Summer"),
    ("Handbags", "Accessories", "Bags", "Casual", "Summer"),
    ("Wallets", "Accessories", "Wallets", "Casual", "Summer"),
    ("Clutches", "Accessories", "Bags", "Party", "Summer"),
    # Watches & Accessories
    ("Watches", "Accessories", "Watches", "Casual", "Summer"),
    ("Sunglasses", "Accessories", "Sunglasses", "Casual", "Summer"),
    ("Belts", "Accessories", "Belts", "Formal", "Summer"),
    ("Caps", "Accessories", "Caps", "Casual", "Summer"),
    ("Socks", "Accessories", "Socks", "Casual", "Summer"),
    # Innerwear & Sportswear
    ("Sports Bra", "Apparel", "Innerwear", "Sports", "Summer"),
    ("Tracksuit", "Sporting Goods", "Sportswear", "Sports", "Winter"),
]

GENDERS = ["Men", "Women", "Unisex"]
GENDER_WEIGHTS = [0.4, 0.45, 0.15]

COLOURS = [
    "Black", "White", "Navy Blue", "Red", "Blue", "Grey", "Green",
    "Maroon", "Olive", "Yellow", "Pink", "Purple", "Orange", "Beige",
    "Brown", "Teal", "Multicolor", "Off White", "Rust", "Peach",
]

BRANDS = [
    "H&M", "Zara", "Mango", "Forever 21", "Only", "Vero Moda",
    "Jack & Jones", "Roadster", "HRX", "Puma", "Nike", "Adidas",
    "Peter England", "Van Heusen", "Allen Solly", "Louis Philippe",
    "W", "Biba", "Fabindia", "Aurelia", "Libas",
    "Reebok", "Skechers", "Woodland", "Red Tape", "Bata",
    "Fastrack", "Titan", "Casio", "Fossil", "Levi's",
    "Wrangler", "Pepe Jeans", "Spykar", "Lee", "American Eagle",
]

ADJECTIVES = [
    "Slim Fit", "Regular Fit", "Relaxed", "Straight", "Tapered",
    "Oversized", "Crop", "Flared", "Pleated", "Embroidered",
    "Printed", "Solid", "Striped", "Checked", "Floral",
    "Self Design", "Woven", "Knitted", "Denim", "Cotton",
    "Linen", "Polyester", "Silk", "Wool", "Synthetic",
]

DESCRIPTION_TEMPLATES = [
    "A {adj} {article} that combines style and comfort. Perfect for {usage} occasions.",
    "Crafted from premium materials, this {adj} {article} is ideal for {usage} wear.",
    "Elevate your wardrobe with this {adj} {article}. Suitable for {usage} settings.",
    "This {article} features a {adj} cut, making it a versatile choice for {usage}.",
    "A must-have {article} for every wardrobe. The {adj} design suits {usage} occasions.",
    "Stay stylish with this {adj} {article}, designed for modern {usage} lifestyles.",
    "Timeless and comfortable, this {adj} {article} is perfect for everyday {usage} use.",
]


def generate_product_name(article_type: str, brand: str, adj: str, colour: str, gender: str) -> str:
    """Generate a realistic product display name."""
    return f"{brand} {gender} {colour} {adj} {article_type}".title()


def generate_row(product_id: int, rng: random.Random) -> dict:
    """Generate a single synthetic product row."""
    product_type = rng.choice(PRODUCT_TYPES)
    article_type, master_cat, sub_cat, usage, season = product_type

    # Gender filtering: some articles are gender-specific
    if article_type in ("Sarees", "Lehenga Choli", "Sports Bra", "Skirts", "Heels", "Clutches", "Tops"):
        gender = "Women"
    elif article_type in ("Blazers", "Formal Shoes") and rng.random() > 0.2:
        gender = rng.choice(["Men", "Women"])
    else:
        gender = rng.choices(GENDERS, weights=GENDER_WEIGHTS)[0]

    colour = rng.choice(COLOURS)
    brand = rng.choice(BRANDS)
    adj = rng.choice(ADJECTIVES)

    name = generate_product_name(article_type, brand, adj, colour, gender)
    description = rng.choice(DESCRIPTION_TEMPLATES).format(
        adj=adj.lower(), article=article_type.lower(), usage=usage.lower()
    )

    year = rng.choice([2021, 2022, 2023, 2024])

    return {
        "id": product_id,
        "gender": gender,
        "masterCategory": master_cat,
        "subCategory": sub_cat,
        "articleType": article_type,
        "baseColour": colour,
        "season": season,
        "year": year,
        "usage": usage,
        "productDisplayName": name,
        "brand": brand,
        "description": description,
        # [SYNTHETIC] flag so this is never confused with real Kaggle data
        "data_source": "[SYNTHETIC]",
    }


def generate_synthetic_dataset(n_products: int = 1000, seed: int = 42) -> None:
    """
    Generate and save a synthetic fashion product CSV.

    Args:
        n_products: Number of products to generate (default 1000).
        seed:       Random seed for reproducibility.
    """
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)

    fieldnames = [
        "id", "gender", "masterCategory", "subCategory", "articleType",
        "baseColour", "season", "year", "usage", "productDisplayName",
        "brand", "description", "data_source",
    ]

    print(f"Generating {n_products} synthetic products -> {OUTPUT_PATH}")

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for i in range(1, n_products + 1):
            writer.writerow(generate_row(i, rng))

    print(f"Done. Dataset saved at: {OUTPUT_PATH}")
    print(
        "\n[NOTE] This is a SYNTHETIC dataset for development purposes only.\n"
        "To use the real Kaggle dataset:\n"
        "  1. Download: https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-small\n"
        "  2. Place styles.csv at: backend/data/styles.csv\n"
        "  3. Run: python scripts/import_products.py --kaggle"
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=1000, help="Number of products to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    generate_synthetic_dataset(n_products=args.n, seed=args.seed)
