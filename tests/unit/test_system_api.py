from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "AI Multi-Agent Business Automation"


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"
    assert data["service"] == "AI Multi-Agent Business Automation"
    assert data["environment"] == "development"


def test_system_info_endpoint() -> None:
    response = client.get("/api/v1/system/info")

    assert response.status_code == 200

    data = response.json()

    assert data["llm_provider"] == "ollama"
    assert data["llm_model"] == "llama3.2"
    assert data["human_approval_enabled"] is True
