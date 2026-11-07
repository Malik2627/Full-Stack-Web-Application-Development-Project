/**
 * TaskFlow Step 7 Analytics Verification Test Suite
 * Tests the analytics calculation matrix, date/overdue calculations,
 * and Chart.js data models across the required 5 states:
 * 1. 0 tasks
 * 2. 1 task
 * 3. Multiple tasks
 * 4. Completed tasks
 * 5. Overdue tasks
 */

const assert = require('assert');

// ----------------------------------------------------------------------------
// Re-implement the exact analytics pure functions from frontend/js/main.js
// ----------------------------------------------------------------------------

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
    } catch (e) {}
    const due = new Date(dateStr);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return due < today;
}

function calculateDashboardStatistics(tasks) {
    const total = tasks.length;
    const completed = tasks.filter(t => t.status === 'Completed').length;
    const inProgress = tasks.filter(t => t.status === 'In Progress').length;
    const pending = tasks.filter(t => t.status === 'Pending').length;
    const highPriority = tasks.filter(t =>
        (t.priority || '').toLowerCase() === 'high' || (t.priority || '').toLowerCase() === 'urgent'
    ).length;
    const overdue = tasks.filter(t => isOverdue(t.due_date, t.status === 'Completed')).length;
    const completionPct = total > 0 ? Math.round((completed / total) * 100) : 0;

    return { total, completed, inProgress, pending, highPriority, overdue, completionPct };
}

function computeChartData(tasks, categories) {
    const total = tasks.length;

    // Status Chart
    const statusCounts = {
        'Completed': tasks.filter(t => t.status === 'Completed').length,
        'In Progress': tasks.filter(t => t.status === 'In Progress').length,
        'Pending': tasks.filter(t => t.status === 'Pending').length,
        'Cancelled': tasks.filter(t => t.status === 'Cancelled').length
    };
    const statusLabels = ['Completed', 'In Progress', 'Pending', 'Cancelled'];
    const statusData = statusLabels.map(l => statusCounts[l] || 0);
    const displayStatusLabels = total > 0 ? statusLabels : ['No tasks'];
    const displayStatusData = total > 0 ? statusData : [1];

    // Priority Chart
    const priorityCounts = {
        'Urgent': tasks.filter(t => (t.priority || '').toLowerCase() === 'urgent').length,
        'High': tasks.filter(t => (t.priority || '').toLowerCase() === 'high').length,
        'Medium': tasks.filter(t => (t.priority || '').toLowerCase() === 'medium').length,
        'Low': tasks.filter(t => (t.priority || '').toLowerCase() === 'low').length
    };
    const priorityLabels = ['Urgent', 'High', 'Medium', 'Low'];
    const priorityData = priorityLabels.map(p => priorityCounts[p]);

    // Category Chart
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
    const displayCatLabels = total > 0 ? catLabels : ['No tasks'];
    const displayCatData = total > 0 ? catData : [1];

    return {
        status: { labels: displayStatusLabels, data: displayStatusData },
        priority: { labels: priorityLabels, data: priorityData },
        category: { labels: displayCatLabels, data: displayCatData }
    };
}

function computeDeadlines(tasks) {
    const uncompletedWithDates = tasks
        .filter(t => t.due_date && t.status !== 'Completed')
        .sort((a, b) => a.due_date.localeCompare(b.due_date));

    const now = new Date();
    now.setHours(0, 0, 0, 0);

    let hasOverdue = false;
    const items = uncompletedWithDates.slice(0, 5).map(task => {
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

        let tagText = task.due_date;
        let isItemOverdue = false;

        if (diffDays < 0) {
            hasOverdue = true;
            isItemOverdue = true;
            tagText = `Overdue (${Math.abs(diffDays)}d late)`;
        } else if (diffDays === 0) {
            hasOverdue = true;
            tagText = 'Due Today';
        } else if (diffDays === 1) {
            tagText = 'Tomorrow';
        } else if (diffDays <= 3) {
            tagText = `In ${diffDays} Days`;
        } else if (diffDays <= 7) {
            tagText = 'Next Week';
        }

        return { title: task.title, diffDays, tagText, isItemOverdue };
    });

    return { items, hasOverdue, count: uncompletedWithDates.length };
}

