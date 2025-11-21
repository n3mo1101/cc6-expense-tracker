/* Transactions Page Scripts */

let currentTransaction = null;

document.addEventListener('DOMContentLoaded', function() {
    initFilters();
    initTransactionRows();
});

/* Initialize Filters */
function initFilters() {
    const searchInput = document.getElementById('searchInput');
    const categoryFilter = document.getElementById('categoryFilter');
    const statusFilter = document.getElementById('statusFilter');
    
    let searchTimeout;
    
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => applyFilters(), 500);
        });
    }
    
    if (categoryFilter) {
        categoryFilter.addEventListener('change', applyFilters);
    }
    
    if (statusFilter) {
        statusFilter.addEventListener('change', applyFilters);
    }
}

/* Apply Filters */
function applyFilters() {
    const params = new URLSearchParams(window.location.search);
    
    const search = document.getElementById('searchInput')?.value || '';
    const category = document.getElementById('categoryFilter')?.value || '';
    const status = document.getElementById('statusFilter')?.value || '';
    
    if (search) params.set('search', search);
    else params.delete('search');
    
    if (category) params.set('category', category);
    else params.delete('category');
    
    if (status) params.set('status', status);
    else params.delete('status');
    
    params.delete('page'); // Reset to page 1
    
    window.location.href = `${window.location.pathname}?${params.toString()}`;
}

/* Sort Transactions */
function sortBy(field) {
    const params = new URLSearchParams(window.location.search);
    const currentSort = params.get('sort_by');
    const currentOrder = params.get('sort_order') || 'desc';
    
    params.set('sort_by', field);
    
    if (currentSort === field) {
        params.set('sort_order', currentOrder === 'desc' ? 'asc' : 'desc');
    } else {
        params.set('sort_order', 'desc');
    }
    
    params.delete('page');
    window.location.href = `${window.location.pathname}?${params.toString()}`;
}

/* Clear Filters */
function clearFilters() {
    window.location.href = window.location.pathname;
}

/* Initialize Transaction Row Clicks */
function initTransactionRows() {
    const rows = document.querySelectorAll('.transaction-row');
    rows.forEach(row => {
        row.addEventListener('click', function(e) {
            if (e.target.closest('button') || e.target.closest('a')) return;
            
            const type = this.dataset.type;
            const id = this.dataset.id;
            viewTransaction(type, id);
        });
    });
}

