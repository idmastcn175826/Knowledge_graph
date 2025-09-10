// knowledgeGraph.js
import { state, API_BASE_URL } from './state.js';
import { formatDate, getKGStatusBadge } from './utils.js';
import { populateKGSelectForQA } from './qa.js';
import { showProgressModal, updateProgressModal, hideProgressModal, showDeleteConfirm, hideConfirmDeleteModal } from './ui.js';

export function initKGEventListeners() {
    document.getElementById('create-kg-btn').addEventListener('click', showCreateKGModal);
    document.getElementById('create-kg-dashboard-btn').addEventListener('click', showCreateKGModal);
    document.getElementById('close-kg-modal').addEventListener('click', hideCreateKGModal);
    document.getElementById('cancel-kg-create').addEventListener('click', hideCreateKGModal);
    document.getElementById('submit-kg-create').addEventListener('click', handleCreateKG);

    document.getElementById('kg-query-btn').addEventListener('click', showKGQueryModal);
    document.getElementById('close-query-modal').addEventListener('click', hideKGQueryModal);
    document.getElementById('cancel-query').addEventListener('click', hideKGQueryModal);
    document.getElementById('submit-query').addEventListener('click', handleKGQuery);

    document.getElementById('close-result-modal').addEventListener('click', hideQueryResultModal);
    document.getElementById('close-result').addEventListener('click', hideQueryResultModal);

    document.getElementById('kg-export-btn').addEventListener('click', handleExportKG);
    document.getElementById('kg-refresh-btn').addEventListener('click', handleRefreshKG);
    document.getElementById('kg-qa-btn').addEventListener('click', startQAWithCurrentKG);
    document.getElementById('kg-back-btn').addEventListener('click', hideKGDetails);

    document.getElementById('confirm-delete').addEventListener('click', handleConfirmDelete);
    document.getElementById('cancel-delete').addEventListener('click', hideConfirmDeleteModal);
}

export async function fetchKnowledgeGraphs() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/kg/list`, {
            headers: {
                'Authorization': `Bearer ${state.token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('获取知识图谱列表失败');
        }

        const result = await response.json();
        state.knowledgeGraphs = result.graphs || [];
        renderKGTable();
        populateKGSelectForQA();
    } catch (error) {
        console.error('获取知识图谱列表失败:', error);
        state.knowledgeGraphs = [];
        renderKGTable();
    }
}

export function renderKGTable() {
    const tableBody = document.getElementById('kg-table');
    const recentTableBody = document.getElementById('recent-kg-table');

    if (state.knowledgeGraphs.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="py-8 text-center text-gray-500">
                    <i class="fa fa-sitemap text-3xl mb-2"></i>
                    <p>暂无知识图谱</p>
                    <p class="text-sm mt-1">点击"创建知识图谱"按钮开始创建</p>
                </td>
            </tr>
        `;
        return;
    }

    let html = '';
    state.knowledgeGraphs.forEach(kg => {
        const {badgeClass, statusText} = getKGStatusBadge(kg.status);
        const safeName = kg.name.replace(/'/g, "\\'");
        const safeKgId = kg.kg_id.replace(/'/g, "\\'");

        html += `<tr class="border-b border-gray-100 hover:bg-gray-50">
            <td class="py-4 font-medium">${kg.name}</td>
            <td class="py-4">${kg.entity_count || 0}</td>
            <td class="py-4">${kg.relation_count || 0}</td>
            <td class="py-4 text-gray-500 text-sm">${formatDate(kg.create_time)}</td>
            <td class="py-4">
                <span class="badge ${badgeClass}">${statusText}</span>
            </td>
            <td class="py-4">
                <div class="flex gap-2">
                    <button class="text-primary hover:text-primary/80" onclick="viewKGDetails('${safeKgId}')" title="查看详情">
                        <i class="fa fa-eye"></i>
                    </button>
                    <button class="text-accent hover:text-accent/80" onclick="startQAWithKG('${safeKgId}', '${safeName}')" title="问答对话">
                        <i class="fa fa-comments"></i>
                    </button>
                    <button class="text-danger hover:text-danger/80" onclick="showDeleteKGConfirm('${safeKgId}', '${safeName}')" title="删除">
                        <i class="fa fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>`;
    });

    tableBody.innerHTML = html;
    updateRecentKGTable();
}

