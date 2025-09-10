import { apiRequest } from './api.js';

// DOM元素缓存
const elements = {
    // 主视图元素
    ragView: document.getElementById('rag-view'),

    // 集合相关元素
    collectionSelect: document.getElementById('rag-collection-select'),
    createCollectionBtn: document.getElementById('create-rag-collection'),
    createCollectionModal: document.getElementById('create-collection-modal'),
    newCollectionName: document.getElementById('new-collection-name'),
    newCollectionDesc: document.getElementById('new-collection-desc'),
    confirmCreateCollection: document.getElementById('confirm-create-collection'),
    deleteCollectionBtn: document.getElementById('delete-rag-collection'),
    collectionInfo: document.getElementById('collection-info'),
    currentCollectionName: document.getElementById('current-collection-name'),
    currentCollectionCount: document.getElementById('current-collection-count'),

    // 文档相关元素
    documentSelect: document.getElementById('rag-document-select'),
    fileUpload: document.getElementById('rag-document-upload'),
    fileUploadArea: document.getElementById('rag-file-upload-area'),
    removeDocumentBtn: document.getElementById('rag-remove-document'),
    uploadProgress: document.getElementById('rag-upload-progress'),
    uploadBar: document.getElementById('rag-upload-bar'),
    uploadFilename: document.getElementById('rag-upload-filename'),
    uploadPercentage: document.getElementById('rag-upload-percentage'),
    pendingFiles: document.getElementById('rag-pending-files'),
    pendingFilesList: document.getElementById('rag-pending-files-list'),
    processFilesBtn: document.getElementById('process-files-btn'),

    // 分块策略元素
    chunkStrategyRadios: document.querySelectorAll('input[name="chunk-strategy"]'),
    chunkSizeInput: document.getElementById('chunk-size'),
    chunkOverlapInput: document.getElementById('chunk-overlap'),

    // 检索设置元素
    modeSelect: document.getElementById('rag-mode'),
    useReRankerCheckbox: document.getElementById('use-re-ranker'),
    useContextCompressionCheckbox: document.getElementById('use-context-compression'),
    topKInput: document.getElementById('rag-top-k'),
    showSourcesCheckbox: document.getElementById('rag-show-sources'),

    // 问答相关元素
    questionInput: document.getElementById('rag-question-input'),
    sendQuestionBtn: document.getElementById('rag-send-question'),
    chatHistory: document.getElementById('rag-chat-history')
};

// 存储待处理的文件
let pendingFiles = [];

// 初始化RAG视图
export function initRagView() {
    // 绑定事件监听器
    bindEventListeners();
    // 初始加载集合列表
    loadCollections();
}

// 绑定所有事件监听器
function bindEventListeners() {
    // 集合相关事件
    if (elements.createCollectionBtn) {
        elements.createCollectionBtn.addEventListener('click', showCreateCollectionModal);
    }
    if (elements.confirmCreateCollection) {
        elements.confirmCreateCollection.addEventListener('click', createCollection);
    }
    if (elements.collectionSelect) {
        elements.collectionSelect.addEventListener('change', handleCollectionChange);
    }
    if (elements.deleteCollectionBtn) {
        elements.deleteCollectionBtn.addEventListener('click', deleteCollection);
    }

    // 关闭模态框事件
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', hideCreateCollectionModal);
    });

    // 文档相关事件
    if (elements.fileUpload) {
        elements.fileUpload.addEventListener('change', handleFileSelection);
    }
    if (elements.removeDocumentBtn) {
        elements.removeDocumentBtn.addEventListener('click', removeSelectedDocuments);
    }
    if (elements.processFilesBtn) {
        elements.processFilesBtn.addEventListener('click', processPendingFiles);
    }

    // 拖放上传事件
    if (elements.fileUploadArea) {
        elements.fileUploadArea.addEventListener('dragover', handleDragOver);
        elements.fileUploadArea.addEventListener('dragleave', handleDragLeave);
        elements.fileUploadArea.addEventListener('drop', handleDrop);
    }

    // 问答相关事件
    if (elements.sendQuestionBtn) {
        elements.sendQuestionBtn.addEventListener('click', handleSendQuestion);
    }
    if (elements.questionInput) {
        elements.questionInput.addEventListener('keypress', handleQuestionKeyPress);
    }

    // 标签切换事件
    setupTabNavigation();
}

