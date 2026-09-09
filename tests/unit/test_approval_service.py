from sqlalchemy import select

from app.database.models import Approval
from app.services import approval_service
from app.services.approval_service import execute_approved_action
from app.tools import request_human_approval


class FakeResponse:
    status_code = 200

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return {
            "success": True,
            "workflow": "business_operations",
            "status": "processed",
            "side_effect_performed": False,
        }


def test_pending_approval_cannot_execute() -> None:
    result = request_human_approval.invoke(
        {
            "action": "trigger_n8n_workflow",
            "payload": {
                "action": "pytest_sensitive_action",
                "payload": {},
            },
        }
    )

    approval_id = result["approval"]["id"]

    execution = execute_approved_action(approval_id)

    assert execution["success"] is False
    assert execution["status"] == "pending"
    assert execution["message"] == ("Action is blocked until human approval is granted.")


def test_approved_action_executes_exactly_once(
    db_session,
    monkeypatch,
) -> None:
    approval = Approval(
        action="trigger_n8n_workflow",
        payload={
            "action": "pytest_approved_action",
            "request_id": "pytest-approval-001",
            "payload": {},
        },
        status="approved",
    )

    db_session.add(approval)
    db_session.commit()
    db_session.refresh(approval)

    def fake_post(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        approval_service.httpx,
        "post",
        fake_post,
    )

    first_execution = execute_approved_action(approval.id)

    assert first_execution["success"] is True
    assert first_execution["status"] == "executed"

    db_session.expire_all()

    stored_approval = db_session.scalar(select(Approval).where(Approval.id == approval.id))

    assert stored_approval is not None
    assert stored_approval.status == "executed"

    second_execution = execute_approved_action(approval.id)

    assert second_execution["success"] is False
    assert second_execution["status"] == "executed"
    assert second_execution["message"] == ("Approved action has already been executed.")
