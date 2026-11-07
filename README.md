# TaskFlow — Student Task Management System

A production-grade, full-stack web application designed for students to organize academic coursework, track assignment deadlines, prioritize study deliverables, and monitor daily productivity through interactive analytics.

---

## 📖 1. Project Overview

**TaskFlow** is a modern, responsive full-stack task management platform built from the ground up to solve the challenges students face when juggling coursework across multiple classes, semesters, and project teams.

This project demonstrates the complete engineering lifecycle of a professional web application:
- **Frontend Development:** Responsive, accessible UI engineered with semantic HTML5, modern CSS3 variables, Vanilla JavaScript (ES6+), and Bootstrap 5.3.
- **Backend Architecture:** Robust Python Flask backend organized into modular application factories, database access layers, and Flask Blueprints.
- **RESTful API Design:** Standardized JSON endpoints covering CRUD operations for Tasks, Categories, and Users with consistent HTTP response conventions.
- **SQL Database Management:** Relational database design using SQLite with foreign-key constraint enforcement, cascade deletion, and automated idempotent seeding.
- **Full CRUD Operations:** Seamless Create, Read, Update, and Delete workflows backed by database persistence.
- **Authentication & Security:** Werkzeug password hashing (`scrypt`), session-based authentication, signed Bearer tokens, and input sanitization.
- **Multi-User Data Isolation:** Strict authorization boundaries guaranteeing that each student only accesses their own academic records.
- **Dashboard Analytics:** Real-time metrics and dynamic data visualizations powered by Chart.js with zero full-page reloads.
- **Responsive & Accessible UI:** Seamless layout transitions across desktop, laptop, tablet, and mobile viewports with WCAG 2.1 AA keyboard navigation.
- **Deployment Ready:** Clean environment configuration supporting zero-downtime cloud hosting.

---

## 🎯 2. Problem Statement

Students frequently manage assignments, exams, laboratory reports, club commitments, and personal milestones across disparate tools—such as paper notebooks, messaging apps, spreadsheets, and calendar reminders. 

This fragmented approach leads to:
1. **Missed Deadlines:** Overdue assignments slip through the cracks without unified chronological tracking.
2. **Prioritization Paralysis:** Inability to visualize which tasks require immediate attention versus those scheduled for later.
3. **Lack of Progress Visibility:** Absence of analytics to measure completed coursework and academic momentum.

**TaskFlow** provides a centralized, student-centric workspace to create, categorize, prioritize, track, and complete academic deliverables in real time.

---

## 🚀 3. Project Objectives

- Build a production-grade full-stack web application adhering to modern software engineering principles.
- Create an intuitive, accessible, and mobile-responsive frontend without heavy external UI frameworks.
- Implement a modular Python Flask backend with clear separation of concerns.
- Expose a clean, standardized REST API with comprehensive status code conventions.
- Design and integrate a normalized SQL relational schema with foreign-key constraints.
- Implement complete CRUD operations across all core domain entities.
- Enforce robust authentication and authorization with multi-user data isolation.
- Provide real-time client-side task search and multi-criteria filtering.
- Compute and render interactive analytics and statistics for study workload insights.
- Provide end-to-end automated testing and cloud-ready configuration.

---

## ✨ 4. Main Features

Only features that physically exist in the codebase are documented below:

### 🔐 Authentication & Account Management
- **User Registration:** Simple account creation with full name, student email, and password (minimum 6 characters).
- **Secure Password Hashing:** Passwords encrypted using Werkzeug's `scrypt` algorithm before database storage. Plaintext passwords are never stored or logged.
- **Dual Authentication Modes:** Supports both traditional cookie sessions and signed Bearer auth tokens.
- **Session Management & Logout:** Dedicated logout endpoint that destroys the session and clears client-side tokens.
- **1-Click Demo Login:** Quick evaluation button to instantly sign in with pre-configured student credentials.
- **Protected Endpoints:** Built-in `@login_required` route decorator preventing unauthorized access.

