from fastapi.testclient import TestClient

from app.api import routes_agents
from app.main import app
from app.schemas.agents import AgentRunResponse, ToolCallRecord

client = TestClient(app)


def test_agents_run_endpoint(monkeypatch) -> None:
    def fake_run_business_agent(request: str) -> AgentRunResponse:
        assert request == "Calculate a quote."

        return AgentRunResponse(
            selected_agent="finance",
            routing_reason="pytest finance route",
            final_response="The total is $4500.",
            tool_calls=[
                ToolCallRecord(
                    name="calculate_quote",
                    arguments={
                        "subtotal": 5000,
                        "discount_percent": 10,
                    },
                )
            ],
        )

    monkeypatch.setattr(
        routes_agents,
        "run_business_agent",
        fake_run_business_agent,
    )

    response = client.post(
        "/api/v1/agents/run",
        json={
            "request": "Calculate a quote.",
        },
        headers={
            "X-Request-ID": "pytest-agent-api-001",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["selected_agent"] == "finance"
    assert data["routing_reason"] == "pytest finance route"
    assert data["final_response"] == "The total is $4500."
    assert data["tool_calls"][0]["name"] == "calculate_quote"

    assert response.headers["x-request-id"] == "pytest-agent-api-001"


def test_agents_run_rejects_empty_request() -> None:
    response = client.post(
        "/api/v1/agents/run",
        json={
            "request": "",
        },
    )

    assert response.status_code == 422
