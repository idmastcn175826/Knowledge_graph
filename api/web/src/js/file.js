// file.js
import {API_BASE_URL, state} from './state.js';
import {formatDate, formatFileSize, getFileIconClass, getFileNameExtension} from './utils.js';
import {hideConfirmDeleteModal, showDeleteConfirm} from './ui.js';

export function initFileEventListeners() {
    document.getElementById('upload-file-btn').addEventListener('click', () => {
        document.getElementById('file-input').click();
    });

    document.getElementById('file-upload-area').addEventListener('click', () => {
        document.getElementById('file-input').click();
    });

    document.getElementById('file-input').addEventListener('change', handleFileSelection);

    const fileUploadArea = document.getElementById('file-upload-area');
    fileUploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        fileUploadArea.classList.add('border-primary');
    });

    fileUploadArea.addEventListener('dragleave', () => {
        fileUploadArea.classList.remove('border-primary');
    });

    fileUploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        fileUploadArea.classList.remove('border-primary');
        if (e.dataTransfer.files.length) {
            uploadFiles(e.dataTransfer.files);
        }
    });
}

export function handleFileSelection(e) {
    if (e.target.files.length) {
        uploadFiles(e.target.files);
        e.target.value = '';
    }
}

export async function uploadFiles(files) {
    if (!files.length) return;

    const progressContainer = document.getElementById('file-upload-progress');
    const progressBar = document.getElementById('upload-progress-bar');
    const progressPercent = document.getElementById('upload-progress-percent');
    const fileNameElement = document.getElementById('uploading-filename');

    progressContainer.classList.remove('hidden');

    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        fileNameElement.textContent = file.name;

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/file/upload`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${state.token}`
                },
                body: formData
            });

            if (!response.ok) {
                throw new Error('文件上传失败');
            }

            const progress = Math.round(((i + 1) / files.length) * 100);
            progressBar.style.width = `${progress}%`;
            progressPercent.textContent = `${progress}%`;
            fetchFiles();
        } catch (error) {
            console.error('文件上传失败:', error);
            alert(`文件 ${file.name} 上传失败: ${error.message}`);
        }
    }

    setTimeout(() => {
        progressContainer.classList.add('hidden');
        progressBar.style.width = '0%';
        progressPercent.textContent = '0%';
    }, 1000);
}

export async function fetchFiles(page = 1, pageSize = 20) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/file/list?page=${page}&page_size=${pageSize}`, {
            headers: {
                'Authorization': `Bearer ${state.token}`
            }
        });

        if (!response.ok) {
            throw new Error('获取文件列表失败');
        }

        const files = await response.json();
        state.files = files;
        state.currentPage = page;
        state.pageSize = pageSize;

        renderFileTable();
        updateFilePagination();
        populateFileSelection();
    } catch (error) {
        console.error('获取文件列表失败:', error);
    }
}

export function renderFileTable() {
    const tableBody = document.getElementById('file-table');

    if (state.files.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="5" class="py-8 text-center text-gray-500">
                    <i class="fa fa-file-o text-3xl mb-2"></i>
                    <p>暂无上传的文件</p>
                    <p class="text-sm mt-1">点击"上传文件"按钮开始上传</p>
                </td>
            </tr>
        `;
        return;
    }

    let html = '';
    state.files.forEach(file => {
        const fileSize = formatFileSize(file.file_size);
        html += `
            <tr class="border-b border-gray-100 hover:bg-gray-50">
                <td class="py-4">
                    <div class="flex items-center gap-3">
                        <i class="fa fa-file-${getFileIconClass(file.file_type, file.file_name)} text-primary"></i>
                        <span>${file.file_name}</span>
                    </div>
                </td>
                <td class="py-4 text-gray-500">${fileSize}</td>
                <td class="py-4">
                    <span class="badge bg-gray-100 text-gray-700">${getFileNameExtension(file.file_name) || file.file_type}</span>
                </td>
                <td class="py-4 text-gray-500 text-sm">${formatDate(file.upload_time)}</td>
                <td class="py-4">
                    <div class="flex gap-2">
                        <button class="text-primary hover:text-primary/80" onclick="downloadFile('${file.file_id}')" title="下载">
                            <i class="fa fa-download"></i>
                        </button>
                        <button class="text-danger hover:text-danger/80" onclick="showDeleteFileConfirm('${file.file_id}', '${file.file_name.replace(/'/g, "\\'")}')" title="删除">
                            <i class="fa fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });

    tableBody.innerHTML = html;
}

export function updateFilePagination() {
    const totalCount = state.files.length;
    const currentPage = state.currentPage;
    const pageSize = state.pageSize;

    const start = (currentPage - 1) * pageSize + 1;
    const end = Math.min(currentPage * pageSize, totalCount);
    document.getElementById('file-showing-range').textContent = `${start}-${end}`;
    document.getElementById('file-total-count').textContent = totalCount;

    const prevBtn = document.getElementById('file-prev-page');
    const nextBtn = document.getElementById('file-next-page');

    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = end >= totalCount;

    prevBtn.onclick = () => {
        if (currentPage > 1) {
            fetchFiles(currentPage - 1, pageSize);
        }
    };

    nextBtn.onclick = () => {
        if (end < totalCount) {
            fetchFiles(currentPage + 1, pageSize);
        }
    };
}

export async function downloadFile(fileId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/file/${fileId}/download`, {
            headers: {
                'Authorization': `Bearer ${state.token}`
            }
        });

        if (!response.ok) {
            throw new Error('文件下载失败');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);

        const file = state.files.find(f => f.file_id === fileId);
        const fileName = file ? file.file_name : 'downloaded-file';

        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();

        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        console.error('文件下载失败:', error);
        alert('文件下载失败: ' + error.message);
    }
}

export function showDeleteFileConfirm(fileId, fileName) {
    const messageElement = document.getElementById('delete-confirmation-message');
    messageElement.textContent = `您确定要删除文件 "${fileName}" 吗？此操作无法撤销。`;

    // 设置确认删除回调
    const confirmBtn = document.getElementById('confirm-delete');
    confirmBtn.setAttribute('data-delete-type', 'file');
    confirmBtn.setAttribute('data-delete-id', fileId);

    // 显示确认模态框
    document.getElementById('confirm-delete-modal').classList.remove('hidden');
}


export async function deleteFile(fileId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/file/${fileId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${state.token}`
            }
        });

        if (!response.ok) {
            throw new Error('文件删除失败');
        }

        fetchFiles();
        hideConfirmDeleteModal();
    } catch (error) {
        console.error('文件删除失败:', error);
        alert('文件删除失败: ' + error.message);
    }
}

export function populateFileSelection() {
    const container = document.getElementById('file-selection-container');

    if (state.files.length === 0) {
        container.innerHTML = `
            <p class="text-gray-500 text-sm italic">暂无上传的文件，请先上传文件</p>
        `;
        return;
    }

    let html = '';
    state.files.forEach(file => {
        html += `
            <div class="flex items-center">
                <input type="checkbox" id="file-${file.file_id}" value="${file.file_id}" class="w-4 h-4 text-primary rounded">
                <label for="file-${file.file_id}" class="ml-2 text-sm">${file.file_name}</label>
            </div>
        `;
    });

    container.innerHTML = html;
}