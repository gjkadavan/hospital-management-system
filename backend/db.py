import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash
from flask import current_app

# ---- helpers -------------------------------------------------

def _now_iso() -> str:
    """UTC timestamp for audit fields."""
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def get_db() -> sqlite3.Connection:
    """
    Create a new sqlite3 connection.
    - Enforce foreign keys.
    - Row factory returns dict-like rows.
    We DO NOT store this globally; each call gets a fresh connection.
    """
    app = current_app if current_app else None
    db_path = None
    if app and app.config.get("DB_PATH"):
        db_path = app.config["DB_PATH"]

    # Fallback if somehow called before app init
    if not db_path:
        from .config import Config
        db_path = Config.DB_PATH

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(seed_demo_users: bool = True):
    """
    Create tables if missing.
    Optionally seed demo users for local/demo/testing usage.
    Safe to call multiple times.
    """

    conn = get_db()
    cur = conn.cursor()

    # USERS (RBAC)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN (
                'Admin','Doctor','Staff','Pharmacy','Patient'
            )),
            full_name TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    """)

    # PATIENTS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            dob TEXT NOT NULL,                 -- YYYY-MM-DD
            phone TEXT NOT NULL,
            medical_history TEXT DEFAULT '',
            owner_user_id INTEGER,             -- link to users.id if this patient can log in
            created_at TEXT NOT NULL,
            FOREIGN KEY(owner_user_id) REFERENCES users(id)
                ON DELETE SET NULL
        );
    """)

    # APPOINTMENTS
    # Prevent double booking: (doctor_id,start_time) UNIQUE.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            start_time TEXT NOT NULL,          -- "YYYY-MM-DD HH:MM"
            reason TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT 'scheduled'
                CHECK(status IN ('scheduled','completed','canceled')),
            created_at TEXT NOT NULL,
            UNIQUE(doctor_id, start_time),
            FOREIGN KEY(patient_id) REFERENCES patients(id)
                ON DELETE CASCADE,
            FOREIGN KEY(doctor_id) REFERENCES users(id)
                ON DELETE CASCADE
        );
    """)

    # PRESCRIPTIONS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            patient_id INTEGER NOT NULL,
            medication TEXT NOT NULL,
            instructions TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(appointment_id) REFERENCES appointments(id)
                ON DELETE CASCADE,
            FOREIGN KEY(patient_id) REFERENCES patients(id)
                ON DELETE CASCADE,
            FOREIGN KEY(doctor_id) REFERENCES users(id)
                ON DELETE CASCADE
        );
    """)

    # BILLING
    cur.execute("""
        CREATE TABLE IF NOT EXISTS billing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'unpaid'
                CHECK(status IN ('unpaid','paid','void')),
            description TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY(patient_id) REFERENCES patients(id)
                ON DELETE CASCADE
        );
    """)

    # NOTIFICATIONS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
                ON DELETE CASCADE
        );
    """)

    # Seed demo users for convenience
    if seed_demo_users:
        demo_users = [
            ("admin",     "admin123",   "Admin",    "System Admin"),
            ("drsmith",   "doctor123",  "Doctor",   "Dr. John Smith"),
            ("reception", "staff123",   "Staff",    "Front Desk Staff"),
            ("pharma",    "pharma123",  "Pharmacy", "Pharmacy Staff"),
            ("alice",     "patient123", "Patient",  "Alice Patient"),
        ]
        for username, pw_plain, role, full_name in demo_users:
            cur.execute("SELECT id FROM users WHERE username = ?;", (username,))
            row = cur.fetchone()
            if not row:
                cur.execute("""
                    INSERT INTO users (
                        username, password_hash, role, full_name, created_at
                    )
                    VALUES (?, ?, ?, ?, ?);
                """, (
                    username,
                    generate_password_hash(pw_plain),
                    role,
                    full_name,
                    _now_iso()
                ))

    conn.commit()
    conn.close()
