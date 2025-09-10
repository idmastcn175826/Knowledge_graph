// utils.js
export function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export function getFileIconClass(fileType, fileName) {
    if (!fileType && !fileName) return 'o';

    const extMatch = fileName ? fileName.match(/\.([^\.]+)$/) : null;
    const ext = extMatch ? extMatch[1].toLowerCase() : '';
    const type = fileType ? fileType.toLowerCase() : '';

    if (ext === 'txt' || type.includes('text/plain')) return 'text-o';
    if (ext === 'pdf' || type.includes('pdf')) return 'pdf-o';
    if (ext === 'doc' || ext === 'docx' || type.includes('word')) return 'word-o';
    if (ext === 'xls' || ext === 'xlsx' || type.includes('excel')) return 'excel-o';
    if (ext === 'ppt' || ext === 'pptx' || type.includes('powerpoint')) return 'powerpoint-o';
    if (type.includes('image')) return 'image-o';
    if (type.includes('audio')) return 'audio-o';
    if (type.includes('video')) return 'video-o';
    if (ext === 'zip' || ext === 'rar' || ext === '7z' || type.includes('zip')) return 'zip-o';
    if (ext === 'js' || ext === 'html' || ext === 'css' || ext === 'py' || ext === 'java' || ext === 'cpp') return 'code-o';

    return 'o';
}

export function getFileNameExtension(fileName) {
    if (!fileName) return '';
    const extMatch = fileName.match(/\.([^\.]+)$/);
    return extMatch ? extMatch[1].toUpperCase() : '';
}

export function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString();
}

export function formatTime(date) {
    return date.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
}

export function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.floor(Math.random() * 10000);
}

export function getKGStatusBadge(status) {
    switch (status) {
        case 'completed':
            return {badgeClass: 'bg-success/10 text-success', statusText: '已完成'};
        case 'processing':
            return {badgeClass: 'bg-warning/10 text-warning', statusText: '处理中'};
        case 'failed':
            return {badgeClass: 'bg-danger/10 text-danger', statusText: '失败'};
        case 'pending':
            return {badgeClass: 'bg-gray-100 text-gray-700', statusText: '等待中'};
        default:
            return {badgeClass: 'bg-primary/10 text-primary', statusText: '未知'};
    }
}

export function updateCurrentTime() {
    const now = new Date();
    document.getElementById('current-time').textContent = now.toLocaleString();
}