import pytest
from backend.app import create_app
from backend.db import init_db

@pytest.fixture
def app():
    """
    Create a fresh Flask app in testing mode with an in-memory DB.
    Initializes schema + demo users.
    """
    flask_app = create_app(testing=True)
    with flask_app.app_context():
        init_db(seed_demo_users=True)
    yield flask_app


@pytest.fixture
def client(app):
    """
    Flask test client to call routes like /api/auth/login
    without running an external server.
    """
    return app.test_client()


def login_as(client, username, password):
    """
    Helper to log in and return parsed JSON (including csrf_token).
    """
    resp = client.post("/api/auth/login", json={
        "username": username,
        "password": password
    })
    assert resp.status_code == 200, "login failed in test helper"
    data = resp.get_json()
    assert data["ok"] is True
    return data


def auth_and_get_csrf_as_role(client, username, password):
    """
    Log in as a given role, return csrf token string.
    Use this token in X-CSRF-Token header for POST/PUT/DELETE.
    """
    data = login_as(client, username, password)
    return data["csrf_token"]
