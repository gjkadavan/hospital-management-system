import secrets
import hmac
import time
from flask import session, request

# ------------------------
# CSRF handling
# ------------------------

def generate_csrf_token() -> str:
    """
    Ensure there's a CSRF token in the session and return it.
    """
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


def validate_csrf_token(client_token: str) -> bool:
    """
    Constant-time compare of provided token vs session token.
    Also adds a simple timestamp check to reduce token reuse risk.
    """
    expected = session.get("csrf_token", "")
    if not expected or not client_token:
        return False

    # constant-time compare
    if not hmac.compare_digest(expected, client_token):
        return False

    # Basic freshness check (optional hardening)
    # We allow ~2 hours reuse. Store timestamp when we generated token.
    now = int(time.time())
    if "csrf_ts" not in session:
        session["csrf_ts"] = now
    # if older than 2 hours, rotate and reject
    if now - session["csrf_ts"] > 7200:
        session["csrf_token"] = secrets.token_hex(32)
        session["csrf_ts"] = now
        return False

    return True


# ------------------------
# Session / RBAC helpers
# ------------------------

def create_session_user(user_id: int, role: str):
    """
    Save the authenticated user in the server-side session.
    """
    session["user_id"] = user_id
    session["role"] = role
    # rotate CSRF on login
    session["csrf_token"] = secrets.token_hex(32)
    session["csrf_ts"] = int(time.time())


def logout_user():
    """
    Clear session information.
    """
    session.clear()


def require_login() -> bool:
    """
    True if session has a logged-in user.
    """
    return "user_id" in session and "role" in session


def require_role(allowed_roles):
    """
    Check that current user has one of the allowed roles.
    allowed_roles is a list like ["Admin", "Doctor"].
    """
    if not require_login():
        return False
    user_role = session.get("role")
    return user_role in allowed_roles


def require_login_and_csrf(allowed_roles=None):
    """
    Unified gatekeeper for protected routes.

    Returns (True, None) if access allowed, OR
    (False, ("Message", http_status_code)) if blocked.

    Enforces:
    - Logged-in user
    - RBAC (if allowed_roles provided)
    - CSRF for mutating methods
    """
    # Must be logged in
    if not require_login():
        return (False, ("Unauthorized", 401))

    # Must have required role(s) if specified
    if allowed_roles and not require_role(allowed_roles):
        return (False, ("Forbidden", 403))

    # Enforce CSRF only on mutating verbs
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        client_token = request.headers.get("X-CSRF-Token", "")
        if not validate_csrf_token(client_token):
            return (False, ("Invalid or missing CSRF token", 403))

    return (True, None)
