from pathlib import Path
from flask import Flask, send_from_directory, session
from flask_cors import CORS
from .config import Config, TestingConfig
from .db import init_db
from .routes.auth import auth_bp
from .routes.api import api_bp

# Resolve absolute paths so this works no matter where you launch python -m backend.app
BASE_DIR = Path(__file__).resolve().parent.parent  # points to project root (Hospital Management)
FRONTEND_TEMPLATES = BASE_DIR / "frontend" / "templates"
FRONTEND_STATIC = BASE_DIR / "frontend" / "static"


def create_app(testing: bool = False) -> Flask:
    """
    Flask application factory.
    If testing=True, use TestingConfig (in-memory DB).
    Otherwise use Config (file-based DB).
    """
    app = Flask(
        __name__,
        static_folder=str(FRONTEND_STATIC),     # serve /static/* from frontend/static
        static_url_path="/static"
    )

    # Load config
    if testing:
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(Config)

    # CORS: allow frontend pages (same origin) to call /api with cookies
    CORS(
        app,
        supports_credentials=True,
        resources={r"/api/*": {"origins": [
            "http://localhost:5000",
            "http://127.0.0.1:5000",
        ]}},
    )

    # Blueprints for API routes
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    # ---- Static page routes (HTML files in frontend/templates/) ----

    @app.route("/")
    def root_index():
        # serve login page
        return send_from_directory(str(FRONTEND_TEMPLATES), "index.html")

    @app.route("/<path:path>")
    def serve_page(path: str):
        """
        This lets you hit /dashboard.html, /patients.html, etc.
        We FIRST try templates (actual pages).
        If the file doesn't exist there, we fall back to static (images, etc.).
        """
        page_path = FRONTEND_TEMPLATES / path
        if page_path.exists():
            return send_from_directory(str(FRONTEND_TEMPLATES), path)

        asset_path = FRONTEND_STATIC / path
        if asset_path.exists():
            # e.g. someone directly navigates to /static/js/api.js
            # This is usually covered by app.static_folder, but keep fallback.
            return send_from_directory(str(FRONTEND_STATIC), path)

        # If we get here, it's not found
        return ("Not found", 404)

    # Harden session on every request
    @app.before_request
    def secure_session_flags():
        session.permanent = False  # expire when browser closes

    return app


if __name__ == "__main__":
    flask_app = create_app(testing=False)

    # init DB + seed demo users
    with flask_app.app_context():
        init_db(seed_demo_users=True)

    # run server
    flask_app.run(host="0.0.0.0", port=5000, debug=flask_app.config["DEBUG"])
