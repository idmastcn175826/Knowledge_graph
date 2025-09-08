// agent.js
import { state, API_BASE_URL } from './state.js';
import { formatTime } from './utils.js';

export function initAgentEventListeners() {
    document.getElementById('clear-agent-memory').addEventListener('click', clearAgentMemory);
    document.getElementById('refresh-agent-tools').addEventListener('click', fetchAgentTools);
    document.getElementById('generate-session-id').addEventListener('click', agentgenerateSessionId);
    document.getElementById('copy-session-id').addEventListener('click', copySessionId);
    document.getElementById('send-agent-query').addEventListener('click', sendAgentQuery);

    document.getElementById('agent-query-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendAgentQuery();
        }
    });

    document.getElementById('session-id-input').addEventListener('change', (e) => {
        state.currentAgentSessionId = e.target.value;
        updateSessionDisplay();
    });
}

export async function fetchAgentTools() {
    try {
        showLoading('tools');

        const response = await fetch(`${API_BASE_URL}/api/v1/agent/tools`, {
            headers: {
                'Authorization': `Bearer ${state.token}`
            }
        });

        if (!response.ok) {
            throw new Error('获取工具列表失败');
        }

        const tools = await response.json();
        renderAgentTools(tools);
    } catch (error) {
        console.error('获取工具列表失败:', error);
        document.getElementById('agent-tools-list').innerHTML = `
            <div class="text-center text-gray-500 py-4">
                <i class="fa fa-exclamation-triangle text-2xl mb-2 text-warning"></i>
                <p class="text-sm">获取工具失败</p>
                <button class="text-primary text-xs mt-1" onclick="fetchAgentTools()">重试</button>
            </div>
        `;
    }
}

export function renderAgentTools(tools) {
    const toolsContainer = document.getElementById('agent-tools-list');
    const toolsCount = document.getElementById('tools-count');

    if (!tools || tools.length === 0) {
        toolsContainer.innerHTML = `
            <div class="text-center text-gray-500 py-4">
                <i class="fa fa-cogs text-2xl mb-2"></i>
                <p class="text-sm">暂无可用工具</p>
            </div>
        `;
        toolsCount.textContent = '0';
        return;
    }

    let html = '';
    tools.forEach(tool => {
        if (typeof tool === 'string') {
            html += `
                <div class="bg-gray-50 p-3 rounded-lg border border-gray-100">
                    <div class="font-medium text-sm">${tool}</div>
                    <span class="tool-badge">字符串工具</span>
                </div>
            `;
        } else {
            html += `
                <div class="bg-gray-50 p-3 rounded-lg border border-gray-100">
                    <div class="font-medium text-sm">${tool.name || '未命名工具'}</div>
                    ${tool.description ? `<div class="text-xs text-gray-500 mt-1">${tool.description}</div>` : ''}
                    <div class="mt-2">
                        <span class="tool-badge">${tool.type || '通用工具'}</span>
                    </div>
                </div>
            `;
        }
    });

    toolsContainer.innerHTML = html;
    toolsCount.textContent = tools.length;
}

