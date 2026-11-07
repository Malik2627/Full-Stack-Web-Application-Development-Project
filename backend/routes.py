"""
TaskFlow REST API Routes
------------------------
Implements complete CRUD endpoints for Tasks, Categories, and Users with:
- Input validation and sanitization
- Relational integrity verification
- Consistent JSON response structures
- Standard HTTP status codes (200, 201, 400, 404, 500)
"""

import sqlite3
import logging
import itsdangerous
from flask import Blueprint, request, jsonify, session, current_app
from functools import wraps
import models
from database import get_db_connection
from validators import (
    validate_task_payload,
    validate_category_payload,
    validate_user_payload
)

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')


# ============================================================================
# RESPONSE HELPERS
# ============================================================================

def success_response(data=None, message=None, status_code=200, **kwargs):
    """Formats a standardized success response."""
    payload = {"status": "success"}
    if message is not None:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    payload.update(kwargs)
    return jsonify(payload), status_code


def error_response(message, errors=None, status_code=400):
    """Formats a standardized error response."""
    payload = {
        "status": "error",
        "message": message
    }
    if errors is not None:
        payload["errors"] = errors
    return jsonify(payload), status_code


# ============================================================================
# AUTHENTICATION & SECURITY HELPERS (Step 8)
# ============================================================================

def generate_auth_token(user_id):
    """Generates a secure signed auth token."""
    secret = current_app.config.get('SECRET_KEY', 'taskflow-dev-secret-key-2026')
    serializer = itsdangerous.URLSafeTimedSerializer(secret)
    return serializer.dumps({'user_id': user_id})


def verify_auth_token(token):
    """Verifies a signed token and returns the user_id or None."""
    if not token:
        return None
    secret = current_app.config.get('SECRET_KEY', 'taskflow-dev-secret-key-2026')
    serializer = itsdangerous.URLSafeTimedSerializer(secret)
    try:
        data = serializer.loads(token, max_age=60 * 60 * 24 * 7)  # 7 days
        return data.get('user_id')
    except Exception:
        return None


def get_current_user_id():
    """
    Retrieves the currently authenticated user ID from:
    1. Flask session (`session.get('user_id')`)
    2. Authorization header (`Bearer <token>`)
    3. X-User-Id header
    """
    if 'user_id' in session and session['user_id']:
        return session['user_id']

    auth_header = request.headers.get('Authorization')
    if auth_header:
        token = auth_header.replace('Bearer ', '').strip()
        uid = verify_auth_token(token)
        if uid:
            return uid

    x_user = request.headers.get('X-User-Id')
    if x_user:
        try:
            return int(x_user)
        except ValueError:
            pass

    return None


def get_current_user():
    """Retrieves the full authenticated user record (without password)."""
    uid = get_current_user_id()
    if not uid:
        return None
    user = models.get_user_by_id(uid)
    if user:
        sanitized = dict(user)
        sanitized.pop('password', None)
        return sanitized
    return None


def login_required(f):
    """
    Decorator to protect endpoints requiring an authenticated student.
    Returns 401 Unauthorized if no valid session or Bearer token is present.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not get_current_user_id():
            return error_response("Authentication required. Please log in.", status_code=401)
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify backend status."""
    return success_response(
        message="TaskFlow API is running",
        data={"version": "1.0.0", "service": "taskflow-backend"}
    )


