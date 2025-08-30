from fastapi.testclient import TestClient
import time
from main import app
from app.core.config import settings

client = TestClient(app)
ACCESS_TOKEN = ""
TEST_TASK_ID = ""  # 用于存储测试任务ID


# 测试前登录获取令牌
def test_login_before_kg():
    global ACCESS_TOKEN
    response = client.post(
        "/api/v1/user/login",
        data={"username": "test_user", "password": "Test123456"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    ACCESS_TOKEN = data["access_token"]


# 测试创建知识图谱任务
def test_create_kg():
    global TEST_TASK_ID
    # 假设已上传测试文件，获取文件ID（实际测试可先调用文件上传接口）
    test_file_id = "2ced6397-ef30-473d-b000-aba115fa729a"  # 替换为实际测试文件ID

    response = client.post(
        "/api/v1/kg/create",
        json={
            "file_ids": [test_file_id],
            "kg_name": "测试知识图谱",
            "algorithms": {
                "preprocess": "simhash",
                "entity_extraction": "qwen",
                "relation_extraction": "qwen",
                "knowledge_completion": "transe"
            },
            "model_api_key": None,  # 可根据测试需求填写实际API密钥
            "enable_completion": True,
            "enable_visualization": True
        },
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert len(data["task_id"]) == 36  # UUID长度验证
    TEST_TASK_ID = data["task_id"]


# 测试查询知识图谱任务进度
def test_kg_progress():
    # 等待任务开始处理（根据实际情况调整等待时间）
    time.sleep(5)

    response = client.get(
        f"/api/v1/kg/progress/{TEST_TASK_ID}",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == TEST_TASK_ID
    assert "progress" in data
    assert "status" in data
    assert "stage" in data
    assert 0 <= data["progress"] <= 100


# 测试获取知识图谱列表
def test_kg_list():
    response = client.get(
        "/api/v1/kg/list?page=1&page_size=10",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)
    assert isinstance(data["total"], int)


# 测试知识图谱查询功能（需在任务完成后执行）
def test_kg_query():
    # 等待任务完成（实际测试可能需要更长时间）
    time.sleep(60)

    # 查询测试创建的知识图谱中的实体
    response = client.post(
        "/api/v1/kg/query",
        json={"entity": "百度"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert isinstance(data["nodes"], list)
    assert isinstance(data["edges"], list)
