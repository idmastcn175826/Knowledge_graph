// user.js
import { state, API_BASE_URL } from './state.js';
import { fetchFiles } from './file.js';
import { fetchKnowledgeGraphs } from './knowledgeGraph.js';
import { initHealthMonitoring } from './health.js';

export async function fetchCurrentUser() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/user/me`, {
            headers: {
                'Authorization': `Bearer ${state.token}`
            }
        });

        if (response.ok) {
            const user = await response.json();
            state.currentUser = user;
            document.getElementById('current-username').textContent = user.username;
            document.getElementById('auth-modal').classList.add('hidden');
            document.getElementById('app').classList.remove('hidden');

            // 使用动态导入来避免循环依赖
            import('./file.js').then(module => {
                module.fetchFiles();
            });

            import('./knowledgeGraph.js').then(module => {
                module.fetchKnowledgeGraphs();
            });

            import('./health.js').then(module => {
                module.initHealthMonitoring();
            });

            // 直接调用dashboard函数
            fetchDashboardStats();
        }
    } catch (error) {
        console.error('获取用户信息失败:', error);
        handleLogout();
    }
}

export function fetchDashboardStats() {
    // 这里使用状态数据，不依赖其他模块
    document.getElementById('kg-count').textContent = state.knowledgeGraphs.length;
    document.getElementById('file-count').textContent = state.files.length;
    document.getElementById('qa-count').textContent = '0';
    document.getElementById('entity-count').textContent = '0';
    updateRecentActivities();
}

export function updateRecentActivities() {
    const container = document.getElementById('recent-activities');

    // 如果没有数据，显示提示
    if (state.files.length === 0 && state.knowledgeGraphs.length === 0) {
        container.innerHTML = `
            <div class="text-center text-gray-500 py-4">
                <i class="fa fa-info-circle text-2xl mb-2"></i>
                <p>暂无活动记录</p>
                <p class="text-sm mt-1">开始使用系统后这里会显示活动记录</p>
            </div>
        `;
        return;
    }

    let html = '';

    // 只显示实际存在的活动
    if (state.files.length > 0) {
        html += `
            <div class="flex items-start gap-4 pb-4 border-b border-gray-100">
                <div class="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-secondary flex-shrink-0">
                    <i class="fa fa-upload"></i>
                </div>
                <div class="flex-1">
                    <p class="text-sm">
                        <span class="font-medium">${state.currentUser?.username || '您'}</span>
                        上传了文件
                        <span class="font-medium">${state.files[0].file_name}</span>
                    </p>
                    <p class="text-xs text-gray-500 mt-1">刚刚</p>
                </div>
            </div>
        `;
    }

    if (state.knowledgeGraphs.length > 0) {
        html += `
            <div class="flex items-start gap-4 pb-4 border-b border-gray-100">
                <div class="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-primary flex-shrink-0">
                    <i class="fa fa-sitemap"></i>
                </div>
                <div class="flex-1">
                    <p class="text-sm">
                        <span class="font-medium">${state.currentUser?.username || '您'}</span>
                        创建了知识图谱
                        <span class="font-medium">${state.knowledgeGraphs[0].name}</span>
                    </p>
                    <p class="text-xs text-gray-500 mt-1">刚刚</p>
                </div>
            </div>
        `;
    }

    container.innerHTML = html;
}

//
export function showLoginError(message) {
    const alert = document.getElementById('login-alert');
    alert.textContent = message;
    alert.classList.remove('hidden');
    setTimeout(() => {
        alert.classList.add('hidden');
    }, 3000);
}

export function showRegisterError(message) {
    const alert = document.getElementById('register-alert');
    alert.textContent = message;
    alert.classList.remove('hidden');
    setTimeout(() => {
        alert.classList.add('hidden');
    }, 3000);
}

export function handleLogout() {
    state.token = null;
    state.currentUser = null;
    localStorage.removeItem('token');
    document.getElementById('auth-modal').classList.remove('hidden');
    document.getElementById('app').classList.add('hidden');
}