### 📝 Task Management (CRUD)
- **Task Creation:** Add tasks with Title, Description, Category, Priority, Status, and Due Date.
- **Task Editing:** Update task properties in-place via an intuitive modal form.
- **Task Deletion:** Safe deletion with an interactive confirmation modal to prevent accidental data loss.
- **Completion Checkbox:** 1-click status toggle directly from the task list and dashboard.
- **Priority Urgency Tags:** Tag tasks as `Low`, `Medium`, `High`, or `Urgent` with color-coded badges.
- **Lifecycle Statuses:** Track work progression across `Pending`, `In Progress`, `Completed`, and `Cancelled`.
- **Calendar Due Dates:** Standardized `YYYY-MM-DD` date picker with server-side validation against invalid calendar days.

### 🔍 Search & Filtering
- **Live Search:** Instant client-side search across task titles, descriptions, and category names.
- **Status Filter Group:** Toggle between `All`, `Pending`, `In Progress`, and `Completed`.
- **Priority Filter Dropdown:** Filter by `Urgent`, `High`, `Medium`, or `Low`.
- **Category Filter Dropdown:** Dynamically populated category selector.
- **Keyboard Shortcut (`Ctrl + K` / `Cmd + K`):** Global hotkey to instantly focus the search input from anywhere in the app.

### 📊 Dashboard Analytics & Visualizations
- **6 Real-Time Metric Cards:**
  - `Total Tasks`: Complete tally of all user coursework.
  - `Completed`: Number of finished tasks with completion percentage.
  - `In Progress`: Active assignments currently underway.
  - `Pending`: Queued deliverables waiting to be started.
  - `High Priority`: Aggregation of High and Urgent tasks requiring focus.
  - `Overdue`: Immediate alert count for deliverables where `due_date < today AND status != 'Completed'`.
- **3 Chart.js Visualizations:**
  1. *Task Status Breakdown (Doughnut):* Visualizes workload distribution across statuses.
  2. *Priority Distribution (Bar):* Bar chart displaying task volume by urgency level.
  3. *Category Workload (Doughnut):* Distribution of tasks across academic categories.
- **Upcoming Deadlines Widget:** Chronologically sorted list of impending assignments with relative due date badges (`Due Today`, `Tomorrow`, `In X Days`, `Overdue`).
- **Recent Tasks (Latest 5):** Quick-glance view of the five most recent tasks with inline status toggles.
- **Zero Full-Page Reloads:** All metrics, charts, and tables update in-place upon any task creation, edit, toggle, or deletion.

### 📂 Category Management
- **Pre-Seeded Academic Categories:** Automatically seeds `Study`, `Personal`, `Work`, `Project`, and `Other` on initialization.
- **Color Coding:** Hex-based color badges associated with each category for rapid visual scanning.
- **Referential Integrity:** Deleting a category automatically sets task references to `NULL` without deleting tasks.

### 📱 Responsive & Accessible UI
- **Viewport Adaptability:** Tailored layouts for Desktop (1200px+), Laptop (992px), Tablet (768px), and Mobile (<768px).
- **Navigation:** Sticky sidebar on desktop; smooth offcanvas slide-out drawer on tablet and mobile.
- **Touch-Friendly Tables:** Wrapped inside responsive containers with custom thin scrollbars to prevent viewport clipping.
- **Accessibility (WCAG 2.1 AA):** High-contrast focus rings (`:focus-visible`), explicit `<label for="...">` bindings, semantic table headers (`scope="col"`), and screen-reader labels.

---

## 🛠️ 5. Technology Stack