export function updateRecentKGTable() {
    const recentTableBody = document.getElementById('recent-kg-table');

    if (!state.knowledgeGraphs || state.knowledgeGraphs.length === 0) {
        recentTableBody.innerHTML = `
            <tr>
                <td colspan="6" class="py-8 text-center text-gray-500">
                    <i class="fa fa-folder-open-o text-3xl mb-2"></i>
                    <p>暂无知识图谱数据</p>
                    <p class="text-sm mt-1">点击"创建知识图谱"开始构建您的第一个知识图谱</p>
                </td>
            </tr>
        `;
        return;
    }

    const recentKGs = [...state.knowledgeGraphs]
        .sort((a, b) => new Date(b.create_time) - new Date(a.create_time))
        .slice(0, 3);

    let recentHtml = '';
    recentKGs.forEach(kg => {
        const kgId = kg.kg_id || kg.id;
        const name = kg.name || '未命名';
        const entityCount = kg.entity_count || 0;
        const relationCount = kg.relation_count || 0;
        const createTime = kg.create_time || kg.created_at;
        const status = kg.status || 'completed';

        const {badgeClass, statusText} = getKGStatusBadge(status);

        recentHtml += `<tr class="border-b border-gray-100 hover:bg-gray-50">
            <td class="py-4 font-medium">${name}</td>
            <td class="py-4">${entityCount}</td>
            <td class="py-4">${relationCount}</td>
            <td class="py-4 text-gray-500 text-sm">${formatDate(createTime)}</td>
            <td class="py-4">
                <span class="badge ${badgeClass}">${statusText}</span>
            </td>
            <td class="py-4">
                <div class="flex gap-2">
                    <button class="text-primary hover:text-primary/80" onclick="viewKGDetails('${kgId}')" title="查看详情">
                        <i class="fa fa-eye"></i>
                    </button>
                    <button class="text-accent hover:text-accent/80" onclick="startQAWithKG('${kgId}', '${name.replace(/'/g, "\\'")}')" title="问答对话">
                        <i class="fa fa-comments"></i>
                    </button>
                </div>
            </td>
        </tr>`;
    });

    recentTableBody.innerHTML = recentHtml;
}

export function viewKGDetails(kgId) {
    const kg = state.knowledgeGraphs.find(k => k.kg_id === kgId);
    if (!kg) return;

    state.currentKGId = kgId;
    document.getElementById('kg-detail-name').textContent = kg.name;
    document.getElementById('kg-detail-meta').textContent =
        `创建于 ${formatDate(kg.create_time)} · 包含 ${kg.entity_count || 0} 个实体 · ${kg.relation_count || 0} 个关系`;

    document.getElementById('kg-list-section').classList.add('hidden');
    document.getElementById('kg-detail-section').classList.remove('hidden');
    visualizeKG(kgId);
}

export function hideKGDetails() {
    document.getElementById('kg-detail-section').classList.add('hidden');
    document.getElementById('kg-list-section').classList.remove('hidden');
    state.currentKGId = null;
}

export function showCreateKGModal() {
    document.getElementById('create-kg-modal').classList.remove('hidden');
    populateFileSelection();
}

export function hideCreateKGModal() {
    document.getElementById('create-kg-modal').classList.add('hidden');
}

