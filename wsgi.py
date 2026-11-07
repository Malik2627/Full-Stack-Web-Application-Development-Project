"""
TaskFlow Production WSGI Entry Point
-------------------------------------
Used by production WSGI application servers (e.g. Gunicorn, uWSGI) to serve TaskFlow.
Compatible with cloud platforms such as Render, Railway, and Heroku.

Production Start Command:
    gunicorn wsgi:app
or
    gunicorn --bind 0.0.0.0:$PORT wsgi:app
"""

import sys
from pathlib import Path

# Ensure the backend directory is in the Python search path
project_root = Path(__file__).resolve().parent
backend_dir = project_root / 'backend'
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run()

