import sys
from pathlib import Path

# Ensure the backend directory is in the Python module search path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from database import init_db
from routes import api_bp


def create_app(config_class=Config):
    """Application factory for TaskFlow backend."""
    frontend_dir = Path(__file__).resolve().parent.parent / 'frontend'
    app = Flask(
        __name__,
        static_folder=str(frontend_dir),
        static_url_path=''
    )
    app.config.from_object(config_class)

    # Enable Cross-Origin Resource Sharing (CORS) with credentials support
    cors_origins = app.config.get('CORS_ORIGINS', '*')
    if isinstance(cors_origins, str) and cors_origins != '*' and ',' in cors_origins:
        cors_origins = [o.strip() for o in cors_origins.split(',') if o.strip()]

    CORS(
        app,
        resources={r"/api/*": {"origins": cors_origins}},
        supports_credentials=True
    )

    # Initialize database directory / file
    with app.app_context():
        init_db()

    # Register blueprints
    app.register_blueprint(api_bp)

    # ========================================================================
    # STEP 10: APPLICATION ERROR HANDLING & USER EXPERIENCE
    # Centralized handlers returning user-friendly messages for standard HTTP codes
    # Strictly suppresses Python tracebacks, internal details, and SQL errors
    # ========================================================================

    @app.errorhandler(400)
    def handle_bad_request(e):
        msg = "Bad request. Please verify the submitted data."
        if hasattr(e, 'description') and e.description and not str(e.description).startswith("400"):
            msg = e.description
        return jsonify({"status": "error", "message": msg}), 400

    @app.errorhandler(401)
    def handle_unauthorized(e):
        msg = "Authentication required. Please log in."
        if hasattr(e, 'description') and e.description and not str(e.description).startswith("401"):
            msg = e.description
        return jsonify({"status": "error", "message": msg}), 401

    @app.errorhandler(403)
    def handle_forbidden(e):
        msg = "Access forbidden. You do not have permission to access this resource."
        if hasattr(e, 'description') and e.description and not str(e.description).startswith("403"):
            msg = e.description
        return jsonify({"status": "error", "message": msg}), 403

    @app.errorhandler(404)
    def handle_not_found(e):
        msg = "Resource or endpoint not found."
        if hasattr(e, 'description') and e.description and not str(e.description).startswith("404"):
            msg = e.description
        return jsonify({"status": "error", "message": msg}), 404

    @app.errorhandler(409)
    def handle_conflict(e):
        msg = "A resource conflict occurred. The submitted item may already exist."
        if hasattr(e, 'description') and e.description and not str(e.description).startswith("409"):
            msg = e.description
        return jsonify({"status": "error", "message": msg}), 409

    @app.errorhandler(500)
    def handle_internal_error(e):
        return jsonify({
            "status": "error",
            "message": "An internal server error occurred. Please try again later."
        }), 500

    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        # Suppress stack trace completely from client output
        return jsonify({
            "status": "error",
            "message": "An unexpected server error occurred. Please try again later."
        }), 500

    @app.route('/api/test-server-error', methods=['GET'])
    def test_server_error_route():
        """Route to test that 500 errors return friendly JSON without tracebacks."""
        raise RuntimeError("Simulated internal server exception for Step 10 verification")

    @app.route('/', methods=['GET'])
    def root():
        """Root API check and browser landing page entry point."""
        from flask import request
        if request.accept_mimetypes.accept_html and not request.accept_mimetypes.accept_json:
            return app.send_static_file('index.html')
        return jsonify({
            "name": "TaskFlow — Student Task Management System API",
            "version": "1.0.0",
            "status": "online",
            "endpoints": {
                "health": "/api/health",
                "db_status": "/api/db/status",
                "tasks": "/api/tasks",
                "categories": "/api/categories",
                "users": "/api/users"
            }
        }), 200

    return app


app = create_app()

if __name__ == '__main__':
    print(f"TaskFlow Backend is starting at http://{Config.HOST}:{Config.PORT}")
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )

