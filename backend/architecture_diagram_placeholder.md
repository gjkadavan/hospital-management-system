# Architecture & ERD (Placeholder for Report)

## Architecture
- Frontend: Static HTML/JS served by Flask (`/` and `/dashboard.html`, etc.)
- Backend: Flask API blueprints under `/api/...`
- Auth: Server-side session cookie + role in session + CSRF token
- DB: SQLite (tables below)
- Tests: pytest (unit + integration) + selenium (UI flow)
- CI: GitHub Actions runs pytest

## ERD (text form)
- users(id, username, password_hash, role)
  - role ∈ {admin, doctor, staff, pharmacy}
- patients(id, first_name, last_name, dob, phone, medical_history)
- appointments(id, patient_id → patients.id,
               doctor_id → users.id,
               appt_datetime,
               status,
               notes)
- billing(id, patient_id → patients.id,
          amount,
          status,
          description,
          created_at)
- pharmacy_orders(id, patient_id → patients.id,
                  drug_name,
                  quantity,
                  status,
                  prescribed_by → users.id,
                  created_at)
- medical_records(id, patient_id → patients.id,
                  record_text,
                  created_at,
                  created_by → users.id)
- notifications(id, message, level, created_at)