// 设置标签导航
function setupTabNavigation() {
    const tabs = {
        document: document.getElementById('tab-document'),
        chunk: document.getElementById('tab-chunk'),
        retrieval: document.getElementById('tab-retrieval')
    };

    const panels = {
        document: document.getElementById('panel-document'),
        chunk: document.getElementById('panel-chunk'),
        retrieval: document.getElementById('panel-retrieval')
    };

    Object.keys(tabs).forEach(key => {
        if (tabs[key]) {
            tabs[key].addEventListener('click', () => {
                Object.values(tabs).forEach(tab => {
                    tab.classList.remove('text-primary', 'border-primary');
                    tab.classList.add('text-gray-500', 'border-transparent');
                });

                Object.values(panels).forEach(panel => {
                    panel.classList.add('hidden');
                });

                tabs[key].classList.add('text-primary', 'border-primary');
                tabs[key].classList.remove('text-gray-500', 'border-transparent');
                if (panels[key]) {
                    panels[key].classList.remove('hidden');
                }
            });
        }
    });
}

// 显示新建集合模态框
function showCreateCollectionModal() {
    if (elements.createCollectionModal) {
        elements.createCollectionModal.classList.remove('hidden');
        if (elements.newCollectionName) {
            elements.newCollectionName.focus();
        }
    }
}

// 隐藏新建集合模态框
function hideCreateCollectionModal() {
    if (elements.createCollectionModal) {
        elements.createCollectionModal.classList.add('hidden');
        if (elements.newCollectionName) elements.newCollectionName.value = '';
        if (elements.newCollectionDesc) elements.newCollectionDesc.value = '';
    }
}

// 加载所有集合
export async function loadCollections() {
    try {
        const collections = await apiRequest('/api/v1/rag/collections', {
            method: 'GET'
        });

        // 清空并填充集合选择框
        if (elements.collectionSelect) {
            elements.collectionSelect.innerHTML = '<option value="">选择文档集合</option>';
            collections.forEach(collection => {
                const option = document.createElement('option');
                option.value = collection.id; // 使用整数ID
                option.textContent = `${collection.name}（${collection.document_count}个文档）`;
                option.dataset.description = collection.description || '';
                elements.collectionSelect.appendChild(option);
            });
        }

        // 初始禁用删除按钮
        if (elements.deleteCollectionBtn) {
            elements.deleteCollectionBtn.disabled = true;
        }
    } catch (error) {
        showToast(`加载集合失败: ${error.message}`);
        console.error('加载集合失败:', error);
    }
}

// 处理集合选择变化
async function handleCollectionChange() {
    const collectionId = elements.collectionSelect?.value;

    // 重置状态
    if (elements.documentSelect) elements.documentSelect.innerHTML = '';
    if (elements.questionInput) elements.questionInput.disabled = !collectionId;
    if (elements.sendQuestionBtn) elements.sendQuestionBtn.disabled = !collectionId;
    if (elements.deleteCollectionBtn) elements.deleteCollectionBtn.disabled = !collectionId;
    resetPendingFiles();

    if (!collectionId) {
        // 未选择集合时的提示
        if (elements.chatHistory) {
            elements.chatHistory.innerHTML = `
                <div class="text-center text-gray-500 py-10">
                    <i class="fa fa-search text-4xl mb-3"></i>
                    <p>请先选择一个文档集合开始问答</p>
                </div>
            `;
        }
        if (elements.collectionInfo) elements.collectionInfo.classList.add('hidden');
        return;
    }

    // 加载选中集合的文档
    await loadCollectionDocuments(collectionId);

    // 更新集合信息
    const selectedOption = elements.collectionSelect?.options[elements.collectionSelect.selectedIndex];
    if (selectedOption && elements.currentCollectionName) {
        elements.currentCollectionName.textContent = selectedOption.textContent.split('（')[0];
    }
    if (selectedOption && elements.currentCollectionCount) {
        const countMatch = selectedOption.textContent.match(/（(\d+)个文档）/);
        elements.currentCollectionCount.textContent = countMatch ? countMatch[1] : '0';
    }
    if (elements.collectionInfo) elements.collectionInfo.classList.remove('hidden');

    // 更新聊天历史提示
    if (elements.chatHistory && selectedOption) {
        elements.chatHistory.innerHTML = `
            <div class="text-center text-gray-500 py-10">
                <i class="fa fa-comment text-4xl mb-3"></i>
                <p>已选择集合: ${selectedOption.textContent.split('（')[0]}</p>
                <p class="mt-2">请上传文档并处理后开始问答</p>
            </div>
        `;
    }
}

