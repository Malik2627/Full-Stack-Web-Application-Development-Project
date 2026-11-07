"""
Step 7 Analytics Integration Test Suite
----------------------------------------
Tests Flask REST API + SQLite integration across all 5 required Step 7 scenarios:
1. 0 tasks
2. 1 task
3. Multiple tasks
4. Completed tasks
5. Overdue tasks
Also tests dynamic in-place updates (creating, updating status, and deleting tasks).
"""

import sys
import json
from datetime import date, timedelta
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import app
from database import get_db_connection


class AnalyticsIntegrationTester:
    def __init__(self):
        self.client = app.test_client()
        self.passed = 0
        self.total = 0

    def assert_true(self, condition, name, details=""):
        self.total += 1
        if condition:
            self.passed += 1
            print(f"  ✓ [{self.passed}] {name}")
        else:
            print(f"  ✗ FAILED: {name} - {details}")
            raise AssertionError(f"{name}: {details}")

    def clean_tasks_table(self):
        """Cleans only tasks table for pristine state testing."""
        conn = get_db_connection()
        conn.execute("DELETE FROM tasks;")
        conn.commit()
        conn.close()

    def get_tasks_from_api(self):
        res = self.client.get('/api/tasks')
        data = res.get_json()
        return data.get('data', [])

    def calculate_stats(self, tasks):
        today = date.today()
        total = len(tasks)
        completed = len([t for t in tasks if t['status'] == 'Completed'])
        in_progress = len([t for t in tasks if t['status'] == 'In Progress'])
        pending = len([t for t in tasks if t['status'] == 'Pending'])
        high_priority = len([t for t in tasks if (t.get('priority') or '').lower() in ('high', 'urgent')])
        
        overdue = 0
        for t in tasks:
            if t.get('due_date') and t.get('status') != 'Completed':
                due = date.fromisoformat(t['due_date'].split('T')[0])
                if due < today:
                    overdue += 1

        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "high_priority": high_priority,
            "overdue": overdue
        }

    def ensure_user(self):
        """Ensures at least one user exists and returns the ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users LIMIT 1;")
        row = cursor.fetchone()
        if row:
            user_id = row['id']
        else:
            cursor.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?);",
                ("Alex Johnson", "alex.student@example.edu", "password123")
            )
            conn.commit()
            user_id = cursor.lastrowid
        conn.close()
        return user_id

    def run(self):
        print("=" * 70)
        print("STEP 7 INTEGRATION TEST: FLASK REST API + SQLITE + ANALYTICS")
        print("=" * 70)

        user_id = self.ensure_user()

        # --------------------------------------------------------------------
        # Scenario 1: 0 Tasks
        # --------------------------------------------------------------------
        print("\n[Scenario 1] Testing with 0 Tasks (Pristine Database)")
        self.clean_tasks_table()
        tasks = self.get_tasks_from_api()
        self.assert_true(len(tasks) == 0, "GET /api/tasks returns empty array")
        stats = self.calculate_stats(tasks)
        self.assert_true(stats["total"] == 0, "Total tasks is 0")
        self.assert_true(stats["completed"] == 0, "Completed tasks is 0")
        self.assert_true(stats["pending"] == 0, "Pending tasks is 0")
        self.assert_true(stats["in_progress"] == 0, "In Progress tasks is 0")
        self.assert_true(stats["high_priority"] == 0, "High Priority tasks is 0")
        self.assert_true(stats["overdue"] == 0, "Overdue tasks is 0")

        # --------------------------------------------------------------------
        # Scenario 2: 1 Task
        # --------------------------------------------------------------------
        print("\n[Scenario 2] Testing with 1 Task")
        future_date = (date.today() + timedelta(days=2)).isoformat()
        res = self.client.post('/api/tasks', json={
            "title": "Machine Learning Lab 1",
            "description": "Implement backpropagation from scratch",
            "priority": "Medium",
            "status": "Pending",
            "due_date": future_date,
            "category_id": 1,
            "user_id": user_id
        })
        self.assert_true(res.status_code == 201, "POST /api/tasks creates single task")
        task_id = res.get_json()['data']['id']

        tasks = self.get_tasks_from_api()
        self.assert_true(len(tasks) == 1, "API returns exactly 1 task")
        stats = self.calculate_stats(tasks)
        self.assert_true(stats["total"] == 1, "Total tasks is 1")
        self.assert_true(stats["pending"] == 1, "Pending count is 1")
        self.assert_true(stats["completed"] == 0, "Completed count is 0")
        self.assert_true(stats["overdue"] == 0, "Overdue count is 0 (future date)")

        # --------------------------------------------------------------------
        # Scenario 3: Multiple Tasks (Diverse categories & priorities)
        # --------------------------------------------------------------------
        print("\n[Scenario 3] Testing with Multiple Tasks (Categories & Priorities)")
        task_samples = [
            ("Database Normalization Quiz", "High", "In Progress", (date.today() + timedelta(days=3)).isoformat(), 1),
            ("Operating Systems Project", "Urgent", "Pending", (date.today() + timedelta(days=5)).isoformat(), 3),
            ("Campus Career Fair Prep", "Low", "Pending", (date.today() + timedelta(days=7)).isoformat(), 2),
            ("Software Engineering Assignment", "High", "Pending", (date.today() + timedelta(days=10)).isoformat(), 1),
            ("Gym & Cardio Session", "Low", "In Progress", (date.today() + timedelta(days=12)).isoformat(), 4),
        ]
        for title, prio, status, due, cat_id in task_samples:
            self.client.post('/api/tasks', json={
                "title": title,
                "priority": prio,
                "status": status,
                "due_date": due,
                "category_id": cat_id,
                "user_id": user_id
            })

        tasks = self.get_tasks_from_api()
        self.assert_true(len(tasks) == 6, f"API returns 6 total tasks (got {len(tasks)})")
        stats = self.calculate_stats(tasks)
        self.assert_true(stats["total"] == 6, "Total tasks is 6")
        self.assert_true(stats["pending"] == 4, f"Pending tasks count is 4 (got {stats['pending']})")
        self.assert_true(stats["in_progress"] == 2, f"In Progress tasks count is 2 (got {stats['in_progress']})")
        # High priority (High + Urgent): Machine Learning(Medium), DB Normalization(High), OS Project(Urgent), Career(Low), SE(High), Gym(Low) -> 3
        self.assert_true(stats["high_priority"] == 3, f"High priority count is 3 (got {stats['high_priority']})")
        self.assert_true(stats["overdue"] == 0, "Overdue count is 0 for future dates")

        # --------------------------------------------------------------------
        # Scenario 4: Completed Tasks
        # --------------------------------------------------------------------
        print("\n[Scenario 4] Testing with Completed Tasks")
        # Mark 2 tasks as Completed via PUT /api/tasks/<id>
        self.client.put(f'/api/tasks/{task_id}', json={"status": "Completed"})
        second_task_id = tasks[1]['id']
        self.client.put(f'/api/tasks/{second_task_id}', json={"status": "Completed"})

        tasks = self.get_tasks_from_api()
        stats = self.calculate_stats(tasks)
        self.assert_true(stats["completed"] == 2, f"Completed tasks count is 2 (got {stats['completed']})")
        completion_pct = round((stats["completed"] / stats["total"]) * 100)
        self.assert_true(completion_pct == 33, f"Completion percentage is 33% (got {completion_pct}%)")

        # --------------------------------------------------------------------
        # Scenario 5: Overdue Tasks (due_date < today AND status != Completed)
        # --------------------------------------------------------------------
        print("\n[Scenario 5] Testing Overdue Tasks (Identification & Resolution)")
        past_date_3d = (date.today() - timedelta(days=3)).isoformat()
        past_date_1d = (date.today() - timedelta(days=1)).isoformat()

        # Add 2 tasks with past due dates
        res1 = self.client.post('/api/tasks', json={
            "title": "Overdue Cloud Computing Essay",
            "priority": "High",
            "status": "Pending",
            "due_date": past_date_3d,
            "category_id": 1,
            "user_id": user_id
        })
        overdue_id_1 = res1.get_json()['data']['id']

        res2 = self.client.post('/api/tasks', json={
            "title": "Overdue Compiler Lab Submission",
            "priority": "Urgent",
            "status": "In Progress",
            "due_date": past_date_1d,
            "category_id": 3,
            "user_id": user_id
        })
        overdue_id_2 = res2.get_json()['data']['id']

        tasks = self.get_tasks_from_api()
        stats = self.calculate_stats(tasks)
        self.assert_true(stats["overdue"] == 2, f"Overdue count is 2 (got {stats['overdue']})")

        # Now mark overdue_id_1 as Completed -> overdue count must drop to 1
        self.client.put(f'/api/tasks/{overdue_id_1}', json={"status": "Completed"})
        tasks = self.get_tasks_from_api()
        stats = self.calculate_stats(tasks)
        self.assert_true(stats["overdue"] == 1, f"Overdue count drops to 1 after completion (got {stats['overdue']})")

        # Now delete overdue_id_2 via DELETE /api/tasks/<id> -> overdue count must drop to 0
        del_res = self.client.delete(f'/api/tasks/{overdue_id_2}')
        self.assert_true(del_res.status_code == 200, "DELETE /api/tasks removes task in-place")
        tasks = self.get_tasks_from_api()
        stats = self.calculate_stats(tasks)
        self.assert_true(stats["overdue"] == 0, f"Overdue count drops to 0 after deletion (got {stats['overdue']})")

        print("=" * 70)
        print(f"ALL {self.passed}/{self.total} STEP 7 INTEGRATION TESTS PASSED! ✓")
        print("=" * 70)


if __name__ == "__main__":
    tester = AnalyticsIntegrationTester()
    tester.run()
