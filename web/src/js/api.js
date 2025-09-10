import { state, API_BASE_URL } from './state.js';

export const HEALTH_API_BASE = `${API_BASE_URL}/api/v1/health`;

export async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const defaultOptions = {
        headers: {
            'Authorization': `Bearer ${state.token || ''}`,
            'Content-Type': 'application/json',
            ...options.headers
        }
    };

    // 处理FormData情况（文件上传）
    const isFormData = options.body instanceof FormData;
    if (isFormData) {
        // 删除Content-Type，让浏览器自动设置multipart/form-data
        delete defaultOptions.headers['Content-Type'];
    }

    try {
        const response = await fetch(url, { ...defaultOptions, ...options });
        const responseText = await response.text();

        // 尝试解析响应内容
        let responseData;
        try {
            responseData = responseText ? JSON.parse(responseText) : {};
        } catch (e) {
            responseData = { text: responseText };
        }

        if (!response.ok) {
            // 构建错误信息
            let errorMessage = `请求失败 (${response.status})`;

            // 处理422验证错误（FastAPI风格）
            if (response.status === 422 && responseData.detail) {
                if (Array.isArray(responseData.detail)) {
                    // 提取字段验证错误
                    errorMessage = responseData.detail.map(item => {
                        const field = item.loc ? item.loc.join('.') : '未知字段';
                        return `${field}: ${item.msg}`;
                    }).join('; ');
                } else {
                    errorMessage = responseData.detail;
                }
            }
            // 处理其他错误
            else if (typeof responseData === 'object' && (responseData.message || responseData.error)) {
                errorMessage = responseData.message || responseData.error;
            }
            // 非JSON响应
            else if (responseData.text) {
                errorMessage = responseData.text;
            }

            throw new Error(errorMessage);
        }

        return responseData;
    } catch (error) {
        console.error('API请求错误:', error);
        throw error;
    }
}