// 加载指定集合的文档
async function loadCollectionDocuments(collectionId) {
    if (!collectionId) return;

    try {
        const documents = await apiRequest(`/api/v1/rag/collections/${collectionId}/documents`, {
            method: 'GET'
        });

        // 填充文档选择框
        if (elements.documentSelect) {
            elements.documentSelect.innerHTML = '';
            documents.forEach(doc => {
                const option = document.createElement('option');
                option.value = doc.id;

                // 显示文档状态图标
                let statusIcon = '';
                switch(doc.status) {
                    case 'processed':
                        statusIcon = '<i class="fa fa-check text-green-500"></i>';
                        break;
                    case 'processing':
                        statusIcon = '<i class="fa fa-spinner fa-spin text-blue-500"></i>';
                        break;
                    case 'failed':
                        statusIcon = '<i class="fa fa-exclamation-triangle text-yellow-500"></i>';
                        break;
                    default:
                        statusIcon = '<i class="fa fa-clock-o text-gray-400"></i>';
                }

                const fileSize = formatFileSize(doc.file_size);
                option.innerHTML = `${statusIcon} ${doc.filename} (${fileSize})`;
                elements.documentSelect.appendChild(option);
            });
        }
    } catch (error) {
        showToast(`加载文档失败: ${error.message}`);
        console.error('加载文档失败:', error);
    }
}

// 创建新集合
async function createCollection() {
    if (!elements.newCollectionName) return;

    const name = elements.newCollectionName.value.trim();
    const description = elements.newCollectionDesc?.value.trim() || '';

    // 验证输入
    if (!name) {
        showToast('请输入集合名称');
        return;
    }

    if (name.length > 100) {
        showToast('集合名称不能超过100个字符');
        return;
    }

    try {
        // 显示加载状态
        if (elements.confirmCreateCollection) {
            elements.confirmCreateCollection.disabled = true;
            elements.confirmCreateCollection.innerHTML = '<i class="fa fa-spinner fa-spin mr-1"></i>创建中...';
        }

        // 发送创建请求（严格匹配后端API）
        await apiRequest('/api/v1/rag/collections', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                description: description
            })
        });

        showToast('集合创建成功');
        hideCreateCollectionModal();
        loadCollections();
    } catch (error) {
        showToast(`创建集合失败: ${error.message}`);
        console.error('创建集合失败:', error);
    } finally {
        // 恢复按钮状态
        if (elements.confirmCreateCollection) {
            elements.confirmCreateCollection.disabled = false;
            elements.confirmCreateCollection.innerHTML = '创建';
        }
    }
}

// 删除集合
async function deleteCollection() {
    const collectionId = elements.collectionSelect?.value;
    if (!collectionId) {
        showToast('请先选择要删除的集合');
        return;
    }

    const selectedOption = elements.collectionSelect?.options[elements.collectionSelect.selectedIndex];
    const collectionName = selectedOption ? selectedOption.textContent.split('（')[0] : '当前集合';

    if (!confirm(`确定要删除集合"${collectionName}"吗？此操作不可恢复！`)) {
        return;
    }

    try {
        // 禁用按钮并显示加载状态
        if (elements.deleteCollectionBtn) {
            elements.deleteCollectionBtn.disabled = true;
            elements.deleteCollectionBtn.innerHTML = '<i class="fa fa-spinner fa-spin mr-1"></i>删除中...';
        }

        // 调用删除API（使用整数ID）
        await apiRequest(`/api/v1/rag/collections/${collectionId}`, {
            method: 'DELETE'
        });

        showToast('集合已成功删除');
        loadCollections();
        handleCollectionChange(); // 重置界面状态
    } catch (error) {
        showToast(`删除集合失败: ${error.message}`);
        console.error('删除集合失败:', error);
    } finally {
        // 恢复按钮状态
        if (elements.deleteCollectionBtn) {
            elements.deleteCollectionBtn.disabled = false;
            elements.deleteCollectionBtn.innerHTML = '<i class="fa fa-trash mr-1"></i><span>删除集合</span>';
        }
    }
}

