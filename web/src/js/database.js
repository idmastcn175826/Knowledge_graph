// database.js
import { state, API_BASE_URL } from './state.js';
import { showProgressModal, hideProgressModal } from './ui.js';

export function initDatabaseEventListeners() {
    // 现有事件监听
    document.getElementById('connect-database-btn').addEventListener('click', handleDatabaseConnect);
    document.getElementById('generate-sql-btn').addEventListener('click', handleGenerateSQL);
    document.getElementById('execute-sql-btn').addEventListener('click', handleExecuteQuery);
    document.getElementById('copy-sql-btn').addEventListener('click', handleCopySQL);

    // 加载保存的连接信息
    loadSavedConnections();

    // 初始化连接选择下拉框事件
    initConnectionSelector();
}

// 初始化连接选择器
function initConnectionSelector() {
    const connectionSelector = document.getElementById('saved-connections');
    if (connectionSelector) {
        connectionSelector.addEventListener('change', (e) => {
            const connectionId = e.target.value;
            if (connectionId) {
                loadConnection(connectionId);
            }
        });
    }
}

// 处理数据库连接并保存
export async function handleDatabaseConnect() {
    const dbType = document.getElementById('sql-database-select').value;
    const host = document.getElementById('db-host').value;
    const port = document.getElementById('db-port').value;
    const database = document.getElementById('db-name').value;
    const tableName = document.getElementById('table-name').value;
    const username = document.getElementById('db-username').value;
    const password = document.getElementById('db-password').value;
    const connectionName = document.getElementById('connection-name')?.value ||
                          `${dbType}_${database}_${new Date().getTime().toString().slice(-4)}`;

    if (!dbType || !host || !database || !username || !password) {
        alert('请填写完整的数据库连接信息');
        return;
    }

    try {
        showProgressModal('连接数据库', '正在连接数据库，请稍候...');

        const response = await fetch(`${API_BASE_URL}/api/v1/dataset/connect`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({
                db_type: dbType,
                host: host,
                user: username,
                password: password,
                database: database,
                port: port ? parseInt(port) : undefined
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '数据库连接失败');
        }

        const result = await response.json();
        const connectionId = result.connection_id;

        // 保存连接信息到状态
        const connectionInfo = {
            id: connectionId,
            name: connectionName,
            dbType,
            host,
            port,
            database,
            tableName,
            username
            // 不保存密码
        };

        state.dbConnections[connectionId] = connectionInfo;
        state.currentConnection = connectionId;

        // 保存到本地存储
        saveConnection(connectionInfo);

        // 更新UI
        document.getElementById('generate-sql-btn').disabled = false;
        updateConnectionSelector();
        hideProgressModal();
        alert('数据库连接成功！');
    } catch (error) {
        console.error('数据库连接失败:', error);
        hideProgressModal();
        alert('数据库连接失败: ' + error.message);
    }
}

// 保存连接信息到本地存储
function saveConnection(connectionInfo) {
    try {
        // 获取现有连接
        const savedConnections = getSavedConnections();

        // 添加或更新连接
        savedConnections[connectionInfo.id] = connectionInfo;

        // 保存回本地存储
        localStorage.setItem('dbConnections', JSON.stringify(savedConnections));
        alert(`连接 "${connectionInfo.name}" 已保存`);
    } catch (error) {
        console.error('保存连接失败:', error);
        alert('保存连接信息失败');
    }
}

// 从本地存储获取所有保存的连接
function getSavedConnections() {
    try {
        const saved = localStorage.getItem('dbConnections');
        return saved ? JSON.parse(saved) : {};
    } catch (error) {
        console.error('获取保存的连接失败:', error);
        return {};
    }
}

// 加载所有保存的连接
function loadSavedConnections() {
    const connections = getSavedConnections();
    state.dbConnections = { ...state.dbConnections, ...connections };
    updateConnectionSelector();
}

// 更新连接选择下拉框
function updateConnectionSelector() {
    const connections = getSavedConnections();
    const selectorContainer = document.getElementById('connection-selector-container');

    // 如果没有容器，创建一个
    if (!selectorContainer) {
        createConnectionSelector();
        return;
    }

    const selector = document.getElementById('saved-connections');
    if (!selector) return;

    // 清空现有选项
    selector.innerHTML = '<option value="">选择已保存的连接</option>';

    // 添加所有连接
    Object.values(connections).forEach(conn => {
        const option = document.createElement('option');
        option.value = conn.id;
        option.textContent = `${conn.name} (${conn.dbType} - ${conn.database})`;
        selector.appendChild(option);
    });
}

// 创建连接选择器UI
function createConnectionSelector() {
    const container = document.createElement('div');
    container.id = 'connection-selector-container';
    container.className = 'mb-4';

    container.innerHTML = `
        <label class="form-label">已保存的连接</label>
        <div class="flex gap-2">
            <select id="saved-connections" class="input flex-1">
                <option value="">选择已保存的连接</option>
            </select>
            <button id="delete-connection" class="btn btn-outline text-danger px-3">
                <i class="fa fa-trash"></i>
            </button>
        </div>
    `;

    // 添加到页面（假设添加到数据库类型选择框下方）
    const dbTypeSelector = document.getElementById('sql-database-select');
    if (dbTypeSelector && dbTypeSelector.parentElement) {
        dbTypeSelector.parentElement.after(container);

        // 添加删除连接事件
        document.getElementById('delete-connection').addEventListener('click', deleteSelectedConnection);

        // 重新加载选项
        updateConnectionSelector();
    }
}

// 加载特定连接
function loadConnection(connectionId) {
    const connections = getSavedConnections();
    const connection = connections[connectionId];

    if (!connection) {
        alert('未找到该连接信息');
        return;
    }

    // 填充表单
    document.getElementById('sql-database-select').value = connection.dbType || '';
    document.getElementById('db-host').value = connection.host || '';
    document.getElementById('db-port').value = connection.port || '';
    document.getElementById('db-name').value = connection.database || '';
    document.getElementById('table-name').value = connection.tableName || '';
    document.getElementById('db-username').value = connection.username || '';
    // 不自动填充密码，需要用户手动输入

    // 更新状态
    state.currentConnection = connectionId;
    document.getElementById('generate-sql-btn').disabled = false;

    alert(`已加载连接: ${connection.name}`);
}

// 删除选中的连接
function deleteSelectedConnection() {
    const selector = document.getElementById('saved-connections');
    const connectionId = selector.value;

    if (!connectionId) {
        alert('请先选择要删除的连接');
        return;
    }

    if (confirm('确定要删除这个连接吗？')) {
        try {
            const connections = getSavedConnections();
            const connectionName = connections[connectionId]?.name || '该连接';

            // 删除连接
            delete connections[connectionId];
            localStorage.setItem('dbConnections', JSON.stringify(connections));

            // 更新状态
            if (state.currentConnection === connectionId) {
                state.currentConnection = null;
                document.getElementById('generate-sql-btn').disabled = true;
            }

            // 更新UI
            updateConnectionSelector();
            alert(`连接 "${connectionName}" 已删除`);
        } catch (error) {
            console.error('删除连接失败:', error);
            alert('删除连接失败');
        }
    }
}

export async function handleGenerateSQL() {
    if (!state.currentConnection) {
        alert('请先连接数据库');
        return;
    }

    const question = document.getElementById('nl-query-input').value;
    const tableName = document.getElementById('table-name').value;

    if (!question) {
        alert('请输入查询问题');
        return;
    }

    try {
        showProgressModal('生成SQL', '正在生成SQL语句，请稍候...');

        const response = await fetch(`${API_BASE_URL}/api/v1/dataset/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({
                connection_id: state.currentConnection,
                question: question,
                table_name: tableName || undefined
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '生成SQL失败');
        }

        const result = await response.json();
        document.getElementById('generated-sql').textContent = result.sql;
        document.getElementById('execute-sql-btn').disabled = false;
        hideProgressModal();
    } catch (error) {
        console.error('生成SQL失败:', error);
        hideProgressModal();
        alert('生成SQL失败: ' + error.message);
    }
}

export async function handleExecuteQuery() {
    const sql = document.getElementById('generated-sql').textContent;

    if (!sql) {
        alert('请先生成SQL语句');
        return;
    }

    try {
        showProgressModal('执行查询', '正在执行查询，请稍候...');

        const response = await fetch(`${API_BASE_URL}/api/v1/dataset/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({
                connection_id: state.currentConnection,
                sql: sql
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '查询执行失败');
        }

        const result = await response.json();
        displayQueryResults(result);
        hideProgressModal();
    } catch (error) {
        console.error('查询执行失败:', error);
        hideProgressModal();
        alert('查询执行失败: ' + error.message);
    }
}

export function handleCopySQL() {
    const sql = document.getElementById('generated-sql').textContent;
    if (sql) {
        navigator.clipboard.writeText(sql).then(() => {
            alert('SQL已复制到剪贴板');
        }).catch(err => {
            console.error('复制失败:', err);
            alert('复制失败，请手动复制');
        });
    }
}

export function displayQueryResults(data) {
    const resultsContainer = document.getElementById('query-results');

    if (!data || data.length === 0) {
        resultsContainer.innerHTML = '<p class="text-gray-500">查询结果为空</p>';
        return;
    }

    let html = '<table class="min-w-full divide-y divide-gray-200"><thead><tr>';
    Object.keys(data[0]).forEach(key => {
        html += `<th class="px-4 py-2 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase">${key}</th>`;
    });
    html += '</tr></thead><tbody class="bg-white divide-y divide-gray-200">';

    data.forEach(row => {
        html += '<tr>';
        Object.values(row).forEach(value => {
            html += `<td class="px-4 py-2 whitespace-nowrap text-sm text-gray-500">${value}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    resultsContainer.innerHTML = html;
}
