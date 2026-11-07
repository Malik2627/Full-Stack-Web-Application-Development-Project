"""
Step 8 User Authentication & Protected Access Test Suite
--------------------------------------------------------
Tests Werkzeug password hashing, user registration, login, logout,
error handling (empty fields, invalid credentials, duplicate email),
and per-user protected task isolation.

Usage:
    python backend/test_auth.py
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


class AuthTester:
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

    def clean_test_users(self):
        """Clean temporary test users from SQLite."""
        conn = get_db_connection()
        conn.execute("DELETE FROM users WHERE email LIKE '%@testsuite.edu' OR email LIKE '%@isolation.edu';")
        conn.commit()
        conn.close()

    def run_all(self):
        print("=" * 70)
        print("STEP 8: USER AUTHENTICATION & SECURITY TEST SUITE")
        print("=" * 70)

        self.clean_test_users()

        # ====================================================================
        # Phase 1: Security & Password Hashing Verification
        # ====================================================================
        print("\n[Phase 1] Security & Werkzeug Password Hashing Verification")
        
        # Test models.hash_password
        raw_pw = "superSecret123"
        hashed = models.hash_password(raw_pw)
        self.assert_test(
            hashed != raw_pw and hashed.startswith(('scrypt:', 'pbkdf2:')),
            "generate_password_hash() securely encrypts passwords with Werkzeug"
        )
        self.assert_test(
            models.verify_user_password(hashed, raw_pw),
            "check_password_hash() correctly verifies matching password"
        )
        self.assert_test(
            not models.verify_user_password(hashed, "wrongPassword!"),
            "check_password_hash() rejects incorrect password"
        )

        # ====================================================================
        # Phase 2: Registration API (POST /api/auth/register)
        # ====================================================================
        print("\n[Phase 2] Registration API Validations & Creation")

        # 1. Missing / Empty fields
        res = self.client.post('/api/auth/register', json={})
        self.assert_test(res.status_code == 400, "POST /api/auth/register rejects empty payload (400)")

        res = self.client.post('/api/auth/register', json={
            "name": "",
            "email": "invalid-email",
            "password": "123"
        })
        self.assert_test(res.status_code == 400, "POST /api/auth/register validates name, email format, and min password length")

        # 2. Successful Registration
        alice_data = {
            "name": "Alice Wonderland",
            "email": "alice@testsuite.edu",
            "password": "alicePassword123"
        }
        res = self.client.post('/api/auth/register', json=alice_data)
        data = res.get_json()
        self.assert_test(
            res.status_code == 201 and data.get('status') == 'success',
            "POST /api/auth/register creates new student account (201 Created)"
        )
        user_info = data.get('data', {}).get('user', {})
        auth_token = data.get('data', {}).get('token')
        self.assert_test(
            user_info.get('email') == alice_data['email'] and 'password' not in user_info,
            "Registration response omits password field for security"
        )
        self.assert_test(
            bool(auth_token),
            "Registration response issues signed auth session token"
        )

        # Verify password in database is NOT stored as plaintext
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE email = ?", (alice_data['email'],))
        row = cursor.fetchone()
        conn.close()
        db_pw = row['password']
        self.assert_test(
            db_pw != alice_data['password'] and db_pw.startswith(('scrypt:', 'pbkdf2:')),
            "SQLite database physically stores Werkzeug hashed password (no plaintext)"
        )

        # ====================================================================
        # Phase 3: Duplicate Registration Prevention
        # ====================================================================
        print("\n[Phase 3] Duplicate Registration Prevention")

        res = self.client.post('/api/auth/register', json=alice_data)
        self.assert_test(
            res.status_code in (400, 409) and "already exists" in res.get_json().get('message', ''),
            "POST /api/auth/register rejects duplicate email registration (409 Conflict / 400 Bad Request)"
        )

        # ====================================================================
        # Phase 4: Login API (POST /api/auth/login)
        # ====================================================================
        print("\n[Phase 4] Login API (Valid & Invalid Scenarios)")

        # 1. Missing credentials
        res = self.client.post('/api/auth/login', json={"email": "alice@testsuite.edu"})
        self.assert_test(res.status_code == 400, "POST /api/auth/login rejects missing password (400)")

        # 2. Invalid password
        res = self.client.post('/api/auth/login', json={
            "email": "alice@testsuite.edu",
            "password": "wrongPassword"
        })
        self.assert_test(res.status_code == 401, "POST /api/auth/login rejects incorrect password (401 Unauthorized)")

        # 3. Non-existent email
        res = self.client.post('/api/auth/login', json={
            "email": "ghost@testsuite.edu",
            "password": "somePassword"
        })
        self.assert_test(res.status_code == 401, "POST /api/auth/login rejects non-existent email (401 Unauthorized)")

        # 4. Successful login
        res = self.client.post('/api/auth/login', json={
            "email": "alice@testsuite.edu",
            "password": "alicePassword123"
        })
        data = res.get_json()
        self.assert_test(
            res.status_code == 200 and data.get('status') == 'success',
            "POST /api/auth/login authenticates user successfully (200 OK)"
        )
        self.assert_test(
            'password' not in data.get('data', {}).get('user', {}),
            "Login response safely omits password field"
        )

        # ====================================================================
        # Phase 5: Authentication Session (GET /api/auth/me & POST /api/auth/logout)
        # ====================================================================
        print("\n[Phase 5] Current User Profile & Logout")

        # 1. GET /api/auth/me with active session
        res = self.client.get('/api/auth/me')
        self.assert_test(
            res.status_code == 200 and res.get_json().get('data', {}).get('user', {}).get('email') == "alice@testsuite.edu",
            "GET /api/auth/me retrieves authenticated user profile via session"
        )

        # 2. GET /api/auth/me with Bearer token
        token = data.get('data', {}).get('token')
        fresh_client = app.test_client()
        res_bearer = fresh_client.get('/api/auth/me', headers={"Authorization": f"Bearer {token}"})
        self.assert_test(
            res_bearer.status_code == 200 and res_bearer.get_json().get('data', {}).get('user', {}).get('name') == "Alice Wonderland",
            "GET /api/auth/me authenticates via Bearer Authorization header"
        )

        # 3. POST /api/auth/logout
        res = self.client.post('/api/auth/logout')
        self.assert_test(res.status_code == 200, "POST /api/auth/logout successfully clears session")

        # 4. Verify unauthenticated access returns 401
        res = self.client.get('/api/auth/me')
        self.assert_test(res.status_code == 401, "GET /api/auth/me returns 401 Unauthorized after logout")

        # ====================================================================
        # Phase 6: Protected Task Access & Per-User Isolation
        # ====================================================================
        print("\n[Phase 6] Protected Functionality & User-Isolated Task Access")

        # 1. Register User A (Alice) and create task
        client_alice = app.test_client()
        res_a = client_alice.post('/api/auth/register', json={
            "name": "Alice Isolation",
            "email": "alice@isolation.edu",
            "password": "passwordA123"
        })
        alice_token = res_a.get_json()['data']['token']

        # Alice creates a task
        res_t1 = client_alice.post('/api/tasks', json={
            "title": "Alice's Secret Thesis Defense",
            "priority": "High",
            "status": "Pending",
            "due_date": "2026-11-20"
        })
        self.assert_test(res_t1.status_code == 201, "Authenticated User A creates task linked to their user_id")
        alice_task_id = res_t1.get_json()['data']['id']

        # 2. Register User B (Bob) and create task
        client_bob = app.test_client()
        res_b = client_bob.post('/api/auth/register', json={
            "name": "Bob Isolation",
            "email": "bob@isolation.edu",
            "password": "passwordB123"
        })
        bob_token = res_b.get_json()['data']['token']

        # Bob creates a task
        res_t2 = client_bob.post('/api/tasks', json={
            "title": "Bob's Discrete Math Homework",
            "priority": "Medium",
            "status": "In Progress",
            "due_date": "2026-11-25"
        })
        self.assert_test(res_t2.status_code == 201, "Authenticated User B creates task linked to their user_id")
        bob_task_id = res_t2.get_json()['data']['id']

        # 3. User B queries GET /api/tasks -> Must ONLY see Bob's task!
        res_bob_tasks = client_bob.get('/api/tasks')
        bob_tasks = res_bob_tasks.get_json()['data']
        bob_titles = [t['title'] for t in bob_tasks]
        self.assert_test(
            "Bob's Discrete Math Homework" in bob_titles and "Alice's Secret Thesis Defense" not in bob_titles,
            "Protected GET /api/tasks scopes results to authenticated user (User B cannot see User A's tasks)"
        )

        # 4. User A queries GET /api/tasks -> Must ONLY see Alice's task!
        res_alice_tasks = client_alice.get('/api/tasks')
        alice_tasks = res_alice_tasks.get_json()['data']
        alice_titles = [t['title'] for t in alice_tasks]
        self.assert_test(
            "Alice's Secret Thesis Defense" in alice_titles and "Bob's Discrete Math Homework" not in alice_titles,
            "User A only sees their own tasks in GET /api/tasks"
        )

        # 5. User B attempts unauthorized access to User A's task
        res_unauth_get = client_bob.get(f'/api/tasks/{alice_task_id}')
        self.assert_test(
            res_unauth_get.status_code == 403,
            "User B blocked from viewing User A's task (403 Forbidden)"
        )

        res_unauth_put = client_bob.put(f'/api/tasks/{alice_task_id}', json={"status": "Completed"})
        self.assert_test(
            res_unauth_put.status_code == 403,
            "User B blocked from modifying User A's task (403 Forbidden)"
        )

        res_unauth_del = client_bob.delete(f'/api/tasks/{alice_task_id}')
        self.assert_test(
            res_unauth_del.status_code == 403,
            "User B blocked from deleting User A's task (403 Forbidden)"
        )

        # 6. User A can successfully modify and delete their own task
        res_auth_put = client_alice.put(f'/api/tasks/{alice_task_id}', json={"status": "Completed"})
        self.assert_test(res_auth_put.status_code == 200, "User A successfully modifies their own task (200 OK)")

        res_auth_del = client_alice.delete(f'/api/tasks/{alice_task_id}')
        self.assert_test(res_auth_del.status_code == 200, "User A successfully deletes their own task (200 OK)")

        # Clean up test users
        self.clean_test_users()

        print("=" * 70)
        print(f"ALL {self.passed}/{self.total} STEP 8 AUTH & SECURITY TESTS PASSED! ✓")
        print("=" * 70)


if __name__ == '__main__':
    tester = AuthTester()
    tester.run_all()

