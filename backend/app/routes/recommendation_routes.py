"""
Recommendation Routes for StyleSense.

Endpoints:
  GET /api/recommendations/personalized (JWT optional: personalized if authenticated, trending if anonymous)
  GET /api/recommendations/similar/<product_id>
  GET /api/recommendations/trending
  GET /api/recommendations/complementary/<product_id>
"""

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

import app.extensions as ext
from app.repositories.product_repository import ProductRepository
from app.repositories.interaction_repository import InteractionRepository
from app.services.recommendation_service import RecommendationService
from app.utils.response import success_response, error_response

recommendation_bp = Blueprint("recommendations", __name__)


def _get_recommendation_service() -> RecommendationService:
    return RecommendationService(
        product_repo=ProductRepository(ext.db),
        interaction_repo=InteractionRepository(ext.db),
        hybrid_w1=current_app.config.get("HYBRID_W1", 0.5),
        hybrid_w2=current_app.config.get("HYBRID_W2", 0.3),
        hybrid_w3=current_app.config.get("HYBRID_W3", 0.2),
    )


@recommendation_bp.route("/personalized", methods=["GET"])
@jwt_required(optional=True)
def get_personalized():
    top_k = min(50, max(1, request.args.get("top_k", 10, type=int)))
    user_id = get_jwt_identity()

    service = _get_recommendation_service()
    recommendations = service.get_personalized(user_id=user_id, top_k=top_k)

    return success_response(
        data={
            "recommendations": recommendations,
            "personalized": bool(user_id),
            "count": len(recommendations),
        },
        message="Personalized recommendations retrieved." if user_id else "Trending items for discovery.",
    )


@recommendation_bp.route("/similar/<product_id>", methods=["GET"])
def get_similar(product_id: str):
    top_k = min(30, max(1, request.args.get("top_k", 10, type=int)))

    service = _get_recommendation_service()
    items = service.get_similar(product_id=product_id, top_k=top_k)

    return success_response(
        data={"similar_products": items, "seed_product_id": product_id, "count": len(items)},
        message="Similar items retrieved via TF-IDF cosine similarity.",
    )


@recommendation_bp.route("/trending", methods=["GET"])
def get_trending():
    top_k = min(50, max(1, request.args.get("top_k", 20, type=int)))
    category = request.args.get("category")

    service = _get_recommendation_service()
    items = service.get_trending(category=category, top_k=top_k)

    return success_response(
        data={"trending_products": items, "count": len(items)},
        message="Trending products retrieved.",
    )


@recommendation_bp.route("/complementary/<product_id>", methods=["GET"])
def get_complementary(product_id: str):
    top_k = min(12, max(1, request.args.get("top_k", 6, type=int)))

    service = _get_recommendation_service()
    items = service.get_complementary(product_id=product_id, top_k=top_k)

    return success_response(
        data={"complementary_products": items, "seed_product_id": product_id, "count": len(items)},
        message="Outfit complementary products generated.",
    )
