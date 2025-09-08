// main.js
import { state } from './state.js';
import { initAuthEventListeners } from './auth.js';
import {
    initFileEventListeners,
    fetchFiles,
    downloadFile,
    showDeleteFileConfirm  // 确保这个函数被导入
} from './file.js';

import {
    initKGEventListeners,
    fetchKnowledgeGraphs,
    viewKGDetails,
    hideKGDetails,
    startQAWithKG,
    showDeleteKGConfirm,
    visualizeKG
} from './knowledgeGraph.js';
import { initQAEventListeners, populateKGSelectForQA, fetchQAHistory } from './qa.js';
import { initDatabaseEventListeners } from './database.js';
import { initConvertEventListeners, handleConvertTypeChange } from './convert.js';
import { initHealthMonitoring } from './health.js';
import { initAgentEventListeners, fetchAgentTools, agentgenerateSessionId } from './agent.js';
import { fetchCurrentUser, fetchDashboardStats } from './user.js'; // 确保这里正确
import { updateCurrentTime } from './utils.js';

// 导出全局函数供HTML调用
window.viewKGDetails = viewKGDetails;
window.hideKGDetails = hideKGDetails;
window.startQAWithKG = startQAWithKG;
window.showDeleteKGConfirm = showDeleteKGConfirm;
window.showDeleteFileConfirm = showDeleteFileConfirm;
window.downloadFile = downloadFile;
window.visualizeKG = visualizeKG;


// DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    if (state.token) {
        fetchCurrentUser();
    } else {
        document.getElementById('auth-modal').classList.remove('hidden');
    }

    initEventListeners();
    initHealthMonitoring();
    updateCurrentTime();
    setInterval(updateCurrentTime, 60000);
});

// 初始化事件监听
function initEventListeners() {
    initAuthEventListeners();
    initFileEventListeners();
    initKGEventListeners();
    initQAEventListeners();
    initDatabaseEventListeners();
    initConvertEventListeners();
    initAgentEventListeners();

    // 导航相关
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const view = item.getAttribute('data-view');
            switchView(view);

            document.querySelectorAll('.nav-item').forEach(navItem => {
                navItem.classList.remove('active');
            });
            item.classList.add('active');
        });
    });

    // 移动端菜单
    document.getElementById('mobile-menu-btn').addEventListener('click', () => {
        const sidebar = document.getElementById('sidebar');
        sidebar.classList.toggle('-translate-x-full');
    });
}

// 切换视图
// 在main.js中修改switchView函数
export function switchView(viewId) {
    document.querySelectorAll('.view').forEach(view => {
        view.classList.add('hidden');
    });

    document.getElementById(viewId).classList.remove('hidden');

    if (viewId === 'file-view') {
        // 动态导入避免循环依赖
        import('./file.js').then(module => {
            module.fetchFiles();
        });
    } else if (viewId === 'kg-view') {
        import('./knowledgeGraph.js').then(module => {
            module.fetchKnowledgeGraphs();
        });
    } else if (viewId === 'qa-view') {
        populateKGSelectForQA();
        fetchQAHistory();
    } else if (viewId === 'dashboard-view') {
        // 动态导入user模块
        import('./user.js').then(module => {
            module.fetchDashboardStats();
        });
    } else if (viewId === 'data-view') {
        handleConvertTypeChange();
    } else if (viewId === 'agent-view') {
        fetchAgentTools();
        if (!document.getElementById('session-id-input').value) {
            agentgenerateSessionId();
        }
    }
}