from tests.conftest import auth_and_get_csrf_as_role

def test_uat_admin_can_view_staff_list(client):
    """
    Role: Admin
    Steps:
      1. Login as admin.
      2. GET /api/staff
    Expected:
      - 200 OK
      - returns list of users with roles.
    """
    csrf_admin = auth_and_get_csrf_as_role(client, "admin", "admin123")
    resp = client.get("/api/staff", headers={"X-CSRF-Token": csrf_admin})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert any(u["role"] == "doctor" for u in data["staff"])

def test_uat_doctor_can_add_record(client):
    """
    Role: Doctor
    Steps:
      1. Login as drsmith (doctor).
      2. POST /api/records/1 with record_text.
    Expected:
      - 201 Created
      - ok: True
    """
    csrf_doc = auth_and_get_csrf_as_role(client, "drsmith", "doctor123")
    resp = client.post(
        "/api/records/1",
        json={"record_text": "Follow-up note from UAT"},
        headers={"X-CSRF-Token": csrf_doc}
    )
    assert resp.status_code == 201
    assert resp.get_json()["ok"] is True

def test_uat_pharmacy_cannot_access_billing(client):
    """
    Role: Pharmacy
    Steps:
      1. Login as pharma.
      2. GET /api/billing
    Expected:
      - 401/403 (forbidden)
    """
    csrf_pharm = auth_and_get_csrf_as_role(client, "pharma", "pharm123")
    resp = client.get("/api/billing", headers={"X-CSRF-Token": csrf_pharm})
    assert resp.status_code in (401,403)
    data = resp.get_json()
    assert data["ok"] is False

def test_uat_staff_can_create_billing_item(client):
    """
    Role: Staff
    Steps:
      1. Login as reception (staff).
      2. POST /api/billing with patient_id, amount, description.
    Expected:
      - 201 Created
      - ok: True
    """
    csrf_staff = auth_and_get_csrf_as_role(client, "reception", "staff123")
    new_bill = {
        "patient_id": 1,
        "amount": 200.0,
        "description": "Blood Test"
    }
    resp = client.post(
        "/api/billing",
        json=new_bill,
        headers={"X-CSRF-Token": csrf_staff}
    )
    assert resp.status_code == 201
    assert resp.get_json()["ok"] is True