export async function handleCreateKG() {
    const kgName = document.getElementById('kg-name').value;
    const selectedFiles = [];
    document.querySelectorAll('#file-selection-container input[type="checkbox"]:checked').forEach(checkbox => {
        selectedFiles.push(checkbox.value);
    });

    if (!kgName) {
        alert('请输入知识图谱名称');
        return;
    }

    if (selectedFiles.length === 0) {
        alert('请至少选择一个文件');
        return;
    }

    const algorithms = {
        preprocess: document.getElementById('preprocess').value,
        entity_extraction: document.getElementById('entity-extraction').value,
        relation_extraction: document.getElementById('relation-extraction').value,
        knowledge_completion: document.getElementById('knowledge-completion').value
    };

    const modelApiKey = document.getElementById('model-api-key').value;
    const enableCompletion = document.getElementById('enable-completion').checked;
    const enableVisualization = document.getElementById('enable-visualization').checked;

    try {
        hideCreateKGModal();
        showProgressModal('正在创建知识图谱', '正在初始化知识图谱构建过程...');

        const response = await fetch(`${API_BASE_URL}/api/v1/kg/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({
                file_ids: selectedFiles,
                kg_name: kgName,
                algorithms,
                model_api_key: modelApiKey || null,
                enable_completion: enableCompletion,
                enable_visualization: enableVisualization
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '知识图谱创建失败');
        }

        const data = await response.json();
        pollKGProgress(data.task_id);

        document.getElementById('kg-name').value = '';
        document.getElementById('model-api-key').value = '';
        document.querySelectorAll('#file-selection-container input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = false;
        });
    } catch (error) {
        console.error('知识图谱创建失败:', error);
        hideProgressModal();
        alert('知识图谱创建失败: ' + error.message);
    }
}

export async function pollKGProgress(taskId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/kg/progress/${taskId}`, {
            headers: {
                'Authorization': `Bearer ${state.token}`
            }
        });

        if (!response.ok) {
            throw new Error('获取构建进度失败');
        }

        const progressData = await response.json();
        updateProgressModal(
            progressData.progress,
            progressData.stage || '处理中',
            progressData.message || '正在处理...'
        );

        if (progressData.progress < 100 && progressData.status !== 'failed') {
            setTimeout(() => {
                pollKGProgress(taskId);
            }, 3000);
        } else if (progressData.status === 'failed') {
            setTimeout(() => {
                hideProgressModal();
                alert('知识图谱构建失败: ' + (progressData.message || '未知错误'));
            }, 1000);
        } else {
            setTimeout(() => {
                hideProgressModal();
                alert('知识图谱构建完成！');
                switchView('kg-view');
                fetchKnowledgeGraphs();
            }, 1000);
        }
    } catch (error) {
        console.error('获取构建进度失败:', error);
        setTimeout(() => {
            hideProgressModal();
            alert('获取构建进度失败: ' + error.message);
        }, 1000);
    }
}

export async function handleExportKG() {
    if (!state.currentKGId) {
        alert('请先选择一个知识图谱');
        return;
    }

    try {
        showProgressModal('正在导出', '正在导出知识图谱数据，请稍候...');

        const response = await fetch(`${API_BASE_URL}/api/v1/kg/${state.currentKGId}/export`, {
            headers: {
                'Authorization': `Bearer ${state.token}`
            }
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || '导出失败');
        }

        const data = await response.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
        const url = window.URL.createObjectURL(blob);

        const kg = state.knowledgeGraphs.find(k => k.kg_id === state.currentKGId);
        const fileName = kg ? `${kg.name}_export_${new Date().toISOString().slice(0, 10)}.json` : 'knowledge_graph_export.json';

        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();

        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        hideProgressModal();
        alert('导出成功！');
    } catch (error) {
        console.error('导出失败:', error);
        hideProgressModal();
        alert('导出失败: ' + error.message);
    }
}

export async function handleRefreshKG() {
    if (!state.currentKGId) {
        alert('请先选择一个知识图谱');
        return;
    }

    try {
        showProgressModal('正在刷新', '正在刷新知识图谱数据，请稍候...');

        const response = await fetch(`${API_BASE_URL}/api/v1/kg/${state.currentKGId}/refresh`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${state.token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || '刷新失败');
        }

        const result = await response.json();
        await fetchKnowledgeGraphs();
        await fetchKnowledgeGraphDetails(state.currentKGId);

        hideProgressModal();
        alert(result.message || '刷新成功！');
    } catch (error) {
        console.error('刷新失败:', error);
        hideProgressModal();
        alert('刷新失败: ' + error.message);
    }
}

