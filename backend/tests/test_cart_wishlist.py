"""
Tests for StyleSense Cart, Wishlist, and Interaction APIs.
"""


def test_cart_operations(client, auth_headers):
    # 1. Initially empty
    res_get = client.get("/api/cart", headers=auth_headers)
    assert res_get.status_code == 200
    cart = res_get.get_json()["data"]["cart"]
    assert len(cart["items"]) == 0

    # 2. Add product P000001
    res_add = client.post(
        "/api/cart/items",
        json={"product_id": "P000001", "quantity": 2, "size": "M", "color": "Maroon"},
        headers=auth_headers,
    )
    assert res_add.status_code == 201
    data = res_add.get_json()["data"]["cart"]
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2
    # Verify unit_price calculated on backend, not submitted by client
    assert data["items"][0]["unit_price"] > 0
    assert data["total"] == round(data["items"][0]["unit_price"] * 2, 2)

    # 3. Update quantity
    res_patch = client.patch(
        "/api/cart/items/P000001",
        json={"quantity": 3},
        headers=auth_headers,
    )
    assert res_patch.status_code == 200
    cart_updated = res_patch.get_json()["data"]["cart"]
    assert cart_updated["items"][0]["quantity"] == 3

    # 4. Remove item
    res_del = client.delete("/api/cart/items/P000001", headers=auth_headers)
    assert res_del.status_code == 200
    cart_empty = res_del.get_json()["data"]["cart"]
    assert len(cart_empty["items"]) == 0


def test_wishlist_operations(client, auth_headers):
    # 1. Add to wishlist
    res_add = client.post(
        "/api/wishlist",
        json={"product_id": "P000002"},
        headers=auth_headers,
    )
    assert res_add.status_code == 201
    assert res_add.get_json()["success"] is True

    # 2. Get wishlist
    res_get = client.get("/api/wishlist", headers=auth_headers)
    assert res_get.status_code == 200
    items = res_get.get_json()["data"]["wishlist"]
    assert len(items) >= 1
    assert any(p["product_id"] == "P000002" for p in items)

    # 3. Wishlist-driven recommendations
    res_rec = client.get("/api/wishlist/recommendations?top_k=4", headers=auth_headers)
    assert res_rec.status_code == 200
    assert "recommendations" in res_rec.get_json()["data"]

    # 4. Remove from wishlist
    res_del = client.delete("/api/wishlist/P000002", headers=auth_headers)
    assert res_del.status_code == 200


def test_interaction_logging(client, auth_headers):
    payload = {
        "product_id": "P000003",
        "interaction_type": "view",
    }
    res = client.post("/api/interactions", json=payload, headers=auth_headers)
    assert res.status_code == 201
    assert res.get_json()["success"] is True

    # Get history
    res_hist = client.get("/api/interactions/history", headers=auth_headers)
    assert res_hist.status_code == 200
    history = res_hist.get_json()["data"]["history"]
    assert len(history) >= 1