// 处理文件选择
function handleFileSelection() {
    const collectionId = elements.collectionSelect?.value;
    if (!collectionId) {
        showToast('请先选择一个文档集合');
        if (elements.fileUpload) elements.fileUpload.value = ''; // 清空选择
        return;
    }

    const files = elements.fileUpload?.files;
    if (!files || files.length === 0) return;

    // 添加到待处理文件列表
    Array.from(files).forEach(file => {
        // 检查是否已在待处理列表中
        const isDuplicate = pendingFiles.some(f =>
            f.name === file.name && f.size === file.size && f.lastModified === file.lastModified
        );

        if (!isDuplicate) {
            pendingFiles.push(file);
            addFileToPendingList(file);
        }
    });

    // 显示待处理文件区域
    if (elements.pendingFiles) elements.pendingFiles.classList.remove('hidden');

    // 清空文件选择
    if (elements.fileUpload) elements.fileUpload.value = '';
}

// 添加文件到待处理列表
function addFileToPendingList(file) {
    if (!elements.pendingFilesList) return;

    const fileSize = formatFileSize(file.size);
    const listItem = document.createElement('li');
    listItem.className = 'flex justify-between items-center p-1 border-b border-gray-100';
    listItem.innerHTML = `
        <span title="${file.name}">${truncateFileName(file.name)}</span>
        <div class="flex items-center gap-2">
            <span class="text-xs text-gray-500">${fileSize}</span>
            <button type="button" class="text-gray-400 hover:text-red-500" 
                    data-name="${file.name}" data-size="${file.size}" 
                    data-modified="${file.lastModified}">
                <i class="fa fa-times"></i>
            </button>
        </div>
    `;

    // 添加删除事件
    const deleteBtn = listItem.querySelector('button');
    deleteBtn?.addEventListener('click', function(e) {
        e.stopPropagation();
        const name = this.dataset.name;
        const size = parseInt(this.dataset.size);
        const modified = parseInt(this.dataset.modified);

        // 从数组中移除
        pendingFiles = pendingFiles.filter(f =>
            !(f.name === name && f.size === size && f.lastModified === modified)
        );

        // 从DOM中移除
        listItem.remove();

        // 如果没有待处理文件，隐藏区域
        if (pendingFiles.length === 0 && elements.pendingFiles) {
            elements.pendingFiles.classList.add('hidden');
        }
    });

    elements.pendingFilesList.appendChild(listItem);
}

// 处理待处理文件
async function processPendingFiles() {
    const collectionId = elements.collectionSelect?.value;
    if (!collectionId) {
        showToast('请先选择一个文档集合');
        return;
    }

    if (pendingFiles.length === 0) {
        showToast('没有待处理的文件');
        return;
    }

    // 禁用处理按钮
    if (elements.processFilesBtn) {
        elements.processFilesBtn.disabled = true;
        elements.processFilesBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i><span>处理中...</span>';
    }

    try {
        // 逐个处理文件
        for (let i = 0; i < pendingFiles.length; i++) {
            await uploadDocument(pendingFiles[i], collectionId);
        }

        showToast(`成功上传 ${pendingFiles.length} 个文件`);

        // 重置待处理文件
        resetPendingFiles();

        // 重新加载文档列表
        await loadCollectionDocuments(collectionId);
    } catch (error) {
        showToast(`文件处理失败: ${error.message}`);
        console.error('文件处理失败:', error);
    } finally {
        // 恢复按钮状态
        if (elements.processFilesBtn) {
            elements.processFilesBtn.disabled = false;
            elements.processFilesBtn.innerHTML = '<i class="fa fa-cogs"></i><span>处理选中文件</span>';
        }
    }
}

