"""
Tests for StyleSense Recommendation APIs.
"""


def test_trending_recommendations(client):
    res = client.get("/api/recommendations/trending?top_k=8")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    recs = data["data"]["trending_products"]
    assert len(recs) <= 8
    assert len(recs) > 0


def test_similar_products_recommendations(client):
    res = client.get("/api/recommendations/similar/P000001?top_k=5")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    sims = data["data"]["similar_products"]
    assert len(sims) <= 5
    for item in sims:
        assert item["product_id"] != "P000001"  # original product excluded
        assert "similarity_score" in item


def test_complementary_products_recommendations(client):
    res = client.get("/api/recommendations/complementary/P000001?top_k=4")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    comps = data["data"]["complementary_products"]
    assert len(comps) <= 4


def test_personalized_recommendations(client, auth_headers):
    # Anonymous request -> returns trending
    res_anon = client.get("/api/recommendations/personalized?top_k=5")
    assert res_anon.status_code == 200
    assert res_anon.get_json()["data"]["personalized"] is False

    # Authenticated user request
    res_auth = client.get("/api/recommendations/personalized?top_k=5", headers=auth_headers)
    assert res_auth.status_code == 200
    assert res_auth.get_json()["data"]["personalized"] is True
    recs = res_auth.get_json()["data"]["recommendations"]
    assert len(recs) > 0
    for r in recs:
        assert "recommendation_reason" in r
