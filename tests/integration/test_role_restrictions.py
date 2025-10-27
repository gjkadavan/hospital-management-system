import pytest
from backend.app import create_app
from backend.db import init_db
import os

@pytest.fixture
def client(monkeypatch, tmp_path):
    db_file = tmp_path / "roles.db"
    monkeypatch.setenv("SECRET_KEY", "rolessecret")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("TESTING", "True")
    monkeypatch.setenv("DEBUG", "False")

    init_db()
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

def _login(client, username, password):
    r = client.post("/api/auth/login", json={
        "username": username,
        "password": password
    })
    assert r.status_code == 200
    return r.get_json()

def test_pharmacy_can_create_billing_but_patient_cannot(client):
    # login pharmacy
    pharma = _login(client, "pharma", "pharma123")
    csrf_pharma = pharma["csrf_token"]

    # pharmacy creates billing for patient_id=1
    r_bill = client.post(
        "/api/billing",
        json={"patient_id": 1, "amount": "99.50", "description": "Antibiotics"},
        headers={"X-CSRF-Token": csrf_pharma}
    )
    assert r_bill.status_code == 201

    # login patient alice (patient role)
    pat = _login(client, "alice", "patient123")
    csrf_pat = pat["csrf_token"]

    # patient tries to create billing -> should be forbidden
    r_bad = client.post(
        "/api/billing",
        json={"patient_id": 1, "amount": "5", "description": "Hack"},
        headers={"X-CSRF-Token": csrf_pat}
    )
    assert r_bad.status_code in (401, 403)
