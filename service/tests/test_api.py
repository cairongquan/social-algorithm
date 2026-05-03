"""后端基础 API 冒烟测试。"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_read_example():
    response = client.get("/api/v1/endpoints/example")
    assert response.status_code == 200
    assert "message" in response.json()
