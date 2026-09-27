"""
Product Catalog Routes for StyleSense.

Endpoints:
  GET /api/products
  GET /api/products/<product_id>
  GET /api/products/search
  GET /api/products/categories
  GET /api/products/brands
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

import app.extensions as ext
from app.repositories.product_repository import ProductRepository
from app.repositories.interaction_repository import InteractionRepository
from app.services.product_service import ProductService
from app.services.interaction_service import InteractionService
from app.utils.pagination import get_pagination_params
from app.utils.response import success_response, error_response

product_bp = Blueprint("products", __name__)


def _get_product_service() -> ProductService:
    return ProductService(ProductRepository(ext.db))


def _get_interaction_service() -> InteractionService:
    return InteractionService(InteractionRepository(ext.db), ProductRepository(ext.db))


@product_bp.route("", methods=["GET"])
def list_products():
    page, per_page = get_pagination_params(request)

    category = request.args.get("category")
    brand = request.args.get("brand")
    gender = request.args.get("gender")
    size = request.args.get("size")
    color = request.args.get("color")
    sort_by = request.args.get("sort_by")

    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)

    service = _get_product_service()
    items, pagination = service.get_products(
        page=page,
        per_page=per_page,
        category=category,
        brand=brand,
        gender=gender,
        min_price=min_price,
        max_price=max_price,
        size=size,
        color=color,
        sort_by=sort_by,
    )

    return success_response(
        data={"products": items},
        pagination=pagination,
        status_code=200,
    )


@product_bp.route("/search", methods=["GET"])
def search_products():
    query = request.args.get("q", "")
    page, per_page = get_pagination_params(request)
    category = request.args.get("category")
    gender = request.args.get("gender")

    service = _get_product_service()
    items, pagination = service.search_products(
        query=query,
        page=page,
        per_page=per_page,
        category=category,
        gender=gender,
    )

    return success_response(
        data={"products": items, "query": query},
        pagination=pagination,
        status_code=200,
    )


@product_bp.route("/categories", methods=["GET"])
def get_categories():
    service = _get_product_service()
    categories = service.get_categories()
    return success_response(data={"categories": categories})


@product_bp.route("/brands", methods=["GET"])
def get_brands():
    category = request.args.get("category")
    service = _get_product_service()
    brands = service.get_brands(category=category)
    return success_response(data={"brands": brands})


@product_bp.route("/<product_id>", methods=["GET"])
@jwt_required(optional=True)
def get_product(product_id: str):
    service = _get_product_service()
    product = service.get_product_by_id(product_id)

    if not product:
        return error_response("PRODUCT_NOT_FOUND", f"Product '{product_id}' not found.", 404)

    # If user is authenticated, track 'view' interaction
    current_user_id = get_jwt_identity()
    if current_user_id:
        try:
            interaction_svc = _get_interaction_service()
            interaction_svc.log(
                user_id=current_user_id,
                product_id=product_id,
                interaction_type="view",
            )
        except Exception:
            pass

    return success_response(data={"product": product})
