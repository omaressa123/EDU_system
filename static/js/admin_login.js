// Admin Login JavaScript - Enhanced to set JWT token after session login

let toggleIcon = document.getElementById('toggleIcon');
let loginForm = document.getElementById('adminLoginForm');
let loginBtn = document.getElementById('loginBtn');
let messageDiv = document.getElementById('message');
let btnText = document.querySelector('.btn-text');
let loadingSpinner = document.querySelector('.loading');

function togglePassword() {
    const passwordInput = document.getElementById('password');
    const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
    passwordInput.setAttribute('type', type);
    
    toggleIcon.classList.toggle('fa-eye');
    toggleIcon.classList.toggle('fa-eye-slash');
}

function showMessage(text, type) {
    messageDiv.textContent = text;
    messageDiv.className = `message ${type} show`;
    messageDiv.classList.remove('hidden');
    
    if (type === 'success') {
        setTimeout(() => {
            messageDiv.classList.add('hidden');
        }, 3000);
    }
}

function setLoading(loading) {
    loginBtn.disabled = loading;
    if (loading) {
        btnText.classList.add('hidden');
        loadingSpinner.classList.remove('hidden');
    } else {
        btnText.classList.remove('hidden');
        loadingSpinner.classList.add('hidden');
    }
}

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();
    
    if (!username || !password) {
        showMessage('Please fill all fields', 'error');
        return;
    }
    
    if (username.length < 3) {
        showMessage('Username must be at least 3 characters', 'error');
        return;
    }
    
    setLoading(true);
    messageDiv.classList.add('hidden');
    
    try {
        const response = await fetch('/admin-login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`,
            credentials: 'same-origin'
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            if (result.token) {
                localStorage.setItem('token', result.token);
            }
            showMessage('Login successful! Redirecting...', 'success');
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1500);
        } else {
            showMessage(result.message || 'Invalid credentials', 'error');
        }
    } catch (error) {
        showMessage('Network error. Please try again.', 'error');
        console.error('Login error:', error);
    } finally {
        setLoading(false);
    }
});

// Form validation
document.querySelectorAll('input[required]').forEach(input => {
    input.addEventListener('blur', function() {
        if (!this.value.trim()) {
            this.style.borderColor = '#ef4444';
        } else {
            this.style.borderColor = '#10b981';
        }
    });
    
    input.addEventListener('input', function() {
        this.style.borderColor = '#e1e5e9';
    });
});

// RTL for Arabic
document.addEventListener('DOMContentLoaded', () => {
    const isArabic = /[\u0600-\u06FF]/.test(document.body.textContent);
    if (isArabic) {
        document.documentElement.setAttribute('dir', 'rtl');
        document.documentElement.setAttribute('lang', 'ar');
    }
});
