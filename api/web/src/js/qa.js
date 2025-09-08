// qa.js
import { state, API_BASE_URL } from './state.js';
import { formatTime, generateSessionId } from './utils.js';

export function initQAEventListeners() {
    document.getElementById('send-question').addEventListener('click', sendQuestion);
    document.getElementById('question-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendQuestion();
        }
    });

    document.getElementById('qa-kg-select').addEventListener('change', handleKGSelectForQA);
    document.getElementById('qa-clear-history').addEventListener('click', clearQAHistory);
}

export function populateKGSelectForQA() {
    const select = document.getElementById('qa-kg-select');
    const currentValue = select.value;

    select.innerHTML = '<option value="">选择知识图谱</option>';

    if (state.knowledgeGraphs.length === 0) {
        document.getElementById('question-input').disabled = true;
        document.getElementById('send-question').disabled = true;
        return;
    }

    state.knowledgeGraphs.forEach(kg => {
        const option = document.createElement('option');
        option.value = kg.kg_id;
        option.textContent = kg.name;
        select.appendChild(option);
    });

    if (currentValue) {
        select.value = currentValue;
    }
}

export function handleKGSelectForQA(e) {
    const kgId = e.target.value;

    if (kgId) {
        state.currentKGId = kgId;
        document.getElementById('question-input').disabled = false;
        document.getElementById('send-question').disabled = false;

        if (!state.currentSessionId) {
            state.currentSessionId = generateSessionId();
        }

        fetchQAHistory(kgId);
    } else {
        document.getElementById('question-input').disabled = true;
        document.getElementById('send-question').disabled = true;
        state.currentKGId = null;
    }
}

