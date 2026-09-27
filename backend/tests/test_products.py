"""
Tests for StyleSense Product Catalog APIs.
"""


def test_list_products_pagination(client):
    res = client.get("/api/products?page=1&per_page=15")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert len(data["data"]["products"]) == 15
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["per_page"] == 15
    assert data["pagination"]["total"] >= 900


def test_filter_products_by_category(client):
    res = client.get("/api/products?category=Topwear&per_page=10")
    assert res.status_code == 200
    data = res.get_json()
    products = data["data"]["products"]
    assert len(products) > 0
    for p in products:
        assert p["category"] == "Topwear"


def test_get_product_detail_and_404(client):
    # Valid product
    res = client.get("/api/products/P000001")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["product"]["product_id"] == "P000001"

    # Non-existent product
    res_404 = client.get("/api/products/P999999")
    assert res_404.status_code == 404
    assert res_404.get_json()["success"] is False


def test_search_products(client):
    res = client.get("/api/products/search?q=Cotton")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "products" in data["data"]
    assert "pagination" in data


def test_categories_and_brands_endpoints(client):
    res_cats = client.get("/api/products/categories")
    assert res_cats.status_code == 200
    cats = res_cats.get_json()["data"]["categories"]
    assert "Topwear" in cats
    assert "Bottomwear" in cats

    res_brands = client.get("/api/products/brands")
    assert res_brands.status_code == 200
    brands = res_brands.get_json()["data"]["brands"]
    assert len(brands) > 0
