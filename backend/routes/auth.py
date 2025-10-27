from flask import Blueprint, request, jsonify, session
from werkzeug.security import check_password_hash
from ..db import get_db
from ..security import (
    create_session_user,
    logout_user,
    generate_csrf_token,
    require_login_and_csrf,
)

auth_bp = Blueprint("auth_bp", __name__, url_prefix="/api/auth")


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    POST /api/auth/login
    Body: { "username": "...", "password": "..." }
    If valid, store user_id + role in session and return csrf_token.
    """
    data = request.json or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if not username or not password:
        return jsonify({"ok": False, "error": "Username and password required"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, password_hash, role FROM users WHERE username = ?;",
        (username,)
    )
    row = cur.fetchone()
    conn.close()

    if (not row) or (not check_password_hash(row["password_hash"], password)):
        return jsonify({"ok": False, "error": "Invalid credentials"}), 401

    create_session_user(row["id"], row["role"])

    return jsonify({
        "ok": True,
        "user": {
            "id": row["id"],
            "role": row["role"]
        },
        "csrf_token": generate_csrf_token()
    }), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    POST /api/auth/logout
    State-changing -> must require login, role check (any role),
    and CSRF.
    """
    ok, err = require_login_and_csrf(
        allowed_roles=["Admin", "Doctor", "Staff", "Pharmacy", "Patient"]
    )
    if not ok:
        msg, code = err
        return jsonify({"ok": False, "error": msg}), code

    logout_user()
    return jsonify({"ok": True}), 200


@auth_bp.route("/me", methods=["GET"])
def me():
    """
    GET /api/auth/me
    Returns current session user info + csrf token.
    Does NOT require CSRF (read-only), but does require login.
    """
    if "user_id" not in session or "role" not in session:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    return jsonify({
        "ok": True,
        "user": {
            "id": session["user_id"],
            "role": session["role"]
        },
        "csrf_token": generate_csrf_token()
    }), 200


@auth_bp.route("/csrf-token", methods=["GET"])
def csrf_token():
    """
    GET /api/auth/csrf-token
    Returns (and sets if missing) the CSRF token for this session.
    """
    if "user_id" not in session:
        # still return a token, but this user isn't authenticated;
        # state-changing routes will still reject them.
        token = generate_csrf_token()
        return jsonify({"ok": True, "csrf_token": token}), 200

    token = generate_csrf_token()
    return jsonify({"ok": True, "csrf_token": token}), 200
