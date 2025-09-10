// auth.js
import { state, API_BASE_URL } from './state.js';
import { fetchCurrentUser } from './user.js';
import { showLoginError, showRegisterError } from './user.js';

export function initAuthEventListeners() {
    document.getElementById('show-register').addEventListener('click', () => {
        document.getElementById('login-form').classList.add('hidden');
        document.getElementById('register-form').classList.remove('hidden');
    });

    document.getElementById('show-login').addEventListener('click', () => {
        document.getElementById('register-form').classList.add('hidden');
        document.getElementById('login-form').classList.remove('hidden');
    });

    document.getElementById('register-btn').addEventListener('click', handleRegister);
    document.getElementById('login-btn').addEventListener('click', handleLogin);
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
}

export async function handleRegister() {
    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const fullName = document.getElementById('register-fullname').value;

    if (!username || !email || !password) {
        showRegisterError('请填写必填字段');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/user/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username,
                email,
                password,
                full_name: fullName
            })
        });

        if (!response.ok) {
            const error = await response.json();
            showRegisterError(error.detail || '注册失败，请稍后重试');
            return;
        }

        document.getElementById('register-form').classList.add('hidden');
        document.getElementById('login-form').classList.remove('hidden');
        alert('注册成功，请登录');
    } catch (error) {
        showRegisterError('网络错误，请稍后重试');
        console.error('注册失败:', error);
    }
}

export async function handleLogin() {
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    if (!username || !password) {
        showLoginError('请填写用户名和密码');
        return;
    }

    try {
        const formData = new FormData();
        formData.append('grant_type', 'password');
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch(`${API_BASE_URL}/api/v1/user/login`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            showLoginError(error.detail || '登录失败，请检查用户名和密码');
            return;
        }

        const data = await response.json();
        state.token = data.access_token;
        localStorage.setItem('token', data.access_token);

        fetchCurrentUser();
    } catch (error) {
        showLoginError('网络错误，请稍后重试');
        console.error('登录失败:', error);
    }
}

export function handleLogout() {
    state.token = null;
    state.currentUser = null;
    localStorage.removeItem('token');

    document.getElementById('auth-modal').classList.remove('hidden');
    document.getElementById('app').classList.add('hidden');
}