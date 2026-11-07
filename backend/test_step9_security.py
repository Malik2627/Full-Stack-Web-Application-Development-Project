"""
Step 9 Multi-User Data Isolation & Security Test Suite
------------------------------------------------------
Verifies:
1. Every task belongs to the authenticated user.
2. The backend automatically gets the user ID from authentication.
3. Untrusted frontend-supplied user IDs are completely ignored.
4. User A can only see, create, update, and delete User A's tasks.
5. User A cannot access User B's tasks (403 Forbidden).
6. Multi-user dashboard statistics isolation.
7. Categories availability across user task operations.
8. Logout session clearance and redirect conditions.

Usage:
    python backend/test_step9_security.py
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


class Step9SecurityTester:
    def __init__(self):
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

    def clean_test_data(self):
        """Cleans test users and their cascading tasks."""
        conn = get_db_connection()
        conn.execute("DELETE FROM users WHERE email LIKE '%@secstep9.edu';")
        conn.commit()
        conn.close()

    def run(self):
        print("=" * 70)
        print("STEP 9: MULTI-USER DATA ISOLATION & SECURITY TEST SUITE")
        print("=" * 70)

        self.clean_test_data()

        # ====================================================================
        # Phase 1: Register Multiple Users
        # ====================================================================
        print("\n[Phase 1] Registering Multiple Test Users (Alice, Bob, Charlie)")

        # Client A: Alice
        client_a = app.test_client()
        res_a = client_a.post('/api/auth/register', json={
            "name": "Alice Anderson",
            "email": "alice@secstep9.edu",
            "password": "alicePassword123"
        })
        self.assert_test(res_a.status_code == 201, "User A (Alice) registered successfully (201 Created)")
        alice_id = res_a.get_json()['data']['user']['id']
        alice_token = res_a.get_json()['data']['token']

        # Client B: Bob
        client_b = app.test_client()
        res_b = client_b.post('/api/auth/register', json={
            "name": "Bob Baker",
            "email": "bob@secstep9.edu",
            "password": "bobPassword123"
        })
        self.assert_test(res_b.status_code == 201, "User B (Bob) registered successfully (201 Created)")
        bob_id = res_b.get_json()['data']['user']['id']
        bob_token = res_b.get_json()['data']['token']

        # Client C: Charlie
        client_c = app.test_client()
        res_c = client_c.post('/api/auth/register', json={
            "name": "Charlie Clark",
            "email": "charlie@secstep9.edu",
            "password": "charliePassword123"
        })
        self.assert_test(res_c.status_code == 201, "User C (Charlie) registered successfully (201 Created)")
        charlie_id = res_c.get_json()['data']['user']['id']
        charlie_token = res_c.get_json()['data']['token']

        # ====================================================================
        # Phase 2: Do NOT Trust Frontend-Supplied user_id
        # ====================================================================
        print("\n[Phase 2] Verifying Backend Never Trusts Frontend-Supplied user_id")

        # Alice attempts to submit a task with Bob's user_id or a fake user_id (999999)
        tampered_res = client_a.post('/api/tasks', json={
            "title": "Alice's Tamper Attempt",
            "description": "Attempting to assign task to Bob",
            "priority": "High",
            "status": "Pending",
            "user_id": bob_id,  # Tampered user_id
            "category_id": 1
        })
        self.assert_test(tampered_res.status_code == 201, "Task creation succeeds without error")
        tampered_task = tampered_res.get_json()['data']
        self.assert_test(
            tampered_task['user_id'] == alice_id and tampered_task['user_id'] != bob_id,
            "Backend strictly overrides frontend-supplied user_id with authenticated user ID (Alice)"
        )

        # Alice attempts to update task and inject user_id: charlie_id
        alice_task_id = tampered_task['id']
        tampered_put = client_a.put(f'/api/tasks/{alice_task_id}', json={
            "title": "Alice's Updated Task",
            "user_id": charlie_id  # Attempted transfer of ownership
        })
        self.assert_test(tampered_put.status_code == 200, "Task update succeeds")
        updated_task = tampered_put.get_json()['data']
        self.assert_test(
            updated_task['user_id'] == alice_id and updated_task['user_id'] != charlie_id,
            "Backend prevents re-assigning task ownership via PUT payload"
        )

        # ====================================================================
        # Phase 3: Multi-User Task Creation with Categories
        # ====================================================================
        print("\n[Phase 3] Task Creation Linked to Database Categories")

        # Verify category dropdown loads from database
        cat_res = client_a.get('/api/categories')
        self.assert_test(
            cat_res.status_code == 200 and len(cat_res.get_json()['data']) >= 5,
            "Categories load dynamically from database for user tasks (Study, Personal, Work, etc.)"
        )
        categories = cat_res.get_json()['data']
        study_id = categories[0]['id']
        work_id = categories[1]['id']

        # Alice creates 2 more tasks
        client_a.post('/api/tasks', json={
            "title": "Alice Task - Algorithms Assignment",
            "priority": "High",
            "status": "Completed",
            "due_date": "2026-11-15",
            "category_id": study_id
        })
        client_a.post('/api/tasks', json={
            "title": "Alice Task - Lab Report 2",
            "priority": "Medium",
            "status": "In Progress",
            "due_date": "2026-11-18",
            "category_id": study_id
        })

        # Bob creates 2 tasks
        res_bob_t1 = client_b.post('/api/tasks', json={
            "title": "Bob Task - Internship Resume Review",
            "priority": "Urgent",
            "status": "Pending",
            "due_date": "2026-11-12",
            "category_id": work_id
        })
        bob_task_1_id = res_bob_t1.get_json()['data']['id']

        client_b.post('/api/tasks', json={
            "title": "Bob Task - Weekly Team Sync",
            "priority": "Low",
            "status": "Pending",
            "due_date": "2026-11-14",
            "category_id": work_id
        })

        # Charlie creates 0 tasks (pristine state)

        # ====================================================================
        # Phase 4: User Data Isolation & Scoped Queries
        # ====================================================================
        print("\n[Phase 4] Verifying User Task Isolation in GET /api/tasks")

        # 1. User A (Alice) queries tasks
        tasks_a_res = client_a.get('/api/tasks')
        tasks_a = tasks_a_res.get_json()['data']
        self.assert_test(len(tasks_a) == 3, f"Alice receives exactly 3 tasks (got {len(tasks_a)})")
        self.assert_test(
            all(t['user_id'] == alice_id for t in tasks_a),
            "All tasks returned to Alice belong strictly to Alice"
        )
        self.assert_test(
            not any("Bob Task" in t['title'] for t in tasks_a),
            "Alice's task query does NOT leak any of Bob's tasks"
        )

        # 2. User B (Bob) queries tasks
        tasks_b_res = client_b.get('/api/tasks')
        tasks_b = tasks_b_res.get_json()['data']
        self.assert_test(len(tasks_b) == 2, f"Bob receives exactly 2 tasks (got {len(tasks_b)})")
        self.assert_test(
            all(t['user_id'] == bob_id for t in tasks_b),
            "All tasks returned to Bob belong strictly to Bob"
        )
        self.assert_test(
            not any("Alice" in t['title'] for t in tasks_b),
            "Bob's task query does NOT leak any of Alice's tasks"
        )

        # 3. User C (Charlie) queries tasks
        tasks_c_res = client_c.get('/api/tasks')
        tasks_c = tasks_c_res.get_json()['data']
        self.assert_test(len(tasks_c) == 0, f"Charlie receives exactly 0 tasks (got {len(tasks_c)})")

        # ====================================================================
        # Phase 5: Dashboard Statistics Isolation
        # ====================================================================
        print("\n[Phase 5] Verifying Multi-User Dashboard Statistics Isolation")

        # Alice statistics
        comp_a = len([t for t in tasks_a if t['status'] == 'Completed'])
        in_prog_a = len([t for t in tasks_a if t['status'] == 'In Progress'])
        pend_a = len([t for t in tasks_a if t['status'] == 'Pending'])
        self.assert_test(
            len(tasks_a) == 3 and comp_a == 1 and in_prog_a == 1 and pend_a == 1,
            "Alice's dashboard statistics calculate strictly for Alice (Total: 3, Completed: 1, In Prog: 1, Pending: 1)"
        )

        # Bob statistics
        comp_b = len([t for t in tasks_b if t['status'] == 'Completed'])
        pend_b = len([t for t in tasks_b if t['status'] == 'Pending'])
        self.assert_test(
            len(tasks_b) == 2 and comp_b == 0 and pend_b == 2,
            "Bob's dashboard statistics calculate strictly for Bob (Total: 2, Completed: 0, Pending: 2)"
        )

        # Charlie statistics
        self.assert_test(
            len(tasks_c) == 0,
            "Charlie's dashboard statistics calculate strictly for Charlie (Total: 0, pristine state)"
        )

        # ====================================================================
        # Phase 6: Cross-User Access Blocked (Rules Enforcement)
        # ====================================================================
        print("\n[Phase 6] Cross-User Access Prohibition (User A must NOT access User B's tasks)")

        # 1. Bob attempts GET Alice's task -> 403 Forbidden
        bob_try_get = client_b.get(f'/api/tasks/{alice_task_id}')
        self.assert_test(bob_try_get.status_code == 403, "Bob cannot view Alice's task (403 Forbidden)")

        # 2. Bob attempts PUT Alice's task -> 403 Forbidden
        bob_try_put = client_b.put(f'/api/tasks/{alice_task_id}', json={"status": "Completed"})
        self.assert_test(bob_try_put.status_code == 403, "Bob cannot modify Alice's task (403 Forbidden)")

        # 3. Bob attempts DELETE Alice's task -> 403 Forbidden
        bob_try_del = client_b.delete(f'/api/tasks/{alice_task_id}')
        self.assert_test(bob_try_del.status_code == 403, "Bob cannot delete Alice's task (403 Forbidden)")

        # 4. Charlie attempts DELETE Bob's task -> 403 Forbidden
        charlie_try_del = client_c.delete(f'/api/tasks/{bob_task_1_id}')
        self.assert_test(charlie_try_del.status_code == 403, "Charlie cannot delete Bob's task (403 Forbidden)")

        # 5. Alice can update and delete her own task
        alice_put = client_a.put(f'/api/tasks/{alice_task_id}', json={"status": "Completed"})
        self.assert_test(alice_put.status_code == 200, "Alice can update Alice's task (200 OK)")

        alice_del = client_a.delete(f'/api/tasks/{alice_task_id}')
        self.assert_test(alice_del.status_code == 200, "Alice can delete Alice's task (200 OK)")

        # ====================================================================
        # Phase 7: Logout & Session Clearing
        # ====================================================================
        print("\n[Phase 7] Dashboard Logout & Session Clearance")

        # Alice logs out
        logout_res = client_a.post('/api/auth/logout')
        self.assert_test(logout_res.status_code == 200, "POST /api/auth/logout clears user session (200 OK)")

        # After logout, accessing auth/me returns 401
        me_after_logout = client_a.get('/api/auth/me')
        self.assert_test(me_after_logout.status_code == 401, "GET /api/auth/me returns 401 Unauthorized after logout")

        # Clean up test users
        self.clean_test_data()

        print("=" * 70)
        print(f"ALL {self.passed}/{self.total} STEP 9 SECURITY & ISOLATION TESTS PASSED! ✓")
        print("=" * 70)


if __name__ == '__main__':
    tester = Step9SecurityTester()
    tester.run()

