import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    """
    Base configuration.
    NOTE:
    - SECRET_KEY MUST be provided via env in production.
    - DB_PATH is path to SQLite file. For grading/demo: backend/hms.db
    """

    # Secret key for session signing
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-key-change-me")

    # Database location (file-based for normal run)
    DB_PATH = os.environ.get("DB_PATH", str(BASE_DIR / "hms.db"))

    # CORS / cookies / sessions
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Strict"
    # In production over HTTPS set SESSION_COOKIE_SECURE=True via env
    SESSION_COOKIE_SECURE = (
        os.environ.get("SESSION_COOKIE_SECURE", "False").lower() == "true"
    )

    # Flags
    TESTING = os.environ.get("TESTING", "False").lower() == "true"
    DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

    # Token lifetime placeholder
    ACCESS_TOKEN_EXP_MIN = int(os.environ.get("ACCESS_TOKEN_EXP_MIN", "60"))


class TestingConfig(Config):
    """
    Overrides for pytest.
    Uses in-memory SQLite per test session.
    """
    TESTING = True
    DEBUG = False
    # In-memory DB so tests don't share state with real data
    DB_PATH = ":memory:"
    # For tests it's fine to run without secure cookies
    SESSION_COOKIE_SECURE = False
