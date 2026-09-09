from typing import Any

from app.tools import n8n_tools
from app.tools.n8n_tools import trigger_n8n_workflow


class FakeResponse:
    status_code = 200

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return {
            "success": True,
            "workflow": "business_operations",
            "status": "processed",
            "action": "create_operations_followup",
            "request_id": "pytest-n8n-001",
            "side_effect_performed": False,
            "message": "Workflow request processed successfully.",
        }


def test_trigger_n8n_workflow(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    def fake_post(
        url: str,
        json: dict[str, Any],
        timeout: float,
    ) -> FakeResponse:
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(
        n8n_tools.httpx,
        "post",
        fake_post,
    )

    result = trigger_n8n_workflow.invoke(
        {
            "action": "create_operations_followup",
            "request_id": "pytest-n8n-001",
            "payload": {
                "title": "Review delayed shipment",
            },
        }
    )

    assert result["success"] is True
    assert result["request_id"] == "pytest-n8n-001"

    workflow_response = result["workflow_response"]

    assert workflow_response["status"] == "processed"
    assert workflow_response["side_effect_performed"] is False

    assert captured["json"]["action"] == "create_operations_followup"
    assert captured["json"]["request_id"] == "pytest-n8n-001"
    assert captured["timeout"] == 10.0


def test_trigger_n8n_workflow_rejects_empty_action() -> None:
    result = trigger_n8n_workflow.invoke(
        {
            "action": "   ",
            "payload": {},
        }
    )

    assert result["success"] is False
    assert result["message"] == "Workflow action cannot be empty."
