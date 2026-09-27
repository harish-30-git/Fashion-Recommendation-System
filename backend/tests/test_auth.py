"""
Tests for StyleSense Authentication APIs.
"""

import uuid


def test_register_success(client):
    uid = uuid.uuid4().hex[:8]
    payload = {
        "email": f"newuser_{uid}@example.com",
        "username": f"user_{uid}",
        "password": "SecurePassword123!",
        "full_name": "New User",
        "gender": "Women",
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "user" in data["data"]
    assert "password_hash" not in data["data"]["user"]
    assert data["data"]["user"]["email"] == payload["email"]


def test_register_duplicate_email(client):
    uid = uuid.uuid4().hex[:8]
    payload = {
        "email": f"dup_{uid}@example.com",
        "username": f"dup1_{uid}",
        "password": "Password123!",
        "full_name": "User One",
    }
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    payload["username"] = f"dup2_{uid}"  # different username, same email
    res2 = client.post("/api/auth/register", json=payload)
    assert res2.status_code == 400
    data = res2.get_json()
    assert data["success"] is False
    assert "already exists" in data["message"]


def test_login_success_and_failure(client):
    uid = uuid.uuid4().hex[:8]
    email = f"login_{uid}@example.com"
    password = "CorrectPassword123!"

    # Register
    client.post("/api/auth/register", json={
        "email": email,
        "username": f"log_{uid}",
        "password": password,
        "full_name": "Login User",
    })

    # Login with wrong password
    res_fail = client.post("/api/auth/login", json={
        "email": email,
        "password": "WrongPassword!",
    })
    assert res_fail.status_code == 401
    assert res_fail.get_json()["success"] is False

    # Login with correct password
    res_succ = client.post("/api/auth/login", json={
        "email": email,
        "password": password,
    })
    assert res_succ.status_code == 200
    data = res_succ.get_json()
    assert data["success"] is True
    assert "access_token" in data["data"]


def test_get_current_user_profile(client, auth_headers):
    # Authenticated
    res = client.get("/api/auth/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "user" in data["data"]
    assert "password_hash" not in data["data"]["user"]

    # Unauthenticated
    res_unauth = client.get("/api/auth/me")
    assert res_unauth.status_code == 401
    assert res_unauth.get_json()["success"] is False
