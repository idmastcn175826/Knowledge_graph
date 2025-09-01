# tests/test_user.py
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app # 导入FastAPI应用
from app.db.init_db import init_db
from app.crud.crud_user import create_user
from app.models.schema import UserCreate

# 测试客户端
client = TestClient(app)

# 测试前初始化数据库（使用测试数据库，需在配置中区分测试环境）
def test_init_db():
    init_db()  # 实际测试应使用测试数据库，避免影响生产数据

# 测试用户注册
def test_create_user():
    response = client.post(
        "/api/v1/user/register",
        json={
            "username": "test_user",
            "email": "test@example.com",
            "password": "Test123456"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "test_user"
    assert "id" in data

# 测试用户登录
def test_user_login():
    response = client.post(
        "/api/v1/user/login",
        data={
            "username": "test_user",
            "password": "Test123456"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data  # 确保返回Token
    assert data["token_type"] == "bearer"