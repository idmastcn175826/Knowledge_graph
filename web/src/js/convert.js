// convert.js
import { state, API_BASE_URL } from './state.js';
import { showProgressModal, hideProgressModal } from './ui.js';
import { formatTime } from './utils.js';

export function initConvertEventListeners() {
    document.getElementById('convert-type-select').addEventListener('change', handleConvertTypeChange);
    document.getElementById('start-convert-btn').addEventListener('click', handleStartConvert);
    document.getElementById('json-convert-btn').addEventListener('click', handleJsonConvert);
}

export function handleConvertTypeChange() {
    const convertType = document.getElementById('convert-type-select').value;

    document.getElementById('file-convert-form').classList.add('hidden');
    document.getElementById('unstructured-convert-form').classList.add('hidden');
    document.getElementById('sql-convert-form').classList.add('hidden');

    if (convertType === 'file') {
        document.getElementById('file-convert-form').classList.remove('hidden');
        populateFileSelect('file-select', ['json', 'csv']);
    } else if (convertType === 'unstructured') {
        document.getElementById('unstructured-convert-form').classList.remove('hidden');
        populateFileSelect('unstructured-file-select', ['pdf', 'txt', 'docx', 'doc']);
    } else if (convertType === 'sql') {
        document.getElementById('sql-convert-form').classList.remove('hidden');
    }
}

export function populateFileSelect(selectId, allowedTypes) {
    const select = document.getElementById(selectId);
    select.innerHTML = '<option value="">请选择文件</option>';

    state.files.forEach(file => {
        const fileExt = file.file_name.split('.').pop().toLowerCase();
        if (allowedTypes.includes(fileExt)) {
            const option = document.createElement('option');
            option.value = file.file_id;
            option.textContent = file.file_name;
            select.appendChild(option);
        }
    });
}

