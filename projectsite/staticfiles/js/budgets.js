/* Budgets Page Scripts */

let currentBudget = null;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize
});

/* Open Create Budget Modal */
function openCreateBudgetModal() {
    document.getElementById('budgetForm').reset();
    document.getElementById('budget-id').value = '';
    document.getElementById('budgetModalLabel').textContent = 'Create Budget';
    document.getElementById('budget-currency').value = primaryCurrency;
    
    // Set default dates (first and last of current month)
    const today = new Date();
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
    const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);
    
    document.getElementById('budget-start-date').value = firstDay.toISOString().split('T')[0];
    document.getElementById('budget-end-date').value = lastDay.toISOString().split('T')[0];
    
    // Reset category filters
    toggleCategoryFilters();
    document.querySelectorAll('.budget-category').forEach(cb => cb.checked = false);
    
    const modal = new bootstrap.Modal(document.getElementById('budgetModal'));
    modal.show();
}

/* Toggle Category Filters Section */
function toggleCategoryFilters() {
    const budgetType = document.getElementById('budget-type').value;
    const section = document.getElementById('category-filters-section');
    
    if (budgetType === 'category_filter') {
        section.style.display = 'block';
    } else {
        section.style.display = 'none';
    }
}

/* View Budget Details */
function viewBudget(budgetId) {
    fetch(`/api/budget/${budgetId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentBudget = data.data;
                showBudgetDetailModal(data.data);
            } else {
                showToast('Error loading budget', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error loading budget', 'error');
        });
}

/* Show Budget Detail Modal */
function showBudgetDetailModal(budget) {
    document.getElementById('detail-name').textContent = budget.name;
    document.getElementById('detail-status').textContent = budget.status === 'active' ? 'Active' : 'Inactive';
    document.getElementById('detail-status').className = `badge ${budget.status === 'active' ? 'bg-success' : 'bg-secondary'}`;
    
    document.getElementById('detail-amount').textContent = `${budget.currency} ${parseFloat(budget.amount).toLocaleString('en-US', {minimumFractionDigits: 2})}`;
    document.getElementById('detail-spent').textContent = `${budget.currency} ${parseFloat(budget.spent_amount).toLocaleString('en-US', {minimumFractionDigits: 2})}`;
    document.getElementById('detail-remaining').textContent = `${budget.currency} ${parseFloat(budget.remaining_amount).toLocaleString('en-US', {minimumFractionDigits: 2})}`;
    
    const startDate = new Date(budget.start_date).toLocaleDateString('en-US', {month: 'short', day: 'numeric', year: 'numeric'});
    const endDate = budget.end_date ? new Date(budget.end_date).toLocaleDateString('en-US', {month: 'short', day: 'numeric', year: 'numeric'}) : 'No end date';
    document.getElementById('detail-period').textContent = `${startDate} - ${endDate}`;
    
    const recurrenceLabels = {
        'one_time': 'One Time',
        'daily': 'Daily',
        'weekly': 'Weekly', 
        'monthly': 'Monthly',
        'yearly': 'Yearly'
    };
    document.getElementById('detail-recurrence').textContent = recurrenceLabels[budget.recurrence_pattern] || budget.recurrence_pattern;
    
    document.getElementById('detail-type').textContent = budget.budget_type === 'category_filter' ? 'Category Filter' : 'Manual';
    
    // Show categories if applicable
    const categoriesRow = document.getElementById('detail-categories-row');
    if (budget.budget_type === 'category_filter' && budget.category_names && budget.category_names.length > 0) {
        categoriesRow.style.display = 'flex';
        document.getElementById('detail-categories').textContent = budget.category_names.join(', ');
    } else {
        categoriesRow.style.display = 'none';
    }
    
    // Update toggle button
    const toggleBtn = document.getElementById('btn-toggle-status');
    if (budget.status === 'active') {
        toggleBtn.innerHTML = '<i class="bi bi-pause-circle me-1"></i>Deactivate';
        toggleBtn.classList.remove('btn-success');
        toggleBtn.classList.add('btn-outline-secondary');
    } else {
        toggleBtn.innerHTML = '<i class="bi bi-play-circle me-1"></i>Activate';
        toggleBtn.classList.remove('btn-outline-secondary');
        toggleBtn.classList.add('btn-success');
    }
    
    const modal = new bootstrap.Modal(document.getElementById('budgetDetailModal'));
    modal.show();
}

/* Open Edit Budget Modal */
function openEditBudgetModal() {
    if (!currentBudget) return;
    
    bootstrap.Modal.getInstance(document.getElementById('budgetDetailModal')).hide();
    
    document.getElementById('budget-id').value = currentBudget.id;
    document.getElementById('budget-name').value = currentBudget.name;
    document.getElementById('budget-amount').value = currentBudget.amount;
    document.getElementById('budget-currency').value = currentBudget.currency;
    document.getElementById('budget-start-date').value = currentBudget.start_date;
    document.getElementById('budget-end-date').value = currentBudget.end_date || '';
    document.getElementById('budget-recurrence').value = currentBudget.recurrence_pattern;
    document.getElementById('budget-type').value = currentBudget.budget_type;
    
    // Handle category filters
    toggleCategoryFilters();
    document.querySelectorAll('.budget-category').forEach(cb => {
        cb.checked = currentBudget.category_ids && currentBudget.category_ids.includes(cb.value);
    });
    
    document.getElementById('budgetModalLabel').textContent = 'Edit Budget';
    
    const modal = new bootstrap.Modal(document.getElementById('budgetModal'));
    modal.show();
}

/* Save Budget */
function saveBudget() {
    const id = document.getElementById('budget-id').value;
    
    const data = {
        name: document.getElementById('budget-name').value,
        amount: document.getElementById('budget-amount').value,
        currency: document.getElementById('budget-currency').value,
        start_date: document.getElementById('budget-start-date').value,
        end_date: document.getElementById('budget-end-date').value || null,
        recurrence_pattern: document.getElementById('budget-recurrence').value,
        budget_type: document.getElementById('budget-type').value,
    };
    
    // Get selected categories if category_filter type
    if (data.budget_type === 'category_filter') {
        const selectedCategories = [];
        document.querySelectorAll('.budget-category:checked').forEach(cb => {
            selectedCategories.push(cb.value);
        });
        data.category_ids = selectedCategories;
    }
    
    const url = id ? `/api/budget/${id}/update/` : '/api/budget/create/';
    
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
            showToast(data.message || 'Budget saved successfully', 'success');
            bootstrap.Modal.getInstance(document.getElementById('budgetModal')).hide();
            setTimeout(() => window.location.reload(), 500);
        } else {
            showToast(data.error || 'Error saving budget', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred', 'error');
    });
}

/* Toggle Budget Status (Active/Inactive) */
function toggleBudgetStatus() {
    if (!currentBudget) return;
    
    const newStatus = currentBudget.status === 'active' ? 'inactive' : 'active';
    
    fetch(`/api/budget/${currentBudget.id}/toggle-status/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({ status: newStatus }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message || 'Budget status updated', 'success');
            bootstrap.Modal.getInstance(document.getElementById('budgetDetailModal')).hide();
            setTimeout(() => window.location.reload(), 500);
        } else {
            showToast(data.error || 'Error updating status', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred', 'error');
    });
}

/* Open Delete Budget Modal */
function openDeleteBudgetModal() {
    if (!currentBudget) return;
    
    bootstrap.Modal.getInstance(document.getElementById('budgetDetailModal')).hide();
    document.getElementById('delete-budget-name').textContent = currentBudget.name;
    
    const modal = new bootstrap.Modal(document.getElementById('deleteBudgetModal'));
    modal.show();
}

/* Confirm Delete Budget */
function confirmDeleteBudget() {
    if (!currentBudget) return;
    
    fetch(`/api/budget/${currentBudget.id}/delete/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message || 'Budget deleted', 'success');
            bootstrap.Modal.getInstance(document.getElementById('deleteBudgetModal')).hide();
            setTimeout(() => window.location.reload(), 500);
        } else {
            showToast(data.error || 'Error deleting budget', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred', 'error');
    });
}

/* Show Toast Notification */
function showToast(message, type = 'info') {
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