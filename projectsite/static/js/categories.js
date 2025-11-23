/* Categories Page Scripts */

let currentCategory = null;
let currentIncomeSource = null;

/* ===== CATEGORY FUNCTIONS ===== */

/* Open Create Category Modal */
function openCreateCategoryModal() {
    document.getElementById('categoryForm').reset();
    document.getElementById('category-id').value = '';
    document.getElementById('categoryModalLabel').textContent = 'Add Category';
    
    const modal = new bootstrap.Modal(document.getElementById('categoryModal'));
    modal.show();
}

/* View Category Details */
function viewCategory(categoryId) {
    fetch(`/api/category/${categoryId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentCategory = data.data;
                showCategoryDetailModal(data.data);
            } else {
                showToast('Error loading category', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error loading category', 'error');
        });
}

/* Show Category Detail Modal */
function showCategoryDetailModal(category) {
    const iconClass = category.icon || 'bi-tag';
    document.getElementById('detail-category-icon').className = `bi ${iconClass}`;
    document.getElementById('detail-category-name').textContent = category.name;
    document.getElementById('detail-category-count').textContent = category.expense_count;
    document.getElementById('detail-category-total').textContent = `${primaryCurrency} ${parseFloat(category.total_spent).toLocaleString('en-US', {minimumFractionDigits: 2})}`;
    
    const modal = new bootstrap.Modal(document.getElementById('categoryDetailModal'));
    modal.show();
}

/* Open Edit Category Modal */
function openEditCategoryModal() {
    if (!currentCategory) return;
    
    bootstrap.Modal.getInstance(document.getElementById('categoryDetailModal')).hide();
    
    document.getElementById('category-id').value = currentCategory.id;
    document.getElementById('category-name').value = currentCategory.name;
    document.getElementById('category-icon').value = currentCategory.icon || '';
    document.getElementById('categoryModalLabel').textContent = 'Edit Category';
    
    const modal = new bootstrap.Modal(document.getElementById('categoryModal'));
    modal.show();
}

/* Save Category */
function saveCategory() {
    const id = document.getElementById('category-id').value;
    
    const data = {
        name: document.getElementById('category-name').value,
        icon: document.getElementById('category-icon').value || null,
    };
    
    const url = id ? `/api/category/${id}/update/` : '/api/category/create/';
    
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
            showToast(data.message || 'Category saved successfully', 'success');
            bootstrap.Modal.getInstance(document.getElementById('categoryModal')).hide();
            setTimeout(() => window.location.reload(), 500);
        } else {
            showToast(data.error || 'Error saving category', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred', 'error');
    });
}

/* Open Delete Category Modal */
function openDeleteCategoryModal() {
    if (!currentCategory) return;
    
    bootstrap.Modal.getInstance(document.getElementById('categoryDetailModal')).hide();
    document.getElementById('delete-category-name').textContent = currentCategory.name;
    
    const modal = new bootstrap.Modal(document.getElementById('deleteCategoryModal'));
    modal.show();
}

/* Confirm Delete Category */
function confirmDeleteCategory() {
    if (!currentCategory) return;
    
    fetch(`/api/category/${currentCategory.id}/delete/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message || 'Category deleted', 'success');
            bootstrap.Modal.getInstance(document.getElementById('deleteCategoryModal')).hide();
            setTimeout(() => window.location.reload(), 500);
        } else {
            showToast(data.error || 'Error deleting category', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred', 'error');
    });
}

/* ===== INCOME SOURCE FUNCTIONS ===== */

/* Open Create Income Source Modal */
function openCreateIncomeSourceModal() {
    document.getElementById('incomeSourceForm').reset();
    document.getElementById('source-id').value = '';
    document.getElementById('incomeSourceModalLabel').textContent = 'Add Income Source';
    
    const modal = new bootstrap.Modal(document.getElementById('incomeSourceModal'));
    modal.show();
}

/* View Income Source Details */
function viewIncomeSource(sourceId) {
    fetch(`/api/income-source/${sourceId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentIncomeSource = data.data;
                showIncomeSourceDetailModal(data.data);
            } else {
                showToast('Error loading income source', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error loading income source', 'error');
        });
}

/* Show Income Source Detail Modal */
function showIncomeSourceDetailModal(source) {
    const iconClass = source.icon || 'bi-cash-stack';
    document.getElementById('detail-source-icon').className = `bi ${iconClass}`;
    document.getElementById('detail-source-name').textContent = source.name;
    document.getElementById('detail-source-count').textContent = source.income_count;
    document.getElementById('detail-source-total').textContent = `${primaryCurrency} ${parseFloat(source.total_earned).toLocaleString('en-US', {minimumFractionDigits: 2})}`;
    
    const modal = new bootstrap.Modal(document.getElementById('incomeSourceDetailModal'));
    modal.show();
}

/* Open Edit Income Source Modal */
function openEditIncomeSourceModal() {
    if (!currentIncomeSource) return;
    
    bootstrap.Modal.getInstance(document.getElementById('incomeSourceDetailModal')).hide();
    
    document.getElementById('source-id').value = currentIncomeSource.id;
    document.getElementById('source-name').value = currentIncomeSource.name;
    document.getElementById('source-icon').value = currentIncomeSource.icon || '';
    document.getElementById('incomeSourceModalLabel').textContent = 'Edit Income Source';
    
    const modal = new bootstrap.Modal(document.getElementById('incomeSourceModal'));
    modal.show();
}

/* Save Income Source */
function saveIncomeSource() {
    const id = document.getElementById('source-id').value;
    
    const data = {
        name: document.getElementById('source-name').value,
        icon: document.getElementById('source-icon').value || null,
    };
    
    const url = id ? `/api/income-source/${id}/update/` : '/api/income-source/create/';
    
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
            showToast(data.message || 'Income source saved successfully', 'success');
            bootstrap.Modal.getInstance(document.getElementById('incomeSourceModal')).hide();
            setTimeout(() => window.location.reload(), 500);
        } else {
            showToast(data.error || 'Error saving income source', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred', 'error');
    });
}

/* Open Delete Income Source Modal */
function openDeleteIncomeSourceModal() {
    if (!currentIncomeSource) return;
    
    bootstrap.Modal.getInstance(document.getElementById('incomeSourceDetailModal')).hide();
    document.getElementById('delete-source-name').textContent = currentIncomeSource.name;
    
    const modal = new bootstrap.Modal(document.getElementById('deleteIncomeSourceModal'));
    modal.show();
}

/* Confirm Delete Income Source */
function confirmDeleteIncomeSource() {
    if (!currentIncomeSource) return;
    
    fetch(`/api/income-source/${currentIncomeSource.id}/delete/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message || 'Income source deleted', 'success');
            bootstrap.Modal.getInstance(document.getElementById('deleteIncomeSourceModal')).hide();
            setTimeout(() => window.location.reload(), 500);
        } else {
            showToast(data.error || 'Error deleting income source', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred', 'error');
    });
}

/* ===== UTILITY FUNCTIONS ===== */

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