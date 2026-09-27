"""
Configuration classes for StyleSense Flask application.

We use a class-based config pattern so that different environments
(development, testing, production) can cleanly inherit from a base.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    """Shared settings across all environments."""

    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    DEBUG: bool = False
    TESTING: bool = False

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(
        hours=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", 24))
    )

    # MongoDB
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/stylesense")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "stylesense")

    # -------------------------------------------------------------------
    # Interaction weights
    # These control how much each user action influences recommendations.
    # They are configurable — not experimentally validated as optimal.
    # -------------------------------------------------------------------
    INTERACTION_WEIGHTS: dict = {
        "view": float(os.getenv("INTERACTION_WEIGHT_VIEW", 0.5)),
        "wishlist": float(os.getenv("INTERACTION_WEIGHT_WISHLIST", 1.5)),
        "cart": float(os.getenv("INTERACTION_WEIGHT_CART", 2.0)),
        "purchase": float(os.getenv("INTERACTION_WEIGHT_PURCHASE", 3.0)),
    }

    # -------------------------------------------------------------------
    # Hybrid recommender weights (should sum to 1.0)
    # W1 = content-based score weight
    # W2 = collaborative filtering score weight
    # W3 = user interaction preference weight
    # -------------------------------------------------------------------
    HYBRID_W1: float = float(os.getenv("RECOMMENDATION_HYBRID_W1", 0.5))
    HYBRID_W2: float = float(os.getenv("RECOMMENDATION_HYBRID_W2", 0.3))
    HYBRID_W3: float = float(os.getenv("RECOMMENDATION_HYBRID_W3", 0.2))


class DevelopmentConfig(BaseConfig):
    """Settings for local development."""

    DEBUG = True


class TestingConfig(BaseConfig):
    """Settings for automated tests — uses a separate test database."""

    TESTING = True
    MONGODB_DB_NAME = "stylesense_test"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)


class ProductionConfig(BaseConfig):
    """Settings for production deployment."""

    DEBUG = False


# Map string names to config classes so create_app() can select by name.
config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
