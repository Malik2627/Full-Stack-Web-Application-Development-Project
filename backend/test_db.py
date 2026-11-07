"""
TaskFlow Database Verification Script
-------------------------------------
Tests and verifies SQLite tables, foreign key constraints, default categories,
and CRUD helper functions for Users, Categories, and Tasks.

Usage:
    python backend/test_db.py
"""

import sys
import sqlite3
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from database import init_db, get_db_connection
import models


def test_database():
    print("=" * 60)
    print("TaskFlow Database Verification Test")
    print("=" * 60)

    # 1. Initialize DB
    print("\n[1/6] Initializing database...")
    init_db()
    print("✓ Database initialized successfully.")

    # 2. Check Tables
    print("\n[2/6] Verifying required tables...")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [row['name'] for row in cursor.fetchall() if row['name'] != 'sqlite_sequence']
    conn.close()

    expected_tables = {'users', 'categories', 'tasks'}
    print(f"  Found tables: {tables}")
    assert expected_tables.issubset(set(tables)), f"Missing tables! Expected {expected_tables}"
    print("✓ All required tables (users, categories, tasks) are present.")

    # 3. Check Seeded Categories
    print("\n[3/6] Verifying seeded categories...")
    categories = models.get_all_categories()
    cat_names = [c['name'] for c in categories]
    print(f"  Categories count: {len(categories)}")
    print(f"  Categories: {cat_names}")

    expected_categories = {"Study", "Personal", "Work", "Project", "Other"}
    for cat in expected_categories:
        assert cat in cat_names, f"Expected category '{cat}' missing from database!"
    print("✓ All 5 default categories successfully seeded.")

    # Re-run init_db to test idempotency (no duplicate categories)
    init_db()
    categories_after = models.get_all_categories()
    assert len(categories) == len(categories_after), "Duplicate categories created on re-initialization!"
    print("✓ Category seeding is idempotent (no duplicates created on re-run).")

    # 4. Test User Model Helpers
    print("\n[4/6] Testing Users model helpers...")
    test_email = "alex.student@example.edu"
    existing_user = models.get_user_by_email(test_email)
    if existing_user:
        user = existing_user
        print(f"  Existing test user retrieved: {user['name']} (ID: {user['id']})")
    else:
        user = models.create_user("Alex Johnson", test_email, "plaintext_temp_password_123")
        print(f"  Created test user: {user['name']} (ID: {user['id']})")

    fetched_user = models.get_user_by_id(user['id'])
    assert fetched_user is not None and fetched_user['email'] == test_email
    print("✓ User creation and retrieval by ID / email verified.")

    # 5. Test Category & Task Helpers with Foreign Keys
    print("\n[5/6] Testing Task model helpers and relationships...")
    study_cat = next(c for c in categories if c['name'] == 'Study')

    task = models.create_task(
        title="Complete CS101 Algorithm Analysis",
        description="Write merge sort complexity proof and run benchmark suite.",
        user_id=user['id'],
        category_id=study_cat['id'],
        priority="High",
        status="Pending",
        due_date="2026-11-20"
    )
    print(f"  Created task: '{task['title']}' (ID: {task['id']}, Category: {task['category_name']}, User: {task['user_name']})")
    assert task['user_id'] == user['id']
    assert task['category_id'] == study_cat['id']
    assert task['priority'] == "High"

    # Test update task
    updated_task = models.update_task(task['id'], status="In Progress", priority="Urgent")
    assert updated_task['status'] == "In Progress"
    assert updated_task['priority'] == "Urgent"
    print(f"  Updated task status to: '{updated_task['status']}'")

    # Filter tasks
    filtered_tasks = models.get_all_tasks(user_id=user['id'], status="In Progress")
    assert any(t['id'] == task['id'] for t in filtered_tasks)
    print(f"  Filtered tasks count for user {user['id']} (status: In Progress): {len(filtered_tasks)}")

    # 6. Test Foreign Key Enforcement
    print("\n[6/6] Testing SQLite foreign key constraint enforcement...")
    non_existent_user_id = 999999
    try:
        models.create_task(
            title="Task with invalid user",
            user_id=non_existent_user_id
        )
        print("✗ ERROR: Foreign key constraint failed to block invalid user_id!")
        sys.exit(1)
    except sqlite3.IntegrityError:
        print("✓ Foreign key constraint successfully blocked orphan task creation.")

    # Clean up test task
    deleted = models.delete_task(task['id'])
    assert deleted, "Failed to delete test task"
    print("✓ Test task cleaned up successfully.")

    print("\n" + "=" * 60)
    print("ALL DATABASE TESTS PASSED SUCCESSFULLY! ✓")
    print("=" * 60)


if __name__ == '__main__':
    test_database()

