import os

os.environ["DATABASE_URL"] = "sqlite:///./test_cloud_optimizer.sqlite3"

from fastapi.testclient import TestClient

from app.database import init_db
from app.main import app


init_db()
client = TestClient(app)


def test_login_page_loads():
    response = client.get("/login")
    assert response.status_code == 200
    assert "AI Cloud Optimizer" in response.text


def test_summary_api_loads():
    response = client.get("/api/summary")
    assert response.status_code == 200
    assert "resources" in response.json()
