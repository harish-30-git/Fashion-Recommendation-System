"""
Pytest configuration and shared fixtures for StyleSense.
"""

import sys
from pathlib import Path
import pytest

# Ensure backend root is in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
import app.extensions as ext


@pytest.fixture(scope="session")
def app():
    """Create and configure a Flask app for testing."""
    test_app = create_app("development")
    test_app.config.update({
        "TESTING": True,
    })
    yield test_app


@pytest.fixture(scope="session")
def client(app):
    """Test client for making HTTP requests."""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Register and log in a temporary test user, returning auth headers."""
    import uuid
    rand_id = uuid.uuid4().hex[:8]
    register_payload = {
        "email": f"testuser_{rand_id}@example.com",
        "username": f"test_{rand_id}",
        "password": "Password123!",
        "full_name": "Test Runner",
        "gender": "Unisex",
    }
    res = client.post("/api/auth/register", json=register_payload)
    data = res.get_json()
    token = data["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