// 上传文档到集合
async function uploadDocument(file, collectionId) {
    try {
        // 显示进度条
        if (elements.uploadProgress) elements.uploadProgress.classList.remove('hidden');
        if (elements.uploadFilename) elements.uploadFilename.textContent = truncateFileName(file.name);
        if (elements.uploadBar) elements.uploadBar.style.width = '0%';
        if (elements.uploadPercentage) elements.uploadPercentage.textContent = '0%';

        // 创建FormData（匹配后端multipart/form-data要求）
        const formData = new FormData();
        formData.append('file', file);

        // 上传文件
        await apiRequest(
            `/api/v1/rag/collections/${collectionId}/documents`,
            {
                method: 'POST',
                body: formData,
                // 不设置Content-Type，让浏览器自动处理
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
                },
                onProgress: (progress) => {
                    const percent = Math.round((progress.loaded / progress.total) * 100);
                    if (elements.uploadBar) elements.uploadBar.style.width = `${percent}%`;
                    if (elements.uploadPercentage) elements.uploadPercentage.textContent = `${percent}%`;
                }
            }
        );
    } catch (error) {
        throw new Error(`文件 "${file.name}" 上传失败: ${error.message}`);
    } finally {
        // 隐藏进度条（最后一个文件处理完后）
        if (pendingFiles.indexOf(file) === pendingFiles.length - 1) {
            setTimeout(() => {
                if (elements.uploadProgress) elements.uploadProgress.classList.add('hidden');
            }, 500);
        }
    }
}

// 重置待处理文件
function resetPendingFiles() {
    pendingFiles = [];
    if (elements.pendingFilesList) elements.pendingFilesList.innerHTML = '';
    if (elements.pendingFiles) elements.pendingFiles.classList.add('hidden');
}

// 移除选中的文档
async function removeSelectedDocuments() {
    const collectionId = elements.collectionSelect?.value;
    const selectedOptions = elements.documentSelect ? Array.from(elements.documentSelect.selectedOptions) : [];

    if (!collectionId) {
        showToast('请先选择一个文档集合');
        return;
    }

    if (selectedOptions.length === 0) {
        showToast('请先选择要移除的文档');
        return;
    }

    if (!confirm(`确定要从集合中移除这 ${selectedOptions.length} 个文档吗？`)) {
        return;
    }

    try {
        // 禁用按钮并显示加载状态
        if (elements.removeDocumentBtn) {
            elements.removeDocumentBtn.disabled = true;
            elements.removeDocumentBtn.innerHTML = '<i class="fa fa-spinner fa-spin mr-1"></i>移除中...';
        }

        // 逐个删除文档
        for (const option of selectedOptions) {
            const documentId = option.value;
            await apiRequest(
                `/api/v1/rag/collections/${collectionId}/documents/${documentId}`,
                { method: 'DELETE' }
            );
        }

        showToast('文档已成功移除');
        await loadCollectionDocuments(collectionId);
    } catch (error) {
        showToast(`移除文档失败: ${error.message}`);
        console.error('移除文档失败:', error);
    } finally {
        // 恢复按钮状态
        if (elements.removeDocumentBtn) {
            elements.removeDocumentBtn.disabled = false;
            elements.removeDocumentBtn.innerHTML = '<i class="fa fa-trash-o mr-1"></i><span>从集合移除</span>';
        }
    }
}

// 处理发送问题
async function handleSendQuestion() {
    const question = elements.questionInput?.value.trim();
    const collectionId = elements.collectionSelect?.value;

    if (!question || !collectionId) return;

    // 清空输入框
    if (elements.questionInput) elements.questionInput.value = '';

    // 添加用户问题到聊天历史
    addMessageToHistory('user', question);

    try {
        // 获取检索参数
        const mode = elements.modeSelect?.value || 'hybrid';
        const topK = elements.topKInput?.value || 5;

        // 显示加载状态
        addMessageToHistory('system', '正在检索相关信息并生成回答...', true);

        // 发送查询请求（匹配后端API）
        const response = await apiRequest(
            `/api/v1/rag/collections/${collectionId}/query`,
            {
                method: 'POST',
                body: JSON.stringify({
                    query: question,
                    top_k: parseInt(topK),
                    mode: mode
                })
            }
        );

        // 移除加载状态
        if (elements.chatHistory && elements.chatHistory.lastChild) {
            elements.chatHistory.removeChild(elements.chatHistory.lastChild);
        }

        // 添加回答到聊天历史
        addMessageToHistory('assistant', response.answer);

        // 如果需要显示来源
        if (elements.showSourcesCheckbox?.checked && response.sources && response.sources.length > 0) {
            addSourcesToHistory(response.sources);
        }
    } catch (error) {
        // 移除加载状态
        if (elements.chatHistory && elements.chatHistory.lastChild) {
            elements.chatHistory.removeChild(elements.chatHistory.lastChild);
        }

        console.error('查询失败:', error);
        addMessageToHistory('assistant', `查询失败: ${error.message}`, false, true);
    }
}

