/**
 * TaskFlow API Service
 * Centralized client for communicating with the Flask REST API.
 * Uses fetch() for all asynchronous network requests.
 */

const TaskFlowAPI = (() => {
    // Single centralized API base configuration for local Flask backend
    const BASE_URL = (() => {
        if (typeof window !== 'undefined' && window.TASKFLOW_API_URL) {
            return window.TASKFLOW_API_URL;
        }
        if (typeof window !== 'undefined' && window.location && window.location.origin && window.location.origin.includes(':5000')) {
            return `${window.location.origin}/api`;
        }
        return 'http://127.0.0.1:5000/api';
    })();

    // Storage keys for authentication (passwords are NEVER stored)
    const TOKEN_KEY = 'taskflow_auth_token';
    const USER_KEY = 'taskflow_auth_user';

    function getStoredToken() {
        if (typeof localStorage !== 'undefined') {
            return localStorage.getItem(TOKEN_KEY);
        }
        return null;
    }

    function getStoredUser() {
        if (typeof localStorage !== 'undefined') {
            const raw = localStorage.getItem(USER_KEY);
            if (raw) {
                try { return JSON.parse(raw); } catch (e) { return null; }
            }
        }
        return null;
    }

    function setAuthData(user, token) {
        if (typeof localStorage !== 'undefined') {
            if (token) localStorage.setItem(TOKEN_KEY, token);
            if (user) {
                // Strictly ensure passwords are never stored in localStorage
                const safeUser = { ...user };
                delete safeUser.password;
                localStorage.setItem(USER_KEY, JSON.stringify(safeUser));
            }
        }
    }

    function clearAuthData() {
        if (typeof localStorage !== 'undefined') {
            localStorage.removeItem(TOKEN_KEY);
            localStorage.removeItem(USER_KEY);
        }
    }

    let activeRequestsCount = 0;
    function updateGlobalLoading(delta) {
        activeRequestsCount = Math.max(0, activeRequestsCount + delta);
        if (typeof document !== 'undefined') {
            const bar = document.getElementById('global-loading-bar');
            if (bar) {
                bar.style.display = activeRequestsCount > 0 ? 'block' : 'none';
            }
        }
    }

    /**
     * Internal fetch wrapper with standardized error handling and JSON parsing.
     * @param {string} endpoint - API path relative to BASE_URL (e.g. '/tasks')
     * @param {object} options - Standard fetch options (method, headers, body)
     * @returns {Promise<{ok: boolean, status: number, data?: any, message?: string, errors?: any}>}
     */
    async function request(endpoint, options = {}) {
        const url = `${BASE_URL}${endpoint}`;
        const token = getStoredToken();
        const headers = {
            'Accept': 'application/json',
            ...(options.body ? { 'Content-Type': 'application/json' } : {}),
            ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
            ...options.headers
        };

        const fetchOptions = {
            credentials: 'include',
            ...options,
            headers
        };

        updateGlobalLoading(1);

        try {
            const response = await fetch(url, fetchOptions);
            const result = await response.json().catch(() => ({}));

            if (!response.ok) {
                // Return structured user-friendly error message
                return {
                    ok: false,
                    status: response.status,
                    message: result.message || 'The server encountered an issue processing your request.',
                    errors: result.errors || null
                };
            }

            return {
                ok: true,
                status: response.status,
                data: result.data !== undefined ? result.data : result,
                count: result.count,
                message: result.message || 'Success'
            };
        } catch (error) {
            // Network failure or offline server handling
            return {
                ok: false,
                status: 0,
                message: 'Unable to connect to the TaskFlow API server. Please check that the Flask backend is running.'
            };
        } finally {
            updateGlobalLoading(-1);
        }
    }

    // ========================================================================
    // SYSTEM & HEALTH CHECKS
    // ========================================================================

    async function checkHealth() {
        return request('/health');
    }

    async function checkDbStatus() {
        return request('/db/status');
    }

    // ========================================================================
    // TASKS API
    // ========================================================================

    /**
     * Retrieve all tasks with optional filters.
     * @param {object} filters - { status, priority, category_id, user_id }
     */
    async function getTasks(filters = {}) {
        const params = new URLSearchParams();
        if (filters.status) params.append('status', filters.status);
        if (filters.priority) params.append('priority', filters.priority);
        if (filters.category_id) params.append('category_id', filters.category_id);
        if (filters.user_id) params.append('user_id', filters.user_id);

        const qs = params.toString() ? `?${params.toString()}` : '';
        return request(`/tasks${qs}`);
    }

    /**
     * Retrieve a single task by ID.
     */
    async function getTask(id) {
        return request(`/tasks/${id}`);
    }

    /**
     * Create a new task.
     * @param {object} data - { title, description, category_id, user_id, priority, status, due_date }
     */
    async function createTask(data) {
        return request('/tasks', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * Update an existing task by ID.
     * @param {number|string} id - Task primary key
     * @param {object} data - Task fields to update
     */
    async function updateTask(id, data) {
        return request(`/tasks/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * Delete a task by ID.
     */
    async function deleteTask(id) {
        return request(`/tasks/${id}`, {
            method: 'DELETE'
        });
    }

    // ========================================================================
    // CATEGORIES API
    // ========================================================================

    /**
     * Retrieve all categories.
     */
    async function getCategories() {
        return request('/categories');
    }

    /**
     * Retrieve a single category by ID.
     */
    async function getCategory(id) {
        return request(`/categories/${id}`);
    }

    /**
     * Create a new category.
     * @param {object} data - { name, color }
     */
    async function createCategory(data) {
        return request('/categories', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * Update an existing category by ID.
     */
    async function updateCategory(id, data) {
        return request(`/categories/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * Delete a category by ID.
     */
    async function deleteCategory(id) {
        return request(`/categories/${id}`, {
            method: 'DELETE'
        });
    }

    // ========================================================================
    // USERS API
    // ========================================================================

    async function getUsers() {
        return request('/users');
    }

    async function getUser(id) {
        return request(`/users/${id}`);
    }

    async function createUser(data) {
        return request('/users', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async function updateUser(id, data) {
        return request(`/users/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async function deleteUser(id) {
        return request(`/users/${id}`, {
            method: 'DELETE'
        });
    }

    // ========================================================================
    // AUTHENTICATION API (Step 8)
    // ========================================================================

    /**
     * Register a new user.
     * @param {object} userData - { name, email, password }
     */
    async function register(userData) {
        const res = await request('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
        if (res.ok && res.data && res.data.user) {
            setAuthData(res.data.user, res.data.token);
        }
        return res;
    }

    /**
     * Authenticate an existing user.
     * @param {object} credentials - { email, password }
     */
    async function login(credentials) {
        const res = await request('/auth/login', {
            method: 'POST',
            body: JSON.stringify(credentials)
        });
        if (res.ok && res.data && res.data.user) {
            setAuthData(res.data.user, res.data.token);
        }
        return res;
    }

    /**
     * Log out current user and clear stored tokens.
     */
    async function logout() {
        try {
            await request('/auth/logout', { method: 'POST' });
        } catch (e) {
            // Ignore offline errors during logout
        } finally {
            clearAuthData();
        }
        return { ok: true, message: 'Logged out successfully.' };
    }

    /**
     * Fetch authenticated user profile from /api/auth/me.
     */
    async function getMe() {
        const res = await request('/auth/me');
        if (res.ok && res.data && res.data.user) {
            setAuthData(res.data.user, getStoredToken());
        }
        return res;
    }

    function getCurrentUser() {
        return getStoredUser();
    }

    function isAuthenticated() {
        return !!getStoredToken() || !!getStoredUser();
    }

    return {
        BASE_URL,
        request,
        checkHealth,
        checkDbStatus,
        // Authentication (Step 8)
        register,
        login,
        logout,
        getMe,
        getCurrentUser,
        isAuthenticated,
        setAuthData,
        clearAuthData,
        // Tasks
        getTasks,
        getTask,
        createTask,
        updateTask,
        deleteTask,
        // Categories
        getCategories,
        getCategory,
        createCategory,
        updateCategory,
        deleteCategory,
        // Users
        getUsers,
        getUser,
        createUser,
        updateUser,
        deleteUser
    };
})();

// Attach to window for browser access, and module.exports for test environments
if (typeof window !== 'undefined') {
    window.TaskFlowAPI = TaskFlowAPI;
}
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TaskFlowAPI };
}