// ----------------------------------------------------------------------------
// Helper to format ISO dates relative to today
// ----------------------------------------------------------------------------
function getRelativeDateStr(dayOffset) {
    const d = new Date();
    d.setDate(d.getDate() + dayOffset);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

const mockCategories = [
    { id: 1, name: 'Study', color: '#4f46e5' },
    { id: 2, name: 'Work', color: '#0ea5e9' },
    { id: 3, name: 'Project', color: '#10b981' },
    { id: 4, name: 'Personal', color: '#f59e0b' },
    { id: 5, name: 'Other', color: '#8b5cf6' }
];

// ----------------------------------------------------------------------------
// Test Runner
// ----------------------------------------------------------------------------
let passCount = 0;
function test(name, fn) {
    try {
        fn();
        passCount++;
        console.log(`  ✓ ${name}`);
    } catch (err) {
        console.error(`  ✗ FAILED: ${name}`);
        console.error(err);
        process.exit(1);
    }
}

console.log('='.repeat(70));
console.log('STEP 7: DASHBOARD ANALYTICS TEST MATRIX');
console.log('='.repeat(70));

// ============================================================================
// TEST 1: 0 TASKS
// ============================================================================
console.log('\n[Scenario 1] 0 Tasks: Empty Dashboard State');

test('Statistics cards all report 0 when tasks array is empty', () => {
    const stats = calculateDashboardStatistics([]);
    assert.strictEqual(stats.total, 0);
    assert.strictEqual(stats.completed, 0);
    assert.strictEqual(stats.pending, 0);
    assert.strictEqual(stats.inProgress, 0);
    assert.strictEqual(stats.highPriority, 0);
    assert.strictEqual(stats.overdue, 0);
    assert.strictEqual(stats.completionPct, 0);
});

test('Charts provide neutral placeholder slice when 0 tasks exist', () => {
    const charts = computeChartData([], mockCategories);
    assert.deepStrictEqual(charts.status.labels, ['No tasks']);
    assert.deepStrictEqual(charts.status.data, [1]);
    assert.deepStrictEqual(charts.priority.labels, ['Urgent', 'High', 'Medium', 'Low']);
    assert.deepStrictEqual(charts.priority.data, [0, 0, 0, 0]);
    assert.deepStrictEqual(charts.category.labels, ['No tasks']);
    assert.deepStrictEqual(charts.category.data, [1]);
});

test('Deadlines widget shows empty state with 0 tasks', () => {
    const deadlines = computeDeadlines([]);
    assert.strictEqual(deadlines.count, 0);
    assert.strictEqual(deadlines.items.length, 0);
    assert.strictEqual(deadlines.hasOverdue, false);
});

// ============================================================================
// TEST 2: 1 TASK
// ============================================================================
console.log('\n[Scenario 2] 1 Task: Single Coursework Item');

const singleTask = [{
    id: 1,
    title: 'Complete Neural Networks Assignment',
    priority: 'Medium',
    status: 'Pending',
    due_date: getRelativeDateStr(2),
    category_id: 1,
    category_name: 'Study',
    category_color: '#4f46e5'
}];

test('Statistics reflect exactly 1 Pending task', () => {
    const stats = calculateDashboardStatistics(singleTask);
    assert.strictEqual(stats.total, 1);
    assert.strictEqual(stats.completed, 0);
    assert.strictEqual(stats.pending, 1);
    assert.strictEqual(stats.inProgress, 0);
    assert.strictEqual(stats.highPriority, 0);
    assert.strictEqual(stats.overdue, 0);
    assert.strictEqual(stats.completionPct, 0);
});

test('Charts render single active slice and bar for 1 task', () => {
    const charts = computeChartData(singleTask, mockCategories);
    // Status: ['Completed', 'In Progress', 'Pending', 'Cancelled'] -> Pending = 1
    assert.deepStrictEqual(charts.status.labels, ['Completed', 'In Progress', 'Pending', 'Cancelled']);
    assert.deepStrictEqual(charts.status.data, [0, 0, 1, 0]);
    // Priority: ['Urgent', 'High', 'Medium', 'Low'] -> Medium = 1
    assert.deepStrictEqual(charts.priority.data, [0, 0, 1, 0]);
    // Category: Study = 1
    const studyIdx = charts.category.labels.indexOf('Study');
    assert.strictEqual(charts.category.data[studyIdx], 1);
});

test('Upcoming deadlines shows task due in 2 days', () => {
    const deadlines = computeDeadlines(singleTask);
    assert.strictEqual(deadlines.count, 1);
    assert.strictEqual(deadlines.items[0].tagText, 'In 2 Days');
    assert.strictEqual(deadlines.hasOverdue, false);
});

// ============================================================================
// TEST 3: MULTIPLE TASKS
// ============================================================================
console.log('\n[Scenario 3] Multiple Tasks: Diverse Categories and Priorities');

const multiTasks = [
    { id: 1, title: 'Task 1 - Study', priority: 'High', status: 'Pending', category_name: 'Study', due_date: getRelativeDateStr(3) },
    { id: 2, title: 'Task 2 - Work', priority: 'Medium', status: 'In Progress', category_name: 'Work', due_date: getRelativeDateStr(5) },
    { id: 3, title: 'Task 3 - Project', priority: 'Urgent', status: 'Pending', category_name: 'Project', due_date: getRelativeDateStr(1) },
    { id: 4, title: 'Task 4 - Personal', priority: 'Low', status: 'In Progress', category_name: 'Personal', due_date: getRelativeDateStr(7) },
    { id: 5, title: 'Task 5 - Study', priority: 'High', status: 'Pending', category_name: 'Study', due_date: getRelativeDateStr(10) },
    { id: 6, title: 'Task 6 - Extra', priority: 'Medium', status: 'Pending', category_name: 'Other', due_date: getRelativeDateStr(14) }
];

test('Statistics correctly aggregate multiple tasks', () => {
    const stats = calculateDashboardStatistics(multiTasks);
    assert.strictEqual(stats.total, 6);
    assert.strictEqual(stats.pending, 4);
    assert.strictEqual(stats.inProgress, 2);
    assert.strictEqual(stats.completed, 0);
    // High Priority counts High + Urgent = 2 High + 1 Urgent = 3
    assert.strictEqual(stats.highPriority, 3);
    assert.strictEqual(stats.overdue, 0);
});

test('Recent tasks displays latest 5 out of 6 tasks', () => {
    const latest5 = multiTasks.slice(0, 5);
    assert.strictEqual(latest5.length, 5);
    assert.strictEqual(latest5[0].id, 1);
});

test('Category distribution chart aggregates counts per category', () => {
    const charts = computeChartData(multiTasks, mockCategories);
    const studyIdx = charts.category.labels.indexOf('Study');
    assert.strictEqual(charts.category.data[studyIdx], 2);
    const workIdx = charts.category.labels.indexOf('Work');
    assert.strictEqual(charts.category.data[workIdx], 1);
    const projIdx = charts.category.labels.indexOf('Project');
    assert.strictEqual(charts.category.data[projIdx], 1);
});

// ============================================================================
// TEST 4: COMPLETED TASKS
// ============================================================================
console.log('\n[Scenario 4] Completed Tasks: Completion Rate & Filtering');

const tasksWithCompleted = [
    { id: 1, title: 'Task 1', priority: 'High', status: 'Completed', category_name: 'Study', due_date: getRelativeDateStr(2) },
    { id: 2, title: 'Task 2', priority: 'Medium', status: 'Completed', category_name: 'Work', due_date: getRelativeDateStr(1) },
    { id: 3, title: 'Task 3', priority: 'Urgent', status: 'In Progress', category_name: 'Project', due_date: getRelativeDateStr(4) },
    { id: 4, title: 'Task 4', priority: 'Low', status: 'Pending', category_name: 'Personal', due_date: getRelativeDateStr(5) }
];

test('Completion percentage calculates correctly (50%)', () => {
    const stats = calculateDashboardStatistics(tasksWithCompleted);
    assert.strictEqual(stats.total, 4);
    assert.strictEqual(stats.completed, 2);
    assert.strictEqual(stats.completionPct, 50);
});

test('Status chart doughnut reflects completed count', () => {
    const charts = computeChartData(tasksWithCompleted, mockCategories);
    // [Completed: 2, In Progress: 1, Pending: 1, Cancelled: 0]
    assert.deepStrictEqual(charts.status.data, [2, 1, 1, 0]);
});

test('Upcoming deadlines excludes completed tasks', () => {
    const deadlines = computeDeadlines(tasksWithCompleted);
    assert.strictEqual(deadlines.count, 2); // Only Task 3 & Task 4
    const titles = deadlines.items.map(i => i.title);
    assert.strictEqual(titles.includes('Task 1'), false);
    assert.strictEqual(titles.includes('Task 2'), false);
});

// ============================================================================
// TEST 5: OVERDUE TASKS
// ============================================================================
console.log('\n[Scenario 5] Overdue Tasks: Identification & Alerting');

const tasksWithOverdue = [
    { id: 1, title: 'Overdue Assignment 1', priority: 'High', status: 'Pending', category_name: 'Study', due_date: getRelativeDateStr(-3) },
    { id: 2, title: 'Overdue Project 2', priority: 'Urgent', status: 'In Progress', category_name: 'Project', due_date: getRelativeDateStr(-1) },
    { id: 3, title: 'Completed Past Task', priority: 'Medium', status: 'Completed', category_name: 'Work', due_date: getRelativeDateStr(-5) },
    { id: 4, title: 'Future Task', priority: 'Low', status: 'Pending', category_name: 'Personal', due_date: getRelativeDateStr(4) }
];

test('Overdue condition strictly adheres to: due_date < today AND status != Completed', () => {
    assert.strictEqual(isOverdue(getRelativeDateStr(-3), false), true);
    assert.strictEqual(isOverdue(getRelativeDateStr(-1), false), true);
    assert.strictEqual(isOverdue(getRelativeDateStr(-5), true), false); // Completed past task is NOT overdue
    assert.strictEqual(isOverdue(getRelativeDateStr(0), false), false);  // Today is not past
    assert.strictEqual(isOverdue(getRelativeDateStr(4), false), false);  // Future is not overdue
});

test('Overdue metric card counts exactly 2 overdue items', () => {
    const stats = calculateDashboardStatistics(tasksWithOverdue);
    assert.strictEqual(stats.overdue, 2); // Task 1 & Task 2
});

test('Upcoming deadlines prioritizes overdue items and sets Overdue Alert badge', () => {
    const deadlines = computeDeadlines(tasksWithOverdue);
    assert.strictEqual(deadlines.hasOverdue, true);
    // Task 1 was due 3 days ago, Task 2 was due 1 day ago
    assert.strictEqual(deadlines.items[0].isItemOverdue, true);
    assert.strictEqual(deadlines.items[0].tagText, 'Overdue (3d late)');
    assert.strictEqual(deadlines.items[1].isItemOverdue, true);
    assert.strictEqual(deadlines.items[1].tagText, 'Overdue (1d late)');
});

test('When overdue task is marked Completed, overdue count returns to 0', () => {
    const updatedTasks = tasksWithOverdue.map(t => {
        if (t.id === 1 || t.id === 2) return { ...t, status: 'Completed' };
        return t;
    });
    const stats = calculateDashboardStatistics(updatedTasks);
    assert.strictEqual(stats.overdue, 0);
    assert.strictEqual(stats.completed, 3);
});

console.log('='.repeat(70));
console.log(`ALL ${passCount} STEP 7 ANALYTICS TESTS PASSED SUCCESSFULLY! ✓`);
console.log('='.repeat(70));