// 处理问题输入框的按键事件
function handleQuestionKeyPress(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        handleSendQuestion();
    }
}

// 拖放上传处理函数
function handleDragOver(e) {
    e.preventDefault();
    if (elements.fileUploadArea) elements.fileUploadArea.classList.add('border-primary');
}

function handleDragLeave() {
    if (elements.fileUploadArea) elements.fileUploadArea.classList.remove('border-primary');
}

function handleDrop(e) {
    e.preventDefault();
    if (elements.fileUploadArea) elements.fileUploadArea.classList.remove('border-primary');

    if (e.dataTransfer.files.length && elements.fileUpload) {
        elements.fileUpload.files = e.dataTransfer.files;
        handleFileSelection();
    }
}

// 添加消息到历史记录
function addMessageToHistory(role, content, isLoading = false, isError = false) {
    if (!elements.chatHistory) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `flex ${role === 'user' ? 'justify-end' : 'justify-start'} mb-4`;

    let avatar, bubbleClass;

    if (role === 'user') {
        avatar = '<i class="fa fa-user"></i>';
        bubbleClass = 'bg-primary text-white';
    } else if (role === 'assistant') {
        avatar = '<i class="fa fa-robot"></i>';
        bubbleClass = 'bg-gray-100 text-gray-800';
        if (isError) bubbleClass = 'bg-red-50 text-red-700';
    } else { // system
        avatar = '<i class="fa fa-cog"></i>';
        bubbleClass = 'bg-blue-50 text-blue-700';
    }

    let contentHtml = content;
    if (isLoading) {
        contentHtml = '<div class="flex space-x-2"><div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div><div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div><div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.4s"></div></div>';
    } else {
        // 简单的Markdown转换
        contentHtml = content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
    }

    messageDiv.innerHTML = `
        <div class="flex items-start gap-3">
            <div class="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-gray-600">
                ${avatar}
            </div>
            <div class="max-w-[80%] p-3 rounded-lg ${bubbleClass}">
                ${contentHtml}
            </div>
        </div>
    `;

    elements.chatHistory.appendChild(messageDiv);
    scrollToBottom();
}

// 添加来源到历史记录
function addSourcesToHistory(sources) {
    if (!elements.chatHistory) return;

    const sourcesDiv = document.createElement('div');
    sourcesDiv.className = 'bg-gray-50 p-4 rounded-lg text-sm mb-4';

    let sourcesHtml = '<p class="font-medium text-gray-700 mb-2">参考来源:</p><ul class="space-y-2">';

    sources.forEach((source, index) => {
        sourcesHtml += `
            <li class="flex items-start gap-2">
                <span class="text-gray-500">#${index + 1}</span>
                <div>
                    <p class="font-medium">${source.filename || '未知文档'}</p>
                    <p class="text-gray-600 mt-1 line-clamp-2">${source.content || '无内容预览'}</p>
                    ${source.score ? `<p class="text-xs text-gray-400 mt-1">相关度: ${(source.score * 100).toFixed(1)}%</p>` : ''}
                </div>
            </li>
        `;
    });

    sourcesHtml += '</ul>';
    sourcesDiv.innerHTML = sourcesHtml;

    elements.chatHistory.appendChild(sourcesDiv);
    scrollToBottom();
}

// 滚动到聊天底部
function scrollToBottom() {
    if (elements.chatHistory) {
        elements.chatHistory.scrollTop = elements.chatHistory.scrollHeight;
    }
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// 截断长文件名
function truncateFileName(name, maxLength = 20) {
    if (name.length <= maxLength) return name;
    return name.substring(0, maxLength - 3) + '...';
}

// 显示提示消息
function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'fixed bottom-4 right-4 bg-gray-800 text-white px-4 py-2 rounded shadow-lg z-50 transition-all duration-300';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-4');
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}
