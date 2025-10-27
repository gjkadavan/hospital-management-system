from flask import Blueprint, request, jsonify, session
from datetime import datetime
import sqlite3

from ..db import get_db
from ..security import require_login_and_csrf
from ..validators import (
    validate_name,
    validate_phone,
    validate_datetime,
    validate_amount,
    validate_positive_int,
    sanitize_text,
)

api_bp = Blueprint("api_bp", __name__, url_prefix="/api")


# ------------------------------------------------------------------
# Internal helpers (not routes)
# ------------------------------------------------------------------

def _patient_visible_to_current_user(patient_row: dict) -> bool:
    """
    Visibility rules for patient record (including medical_history):
    - Admin / Staff / Doctor: can see all patients
    - That specific Patient: can see themselves
    - Pharmacy: can see demographics but NOT medical_history
      => We enforce redaction later.
    """
    user_role = session.get("role")
    user_id = session.get("user_id")
    if user_role in ("Admin", "Staff", "Doctor"):
        return True
    if user_role == "Patient":
        # If this patient is linked to this user_id via owner_user_id, allow.
        return patient_row.get("owner_user_id") == user_id
    if user_role == "Pharmacy":
        return True  # Pharmacy can see limited info (we'll redact history)
    return False


def _redact_patient_for_pharmacy(row: dict) -> dict:
    """
    Pharmacy should not see full medical_history.
    """
    if session.get("role") == "Pharmacy":
        redacted = dict(row)
        redacted["medical_history"] = "[REDACTED]"
        return redacted
    return dict(row)


def _role_allows_billing_creation(role: str) -> bool:
    # Only Admin or Pharmacy can create billing entries
    return role in ("Admin", "Pharmacy")


def _role_allows_billing_view(role: str) -> bool:
    # Admin / Pharmacy / Staff can view any;
    # Patients can view their own later when filtered.
    return role in ("Admin", "Pharmacy", "Staff", "Patient")


# ------------------------------------------------------------------
# PATIENT REGISTRATION
# Only Admin or Staff can register patients.
# ------------------------------------------------------------------