export async function fetchKnowledgeGraphDetails(kgId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/kg/${kgId}`, {
            headers: {
                'Authorization': `Bearer ${state.token}`
            }
        });

        if (response.ok) {
            const kg = await response.json();
            const index = state.knowledgeGraphs.findIndex(k => k.kg_id === kgId);
            if (index !== -1) {
                state.knowledgeGraphs[index] = {...state.knowledgeGraphs[index], ...kg};
            }

            if (state.currentKGId === kgId) {
                document.getElementById('kg-detail-name').textContent = kg.name;
                document.getElementById('kg-detail-meta').textContent =
                    `创建于 ${formatDate(kg.create_time)} · 包含 ${kg.entity_count || 0} 个实体 · ${kg.relation_count || 0} 个关系`;
            }
        }
    } catch (error) {
        console.error('获取知识图谱详情失败:', error);
    }
}

export async function visualizeKG(kgId) {
    const container = document.getElementById('kg-visualization');
    container.innerHTML = `
        <div class="w-full h-full flex items-center justify-center text-gray-400">
            <div class="text-center">
                <i class="fa fa-spinner fa-spin text-2xl mb-3"></i>
                <p>正在加载知识图谱数据...</p>
            </div>
        </div>
    `;

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/kg/${kgId}/visualize`, {
            headers: {
                'Authorization': `Bearer ${state.token}`
            }
        });

        if (!response.ok) {
            throw new Error('获取可视化数据失败');
        }

        const data = await response.json();
        const nodes = new vis.DataSet(data.nodes || []);
        const edges = new vis.DataSet(data.edges || []);

        const networkData = {
            nodes: nodes,
            edges: edges
        };

        const options = {
            nodes: {
                shape: 'dot',
                size: 20,
                font: {
                    size: 12,
                    face: 'Tahoma'
                },
                borderWidth: 2
            },
            edges: {
                width: 2,
                smooth: {
                    type: 'continuous'
                }
            },
            physics: {
                stabilization: true,
                barnesHut: {
                    gravitationalConstant: -80000,
                    springConstant: 0.001,
                    springLength: 200
                }
            },
            interaction: {
                tooltipDelay: 200,
                hideEdgesOnDrag: true
            }
        };

        container.innerHTML = '';
        new vis.Network(container, networkData, options);
    } catch (error) {
        console.error('知识图谱可视化失败:', error);
        container.innerHTML = `
            <div class="w-full h-full flex items-center justify-center text-gray-400">
                <div class="text-center">
                    <i class="fa fa-exclamation-triangle text-2xl mb-3 text-warning"></i>
                    <p>知识图谱加载失败: ${error.message}</p>
                    <button class="mt-2 text-primary hover:underline text-sm" onclick="visualizeKG('${kgId}')">重试</button>
                </div>
            </div>
        `;
    }
}

export function showKGQueryModal() {
    if (!state.currentKGId) {
        alert('请先选择一个知识图谱');
        return;
    }
    document.getElementById('kg-query-modal').classList.remove('hidden');
}

export function hideKGQueryModal() {
    document.getElementById('kg-query-modal').classList.add('hidden');
}

