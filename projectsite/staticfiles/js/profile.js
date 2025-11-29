/* Profile Page Scripts */

/* Avatar picker callback for profile */
function updateProfileAvatar(avatarPath) {
    document.getElementById('profile-avatar').value = avatarPath;
    updateAvatarDisplay('profile-avatar-display', avatarPath);
}

/* Save Profile Changes */
function saveProfile() {
    const data = {
        first_name: document.getElementById('first-name').value,
        last_name: document.getElementById('last-name').value,
        email: document.getElementById('email').value,
        primary_currency: document.getElementById('primary-currency').value,
        avatar: document.getElementById('profile-avatar').value, // Include avatar
    };
    
    fetch('/api/profile/update/', {
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
            showToast(data.message || 'Profile updated successfully', 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showToast(data.error || 'Error updating profile', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred', 'error');
    });
}

/* Open Change Password Modal */
function openChangePasswordModal() {
    document.getElementById('passwordForm').reset();
    const modal = new bootstrap.Modal(document.getElementById('changePasswordModal'));
    modal.show();
}

/* Change Password */
function changePassword() {
    const currentPassword = document.getElementById('current-password').value;
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    
    // Validate
    if (newPassword !== confirmPassword) {
        showToast('New passwords do not match', 'error');
        return;
    }
    
    if (newPassword.length < 8) {
        showToast('Password must be at least 8 characters', 'error');
        return;
    }
    
    const data = {
        current_password: currentPassword,
        new_password: newPassword,
    };
    
    fetch('/api/profile/change-password/', {
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
            showToast(data.message || 'Password changed successfully', 'success');
            bootstrap.Modal.getInstance(document.getElementById('changePasswordModal')).hide();
            document.getElementById('passwordForm').reset();
        } else {
            showToast(data.error || 'Error changing password', 'error');
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