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


def test_remote_resource_can_register_and_send_metric():
    register_response = client.post(
        "/api/resources/register",
        data={
            "name": "test-remote-server",
            "provider": "AWS",
            "resource_type": "EC2 Application Server",
            "instance_size": "t3.micro",
            "region": "eu-west-2",
            "hourly_cost": 0.02,
        },
    )
    assert register_response.status_code == 200
    resource_id = register_response.json()["resource_id"]

    metric_response = client.post(
        "/api/metrics",
        data={
            "resource_id": resource_id,
            "cpu_percent": 25,
            "memory_percent": 55,
            "disk_percent": 40,
            "network_in_mb": 1.2,
            "network_out_mb": 0.8,
            "response_time_ms": 120,
        },
    )

    assert metric_response.status_code == 200
    assert metric_response.json()["status"] == "stored"