/* View Transaction Detail */
function viewTransaction(type, id) {
    fetch(`/api/transaction/${type}/${id}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentTransaction = data.data;
                showDetailModal(data.data);
            } else {
                showToast('Error loading transaction', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error loading transaction', 'error');
        });
}

/* Show Detail Modal */
function showDetailModal(transaction) {
    const modal = document.getElementById('detailModal');
    
    document.getElementById('detail-type').textContent = transaction.type === 'income' ? 'Income' : 'Expense';
    document.getElementById('detail-type').className = `badge ${transaction.type === 'income' ? 'bg-success' : 'bg-danger'}`;
    document.getElementById('detail-name').textContent = transaction.name;
    document.getElementById('detail-amount').textContent = `${transaction.currency} ${parseFloat(transaction.amount).toLocaleString('en-US', {minimumFractionDigits: 2})}`;
    document.getElementById('detail-amount').className = `detail-value ${transaction.type}`;
    
    if (transaction.converted_amount && transaction.currency !== primaryCurrency) {
        document.getElementById('detail-converted').textContent = `${primaryCurrency} ${parseFloat(transaction.converted_amount).toLocaleString('en-US', {minimumFractionDigits: 2})}`;
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
    
    // Show/hide mark complete button
    const completeBtn = document.getElementById('btn-mark-complete');
    if (transaction.status === 'pending') {
        completeBtn.style.display = 'inline-block';
    } else {
        completeBtn.style.display = 'none';
    }
    
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

/* Open Create Income Modal */
function openCreateIncomeModal() {
    document.getElementById('incomeForm').reset();
    document.getElementById('income-id').value = '';
    document.getElementById('incomeModalLabel').textContent = 'Add Income';
    
    // Set default date to today
    document.getElementById('income-date').value = new Date().toISOString().split('T')[0];
    document.getElementById('income-currency').value = primaryCurrency;
    
    const modal = new bootstrap.Modal(document.getElementById('incomeModal'));
    modal.show();
}

/* Open Create Expense Modal */
function openCreateExpenseModal() {
    document.getElementById('expenseForm').reset();
    document.getElementById('expense-id').value = '';
    document.getElementById('expenseModalLabel').textContent = 'Add Expense';
    
    // Set default date to today
    document.getElementById('expense-date').value = new Date().toISOString().split('T')[0];
    document.getElementById('expense-currency').value = primaryCurrency;
    
    const modal = new bootstrap.Modal(document.getElementById('expenseModal'));
    modal.show();
}

/* Open Edit Modal */
function openEditModal() {
    if (!currentTransaction) return;
    
    bootstrap.Modal.getInstance(document.getElementById('detailModal')).hide();
    
    if (currentTransaction.type === 'income') {
        document.getElementById('income-id').value = currentTransaction.id;
        document.getElementById('income-source').value = currentTransaction.source_id;
        document.getElementById('income-amount').value = currentTransaction.amount;
        document.getElementById('income-currency').value = currentTransaction.currency;
        document.getElementById('income-date').value = currentTransaction.date;
        document.getElementById('income-description').value = currentTransaction.description || '';
        document.getElementById('income-status').value = currentTransaction.status;
        document.getElementById('incomeModalLabel').textContent = 'Edit Income';
        
        const modal = new bootstrap.Modal(document.getElementById('incomeModal'));
        modal.show();
    } else {
        document.getElementById('expense-id').value = currentTransaction.id;
        document.getElementById('expense-category').value = currentTransaction.category_id;
        document.getElementById('expense-amount').value = currentTransaction.amount;
        document.getElementById('expense-currency').value = currentTransaction.currency;
        document.getElementById('expense-date').value = currentTransaction.date;
        document.getElementById('expense-description').value = currentTransaction.description || '';
        document.getElementById('expense-status').value = currentTransaction.status;
        document.getElementById('expense-budget').value = currentTransaction.budget_id || '';
        document.getElementById('expenseModalLabel').textContent = 'Edit Expense';
        
        const modal = new bootstrap.Modal(document.getElementById('expenseModal'));
        modal.show();
    }
}

/* Save Income */
function saveIncome() {
    const id = document.getElementById('income-id').value;
    const data = {
        source_id: document.getElementById('income-source').value,
        amount: document.getElementById('income-amount').value,
        currency: document.getElementById('income-currency').value,
        transaction_date: document.getElementById('income-date').value,
        description: document.getElementById('income-description').value,
        status: document.getElementById('income-status').value,
    };
    
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
            showToast(data.message, 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showToast(data.error, 'error');
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
    const data = {
        category_id: document.getElementById('expense-category').value,
        amount: document.getElementById('expense-amount').value,
        currency: document.getElementById('expense-currency').value,
        transaction_date: document.getElementById('expense-date').value,
        description: document.getElementById('expense-description').value,
        status: document.getElementById('expense-status').value,
        budget_id: document.getElementById('expense-budget').value || null,
    };
    
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
            showToast(data.message, 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showToast(data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred', 'error');
    });
}

/* Mark as Complete */
function markComplete() {
    if (!currentTransaction) return;
    
    fetch(`/api/transaction/${currentTransaction.type}/${currentTransaction.id}/complete/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showToast(data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred', 'error');
    });
}

/* Open Delete Confirmation */
function openDeleteModal() {
    if (!currentTransaction) return;
    
    bootstrap.Modal.getInstance(document.getElementById('detailModal')).hide();
    
    document.getElementById('delete-transaction-name').textContent = currentTransaction.name;
    
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    modal.show();
}

/* Confirm Delete */
function confirmDelete() {
    if (!currentTransaction) return;
    
    fetch(`/api/transaction/${currentTransaction.type}/${currentTransaction.id}/delete/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showToast(data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred', 'error');
    });
}

/* Show Toast Notification */
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;
    
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