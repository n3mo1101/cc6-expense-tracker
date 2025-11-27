/* Dashboard Charts and Interactions */

let spendingChart;
let categoryChart;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initSpendingChart('yearly');
    initCategoryChart();
});

// Spending Trends Chart
function initSpendingChart(type) {
    const ctx = document.getElementById('spendingTrendsChart');
    if (!ctx) return;
    
    if (spendingChart) {
        spendingChart.destroy();
    }

    const data = type === 'yearly' ? spendingTrendsData : currentMonthData;
    const tooltipLabels = type === 'monthly' ? currentMonthData.tooltip_labels : null;

    spendingChart = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Expenses',
                data: data.data,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: '#667eea',
                pointHoverBorderColor: '#fff',
                pointHoverBorderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index',
            },
            plugins: {
                legend: {
                    display: false,
                },
                tooltip: {
                    backgroundColor: '#1F2937',
                    titleColor: '#F9FAFB',
                    bodyColor: '#F9FAFB',
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        title: function(context) {
                            if (tooltipLabels && context[0]) {
                                return tooltipLabels[context[0].dataIndex];
                            }
                            return context[0].label;
                        },
                        label: function(context) {
                            return dashboardCurrency + ' ' + context.parsed.y.toLocaleString('en-US', {minimumFractionDigits: 2});
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false,
                    },
                    ticks: {
                        maxRotation: 0,
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return dashboardCurrency + ' ' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

// Toggle between yearly and monthly view
function toggleTrendsChart(type) {
    initSpendingChart(type);
    
    const btnYearly = document.getElementById('btn-yearly');
    const btnMonthly = document.getElementById('btn-monthly');
    
    if (type === 'yearly') {
        btnYearly.classList.add('active');
        btnMonthly.classList.remove('active');
    } else {
        btnMonthly.classList.add('active');
        btnYearly.classList.remove('active');
    }
}

// Category Donut Chart
function initCategoryChart() {
    const ctx = document.getElementById('categoryChart');
    if (!ctx) return;
    
    // Handle empty data
    if (!categoryData.data || categoryData.data.length === 0) {
        ctx.parentElement.innerHTML = '<div class="text-center text-muted py-5"><i class="bi bi-pie-chart fs-1 mb-2 d-block opacity-50"></i>No expenses this month</div>';
        return;
    }
    
    categoryChart = new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: categoryData.labels,
            datasets: [{
                data: categoryData.data,
                backgroundColor: categoryData.colors,
                borderWidth: 0,
                hoverOffset: 4,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    display: false,
                },
                tooltip: {
                    backgroundColor: '#1F2937',
                    titleColor: '#F9FAFB',
                    bodyColor: '#F9FAFB',
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return dashboardCurrency + ' ' + context.parsed.toLocaleString('en-US', {minimumFractionDigits: 2}) + ' (' + percentage + '%)';
                        }
                    }
                }
            }
        }
    });

    // Build custom legend
    buildCategoryLegend();
}

// Custom legend for category chart
function buildCategoryLegend() {
    const legendContainer = document.getElementById('categoryLegend');
    if (!legendContainer) return;
    
    if (!categoryData.labels || categoryData.labels.length === 0) {
        legendContainer.innerHTML = '';
        return;
    }
    
    legendContainer.innerHTML = '';
    const total = categoryData.data.reduce((a, b) => a + b, 0);

    categoryData.labels.forEach((label, index) => {
        const percentage = total > 0 ? ((categoryData.data[index] / total) * 100).toFixed(0) : 0;
        
        const item = document.createElement('div');
        item.className = 'category-legend-item';
        item.innerHTML = `
            <div class="d-flex align-items-center">
                <span class="category-dot" style="background-color: ${categoryData.colors[index]}"></span>
                <span class="text-muted">${label}</span>
            </div>
            <span class="fw-semibold">${percentage}%</span>
        `;
        legendContainer.appendChild(item);
    });
}

/* Transaction Modal Functions */

function openCreateIncomeModal() {
    document.getElementById('incomeForm').reset();
    document.getElementById('income-id').value = '';
    document.getElementById('incomeModalLabel').textContent = 'Add Income';
    document.getElementById('income-date').value = new Date().toISOString().split('T')[0];
    document.getElementById('income-currency').value = dashboardCurrency;
    
    // Reset recurring fields
    toggleRecurringFields('income', false);
    
    const modal = new bootstrap.Modal(document.getElementById('incomeModal'));
    modal.show();
}

