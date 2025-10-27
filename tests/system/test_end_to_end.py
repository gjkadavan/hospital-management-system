from tests.conftest import auth_and_get_csrf_as_role

def test_full_patient_flow(client):
    # 1. staff registers a new patient
    csrf_staff = auth_and_get_csrf_as_role(client, "reception", "staff123")
    new_patient = {
        "first_name": "Alice",
        "last_name": "Smith",
        "dob": "1990-01-01",
        "phone": "555-1234",
        "medical_history": "Asthma"
    }
    r_patient = client.post(
        "/api/patients",
        json=new_patient,
        headers={"X-CSRF-Token": csrf_staff}
    )
    assert r_patient.status_code == 201
    pid = r_patient.get_json()["patient_id"]

    # 2. staff books appointment with doctor (drsmith is seeded doctor)
    appt_payload = {
        "patient_id": pid,
        "doctor_id": 2,  # assumes drsmith got ID=2 in seed
        "appt_datetime": "2025-10-25 10:30",
        "notes": "Initial consult"
    }
    r_appt = client.post(
        "/api/appointments",
        json=appt_payload,
        headers={"X-CSRF-Token": csrf_staff}
    )
    assert r_appt.status_code == 201
    appt_id = r_appt.get_json()["appointment_id"]
    assert appt_id is not None

    # 3. doctor adds a medical record
    csrf_doc = auth_and_get_csrf_as_role(client, "drsmith", "doctor123")
    note_payload = {
        "record_text": "Mild wheeze, recommend inhaler"
    }
    r_note = client.post(
        f"/api/records/{pid}",
        json=note_payload,
        headers={"X-CSRF-Token": csrf_doc}
    )
    assert r_note.status_code == 201
    assert r_note.get_json()["ok"] is True

    # 4. doctor prescribes medication
    pharm_payload = {
        "patient_id": pid,
        "drug_name": "InhalerX",
        "quantity": 1
    }
    r_rx = client.post(
        "/api/pharmacy",
        json=pharm_payload,
        headers={"X-CSRF-Token": csrf_doc}
    )
    assert r_rx.status_code == 201
    assert r_rx.get_json()["ok"] is True

    # 5. pharmacy views queue
    csrf_pharm = auth_and_get_csrf_as_role(client, "pharma", "pharm123")
    r_queue = client.get(
        "/api/pharmacy",
        headers={"X-CSRF-Token": csrf_pharm}
    )
    assert r_queue.status_code == 200
    data = r_queue.get_json()
    assert data["ok"] is True
    assert len(data["pharmacy_orders"]) >= 1
