"""
Shopping Cart Service for StyleSense.

CRITICAL SECURITY & INTEGRITY RULES:
  1. Backend Price Calculation: The client NEVER dictates unit_price or cart total.
     Unit price is snapshotted from the product catalog in the database at the time
     of adding to cart.
  2. Stock Validation: Quantities are strictly checked against real-time stock
     before accepting additions or updates.
  3. Hydration: Cart item responses hydrate current product metadata (name, brand,
     image_url, and current stock status) alongside stored item details.
"""

from typing import Any
from app.repositories.cart_repository import CartRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.interaction_repository import InteractionRepository


class CartService:
    def __init__(
        self,
        cart_repo: CartRepository,
        product_repo: ProductRepository,
        interaction_repo: InteractionRepository | None = None,
        interaction_weights: dict[str, float] | None = None,
    ):
        self.cart_repo = cart_repo
        self.product_repo = product_repo
        self.interaction_repo = interaction_repo
        self.weights = interaction_weights or {"cart": 2.0}

    def get_cart(self, user_id: str) -> dict[str, Any]:
        """Fetch user cart with hydrated product details."""
        raw_cart = self.cart_repo.get_by_user(user_id)
        return self._hydrate_cart(raw_cart)

    def add_item(
        self,
        user_id: str,
        product_id: str,
        quantity: int,
        size: str,
        color: str,
    ) -> tuple[dict[str, Any] | None, str | None]:
        """
        Add an item to the shopping cart.

        Returns:
            (hydrated_cart_dict, error_message)
        """
        product = self.product_repo.find_by_id(product_id)
        if not product:
            return None, "Product not found."

        if not product.get("is_available", True) or product.get("stock", 0) <= 0:
            return None, "This product is currently out of stock."

        if quantity > product.get("stock", 0):
            return None, f"Requested quantity ({quantity}) exceeds available stock ({product.get('stock')})."

        # Snapshot unit price from DB (selling price)
        unit_price = float(product.get("discounted_price", product.get("price", 0.0)))

        # Update cart
        raw_cart = self.cart_repo.add_item(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
            size=size,
            color=color,
            unit_price=unit_price,
        )

        # Log cart interaction for personalized recommendations
        if self.interaction_repo:
            try:
                self.interaction_repo.log(
                    user_id=user_id,
                    product_id=product_id,
                    interaction_type="cart",
                    weights=self.weights,
                )
            except Exception:
                pass

        return self._hydrate_cart(raw_cart), None

    def update_item_quantity(
        self, user_id: str, product_id: str, quantity: int
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Update quantity of an existing item in the cart."""
        product = self.product_repo.find_by_id(product_id)
        if not product:
            return None, "Product not found."

        if quantity > product.get("stock", 0):
            return None, f"Requested quantity exceeds available stock ({product.get('stock')})."

        if quantity <= 0:
            raw_cart = self.cart_repo.remove_item(user_id, product_id)
        else:
            raw_cart = self.cart_repo.update_item_quantity(user_id, product_id, quantity)

        return self._hydrate_cart(raw_cart), None

    def remove_item(self, user_id: str, product_id: str) -> dict[str, Any]:
        """Remove an item from the cart."""
        raw_cart = self.cart_repo.remove_item(user_id, product_id)
        return self._hydrate_cart(raw_cart)

    def clear_cart(self, user_id: str) -> dict[str, Any]:
        """Empty the user's cart."""
        raw_cart = self.cart_repo.clear(user_id)
        return self._hydrate_cart(raw_cart)

    def _hydrate_cart(self, raw_cart: dict[str, Any]) -> dict[str, Any]:
        """Hydrate cart items with current product metadata and live stock."""
        items = raw_cart.get("items", [])
        if not items:
            return raw_cart

        pids = [item["product_id"] for item in items]
        products = self.product_repo.find_by_ids(pids)
        prod_map = {p["product_id"]: p for p in products}

        hydrated_items = []
        for item in items:
            h_item = dict(item)
            p = prod_map.get(item["product_id"])
            if p:
                h_item["name"] = p.get("name")
                h_item["brand"] = p.get("brand")
                h_item["image_url"] = p.get("image_url")
                h_item["current_price"] = p.get("discounted_price")
                h_item["in_stock"] = p.get("is_available", True) and p.get("stock", 0) >= item["quantity"]
                h_item["available_stock"] = p.get("stock", 0)
            hydrated_items.append(h_item)

        result = dict(raw_cart)
        result["items"] = hydrated_items
        return result
