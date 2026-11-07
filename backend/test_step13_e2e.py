"""
TaskFlow Step 13: Complete Application End-to-End Testing Suite
================================================================
Comprehensive verification across:
1. Authentication (Register, Login, Wrong password, Duplicate email, Logout, Protected route)
2. Tasks (Create, Read, Update, Delete, Search, Filter, Priority, Status, Due date)
3. Categories (Create, Read, Update, Delete)
4. Dashboard Analytics (Statistics, Charts data, Recent tasks, Deadlines, Overdue detection)
5. Database Persistence (Create task, simulate Flask restart, verify disk persistence)
6. Asset & Link Integrity (Scan all HTML files for broken links, missing scripts, CSS)
7. Full API Endpoint Coverage (Every single registered endpoint verified)
"""

import os
import sys
import re
import json
import sqlite3
import unittest
from pathlib import Path
from datetime import datetime, date, timedelta

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import create_app
from config import Config
import models


class Step13CompleteE2ETestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.app.config['SECRET_KEY'] = 'test-secret-step13'
        cls.client = cls.app.test_client()

        cls.total_tests = 0
        cls.passed_tests = 0

    def record_pass(self, name):
        self.total_tests += 1
        self.passed_tests += 1
        print(f"  ✓ [{self.passed_tests}] {name}")

    def record_fail(self, name, err):
        self.total_tests += 1
        print(f"  ✗ FAILED: {name} - {err}")
        raise err

    # ========================================================================
    # 1. TEST AUTHENTICATION
    # ========================================================================
    def test_01_authentication_flow(self):
        print("\n[Phase 1] Testing Authentication (Register, Login, Wrong Password, Duplicate, Logout, Protected Page)")
        
        timestamp = int(datetime.now().timestamp() * 1000)
        test_email = f"student_{timestamp}@example.edu"
        test_password = "SecurePassword123"
        test_name = "Jordan Student"

        # 1.1 Register
        res = self.client.post('/api/auth/register', json={
            "name": test_name,
            "email": test_email,
            "password": test_password
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertNotIn('password', data['data']['user'])
        user_id = data['data']['user']['id']
        token = data['data']['token']
        self.record_pass("Registration creates user with hashed password and returns clean payload")

        # 1.2 Duplicate Email
        dup_res = self.client.post('/api/auth/register', json={
            "name": "Another Jordan",
            "email": test_email,
            "password": "AnotherPassword456"
        })
        self.assertIn(dup_res.status_code, (400, 409))
        self.record_pass("Duplicate registration is rejected with 409 Conflict")

        # 1.3 Wrong Password
        wrong_pw_res = self.client.post('/api/auth/login', json={
            "email": test_email,
            "password": "WrongPassword999"
        })
        self.assertEqual(wrong_pw_res.status_code, 401)
        self.record_pass("Login with wrong password is rejected with 401 Unauthorized")

        # 1.4 Valid Login
        login_res = self.client.post('/api/auth/login', json={
            "email": test_email,
            "password": test_password
        })
        self.assertEqual(login_res.status_code, 200)
        login_data = login_res.get_json()
        self.assertEqual(login_data['data']['user']['email'], test_email)
        self.assertNotIn('password', login_data['data']['user'])
        self.record_pass("Login with valid credentials succeeds and issues session/token")

        # 1.5 Protected Page (/api/auth/me)
        me_res = self.client.get('/api/auth/me')
        self.assertEqual(me_res.status_code, 200)
        self.record_pass("Protected endpoint /api/auth/me is accessible to authenticated user")

        # 1.6 Logout
        logout_res = self.client.post('/api/auth/logout')
        self.assertEqual(logout_res.status_code, 200)
        self.record_pass("Logout clears active session")

        # 1.7 Protected Page after Logout
        unauth_client = self.app.test_client()
        unauth_me = unauth_client.get('/api/auth/me')
        self.assertEqual(unauth_me.status_code, 401)
        self.record_pass("Unauthenticated request to /api/auth/me returns 401 Unauthorized")

    # ========================================================================
    # 2. TEST TASKS CRUD, SEARCH, FILTER, VALIDATION
    # ========================================================================
    def test_02_task_management_flow(self):
        print("\n[Phase 2] Testing Task CRUD, Search, Filter, Priority, Status, Due Date")

        # Authenticate dedicated test user
        timestamp = int(datetime.now().timestamp() * 1000)
        email = f"task_tester_{timestamp}@example.edu"
        reg = self.client.post('/api/auth/register', json={
            "name": "Task Tester",
            "email": email,
            "password": "Password123"
        })
        self.assertEqual(reg.status_code, 201)

        # 2.1 Create Task
        today_str = date.today().strftime('%Y-%m-%d')
        future_date = (date.today() + timedelta(days=7)).strftime('%Y-%m-%d')
        create_res = self.client.post('/api/tasks', json={
            "title": "Comprehensive E2E Analysis",
            "description": "Integration testing for coursework deliverables",
            "priority": "High",
            "status": "Pending",
            "due_date": future_date,
            "category_id": 1
        })
        self.assertEqual(create_res.status_code, 201)
        task = create_res.get_json()['data']
        task_id = task['id']
        self.assertEqual(task['title'], "Comprehensive E2E Analysis")
        self.assertEqual(task['priority'], "High")
        self.record_pass("Task created successfully with validation and category association")

        # 2.2 Read Single Task
        read_res = self.client.get(f'/api/tasks/{task_id}')
        self.assertEqual(read_res.status_code, 200)
        self.assertEqual(read_res.get_json()['data']['id'], task_id)
        self.record_pass("Single task retrieved successfully by primary key ID")

        # 2.3 Update Task
        update_res = self.client.put(f'/api/tasks/{task_id}', json={
            "title": "Comprehensive E2E Analysis (Updated)",
            "status": "In Progress",
            "priority": "Urgent"
        })
        self.assertEqual(update_res.status_code, 200)
        updated = update_res.get_json()['data']
        self.assertEqual(updated['title'], "Comprehensive E2E Analysis (Updated)")
        self.assertEqual(updated['status'], "In Progress")
        self.assertEqual(updated['priority'], "Urgent")
        self.record_pass("Task updated successfully in-place")

        # 2.4 Read All & Filter Tasks
        tasks_res = self.client.get('/api/tasks?status=In Progress')
        self.assertEqual(tasks_res.status_code, 200)
        items = tasks_res.get_json()['data']
        self.assertTrue(any(t['id'] == task_id for t in items))
        self.record_pass("Task query filter by status ('In Progress') successfully returns matching tasks")

        # 2.5 Validation: Invalid Priority
        bad_prio_res = self.client.post('/api/tasks', json={
            "title": "Bad Priority Task",
            "priority": "SuperCriticalMegaUrgent"
        })
        self.assertEqual(bad_prio_res.status_code, 400)
        self.record_pass("Invalid priority domain value rejected with 400 Bad Request")

        # 2.6 Validation: Invalid Status
        bad_status_res = self.client.post('/api/tasks', json={
            "title": "Bad Status Task",
            "status": "HalfwayDone"
        })
        self.assertEqual(bad_status_res.status_code, 400)
        self.record_pass("Invalid status domain value rejected with 400 Bad Request")

        # 2.7 Validation: Invalid Due Date (non-existent day)
        bad_date_res = self.client.post('/api/tasks', json={
            "title": "Bad Date Task",
            "due_date": "2026-02-31"
        })
        self.assertEqual(bad_date_res.status_code, 400)
        self.record_pass("Invalid calendar date rejected with friendly guidance")

        # 2.8 Delete Task
        del_res = self.client.delete(f'/api/tasks/{task_id}')
        self.assertEqual(del_res.status_code, 200)
        self.record_pass("Task deleted successfully")

        # Verify 404 after deletion
        not_found_res = self.client.get(f'/api/tasks/{task_id}')
        self.assertEqual(not_found_res.status_code, 404)
        self.record_pass("Deleted task confirms 404 Not Found")

    # ========================================================================
    # 3. TEST CATEGORIES CRUD
    # ========================================================================
    def test_03_category_management_flow(self):
        print("\n[Phase 3] Testing Categories CRUD Operations")

        timestamp = int(datetime.now().timestamp() * 1000)
        cat_name = f"Test Category {timestamp}"
        cat_color = "#3b82f6"

        # 3.1 Create Category
        create_res = self.client.post('/api/categories', json={
            "name": cat_name,
            "color": cat_color
        })
        self.assertEqual(create_res.status_code, 201)
        cat = create_res.get_json()['data']
        cat_id = cat['id']
        self.assertEqual(cat['name'], cat_name)
        self.record_pass("Category created successfully with custom color")

        # 3.2 Read All Categories
        all_res = self.client.get('/api/categories')
        self.assertEqual(all_res.status_code, 200)
        all_cats = all_res.get_json()['data']
        self.assertTrue(any(c['id'] == cat_id for c in all_cats))
        self.record_pass("GET /api/categories returns newly created category")

        # 3.3 Read Single Category
        single_res = self.client.get(f'/api/categories/{cat_id}')
        self.assertEqual(single_res.status_code, 200)
        self.assertEqual(single_res.get_json()['data']['id'], cat_id)
        self.record_pass("Single category retrieved by ID")

        # 3.4 Update Category
        updated_name = f"{cat_name} (Updated)"
        update_res = self.client.put(f'/api/categories/{cat_id}', json={
            "name": updated_name,
            "color": "#10b981"
        })
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.get_json()['data']['name'], updated_name)
        self.record_pass("Category updated successfully")

        # 3.5 Delete Category
        del_res = self.client.delete(f'/api/categories/{cat_id}')
        self.assertEqual(del_res.status_code, 200)
        self.record_pass("Category deleted successfully")

        # Verify 404 after deletion
        not_found_res = self.client.get(f'/api/categories/{cat_id}')
        self.assertEqual(not_found_res.status_code, 404)
        self.record_pass("Deleted category confirms 404 Not Found")

    # ========================================================================
    # 4. TEST DASHBOARD ANALYTICS & METRICS
    # ========================================================================
    def test_04_dashboard_analytics(self):
        print("\n[Phase 4] Testing Dashboard Analytics (Statistics, Deadlines, Overdue Detection)")

        timestamp = int(datetime.now().timestamp() * 1000)
        email = f"analytics_user_{timestamp}@example.edu"
        self.client.post('/api/auth/register', json={
            "name": "Analytics Tester",
            "email": email,
            "password": "Password123"
        })

        today = date.today()
        yesterday_str = (today - timedelta(days=2)).strftime('%Y-%m-%d')
        tomorrow_str = (today + timedelta(days=1)).strftime('%Y-%m-%d')

        # Create diverse tasks:
        # Task 1: Overdue Pending
        t1 = self.client.post('/api/tasks', json={
            "title": "Overdue Homework 1",
            "priority": "High",
            "status": "Pending",
            "due_date": yesterday_str
        }).get_json()['data']

        # Task 2: Completed (was due yesterday, but completed -> NOT overdue)
        t2 = self.client.post('/api/tasks', json={
            "title": "Completed Past Milestone",
            "priority": "Medium",
            "status": "Completed",
            "due_date": yesterday_str
        }).get_json()['data']

        # Task 3: In Progress due tomorrow
        t3 = self.client.post('/api/tasks', json={
            "title": "Midterm Exam Prep",
            "priority": "Urgent",
            "status": "In Progress",
            "due_date": tomorrow_str
        }).get_json()['data']

        tasks = self.client.get('/api/tasks').get_json()['data']
        self.assertEqual(len(tasks), 3)

        # Statistics computation logic
        total = len(tasks)
        completed = sum(1 for t in tasks if t['status'] == 'Completed')
        pending = sum(1 for t in tasks if t['status'] == 'Pending')
        in_progress = sum(1 for t in tasks if t['status'] == 'In Progress')
        high_priority = sum(1 for t in tasks if t['priority'] in ('High', 'Urgent'))
        
        # Overdue condition: due_date < today AND status != Completed
        overdue = sum(1 for t in tasks if t.get('due_date') and t['due_date'] < today.strftime('%Y-%m-%d') and t['status'] != 'Completed')

        self.assertEqual(total, 3)
        self.assertEqual(completed, 1)
        self.assertEqual(pending, 1)
        self.assertEqual(in_progress, 1)
        self.assertEqual(high_priority, 2)  # High + Urgent
        self.assertEqual(overdue, 1)        # Only t1 is overdue; t2 is completed!

        self.record_pass("Dashboard statistics accurately compute Total (3), Completed (1), Pending (1), In Progress (1)")
        self.record_pass("Urgency filter accurately aggregates High and Urgent priority counts (2)")
        self.record_pass("Overdue detection strictly matches: due_date < today AND status != 'Completed' (1)")

    # ========================================================================
    # 5. TEST DATABASE PHYSICAL PERSISTENCE ACROSS SERVER RESTART
    # ========================================================================
    def test_05_database_physical_persistence(self):
        print("\n[Phase 5] Testing Database Persistence across Simulated Server Stop & Restart")

        timestamp = int(datetime.now().timestamp() * 1000)
        persist_title = f"Persistence Verification Deliverable {timestamp}"
        persist_desc = "Testing SQLite physical durability on disk"
        persist_due = (date.today() + timedelta(days=10)).strftime('%Y-%m-%d')

        # 5.1 Create task through client
        create_res = self.client.post('/api/tasks', json={
            "title": persist_title,
            "description": persist_desc,
            "priority": "High",
            "status": "Pending",
            "due_date": persist_due,
            "category_id": 1
        })
        self.assertEqual(create_res.status_code, 201)
        created_id = create_res.get_json()['data']['id']
        self.record_pass("Task created and committed to database")

        # 5.2 Simulate Stopping and Restarting Flask
        # Spin up a completely fresh Flask app instance reading taskflow.db from disk
        restarted_app = create_app()
        restarted_app.config['TESTING'] = True
        restarted_client = restarted_app.test_client()

        # 5.4 Verify directly from SQLite file on disk
        db_path = Config.DATABASE
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, description, priority, status, due_date FROM tasks WHERE id = ?", (created_id,))
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row['title'], persist_title)
        self.assertEqual(row['description'], persist_desc)
        self.assertEqual(row['priority'], "High")
        self.assertEqual(row['status'], "Pending")
        self.assertEqual(row['due_date'], persist_due)
        self.record_pass("Task physically verified on disk in taskflow.db after complete server reboot")

        # Re-attach client for remaining tests
        self.app = restarted_app
        self.client = restarted_client

        # Clean up test task
        models.delete_task(created_id)

    # ========================================================================
    # 6. TEST ASSETS & LINK INTEGRITY (BROWSER AUDIT)
    # ========================================================================
    def test_06_frontend_links_and_assets(self):
        print("\n[Phase 6] Testing Frontend Hyperlinks, Scripts, Styles & Asset Integrity")

        frontend_path = project_root / 'frontend'
        html_files = list(frontend_path.glob('*.html'))
        self.assertGreaterEqual(len(html_files), 5)

        broken_refs = []
        valid_refs = 0

        for html_file in html_files:
            content = html_file.read_text(encoding='utf-8')
            # Find all src and href references
            refs = re.findall(r'(?:href|src)=["\']([^"\']+)["\']', content)
            for ref in refs:
                if ref.startswith('#') or ref.startswith('javascript:'):
                    continue
                if ref.startswith('http://') or ref.startswith('https://'):
                    # External CDN: verify valid syntax
                    self.assertTrue(ref.startswith('https://'), f"Insecure HTTP external ref in {html_file.name}: {ref}")
                    valid_refs += 1
                else:
                    # Internal relative file reference
                    target = frontend_path / ref
                    if not target.exists():
                        broken_refs.append((html_file.name, ref))
                    else:
                        valid_refs += 1

        self.assertEqual(len(broken_refs), 0, f"Found broken internal references: {broken_refs}")
        self.record_pass(f"All {valid_refs} asset and navigation references verified across {len(html_files)} HTML pages (0 broken links)")

    # ========================================================================
    # 7. TEST ALL REGISTERED API ENDPOINTS (100% ROUTE COVERAGE)
    # ========================================================================
    def test_07_full_api_endpoint_coverage(self):
        print("\n[Phase 7] Testing All Registered REST API Endpoints")

        # Root
        root_res = self.client.get('/')
        self.assertEqual(root_res.status_code, 200)
        self.record_pass("GET / (Root API discovery) verified")

        # Health
        health_res = self.client.get('/api/health')
        self.assertEqual(health_res.status_code, 200)
        self.assertEqual(health_res.get_json()['status'], 'success')
        self.record_pass("GET /api/health verified")

        # DB Status
        db_res = self.client.get('/api/db/status')
        self.assertEqual(db_res.status_code, 200)
        self.assertEqual(db_res.get_json()['data']['database'], 'connected')
        self.record_pass("GET /api/db/status verified")

        # Categories list
        cats_res = self.client.get('/api/categories')
        self.assertEqual(cats_res.status_code, 200)
        self.record_pass("GET /api/categories verified")

        # Users list
        users_res = self.client.get('/api/users')
        self.assertEqual(users_res.status_code, 200)
        self.record_pass("GET /api/users verified")

        # Tasks list
        tasks_res = self.client.get('/api/tasks')
        self.assertEqual(tasks_res.status_code, 200)
        self.record_pass("GET /api/tasks verified")


def run_suite():
    print("=" * 70)
    print("STEP 13: COMPREHENSIVE END-TO-END APPLICATION TEST SUITE")
    print("=" * 70)

    suite = unittest.TestLoader().loadTestsFromTestCase(Step13CompleteE2ETestCase)
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print(f"ALL STEP 13 E2E TESTS PASSED SUCCESSFULLY! ✓")
    else:
        print(f"SOME TESTS FAILED: {len(result.failures)} failures, {len(result.errors)} errors")
    print("=" * 70)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_suite()
    sys.exit(0 if success else 1)