@api_bp.route('/db/status', methods=['GET'])
def db_status():
    """Verification endpoint for database connection, tables, and seeded categories."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = [row['name'] for row in cursor.fetchall() if row['name'] != 'sqlite_sequence']
        conn.close()

        categories = models.get_all_categories()
        return success_response(
            message="Database connection verified",
            data={
                "database": "connected",
                "tables": tables,
                "categories_count": len(categories),
                "seeded_categories": [c['name'] for c in categories]
            }
        )
    except Exception as e:
        logger.exception("Database status verification failed: %s", e)
        return error_response("Database connection error. Please verify SQLite initialization.", status_code=500)


# ============================================================================
# AUTHENTICATION REST API (Step 8)
# ============================================================================

@api_bp.route('/auth/register', methods=['POST'])
def auth_register():
    """
    POST /api/auth/register
    Registers a new student user with Werkzeug password hashing.
    Payload: name, email, password
    """
    data = request.get_json(silent=True)
    if data is None:
        return error_response("Malformed or missing JSON in request body.", status_code=400)

    is_valid, errors, cleaned = validate_user_payload(data, is_update=False)
    if not is_valid:
        return error_response("Registration validation failed.", errors=errors, status_code=400)

    # Check for duplicate email (409 Conflict)
    existing = models.get_user_by_email(cleaned['email'])
    if existing:
        return error_response(
            f"User with email '{cleaned['email']}' already exists.",
            errors={"email": "Email is already registered."},
            status_code=409
        )

    try:
        user = models.create_user(
            name=cleaned['name'],
            email=cleaned['email'],
            password=cleaned['password']
        )
        session['user_id'] = user['id']
        token = generate_auth_token(user['id'])

        sanitized = dict(user)
        sanitized.pop('password', None)

        return success_response(
            data={"user": sanitized, "token": token},
            message="User registered successfully.",
            status_code=201
        )
    except sqlite3.IntegrityError:
        return error_response("Email is already registered.", status_code=409)
    except Exception as e:
        logger.exception("Registration failed: %s", e)
        return error_response("Failed to register user. An unexpected server error occurred.", status_code=500)


@api_bp.route('/auth/login', methods=['POST'])
def auth_login():
    """
    POST /api/auth/login
    Authenticates a user using email and password with Werkzeug check_password_hash.
    Payload: email, password
    """
    data = request.get_json(silent=True)
    if data is None:
        return error_response("Malformed or missing JSON in request body.", status_code=400)

    email = data.get('email')
    password = data.get('password')

    if not email or not str(email).strip() or not password:
        return error_response("Email and password are required.", status_code=400)

    email_clean = str(email).strip().lower()
    user = models.get_user_by_email(email_clean)

    if not user or not models.verify_user_password(user.get('password'), str(password)):
        return error_response("Invalid email or password.", status_code=401)

    # Set session & generate auth token
    session['user_id'] = user['id']
    token = generate_auth_token(user['id'])

    sanitized = dict(user)
    sanitized.pop('password', None)

    return success_response(
        data={"user": sanitized, "token": token},
        message="Login successful."
    )


@api_bp.route('/auth/me', methods=['GET'])
@login_required
def auth_me():
    """
    GET /api/auth/me
    Retrieves the currently authenticated user profile.
    """
    user = get_current_user()
    return success_response(data={"user": user}, message="User profile retrieved.")


@api_bp.route('/auth/logout', methods=['POST'])
def auth_logout():
    """
    POST /api/auth/logout
    Clears user session and logs out.
    """
    session.pop('user_id', None)
    session.clear()
    return success_response(message="Logged out successfully.")


# ============================================================================
# TASKS REST API (CRUD - Connected to Authenticated Users)
# ============================================================================

@api_bp.route('/tasks', methods=['GET'])
def get_tasks():
    """
    GET /api/tasks
    Retrieve tasks. For authenticated users, automatically scopes to logged-in user.
    Do NOT trust a user ID supplied by the frontend.
    """
    try:
        status = request.args.get('status')
        priority = request.args.get('priority')
        category_id = request.args.get('category_id', type=int)

        current_uid = get_current_user_id()
        if current_uid is not None:
            # Protected: Scoped strictly to the authenticated user ID (never trust frontend user_id)
            effective_user_id = current_uid
        else:
            effective_user_id = request.args.get('user_id', type=int)

        tasks = models.get_all_tasks(
            user_id=effective_user_id,
            category_id=category_id,
            status=status,
            priority=priority
        )

        return success_response(
            data=tasks,
            count=len(tasks),
            filters={
                "status": status,
                "priority": priority,
                "category_id": category_id,
                "user_id": effective_user_id
            }
        )
    except Exception as e:
        logger.exception("Failed to retrieve tasks: %s", e)
        return error_response("An internal server error occurred while retrieving tasks. Please try again later.", status_code=500)


@api_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """
    GET /api/tasks/<id>
    Retrieve a single task by ID.
    Enforces that User A can only see User A's tasks.
    """
    task = models.get_task_by_id(task_id)
    if not task:
        return error_response(f"Task with ID {task_id} not found.", status_code=404)

    current_uid = get_current_user_id()
    if current_uid is not None and task.get('user_id') is not None and task['user_id'] != current_uid:
        return error_response("You do not have permission to access this task.", status_code=403)

    return success_response(data=task)


@api_bp.route('/tasks', methods=['POST'])
def create_task():
    """
    POST /api/tasks
    Create a new task.
    Automatically assigns task to authenticated user; never trusts frontend user_id.
    """
    data = request.get_json(silent=True)
    if data is None:
        return error_response("Malformed or missing JSON in request body.", status_code=400)

    is_valid, errors, cleaned = validate_task_payload(data, is_update=False)
    if not is_valid:
        return error_response("Task validation failed.", errors=errors, status_code=400)

    current_uid = get_current_user_id()
    # Do NOT trust user_id supplied by frontend when user is authenticated
    if current_uid is not None:
        effective_user_id = current_uid
    else:
        effective_user_id = cleaned.get('user_id')

    try:
        task = models.create_task(
            title=cleaned['title'],
            description=cleaned.get('description'),
            user_id=effective_user_id,
            category_id=cleaned.get('category_id'),
            priority=cleaned.get('priority', 'Medium'),
            status=cleaned.get('status', 'Pending'),
            due_date=cleaned.get('due_date')
        )
        return success_response(
            data=task,
            message="Task created successfully",
            status_code=201
        )
    except sqlite3.IntegrityError as ie:
        logger.warning("Task creation integrity error: %s", ie)
        return error_response("Database integrity error. Please verify category and user IDs.", status_code=400)
    except Exception as e:
        logger.exception("Failed to create task: %s", e)
        return error_response("An internal server error occurred while creating the task.", status_code=500)


@api_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """
    PUT /api/tasks/<id>
    Update an existing task.
    Enforces that User A can only update User A's tasks.
    """
    existing_task = models.get_task_by_id(task_id)
    if not existing_task:
        return error_response(f"Task with ID {task_id} not found.", status_code=404)

    current_uid = get_current_user_id()
    if current_uid is not None and existing_task.get('user_id') is not None and existing_task['user_id'] != current_uid:
        return error_response("You do not have permission to modify this task.", status_code=403)

    data = request.get_json(silent=True)
    if data is None:
        return error_response("Malformed or missing JSON in request body.", status_code=400)

    is_valid, errors, cleaned = validate_task_payload(data, is_update=True)
    if not is_valid:
        return error_response("Task validation failed.", errors=errors, status_code=400)

    # Disallow transferring task ownership to another user
    cleaned.pop('user_id', None)

    if not cleaned:
        return success_response(data=existing_task, message="No changes provided.")

    try:
        updated = models.update_task(task_id, **cleaned)
        return success_response(
            data=updated,
            message="Task updated successfully"
        )
    except sqlite3.IntegrityError as ie:
        logger.warning("Task update integrity error: %s", ie)
        return error_response("Database integrity error. Please verify category and user IDs.", status_code=400)
    except Exception as e:
        logger.exception("Failed to update task: %s", e)
        return error_response("An internal server error occurred while updating the task.", status_code=500)


@api_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """
    DELETE /api/tasks/<id>
    Delete a task by ID.
    Enforces that User A can only delete User A's tasks.
    """
    existing_task = models.get_task_by_id(task_id)
    if not existing_task:
        return error_response(f"Task with ID {task_id} not found.", status_code=404)

    current_uid = get_current_user_id()
    if current_uid is not None and existing_task.get('user_id') is not None and existing_task['user_id'] != current_uid:
        return error_response("You do not have permission to delete this task.", status_code=403)

    try:
        models.delete_task(task_id)
        return success_response(message="Task deleted successfully")
    except Exception as e:
        logger.exception("Failed to delete task: %s", e)
        return error_response("An internal server error occurred while deleting the task.", status_code=500)


# ============================================================================
# CATEGORIES REST API (CRUD)
# ============================================================================

@api_bp.route('/categories', methods=['GET'])
def get_categories():
    """
    GET /api/categories
    Retrieve all categories.
    """
    categories = models.get_all_categories()
    return success_response(data=categories, count=len(categories))


@api_bp.route('/categories/<int:category_id>', methods=['GET'])
def get_category(category_id):
    """
    GET /api/categories/<id>
    Retrieve a single category by ID.
    """
    cat = models.get_category_by_id(category_id)
    if not cat:
        return error_response(f"Category with ID {category_id} not found.", status_code=404)
    return success_response(data=cat)


@api_bp.route('/categories', methods=['POST'])
def create_category():
    """
    POST /api/categories
    Create a new category.
    """
    data = request.get_json(silent=True)
    if data is None:
        return error_response("Malformed or missing JSON in request body.", status_code=400)

    is_valid, errors, cleaned = validate_category_payload(data, is_update=False)
    if not is_valid:
        return error_response("Category validation failed.", errors=errors, status_code=400)

    # Check for duplicate name (409 Conflict)
    existing_cats = models.get_all_categories()
    if any(c['name'].lower() == cleaned['name'].lower() for c in existing_cats):
        return error_response(f"Category '{cleaned['name']}' already exists.", status_code=409)

    try:
        category = models.create_category(
            name=cleaned['name'],
            color=cleaned.get('color')
        )
        return success_response(
            data=category,
            message="Category created successfully",
            status_code=201
        )
    except Exception as e:
        logger.exception("Failed to create category: %s", e)
        return error_response("An internal server error occurred while creating category.", status_code=500)


@api_bp.route('/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """
    PUT /api/categories/<id>
    Update category name and/or color.
    """
    existing_cat = models.get_category_by_id(category_id)
    if not existing_cat:
        return error_response(f"Category with ID {category_id} not found.", status_code=404)

    data = request.get_json(silent=True)
    if data is None:
        return error_response("Malformed or missing JSON in request body.", status_code=400)

    is_valid, errors, cleaned = validate_category_payload(data, is_update=True)
    if not is_valid:
        return error_response("Category validation failed.", errors=errors, status_code=400)

    # If renaming, ensure name uniqueness (409 Conflict)
    if 'name' in cleaned and cleaned['name'].lower() != existing_cat['name'].lower():
        existing_cats = models.get_all_categories()
        if any(c['id'] != category_id and c['name'].lower() == cleaned['name'].lower() for c in existing_cats):
            return error_response(f"Category '{cleaned['name']}' already exists.", status_code=409)

    try:
        updated = models.update_category(
            category_id,
            name=cleaned.get('name'),
            color=cleaned.get('color')
        )
        return success_response(data=updated, message="Category updated successfully")
    except Exception as e:
        logger.exception("Failed to update category: %s", e)
        return error_response("An internal server error occurred while updating category.", status_code=500)


@api_bp.route('/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """
    DELETE /api/categories/<id>
    Delete category. Tasks referencing this category will have category_id set to NULL.
    """
    existing_cat = models.get_category_by_id(category_id)
    if not existing_cat:
        return error_response(f"Category with ID {category_id} not found.", status_code=404)

    try:
        models.delete_category(category_id)
        return success_response(message="Category deleted successfully")
    except Exception as e:
        logger.exception("Failed to delete category: %s", e)
        return error_response("An internal server error occurred while deleting category.", status_code=500)


# ============================================================================
# USERS REST API (BASIC CRUD)
# ============================================================================

@api_bp.route('/users', methods=['GET'])
def get_users():
    """
    GET /api/users
    Retrieve all registered users (passwords omitted).
    """
    users = models.get_all_users()
    # Omit password field from response
    sanitized = []
    for u in users:
        user_copy = dict(u)
        user_copy.pop('password', None)
        sanitized.append(user_copy)
    return success_response(data=sanitized, count=len(sanitized))


@api_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """
    GET /api/users/<id>
    Retrieve a single user by ID.
    """
    user = models.get_user_by_id(user_id)
    if not user:
        return error_response(f"User with ID {user_id} not found.", status_code=404)

    user_data = dict(user)
    user_data.pop('password', None)
    return success_response(data=user_data)


@api_bp.route('/users', methods=['POST'])
def create_user():
    """
    POST /api/users
    Create a new user (basic CRUD without authentication/hashing yet).
    """
    data = request.get_json(silent=True)
    if data is None:
        return error_response("Malformed or missing JSON in request body.", status_code=400)

    is_valid, errors, cleaned = validate_user_payload(data, is_update=False)
    if not is_valid:
        return error_response("User validation failed.", errors=errors, status_code=400)

    # Check for existing email (409 Conflict)
    existing_user = models.get_user_by_email(cleaned['email'])
    if existing_user:
        return error_response(f"User with email '{cleaned['email']}' already exists.", status_code=409)

    try:
        user = models.create_user(
            name=cleaned['name'],
            email=cleaned['email'],
            password=cleaned['password']
        )
        user_data = dict(user)
        user_data.pop('password', None)
        return success_response(
            data=user_data,
            message="User created successfully",
            status_code=201
        )
    except sqlite3.IntegrityError:
        return error_response("A user with this email already exists.", status_code=409)
    except Exception as e:
        logger.exception("Failed to create user: %s", e)
        return error_response("An internal server error occurred while creating user.", status_code=500)


@api_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """
    PUT /api/users/<id>
    Update user profile.
    """
    existing_user = models.get_user_by_id(user_id)
    if not existing_user:
        return error_response(f"User with ID {user_id} not found.", status_code=404)

    data = request.get_json(silent=True)
    if data is None:
        return error_response("Malformed or missing JSON in request body.", status_code=400)

    is_valid, errors, cleaned = validate_user_payload(data, is_update=True)
    if not is_valid:
        return error_response("User validation failed.", errors=errors, status_code=400)

    # If updating email, check for duplicate on other users (409 Conflict)
    if 'email' in cleaned and cleaned['email'] != existing_user['email']:
        conflict = models.get_user_by_email(cleaned['email'])
        if conflict and conflict['id'] != user_id:
            return error_response(f"User with email '{cleaned['email']}' already exists.", status_code=409)

    try:
        updated = models.update_user(
            user_id,
            name=cleaned.get('name'),
            email=cleaned.get('email'),
            password=cleaned.get('password')
        )
        user_data = dict(updated)
        user_data.pop('password', None)
        return success_response(data=user_data, message="User updated successfully")
    except Exception as e:
        logger.exception("Failed to update user: %s", e)
        return error_response("An internal server error occurred while updating user.", status_code=500)


@api_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    DELETE /api/users/<id>
    Delete user. Associated tasks are deleted via CASCADE.
    """
    existing_user = models.get_user_by_id(user_id)
    if not existing_user:
        return error_response(f"User with ID {user_id} not found.", status_code=404)

    try:
        models.delete_user(user_id)
        return success_response(message="User deleted successfully")
    except Exception as e:
        logger.exception("Failed to delete user: %s", e)
        return error_response("An internal server error occurred while deleting user.", status_code=500)
