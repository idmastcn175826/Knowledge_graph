# tests/test_file.py
import os
import tempfile

# from app.main import app
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

# 全局变量：登录后的Token（用于鉴权）
ACCESS_TOKEN = ""

# 测试前先登录
def test_login_before_file():
    global ACCESS_TOKEN
    response = client.post(
        "/api/v1/user/login",
        data={"username": "test_user", "password": "Test123456"}
    )
    ACCESS_TOKEN = response.json()["access_token"]
    assert ACCESS_TOKEN != ""

# 测试文件上传
def test_upload_file():
    # 创建临时测试文件（PDF格式）
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        temp_file.write(b"Test PDF content")  # 写入测试内容
        temp_file_path = temp_file.name

    try:
        # 读取临时文件并上传
        with open(temp_file_path, "rb") as f:
            response = client.post(
                "/api/v1/file/upload",
                files={"file": ("test_upload.pdf", f, "application/pdf")},
                headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
            )
        assert response.status_code == 200
        data = response.json()
        assert "file_id" in data  # 确保返回文件ID
        assert data["filename"] == "test_upload.pdf"
    finally:
        # 删除临时文件
        os.unlink(temp_file_path)

# 测试文件列表
def test_get_file_list():
    response = client.get(
        "/api/v1/file/list?page=1&page_size=20",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data  # 列表数据
    assert "total" in data  # 总数