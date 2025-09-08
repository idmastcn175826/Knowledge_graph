// health.js
import { state, API_BASE_URL } from './state.js';  // 从state.js导入
export const HEALTH_API_BASE = `${API_BASE_URL}/api/v1/health`;

export function initHealthMonitoring() {
    console.log('初始化健康监测...');
    fetchHealthData();
    fetchEmergencyContacts();
    setInterval(fetchHealthData, 30000);
    initHealthChart();
    setTimeout(simulateHealthDevice, 2000);
    setInterval(simulateHealthDevice, 60000);
}

export async function fetchHealthData() {
    try {
        const response = await fetch(`${HEALTH_API_BASE}/health-data?limit=10`, {
            headers: {
                'Authorization': `Bearer ${state.token}`
            }
        });

        if (response.ok) {
            const healthData = await response.json();
            state.healthData = healthData;

            if (healthData.length > 0) {
                state.latestHealthData = healthData[healthData.length - 1];
                updateHealthDashboard(state.latestHealthData);
                analyzeHealthData(state.latestHealthData);
            } else {
                const mockData = generateMockHealthData();
                updateHealthDashboard(mockData);
            }

            updateHealthChart();
        } else {
            console.warn('获取健康数据失败，使用模拟数据');
            const mockData = generateMockHealthData();
            updateHealthDashboard(mockData);
            updateHealthChart();
        }
    } catch (error) {
        console.error('获取健康数据失败:', error);
        const mockData = generateMockHealthData();
        updateHealthDashboard(mockData);
        updateHealthChart();
    }
}

export async function fetchEmergencyContacts() {
    try {
        const response = await fetch(`${HEALTH_API_BASE}/emergency-contacts`, {
            headers: {
                'Authorization': `Bearer ${state.token}`
            }
        });

        if (response.ok) {
            const contacts = await response.json();
            state.emergencyContacts = contacts;
            document.getElementById('emergency-contacts-count').textContent = contacts.length;
            updateEmergencyContactsList(contacts);
        } else {
            console.warn('获取紧急联系人失败，使用模拟数据');
            generateMockEmergencyContacts();
        }
    } catch (error) {
        console.error('获取紧急联系人失败:', error);
        generateMockEmergencyContacts();
    }
}

export async function uploadHealthData(healthData) {
    try {
        const response = await fetch(`${HEALTH_API_BASE}/health-data`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify(healthData)
        });

        if (response.ok) {
            const result = await response.json();
            console.log('健康数据上传成功:', result);
            fetchHealthData();
            return result;
        } else {
            throw new Error('健康数据上传失败');
        }
    } catch (error) {
        console.error('上传健康数据失败:', error);
        return null;
    }
}

