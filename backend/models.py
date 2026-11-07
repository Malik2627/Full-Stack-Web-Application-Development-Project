"""
TaskFlow Models and Database Helper Functions
----------------------------------------------
Provides CRUD operations and helper functions for Users, Categories, and Tasks.
All functions manage SQLite connections safely, enable foreign keys, and return dict representations.
"""

import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection


# ============================================================================
# USERS MODEL HELPERS
# ============================================================================

def hash_password(password):
    """Securely hash a password using Werkzeug."""
    if not password:
        return ""
    # If already a werkzeug hash, avoid double-hashing
    if password.startswith(('scrypt:', 'pbkdf2:')):
        return password
    return generate_password_hash(password)


def verify_user_password(stored_hash, provided_password):
    """
    Verifies a password against the stored password hash using Werkzeug.
    Falls back to direct comparison for legacy pre-Step 8 seed records.
    """
    if not stored_hash or not provided_password:
        return False
    try:
        if check_password_hash(stored_hash, provided_password):
            return True
    except Exception:
        pass
    return stored_hash == provided_password


def create_user(name, email, password):
    """
    Create a new user with secure Werkzeug password hashing.
    Returns the created user dictionary (password omitted or sanitized).
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        hashed = hash_password(password)
        cursor.execute(
            """
            INSERT INTO users (name, email, password)
            VALUES (?, ?, ?)
            """,
            (name.strip(), email.strip().lower(), hashed)
        )
        conn.commit()
        user_id = cursor.lastrowid
        return get_user_by_id(user_id)
    finally:
        conn.close()


def get_user_by_id(user_id):
    """
    Retrieve a single user by primary key ID.
    Returns dict or None.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, email, password, created_at FROM users WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_email(email):
    """
    Retrieve a user by their email address (case-insensitive).
    Returns dict or None.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, email, password, created_at FROM users WHERE LOWER(email) = LOWER(?)",
            (email.strip(),)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_all_users():
    """
    Retrieve all registered users.
    Returns a list of user dictionaries.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, created_at FROM users ORDER BY id ASC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def update_user(user_id, name=None, email=None, password=None):
    """
    Update user profile fields.
    Returns updated user dict or None if not found.
    """
    existing = get_user_by_id(user_id)
    if not existing:
        return None

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        new_name = name.strip() if name is not None else existing['name']
        new_email = email.strip().lower() if email is not None else existing['email']
        new_password = hash_password(password) if password is not None else existing['password']

        cursor.execute(
            "UPDATE users SET name = ?, email = ?, password = ? WHERE id = ?",
            (new_name, new_email, new_password, user_id)
        )
        conn.commit()
        return get_user_by_id(user_id)
    finally:
        conn.close()


def delete_user(user_id):
    """
    Delete a user by ID.
    Associated tasks are automatically deleted via CASCADE.
    Returns True if deleted, False otherwise.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ============================================================================
# CATEGORIES MODEL HELPERS
# ============================================================================

def create_category(name, color=None):
    """
    Create a new task category.
    Returns the created category dictionary.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO categories (name, color) VALUES (?, ?)",
            (name.strip(), color.strip() if color else None)
        )
        conn.commit()
        category_id = cursor.lastrowid
        return get_category_by_id(category_id)
    finally:
        conn.close()


def get_all_categories():
    """
    Retrieve all categories.
    Returns a list of category dictionaries.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, color, created_at FROM categories ORDER BY id ASC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_category_by_id(category_id):
    """
    Retrieve a single category by ID.
    Returns dict or None.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, color, created_at FROM categories WHERE id = ?",
            (category_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_category(category_id, name=None, color=None):
    """
    Update a category's name and/or color.
    Returns updated category dict or None if not found.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        existing = get_category_by_id(category_id)
        if not existing:
            return None

        new_name = name.strip() if name is not None else existing['name']
        new_color = color.strip() if color is not None else existing['color']

        cursor.execute(
            "UPDATE categories SET name = ?, color = ? WHERE id = ?",
            (new_name, new_color, category_id)
        )
        conn.commit()
        return get_category_by_id(category_id)
    finally:
        conn.close()


def delete_category(category_id):
    """
    Delete a category by ID.
    Foreign key in tasks is configured with ON DELETE SET NULL.
    Returns True if deleted, False otherwise.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ============================================================================
# TASKS MODEL HELPERS
# ============================================================================

def create_task(title, description=None, user_id=None, category_id=None,
                priority='Medium', status='Pending', due_date=None):
    """
    Create a new student task linked to a user and category.
    Returns the created task dictionary.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO tasks (
                user_id, category_id, title, description,
                priority, status, due_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                category_id,
                title.strip(),
                description.strip() if description else None,
                priority or 'Medium',
                status or 'Pending',
                due_date
            )
        )
        conn.commit()
        task_id = cursor.lastrowid
        return get_task_by_id(task_id)
    finally:
        conn.close()


def get_all_tasks(user_id=None, category_id=None, status=None, priority=None):
    """
    Retrieve tasks with optional filters (user_id, category_id, status, priority).
    Includes joined user and category information.
    Returns a list of task dictionaries.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                t.id,
                t.user_id,
                t.category_id,
                t.title,
                t.description,
                t.priority,
                t.status,
                t.due_date,
                t.created_at,
                t.updated_at,
                u.name AS user_name,
                u.email AS user_email,
                c.name AS category_name,
                c.color AS category_color
            FROM tasks t
            LEFT JOIN users u ON t.user_id = u.id
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE 1=1
        """
        params = []

        if user_id is not None:
            query += " AND t.user_id = ?"
            params.append(user_id)

        if category_id is not None:
            query += " AND t.category_id = ?"
            params.append(category_id)

        if status is not None:
            query += " AND LOWER(t.status) = LOWER(?)"
            params.append(status)

        if priority is not None:
            query += " AND LOWER(t.priority) = LOWER(?)"
            params.append(priority)

        query += " ORDER BY t.created_at DESC"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_task_by_id(task_id):
    """
    Retrieve a single task by ID with joined user and category details.
    Returns dict or None.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                t.id,
                t.user_id,
                t.category_id,
                t.title,
                t.description,
                t.priority,
                t.status,
                t.due_date,
                t.created_at,
                t.updated_at,
                u.name AS user_name,
                u.email AS user_email,
                c.name AS category_name,
                c.color AS category_color
            FROM tasks t
            LEFT JOIN users u ON t.user_id = u.id
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE t.id = ?
            """,
            (task_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_task(task_id, **kwargs):
    """
    Update task fields (title, description, user_id, category_id, priority, status, due_date).
    Automatically updates updated_at timestamp.
    Returns updated task dict or None if not found.
    """
    allowed_fields = {
        'title', 'description', 'user_id', 'category_id',
        'priority', 'status', 'due_date'
    }

    updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
    if not updates:
        return get_task_by_id(task_id)

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        set_clauses = [f"{field} = ?" for field in updates.keys()]
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        values = list(updates.values())
        values.append(task_id)

        query = f"UPDATE tasks SET {', '.join(set_clauses)} WHERE id = ?"
        cursor.execute(query, tuple(values))
        conn.commit()

        if cursor.rowcount == 0:
            return None
        return get_task_by_id(task_id)
    finally:
        conn.close()


def delete_task(task_id):
    """
    Delete a task by ID.
    Returns True if deleted, False otherwise.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
