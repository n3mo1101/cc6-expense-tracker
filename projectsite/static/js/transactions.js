/* Transactions Page Scripts */

let currentTransaction = null;
let currentPage = 1;
let currentSort = 'date_desc';
let searchTimeout;

document.addEventListener('DOMContentLoaded', function() {
    initFilters();
    initTransactionRows();
    updateSortIcons();
});

/* Initialize Filters */
function initFilters() {
    const searchInput = document.getElementById('searchInput');
    const typeFilter = document.getElementById('typeFilter');
    const statusFilter = document.getElementById('statusFilter');
    
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                currentPage = 1;
                loadTransactions();
            }, 400);
        });
    }
    
    if (typeFilter) {
        typeFilter.addEventListener('change', function() {
            currentPage = 1;
            loadTransactions();
        });
    }
    
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            currentPage = 1;
            loadTransactions();
        });
    }
}

/* Toggle Sort */
function toggleSort(field) {
    if (field === 'date') {
        currentSort = currentSort === 'date_desc' ? 'date_asc' : 'date_desc';
    } else if (field === 'amount') {
        currentSort = currentSort === 'amount_desc' ? 'amount_asc' : 'amount_desc';
    }
    
    currentPage = 1;
    updateSortIcons();
    loadTransactions();
}

/* Update Sort Button Icons */
function updateSortIcons() {
    const sortDateBtn = document.getElementById('sort-date');
    const sortAmountBtn = document.getElementById('sort-amount');
    
    if (!sortDateBtn || !sortAmountBtn) return;
    
    // Reset all buttons
    sortDateBtn.classList.remove('active');
    sortAmountBtn.classList.remove('active');
    sortDateBtn.querySelector('i').className = 'bi bi-arrow-down-up';
    sortAmountBtn.querySelector('i').className = 'bi bi-arrow-down-up';
    
    // Set active button
    if (currentSort.startsWith('date')) {
        sortDateBtn.classList.add('active');
        sortDateBtn.querySelector('i').className = currentSort === 'date_asc' ? 'bi bi-arrow-up' : 'bi bi-arrow-down';
    } else if (currentSort.startsWith('amount')) {
        sortAmountBtn.classList.add('active');
        sortAmountBtn.querySelector('i').className = currentSort === 'amount_asc' ? 'bi bi-arrow-up' : 'bi bi-arrow-down';
    }
}

/* Load Transactions via AJAX */
function loadTransactions() {
    const search = document.getElementById('searchInput')?.value || '';
    const type = document.getElementById('typeFilter')?.value || '';
    const status = document.getElementById('statusFilter')?.value || '';
    
    const params = new URLSearchParams({
        search: search,
        type: type,
        status: status,
        page: currentPage,
        sort: currentSort,
        ajax: '1'
    });
    
    fetch(`/transactions/?${params.toString()}`, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        updateTransactionsTable(data);
    })
    .catch(error => {
        console.error('Error loading transactions:', error);
    });
}

/* Update Table with AJAX Data */
function updateTransactionsTable(data) {
    const tbody = document.getElementById('transactions-body');
    
    // Update count
    document.getElementById('total-count').textContent = data.total_count;
    document.getElementById('plural-suffix').textContent = data.total_count === 1 ? '' : 's';
    
    // Update rows
    if (data.transactions.length === 0) {
        tbody.innerHTML = `
            <tr id="empty-row">
                <td colspan="4">
                    <div class="empty-transactions">
                        <i class="bi bi-receipt d-block"></i>
                        <h5>No transactions found</h5>
                        <p>Try adjusting your filters</p>
                    </div>
                </td>
            </tr>
        `;
    } else {
        tbody.innerHTML = data.transactions.map(t => createTransactionRow(t)).join('');
        initTransactionRows();
    }
    
    // Update pagination
    updatePagination(data);
}