export async function triggerEmergency() {
    if (confirm('确定要触发紧急求助吗？')) {
        try {
            const emergencyData = {
                risk_level: 'critical',
                type: 'manual',
                description: '用户手动触发紧急求助',
                health_data_id: state.latestHealthData?.id || null
            };

            const response = await fetch(`${HEALTH_API_BASE}/emergency`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${state.token}`
                },
                body: JSON.stringify(emergencyData)
            });

            if (response.ok) {
                const result = await response.json();
                alert('已触发紧急求助，帮助正在路上！');
                console.log('紧急事件触发成功:', result);
            } else {
                throw new Error('求助请求失败');
            }
        } catch (error) {
            console.error('触发紧急求助失败:', error);
            alert('触发紧急求助失败，请检查网络连接');
        }
    }
}

export async function saveEmergencyContact() {
    const name = document.getElementById('contact-name').value;
    const relationship = document.getElementById('contact-relationship').value;
    const phone = document.getElementById('contact-phone').value;
    const email = document.getElementById('contact-email').value;
    const priority = document.getElementById('contact-priority').value;

    if (!name || !relationship || !phone) {
        alert('请填写必填字段（姓名、关系、电话）');
        return;
    }

    try {
        const contactData = {
            name,
            contact_relationship: relationship,
            phone_number: phone,
            email: email || '',
            priority: parseInt(priority) || 1
        };

        const response = await fetch(`${HEALTH_API_BASE}/emergency-contacts`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify(contactData)
        });

        if (response.ok) {
            const result = await response.json();
            alert('联系人保存成功！');
            document.getElementById('emergency-contacts-modal').classList.add('hidden');
            fetchEmergencyContacts();
            console.log('联系人保存成功:', result);
        } else {
            throw new Error('保存联系人失败');
        }
    } catch (error) {
        console.error('保存紧急联系人失败:', error);
        alert('保存失败: ' + error.message);
    }
}

export function simulateHealthDevice() {
    const mockData = {
        device_id: 'simulated_watch_001',
        device_type: 'smart_watch',
        heart_rate: Math.floor(60 + Math.random() * 40),
        blood_oxygen: Math.floor(95 + Math.random() * 5),
        systolic_bp: Math.floor(110 + Math.random() * 30),
        diastolic_bp: Math.floor(70 + Math.random() * 20),
        blood_glucose: (5.0 + (Math.random() * 3)).toFixed(1),
        temperature: (36.5 + (Math.random() * 1.5)).toFixed(1),
        respiratory_rate: Math.floor(12 + Math.random() * 8),
        steps: Math.floor(Math.random() * 1000),
        calories: Math.floor(Math.random() * 500),
        distance: (Math.random() * 5).toFixed(2),
        latitude: 39.9042 + (Math.random() * 0.1 - 0.05),
        longitude: 116.4074 + (Math.random() * 0.1 - 0.05),
        altitude: 50 + Math.random() * 100,
        environment_temp: 20 + Math.random() * 15,
        environment_humidity: 30 + Math.random() * 50,
        timestamp: new Date().toISOString()
    };

    uploadHealthData(mockData);
}

export function updateHealthDashboard(data) {
    if (data.heart_rate !== undefined && data.heart_rate !== null) {
        document.getElementById('current-heart-rate').textContent = data.heart_rate;
        document.getElementById('heart-rate-time').textContent = new Date().toLocaleTimeString();
    }

    if (data.blood_oxygen !== undefined && data.blood_oxygen !== null) {
        document.getElementById('current-blood-oxygen').textContent = data.blood_oxygen + '%';
        document.getElementById('blood-oxygen-time').textContent = new Date().toLocaleTimeString();
    }

    if (data.systolic_bp !== undefined && data.diastolic_bp !== undefined) {
        document.getElementById('current-blood-pressure').textContent =
            `${data.systolic_bp}/${data.diastolic_bp}`;
        document.getElementById('blood-pressure-time').textContent = new Date().toLocaleTimeString();
    }
}

// 初始化健康图表
export function initHealthChart() {
    console.log('初始化健康图表...');

    // 这里可以初始化图表，如果没有图表库，可以显示简单的数据
    const chartContainer = document.getElementById('health-chart-container');
    if (chartContainer) {
        chartContainer.innerHTML = `
            <div class="text-center text-gray-500 py-8">
                <i class="fa fa-line-chart text-3xl mb-3"></i>
                <p>健康数据图表</p>
                <p class="text-sm mt-1">实时健康监测数据显示区</p>
            </div>
        `;
    }
}

export function updateHealthStatus(latestData) {
    console.log('更新健康状态:', latestData);
}


//健康设备管理数据返回接口函数
export function generateMockHealthData() {
    console.log('生成模拟健康数据');

    // 返回模拟的健康数据对象
    return {
        device_id: 'simulated_watch_001',
        device_type: 'smart_watch',
        heart_rate: Math.floor(60 + Math.random() * 40), // 60-100 的心率
        blood_oxygen: Math.floor(95 + Math.random() * 5), // 95-100% 的血氧
        systolic_bp: Math.floor(110 + Math.random() * 30), // 110-140 收缩压
        diastolic_bp: Math.floor(70 + Math.random() * 20), // 70-90 舒张压
        blood_glucose: (4.0 + (Math.random() * 3)).toFixed(1), // 4.0-7.0 血糖
        temperature: (36.2 + (Math.random() * 1.3)).toFixed(1), // 36.2-37.5 体温
        respiratory_rate: Math.floor(12 + Math.random() * 8), // 12-20 呼吸频率
        steps: Math.floor(Math.random() * 5000), // 0-5000 步数
        calories: Math.floor(Math.random() * 800), // 0-800 卡路里
        distance: (Math.random() * 8).toFixed(2), // 0-8 km 距离
        timestamp: new Date().toISOString()
    };
}
// 生成模拟紧急联系人
export function generateMockEmergencyContacts() {
    console.log('生成模拟紧急联系人');

    // 返回模拟的紧急联系人数据
    const mockContacts = [
        {
            id: 1,
            name: '张医生',
            contact_relationship: '家庭医生',
            phone_number: '13800138000',
            email: 'doctor@example.com',
            priority: 1
        },
        {
            id: 2,
            name: '李家人',
            contact_relationship: '家人',
            phone_number: '13900139000',
            email: 'family@example.com',
            priority: 2
        }
    ];

    // 更新UI显示
    document.getElementById('emergency-contacts-count').textContent = mockContacts.length;
    updateEmergencyContactsList(mockContacts);

    return mockContacts;
}
export function setupEmergencyButton() {
    console.log('设置紧急按钮');
}

export function initEmergencyContactsModal() {
    console.log('初始化紧急联系人模态框');
}

// 更新紧急联系人列表
export function updateEmergencyContactsList(contacts) {
    console.log('更新紧急联系人列表:', contacts);

    const container = document.getElementById('emergency-contacts-list');
    if (!container) return;

    if (!contacts || contacts.length === 0) {
        container.innerHTML = `
            <div class="text-center text-gray-500 py-4">
                <i class="fa fa-users text-2xl mb-2"></i>
                <p>暂无紧急联系人</p>
                <p class="text-sm mt-1">点击"管理联系人"添加</p>
            </div>
        `;
        return;
    }

    let html = '';
    contacts.forEach(contact => {
        html += `
            <div class="bg-gray-50 p-3 rounded-lg border border-gray-100">
                <div class="flex items-center justify-between">
                    <div>
                        <div class="font-medium">${contact.name}</div>
                        <div class="text-sm text-gray-500">${contact.contact_relationship}</div>
                    </div>
                    <div class="text-right">
                        <div class="text-sm">${contact.phone_number}</div>
                        ${contact.email ? `<div class="text-xs text-gray-400">${contact.email}</div>` : ''}
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// 分析健康数据
export function analyzeHealthData(data) {
    console.log('分析健康数据:', data);

    if (!data) return;

    // 简单的健康数据分析
    let status = '良好';
    let message = '您的健康状况良好';

    if (data.heart_rate < 60 || data.heart_rate > 100) {
        status = '注意';
        message = '心率异常，请注意休息';
    }

    if (data.blood_oxygen < 95) {
        status = '警告';
        message = '血氧饱和度较低，请及时就医';
    }

    if (data.systolic_bp > 140 || data.diastolic_bp > 90) {
        status = '注意';
        message = '血压偏高，请注意监测';
    }

    // 更新健康状态显示
    const statusElement = document.getElementById('health-status');
    const messageElement = document.getElementById('health-message');

    if (statusElement && messageElement) {
        statusElement.textContent = `健康状态: ${status}`;
        messageElement.textContent = message;

        // 根据状态设置颜色
        if (status === '良好') {
            statusElement.className = 'text-success';
        } else if (status === '注意') {
            statusElement.className = 'text-warning';
        } else {
            statusElement.className = 'text-danger';
        }
    }
}

// 修改 health.js 中的 updateHealthChart 函数
export function updateHealthChart() {
    console.log('更新健康图表...');

    // 如果没有图表库，可以更新数字显示
    if (state.latestHealthData) {
        const statsElement = document.getElementById('health-stats');
        if (statsElement) {
            statsElement.innerHTML = `
                <div class="grid grid-cols-2 gap-4">
                    <div class="text-center">
                        <div class="text-2xl font-bold">${state.latestHealthData.heart_rate || '--'}</div>
                        <div class="text-sm text-gray-500">心率</div>
                    </div>
                    <div class="text-center">
                        <div class="text-2xl font-bold">${state.latestHealthData.blood_oxygen || '--'}%</div>
                        <div class="text-sm text-gray-500">血氧</div>
                    </div>
                </div>
            `;
        }
    }
}