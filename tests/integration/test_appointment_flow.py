import pytest
from backend.app import create_app
from backend.db import init_db, get_db
from backend.config import Config
import os

@pytest.fixture
def client(monkeypatch, tmp_path):
    db_file = tmp_path / "appt.db"
    monkeypatch.setenv("SECRET_KEY", "apptsecret")
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
    data = r.get_json()
    return data["csrf_token"]

def test_double_booking_blocked(client):
    csrf = _login(client, "reception", "staff123")  # Staff can book

    # Get patient Alice (user `alice` is Patient; seed created a patient record or we'll just create one)
    # We'll create a patient first (Staff allowed)
    r_pat = client.post(
        "/api/patients",
        json={
            "first_name": "Alice",
            "last_name": "Doe",
            "dob": "1990-01-01",
            "phone": "555-0000",
            "medical_history": "N/A",
            "owner_user_id": 5  # alice in seed
        },
        headers={"X-CSRF-Token": csrf}
    )
    assert r_pat.status_code == 201
    pid = r_pat.get_json()["patient_id"]

    # create first appt for drsmith
    first = client.post(
        "/api/appointments",
        json={
            "patient_id": pid,
            "doctor_id": 2,  # drsmith is seeded as id 2 typically
            "start_time": "2025-10-24 13:30",
            "reason": "Checkup"
        },
        headers={"X-CSRF-Token": csrf}
    )
    assert first.status_code == 201

    # create second appt same doctor same time -> expect 409
    second = client.post(
        "/api/appointments",
        json={
            "patient_id": pid,
            "doctor_id": 2,
            "start_time": "2025-10-24 13:30",
            "reason": "Another"
        },
        headers={"X-CSRF-Token": csrf}
    )
    assert second.status_code == 409
    j = second.get_json()
    assert j["ok"] is False
    assert "Doctor already has an appointment" in j["error"]