/* Create Transaction Row HTML */
function createTransactionRow(t) {
    const icon = t.type === 'income' ? 'up' : 'down';
    const sign = t.type === 'income' ? '+' : '-';
    const amount = parseFloat(t.amount).toLocaleString('en-US', {minimumFractionDigits: 2});
    const date = new Date(t.date).toLocaleDateString('en-US', {month: 'short', day: 'numeric', year: 'numeric'});
    const desc = t.description ? `<p class="transaction-description">${truncateWords(t.description, 8)}</p>` : '';
    const status = t.status.charAt(0).toUpperCase() + t.status.slice(1);
    
    return `
        <tr class="transaction-row" data-type="${t.type}" data-id="${t.id}">
            <!-- Desktop View -->
            <td class="hide-mobile">
                <div class="d-flex align-items-center gap-3">
                    <div class="transaction-type-icon ${t.type}">
                        <i class="bi bi-arrow-${icon}-short"></i>
                    </div>
                    <div>
                        <p class="transaction-name">${t.name}</p>
                        ${desc}
                    </div>
                </div>
            </td>
            <td class="hide-mobile">
                <span class="text-muted">${date}</span>
            </td>
            <td class="hide-mobile">
                <span class="transaction-amount ${t.type}">${sign}${t.currency} ${amount}</span>
            </td>
            <td class="hide-mobile">
                <span class="status-badge ${t.status}">${status}</span>
            </td>
            
            <!-- Mobile View -->
            <td class="show-mobile-only" colspan="4">
                <div class="mobile-transaction-header">
                    <div class="transaction-type-icon ${t.type}">
                        <i class="bi bi-arrow-${icon}-short"></i>
                    </div>
                    <div class="mobile-transaction-info">
                        <p class="transaction-name mb-0">${t.name}</p>
                        <small class="text-muted">${date}</small>
                    </div>
                    <div class="mobile-amount-status">
                        <span class="transaction-amount ${t.type}">${sign}${t.currency} ${amount}</span>
                        <span class="status-badge ${t.status}">${status}</span>
                    </div>
                </div>
            </td>
        </tr>
    `;
}

/* Truncate words helper */
function truncateWords(str, numWords) {
    if (!str) return '';
    const words = str.split(' ');
    if (words.length <= numWords) return str;
    return words.slice(0, numWords).join(' ') + '...';
}

/* Update Pagination */
function updatePagination(data) {
    const footer = document.getElementById('pagination-footer');
    
    if (data.total_pages <= 1) {
        footer.innerHTML = '<span class="pagination-info text-muted">Showing all results</span>';
        return;
    }
    
    const prevDisabled = !data.has_previous ? 'disabled' : '';
    const nextDisabled = !data.has_next ? 'disabled' : '';
    
    footer.innerHTML = `
        <span class="pagination-info">
            Page <span id="current-page">${data.page}</span> of <span id="total-pages">${data.total_pages}</span>
        </span>
        <nav>
            <ul class="pagination pagination-sm mb-0">
                <li class="page-item ${prevDisabled}">
                    <a class="page-link" href="#" onclick="loadPage(${data.page - 1}); return false;">&laquo; Previous</a>
                </li>
                <li class="page-item ${nextDisabled}">
                    <a class="page-link" href="#" onclick="loadPage(${data.page + 1}); return false;">Next &raquo;</a>
                </li>
            </ul>
        </nav>
    `;
    
    currentPage = data.page;
}

/* Load Specific Page */
function loadPage(page) {
    if (page < 1) return;
    currentPage = page;
    loadTransactions();
}

/* Clear Filters */
function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('typeFilter').value = '';
    document.getElementById('statusFilter').value = '';
    currentPage = 1;
    currentSort = 'date_desc';
    updateSortIcons();
    loadTransactions();
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
            bootstrap.Modal.getInstance(document.getElementById('incomeModal')).hide();
            loadTransactions();
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
            bootstrap.Modal.getInstance(document.getElementById('expenseModal')).hide();
            loadTransactions();
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
            bootstrap.Modal.getInstance(document.getElementById('detailModal')).hide();
            loadTransactions();
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
            bootstrap.Modal.getInstance(document.getElementById('deleteModal')).hide();
            loadTransactions();
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