@api_bp.route("/patients", methods=["POST"])
def create_patient():
    ok, err = require_login_and_csrf(allowed_roles=["Admin", "Staff"])
    if not ok:
        msg, code = err
        return jsonify({"ok": False, "error": msg}), code

    data = request.json or {}
    fn = sanitize_text(data.get("first_name", ""), max_len=50)
    ln = sanitize_text(data.get("last_name", ""), max_len=50)
    dob = sanitize_text(data.get("dob", ""), max_len=10)  # "YYYY-MM-DD"
    phone = sanitize_text(data.get("phone", ""), max_len=20)
    history = sanitize_text(data.get("medical_history", ""), max_len=2000)
    owner_user_id = data.get("owner_user_id")  # (optional) link to Patient user account

    # Validate required fields
    if (
        not validate_name(fn)
        or not validate_name(ln)
        or not dob
        or not validate_phone(phone)
    ):
        return jsonify({"ok": False, "error": "Invalid input"}), 400

    # owner_user_id (if provided) must refer to a user with role=Patient
    if owner_user_id is not None and not validate_positive_int(owner_user_id):
        return jsonify({"ok": False, "error": "Invalid owner_user_id"}), 400

    conn = get_db()
    cur = conn.cursor()

    if owner_user_id:
        cur.execute("SELECT id, role FROM users WHERE id = ?;", (owner_user_id,))
        urow = cur.fetchone()
        if not urow or urow["role"] != "Patient":
            conn.close()
            return jsonify({"ok": False, "error": "Invalid owner user link"}), 400

    cur.execute(
        """
        INSERT INTO patients
            (first_name, last_name, dob, phone, medical_history,
             owner_user_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        (
            fn,
            ln,
            dob,
            phone,
            history,
            owner_user_id,
            datetime.utcnow().isoformat()
        )
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()

    return jsonify({"ok": True, "patient_id": new_id}), 201


# ------------------------------------------------------------------
# PATIENT FETCH (details)
# Visible to Admin, Staff, Doctor, Pharmacy (redacted), and that Patient.
# ------------------------------------------------------------------

@api_bp.route("/patients/<int:patient_id>", methods=["GET"])
def get_patient(patient_id: int):
    ok, err = require_login_and_csrf(
        allowed_roles=["Admin", "Staff", "Doctor", "Patient", "Pharmacy"]
    )
    if not ok:
        msg, code = err
        return jsonify({"ok": False, "error": msg}), code

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM patients WHERE id = ?;", (patient_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return jsonify({"ok": False, "error": "Not found"}), 404

    row = dict(row)

    if not _patient_visible_to_current_user(row):
        return jsonify({"ok": False, "error": "Forbidden"}), 403

    # Redact if pharmacy
    safe_row = _redact_patient_for_pharmacy(row)

    return jsonify({"ok": True, "patient": safe_row}), 200


# ------------------------------------------------------------------
# APPOINTMENTS
# Anyone can read their own relevant appointments (GET).
# Create rules:
# - Admin, Staff, Patient can create.
# - Validate doctor_id refers to a Doctor.
# - Validate datetime format.
# - UNIQUE(doctor_id,start_time) to block double booking -> 409 on violation.
# ------------------------------------------------------------------

@api_bp.route("/appointments", methods=["POST"])
def create_appointment():
    ok, err = require_login_and_csrf(allowed_roles=["Admin", "Staff", "Patient"])
    if not ok:
        msg, code = err
        return jsonify({"ok": False, "error": msg}), code

    data = request.json or {}
    patient_id = data.get("patient_id")
    doctor_id = data.get("doctor_id")
    start_time = data.get("start_time", "")
    reason = sanitize_text(data.get("reason", ""), max_len=200)

    if (
        not validate_positive_int(patient_id)
        or not validate_positive_int(doctor_id)
        or not validate_datetime(start_time)
    ):
        return jsonify({"ok": False, "error": "Invalid input"}), 400

    conn = get_db()
    cur = conn.cursor()

    # check patient exists
    cur.execute("SELECT id, owner_user_id FROM patients WHERE id = ?;", (patient_id,))
    prow = cur.fetchone()
    if not prow:
        conn.close()
        return jsonify({"ok": False, "error": "Unknown patient"}), 400

    # if caller is Patient role, enforce self-booking
    if session["role"] == "Patient":
        if prow["owner_user_id"] != session["user_id"]:
            conn.close()
            return jsonify({"ok": False, "error": "Forbidden"}), 403

    # check doctor exists AND has role Doctor
    cur.execute("SELECT id, role FROM users WHERE id = ?;", (doctor_id,))
    drow = cur.fetchone()
    if not drow or drow["role"] != "Doctor":
        conn.close()
        return jsonify({"ok": False, "error": "doctor_id must reference a Doctor"}), 400

    try:
        cur.execute(
            """
            INSERT INTO appointments
                (patient_id, doctor_id, start_time, reason, status, created_at)
            VALUES (?, ?, ?, ?, 'scheduled', ?);
            """,
            (
                patient_id,
                doctor_id,
                start_time,
                reason,
                datetime.utcnow().isoformat()
            )
        )
        conn.commit()
        new_id = cur.lastrowid
    except sqlite3.IntegrityError as e:
        # UNIQUE(doctor_id,start_time) violation -> double booking
        conn.rollback()
        conn.close()
        return jsonify({
            "ok": False,
            "error": "Doctor already has an appointment at that time",
            "detail": str(e)
        }), 409

    conn.close()
    return jsonify({"ok": True, "appointment_id": new_id}), 201


@api_bp.route("/appointments/<int:doctor_id>", methods=["GET"])
def list_appointments_for_doctor(doctor_id: int):
    """
    GET /api/appointments/<doctor_id>
    Admin/Staff/Doctor can view all appointments for that doctor.
    Patient can only see appointments where patient.owner_user_id == themselves
    Pharmacy should NOT see appointments (privacy).
    """
    ok, err = require_login_and_csrf(
        allowed_roles=["Admin", "Staff", "Doctor", "Patient"]
    )
    if not ok:
        msg, code = err
        return jsonify({"ok": False, "error": msg}), code

    # Pharmacy role is not in allowed_roles above, so it's already blocked.

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT a.id,
               a.patient_id,
               a.doctor_id,
               a.start_time,
               a.reason,
               a.status,
               a.created_at,
               p.first_name || ' ' || p.last_name AS patient_name,
               u.full_name AS doctor_name,
               p.owner_user_id AS patient_owner_uid
          FROM appointments a
          JOIN patients p ON p.id = a.patient_id
          JOIN users u    ON u.id = a.doctor_id
         WHERE a.doctor_id = ?
         ORDER BY a.start_time ASC;
        """,
        (doctor_id,)
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    role = session["role"]
    uid = session["user_id"]

    if role == "Patient":
        # keep only rows where this patient belongs to this user
        rows = [r for r in rows if r["patient_owner_uid"] == uid]

    # Drop patient_owner_uid from response
    for r in rows:
        if "patient_owner_uid" in r:
            del r["patient_owner_uid"]

    return jsonify({"ok": True, "appointments": rows}), 200


# ------------------------------------------------------------------
# PRESCRIPTIONS
# Only Doctor can create prescriptions.
# Viewing:
#   - Doctor / Pharmacy / Admin / Staff: can view any patient's prescriptions
#   - Patient: can ONLY view theirs.
# ------------------------------------------------------------------

@api_bp.route("/prescriptions", methods=["POST"])
def create_prescription():
    ok, err = require_login_and_csrf(allowed_roles=["Doctor"])
    if not ok:
        msg, code = err
        return jsonify({"ok": False, "error": msg}), code

    data = request.json or {}
    appointment_id = data.get("appointment_id")
    patient_id = data.get("patient_id")
    medication = sanitize_text(data.get("medication", ""), max_len=200)
    instructions = sanitize_text(data.get("instructions", ""), max_len=500)

    if (
        not validate_positive_int(appointment_id)
        or not validate_positive_int(patient_id)
        or not medication
        or not instructions
    ):
        return jsonify({"ok": False, "error": "Invalid input"}), 400

    conn = get_db()
    cur = conn.cursor()

    # Verify that appointment exists and matches patient_id and doctor_id==session user
    cur.execute(
        """
        SELECT id, doctor_id, patient_id
          FROM appointments
         WHERE id = ?;
        """,
        (appointment_id,)
    )
    arow = cur.fetchone()
    if (
        not arow
        or arow["patient_id"] != patient_id
        or arow["doctor_id"] != session["user_id"]
    ):
        conn.close()
        return jsonify({"ok": False, "error": "Appointment mismatch/unauthorized"}), 403

    cur.execute(
        """
        INSERT INTO prescriptions
            (appointment_id, doctor_id, patient_id,
             medication, instructions, created_at)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        (
            appointment_id,
            session["user_id"],
            patient_id,
            medication,
            instructions,
            datetime.utcnow().isoformat()
        )
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()

    return jsonify({"ok": True, "prescription_id": new_id}), 201


@api_bp.route("/prescriptions/<int:patient_id>", methods=["GET"])
def view_prescriptions(patient_id: int):
    ok, err = require_login_and_csrf(
        allowed_roles=["Doctor", "Pharmacy", "Admin", "Staff", "Patient"]
    )
    if not ok:
        msg, code = err
        return jsonify({"ok": False, "error": msg}), code

    # Patient can ONLY view their own prescriptions
    if session["role"] == "Patient" and session["user_id"] != patient_id:
        return jsonify({"ok": False, "error": "Forbidden"}), 403

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id,
               appointment_id,
               doctor_id,
               patient_id,
               medication,
               instructions,
               created_at
          FROM prescriptions
         WHERE patient_id = ?
         ORDER BY created_at DESC;
        """,
        (patient_id,)
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    return jsonify({"ok": True, "prescriptions": rows}), 200


# ------------------------------------------------------------------
# BILLING
# Creation:
#   - Admin or Pharmacy
#
# Viewing:
#   - Admin / Pharmacy / Staff: can view all
#   - Patient: can view only their own entries
# ------------------------------------------------------------------

@api_bp.route("/billing", methods=["POST"])
def create_bill():
    ok, err = require_login_and_csrf(
        allowed_roles=["Admin", "Pharmacy"]
    )
    if not ok:
        msg, code = err
        return jsonify({"ok": False, "error": msg}), code

    data = request.json or {}
    patient_id = data.get("patient_id")
    amount = data.get("amount")
    description = sanitize_text(data.get("description", ""), max_len=200)

    if (not validate_positive_int(patient_id)) or (not validate_amount(amount)):
        return jsonify({"ok": False, "error": "Invalid input"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO billing
            (patient_id, amount, description, status, created_at)
        VALUES (?, ?, ?, 'unpaid', ?);
        """,
        (
            patient_id,
            float(amount),
            description,
            datetime.utcnow().isoformat()
        )
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()

    return jsonify({"ok": True, "bill_id": new_id}), 201


@api_bp.route("/billing/<int:patient_id>", methods=["GET"])
def view_billing(patient_id: int):
    ok, err = require_login_and_csrf(
        allowed_roles=["Admin", "Pharmacy", "Staff", "Patient"]
    )
    if not ok:
        msg, code = err
        return jsonify({"ok": False, "error": msg}), code

    # If I'm a Patient, I can only see my own bills.
    if session["role"] == "Patient" and session["user_id"] != patient_id:
        return jsonify({"ok": False, "error": "Forbidden"}), 403

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id,
               patient_id,
               amount,
               status,
               description,
               created_at
          FROM billing
         WHERE patient_id = ?
         ORDER BY created_at DESC;
        """,
        (patient_id,)
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    return jsonify({"ok": True, "billing": rows}), 200


# ------------------------------------------------------------------
# NOTIFICATIONS
# User can only fetch their own notifications.
# ------------------------------------------------------------------

@api_bp.route("/notifications", methods=["GET"])
def my_notifications():
    ok, err = require_login_and_csrf(
        allowed_roles=["Admin", "Staff", "Doctor", "Pharmacy", "Patient"]
    )
    if not ok:
        msg, code = err
        return jsonify({"ok": False, "error": msg}), code

    uid = session["user_id"]

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id,
               message,
               is_read,
               created_at
          FROM notifications
         WHERE user_id = ?
         ORDER BY created_at DESC;
        """,
        (uid,)
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    return jsonify({"ok": True, "notifications": rows}), 200
