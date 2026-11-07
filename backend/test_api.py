"""
TaskFlow REST API Comprehensive Test Suite
-------------------------------------------
Tests every endpoint, CRUD operations, validations, HTTP status codes,
and relational integrity across Users, Categories, and Tasks.

Usage:
    python backend/test_api.py
"""

import sys
import json
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import app
from database import get_db_connection


class APITester:
    def __init__(self):
        self.client = app.test_client()
        self.passed_tests = 0
        self.total_tests = 0
        self.test_user_id = None
        self.test_category_id = None
        self.test_task_id = None

    def assert_test(self, condition, test_name, details=""):
        self.total_tests += 1
        if condition:
            self.passed_tests += 1
            print(f"  ✓ [{self.passed_tests}] {test_name}")
        else:
            print(f"  ✗ FAILED: {test_name} - {details}")
            raise AssertionError(f"Test failed: {test_name}. {details}")

    def run_all(self):
        print("=" * 70)
        print("TASKFLOW REST API CRUD & VALIDATION TEST SUITE")
        print("=" * 70)

        # Clean leftover test user if any
        conn = get_db_connection()
        conn.execute("DELETE FROM users WHERE email = 'maria.garcia@university.edu';")
        conn.commit()
        conn.close()

        self.test_health_and_status()
        self.test_categories_crud()
        self.test_users_crud()
        # Set authenticated session for task tests
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.test_user_id
        self.test_tasks_validation()
        self.test_tasks_crud_and_filters()
        self.test_persistence()

        print("\n" + "=" * 70)
        print(f"ALL {self.passed_tests}/{self.total_tests} API TESTS PASSED SUCCESSFULLY! ✓")
        print("=" * 70)

    # ------------------------------------------------------------------------
    # 1. Health & DB Status Endpoints
    # ------------------------------------------------------------------------
    def test_health_and_status(self):
        print("\n[Phase 1] Testing Health & DB Status Endpoints")

        # GET /api/health
        res = self.client.get('/api/health')
        data = res.get_json()
        self.assert_test(
            res.status_code == 200 and data.get('status') == 'success' and 'TaskFlow API is running' in data.get('message', ''),
            "GET /api/health returns 200 and success status"
        )

        # GET /api/db/status
        res = self.client.get('/api/db/status')
        data = res.get_json()
        self.assert_test(
            res.status_code == 200 and data.get('data', {}).get('database') == 'connected',
            "GET /api/db/status confirms database is connected with seeded tables"
        )

    # ------------------------------------------------------------------------
    # 2. Categories API CRUD
    # ------------------------------------------------------------------------
    def test_categories_crud(self):
        print("\n[Phase 2] Testing Categories API (CRUD & Validation)")

        # GET /api/categories
        res = self.client.get('/api/categories')
        data = res.get_json()
        self.assert_test(
            res.status_code == 200 and isinstance(data.get('data'), list) and len(data.get('data')) >= 5,
            "GET /api/categories returns 200 and list of categories (includes seeded defaults)"
        )

        # POST /api/categories - Validation (missing name)
        res = self.client.post('/api/categories', json={"color": "#ff0000"})
        self.assert_test(
            res.status_code == 400 and res.get_json().get('status') == 'error',
            "POST /api/categories rejects payload without name (400 Bad Request)"
        )

        # POST /api/categories - Success
        res = self.client.post('/api/categories', json={"name": "Computer Science Electives", "color": "#8b5cf6"})
        data = res.get_json()
        self.assert_test(
            res.status_code == 201 and data.get('data', {}).get('name') == "Computer Science Electives",
            "POST /api/categories creates new category (201 Created)"
        )
        self.test_category_id = data.get('data', {}).get('id')

        # POST /api/categories - Duplicate name (409 Conflict / 400 Bad Request)
        res = self.client.post('/api/categories', json={"name": "Computer Science Electives"})
        self.assert_test(
            res.status_code in (400, 409),
            "POST /api/categories prevents duplicate category name (409 Conflict / 400 Bad Request)"
        )

        # GET /api/categories/<id>
        res = self.client.get(f'/api/categories/{self.test_category_id}')
        data = res.get_json()
        self.assert_test(
            res.status_code == 200 and data.get('data', {}).get('id') == self.test_category_id,
            f"GET /api/categories/{self.test_category_id} retrieves single category (200 OK)"
        )

        # PUT /api/categories/<id>
        res = self.client.put(f'/api/categories/{self.test_category_id}', json={"name": "CS Electives", "color": "#7c3aed"})
        data = res.get_json()
        self.assert_test(
            res.status_code == 200 and data.get('data', {}).get('name') == "CS Electives",
            "PUT /api/categories/<id> updates category name and color (200 OK)"
        )

        # DELETE /api/categories/<id>
        res = self.client.delete(f'/api/categories/{self.test_category_id}')
        self.assert_test(
            res.status_code == 200 and res.get_json().get('status') == 'success',
            "DELETE /api/categories/<id> deletes category (200 OK)"
        )

        # GET /api/categories/<id> after delete
        res = self.client.get(f'/api/categories/{self.test_category_id}')
        self.assert_test(
            res.status_code == 404,
            "GET /api/categories/<deleted_id> returns 404 Not Found"
        )

    # ------------------------------------------------------------------------
    # 3. Users API CRUD
    # ------------------------------------------------------------------------
    def test_users_crud(self):
        print("\n[Phase 3] Testing Users API (CRUD & Validation)")

        # GET /api/users
        res = self.client.get('/api/users')
        self.assert_test(
            res.status_code == 200 and isinstance(res.get_json().get('data'), list),
            "GET /api/users returns 200 and list of users"
        )

        # POST /api/users - Validation (invalid email)
        res = self.client.post('/api/users', json={"name": "John Doe", "email": "not-an-email", "password": "pass"})
        self.assert_test(
            res.status_code == 400 and "email" in res.get_json().get('errors', {}),
            "POST /api/users rejects invalid email format (400 Bad Request)"
        )

        # POST /api/users - Success
        user_payload = {
            "name": "Maria Garcia",
            "email": "maria.garcia@university.edu",
            "password": "plain_text_dev_pass_123"
        }
        res = self.client.post('/api/users', json=user_payload)
        data = res.get_json()
        self.assert_test(
            res.status_code == 201 and data.get('data', {}).get('email') == user_payload['email'],
            "POST /api/users creates user successfully (201 Created)"
        )
        # Verify password omitted from response
        self.assert_test(
            'password' not in data.get('data', {}),
            "POST /api/users response safely omits password field"
        )
        self.test_user_id = data.get('data', {}).get('id')

        # POST /api/users - Duplicate email (409 Conflict / 400 Bad Request)
        res = self.client.post('/api/users', json=user_payload)
        self.assert_test(
            res.status_code in (400, 409),
            "POST /api/users rejects duplicate email registration (409 Conflict / 400 Bad Request)"
        )

        # GET /api/users/<id>
        res = self.client.get(f'/api/users/{self.test_user_id}')
        data = res.get_json()
        self.assert_test(
            res.status_code == 200 and data.get('data', {}).get('id') == self.test_user_id and 'password' not in data.get('data', {}),
            f"GET /api/users/{self.test_user_id} retrieves single user safely (200 OK)"
        )

        # PUT /api/users/<id>
        res = self.client.put(f'/api/users/{self.test_user_id}', json={"name": "Maria G. Silva"})
        data = res.get_json()
        self.assert_test(
            res.status_code == 200 and data.get('data', {}).get('name') == "Maria G. Silva",
            "PUT /api/users/<id> updates user profile (200 OK)"
        )

    # ------------------------------------------------------------------------
    # 4. Tasks API Validation
    # ------------------------------------------------------------------------
    def test_tasks_validation(self):
        print("\n[Phase 4] Testing Tasks API Validations")

        # Missing title
        res = self.client.post('/api/tasks', json={"description": "No title provided"})
        self.assert_test(
            res.status_code == 400 and 'title' in res.get_json().get('errors', {}),
            "POST /api/tasks rejects missing title (400 Bad Request)"
        )

        # Empty title string
        res = self.client.post('/api/tasks', json={"title": "   ", "user_id": self.test_user_id})
        self.assert_test(
            res.status_code == 400 and 'title' in res.get_json().get('errors', {}),
            "POST /api/tasks rejects whitespace-only title (400 Bad Request)"
        )

        # Invalid priority
        res = self.client.post('/api/tasks', json={"title": "Test Task", "priority": "SuperUrgent"})
        self.assert_test(
            res.status_code == 400 and 'priority' in res.get_json().get('errors', {}),
            "POST /api/tasks rejects invalid priority value (400 Bad Request)"
        )

        # Invalid status
        res = self.client.post('/api/tasks', json={"title": "Test Task", "status": "FinishedForever"})
        self.assert_test(
            res.status_code == 400 and 'status' in res.get_json().get('errors', {}),
            "POST /api/tasks rejects invalid status value (400 Bad Request)"
        )

        # Invalid due_date format
        res = self.client.post('/api/tasks', json={"title": "Test Task", "due_date": "10-11-2026"})
        self.assert_test(
            res.status_code == 400 and 'due_date' in res.get_json().get('errors', {}),
            "POST /api/tasks rejects non YYYY-MM-DD date format (400 Bad Request)"
        )

        # Non-existent user_id
        res = self.client.post('/api/tasks', json={"title": "Test Task", "user_id": 999999})
        self.assert_test(
            res.status_code == 400 and 'user_id' in res.get_json().get('errors', {}),
            "POST /api/tasks validates foreign key and rejects non-existent user_id (400 Bad Request)"
        )

        # Non-existent category_id
        res = self.client.post('/api/tasks', json={"title": "Test Task", "category_id": 999999})
        self.assert_test(
            res.status_code == 400 and 'category_id' in res.get_json().get('errors', {}),
            "POST /api/tasks validates foreign key and rejects non-existent category_id (400 Bad Request)"
        )

    # ------------------------------------------------------------------------
    # 5. Tasks API CRUD & Filters
    # ------------------------------------------------------------------------
    def test_tasks_crud_and_filters(self):
        print("\n[Phase 5] Testing Tasks API CRUD & Filtering")

        # POST /api/tasks - Exact example from prompt
        task_payload = {
            "title": "Complete Deep Learning Assignment",
            "description": "Finish CNN and object detection notes",
            "priority": "High",
            "status": "Pending",
            "due_date": "2026-11-10",
            "category_id": 1,  # 'Study' seeded category
            "user_id": self.test_user_id
        }
        res = self.client.post('/api/tasks', json=task_payload)
        data = res.get_json()
        self.assert_test(
            res.status_code == 201 and data.get('data', {}).get('title') == task_payload['title'],
            "POST /api/tasks creates task successfully (201 Created)"
        )
        task_data = data.get('data', {})
        self.test_task_id = task_data.get('id')
        self.assert_test(
            task_data.get('category_name') == "Study" and task_data.get('user_name') == "Maria G. Silva",
            "Created task response includes joined category_name and user_name"
        )

        # Create a second task for filter testing
        res2 = self.client.post('/api/tasks', json={
            "title": "Prepare Gym Schedule",
            "priority": "Low",
            "status": "Completed",
            "category_id": 2,  # 'Personal'
            "user_id": self.test_user_id
        })
        task2_id = res2.get_json().get('data', {}).get('id')

        # GET /api/tasks
        res = self.client.get('/api/tasks')
        data = res.get_json()
        self.assert_test(
            res.status_code == 200 and data.get('count') >= 2,
            "GET /api/tasks retrieves all tasks (200 OK)"
        )

        # Filter ?status=Pending
        res = self.client.get('/api/tasks?status=Pending')
        data = res.get_json()
        self.assert_test(
            res.status_code == 200 and all(t['status'] == 'Pending' for t in data.get('data', [])),
            "GET /api/tasks?status=Pending returns only Pending tasks"
        )

        # Filter ?priority=High
        res = self.client.get('/api/tasks?priority=High')
        data = res.get_json()
        self.assert_test(
            res.status_code == 200 and all(t['priority'] == 'High' for t in data.get('data', [])),
            "GET /api/tasks?priority=High returns only High priority tasks"
        )

        # Filter ?category_id=1
        res = self.client.get('/api/tasks?category_id=1')
        data = res.get_json()
        self.assert_test(
            res.status_code == 200 and all(t['category_id'] == 1 for t in data.get('data', [])),
            "GET /api/tasks?category_id=1 returns only tasks in category 1"
        )

        # GET /api/tasks/<id>
        res = self.client.get(f'/api/tasks/{self.test_task_id}')
        data = res.get_json()
        self.assert_test(
            res.status_code == 200 and data.get('data', {}).get('id') == self.test_task_id,
            f"GET /api/tasks/{self.test_task_id} returns single task (200 OK)"
        )

        # PUT /api/tasks/<id>
        update_payload = {
            "status": "In Progress",
            "priority": "Urgent",
            "due_date": "2026-11-15",
            "description": "Updated CNN architecture notes and model checkpointing"
        }
        res = self.client.put(f'/api/tasks/{self.test_task_id}', json=update_payload)
        data = res.get_json()
        updated_data = data.get('data', {})
        self.assert_test(
            res.status_code == 200 and updated_data.get('status') == "In Progress" and updated_data.get('priority') == "Urgent",
            f"PUT /api/tasks/{self.test_task_id} updates task fields (200 OK)"
        )

        # DELETE /api/tasks/<id>
        res = self.client.delete(f'/api/tasks/{self.test_task_id}')
        self.assert_test(
            res.status_code == 200 and res.get_json().get('status') == 'success',
            f"DELETE /api/tasks/{self.test_task_id} deletes task (200 OK)"
        )

        # GET /api/tasks/<deleted_id> -> 404
        res = self.client.get(f'/api/tasks/{self.test_task_id}')
        self.assert_test(
            res.status_code == 404,
            "GET /api/tasks/<deleted_id> returns 404 Not Found"
        )

        # Clean up second task
        self.client.delete(f'/api/tasks/{task2_id}')

        # Clean up user (which tests DELETE /api/users/<id>)
        res = self.client.delete(f'/api/users/{self.test_user_id}')
        self.assert_test(
            res.status_code == 200,
            f"DELETE /api/users/{self.test_user_id} deletes user successfully (200 OK)"
        )

    # ------------------------------------------------------------------------
    # 6. Database Persistence
    # ------------------------------------------------------------------------
    def test_persistence(self):
        print("\n[Phase 6] Verifying SQLite Physical Persistence")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM categories")
        count = cursor.fetchone()['count']
        conn.close()

        self.assert_test(
            count >= 5,
            f"Direct SQLite file query confirms {count} categories physically persisted in taskflow.db"
        )


if __name__ == '__main__':
    tester = APITester()
    tester.run_all()

