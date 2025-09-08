// database.js
import { state, API_BASE_URL } from './state.js';
import { showProgressModal, hideProgressModal } from './ui.js';

export function initDatabaseEventListeners() {
    document.getElementById('connect-database-btn').addEventListener('click', handleDatabaseConnect);
    document.getElementById('test-db-connection').addEventListener('click', handleTestConnection);
    document.getElementById('generate-sql-btn').addEventListener('click', handleGenerateSQL);
    document.getElementById('execute-sql-btn').addEventListener('click', handleExecuteQuery);
    document.getElementById('copy-sql-btn').addEventListener('click', handleCopySQL);
}

export async function handleDatabaseConnect() {
    const dbType = document.getElementById('sql-database-select').value;
    const host = document.getElementById('db-host').value;
    const port = document.getElementById('db-port').value;
    const database = document.getElementById('db-name').value;
    const username = document.getElementById('db-username').value;
    const password = document.getElementById('db-password').value;

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
        state.dbConnections[connectionId] = {
            dbType,
            host,
            database,
            connectionId
        };
        state.currentConnection = connectionId;

        document.getElementById('generate-sql-btn').disabled = false;
        hideProgressModal();
        alert('数据库连接成功！');
    } catch (error) {
        console.error('数据库连接失败:', error);
        hideProgressModal();
        alert('数据库连接失败: ' + error.message);
    }
}

export async function handleTestConnection() {
    // 测试连接实现
    alert('测试连接功能待实现');
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