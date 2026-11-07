import sys
import sqlite3
from pathlib import Path

# Ensure backend directory is in sys.path regardless of execution working directory
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from config import Config

# Default initial categories for students
DEFAULT_CATEGORIES = [
    {"name": "Study", "color": "#4f46e5"},
    {"name": "Personal", "color": "#10b981"},
    {"name": "Work", "color": "#0ea5e9"},
    {"name": "Project", "color": "#f59e0b"},
    {"name": "Other", "color": "#64748b"}
]

# Initial coursework tasks for student demo
INITIAL_TASKS = [
    {
        "title": "Complete Deep Learning Assignment",
        "description": "Finish CNN and object detection notes",
        "priority": "High",
        "status": "In Progress",
        "due_date": "2026-11-10",
        "category_name": "Study"
    },
    {
        "title": "Database Schema Design Report",
        "description": "Document relational model & SQLite triggers",
        "priority": "Urgent",
        "status": "Pending",
        "due_date": "2026-11-12",
        "category_name": "Project"
    },
    {
        "title": "Linear Algebra Problem Set 4",
        "description": "Eigenvalues and matrix decomposition proofs",
        "priority": "Medium",
        "status": "Completed",
        "due_date": "2026-11-05",
        "category_name": "Study"
    },
    {
        "title": "Software Engineering Sprint Retro",
        "description": "Prepare backlog presentation for team meeting",
        "priority": "Medium",
        "status": "In Progress",
        "due_date": "2026-11-14",
        "category_name": "Work"
    },
    {
        "title": "Campus Tech Club Presentation",
        "description": "Build 10 slide deck on modern Full-Stack web apps",
        "priority": "Low",
        "status": "Completed",
        "due_date": "2026-11-03",
        "category_name": "Personal"
    }
]


def get_db_connection():
    """
    Establish and return a SQLite database connection.
    - Connects to taskflow.db (ensuring parent directory exists)
    - Enables foreign key constraint enforcement
    - Configures row_factory for column-name-based row access
    """
    db_path = Path(Config.DATABASE)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    # Enable SQLite foreign-key support
    conn.execute("PRAGMA foreign_keys = ON;")
    # Enable accessing columns by name
    conn.row_factory = sqlite3.Row
    return conn


def create_tables(conn):
    """
    Create database tables (users, categories, tasks) if they do not exist.
    Preserves existing data.
    """
    cursor = conn.cursor()

    # 1. Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. Categories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL UNIQUE,
            color VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 3. Tasks table with foreign keys
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category_id INTEGER,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            priority VARCHAR(20) DEFAULT 'Medium',
            status VARCHAR(20) DEFAULT 'Pending',
            due_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE SET NULL
        );
    """)

    conn.commit()


def seed_categories(conn):
    """
    Seed initial categories if they do not already exist.
    Prevents duplicate entries across restarts.
    """
    cursor = conn.cursor()
    for cat in DEFAULT_CATEGORIES:
        cursor.execute(
            "SELECT id FROM categories WHERE LOWER(name) = LOWER(?)",
            (cat["name"],)
        )
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO categories (name, color) VALUES (?, ?)",
                (cat["name"], cat["color"])
            )
    conn.commit()


def seed_default_user(conn):
    """
    Seed a default student profile (Alex Johnson) if not exists.
    Uses Werkzeug secure password hashing to prevent plain-text storage.
    """
    from werkzeug.security import generate_password_hash
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = 'alex.student@example.edu'")
    user = cursor.fetchone()
    if not user:
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            ("Alex Johnson", "alex.student@example.edu", generate_password_hash("student123"))
        )
        conn.commit()
        return cursor.lastrowid
    return user['id']


def seed_sample_tasks(conn, user_id):
    """
    Seed initial coursework tasks only if the tasks table is empty.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS count FROM tasks")
    count = cursor.fetchone()['count']
    if count == 0:
        for t in INITIAL_TASKS:
            cursor.execute("SELECT id FROM categories WHERE LOWER(name) = LOWER(?)", (t['category_name'],))
            cat_row = cursor.fetchone()
            cat_id = cat_row['id'] if cat_row else 1

            cursor.execute(
                """
                INSERT INTO tasks (user_id, category_id, title, description, priority, status, due_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, cat_id, t['title'], t['description'], t['priority'], t['status'], t['due_date'])
            )
        conn.commit()


def init_db():
    """
    Initialize the database when Flask starts:
    1. Check whether database file/directory exists and connect
    2. Create required tables if they don't already exist
    3. Seed default categories without duplicating existing records
    4. Seed default student profile and initial tasks if empty
    5. Close connection safely
    """
    conn = get_db_connection()
    try:
        create_tables(conn)
        seed_categories(conn)
        user_id = seed_default_user(conn)
        seed_sample_tasks(conn, user_id)
    finally:
        conn.close()
