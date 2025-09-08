// ui.js
export function showProgressModal(title, message) {
    document.getElementById('progress-title').textContent = title;
    document.getElementById('progress-message').textContent = message;
    document.getElementById('progress-stage').textContent = '准备中';
    document.getElementById('progress-percent').textContent = '0%';
    document.getElementById('progress-bar').style.width = '0%';
    document.getElementById('progress-modal').classList.remove('hidden');
}

export function updateProgressModal(progress, stage, message) {
    document.getElementById('progress-stage').textContent = stage;
    document.getElementById('progress-message').textContent = message;
    document.getElementById('progress-percent').textContent = `${progress}%`;
    document.getElementById('progress-bar').style.width = `${progress}%`;
}

export function hideProgressModal() {
    document.getElementById('progress-modal').classList.add('hidden');
}

export function showDeleteConfirm(type, id, name) {
    const messageElement = document.getElementById('delete-confirmation-message');
    messageElement.textContent = `您确定要删除${type === 'kg' ? '知识图谱' : '文件'} "${name}" 吗？此操作无法撤销。`;

    const confirmBtn = document.getElementById('confirm-delete');
    confirmBtn.setAttribute('data-delete-type', type);
    confirmBtn.setAttribute('data-delete-id', id);

    document.getElementById('confirm-delete-modal').classList.remove('hidden');
}

export function hideConfirmDeleteModal() {
    document.getElementById('confirm-delete-modal').classList.add('hidden');
}