function openCreateExpenseModal() {
    document.getElementById('expenseForm').reset();
    document.getElementById('expense-id').value = '';
    document.getElementById('expenseModalLabel').textContent = 'Add Expense';
    document.getElementById('expense-date').value = new Date().toISOString().split('T')[0];
    document.getElementById('expense-currency').value = dashboardCurrency;
    
    // Reset recurring fields
    toggleRecurringFields('expense', false);
    
    const modal = new bootstrap.Modal(document.getElementById('expenseModal'));
    modal.show();
}

/* Toggle Recurring Fields */
function toggleRecurringFields(type, show) {
    const recurringFields = document.getElementById(`${type}-recurring-fields`);
    const recurringCheckbox = document.getElementById(`${type}-is-recurring`);
    
    if (recurringFields) {
        recurringFields.style.display = show ? 'block' : 'none';
    }
    if (recurringCheckbox) {
        recurringCheckbox.checked = show;
    }
}

/* Save Income */
function saveIncome() {
    const id = document.getElementById('income-id').value;
    const isRecurring = document.getElementById('income-is-recurring')?.checked || false;
    
    const data = {
        source_id: document.getElementById('income-source').value,
        amount: document.getElementById('income-amount').value,
        currency: document.getElementById('income-currency').value,
        transaction_date: document.getElementById('income-date').value,
        description: document.getElementById('income-description').value,
        status: document.getElementById('income-status').value,
    };
    
    // Add recurring fields if checked
    if (isRecurring) {
        data.is_recurring = true;
        data.recurrence_pattern = document.getElementById('income-recurrence-pattern')?.value || 'monthly';
        data.recurrence_end_date = document.getElementById('income-recurrence-end')?.value || null;
    }
    
    const url = id ? `/api/transaction/income/${id}/update/` : '/api/income/create/';
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message || 'Income saved successfully', 'success');
            bootstrap.Modal.getInstance(document.getElementById('incomeModal')).hide();
            // Reload page to refresh dashboard data
            setTimeout(() => window.location.reload(), 500);
        } else {
            showToast(data.error || 'Error saving income', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred', 'error');
    });
}

/* Save Expense */
function saveExpense() {
    const id = document.getElementById('expense-id').value;
    const isRecurring = document.getElementById('expense-is-recurring')?.checked || false;
    
    const data = {
        category_id: document.getElementById('expense-category').value,
        amount: document.getElementById('expense-amount').value,
        currency: document.getElementById('expense-currency').value,
        transaction_date: document.getElementById('expense-date').value,
        description: document.getElementById('expense-description').value,
        status: document.getElementById('expense-status').value,
        budget_id: document.getElementById('expense-budget')?.value || null,
    };
    
    // Add recurring fields if checked
    if (isRecurring) {
        data.is_recurring = true;
        data.recurrence_pattern = document.getElementById('expense-recurrence-pattern')?.value || 'monthly';
        data.recurrence_end_date = document.getElementById('expense-recurrence-end')?.value || null;
    }
    
    const url = id ? `/api/transaction/expense/${id}/update/` : '/api/expense/create/';
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message || 'Expense saved successfully', 'success');
            bootstrap.Modal.getInstance(document.getElementById('expenseModal')).hide();
            // Reload page to refresh dashboard data
            setTimeout(() => window.location.reload(), 500);
        } else {
            showToast(data.error || 'Error saving expense', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred', 'error');
    });
}

/* Show Toast Notification */
function showToast(message, type = 'info') {
    // Check if toast container exists, create if not
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    const toastId = 'toast-' + Date.now();
    const bgClass = type === 'success' ? 'bg-success' : type === 'error' ? 'bg-danger' : 'bg-primary';
    
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    const toastEl = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastEl, { autohide: true, delay: 3000 });
    toast.show();
    
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

/* ===== TRANSACTION INTERACTION FUNCTIONS ===== */

let currentDashboardTransaction = null;

