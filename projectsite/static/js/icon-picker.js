/* Icon and Avatar Picker */

// Available icons (categories/income sources)
const availableIcons = [
    'icon-default.png',
    'ec-food.png',
    'ec-grocery.png',
    'ec-transport.png',
    'ec-shopping.png',
    'ec-games.png',
    'ec-entertainment.png',
    'ec-bills.png',
    'ec-health.png',
    'ec-education.png',
    'is-payment.png',
    'is-investment.png',
    'is-salary.png',
    'is-freelance.png',
    'is-business.png',
    'is-savings.png',
    'is-gift.png',
    'icon-other.png',
];

// Available avatars (user profile)
const availableAvatars = [
    'avatar1.png',
    'avatar2.png',
    'avatar3.png',
    'avatar4.png',
    'avatar5.png',
    'avatar6.png',
    'avatar7.png',
    'avatar8.png',
    'avatar9.png',
    'avatar10.png',
    'avatar11.png',
    'avatar12.png',
    'avatar13.png',
    'avatar14.png',
    'avatar15.png',    
];

let currentIconCallback = null;
let currentAvatarCallback = null;
let selectedIconPath = null;
let selectedAvatarPath = null;

/**
 * Open icon picker modal
 * @param {string} currentIcon - Currently selected icon path
 * @param {function} callback - Function to call when icon is selected
 */
function openIconPicker(currentIcon, callback) {
    currentIconCallback = callback;
    selectedIconPath = currentIcon;
    
    const grid = document.getElementById('iconPickerGrid');
    if (!grid) {
        console.error('Icon picker grid not found');
        return;
    }
    
    grid.innerHTML = '';
    
    availableIcons.forEach(icon => {
        const iconPath = `/static/img/icons/${icon}`;
        const isSelected = iconPath === currentIcon;
        
        const col = document.createElement('div');
        col.className = 'col-3 col-md-2';
        
        const item = document.createElement('div');
        item.className = `icon-picker-item ${isSelected ? 'selected' : ''}`;
        item.onclick = () => selectIcon(iconPath, item);
        
        const img = document.createElement('img');
        img.src = iconPath;
        img.alt = icon;
        img.onerror = function() {
            this.style.display = 'none';
            item.innerHTML = '<i class="bi bi-image text-muted"></i>';
        };
        
        item.appendChild(img);
        col.appendChild(item);
        grid.appendChild(col);
    });
    
    const modal = new bootstrap.Modal(document.getElementById('iconPickerModal'));
    modal.show();
}

/**
 * Select an icon
 */
function selectIcon(iconPath, element) {
    selectedIconPath = iconPath;
    
    // Remove selected class from all items
    document.querySelectorAll('#iconPickerGrid .icon-picker-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    // Add selected class to clicked item
    element.classList.add('selected');
    
    // Call callback and close modal
    if (currentIconCallback) {
        currentIconCallback(iconPath);
    }
    
    bootstrap.Modal.getInstance(document.getElementById('iconPickerModal')).hide();
}

/**
 * Open avatar picker modal
 * @param {string} currentAvatar - Currently selected avatar path
 * @param {function} callback - Function to call when avatar is selected
 */
function openAvatarPicker(currentAvatar, callback) {
    currentAvatarCallback = callback;
    selectedAvatarPath = currentAvatar;
    
    const grid = document.getElementById('avatarPickerGrid');
    if (!grid) {
        console.error('Avatar picker grid not found');
        return;
    }
    
    grid.innerHTML = '';
    
    availableAvatars.forEach(avatar => {
        const avatarPath = `/static/img/avatars/${avatar}`;
        const isSelected = avatarPath === currentAvatar;
        
        // Remove Bootstrap column classes, use our custom structure
        const item = document.createElement('div');
        item.className = `avatar-picker-item ${isSelected ? 'selected' : ''}`;
        item.onclick = () => selectAvatar(avatarPath, item);
        
        const img = document.createElement('img');
        img.src = avatarPath;
        img.alt = avatar;
        img.onerror = function() {
            this.style.display = 'none';
            // Create a fallback circular avatar
            const fallback = document.createElement('div');
            fallback.className = 'avatar-fallback';
            fallback.innerHTML = '<i class="bi bi-person-circle fs-1 text-muted"></i>';
            fallback.style.width = '70px';
            fallback.style.height = '70px';
            fallback.style.borderRadius = '50%';
            fallback.style.display = 'flex';
            fallback.style.alignItems = 'center';
            fallback.style.justifyContent = 'center';
            fallback.style.background = 'var(--bs-light)';
            item.appendChild(fallback);
        };
        
        item.appendChild(img);
        grid.appendChild(item); // Add directly to grid, no column wrapper
    });
    
    const modal = new bootstrap.Modal(document.getElementById('avatarPickerModal'));
    modal.show();
}

/**
 * Select an avatar
 */
function selectAvatar(avatarPath, element) {
    selectedAvatarPath = avatarPath;
    
    // Remove selected class from all items
    document.querySelectorAll('#avatarPickerGrid .avatar-picker-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    // Add selected class to clicked item
    element.classList.add('selected');
    
    // Call callback and close modal
    if (currentAvatarCallback) {
        currentAvatarCallback(avatarPath);
    }
    
    bootstrap.Modal.getInstance(document.getElementById('avatarPickerModal')).hide();
}

/**
 * Update icon display element
 * @param {string} elementId - ID of the element to update
 * @param {string} iconPath - Path to the icon
 */
function updateIconDisplay(elementId, iconPath) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const img = element.querySelector('img');
    if (img) {
        img.src = iconPath || '/static/img/icons/icon-default.png';
    } else {
        element.innerHTML = `<img src="${iconPath || '/static/img/icons/icon-default.png'}" alt="Icon">`;
    }
}

/**
 * Update avatar display element
 * @param {string} elementId - ID of the element to update
 * @param {string} avatarPath - Path to the avatar
 */
function updateAvatarDisplay(elementId, avatarPath) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const img = element.querySelector('img');
    if (img) {
        img.src = avatarPath || '/static/img/avatars/avatar1.png';
    } else {
        element.innerHTML = `<img src="${avatarPath || '/static/img/avatars/avatar1.png'}" alt="Avatar">`;
    }
}