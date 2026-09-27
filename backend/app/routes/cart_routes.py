"""
Shopping Cart Routes for StyleSense.

All cart routes are strictly protected with JWT authentication.
Each user can only access and manipulate their own cart.

Endpoints:
  GET    /api/cart
  POST   /api/cart/items
  PATCH  /api/cart/items/<product_id>
  DELETE /api/cart/items/<product_id>
  DELETE /api/cart
"""

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

import app.extensions as ext
from app.repositories.cart_repository import CartRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.interaction_repository import InteractionRepository
from app.services.cart_service import CartService
from app.utils.response import success_response, error_response

cart_bp = Blueprint("cart", __name__)


def _get_cart_service() -> CartService:
    return CartService(
        cart_repo=CartRepository(ext.db),
        product_repo=ProductRepository(ext.db),
        interaction_repo=InteractionRepository(ext.db),
        interaction_weights=current_app.config.get("INTERACTION_WEIGHTS"),
    )


@cart_bp.route("", methods=["GET"])
@jwt_required()
def get_cart():
    user_id = get_jwt_identity()
    service = _get_cart_service()
    cart = service.get_cart(user_id)
    return success_response(data={"cart": cart})


@cart_bp.route("/items", methods=["POST"])
@jwt_required()
def add_item():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True)
    if not data or not data.get("product_id"):
        return error_response("VALIDATION_ERROR", "'product_id' is required.", 400)

    product_id = data["product_id"]
    quantity = int(data.get("quantity", 1))
    size = str(data.get("size", "M"))
    color = str(data.get("color", "Default"))

    if quantity < 1:
        return error_response("INVALID_QUANTITY", "Quantity must be at least 1.", 400)

    service = _get_cart_service()
    cart, error = service.add_item(
        user_id=user_id,
        product_id=product_id,
        quantity=quantity,
        size=size,
        color=color,
    )

    if error:
        return error_response("CART_ERROR", error, 400)

    return success_response(data={"cart": cart}, message="Item added to cart.", status_code=201)


@cart_bp.route("/items/<product_id>", methods=["PATCH"])
@jwt_required()
def update_item_quantity(product_id: str):
    user_id = get_jwt_identity()
    data = request.get_json(silent=True)
    if not data or "quantity" not in data:
        return error_response("VALIDATION_ERROR", "'quantity' field is required.", 400)

    try:
        quantity = int(data["quantity"])
    except (ValueError, TypeError):
        return error_response("VALIDATION_ERROR", "'quantity' must be an integer.", 400)

    service = _get_cart_service()
    cart, error = service.update_item_quantity(
        user_id=user_id, product_id=product_id, quantity=quantity
    )

    if error:
        return error_response("CART_ERROR", error, 400)

    return success_response(data={"cart": cart}, message="Cart item updated.")


@cart_bp.route("/items/<product_id>", methods=["DELETE"])
@jwt_required()
def remove_item(product_id: str):
    user_id = get_jwt_identity()
    service = _get_cart_service()
    cart = service.remove_item(user_id=user_id, product_id=product_id)
    return success_response(data={"cart": cart}, message="Item removed from cart.")


@cart_bp.route("", methods=["DELETE"])
@jwt_required()
def clear_cart():
    user_id = get_jwt_identity()
    service = _get_cart_service()
    cart = service.clear_cart(user_id=user_id)
    return success_response(data={"cart": cart}, message="Cart cleared.")