/* View Transaction from Dashboard */
function viewDashboardTransaction(type, id) {
    fetch(`/api/transaction/${type}/${id}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentDashboardTransaction = data.data;
                showTransactionDetailModal(data.data);
            } else {
                showToast('Error loading transaction', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error loading transaction', 'error');
        });
}

/* Show Transaction Detail Modal */
function showTransactionDetailModal(transaction) {
    const modal = document.getElementById('transactionDetailModal');
    
    document.getElementById('detail-type').textContent = transaction.type === 'income' ? 'Income' : 'Expense';
    document.getElementById('detail-type').className = `badge ${transaction.type === 'income' ? 'bg-success' : 'bg-danger'}`;
    document.getElementById('detail-name').textContent = transaction.name;
    document.getElementById('detail-amount').textContent = `${transaction.currency} ${parseFloat(transaction.amount).toLocaleString('en-US', {minimumFractionDigits: 2})}`;
    document.getElementById('detail-amount').className = `detail-value ${transaction.type}`;
    
    if (transaction.converted_amount && transaction.currency !== dashboardCurrency) {
        document.getElementById('detail-converted').textContent = `${dashboardCurrency} ${parseFloat(transaction.converted_amount).toLocaleString('en-US', {minimumFractionDigits: 2})}`;
        document.getElementById('detail-converted-row').style.display = 'flex';
    } else {
        document.getElementById('detail-converted-row').style.display = 'none';
    }
    
    document.getElementById('detail-date').textContent = new Date(transaction.date).toLocaleDateString('en-US', {
        year: 'numeric', month: 'long', day: 'numeric'
    });
    
    document.getElementById('detail-status').textContent = transaction.status.charAt(0).toUpperCase() + transaction.status.slice(1);
    document.getElementById('detail-status').className = `status-badge ${transaction.status}`;
    
    document.getElementById('detail-description').textContent = transaction.description || '-';
    
    const completeBtn = document.getElementById('btn-mark-complete');
    if (transaction.status === 'pending') {
        completeBtn.style.display = 'inline-block';
    } else {
        completeBtn.style.display = 'none';
    }
    
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

/* Open Edit Transaction Modal */
function openEditTransactionModal() {
    if (!currentDashboardTransaction) return;
    
    bootstrap.Modal.getInstance(document.getElementById('transactionDetailModal')).hide();
    
    if (currentDashboardTransaction.type === 'income') {
        document.getElementById('income-id').value = currentDashboardTransaction.id;
        document.getElementById('income-source').value = currentDashboardTransaction.source_id;
        document.getElementById('income-amount').value = currentDashboardTransaction.amount;
        document.getElementById('income-currency').value = currentDashboardTransaction.currency;
        document.getElementById('income-date').value = currentDashboardTransaction.date;
        document.getElementById('income-description').value = currentDashboardTransaction.description || '';
        document.getElementById('income-status').value = currentDashboardTransaction.status;
        document.getElementById('incomeModalLabel').textContent = 'Edit Income';
        
        toggleRecurringFields('income', false);
        
        const modal = new bootstrap.Modal(document.getElementById('incomeModal'));
        modal.show();
    } else {
        document.getElementById('expense-id').value = currentDashboardTransaction.id;
        document.getElementById('expense-category').value = currentDashboardTransaction.category_id;
        document.getElementById('expense-amount').value = currentDashboardTransaction.amount;
        document.getElementById('expense-currency').value = currentDashboardTransaction.currency;
        document.getElementById('expense-date').value = currentDashboardTransaction.date;
        document.getElementById('expense-description').value = currentDashboardTransaction.description || '';
        document.getElementById('expense-status').value = currentDashboardTransaction.status;
        document.getElementById('expense-budget').value = currentDashboardTransaction.budget_id || '';
        document.getElementById('expenseModalLabel').textContent = 'Edit Expense';
        
        toggleRecurringFields('expense', false);
        
        const modal = new bootstrap.Modal(document.getElementById('expenseModal'));
        modal.show();
    }
}

/* Mark Transaction Complete */
function markTransactionComplete() {
    if (!currentDashboardTransaction) return;
    
    fetch(`/api/transaction/${currentDashboardTransaction.type}/${currentDashboardTransaction.id}/complete/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message || 'Transaction marked as complete', 'success');
            bootstrap.Modal.getInstance(document.getElementById('transactionDetailModal')).hide();
            setTimeout(() => window.location.reload(), 500);
        } else {
            showToast(data.error || 'Error updating transaction', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred', 'error');
    });
}

/* Open Delete Transaction Modal */
function openDeleteTransactionModal() {
    if (!currentDashboardTransaction) return;
    
    bootstrap.Modal.getInstance(document.getElementById('transactionDetailModal')).hide();
    document.getElementById('delete-transaction-name').textContent = currentDashboardTransaction.name;
    
    const modal = new bootstrap.Modal(document.getElementById('deleteTransactionModal'));
    modal.show();
}

/* Confirm Delete Transaction */
function confirmDeleteTransaction() {
    if (!currentDashboardTransaction) return;
    
    fetch(`/api/transaction/${currentDashboardTransaction.type}/${currentDashboardTransaction.id}/delete/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message || 'Transaction deleted', 'success');
            bootstrap.Modal.getInstance(document.getElementById('deleteTransactionModal')).hide();
            setTimeout(() => window.location.reload(), 500);
        } else {
            showToast(data.error || 'Error deleting transaction', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred', 'error');
    });
}