export async function sendQuestion() {
    const question = document.getElementById('question-input').value.trim();

    if (!question) return;

    if (!state.currentKGId) {
        alert('请先选择一个知识图谱');
        return;
    }

    if (!state.currentSessionId) {
        state.currentSessionId = generateSessionId();
    }

    try {
        addMessageToHistory(question, 'user');
        document.getElementById('question-input').value = '';
        const thinkingMessageId = addMessageToHistory('正在思考...', 'ai', true);

        const response = await fetch(`${API_BASE_URL}/api/v1/qa/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({
                kg_id: state.currentKGId,
                question: question,
                top_k: 5,
                use_context: true,
                session_id: state.currentSessionId
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '问答失败');
        }

        const result = await response.json();
        removeMessageFromHistory(thinkingMessageId);
        addMessageToHistory(result.answer, 'ai');
        updateRelatedEntitiesAndRelations(result.related_entities, result.related_relations);
    } catch (error) {
        console.error('问答失败:', error);
        document.getElementById('chat-history').lastChild.remove();
        addMessageToHistory(`出错了: ${error.message}`, 'ai');
    }
}

export function addMessageToHistory(content, sender, isThinking = false) {
    const chatHistory = document.getElementById('chat-history');
    const messageId = `msg-${Date.now()}`;

    if (chatHistory.querySelector('.text-center') && !isThinking) {
        chatHistory.innerHTML = '';
    }

    const messageDiv = document.createElement('div');
    messageDiv.id = messageId;
    messageDiv.className = `flex ${sender === 'user' ? 'justify-start' : 'justify-end'}`;

    const bubbleClass = sender === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai';
    const icon = sender === 'user' ? 'fa-user' : 'fa-robot';
    const iconColor = sender === 'user' ? 'text-gray-500' : 'text-primary';

    messageDiv.innerHTML = `
        <div class="${bubbleClass}">
            <div class="flex items-center gap-2 mb-2">
                <i class="fa ${icon} ${iconColor} text-sm"></i>
                <span class="text-sm font-medium">${sender === 'user' ? '我' : 'AI'}</span>
                <span class="text-xs text-gray-400 ml-auto">${formatTime(new Date())}</span>
            </div>
            <div class="text-gray-800">
                ${isThinking ? '<i class="fa fa-spinner fa-spin"></i>' : content}
            </div>
        </div>
    `;

    chatHistory.appendChild(messageDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;

    return messageId;
}

export function removeMessageFromHistory(messageId) {
    const message = document.getElementById(messageId);
    if (message) {
        message.remove();
    }
}

export function updateRelatedEntitiesAndRelations(entities, relations) {
    const entitiesContainer = document.getElementById('entities-container');
    const relationsContainer = document.getElementById('relations-container');

    if (entities && entities.length > 0) {
        let entitiesHtml = '';
        entities.forEach(entity => {
            entitiesHtml += `
                <div class="bg-gray-50 p-2 rounded-lg text-sm">
                    ${entity.name || '未命名实体'}
                    ${entity.type ? `<span class="text-xs text-gray-500 ml-1">(${entity.type})</span>` : ''}
                </div>
            `;
        });
        entitiesContainer.innerHTML = entitiesHtml;
    } else {
        entitiesContainer.innerHTML = '<p class="text-gray-500 text-sm italic">暂无相关实体</p>';
    }

    if (relations && relations.length > 0) {
        let relationsHtml = '';
        relations.forEach(relation => {
            relationsHtml += `
                <div class="bg-gray-50 p-2 rounded-lg text-sm">
                    <span>${relation.source || '来源'}</span>
                    <span class="text-primary mx-1">${relation.type || '关系'}</span>
                    <span>${relation.target || '目标'}</span>
                </div>
            `;
        });
        relationsContainer.innerHTML = relationsHtml;
    } else {
        relationsContainer.innerHTML = '<p class="text-gray-500 text-sm italic">暂无相关关系</p>';
    }
}

export async function fetchQAHistory(kgId = null) {
    const chatHistory = document.getElementById('chat-history');

    if (!kgId && !state.currentKGId) {
        chatHistory.innerHTML = `
            <div class="text-center text-gray-500 py-10">
                <i class="fa fa-comments-o text-4xl mb-3"></i>
                <p>请先选择一个知识图谱开始对话</p>
            </div>
        `;
        return;
    }

    const targetKgId = kgId || state.currentKGId;

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/qa/history?kg_id=${targetKgId}`, {
            headers: {
                'Authorization': `Bearer ${state.token}`
            }
        });

        if (!response.ok) {
            throw new Error('获取问答历史失败');
        }

        const result = await response.json();
        chatHistory.innerHTML = '';

        if (result.history && result.history.length > 0) {
            state.currentSessionId = result.session_id;

            result.history.forEach(item => {
                addMessageToHistory(item.query.question, 'user');
                addMessageToHistory(item.answer.answer, 'ai');
            });

            const lastAnswer = result.history[result.history.length - 1].answer;
            updateRelatedEntitiesAndRelations(lastAnswer.related_entities, lastAnswer.related_relations);
        } else {
            chatHistory.innerHTML = `
                <div class="text-center text-gray-500 py-10">
                    <i class="fa fa-comment-o text-4xl mb-3"></i>
                    <p>暂无对话历史</p>
                    <p class="text-sm mt-1">请输入问题开始对话</p>
                </div>
            `;
            updateRelatedEntitiesAndRelations([], []);
        }
    } catch (error) {
        console.error('获取问答历史失败:', error);
        chatHistory.innerHTML = `
            <div class="text-center text-gray-500 py-10">
                <i class="fa fa-exclamation-triangle text-4xl mb-3 text-warning"></i>
                <p>加载对话历史失败</p>
                <button class="mt-2 text-primary hover:underline text-sm" onclick="fetchQAHistory('${targetKgId}')">重试</button>
            </div>
        `;
    }
}

export function clearQAHistory() {
    if (!state.currentKGId) {
        alert('请先选择一个知识图谱');
        return;
    }

    if (confirm('确定要清空当前知识图谱的问答历史吗？')) {
        state.currentSessionId = generateSessionId();
        const chatHistory = document.getElementById('chat-history');
        chatHistory.innerHTML = `
            <div class="text-center text-gray-500 py-10">
                <i class="fa fa-comment-o text-4xl mb-3"></i>
                <p>暂无对话历史</p>
                <p class="text-sm mt-1">请输入问题开始对话</p>
            </div>
        `;
        updateRelatedEntitiesAndRelations([], []);
    }
}