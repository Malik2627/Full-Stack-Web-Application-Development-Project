"""
Step 10 Application Validation, Error Handling & Security Test Suite
--------------------------------------------------------------------
Tests:
1. Backend input validations:
   - Required fields
   - Email format & length
   - Password minimum length
   - Task title validation
   - Priority domain validation
   - Status domain validation
   - Category reference validation
   - Real calendar date validation (rejecting non-existent calendar days e.g. 2026-02-31)
2. HTTP status codes:
   - 400 Bad Request
   - 401 Unauthorized
   - 403 Forbidden
   - 404 Not Found
   - 409 Conflict
   - 500 Server Error
3. User Experience & Information Leak Prevention:
   - Zero Python tracebacks in error responses
   - Zero raw SQL / sqlite3 error strings leaked to client
   - Friendly, user-safe error messages

Usage:
    python backend/test_step10_validation.py
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
import models


class Step10ValidationTester:
    def __init__(self):
        self.client = app.test_client()
        self.passed = 0
        self.total = 0

    def assert_test(self, condition, name, details=""):
        self.total += 1
        if condition:
            self.passed += 1
            print(f"  ✓ [{self.passed}] {name}")
        else:
            print(f"  ✗ FAILED: {name} - {details}")
            raise AssertionError(f"Test failed: {name}. {details}")

    def clean_db(self):
        conn = get_db_connection()
        conn.execute("DELETE FROM users WHERE email LIKE '%@step10.edu';")
        conn.commit()
        conn.close()

    def run_all(self):
        print("=" * 70)
        print("STEP 10: APPLICATION VALIDATION & ERROR HANDLING TEST SUITE")
        print("=" * 70)

        self.clean_db()

        # ====================================================================
        # Phase 1: Registration & Auth Input Validations
        # ====================================================================
        print("\n[Phase 1] Auth Input Validation (Email, Password, Name)")

        # 1. Missing / Empty email
        res = self.client.post('/api/auth/register', json={"name": "Test User", "password": "password123"})
        data = res.get_json()
        self.assert_test(
            res.status_code == 400 and 'email' in data.get('errors', {}),
            "Rejects registration without email (400 Bad Request)"
        )

        # 2. Invalid email format
        res = self.client.post('/api/auth/register', json={"name": "Test User", "email": "not-an-email", "password": "password123"})
        data = res.get_json()
        self.assert_test(
            res.status_code == 400 and "valid email" in data.get('errors', {}).get('email', '').lower(),
            "Rejects invalid email format with friendly guidance (400 Bad Request)"
        )

        # 3. Missing password
        res = self.client.post('/api/auth/register', json={"name": "Test User", "email": "valid@step10.edu"})
        data = res.get_json()
        self.assert_test(
            res.status_code == 400 and 'password' in data.get('errors', {}),
            "Rejects registration without password (400 Bad Request)"
        )

        # 4. Short password (< 6 chars)
        res = self.client.post('/api/auth/register', json={"name": "Test User", "email": "valid@step10.edu", "password": "123"})
        data = res.get_json()
        self.assert_test(
            res.status_code == 400 and "at least 6 characters" in data.get('errors', {}).get('password', ''),
            "Enforces minimum 6 character password length (400 Bad Request)"
        )

        # 5. Missing user name
        res = self.client.post('/api/auth/register', json={"name": "   ", "email": "valid@step10.edu", "password": "password123"})
        data = res.get_json()
        self.assert_test(
            res.status_code == 400 and 'name' in data.get('errors', {}),
            "Rejects registration with whitespace-only name (400 Bad Request)"
        )

        # Register User A for subsequent tests
        user_a_res = self.client.post('/api/auth/register', json={
            "name": "Validation User A",
            "email": "user.a@step10.edu",
            "password": "userA_secret123"
        })
        self.assert_test(user_a_res.status_code == 201, "Registers User A successfully (201 Created)")
        user_a = user_a_res.get_json()['data']['user']
        user_a_id = user_a['id']
        token_a = user_a_res.get_json()['data']['token']

        # ====================================================================
        # Phase 2: Conflict Handling (409 Conflict)
        # ====================================================================
        print("\n[Phase 2] HTTP 409 Conflict Handling")

        # 6. Duplicate email registration
        dup_reg = self.client.post('/api/auth/register', json={
            "name": "Duplicate A",
            "email": "user.a@step10.edu",
            "password": "anotherPassword"
        })
        self.assert_test(
            dup_reg.status_code == 409 and "already exists" in dup_reg.get_json().get('message', ''),
            "Duplicate email registration returns 409 Conflict"
        )

        # 7. Duplicate category creation
        dup_cat = self.client.post('/api/categories', json={"name": "Study"})
        self.assert_test(
            dup_cat.status_code == 409 and "already exists" in dup_cat.get_json().get('message', ''),
            "Duplicate category creation returns 409 Conflict"
        )

        # ====================================================================
        # Phase 3: Task Validation (Title, Priority, Status, Category, Date)
        # ====================================================================
        print("\n[Phase 3] Task Field Validations (Title, Priority, Status, Date)")
        headers_a = {'Authorization': f'Bearer {token_a}'}

        # 8. Missing task title
        res = self.client.post('/api/tasks', headers=headers_a, json={
            "description": "Forgot to provide a title",
            "priority": "High"
        })
        data = res.get_json()
        self.assert_test(
            res.status_code == 400 and data.get('errors', {}).get('title') == "Task title is required.",
            "Rejects missing task title with 'Task title is required.' (400 Bad Request)"
        )

        # 9. Empty / Whitespace-only title
        res = self.client.post('/api/tasks', headers=headers_a, json={
            "title": "     ",
            "priority": "High"
        })
        data = res.get_json()
        self.assert_test(
            res.status_code == 400 and data.get('errors', {}).get('title') == "Task title is required.",
            "Rejects whitespace-only task title (400 Bad Request)"
        )

        # 10. Invalid priority
        res = self.client.post('/api/tasks', headers=headers_a, json={
            "title": "Valid Task Title",
            "priority": "NonExistentPriority"
        })
        data = res.get_json()
        self.assert_test(
            res.status_code == 400 and 'priority' in data.get('errors', {}),
            "Rejects invalid priority value (400 Bad Request)"
        )

        # 11. Invalid status
        res = self.client.post('/api/tasks', headers=headers_a, json={
            "title": "Valid Task Title",
            "status": "DoingRightNow"
        })
        data = res.get_json()
        self.assert_test(
            res.status_code == 400 and 'status' in data.get('errors', {}),
            "Rejects invalid status value (400 Bad Request)"
        )

        # 12. Invalid calendar date: non-existent February 31st (2026-02-31)
        res = self.client.post('/api/tasks', headers=headers_a, json={
            "title": "Test Calendar Date",
            "due_date": "2026-02-31"
        })
        data = res.get_json()
        self.assert_test(
            res.status_code == 400 and "Due date cannot be invalid" in data.get('errors', {}).get('due_date', ''),
            "Rejects non-existent calendar day 2026-02-31 with 'Due date cannot be invalid' (400)"
        )

        # 13. Invalid date format: DD-MM-YYYY
        res = self.client.post('/api/tasks', headers=headers_a, json={
            "title": "Test Date Format",
            "due_date": "31-12-2026"
        })
        data = res.get_json()
        self.assert_test(
            res.status_code == 400 and "Due date cannot be invalid" in data.get('errors', {}).get('due_date', ''),
            "Rejects invalid date format DD-MM-YYYY with 'Due date cannot be invalid' (400)"
        )

        # 14. Non-existent category reference
        res = self.client.post('/api/tasks', headers=headers_a, json={
            "title": "Valid Task",
            "category_id": 999999
        })
        data = res.get_json()
        self.assert_test(
            res.status_code == 400 and 'category_id' in data.get('errors', {}),
            "Rejects non-existent category foreign key (400 Bad Request)"
        )

        # ====================================================================
        # Phase 4: HTTP Status Codes Verification (401, 403, 404)
        # ====================================================================
        print("\n[Phase 4] HTTP Status Codes: 401 Unauthorized, 403 Forbidden, 404 Not Found")

        # 15. 401 Unauthorized: Accessing /api/auth/me without authentication
        unauth_client = app.test_client()
        res = unauth_client.get('/api/auth/me')
        self.assert_test(res.status_code == 401, "GET /api/auth/me returns 401 Unauthorized when unauthenticated")

        # 16. 401 Unauthorized: Login with invalid password
        res = self.client.post('/api/auth/login', json={"email": "user.a@step10.edu", "password": "wrongPassword"})
        self.assert_test(res.status_code == 401, "POST /api/auth/login returns 401 Unauthorized on bad credentials")

        # Create task for User A
        task_a_res = self.client.post('/api/tasks', headers=headers_a, json={
            "title": "User A Private Coursework",
            "priority": "High",
            "status": "Pending",
            "due_date": "2026-11-20"
        })
        task_a = task_a_res.get_json()['data']
        task_a_id = task_a['id']

        # Register User B
        user_b_res = self.client.post('/api/auth/register', json={
            "name": "Validation User B",
            "email": "user.b@step10.edu",
            "password": "userB_secret123"
        })
        token_b = user_b_res.get_json()['data']['token']
        headers_b = {'Authorization': f'Bearer {token_b}'}

        # 17. 403 Forbidden: User B attempting to view User A's task
        res = self.client.get(f'/api/tasks/{task_a_id}', headers=headers_b)
        self.assert_test(res.status_code == 403, "GET /api/tasks/<other_user_id> returns 403 Forbidden")

        # 18. 403 Forbidden: User B attempting to edit User A's task
        res = self.client.put(f'/api/tasks/{task_a_id}', headers=headers_b, json={"title": "Hacked Title"})
        self.assert_test(res.status_code == 403, "PUT /api/tasks/<other_user_id> returns 403 Forbidden")

        # 19. 403 Forbidden: User B attempting to delete User A's task
        res = self.client.delete(f'/api/tasks/{task_a_id}', headers=headers_b)
        self.assert_test(res.status_code == 403, "DELETE /api/tasks/<other_user_id> returns 403 Forbidden")

        # 20. 404 Not Found: Requesting non-existent task ID
        res = self.client.get('/api/tasks/888888', headers=headers_a)
        self.assert_test(res.status_code == 404, "GET /api/tasks/<nonexistent> returns 404 Not Found")

        # 21. 404 Not Found: Requesting non-existent category ID
        res = self.client.get('/api/categories/888888')
        self.assert_test(res.status_code == 404, "GET /api/categories/<nonexistent> returns 404 Not Found")

        # 22. 404 Not Found: Requesting non-existent API endpoint
        res = self.client.get('/api/completely-unknown-route')
        self.assert_test(res.status_code == 404, "Non-existent API endpoint returns 404 Not Found JSON")

        # ====================================================================
        # Phase 5: 500 Server Error & Traceback / SQL Leak Prevention
        # ====================================================================
        print("\n[Phase 5] 500 Server Error & Information Masking (No Tracebacks / SQL Leaks)")

        # 23. Simulated internal server error returns 500
        res = self.client.get('/api/test-server-error')
        self.assert_test(res.status_code == 500, "Simulated server exception returns 500 Internal Server Error")

        # 24. 500 error response returns structured JSON with friendly message
        data_500 = res.get_json()
        self.assert_test(
            data_500.get('status') == 'error' and "server error" in data_500.get('message', '').lower(),
            "500 response contains user-friendly message without internal error specifics"
        )

        # 25. Response NEVER contains Python traceback
        res_text = res.get_data(as_text=True)
        self.assert_test(
            "Traceback (most recent call last)" not in res_text and 'File "' not in res_text,
            "Response strictly suppresses Python traceback and stack frames"
        )

        # 26. Response NEVER leaks internal SQLite details
        self.assert_test(
            "sqlite3" not in res_text and "OperationalError" not in res_text and "IntegrityError" not in res_text,
            "Response strictly suppresses SQL database driver and table details"
        )

        # Clean test accounts
        self.clean_db()

        print("\n" + "=" * 70)
        print(f"ALL {self.passed}/{self.total} STEP 10 VALIDATION & ERROR HANDLING TESTS PASSED! ✓")
        print("=" * 70)


if __name__ == '__main__':
    tester = Step10ValidationTester()
    tester.run_all()
