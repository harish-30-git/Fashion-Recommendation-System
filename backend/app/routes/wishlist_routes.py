"""
Wishlist Routes for StyleSense.

All wishlist operations require JWT authentication and are scoped strictly
to the authenticated user.

Endpoints:
  GET    /api/wishlist
  POST   /api/wishlist
  DELETE /api/wishlist/<product_id>
  GET    /api/wishlist/recommendations
"""

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

import app.extensions as ext
from app.repositories.wishlist_repository import WishlistRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.interaction_repository import InteractionRepository
from app.services.wishlist_service import WishlistService
from app.utils.response import success_response, error_response

wishlist_bp = Blueprint("wishlist", __name__)


def _get_wishlist_service() -> WishlistService:
    return WishlistService(
        wishlist_repo=WishlistRepository(ext.db),
        product_repo=ProductRepository(ext.db),
        interaction_repo=InteractionRepository(ext.db),
        interaction_weights=current_app.config.get("INTERACTION_WEIGHTS"),
    )


@wishlist_bp.route("", methods=["GET"])
@jwt_required()
def get_wishlist():
    user_id = get_jwt_identity()
    service = _get_wishlist_service()
    products = service.get_wishlist(user_id)
    return success_response(
        data={"wishlist": products, "count": len(products)},
        message="Wishlist retrieved.",
    )


@wishlist_bp.route("", methods=["POST"])
@jwt_required()
def add_to_wishlist():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True)
    if not data or not data.get("product_id"):
        return error_response("VALIDATION_ERROR", "'product_id' is required.", 400)

    product_id = data["product_id"]
    service = _get_wishlist_service()
    success, error = service.add_to_wishlist(user_id=user_id, product_id=product_id)

    if error:
        return error_response("WISHLIST_ERROR", error, 400)

    return success_response(
        data={"product_id": product_id, "saved": True},
        message="Product saved to wishlist.",
        status_code=201,
    )


@wishlist_bp.route("/<product_id>", methods=["DELETE"])
@jwt_required()
def remove_from_wishlist(product_id: str):
    user_id = get_jwt_identity()
    service = _get_wishlist_service()
    removed = service.remove_from_wishlist(user_id=user_id, product_id=product_id)
    return success_response(
        data={"product_id": product_id, "removed": removed},
        message="Product removed from wishlist.",
    )


@wishlist_bp.route("/recommendations", methods=["GET"])
@jwt_required()
def get_wishlist_recommendations():
    user_id = get_jwt_identity()
    top_k = min(30, max(1, request.args.get("top_k", 10, type=int)))
    service = _get_wishlist_service()
    recommendations = service.get_similar_from_wishlist(user_id=user_id, top_k=top_k)
    return success_response(
        data={"recommendations": recommendations, "count": len(recommendations)},
        message="Wishlist-driven recommendations generated.",
    )
