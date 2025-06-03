let isLoading = false;

function openSettings() {
    const modal = document.getElementById('settingsModal');
    modal.classList.add('active');
    loadCurrentSettings();
}

function closeSettings() {
    const modal = document.getElementById('settingsModal');
    modal.classList.remove('active');
    clearMessage();
}

document.addEventListener('DOMContentLoaded', function() {
    const settingsModal = document.getElementById('settingsModal');
    if (settingsModal) {
        settingsModal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeSettings();
            }
        });
    }
});

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeSettings();
    }
});

async function loadCurrentSettings() {
    try {
        const response = await fetch('/api/settings');
        if (response.ok) {
            const settings = await response.json();
            document.getElementById('username').value = settings.username || '';
        } else {
            console.log('No existing settings found');
        }
    } catch (error) {
        console.error('Error loading settings:', error);
        showMessage('Failed to load current settings', 'error');
    }
}

async function saveSettings(event) {
    event.preventDefault();
    
    if (isLoading) return;
    
    const username = document.getElementById('username').value.trim();
    
    if (!username) {
        showMessage('Please enter a username', 'error');
        return;
    }
    
    setLoading(true);
    clearMessage();
    
    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showMessage('Settings saved successfully!', 'success');
            setTimeout(() => {
                closeSettings();
            }, 1500);
        } else {
            showMessage(result.error || 'Failed to save settings', 'error');
        }
    } catch (error) {
        console.error('Error saving settings:', error);
        showMessage('Failed to save settings. Please try again.', 'error');
    } finally {
        setLoading(false);
    }
}

function showMessage(message, type) {
    const container = document.getElementById('messageContainer');
    container.innerHTML = `<div class="message ${type}">${message}</div>`;
}

function clearMessage() {
    document.getElementById('messageContainer').innerHTML = '';
}

function setLoading(loading) {
    isLoading = loading;
    const saveBtn = document.getElementById('saveBtn');
    const form = document.getElementById('settingsForm');
    
    if (loading) {
        saveBtn.disabled = true;
        saveBtn.textContent = 'Saving...';
        form.classList.add('loading');
    } else {
        saveBtn.disabled = false;
        saveBtn.textContent = 'Save';
        form.classList.remove('loading');
    }
}