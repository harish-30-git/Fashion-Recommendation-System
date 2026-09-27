"""
StyleSense Flask Application Factory.

Using the app factory pattern (create_app) means we can:
  1. Create multiple app instances for testing without state leakage.
  2. Defer extension binding until a config is chosen.
  3. Register blueprints cleanly in one place.
"""

import os
from flask import Flask
from pymongo import MongoClient

from app.config import config_map
from app.extensions import jwt, cors
import app.extensions as ext
from app.utils.logger import setup_logger


def create_app(config_name: str | None = None) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        config_name: One of 'development', 'testing', 'production'.
                     Defaults to the FLASK_ENV environment variable,
                     falling back to 'development'.

    Returns:
        Configured Flask application instance.
    """
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)

    # ------------------------------------------------------------------ #
    # Load configuration                                                   #
    # ------------------------------------------------------------------ #
    config_class = config_map.get(config_name, config_map["development"])
    app.config.from_object(config_class)

    # ------------------------------------------------------------------ #
    # Initialize extensions                                                #
    # ------------------------------------------------------------------ #
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # ------------------------------------------------------------------ #
    # MongoDB connection                                                   #
    # ------------------------------------------------------------------ #
    ext.mongo_client = MongoClient(app.config["MONGODB_URI"])
    ext.db = ext.mongo_client[app.config["MONGODB_DB_NAME"]]
    try:
        _ensure_indexes(ext.db)
    except Exception as e:
        app.logger.warning(
            "Could not create MongoDB indexes (DB not reachable yet): %s. "
            "Indexes will be created on first successful connection.",
            str(e)[:120],
        )

    # ------------------------------------------------------------------ #
    # Logging                                                              #
    # ------------------------------------------------------------------ #
    setup_logger(app)

    # ------------------------------------------------------------------ #
    # Error Handlers & JWT Callbacks                                       #
    # ------------------------------------------------------------------ #
    _register_error_handlers(app)

    # ------------------------------------------------------------------ #
    # Register blueprints (route handlers)                                 #
    # ------------------------------------------------------------------ #
    _register_blueprints(app)

    app.logger.info(
        "StyleSense started [env=%s, db=%s]",
        config_name,
        app.config["MONGODB_DB_NAME"],
    )

    return app


def _register_error_handlers(app: Flask) -> None:
    """Register standard JSON responses for errors and JWT events."""
    from app.utils.response import error_response

    @jwt.unauthorized_loader
    def unauthorized_callback(callback):
        return error_response(
            "UNAUTHORIZED", "Missing or invalid Authorization header. Please login.", 401
        )

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return error_response(
            "TOKEN_EXPIRED", "Your session has expired. Please login again.", 401
        )

    @jwt.invalid_token_loader
    def invalid_token_callback(callback):
        return error_response("INVALID_TOKEN", "Invalid authorization token.", 401)

    @app.errorhandler(404)
    def not_found(e):
        return error_response("NOT_FOUND", "The requested resource was not found.", 404)

    @app.errorhandler(405)
    def method_not_allowed(e):
        return error_response("METHOD_NOT_ALLOWED", "Method not allowed for this endpoint.", 405)

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error("Internal Server Error: %s", e)
        return error_response("INTERNAL_SERVER_ERROR", "An unexpected error occurred.", 500)


def _register_blueprints(app: Flask) -> None:
    """Import and register all route blueprints."""
    from app.routes.auth_routes import auth_bp
    from app.routes.product_routes import product_bp
    from app.routes.recommendation_routes import recommendation_bp
    from app.routes.cart_routes import cart_bp
    from app.routes.wishlist_routes import wishlist_bp
    from app.routes.interaction_routes import interaction_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(product_bp, url_prefix="/api/products")
    app.register_blueprint(recommendation_bp, url_prefix="/api/recommendations")
    app.register_blueprint(cart_bp, url_prefix="/api/cart")
    app.register_blueprint(wishlist_bp, url_prefix="/api/wishlist")
    app.register_blueprint(interaction_bp, url_prefix="/api/interactions")


def _ensure_indexes(db) -> None:
    """
    Create MongoDB indexes for frequently queried fields.

    Indexes are idempotent — safe to call on every startup.
    Each index is explained below so you can discuss the reasoning
    in a technical interview.
    """
    # users: email and username must be unique and are looked up on login
    db.users.create_index("email", unique=True)
    db.users.create_index("username", unique=True)

    # products: queried heavily by category, brand, gender, availability
    db.products.create_index("product_id", unique=True)
    db.products.create_index("category")
    db.products.create_index("brand")
    db.products.create_index("gender")
    db.products.create_index("is_available")
    # Compound index for the most common filter combination
    db.products.create_index([("category", 1), ("gender", 1), ("is_available", 1)])
    # Text index for full-text search on name and description
    db.products.create_index([("name", "text"), ("description", "text")])

    # interactions: queried by user to build recommendation profiles
    db.interactions.create_index("user_id")
    db.interactions.create_index("product_id")
    db.interactions.create_index("timestamp")
    # Compound index for "all interactions by this user on this product"
    db.interactions.create_index([("user_id", 1), ("product_id", 1)])

    # wishlists: the compound unique index prevents duplicate wishlist entries
    # at the database level — not just in application code
    db.wishlists.create_index(
        [("user_id", 1), ("product_id", 1)], unique=True
    )

    # carts: one cart document per user
    db.carts.create_index("user_id", unique=True)
