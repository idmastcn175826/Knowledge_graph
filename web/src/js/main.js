// main.js
import { state } from './state.js';
import { initAuthEventListeners } from './auth.js';
import { initFileEventListeners, fetchFiles, downloadFile, showDeleteFileConfirm } from './file.js';
import {
    initKGEventListeners, fetchKnowledgeGraphs, viewKGDetails,
    hideKGDetails, startQAWithKG, showDeleteKGConfirm, visualizeKG
} from './knowledgeGraph.js';
import { initQAEventListeners, populateKGSelectForQA, fetchQAHistory } from './qa.js';
import { initDatabaseEventListeners } from './database.js';
import { initConvertEventListeners, handleConvertTypeChange } from './convert.js';
// import { initHealthMonitoring } from './health.js';
import { initAgentEventListeners, fetchAgentTools, agentgenerateSessionId } from './agent.js';
import { fetchCurrentUser, fetchDashboardStats } from './user.js';
import { updateCurrentTime } from './utils.js';

// RAG系统相关导入
import { initRagView, loadCollections } from './rag.js';

// 全局函数注册（供HTML直接调用）
window.viewKGDetails = viewKGDetails;
window.hideKGDetails = hideKGDetails;
window.startQAWithKG = startQAWithKG;
window.showDeleteKGConfirm = showDeleteKGConfirm;
window.showDeleteFileConfirm = showDeleteFileConfirm;
window.downloadFile = downloadFile;
window.visualizeKG = visualizeKG;

// 视图初始化映射表（优化代码结构，避免过多if-else）
const VIEW_INITIALIZERS = {
    'file-view': () => import('./file.js').then(module => module.fetchFiles()),
    'kg-view': () => import('./knowledgeGraph.js').then(module => module.fetchKnowledgeGraphs()),
    'qa-view': () => { populateKGSelectForQA(); fetchQAHistory(); },
    'dashboard-view': () => import('./user.js').then(module => module.fetchDashboardStats()),
    'data-view': () => handleConvertTypeChange(),
    'agent-view': () => {
        fetchAgentTools();
        if (!document.getElementById('session-id-input').value) {
            agentgenerateSessionId();
        }
    },
    'rag-view': () => loadCollections() // RAG视图初始化：加载集合列表
};

/**
 * 初始化所有事件监听器
 */
function initAllEventListeners() {
    // 基础功能事件监听
    initAuthEventListeners();
    initFileEventListeners();
    initKGEventListeners();
    initQAEventListeners();
    initDatabaseEventListeners();
    initConvertEventListeners();
    initAgentEventListeners();

    // RAG系统事件监听（已在initRagView中处理，此处无需重复）

    // 导航切换事件
    initNavigationListeners();
}

/**
 * 初始化导航切换逻辑
 */
function initNavigationListeners() {
    // 桌面端导航
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetView = item.getAttribute('data-view');
            if (targetView) {
                switchToView(targetView);
                highlightActiveNavItem(item);
            }
        });
    });

    // 移动端菜单切换
    document.getElementById('mobile-menu-btn')?.addEventListener('click', () => {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) sidebar.classList.toggle('-translate-x-full');
    });
}

/**
 * 切换视图显示
 * @param {string} viewId - 视图ID（对应DOM元素的id）
 */
function switchToView(viewId) {
    // 隐藏所有视图
    document.querySelectorAll('.view').forEach(view => {
        view.classList.add('hidden');
    });

    // 显示目标视图
    const targetView = document.getElementById(viewId);
    if (targetView) {
        targetView.classList.remove('hidden');

        // 执行视图专属初始化逻辑
        const initializer = VIEW_INITIALIZERS[viewId];
        if (initializer) {
            try {
                initializer();
            } catch (error) {
                console.error(`初始化视图 ${viewId} 失败:`, error);
            }
        }
    } else {
        console.warn(`未找到视图元素: ${viewId}`);
    }
}

/**
 * 高亮当前激活的导航项
 * @param {HTMLElement} activeItem - 激活的导航项元素
 */
function highlightActiveNavItem(activeItem) {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    activeItem.classList.add('active');
}

/**
 * 应用初始化入口
 */
function initializeApp() {
    // 检查登录状态
    if (state.token) {
        fetchCurrentUser(); // 已登录：加载用户信息
    } else {
        // 未登录：显示登录模态框
        const authModal = document.getElementById('auth-modal');
        if (authModal) authModal.classList.remove('hidden');
    }

    // 初始化所有事件监听
    initAllEventListeners();

    // 初始化健康监控
    // initHealthMonitoring();

    // 初始化时间显示并定时更新
    updateCurrentTime();
    setInterval(updateCurrentTime, 60000);

    // 初始化RAG系统
    initRagView();
}

// DOM加载完成后启动应用
document.addEventListener('DOMContentLoaded', initializeApp);

// 导出常用函数供外部调用
export { switchToView };
