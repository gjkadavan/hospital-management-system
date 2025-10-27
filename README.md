# 🏥 Hospital Management System (HMS)

A **role-based hospital management system** built using **Flask (Python)** and **SQLite**, featuring secure authentication, role-based access control, patient record management, appointments, prescriptions, billing, pharmacy inventory, and notifications.

---

## 🚀 Features

### 🔐 Authentication & Sessions
- Secure login for Admin, Staff, Doctor, Pharmacy, and Patient.
- Passwords hashed with `werkzeug.security`.
- Sessions stored server-side (Flask session cookies).
- CSRF tokens validated for all state-changing routes (POST, PUT, DELETE).

### 👥 Roles & Permissions
| Role | Permissions |
|------|--------------|
| **Admin** | Full access to all modules. |
| **Doctor** | View patients, create prescriptions. |
| **Staff** | Register patients, schedule appointments. |
| **Pharmacy** | Manage drug stock, create billing entries. |
| **Patient** | View their own records, prescriptions, billing. |

### 📅 Appointment Scheduling
- Prevents double-booking for doctors (unique timeslot constraint).
- Supports notes and automatic status updates.

### 💊 Pharmacy & Billing
- Pharmacy stock view with reorder alerts.
- Only Pharmacy/Admin can create invoices.
- Billing tied to patients; restricted view by role.

### 🩺 Patient Records
- Doctors can create prescriptions for patients.
- Admins can view all; patients see only their own.

### 🧾 Notifications
- Schedule reminders for appointments or follow-ups.
- View pending/sent notifications.

---

## 🏗️ Project Structure

Hospital Management/
├── backend/
│ ├── init.py
│ ├── app.py
│ ├── api.py
│ ├── db.py
│ ├── config.py
│ └── requirements.txt
├── frontend/
│ ├── templates/
│ │ ├── index.html
│ │ ├── dashboard.html
│ │ ├── patients.html
│ │ ├── appointments.html
│ │ ├── records.html
│ │ ├── billing.html
│ │ ├── pharmacy.html
│ │ ├── notifications.html
│ │ └── staff.html
│ └── static/
│ ├── css/style.css
│ ├── js/api.js
│ ├── js/auth.js
│ ├── js/utils.js
│ └── img/
├── tests/
│ ├── conftest.py
│ ├── test_auth.py
│ ├── test_appointments.py
│ ├── test_patients.py
│ └── test_billing.py
├── docs/
│ ├── architecture_diagram.png
│ ├── er_diagram.png
│ ├── risk_matrix.md
│ └── cocomo_estimate.md
├── .github/workflows/ci.yml
├── .gitignore
├── run_local.sh
└── README.md

yaml
Copy code

---

## ⚙️ Installation & Setup

### 
1️⃣ Clone the Repository
```bash
git clone https://github.com/<your-username>/hospital-management.git
cd hospital-management

2️⃣ Create and Activate Virtual Environment
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

3️⃣ Install Dependencies
pip install -r backend/requirements.txt

4️⃣ Initialize Database
cd backend
python db.py
This creates hospital.db (SQLite) with all required tables and default demo users:

admin / admin123

drsmith / doctor123

reception / staff123

pharma / pharmacy123

john / patient123

5️⃣ Run Locally
bash run_local.sh
# or manually:
python -m backend.app
The app runs at http://127.0.0.1:5000

🧪 Running Tests (CI/CD)
Local Test Run
pytest -v


GitHub Actions CI
The workflow file .github/workflows/ci.yml automatically:

Sets up Python 3.10+

Installs dependencies

Runs all tests

Fails the build if any test fails

🛡️ Security Design
CSRF protection on all modifying routes (require_login_and_csrf decorator).

Role-based access check before database operations.

No direct SQL — all queries use parameterized SQLite via cursor.execute(?, …).

Session cookie is HTTP-only and server-managed.

Passwords are hashed using generate_password_hash (never plaintext).

📘 API Endpoints Overview
Endpoint	Method	Role	Description
/api/auth/login	POST	All	Login user
/api/auth/logout	POST	All	Logout current session
/api/patients	GET/POST	Staff/Admin	Manage patients
/api/appointments	GET/POST	Staff/Doctor/Admin	Manage appointments
/api/prescriptions	POST	Doctor	Create prescription
/api/prescriptions/<patient_id>	GET	Doctor/Admin/Pharmacy/Patient	View prescriptions
/api/pharmacy	GET/POST	Pharmacy/Admin	Manage stock
/api/billing	POST	Pharmacy/Admin	Create invoice
/api/billing/<patient_id>	GET	Authenticated	View patient billing
/api/notifications	GET/POST	Staff/Admin	Manage notifications

🧭 Demo Login Roles
Username	Password	Role
admin	admin123	Admin
drsmith	doctor123	Doctor
reception	staff123	Staff
pharma	pharmacy123	Pharmacy
john	patient123	Patient

🧰 Tech Stack
Layer	Technology
Backend	Flask, SQLite3
Frontend	HTML, CSS, JS (Vanilla)
Auth	Flask Session + CSRF Tokens
Testing	Pytest
CI/CD	GitHub Actions
Deployment	Local / Render / Railway (optional)

📚 Documentation
Additional documents in /docs/:

architecture_diagram.png — component-level system architecture.

er_diagram.png — database schema diagram.

risk_matrix.md — project risk evaluation.

cocomo_estimate.md — effort estimation model.