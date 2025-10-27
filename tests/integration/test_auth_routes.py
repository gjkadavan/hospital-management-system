import pytest
from backend.app import create_app
from backend.db import init_db, get_db
from backend.config import Config
import os

@pytest.fixture
def client(monkeypatch, tmp_path):
    # point DB to temp file
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("SECRET_KEY", "testsecret")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("TESTING", "True")
    monkeypatch.setenv("DEBUG", "False")

    # re-init DB
    init_db()
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

def test_login_success_and_me(client):
    resp = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert "csrf_token" in data
    assert data["user"]["role"] == "Admin"

    # /me should now reflect session
    resp2 = client.get("/api/auth/me")
    assert resp2.status_code == 200
    me_data = resp2.get_json()
    assert me_data["ok"] is True
    assert me_data["user"]["role"] == "Admin"

def test_login_fail(client):
    resp = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "wrong"
    })
    assert resp.status_code == 401
    assert resp.get_json()["ok"] is False