| Layer | Technology | Purpose & Description |
|---|---|---|
| **Frontend Language** | HTML5, CSS3, JavaScript (ES6+) | Semantic markup, custom design tokens, modern fetch client |
| **UI Framework** | Bootstrap 5.3.3 | Responsive grid, modal dialogs, offcanvas sidebar |
| **Icons** | Bootstrap Icons 1.11.3 | Clean iconography across sidebar, tables, and buttons |
| **Data Visualization** | Chart.js | Interactive HTML5 Canvas doughnut and bar charts |
| **Backend Language** | Python 3.10+ | Server-side runtime and application logic |
| **Web Framework** | Flask 3.0+ | Lightweight WSGI web framework and Blueprint routing |
| **CORS Middleware** | Flask-CORS 4.0+ | Cross-Origin Resource Sharing with credential support |
| **Security & Hashing** | Werkzeug | Secure `scrypt` password hashing and verification |
| **Token Serialization** | itsdangerous | Cryptographically signed URL-safe Bearer authentication tokens |
| **Configuration** | python-dotenv | Environment variable management from `.env` |
| **Database** | SQLite 3 | Serverless, relational, ACID-compliant SQL database |
| **Query Engine** | Parameterized SQL | 100% parameterized queries via Python's native `sqlite3` |
| **Testing** | `unittest` & Node.js | Automated unit, security, integration, and E2E suites |
| **Version Control** | Git | Distributed source control management |
| **Target Repository** | GitHub | [Malik2627/Full-Stack-Web-Application-Development-Project](https://github.com/Malik2627/Full-Stack-Web-Application-Development-Project) |
| **Target Deployment** | Render / Railway / PythonAnywhere | Cloud WSGI hosting ready |

---

## 🏗️ 6. System Architecture

TaskFlow uses a clean, decoupled 3-tier client-server architecture:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION TIER                             │
│       HTML5 + CSS3 + Bootstrap 5 + Vanilla JavaScript (ES6+)           │
│                                                                        │
│   [ dashboard.html ]    [ tasks.html ]    [ login.html / register.html ]
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP Requests (Fetch API)
                                    │ JSON Payloads + Bearer Tokens
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          APPLICATION TIER                              │
│                    Python 3 + Flask REST API                           │
│                                                                        │
│   • Blueprint Routing (`routes.py`)                                    │
│   • Auth & Session Management (`@login_required`)                      │
│   • Input Validation & Sanitization (`validators.py`)                  │
│   • Centralized Error Handlers (400, 401, 403, 404, 409, 500)          │
│   • Business Logic & Domain Models (`models.py`)                       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Parameterized SQL Queries
                                    │ (PRAGMA foreign_keys = ON)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                            DATA TIER                                   │
│                        SQLite Database                                 │
│                                                                        │
│   • Table: `users`      (Student accounts & hashed credentials)        │
│   • Table: `categories` (Workload groupings & colors)                  │
│   • Table: `tasks`      (Deliverables, priorities, statuses, dates)    │
│                                                                        │
│   Physical File: `database/taskflow.db`                                │
└────────────────────────────────────────────────────────────────────────┘
```

### Architectural Flow:
1. **User Action:** The student triggers an action in the browser (e.g. creating a task or changing a filter).
2. **Client Service (`frontend/js/api.js`):** Vanilla JS formats the request, attaches the auth token or session cookie, and triggers an asynchronous `fetch()` call.
3. **API Routing (`backend/routes.py`):** Flask matches the endpoint and verifies user identity via session or Bearer token.
4. **Validation Layer (`backend/validators.py`):** Payload fields are validated for required fields, length limits, allowed domain values, and calendar date validity.
5. **Data Access Layer (`backend/models.py`):** Executes parameterized SQL queries against `taskflow.db` with foreign keys enabled.
6. **JSON Serialization:** The controller constructs a standardized response envelope (`status`, `message`, `data`).
7. **DOM Mutation (`frontend/js/main.js`):** The client dynamically renders updated HTML tables and refreshes Chart.js canvases in-place without page reloads.

---

## 🗄️ 7. Database Design

The relational database is persisted in `database/taskflow.db`. Foreign-key enforcement is enabled on every connection via `PRAGMA foreign_keys = ON;`.

### Entity-Relationship Diagram

```text
  ┌──────────────┐                 ┌──────────────┐
  │    users     │                 │  categories  │
  ├──────────────┤                 ├──────────────┤
  │ id (PK)      │                 │ id (PK)      │
  │ name         │                 │ name         │
  │ email        │                 │ color        │
  │ password     │                 │ created_at   │
  │ created_at   │                 └──────┬───────┘
  └──────┬───────┘                        │
         │ 1                              │ 1
         │                                │
         │ *                              │ *
  ┌──────┴────────────────────────────────┴───────┐
  │                    tasks                      │
  ├───────────────────────────────────────────────┤
  │ id (PK)                                       │
  │ user_id (FK -> users.id, ON DELETE CASCADE)   │
  │ category_id (FK -> categories.id, SET NULL)   │
  │ title                                         │
  │ description                                   │
  │ priority ('Low','Medium','High','Urgent')     │
  │ status ('Pending','In Progress','Completed')  │
  │ due_date                                      │
  │ created_at                                    │
  │ updated_at                                    │
  └───────────────────────────────────────────────┘
```

### Table Schemas

#### 1. `users` Table
Stores student account details and hashed credentials.
```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. `categories` Table
Stores organizational categories for grouping student tasks.
```sql
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    color VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. `tasks` Table
Stores assignment deliverables, milestones, and homework tasks.
```sql
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
```

---

## 🔄 8. CRUD Operations Mapping

TaskFlow strictly maps standard HTTP verbs to domain operations:

| Operation | HTTP Verb | Endpoint | Description |
|---|:---:|---|---|
| **Create** | `POST` | `/api/tasks` | Inserts a new task bound to the authenticated student |
| **Read** | `GET` | `/api/tasks` | Retrieves all tasks owned by the current student |
| **Read (Single)** | `GET` | `/api/tasks/<id>` | Retrieves full details of a specific task |
| **Update** | `PUT` | `/api/tasks/<id>` | Updates title, status, priority, description, or due date |
| **Delete** | `DELETE` | `/api/tasks/<id>` | Permanently removes a task record |

---

## 📡 9. REST API Documentation

All API endpoints return standardized JSON payloads:
```json
{
  "status": "success",
  "message": "Description of action taken",
  "data": {}
}
```

### Complete Endpoints Reference

| Method | Endpoint | Auth Required | Description | Status Code |
|---|---|:---:|---|:---:|
| `GET` | `/` | No | API service discovery and online status check | `200` |
| `GET` | `/api/health` | No | Basic health check service verification | `200` |
| `GET` | `/api/db/status` | No | Database connectivity and seeded table status | `200` |
| `POST` | `/api/auth/register` | No | Register a new user (`name`, `email`, `password`) | `201`, `400`, `409` |
| `POST` | `/api/auth/login` | No | Authenticate user credentials and issue session/token | `200`, `400`, `401` |
| `GET` | `/api/auth/me` | **Yes** | Retrieve currently authenticated user profile | `200`, `401` |
| `POST` | `/api/auth/logout` | No | Clear active user session and logout | `200` |
| `GET` | `/api/tasks` | Optional | Retrieve student tasks (supports `status`, `priority`, `category_id`) | `200` |
| `POST` | `/api/tasks` | Optional | Create a task (auto-binds to logged-in user) | `201`, `400` |
| `GET` | `/api/tasks/<id>` | Optional | Retrieve single task by ID (enforces ownership) | `200`, `403`, `404` |
| `PUT` | `/api/tasks/<id>` | Optional | Update task fields (disallows transferring ownership) | `200`, `400`, `403`, `404` |
| `DELETE` | `/api/tasks/<id>` | Optional | Delete task (enforces ownership) | `200`, `403`, `404` |
| `GET` | `/api/categories` | No | Retrieve all task categories | `200` |
| `POST` | `/api/categories` | No | Create a category (`name`, `color`) | `201`, `400`, `409` |
| `GET` | `/api/categories/<id>` | No | Retrieve single category by ID | `200`, `404` |
| `PUT` | `/api/categories/<id>` | No | Update category name and/or color | `200`, `400`, `404`, `409` |
| `DELETE` | `/api/categories/<id>` | No | Delete category (sets `tasks.category_id = NULL`) | `200`, `404` |
| `GET` | `/api/users` | No | Retrieve user list (passwords stripped) | `200` |
| `POST` | `/api/users` | No | Basic user creation helper | `201`, `400`, `409` |
| `GET` | `/api/users/<id>` | No | Retrieve single user by ID | `200`, `404` |
| `PUT` | `/api/users/<id>` | No | Update user profile | `200`, `400`, `404`, `409` |
| `DELETE` | `/api/users/<id>` | No | Delete user (cascades to user tasks) | `200`, `404` |

---

## 💻 10. Frontend Pages & Views

| Page | File | Description |
|---|---|---|
| **Landing Page** | [`frontend/index.html`](file:///D:/Task-flow/frontend/index.html) | Welcome banner, hero presentation, core features, full-stack architecture summary, and live backend connection health indicator badge. |
| **Sign In** | [`frontend/login.html`](file:///D:/Task-flow/frontend/login.html) | Student login form with real-time email validation, password show/hide toggle, and a 1-click **Demo Student Fill** button. |
| **Registration** | [`frontend/register.html`](file:///D:/Task-flow/frontend/register.html) | Student account creation form with real-time password match checks, email validation, and terms confirmation. |
| **Dashboard** | [`frontend/dashboard.html`](file:///D:/Task-flow/frontend/dashboard.html) | Central command center with 6 metric cards, 3 Chart.js graphs, Recent Tasks (latest 5), Upcoming Deadlines list, and an instant Quick Add Task form. |
| **Task Management** | [`frontend/tasks.html`](file:///D:/Task-flow/frontend/tasks.html) | Complete coursework interface featuring live search, multi-criteria filter toolbar, interactive task table, completion checkboxes, and action buttons. |

### Modal Dialogs
- **Add / Edit Task Modal:** Dual-mode modal for creating and updating tasks with validation feedback.
- **Delete Confirmation Modal:** Protects users by requiring explicit confirmation before permanent task removal.
- **Categories Modal:** Displays active categories with their associated hex theme colors.
- **Settings Modal:** Displays active student profile information and API configuration.

---

## 📂 11. Project Directory Structure

```text
D:\Task-flow
│
├── frontend/                       # Client-side presentation tier
│   ├── index.html                  # Landing page with live backend health monitor
│   ├── dashboard.html              # Main analytics dashboard & metric cards
│   ├── tasks.html                  # Full task management interface (CRUD & filters)
│   ├── login.html                  # Student sign in page with demo credentials
│   ├── register.html               # New student account registration page
│   ├── test_analytics_matrix.js    # Node.js automated analytics verification test
│   ├── css/
│   │   └── style.css               # Design system, CSS variables, responsive layout
│   └── js/
│       ├── api.js                  # Centralized REST API client (Fetch API)
│       └── main.js                 # UI controller, Chart.js integrations, live events
│
├── backend/                        # Server-side application tier
│   ├── app.py                      # Flask application factory, CORS & error handlers
│   ├── config.py                   # Environment configuration loader (.env support)
│   ├── database.py                 # SQLite connection manager, table creator & seeders
│   ├── models.py                   # Data access layer & SQL helper functions
│   ├── routes.py                   # Flask Blueprint REST API endpoints & auth decorators
│   ├── validators.py               # Input validation, domain checks & calendar date validators
│   ├── requirements.txt            # Python dependencies (Flask, Flask-CORS, python-dotenv)
│   ├── test_api.py                 # REST API CRUD & validation test suite (36 tests)
│   ├── test_auth.py                # Password hashing & auth session test suite (28 tests)
│   ├── test_db.py                  # Database integrity & schema test suite (6 tests)
│   ├── test_step7_analytics.py     # Analytics & statistics integration tests (25 tests)
│   ├── test_step9_security.py      # Multi-user data isolation test suite (26 tests)
│   ├── test_step10_validation.py   # Application validation & error handling tests (27 tests)
│   └── test_step13_e2e.py          # End-to-end full application test suite (33 tests)
│
├── database/                       # Physical database storage
│   └── taskflow.db                 # SQLite physical database file
│
├── .env.example                    # Sample environment variables template
├── .gitignore                      # Git ignore rules for Python, DB, and environment files
└── README.md                       # Comprehensive project documentation
```

---

## ⚙️ 12. Local Installation & Setup

Follow these steps to run TaskFlow locally on your development machine:

### Prerequisites
- **Python 3.10+** installed ([python.org](https://www.python.org/downloads/))
- **Git** installed ([git-scm.com](https://git-scm.com/))
- Any modern web browser (Chrome, Firefox, Edge, Safari)

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/Malik2627/Full-Stack-Web-Application-Development-Project.git
```

---

### Step 2: Navigate to Project Directory
```bash
cd Full-Stack-Web-Application-Development-Project
```

---

### Step 3: Create a Python Virtual Environment
```bash
python -m venv venv
```

---

### Step 4: Activate the Virtual Environment
- **On Windows (PowerShell):**
  ```powershell
  venv\Scripts\Activate.ps1
  ```
- **On Windows (Command Prompt):**
  ```cmd
  venv\Scripts\activate.bat
  ```
- **On macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```

---

### Step 5: Install Python Dependencies
```bash
pip install -r backend/requirements.txt
```

---

### Step 6: (Optional) Configure Environment Variables
Copy `.env.example` to `.env` if you wish to customize ports or secret keys:
```bash
copy .env.example .env
```
*(Note: TaskFlow automatically provides sensible local defaults if `.env` is omitted.)*

---

### Step 7: Start the Flask Backend Server
```bash
python backend/app.py
```
The server will initialize the SQLite database (`database/taskflow.db`), run table migrations, seed default categories, and start listening at:
```text
http://127.0.0.1:5000
```

---

### Step 8: Open the Frontend Application
Open your web browser and navigate directly to:
```text
http://127.0.0.1:5000
```
Or open [`frontend/index.html`](file:///D:/Task-flow/frontend/index.html) in your browser.

**Demo Credentials for Instant Evaluation:**
- **Email:** `alex.student@example.edu`
- **Password:** `student123`
*(Or click the **Demo Student Fill** button on the Sign In page!)*

---

## 🔒 13. Security Implementation

TaskFlow incorporates standard web application security best practices:

1. **SQL Injection Prevention:** Every database query in `models.py` and `database.py` utilizes parameterized statements (`?`). Dynamic column identifiers in `update_task()` are restricted to a strict whitelist (`allowed_fields`).
2. **Password Encryption:** Passwords are hashed with Werkzeug's `scrypt` algorithm using unique cryptographic salts. Plaintext passwords are never stored in SQLite and are stripped before returning JSON responses.
3. **Session & Cookie Security:**
   - `SESSION_COOKIE_HTTPONLY = True`: Blocks client-side JavaScript access to cookies, mitigating Cross-Site Scripting (XSS) session theft.
   - `SESSION_COOKIE_SAMESITE = 'Lax'`: Mitigates Cross-Site Request Forgery (CSRF).
   - `SESSION_COOKIE_SECURE`: Configurable via `.env` for production HTTPS.
4. **Data Isolation (Access Control):** The backend extracts user ID strictly from the verified session or signed token. Cross-user modification, deletion, or viewing attempts return `403 Forbidden`.
5. **Information Masking:** Centralized error handlers intercept uncaught exceptions and return friendly JSON messages, strictly suppressing Python stack traces and database internals.
6. **Input Validation:** Input constraints validate email format, password length (6+ characters), allowed status/priority domains, and real calendar dates (detecting non-existent days like February 31st).

---

## 🧪 14. Testing & Verification

TaskFlow includes an extensive automated test suite covering unit tests, security assertions, analytics logic, and end-to-end user flows.

### Automated Test Battery Results

```text
======================================================================
1. Step 13 Comprehensive End-to-End Suite  (test_step13_e2e.py)        : 33/33 PASSED ✓
2. Step 10 Validation & Error Handling      (test_step10_validation.py) : 27/27 PASSED ✓
3. Step 9 Multi-User Isolation & Security   (test_step9_security.py)    : 26/26 PASSED ✓
4. Step 8 User Authentication & Passwords   (test_auth.py)              : 28/28 PASSED ✓
5. Step 7 Analytics Integration Test        (test_step7_analytics.py)   : 25/25 PASSED ✓
6. Step 7 Analytics Scenario Matrix (Node)  (test_analytics_matrix.js)  : 16/16 PASSED ✓
7. Step 3 REST API CRUD Operations          (test_api.py)               : 36/36 PASSED ✓
8. Step 2 Database Schema & Seeding         (test_db.py)                :  6/6  PASSED ✓
======================================================================
TOTAL AUTOMATED TEST ASSERTIONS: 197 / 197 PASSED (100% SUCCESS RATE)
======================================================================
```

### Feature Verification Summary

| Feature / Domain | Test Suite | Status | Notes |
|---|---|:---:|---|
| **User Registration** | `test_auth.py`, `test_step13_e2e.py` | **PASSED** | Validates email format, password length, hashes password, returns 201 |
| **User Login** | `test_auth.py`, `test_step13_e2e.py` | **PASSED** | Verifies credentials via `check_password_hash`, creates session |
| **Wrong Password Rejection** | `test_auth.py`, `test_step13_e2e.py` | **PASSED** | Returns 401 Unauthorized with sanitized error message |
| **Duplicate Email Prevention** | `test_auth.py`, `test_step10_validation.py` | **PASSED** | Returns 409 Conflict when registering an existing email |
| **User Logout** | `test_auth.py`, `test_step9_security.py` | **PASSED** | Clears session cookie and invalidates client state |
| **Protected Route Enforcement** | `test_auth.py`, `test_step13_e2e.py` | **PASSED** | Unauthenticated `/api/auth/me` returns 401 Unauthorized |
| **Task Creation** | `test_api.py`, `test_step13_e2e.py` | **PASSED** | Inserts task bound to authenticated student; returns 201 Created |
| **Task Reading (Single & List)** | `test_api.py`, `test_step9_security.py` | **PASSED** | Retrieves scoped tasks with joined user and category data |
| **Task Update** | `test_api.py`, `test_step9_security.py` | **PASSED** | In-place update of fields; prevents reassigning ownership |
| **Task Deletion** | `test_api.py`, `test_step9_security.py` | **PASSED** | Removes task; subsequent lookup confirms 404 Not Found |
| **Cross-User Data Isolation** | `test_step9_security.py` | **PASSED** | User A cannot access, edit, or delete User B's tasks (403 Forbidden) |
| **Task Search & Filtering** | `test_api.py`, `test_step13_e2e.py` | **PASSED** | Filters by status, priority, category; client-side real-time search |
| **Calendar Date Validation** | `test_step10_validation.py` | **PASSED** | Rejects non-existent calendar days (e.g. 2026-02-31) |
| **Categories Management** | `test_api.py`, `test_db.py` | **PASSED** | Complete CRUD; duplicate names rejected with 409 Conflict |
| **Dashboard Statistics** | `test_step7_analytics.py`, `test_analytics_matrix.js` | **PASSED** | Accurately aggregates Total, Completed, In Progress, Pending |
| **Overdue Detection** | `test_step7_analytics.py`, `test_analytics_matrix.js` | **PASSED** | Accurately identifies `due_date < today AND status != 'Completed'` |
| **Database Persistence** | `test_step13_e2e.py` | **PASSED** | Physical disk durability verified across simulated server restarts |
| **Asset & Link Integrity** | `test_step13_e2e.py` | **PASSED** | All 66 internal assets and links verified (0 broken links) |

### Running the Test Suites Locally
Run all test suites with a single command:
```bash
python backend/test_step13_e2e.py
python backend/test_step10_validation.py
python backend/test_step9_security.py
python backend/test_auth.py
python backend/test_api.py
python backend/test_step7_analytics.py
python backend/test_db.py
node frontend/test_analytics_matrix.js
```

---

## 📸 15. Screenshots

*Placeholder section for project presentation screenshots:*

1. **Home / Landing Page**  
   ![Home Page Placeholder](https://via.placeholder.com/800x450/4f46e5/ffffff?text=TaskFlow+Landing+Page)  
   *Hero banner with student task management overview and live backend API status badge.*

2. **Student Sign In**  
   ![Sign In Placeholder](https://via.placeholder.com/800x450/0f172a/ffffff?text=Student+Sign+In+Page)  
   *Authentication form with password visibility toggle and 1-click Demo Student Fill.*

3. **Student Registration**  
   ![Registration Placeholder](https://via.placeholder.com/800x450/0f172a/ffffff?text=Student+Registration+Page)  
   *Account registration form with real-time field validation.*

4. **Dashboard & Analytics**  
   ![Dashboard Overview Placeholder](https://via.placeholder.com/800x450/4f46e5/ffffff?text=Dashboard+Analytics+and+Metrics)  
   *Real-time statistics cards, upcoming deadlines widget, and recent tasks.*

5. **Visual Charts (Chart.js)**  
   ![Charts Placeholder](https://via.placeholder.com/800x450/10b981/ffffff?text=Interactive+Chart.js+Analytics)  
   *Task status doughnut chart, priority distribution bar chart, and category workload chart.*

6. **Task Management Table**  
   ![Task Table Placeholder](https://via.placeholder.com/800x450/0ea5e9/ffffff?text=Task+Management+Interface)  
   *Interactive coursework deliverables table with search box and filter button group.*

7. **Add / Edit Task Modal**  
   ![Modal Placeholder](https://via.placeholder.com/800x450/8b5cf6/ffffff?text=Add+and+Edit+Task+Modal)  
   *Form modal for creating and updating assignment titles, priorities, categories, and due dates.*

8. **Mobile Responsive View**  
   ![Mobile View Placeholder](https://via.placeholder.com/400x700/4f46e5/ffffff?text=Mobile+Offcanvas+Drawer)  
   *Mobile viewport layout featuring slide-out offcanvas drawer and touch-friendly controls.*

---

## 🌐 16. Deployment Status

- **Local Development & Testing:** Fully operational (`http://127.0.0.1:5000`)
- **Target GitHub Repository:** [Malik2627/Full-Stack-Web-Application-Development-Project](https://github.com/Malik2627/Full-Stack-Web-Application-Development-Project)
- **Live Demo:** `Coming soon` *(Cloud deployment will be executed in subsequent release stages)*

---

## 🔮 17. Future Enhancements

Potential extensions planned for future iterations of TaskFlow:
- **Email Due Date Reminders:** Automated notification emails for assignments due within 24 hours.
- **Calendar Integration:** Export tasks and deadlines as `.ics` feeds compatible with Google Calendar and Apple Calendar.
- **Kanban Board View:** Drag-and-drop board view organized by `Pending`, `In Progress`, and `Completed`.
- **Dark Mode Theme:** User-toggleable dark theme using CSS variables.
- **Recurring Deliverables:** Support for recurring weekly homework, quizzes, and lab sessions.
- **File Attachments:** Uploading assignment PDFs, lecture notes, or project specifications.
- **Progressive Web App (PWA):** Offline support and home-screen installation on iOS and Android devices.

---

## 🎓 18. Conclusion

**TaskFlow** represents a comprehensive demonstration of the full-stack software development lifecycle:

```text
    Planning & Requirements
              ↓
    Relational Database Design (SQLite)
              ↓
    RESTful API Architecture (Python / Flask)
              ↓
    Security & Authentication (Werkzeug / Sessions)
              ↓
    Frontend Engineering (HTML5 / CSS3 / Vanilla JS)
              ↓
    UI Polish, Accessibility & Responsiveness (Bootstrap 5)
              ↓
    Automated Testing (197 / 197 Assertions Passed)
              ↓
    Cloud Deployment Preparation
```

By unifying academic assignment organization, deadline tracking, visual analytics, and multi-user data isolation into a lightweight, high-performance web application, TaskFlow provides an intuitive, robust tool built specifically for student productivity.

---

## 📄 License & Attribution

Developed as a student full-stack web application project. Built with Python, Flask, SQLite, Vanilla JavaScript, and Bootstrap 5.