export async function handleStartConvert() {
    const convertType = document.getElementById('convert-type-select').value;
    const outputPath = document.getElementById('output-path').value;

    if (!outputPath) {
        alert('请输入输出路径');
        return;
    }

    let sourceInfo = {};

    try {
        showProgressModal('数据转换', '正在准备转换数据，请稍候...');

        if (convertType === 'file') {
            const fileId = document.getElementById('file-select').value;
            const fileFormat = document.getElementById('file-format').value;

            if (!fileId) {
                throw new Error('请选择文件');
            }

            const file = state.files.find(f => f.file_id === fileId);
            if (!file) {
                throw new Error('选择的文件不存在');
            }

            sourceInfo = {
                path: file.file_path || file.file_name,
                format: fileFormat
            };
        } else if (convertType === 'unstructured') {
            const fileId = document.getElementById('unstructured-file-select').value;
            const fileFormat = document.getElementById('unstructured-format').value;

            if (!fileId) {
                throw new Error('请选择文件');
            }

            const file = state.files.find(f => f.file_id === fileId);
            if (!file) {
                throw new Error('选择的文件不存在');
            }

            sourceInfo = {
                path: file.file_path || file.file_name,
                format: fileFormat
            };
        } else if (convertType === 'sql') {
            const dbType = document.getElementById('sql-db-type').value;
            const host = document.getElementById('sql-host').value;
            const port = document.getElementById('sql-port').value;
            const database = document.getElementById('sql-database').value;
            const username = document.getElementById('sql-username').value;
            const password = document.getElementById('sql-password').value;
            const query = document.getElementById('sql-query').value;

            if (!host || !database || !username || !query) {
                throw new Error('请填写完整的数据库信息');
            }

            sourceInfo = {
                type: dbType,
                config: {
                    host,
                    database,
                    user: username,
                    password,
                    port: port ? parseInt(port) : undefined
                },
                query
            };
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/convert/convert`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({
                source_type: convertType,
                source_info: sourceInfo,
                output_path: outputPath
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '数据转换失败');
        }

        const result = await response.json();
        document.getElementById('convert-result').innerHTML = `
            <div class="p-4 bg-success/10 text-success rounded-lg">
                <div class="flex items-center justify-between mb-2">
                    <span class="font-medium">转换成功</span>
                    <i class="fa fa-check-circle"></i>
                </div>
                <p class="text-sm">输出路径: ${result.output_path}</p>
                <p class="text-sm">转换数量: ${result.converted_count} 条</p>
            </div>
        `;

        addConvertHistory(convertType, outputPath, result.converted_count);
        hideProgressModal();
        alert('数据转换成功！');
    } catch (error) {
        console.error('数据转换失败:', error);
        hideProgressModal();
        alert('数据转换失败: ' + error.message);

        document.getElementById('convert-result').innerHTML = `
            <div class="p-4 bg-danger/10 text-danger rounded-lg">
                <div class="flex items-center justify-between mb-2">
                    <span class="font-medium">转换失败</span>
                    <i class="fa fa-exclamation-circle"></i>
                </div>
                <p class="text-sm">${error.message}</p>
            </div>
        `;
    }
}

export async function handleJsonConvert() {
    const fileId = document.getElementById('json-file-select').value;
    const structureType = document.getElementById('json-structure-type').value;
    const outputPath = document.getElementById('json-output-path').value;

    if (!fileId || !outputPath) {
        alert('请选择JSON文件并指定输出路径');
        return;
    }

    try {
        showProgressModal('JSON转换', '正在处理JSON文件，请稍候...');

        const file = state.files.find(f => f.file_id === fileId);
        if (!file) {
            throw new Error('选择的文件不存在');
        }

        const requestData = {
            source_type: 'file',
            source_info: {
                path: file.file_path || file.file_name,
                format: 'json'
            },
            output_path: outputPath
        };

        if (structureType === 'custom') {
            const fieldMapping = document.getElementById('json-field-mapping').value;
            try {
                const mapping = JSON.parse(fieldMapping);
                requestData.source_info.field_mapping = mapping;
            } catch (e) {
                throw new Error('字段映射格式错误，必须是有效的JSON');
            }
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/convert/convert`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'JSON转换失败');
        }

        const result = await response.json();
        document.getElementById('convert-result').innerHTML = `
            <div class="p-4 bg-success/10 text-success rounded-lg">
                <div class="flex items-center justify-between mb-2">
                    <span class="font-medium">JSON转换成功</span>
                    <i class="fa fa-check-circle"></i>
                </div>
                <p class="text-sm">输出路径: ${result.output_path}</p>
                <p class="text-sm">转换数量: ${result.converted_count} 条</p>
                <button class="btn btn-outline btn-sm mt-2" onclick="downloadFile('${result.output_path}')">
                    <i class="fa fa-download"></i> 下载转换结果
                </button>
            </div>
        `;

        addConvertHistory('json', outputPath, result.converted_count);
        hideProgressModal();
        alert('JSON文件转换成功！');
    } catch (error) {
        console.error('JSON转换失败:', error);
        hideProgressModal();
        alert('JSON转换失败: ' + error.message);

        document.getElementById('convert-result').innerHTML = `
            <div class="p-4 bg-danger/10 text-danger rounded-lg">
                <div class="flex items-center justify-between mb-2">
                    <span class="font-medium">JSON转换失败</span>
                    <i class="fa fa-exclamation-circle"></i>
                </div>
                <p class="text-sm">${error.message}</p>
            </div>
        `;
    }
}

export function addConvertHistory(type, outputPath, count) {
    const historyContainer = document.getElementById('convert-history');

    if (historyContainer.querySelector('.text-center')) {
        historyContainer.innerHTML = '';
    }

    const historyItem = document.createElement('div');
    historyItem.className = 'flex items-center justify-between p-3 bg-gray-50 rounded-lg';
    historyItem.innerHTML = `
        <div>
            <div class="font-medium">${getConvertTypeName(type)}转换</div>
            <div class="text-sm text-gray-500">${outputPath}</div>
        </div>
        <div class="text-right">
            <div class="text-sm">${count} 条数据</div>
            <div class="text-xs text-gray-400">${formatTime(new Date())}</div>
        </div>
    `;

    historyContainer.prepend(historyItem);
}

export function getConvertTypeName(type) {
    const typeMap = {
        'file': '文件',
        'unstructured': '非结构化文件',
        'sql': 'SQL数据库'
    };
    return typeMap[type] || type;
}