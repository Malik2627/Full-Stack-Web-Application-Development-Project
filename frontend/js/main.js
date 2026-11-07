/**
 * TaskFlow Main Application Controller
 * - Dashboard Analytics with Chart.js (Status, Priority, Category distributions)
 * - Real-time statistics (Total, Completed, Pending, In Progress, High Priority, Overdue)
 * - Complete CRUD operations for Task Management (tasks.html)
 * - Instant live updates without full browser reloads
 */

document.addEventListener('DOMContentLoaded', () => {
    // Shared state caches
    let cachedTasks = [];
    let cachedCategories = [];
    let taskPendingDeleteId = null;

    // Chart.js instances
    let statusChartInstance = null;
    let priorityChartInstance = null;
    let categoryChartInstance = null;

    // ========================================================================
    // 0. User Authentication & Profile Session (Step 8)
    // ========================================================================
    function initAuthSession() {
        if (!window.TaskFlowAPI) return;

        const isAppPage = document.getElementById('recent-tasks-body') || document.getElementById('tasks-table-body');
        const currentUser = window.TaskFlowAPI.getCurrentUser();

        // If on protected dashboard or tasks page and not authenticated, redirect to login
        if (isAppPage && !window.TaskFlowAPI.isAuthenticated()) {
            const isLocalFile = window.location.protocol === 'file:';
            // Allow browsing on local file unless user wants to sign in
            if (!isLocalFile) {
                window.location.href = 'login.html';
                return;
            }
        }

        // Render current user profile details in UI
        if (currentUser) {
            updateUserProfileUI(currentUser);
        }

        // Attach logout handlers across navbar dropdown, desktop sidebar, and mobile menu
        document.querySelectorAll('#auth-logout-btn, .mobile-logout-link, .sidebar-logout-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.preventDefault();
                await window.TaskFlowAPI.logout();
                window.location.href = 'login.html';
            });
        });
    }

    function updateUserProfileUI(user) {
        if (!user) return;
        const name = user.name || 'Student';
        const email = user.email || 'student@example.edu';

        const parts = name.trim().split(/\s+/);
        const initials = parts.length > 1
            ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
            : name.slice(0, 2).toUpperCase();

        const sidebarAvatar = document.getElementById('sidebar-avatar');
        const sidebarName = document.getElementById('sidebar-user-name');
        const navbarAvatar = document.getElementById('navbar-avatar');
        const navbarName = document.getElementById('navbar-user-name');
        const dropdownName = document.getElementById('dropdown-user-name');
        const dropdownEmail = document.getElementById('dropdown-user-email');

        if (sidebarAvatar) sidebarAvatar.textContent = initials;
        if (sidebarName) sidebarName.textContent = name;
        if (navbarAvatar) navbarAvatar.textContent = initials;
        if (navbarName) navbarName.textContent = name;
        if (dropdownName) dropdownName.textContent = name;
        if (dropdownEmail) dropdownEmail.textContent = email;
    }

    initAuthSession();

    // ========================================================================
    // 1. Landing Page Health Status Indicator (index.html)
    // ========================================================================
    const statusBadge = document.getElementById('api-status-badge');
    const statusText = document.getElementById('api-status-text');
    const testApiBtn = document.getElementById('test-api-btn');
    const apiResponseAlert = document.getElementById('api-response-alert');

    function updateApiStatus(state, message) {
        if (!statusBadge || !statusText) return;
        statusBadge.className = 'status-indicator';

        if (state === 'connected') {
            statusBadge.classList.add('status-connected');
            statusText.textContent = 'API Online';
        } else if (state === 'offline') {
            statusBadge.classList.add('status-offline');
            statusText.textContent = 'API Offline';
        } else {
            statusBadge.classList.add('status-checking');
            statusText.textContent = 'Checking API...';
        }

        if (apiResponseAlert) {
            apiResponseAlert.className = `alert alert-${state === 'connected' ? 'success' : state === 'offline' ? 'danger' : 'warning'} mt-3`;
            apiResponseAlert.textContent = message;
            apiResponseAlert.classList.remove('d-none');
        }
    }

    async function verifyBackendHealth() {
        if (!window.TaskFlowAPI || !statusBadge) return;
        updateApiStatus('checking', 'Connecting to Flask API at ' + window.TaskFlowAPI.BASE_URL + ' ...');
        const result = await window.TaskFlowAPI.checkHealth();
        if (result && result.ok) {
            updateApiStatus('connected', `Backend Online: ${result.message || 'Connected to TaskFlow API'}`);
        } else {
            updateApiStatus('offline', 'Backend Offline: Start Flask server using python app.py on port 5000.');
        }
    }

    if (testApiBtn) {
        testApiBtn.addEventListener('click', (e) => {
            e.preventDefault();
            verifyBackendHealth();
        });
    }

    if (statusBadge) {
        verifyBackendHealth();
    }

    // ========================================================================
    // 2. Dashboard & Analytics Controller (dashboard.html)
    // ========================================================================
    const dashboardTableBody = document.getElementById('recent-tasks-body');

    if (dashboardTableBody) {
        initDashboard();
    }

    async function initDashboard() {
        // Refresh / Sync button
        const refreshBtn = document.getElementById('refresh-dashboard-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', (e) => {
                e.preventDefault();
                loadDashboardData();
            });
        }

        // Quick add task form handler
        const quickAddForm = document.getElementById('quick-add-form');
        if (quickAddForm) {
            quickAddForm.addEventListener('submit', handleDashboardQuickAdd);
        }

        // Modal add task form handler
        const modalAddForm = document.getElementById('modal-add-task-form');
        if (modalAddForm) {
            modalAddForm.addEventListener('submit', handleDashboardModalAdd);
        }

        // Live input validation listeners for immediate feedback
        const quickTitle = document.getElementById('quick-title');
        if (quickTitle) {
            quickTitle.addEventListener('input', () => {
                if (quickTitle.value.trim()) quickTitle.classList.remove('is-invalid');
            });
            quickTitle.addEventListener('blur', () => {
                if (!quickTitle.value.trim()) quickTitle.classList.add('is-invalid');
            });
        }
        const quickDate = document.getElementById('quick-due-date');
        if (quickDate) {
            quickDate.addEventListener('input', () => {
                if (isValidCalendarDate(quickDate.value)) quickDate.classList.remove('is-invalid');
                else quickDate.classList.add('is-invalid');
            });
            quickDate.addEventListener('change', () => {
                if (isValidCalendarDate(quickDate.value)) quickDate.classList.remove('is-invalid');
                else quickDate.classList.add('is-invalid');
            });
        }
        const dashModalTitle = document.getElementById('modal-task-title');
        if (dashModalTitle) {
            dashModalTitle.addEventListener('input', () => {
                if (dashModalTitle.value.trim()) {
                    dashModalTitle.classList.remove('is-invalid');
                    const err = document.getElementById('modal-error-alert');
                    if (err) err.classList.add('d-none');
                }
            });
            dashModalTitle.addEventListener('blur', () => {
                if (!dashModalTitle.value.trim()) dashModalTitle.classList.add('is-invalid');
            });
        }
        const dashModalDate = document.getElementById('modal-task-date');
        if (dashModalDate) {
            dashModalDate.addEventListener('input', () => {
                if (isValidCalendarDate(dashModalDate.value)) {
                    dashModalDate.classList.remove('is-invalid');
                    const err = document.getElementById('modal-error-alert');
                    if (err) err.classList.add('d-none');
                } else {
                    dashModalDate.classList.add('is-invalid');
                }
            });
            dashModalDate.addEventListener('change', () => {
                if (isValidCalendarDate(dashModalDate.value)) {
                    dashModalDate.classList.remove('is-invalid');
                } else {
                    dashModalDate.classList.add('is-invalid');
                }
            });
        }

        // Dashboard search input
        const dashSearchInput = document.getElementById('dashboard-search-input');
        if (dashSearchInput) {
            dashSearchInput.addEventListener('input', () => {
                const query = dashSearchInput.value.trim().toLowerCase();
                const filtered = cachedTasks.filter(t =>
                    (t.title && t.title.toLowerCase().includes(query)) ||
                    (t.description && t.description.toLowerCase().includes(query)) ||
                    (t.category_name && t.category_name.toLowerCase().includes(query))
                );
                renderDashboardRecentTasks(filtered);
            });
        }

        // Initial live fetch
        await loadDashboardData();
    }

    /**
     * Load tasks and categories from the Flask REST API and update all analytics widgets
     */
    async function loadDashboardData() {
        showDashboardLoadingState();

        try {
            const [tasksRes, categoriesRes] = await Promise.all([
                window.TaskFlowAPI.getTasks(),
                window.TaskFlowAPI.getCategories()
            ]);

            if (!tasksRes.ok) {
                if (tasksRes.status === 401) {
                    window.TaskFlowAPI.clearAuthData();
                    window.location.href = 'login.html';
                    return;
                }
                showDashboardErrorState(tasksRes.message || 'Unable to retrieve tasks from the server.');
                return;
            }

            cachedTasks = Array.isArray(tasksRes.data) ? tasksRes.data : [];
            cachedCategories = Array.isArray(categoriesRes.data) ? categoriesRes.data : [];

            // 1. Calculate and update the 6 Dashboard Statistics cards
            renderDashboardStatistics(cachedTasks);

            // 2. Render or update the 3 Analytics Charts via Chart.js
            renderAnalyticsCharts(cachedTasks, cachedCategories);

            // 3. Render latest 5 recent tasks table
            renderDashboardRecentTasks(cachedTasks);

            // 4. Render upcoming deadlines and overdue tasks
            renderDashboardDeadlines(cachedTasks);

            // 5. Update progress mini-summary
            renderProgressSummary(cachedTasks);

            // 6. Populate category dropdowns & modal
            populateDashboardCategorySelects(cachedCategories);
            renderCategoriesModal(cachedCategories, cachedTasks);

            // 7. Update sidebar task counts
            updateSidebarCounts(cachedTasks.length);

        } catch (err) {
            console.error('Dashboard load failed:', err);
            showDashboardErrorState('A network error occurred while connecting to the database.');
        }
    }

    function showDashboardLoadingState() {
        if (dashboardTableBody) {
            dashboardTableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center py-4 text-muted">
                        <div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>
                        Fetching live tasks from SQLite database...
                    </td>
                </tr>
            `;
        }
    }

    function showDashboardErrorState(userMessage) {
        const alertContainer = document.getElementById('dashboard-alert-container');
        if (alertContainer) {
            alertContainer.innerHTML = `
                <div class="alert alert-warning alert-dismissible fade show shadow-sm mb-4" role="alert">
                    <div class="d-flex align-items-center gap-2">
                        <i class="bi bi-exclamation-triangle-fill fs-5 text-warning"></i>
                        <div>
                            <strong>Backend Unavailable:</strong> ${escapeHtml(userMessage)}
                            <div class="small mt-1">Make sure the Flask API is running: <code>python app.py</code></div>
                        </div>
                        <button type="button" class="btn btn-sm btn-outline-dark ms-auto" id="retry-dashboard-btn">
                            <i class="bi bi-arrow-clockwise me-1"></i>Retry
                        </button>
                    </div>
                </div>
            `;
            const retryBtn = document.getElementById('retry-dashboard-btn');
            if (retryBtn) {
                retryBtn.addEventListener('click', () => {
                    alertContainer.innerHTML = '';
                    loadDashboardData();
                });
            }
        }

        if (dashboardTableBody) {
            dashboardTableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center py-4 text-muted">
                        <i class="bi bi-wifi-off fs-4 d-block mb-2 text-danger"></i>
                        <span>Unable to load tasks. Verify Flask server connection.</span>
                    </td>
                </tr>
            `;
        }
    }

    /**
     * 1. Calculate and display the 6 Dashboard Statistics:
     * - Total Tasks
     * - Completed Tasks
     * - Pending Tasks
     * - In Progress
     * - High Priority
     * - Overdue
     */
    function renderDashboardStatistics(tasks) {
        const total = tasks.length;
        const completed = tasks.filter(t => t.status === 'Completed').length;
        const inProgress = tasks.filter(t => t.status === 'In Progress').length;
        const pending = tasks.filter(t => t.status === 'Pending').length;
        const highPriority = tasks.filter(t =>
            (t.priority || '').toLowerCase() === 'high' || (t.priority || '').toLowerCase() === 'urgent'
        ).length;
        const overdue = tasks.filter(t => isOverdue(t.due_date, t.status === 'Completed')).length;

        const completionPct = total > 0 ? Math.round((completed / total) * 100) : 0;

        // Elements
        const elTotal = document.getElementById('metric-total');
        const elCompleted = document.getElementById('metric-completed');
        const elInProgress = document.getElementById('metric-inprogress');
        const elPending = document.getElementById('metric-pending');
        const elHigh = document.getElementById('metric-high');
        const elOverdue = document.getElementById('metric-overdue');

        if (elTotal) elTotal.textContent = total;
        if (elCompleted) elCompleted.textContent = completed;
        if (elInProgress) elInProgress.textContent = inProgress;
        if (elPending) elPending.textContent = pending;
        if (elHigh) elHigh.textContent = highPriority;
        if (elOverdue) elOverdue.textContent = overdue;

        // Subtitles
        const subComp = document.getElementById('metric-completed-sub');
        if (subComp) subComp.textContent = `${completionPct}% finished`;

        const subOverdue = document.getElementById('metric-overdue-sub');
        if (subOverdue) {
            subOverdue.textContent = overdue > 0 ? `${overdue} overdue items` : 'No overdue items';
        }
    }

    /**
     * 2. Render or Update the 3 Analytics Charts using Chart.js:
     * - Task Status Chart (Doughnut)
     * - Priority Distribution Chart (Bar)
     * - Category Distribution Chart (Doughnut)
     */
    function renderAnalyticsCharts(tasks, categories) {
        if (typeof Chart === 'undefined') {
            console.warn('Chart.js is not loaded.');
            return;
        }

        const total = tasks.length;

        // --------------------------------------------------------------------
        // Chart 1: Task Status Chart (Doughnut)
        // --------------------------------------------------------------------
        const statusCounts = {
            'Completed': tasks.filter(t => t.status === 'Completed').length,
            'In Progress': tasks.filter(t => t.status === 'In Progress').length,
            'Pending': tasks.filter(t => t.status === 'Pending').length,
            'Cancelled': tasks.filter(t => t.status === 'Cancelled').length
        };

        const statusLabels = ['Completed', 'In Progress', 'Pending', 'Cancelled'];
        const statusData = statusLabels.map(l => statusCounts[l] || 0);
        const statusColors = ['#10b981', '#4f46e5', '#f59e0b', '#94a3b8'];

        const displayStatusLabels = total > 0 ? statusLabels : ['No tasks'];
        const displayStatusData = total > 0 ? statusData : [1];
        const displayStatusColors = total > 0 ? statusColors : ['#e2e8f0'];

        const statusCanvas = document.getElementById('statusChart');
        if (statusCanvas) {
            if (statusChartInstance) {
                statusChartInstance.data.labels = displayStatusLabels;
                statusChartInstance.data.datasets[0].data = displayStatusData;
                statusChartInstance.data.datasets[0].backgroundColor = displayStatusColors;
                statusChartInstance.update();
            } else {
                statusChartInstance = new Chart(statusCanvas, {
                    type: 'doughnut',
                    data: {
                        labels: displayStatusLabels,
                        datasets: [{
                            data: displayStatusData,
                            backgroundColor: displayStatusColors,
                            borderWidth: 2,
                            borderColor: '#ffffff'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: { boxWidth: 12, font: { size: 11 } }
                            },
                            tooltip: {
                                backgroundColor: '#0f172a',
                                titleFont: { size: 12, weight: 'bold' },
                                bodyFont: { size: 11 },
                                padding: 8,
                                cornerRadius: 6,
                                boxPadding: 4
                            }
                        },
                        cutout: '65%'
                    }
                });
            }
        }

        // --------------------------------------------------------------------
        // Chart 2: Priority Distribution Chart (Bar)
        // --------------------------------------------------------------------
        const priorityCounts = {
            'Urgent': tasks.filter(t => (t.priority || '').toLowerCase() === 'urgent').length,
            'High': tasks.filter(t => (t.priority || '').toLowerCase() === 'high').length,
            'Medium': tasks.filter(t => (t.priority || '').toLowerCase() === 'medium').length,
            'Low': tasks.filter(t => (t.priority || '').toLowerCase() === 'low').length
        };

        const priorityLabels = ['Urgent', 'High', 'Medium', 'Low'];
        const priorityData = priorityLabels.map(p => priorityCounts[p]);
        const priorityColors = ['#ef4444', '#f97316', '#f59e0b', '#0ea5e9'];

        const priorityCanvas = document.getElementById('priorityChart');
        if (priorityCanvas) {
            if (priorityChartInstance) {
                priorityChartInstance.data.labels = priorityLabels;
                priorityChartInstance.data.datasets[0].data = priorityData;
                priorityChartInstance.update();
            } else {
                priorityChartInstance = new Chart(priorityCanvas, {
                    type: 'bar',
                    data: {
                        labels: priorityLabels,
                        datasets: [{
                            label: 'Tasks',
                            data: priorityData,
                            backgroundColor: priorityColors,
                            borderRadius: 6
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                backgroundColor: '#0f172a',
                                titleFont: { size: 12, weight: 'bold' },
                                bodyFont: { size: 11 },
                                padding: 8,
                                cornerRadius: 6,
                                boxPadding: 4
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: { precision: 0, font: { size: 10 } },
                                grid: { color: '#f1f5f9' }
                            },
                            x: {
                                ticks: { font: { size: 11 } },
                                grid: { display: false }
                            }
                        }
                    }
                });
            }
        }

        // --------------------------------------------------------------------
        // Chart 3: Category Distribution Chart (Doughnut)
        // --------------------------------------------------------------------
        const catMap = {};
        categories.forEach(c => {
            catMap[c.name] = { count: 0, color: c.color || '#64748b' };
        });

        tasks.forEach(t => {
            const name = t.category_name || 'General';
            if (!catMap[name]) {
                catMap[name] = { count: 0, color: t.category_color || '#4f46e5' };
            }
            catMap[name].count++;
        });

        const catLabels = Object.keys(catMap);
        const catData = catLabels.map(l => catMap[l].count);
        const catColors = catLabels.map(l => catMap[l].color);

        const displayCatLabels = total > 0 ? catLabels : ['No tasks'];
        const displayCatData = total > 0 ? catData : [1];
        const displayCatColors = total > 0 ? catColors : ['#e2e8f0'];

        const categoryCanvas = document.getElementById('categoryChart');
        if (categoryCanvas) {
            if (categoryChartInstance) {
                categoryChartInstance.data.labels = displayCatLabels;
                categoryChartInstance.data.datasets[0].data = displayCatData;
                categoryChartInstance.data.datasets[0].backgroundColor = displayCatColors;
                categoryChartInstance.update();
            } else {
                categoryChartInstance = new Chart(categoryCanvas, {
                    type: 'doughnut',
                    data: {
                        labels: displayCatLabels,
                        datasets: [{
                            data: displayCatData,
                            backgroundColor: displayCatColors,
                            borderWidth: 2,
                            borderColor: '#ffffff'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: { boxWidth: 12, font: { size: 11 } }
                            },
                            tooltip: {
                                backgroundColor: '#0f172a',
                                titleFont: { size: 12, weight: 'bold' },
                                bodyFont: { size: 11 },
                                padding: 8,
                                cornerRadius: 6,
                                boxPadding: 4
                            }
                        },
                        cutout: '60%'
                    }
                });
            }
        }
    }

    /**
     * 3. Recent Tasks: Display the latest 5 tasks
     */
    function renderDashboardRecentTasks(tasks) {
        if (!dashboardTableBody) return;

        const badge = document.getElementById('recent-tasks-badge');
        if (badge) badge.textContent = `${Math.min(5, tasks.length)} of ${tasks.length}`;

        if (tasks.length === 0) {
            dashboardTableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center py-5">
                        <div class="empty-state">
                            <i class="bi bi-clipboard-plus text-primary mb-2 d-block" style="font-size: 2.5rem;"></i>
                            <h6 class="fw-bold text-dark mb-1">No tasks found</h6>
                            <p class="text-muted small mb-3">Create your first task to get started.</p>
                            <button class="btn btn-primary btn-sm" data-bs-toggle="modal" data-bs-target="#addTaskModal">
                                <i class="bi bi-plus-lg me-1"></i>Create First Task
                            </button>
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        // Show latest 5 tasks
        const latest5 = tasks.slice(0, 5);

        dashboardTableBody.innerHTML = latest5.map(task => {
            const isCompleted = task.status === 'Completed';
            const catColor = task.category_color || '#64748b';
            const catName = task.category_name || 'General';
            const priorityClass = getPriorityBadgeClass(task.priority);
            const statusClass = getStatusBadgeClass(task.status);
            const formattedDate = formatDueDate(task.due_date);
            const overdue = isOverdue(task.due_date, isCompleted);

            return `
                <tr data-task-id="${task.id}">
                    <td>
                        <input class="form-check-input task-checkbox" 
                               type="checkbox" 
                               ${isCompleted ? 'checked' : ''} 
                               data-task-id="${task.id}"
                               title="Click to toggle status">
                    </td>
                    <td>
                        <div class="task-title-cell ${isCompleted ? 'task-title-completed' : ''}">${escapeHtml(task.title)}</div>
                        ${task.description ? `<div class="text-muted small text-truncate" style="max-width: 280px;">${escapeHtml(task.description)}</div>` : ''}
                    </td>
                    <td>
                        <span class="badge-category" style="background-color: ${catColor}20; color: ${catColor}; border: 1px solid ${catColor}40;">
                            <span class="cat-dot" style="background-color: ${catColor};"></span>
                            ${escapeHtml(catName)}
                        </span>
                    </td>
                    <td><span class="badge-priority ${priorityClass}">${escapeHtml(task.priority || 'Medium')}</span></td>
                    <td><span class="badge-status ${statusClass}">${escapeHtml(task.status || 'Pending')}</span></td>
                    <td>
                        <span class="small ${overdue ? 'text-danger fw-semibold' : 'text-muted'}">
                            <i class="bi ${overdue ? 'bi-exclamation-circle-fill text-danger' : 'bi-calendar3'} me-1"></i>
                            ${formattedDate}
                            ${overdue ? '<span class="badge bg-danger-subtle text-danger ms-1">Overdue</span>' : ''}
                        </span>
                    </td>
                    <td class="text-end">
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-sm btn-light border btn-dash-toggle" 
                                    data-task-id="${task.id}" 
                                    data-status="${task.status}"
                                    title="${isCompleted ? 'Mark as Pending' : 'Mark as Completed'}"
                                    aria-label="${isCompleted ? 'Mark as Pending' : 'Mark as Completed'}">
                                <i class="bi ${isCompleted ? 'bi-arrow-counterclockwise' : 'bi-check2'}"></i>
                            </button>
                            <button class="btn btn-sm btn-light border text-danger btn-dash-delete" 
                                    data-task-id="${task.id}" 
                                    data-task-title="${escapeHtml(task.title)}"
                                    title="Delete task"
                                    aria-label="Delete task: ${escapeHtml(task.title)}">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');

        // Attach toggle handlers
        dashboardTableBody.querySelectorAll('.task-checkbox, .btn-dash-toggle').forEach(el => {
            el.addEventListener('click', async (e) => {
                const taskId = el.getAttribute('data-task-id');
                const isChk = el.classList.contains('task-checkbox');
                const currentStatus = el.getAttribute('data-status') || (isChk && !el.checked ? 'Completed' : 'Pending');
                const nextStatus = currentStatus === 'Completed' ? 'Pending' : 'Completed';
                await window.TaskFlowAPI.updateTask(taskId, { status: nextStatus });
                // Refresh dashboard data & charts without full page reload
                await loadDashboardData();
            });
        });

        // Attach delete handlers for instant in-place refresh with standard confirmation
        dashboardTableBody.querySelectorAll('.btn-dash-delete').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const taskId = btn.getAttribute('data-task-id');
                const taskTitle = btn.getAttribute('data-task-title') || 'this task';
                if (confirm("Are you sure you want to delete this task?")) {
                    await window.TaskFlowAPI.deleteTask(taskId);
                    await loadDashboardData();
                }
            });
        });
    }

    /**
     * 4. Upcoming Deadlines & Overdue tasks
     */
    function renderDashboardDeadlines(tasks) {
        const container = document.getElementById('upcoming-deadlines-container');
        if (!container) return;

        // Filter uncompleted tasks that have due dates and sort by due_date ascending
        const uncompletedWithDates = tasks
            .filter(t => t.due_date && t.status !== 'Completed')
            .sort((a, b) => a.due_date.localeCompare(b.due_date));

        const deadlinesBadge = document.getElementById('deadlines-badge');

        if (uncompletedWithDates.length === 0) {
            container.innerHTML = `
                <div class="text-center py-4 text-muted small">
                    <i class="bi bi-calendar-check text-success fs-3 d-block mb-1"></i>
                    <div class="fw-bold text-dark mb-1">No upcoming deadlines found</div>
                    <div class="text-muted">All coursework deliverables are up to date!</div>
                </div>
            `;
            if (deadlinesBadge) {
                deadlinesBadge.textContent = 'None';
                deadlinesBadge.className = 'badge bg-success-subtle text-success border border-success-subtle';
            }
            return;
        }

        const now = new Date();
        now.setHours(0, 0, 0, 0);

        let hasOverdue = false;

        container.innerHTML = uncompletedWithDates.slice(0, 5).map(task => {
            let diffDays = 0;
            try {
                const parts = task.due_date.split('T')[0].split('-');
                const dueDate = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
                const diffTime = dueDate - now;
                diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));
            } catch (e) {
                const dueDate = new Date(task.due_date);
                const diffTime = dueDate - now;
                diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));
            }

            let itemClass = 'deadline-normal';
            let tagClass = 'deadline-tag-normal';
            let tagText = formatDueDate(task.due_date);

            if (diffDays < 0) {
                hasOverdue = true;
                itemClass = 'deadline-urgent';
                tagClass = 'deadline-tag-urgent';
                tagText = `Overdue (${Math.abs(diffDays)}d late)`;
            } else if (diffDays === 0) {
                hasOverdue = true;
                itemClass = 'deadline-urgent';
                tagClass = 'deadline-tag-urgent';
                tagText = 'Due Today';
            } else if (diffDays === 1) {
                itemClass = 'deadline-urgent';
                tagClass = 'deadline-tag-urgent';
                tagText = 'Tomorrow';
            } else if (diffDays <= 3) {
                itemClass = 'deadline-soon';
                tagClass = 'deadline-tag-soon';
                tagText = `In ${diffDays} Days`;
            } else if (diffDays <= 7) {
                itemClass = 'deadline-normal';
                tagClass = 'deadline-tag-normal';
                tagText = 'Next Week';
            }

            return `
                <div class="deadline-item ${itemClass}">
                    <div>
                        <div class="fw-bold small text-dark">${escapeHtml(task.title)}</div>
                        <div class="text-muted" style="font-size: 0.75rem;">
                            ${escapeHtml(task.category_name || 'Coursework')} &bull; Priority: ${escapeHtml(task.priority || 'Medium')}
                        </div>
                    </div>
                    <span class="deadline-tag ${tagClass}">${tagText}</span>
                </div>
            `;
        }).join('');

        if (deadlinesBadge) {
            if (hasOverdue) {
                deadlinesBadge.textContent = 'Overdue Alert';
                deadlinesBadge.className = 'badge bg-danger-subtle text-danger border border-danger-subtle';
            } else {
                deadlinesBadge.textContent = `${uncompletedWithDates.length} Pending`;
                deadlinesBadge.className = 'badge bg-primary-subtle text-primary border border-primary-subtle';
            }
        }
    }

    /**
     * Progress summary breakdown bar
     */
    function renderProgressSummary(tasks) {
        const total = tasks.length;
        const comp = tasks.filter(t => t.status === 'Completed').length;
        const inProg = tasks.filter(t => t.status === 'In Progress').length;
        const pend = tasks.filter(t => t.status === 'Pending').length;

        const compPct = total > 0 ? Math.round((comp / total) * 100) : 0;
        const inProgPct = total > 0 ? Math.round((inProg / total) * 100) : 0;
        const pendPct = total > 0 ? Math.max(0, 100 - compPct - inProgPct) : 0;

        const badgeOverall = document.getElementById('status-badge-overall');
        if (badgeOverall) badgeOverall.textContent = `${compPct}%`;

        const barComp = document.getElementById('status-bar-completed');
        const barInProg = document.getElementById('status-bar-inprogress');
        const barPend = document.getElementById('status-bar-pending');

        if (barComp) barComp.style.width = `${compPct}%`;
        if (barInProg) barInProg.style.width = `${inProgPct}%`;
        if (barPend) barPend.style.width = `${pendPct}%`;

        const cntComp = document.getElementById('status-count-completed');
        const cntInProg = document.getElementById('status-count-inprogress');
        const cntPend = document.getElementById('status-count-pending');

        if (cntComp) cntComp.textContent = comp;
        if (cntInProg) cntInProg.textContent = inProg;
        if (cntPend) cntPend.textContent = pend;
    }

    /**
     * Quick Add task from Dashboard (POST /api/tasks)
     */
    async function handleDashboardQuickAdd(e) {
        e.preventDefault();
        const titleInput = document.getElementById('quick-title');
        const catSelect = document.getElementById('quick-category');
        const prioSelect = document.getElementById('quick-priority');
        const dateInput = document.getElementById('quick-due-date');
        const submitBtn = document.getElementById('quick-add-submit-btn');
        const toast = document.getElementById('quick-add-toast');

        let hasErr = false;
        if (!titleInput || !titleInput.value.trim()) {
            if (titleInput) titleInput.classList.add('is-invalid');
            hasErr = true;
        } else {
            titleInput.classList.remove('is-invalid');
        }

        if (dateInput && dateInput.value && !isValidCalendarDate(dateInput.value)) {
            dateInput.classList.add('is-invalid');
            hasErr = true;
        } else if (dateInput) {
            dateInput.classList.remove('is-invalid');
        }

        if (hasErr) return;

        const payload = {
            title: titleInput.value.trim(),
            category_id: catSelect && catSelect.value ? parseInt(catSelect.value) : null,
            priority: prioSelect ? prioSelect.value : 'Medium',
            status: 'Pending',
            due_date: dateInput && dateInput.value ? dateInput.value : null
        };

        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Adding...';
        }

        try {
            const res = await window.TaskFlowAPI.createTask(payload);
            if (res.ok) {
                titleInput.value = '';
                if (dateInput) dateInput.value = '';
                if (toast) {
                    toast.classList.remove('d-none');
                    setTimeout(() => toast.classList.add('d-none'), 3500);
                }
                // Refresh dashboard statistics & charts in-place without page reload
                await loadDashboardData();
            } else {
                alert(res.message || 'Error creating task.');
            }
        } catch (err) {
            console.error('Quick add failed:', err);
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="bi bi-plus-lg me-1"></i>Add Task';
            }
        }
    }

    /**
     * Modal Add task from Dashboard (POST /api/tasks)
     */
    async function handleDashboardModalAdd(e) {
        e.preventDefault();
        const title = document.getElementById('modal-task-title');
        const desc = document.getElementById('modal-task-desc');
        const cat = document.getElementById('modal-task-cat');
        const prio = document.getElementById('modal-task-priority');
        const date = document.getElementById('modal-task-date');
        const submitBtn = document.getElementById('modal-task-submit-btn');
        const errorAlert = document.getElementById('modal-error-alert');

        let hasErr = false;
        if (!title || !title.value.trim()) {
            if (title) title.classList.add('is-invalid');
            hasErr = true;
        } else {
            title.classList.remove('is-invalid');
        }

        if (date && date.value && !isValidCalendarDate(date.value)) {
            date.classList.add('is-invalid');
            hasErr = true;
        } else if (date) {
            date.classList.remove('is-invalid');
        }

        if (hasErr) {
            if (errorAlert) {
                errorAlert.textContent = !title || !title.value.trim() ? 'Task title is required' : 'Due date cannot be invalid';
                errorAlert.classList.remove('d-none');
            }
            return;
        }

        const payload = {
            title: title.value.trim(),
            description: desc ? desc.value.trim() : null,
            category_id: cat && cat.value ? parseInt(cat.value) : null,
            priority: prio ? prio.value : 'Medium',
            status: 'Pending',
            due_date: date && date.value ? date.value : null
        };

        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Saving...';
        }

        try {
            const res = await window.TaskFlowAPI.createTask(payload);
            if (res.ok) {
                title.value = '';
                if (desc) desc.value = '';
                if (date) date.value = '';
                if (errorAlert) errorAlert.classList.add('d-none');

                const modalEl = document.getElementById('addTaskModal');
                if (modalEl && window.bootstrap) {
                    const modal = window.bootstrap.Modal.getInstance(modalEl);
                    if (modal) modal.hide();
                }

                // Refresh dashboard data & charts in-place
                await loadDashboardData();
            } else {
                if (errorAlert) {
                    errorAlert.textContent = res.message || 'Validation error.';
                    errorAlert.classList.remove('d-none');
                }
            }
        } catch (err) {
            console.error('Modal add failed:', err);
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="bi bi-plus-lg me-1"></i>Create Task';
            }
        }
    }

    function populateDashboardCategorySelects(categories) {
        const quickSelect = document.getElementById('quick-category');
        const modalSelect = document.getElementById('modal-task-cat');

        if (!categories || categories.length === 0) return;

        const optionsHtml = categories.map((cat, idx) => `
            <option value="${cat.id}" ${idx === 0 ? 'selected' : ''}>${escapeHtml(cat.name)}</option>
        `).join('');

        if (quickSelect) quickSelect.innerHTML = optionsHtml;
        if (modalSelect) modalSelect.innerHTML = optionsHtml;
    }

    function renderCategoriesModal(categories, tasks) {
        const modalList = document.getElementById('modal-categories-list');
        if (!modalList) return;

        if (!categories || categories.length === 0) {
            modalList.innerHTML = '<div class="text-muted small py-2">No categories available.</div>';
            return;
        }

        modalList.innerHTML = categories.map(cat => {
            const count = tasks.filter(t => t.category_id === cat.id).length;
            const color = cat.color || '#64748b';
            return `
                <div class="list-group-item d-flex justify-content-between align-items-center px-0">
                    <span class="d-flex align-items-center gap-2">
                        <span class="cat-dot" style="background-color: ${color};"></span>
                        <strong class="small">${escapeHtml(cat.name)}</strong>
                    </span>
                    <span class="badge bg-light text-muted border">${count} Tasks</span>
                </div>
            `;
        }).join('');
    }

    function updateSidebarCounts(count) {
        ['sidebar-task-count', 'mobile-sidebar-task-count', 'sidebar-tasks-count', 'mobile-sidebar-tasks-count'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = count;
        });
    }

    // ========================================================================
    // 3. Task Management Page Controller (tasks.html)
    // ========================================================================
    const tasksTableBody = document.getElementById('tasks-table-body');

    if (tasksTableBody) {
        initTaskManagementPage();
    }

    async function initTaskManagementPage() {
        const addBtns = [
            document.getElementById('top-add-task-btn'),
            document.getElementById('page-add-task-btn'),
            document.getElementById('sidebar-add-task-btn'),
            document.getElementById('mobile-sidebar-add-task-btn')
        ];

        addBtns.forEach(btn => {
            if (btn) {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    openTaskModalForCreate();
                });
            }
        });

        const refreshBtn = document.getElementById('refresh-tasks-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', (e) => {
                e.preventDefault();
                loadTaskManagementData();
            });
        }

        const taskModalForm = document.getElementById('task-modal-form');
        if (taskModalForm) {
            taskModalForm.addEventListener('submit', handleTaskModalSubmit);
        }

        const confirmDeleteBtn = document.getElementById('confirm-delete-action-btn');
        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', handleConfirmDelete);
        }

        const statusFilterBtns = document.querySelectorAll('.status-filter-btn');
        statusFilterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                statusFilterBtns.forEach(b => {
                    b.classList.remove('btn-primary', 'active');
                    b.classList.add('btn-outline-secondary');
                });
                btn.classList.add('btn-primary', 'active');
                btn.classList.remove('btn-outline-secondary');
                applyTaskFilters();
            });
        });

        const prioSelect = document.getElementById('priority-filter-select');
        if (prioSelect) prioSelect.addEventListener('change', applyTaskFilters);

        const catSelect = document.getElementById('category-filter-select');
        if (catSelect) catSelect.addEventListener('change', applyTaskFilters);

        const toolbarSearch = document.getElementById('toolbar-search-input');
        const navbarSearch = document.getElementById('tasks-search-input');

        if (toolbarSearch) {
            toolbarSearch.addEventListener('input', () => {
                if (navbarSearch) navbarSearch.value = toolbarSearch.value;
                applyTaskFilters();
            });
        }
        if (navbarSearch) {
            navbarSearch.addEventListener('input', () => {
                if (toolbarSearch) toolbarSearch.value = navbarSearch.value;
                applyTaskFilters();
            });
        }

        // Live input validation listeners for immediate modal feedback
        const modalTitleInput = document.getElementById('modal-task-title');
        if (modalTitleInput) {
            modalTitleInput.addEventListener('input', () => {
                if (modalTitleInput.value.trim()) {
                    modalTitleInput.classList.remove('is-invalid');
                    const err = document.getElementById('modal-form-error');
                    if (err) err.classList.add('d-none');
                }
            });
            modalTitleInput.addEventListener('blur', () => {
                if (!modalTitleInput.value.trim()) {
                    modalTitleInput.classList.add('is-invalid');
                }
            });
        }

        const modalDateInput = document.getElementById('modal-task-due-date');
        if (modalDateInput) {
            modalDateInput.addEventListener('input', () => {
                if (isValidCalendarDate(modalDateInput.value)) {
                    modalDateInput.classList.remove('is-invalid');
                    const err = document.getElementById('modal-form-error');
                    if (err) err.classList.add('d-none');
                } else {
                    modalDateInput.classList.add('is-invalid');
                }
            });
            modalDateInput.addEventListener('change', () => {
                if (isValidCalendarDate(modalDateInput.value)) {
                    modalDateInput.classList.remove('is-invalid');
                } else {
                    modalDateInput.classList.add('is-invalid');
                }
            });
        }

        await loadTaskManagementData();
    }

    async function loadTaskManagementData() {
        if (!tasksTableBody) return;
        tasksTableBody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-5 text-muted">
                    <div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>
                    Loading coursework tasks from database...
                </td>
            </tr>
        `;

        try {
            const [tasksRes, categoriesRes] = await Promise.all([
                window.TaskFlowAPI.getTasks(),
                window.TaskFlowAPI.getCategories()
            ]);

            if (!tasksRes.ok) {
                if (tasksRes.status === 401) {
                    window.TaskFlowAPI.clearAuthData();
                    window.location.href = 'login.html';
                    return;
                }
                showTasksErrorState(tasksRes.message || 'Unable to retrieve tasks from the server.');
                return;
            }

            cachedTasks = Array.isArray(tasksRes.data) ? tasksRes.data : [];
            cachedCategories = Array.isArray(categoriesRes.data) ? categoriesRes.data : [];

            populateCategoriesFilter(cachedCategories);
            populateModalCategorySelect(cachedCategories);
            renderCategoriesModal(cachedCategories, cachedTasks);
            updateSidebarCounts(cachedTasks.length);
            applyTaskFilters();

        } catch (err) {
            console.error('Task management load failed:', err);
            showTasksErrorState('A network error occurred while connecting to the database.');
        }
    }

    function showTasksErrorState(message) {
        showTasksAlert('warning', `<strong>Backend Unavailable:</strong> ${escapeHtml(message)} (Ensure Flask is running at http://127.0.0.1:5000)`);
        if (!tasksTableBody) return;
        tasksTableBody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-5 text-muted">
                    <i class="bi bi-wifi-off fs-2 d-block mb-2 text-danger"></i>
                    <h6 class="fw-bold">Unable to Connect to API</h6>
                    <button class="btn btn-sm btn-outline-primary mt-2" onclick="location.reload()">
                        <i class="bi bi-arrow-clockwise me-1"></i>Retry
                    </button>
                </td>
            </tr>
        `;
    }

    function showTasksAlert(type, messageHtml) {
        const container = document.getElementById('tasks-alert-container');
        if (!container) return;

        container.innerHTML = `
            <div class="alert alert-${type} alert-dismissible fade show shadow-sm mb-4" role="alert">
                <div class="d-flex align-items-center gap-2">
                    <i class="bi ${type === 'success' ? 'bi-check-circle-fill text-success' : 'bi-exclamation-triangle-fill text-warning'} fs-5"></i>
                    <div class="small">${messageHtml}</div>
                </div>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;

        if (type === 'success') {
            setTimeout(() => {
                const alertEl = container.querySelector('.alert');
                if (alertEl && window.bootstrap) {
                    const bsAlert = window.bootstrap.Alert.getInstance(alertEl);
                    if (bsAlert) bsAlert.close();
                }
            }, 4000);
        }
    }

    function populateCategoriesFilter(categories) {
        const catSelect = document.getElementById('category-filter-select');
        if (!catSelect) return;

        const currentVal = catSelect.value || 'all';
        catSelect.innerHTML = '<option value="all">All Categories</option>' +
            categories.map(c => `
                <option value="${c.id}" ${currentVal == c.id ? 'selected' : ''}>${escapeHtml(c.name)}</option>
            `).join('');
    }

    function populateModalCategorySelect(categories) {
        const modalCatSelect = document.getElementById('modal-task-category');
        if (!modalCatSelect) return;

        if (categories.length === 0) {
            modalCatSelect.innerHTML = '<option value="">No categories available</option>';
            return;
        }

        modalCatSelect.innerHTML = categories.map((c, idx) => `
            <option value="${c.id}" ${idx === 0 ? 'selected' : ''}>${escapeHtml(c.name)}</option>
        `).join('');
    }

    function applyTaskFilters() {
        if (!tasksTableBody) return;

        const activeStatusBtn = document.querySelector('.status-filter-btn.active');
        const statusFilter = activeStatusBtn ? activeStatusBtn.getAttribute('data-status') : 'all';

        const prioSelect = document.getElementById('priority-filter-select');
        const prioFilter = prioSelect ? prioSelect.value : 'all';

        const catSelect = document.getElementById('category-filter-select');
        const catFilter = catSelect ? catSelect.value : 'all';

        const toolbarSearch = document.getElementById('toolbar-search-input');
        const searchQuery = toolbarSearch ? toolbarSearch.value.trim().toLowerCase() : '';

        const filtered = cachedTasks.filter(task => {
            const matchesStatus = (statusFilter === 'all') ||
                (task.status && task.status.toLowerCase() === statusFilter.toLowerCase());

            const matchesPrio = (prioFilter === 'all') ||
                (task.priority && task.priority.toLowerCase() === prioFilter.toLowerCase());

            const matchesCat = (catFilter === 'all') ||
                (task.category_id && String(task.category_id) === String(catFilter));

            const titleMatch = task.title && task.title.toLowerCase().includes(searchQuery);
            const descMatch = task.description && task.description.toLowerCase().includes(searchQuery);
            const catMatch = task.category_name && task.category_name.toLowerCase().includes(searchQuery);
            const matchesSearch = !searchQuery || titleMatch || descMatch || catMatch;

            return matchesStatus && matchesPrio && matchesCat && matchesSearch;
        });

        renderTasksTable(filtered, cachedTasks.length);
    }

    function renderTasksTable(filteredTasks, totalInDb) {
        if (!tasksTableBody) return;

        const countBadge = document.getElementById('tasks-table-count-badge');
        if (countBadge) {
            countBadge.textContent = `${filteredTasks.length} of ${totalInDb} Tasks`;
        }

        if (filteredTasks.length === 0) {
            if (totalInDb === 0) {
                tasksTableBody.innerHTML = `
                    <tr>
                        <td colspan="7" class="text-center py-5">
                            <div class="empty-state">
                                <i class="bi bi-clipboard-plus text-primary" style="font-size: 3rem;"></i>
                                <h5 class="fw-bold text-dark mt-2">No tasks found</h5>
                                <p class="text-muted small mb-3">Create your first task to get started.</p>
                                <button class="btn btn-primary btn-sm px-3 shadow-sm" onclick="document.getElementById('page-add-task-btn').click()">
                                    <i class="bi bi-plus-lg me-1"></i>Create First Task
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
            } else {
                tasksTableBody.innerHTML = `
                    <tr>
                        <td colspan="7" class="text-center py-5">
                            <div class="empty-state">
                                <i class="bi bi-funnel text-muted" style="font-size: 2.5rem;"></i>
                                <h6 class="fw-bold text-dark mt-2">No tasks found</h6>
                                <p class="text-muted small mb-2">No coursework deliverables match your current search and filter criteria.</p>
                                <button class="btn btn-outline-secondary btn-sm" id="reset-filters-btn">
                                    <i class="bi bi-arrow-counterclockwise me-1"></i>Reset All Filters
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
                const resetBtn = document.getElementById('reset-filters-btn');
                if (resetBtn) resetBtn.addEventListener('click', resetAllFilters);
            }
            return;
        }

        tasksTableBody.innerHTML = filteredTasks.map(task => {
            const isCompleted = task.status === 'Completed';
            const catColor = task.category_color || '#64748b';
            const catName = task.category_name || 'General';
            const priorityClass = getPriorityBadgeClass(task.priority);
            const statusClass = getStatusBadgeClass(task.status);
            const formattedDate = formatDueDate(task.due_date);
            const overdue = isOverdue(task.due_date, isCompleted);

            return `
                <tr data-task-id="${task.id}">
                    <td>
                        <input class="form-check-input task-checkbox" 
                               type="checkbox" 
                               ${isCompleted ? 'checked' : ''} 
                               data-task-id="${task.id}"
                               title="Click to toggle completion">
                    </td>
                    <td>
                        <div class="task-title-cell ${isCompleted ? 'task-title-completed' : ''}">${escapeHtml(task.title)}</div>
                        ${task.description ? `<div class="text-muted small text-truncate" style="max-width: 320px;">${escapeHtml(task.description)}</div>` : ''}
                    </td>
                    <td>
                        <span class="badge-category" style="background-color: ${catColor}20; color: ${catColor}; border: 1px solid ${catColor}40;">
                            <span class="cat-dot" style="background-color: ${catColor};"></span>
                            ${escapeHtml(catName)}
                        </span>
                    </td>
                    <td><span class="badge-priority ${priorityClass}">${escapeHtml(task.priority || 'Medium')}</span></td>
                    <td><span class="badge-status ${statusClass}">${escapeHtml(task.status || 'Pending')}</span></td>
                    <td>
                        <span class="small ${overdue ? 'text-danger fw-semibold' : 'text-muted'}">
                            <i class="bi ${overdue ? 'bi-exclamation-circle-fill text-danger' : 'bi-calendar3'} me-1"></i>
                            ${formattedDate}
                        </span>
                    </td>
                    <td class="text-end">
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-light border btn-edit-task" data-task-id="${task.id}" title="Edit task" aria-label="Edit task: ${escapeHtml(task.title)}">
                                <i class="bi bi-pencil-square text-primary me-1"></i><span class="d-none d-sm-inline">Edit</span>
                            </button>
                            <button class="btn btn-light border text-danger btn-delete-task" data-task-id="${task.id}" data-task-title="${escapeHtml(task.title)}" title="Delete task" aria-label="Delete task: ${escapeHtml(task.title)}">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');

        attachTaskTableActions();
    }

    function attachTaskTableActions() {
        if (!tasksTableBody) return;

        tasksTableBody.querySelectorAll('.task-checkbox').forEach(chk => {
            chk.addEventListener('change', async (e) => {
                const taskId = e.target.getAttribute('data-task-id');
                const newStatus = e.target.checked ? 'Completed' : 'Pending';
                await mutateTaskStatus(taskId, newStatus);
            });
        });

        tasksTableBody.querySelectorAll('.btn-edit-task').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const taskId = btn.getAttribute('data-task-id');
                openTaskModalForEdit(taskId);
            });
        });

        tasksTableBody.querySelectorAll('.btn-delete-task').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const taskId = btn.getAttribute('data-task-id');
                const taskTitle = btn.getAttribute('data-task-title') || 'this task';
                openDeleteConfirmationModal(taskId, taskTitle);
            });
        });
    }

    function resetAllFilters() {
        const toolbarSearch = document.getElementById('toolbar-search-input');
        if (toolbarSearch) toolbarSearch.value = '';
        const navbarSearch = document.getElementById('tasks-search-input');
        if (navbarSearch) navbarSearch.value = '';

        const statusFilterBtns = document.querySelectorAll('.status-filter-btn');
        statusFilterBtns.forEach(b => {
            if (b.getAttribute('data-status') === 'all') {
                b.classList.add('btn-primary', 'active');
                b.classList.remove('btn-outline-secondary');
            } else {
                b.classList.remove('btn-primary', 'active');
                b.classList.add('btn-outline-secondary');
            }
        });

        const prioSelect = document.getElementById('priority-filter-select');
        if (prioSelect) prioSelect.value = 'all';

        const catSelect = document.getElementById('category-filter-select');
        if (catSelect) catSelect.value = 'all';

        applyTaskFilters();
    }

    function openTaskModalForCreate() {
        const modalEl = document.getElementById('taskModal');
        if (!modalEl) return;

        const titleEl = document.getElementById('modal-task-title');
        const dateEl = document.getElementById('modal-task-due-date');
        if (titleEl) titleEl.classList.remove('is-invalid');
        if (dateEl) dateEl.classList.remove('is-invalid');

        document.getElementById('modal-task-id').value = '';
        if (titleEl) titleEl.value = '';
        document.getElementById('modal-task-desc').value = '';
        document.getElementById('modal-task-priority').value = 'Medium';
        document.getElementById('modal-task-status').value = 'Pending';
        if (dateEl) dateEl.value = '';

        const errAlert = document.getElementById('modal-form-error');
        if (errAlert) errAlert.classList.add('d-none');

        document.getElementById('taskModalLabel').innerHTML = '<i class="bi bi-plus-circle text-primary me-2"></i>Create New Task';
        document.getElementById('modal-save-task-btn').innerHTML = '<i class="bi bi-check2 me-1"></i>Save Task';

        if (window.bootstrap) {
            const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
            modal.show();
        }
    }

    function openTaskModalForEdit(taskId) {
        const task = cachedTasks.find(t => String(t.id) === String(taskId));
        if (!task) return;

        const modalEl = document.getElementById('taskModal');
        if (!modalEl) return;

        const titleEl = document.getElementById('modal-task-title');
        const dateEl = document.getElementById('modal-task-due-date');
        if (titleEl) titleEl.classList.remove('is-invalid');
        if (dateEl) dateEl.classList.remove('is-invalid');

        document.getElementById('modal-task-id').value = task.id;
        if (titleEl) titleEl.value = task.title || '';
        document.getElementById('modal-task-desc').value = task.description || '';
        document.getElementById('modal-task-category').value = task.category_id || (cachedCategories[0] ? cachedCategories[0].id : '');
        document.getElementById('modal-task-priority').value = task.priority || 'Medium';
        document.getElementById('modal-task-status').value = task.status || 'Pending';
        if (dateEl) dateEl.value = task.due_date || '';

        const errAlert = document.getElementById('modal-form-error');
        if (errAlert) errAlert.classList.add('d-none');

        document.getElementById('taskModalLabel').innerHTML = '<i class="bi bi-pencil-square text-primary me-2"></i>Edit Task';
        document.getElementById('modal-save-task-btn').innerHTML = '<i class="bi bi-check2 me-1"></i>Update Task';

        if (window.bootstrap) {
            const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
            modal.show();
        }
    }

    async function handleTaskModalSubmit(e) {
        e.preventDefault();

        const taskId = document.getElementById('modal-task-id').value.trim();
        const titleEl = document.getElementById('modal-task-title');
        const descEl = document.getElementById('modal-task-desc');
        const catEl = document.getElementById('modal-task-category');
        const prioEl = document.getElementById('modal-task-priority');
        const statusEl = document.getElementById('modal-task-status');
        const dateEl = document.getElementById('modal-task-due-date');

        const title = titleEl ? titleEl.value.trim() : '';
        const desc = descEl ? descEl.value.trim() : '';
        const categoryId = catEl ? catEl.value : '';
        const priority = prioEl ? prioEl.value : 'Medium';
        const status = statusEl ? statusEl.value : 'Pending';
        const dueDate = dateEl ? dateEl.value : '';

        const saveBtn = document.getElementById('modal-save-task-btn');
        const errorAlert = document.getElementById('modal-form-error');

        // Frontend validation
        let hasError = false;
        if (!title) {
            if (titleEl) titleEl.classList.add('is-invalid');
            if (errorAlert) {
                errorAlert.textContent = 'Task title is required';
                errorAlert.classList.remove('d-none');
            }
            hasError = true;
        } else if (titleEl) {
            titleEl.classList.remove('is-invalid');
        }

        if (dueDate && !isValidCalendarDate(dueDate)) {
            if (dateEl) dateEl.classList.add('is-invalid');
            if (errorAlert) {
                errorAlert.textContent = 'Due date cannot be invalid';
                errorAlert.classList.remove('d-none');
            }
            hasError = true;
        } else if (dateEl) {
            dateEl.classList.remove('is-invalid');
        }

        if (hasError) return;

        if (errorAlert) errorAlert.classList.add('d-none');

        const payload = {
            title,
            description: desc || null,
            category_id: categoryId ? parseInt(categoryId) : null,
            priority,
            status,
            due_date: dueDate || null
        };

        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Saving...';
        }

        try {
            let res;
            const isEditing = Boolean(taskId);

            if (isEditing) {
                res = await window.TaskFlowAPI.updateTask(taskId, payload);
            } else {
                res = await window.TaskFlowAPI.createTask(payload);
            }

            if (res.ok) {
                const modalEl = document.getElementById('taskModal');
                if (modalEl && window.bootstrap) {
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    if (modal) modal.hide();
                }

                showTasksAlert('success', isEditing ? '✓ Task updated successfully!' : '✓ New task created and saved to database!');
                await loadTaskManagementData();
            } else {
                if (errorAlert) {
                    errorAlert.textContent = res.message || 'Validation error saving task.';
                    errorAlert.classList.remove('d-none');
                }
            }
        } catch (err) {
            console.error('Save task error:', err);
        } finally {
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.innerHTML = '<i class="bi bi-check2 me-1"></i>Save Task';
            }
        }
    }

    function openDeleteConfirmationModal(taskId, taskTitle) {
        taskPendingDeleteId = taskId;
        const titleEl = document.getElementById('delete-modal-task-title');
        if (titleEl) titleEl.textContent = `"${taskTitle}"`;

        const modalEl = document.getElementById('deleteConfirmModal');
        if (modalEl && window.bootstrap) {
            const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
            modal.show();
        } else {
            // Immediate confirmation fallback
            if (window.confirm("Are you sure you want to delete this task?")) {
                handleConfirmDelete();
            }
        }
    }

    async function handleConfirmDelete() {
        if (!taskPendingDeleteId) return;

        const deleteBtn = document.getElementById('confirm-delete-action-btn');
        if (deleteBtn) {
            deleteBtn.disabled = true;
            deleteBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Deleting...';
        }

        try {
            const res = await window.TaskFlowAPI.deleteTask(taskPendingDeleteId);

            const modalEl = document.getElementById('deleteConfirmModal');
            if (modalEl && window.bootstrap) {
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
            }

            if (res.ok) {
                showTasksAlert('success', '✓ Task permanently deleted from database.');
                await loadTaskManagementData();
            } else {
                showTasksAlert('warning', `Could not delete task: ${res.message}`);
            }
        } catch (err) {
            console.error('Delete task failed:', err);
            showTasksAlert('danger', 'Network error deleting task.');
        } finally {
            if (deleteBtn) {
                deleteBtn.disabled = false;
                deleteBtn.innerHTML = '<i class="bi bi-trash me-1"></i>Delete';
            }
            taskPendingDeleteId = null;
        }
    }

    async function mutateTaskStatus(taskId, newStatus) {
        try {
            const res = await window.TaskFlowAPI.updateTask(taskId, { status: newStatus });
            if (res.ok) {
                const index = cachedTasks.findIndex(t => String(t.id) === String(taskId));
                if (index !== -1) {
                    cachedTasks[index].status = newStatus;
                }
                applyTaskFilters();
            } else {
                showTasksAlert('warning', `Failed to update status: ${res.message}`);
            }
        } catch (err) {
            console.error('Status toggle failed:', err);
        }
    }

    // ========================================================================
    // Utility Formatting & Status Helpers
    // ========================================================================
    function getPriorityBadgeClass(prio) {
        const p = (prio || 'medium').toLowerCase();
        if (p === 'urgent') return 'priority-urgent';
        if (p === 'high') return 'priority-high';
        if (p === 'low') return 'priority-low';
        return 'priority-medium';
    }

    function getStatusBadgeClass(status) {
        const s = (status || 'pending').toLowerCase();
        if (s === 'completed') return 'status-badge-completed';
        if (s === 'in progress') return 'status-badge-in-progress';
        return 'status-badge-pending';
    }

    function formatDueDate(dateStr) {
        if (!dateStr) return 'No deadline';
        try {
            const parts = dateStr.split('-');
            if (parts.length === 3) {
                const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                const month = months[parseInt(parts[1], 10) - 1] || parts[1];
                return `${month} ${parts[2]}, ${parts[0]}`;
            }
            return dateStr;
        } catch {
            return dateStr;
        }
    }

    /**
     * Overdue calculation:
     * due_date < today AND status != Completed
     */
    function isOverdue(dateStr, isCompleted) {
        if (!dateStr || isCompleted) return false;
        try {
            const parts = dateStr.split('T')[0].split('-');
            if (parts.length === 3) {
                const due = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
                const today = new Date();
                today.setHours(0, 0, 0, 0);
                return due < today;
            }
        } catch (e) {
            // fallback
        }
        const due = new Date(dateStr);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return due < today;
    }

    function isValidCalendarDate(dateStr) {
        if (!dateStr || !dateStr.trim()) return true; // optional
        const parts = dateStr.trim().split('-');
        if (parts.length !== 3) return false;
        const y = parseInt(parts[0], 10);
        const m = parseInt(parts[1], 10);
        const d = parseInt(parts[2], 10);
        if (isNaN(y) || isNaN(m) || isNaN(d)) return false;
        if (y < 1900 || y > 2100 || m < 1 || m > 12 || d < 1 || d > 31) return false;
        const dt = new Date(y, m - 1, d);
        return dt.getFullYear() === y && dt.getMonth() === (m - 1) && dt.getDate() === d;
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // ========================================================================
    // Global Keyboard Navigation (Ctrl + K to focus search, Esc to blur)
    // ========================================================================
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) {
            const activeSearch = document.getElementById('toolbar-search-input') 
                || document.getElementById('tasks-search-input') 
                || document.getElementById('dashboard-search-input');
            if (activeSearch) {
                e.preventDefault();
                activeSearch.focus();
                if (typeof activeSearch.select === 'function') {
                    activeSearch.select();
                }
            }
        } else if (e.key === 'Escape') {
            const activeEl = document.activeElement;
            if (activeEl && (activeEl.id === 'toolbar-search-input' || activeEl.id === 'tasks-search-input' || activeEl.id === 'dashboard-search-input')) {
                activeEl.blur();
            }
        }
    });
});