export async function handleKGQuery() {
    const queryContent = document.getElementById('query-content').value;
    const queryType = document.getElementById('query-type').value;
    const topK = parseInt(document.getElementById('query-top-k').value);
    const includeEntities = document.getElementById('include-entities').checked;
    const includeRelations = document.getElementById('include-relations').checked;

    if (!queryContent) {
        alert('请输入查询内容');
        return;
    }

    try {
        hideKGQueryModal();
        showProgressModal('正在查询', '正在查询知识图谱，请稍候...');

        const response = await fetch(`${API_BASE_URL}/api/v1/kg/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({
                kg_id: state.currentKGId,
                query: queryContent,
                query_type: queryType,
                top_k: topK,
                include_entities: includeEntities,
                include_relations: includeRelations
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '查询失败');
        }

        const result = await response.json();
        hideProgressModal();
        showQueryResult(result, queryContent);
    } catch (error) {
        console.error('知识图谱查询失败:', error);
        hideProgressModal();
        alert('查询失败: ' + error.message);
    }
}

export function showQueryResult(result, queryContent) {
    document.getElementById('result-query-content').textContent = queryContent;
    document.getElementById('result-answer').textContent = result.answer || '未找到相关答案';

    const entitiesContainer = document.getElementById('result-entities');
    document.getElementById('entities-count').textContent = result.entities ? result.entities.length : 0;

    if (result.entities && result.entities.length > 0) {
        let entitiesHtml = '';
        result.entities.forEach(entity => {
            entitiesHtml += `
                <div class="bg-gray-50 p-3 rounded-lg border border-gray-100">
                    <div class="font-medium">${entity.name || '未命名实体'}</div>
                    ${entity.type ? `<div class="text-xs text-gray-500">类型: ${entity.type}</div>` : ''}
                </div>
            `;
        });
        entitiesContainer.innerHTML = entitiesHtml;
    } else {
        entitiesContainer.innerHTML = '<p class="text-gray-500 text-sm italic">无相关实体</p>';
    }

    const relationsContainer = document.getElementById('result-relations');
    document.getElementById('relations-count').textContent = result.relations ? result.relations.length : 0;

    if (result.relations && result.relations.length > 0) {
        let relationsHtml = '';
        result.relations.forEach(relation => {
            relationsHtml += `
                <div class="bg-gray-50 p-3 rounded-lg border border-gray-100">
                    <div class="flex items-center justify-between">
                        <span class="font-medium">${relation.source || '来源'}</span>
                        <span class="text-primary">${relation.type || '关系'}</span>
                        <span class="font-medium">${relation.target || '目标'}</span>
                    </div>
                </div>
            `;
        });
        relationsContainer.innerHTML = relationsHtml;
    } else {
        relationsContainer.innerHTML = '<p class="text-gray-500 text-sm italic">无相关关系</p>';
    }

    document.getElementById('query-result-modal').classList.remove('hidden');
}

export function hideQueryResultModal() {
    document.getElementById('query-result-modal').classList.add('hidden');
}

export function showDeleteKGConfirm(kgId, kgName) {
    showDeleteConfirm('kg', kgId, kgName);
}

export async function deleteKG(kgId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/kg/${kgId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${state.token}`
            }
        });

        if (!response.ok) {
            throw new Error('知识图谱删除失败');
        }

        fetchKnowledgeGraphs();

        if (state.currentKGId === kgId) {
            document.getElementById('kg-detail-section').classList.add('hidden');
            state.currentKGId = null;
        }

        if (document.getElementById('qa-kg-select').value === kgId) {
            document.getElementById('qa-kg-select').value = '';
            document.getElementById('question-input').disabled = true;
            document.getElementById('send-question').disabled = true;
            state.currentKGId = null;
            state.currentSessionId = null;
            fetchQAHistory();
        }

        hideConfirmDeleteModal();
    } catch (error) {
        console.error('知识图谱删除失败:', error);
        alert('知识图谱删除失败: ' + error.message);
    }
}

export function handleConfirmDelete() {
    const deleteType = document.getElementById('confirm-delete').getAttribute('data-delete-type');
    const deleteId = document.getElementById('confirm-delete').getAttribute('data-delete-id');

    if (deleteType === 'kg') {
        deleteKG(deleteId);
    } else if (deleteType === 'file') {
        deleteFile(deleteId);
    }

    hideConfirmDeleteModal();
}

export function startQAWithCurrentKG() {
    if (!state.currentKGId) {
        alert('请先选择一个知识图谱');
        return;
    }

    const kg = state.knowledgeGraphs.find(k => k.kg_id === state.currentKGId);
    if (kg) {
        startQAWithKG(state.currentKGId, kg.name);
    }
}

export function startQAWithKG(kgId, kgName) {
    switchView('qa-view');
    document.querySelectorAll('.nav-item').forEach(navItem => {
        navItem.classList.remove('active');
    });
    document.querySelector('.nav-item[data-view="qa-view"]').classList.add('active');

    const select = document.getElementById('qa-kg-select');
    select.value = kgId;
    const event = new Event('change');
    select.dispatchEvent(event);
}