export async function clearAgentMemory() {
    const sessionId = document.getElementById('session-id-input').value;

    if (!sessionId) {
        alert('请先生成或输入会话ID');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/agent/clear-memory?session_id=${encodeURIComponent(sessionId)}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${state.token}`
            }
        });

        if (!response.ok) {
            throw new Error('清除记忆失败');
        }

        const result = await response.json();
        alert('记忆清除成功');

        document.getElementById('agent-chat-history').innerHTML = `
            <div class="text-center text-gray-500 py-10">
                <i class="fa fa-robot text-4xl mb-3"></i>
                <p>开始新的对话</p>
                <p class="text-sm mt-1">会话记忆已清除</p>
            </div>
        `;
    } catch (error) {
        console.error('清除记忆失败:', error);
        alert('清除记忆失败: ' + error.message);
    }
}

export function agentgenerateSessionId() {
    const sessionId = 'agent_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    document.getElementById('session-id-input').value = sessionId;
    state.currentAgentSessionId = sessionId;
    updateSessionDisplay();
    return sessionId;
}

export function copySessionId() {
    const sessionIdInput = document.getElementById('session-id-input');
    sessionIdInput.select();
    document.execCommand('copy');
    alert('会话ID已复制到剪贴板');
}

export function updateSessionDisplay() {
    const sessionDisplay = document.getElementById('current-session-display');
    const sessionId = state.currentAgentSessionId;

    if (sessionId) {
        const shortId = sessionId.length > 20 ? sessionId.substr(0, 10) + '...' + sessionId.substr(-10) : sessionId;
        sessionDisplay.textContent = `会话: ${shortId}`;
    } else {
        sessionDisplay.textContent = '新会话';
    }
}

export async function sendAgentQuery() {
    const query = document.getElementById('agent-query-input').value.trim();
    const sessionId = document.getElementById('session-id-input').value;

    if (!query) {
        alert('请输入问题');
        return;
    }

    try {
        addAgentMessage(query, 'user');
        document.getElementById('agent-query-input').value = '';
        const thinkingId = addAgentMessage('正在思考...', 'ai', true);

        const requestData = {
            query: query
        };

        if (sessionId) {
            requestData.session_id = sessionId;
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/agent/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || '查询失败');
        }

        const result = await response.json();
        removeAgentMessage(thinkingId);
        addAgentMessage(result.response, 'ai', false, result);

        if (result.session_id) {
            document.getElementById('session-id-input').value = result.session_id;
            state.currentAgentSessionId = result.session_id;
            updateSessionDisplay();
        }
    } catch (error) {
        console.error('智能体查询失败:', error);
        removeAgentMessage('thinking');
        addAgentMessage(`抱歉，发生了错误: ${error.message}`, 'ai');
    }
}

export function addAgentMessage(content, sender, isThinking = false, result = null) {
    const chatHistory = document.getElementById('agent-chat-history');
    const messageId = isThinking ? 'thinking' : `msg_${Date.now()}`;

    if (chatHistory.querySelector('.text-center') && !isThinking) {
        chatHistory.innerHTML = '';
    }

    const messageDiv = document.createElement('div');
    messageDiv.id = messageId;
    messageDiv.className = `flex ${sender === 'user' ? 'justify-start' : 'justify-end'} mb-4`;

    const bubbleClass = sender === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai';
    const icon = sender === 'user' ? 'fa-user' : 'fa-robot';
    const iconColor = sender === 'user' ? 'text-gray-500' : 'text-primary';

    let messageContent = isThinking ?
        '<div class="flex items-center"><i class="fa fa-spinner fa-spin mr-2"></i>正在思考...</div>' :
        content;

    let extraInfo = '';
    if (result && !isThinking) {
        if (result.thought_process) {
            extraInfo += `
                <div class="mt-3 p-3 bg-gray-100 rounded-lg">
                    <div class="font-medium text-sm mb-2">思考过程:</div>
                    <div class="text-xs text-gray-600 whitespace-pre-wrap">${result.thought_process}</div>
                </div>
            `;
        }

        if (result.tool_used && Object.keys(result.tool_used).length > 0) {
            extraInfo += `
                <div class="mt-3 p-3 bg-blue-50 rounded-lg">
                    <div class="font-medium text-sm mb-2">使用的工具:</div>
                    <div class="text-xs">
                        ${Object.entries(result.tool_used).map(([name, data]) =>
                            `<div class="mb-1"><span class="font-medium">${name}:</span> ${JSON.stringify(data)}</div>`
                        ).join('')}
                    </div>
                </div>
            `;
        }
    }

    messageDiv.innerHTML = `
        <div class="${bubbleClass}">
            <div class="flex items-center gap-2 mb-2">
                <i class="fa ${icon} ${iconColor}"></i>
                <span class="text-sm font-medium">${sender === 'user' ? '您' : '智能体'}</span>
                <span class="text-xs text-gray-400 ml-auto">${new Date().toLocaleTimeString()}</span>
            </div>
            <div class="text-gray-800">
                ${messageContent}
                ${extraInfo}
            </div>
        </div>
    `;

    chatHistory.appendChild(messageDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;

    return messageId;
}

export function removeAgentMessage(messageId) {
    const message = document.getElementById(messageId);
    if (message) {
        message.remove();
    }
}

export function showLoading(type) {
    if (type === 'tools') {
        document.getElementById('agent-tools-list').innerHTML = `
            <div class="text-center text-gray-500 py-4">
                <i class="fa fa-spinner fa-spin text-2xl mb-2"></i>
                <p class="text-sm">加载中...</p>
            </div>
        `;
    }
}