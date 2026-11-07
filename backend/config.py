"""
TaskFlow Configuration Module
-----------------------------
Loads configuration settings from environment variables with safe defaults.
Supports .env files via python-dotenv for local development without committing secrets.
Configured for production cloud deployment (Render, Railway) and local execution.
"""

import os
from pathlib import Path

# Base directory paths
BACKEND_DIR = Path(__file__).resolve().parent
BASE_DIR = BACKEND_DIR.parent
DATABASE_DIR = BASE_DIR / 'database'

# Attempt to load .env file from the project root if present
try:
    from dotenv import load_dotenv
    env_file = BASE_DIR / '.env'
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass

# Determine database path from environment or default location
_env_db_path = os.environ.get('DATABASE_PATH')
if _env_db_path:
    DATABASE_PATH = Path(_env_db_path)
    if not DATABASE_PATH.is_absolute():
        DATABASE_PATH = BASE_DIR / DATABASE_PATH
else:
    DATABASE_PATH = DATABASE_DIR / 'taskflow.db'


class Config:
    """Base application configuration with production-ready security defaults."""
    # Cryptographic secret key for signing sessions and Bearer auth tokens
    SECRET_KEY = os.environ.get('SECRET_KEY', 'taskflow-dev-secret-key-2026')

    # Debug mode (defaults to False for production; set FLASK_DEBUG=True in .env for local development)
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')

    # Server binding & Cloud port (Render injects PORT, e.g. 10000)
    HOST = os.environ.get('FLASK_HOST', os.environ.get('HOST', '0.0.0.0'))
    PORT = int(os.environ.get('PORT', os.environ.get('FLASK_PORT', 5000)))

    # SQLite database file path
    DATABASE = str(DATABASE_PATH)

    # Cross-Origin Resource Sharing (CORS) origins
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')

    # Session cookie security settings (protects against XSS and CSRF)
    SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY', 'True').lower() in ('true', '1', 't')
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1', 't')
