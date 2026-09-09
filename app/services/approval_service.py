from typing import Any

import httpx

from app.config import get_settings
from app.core.logging import get_logger
from app.database.database import SessionLocal
from app.database.models import Approval

logger = get_logger(__name__)


def execute_approved_action(approval_id: int) -> dict[str, Any]:
    """Execute an approved sensitive action exactly once."""
    settings = get_settings()

    logger.info(
        "approval_execution_requested",
        approval_id=approval_id,
    )

    with SessionLocal() as db:
        approval = db.get(Approval, approval_id)

        if approval is None:
            logger.warning(
                "approval_not_found",
                approval_id=approval_id,
            )

            return {
                "success": False,
                "approval_id": approval_id,
                "message": "Approval request not found.",
            }

        if approval.status == "pending":
            logger.warning(
                "approval_execution_blocked",
                approval_id=approval.id,
                approval_status=approval.status,
                reason="human_approval_required",
            )

            return {
                "success": False,
                "approval_id": approval.id,
                "status": approval.status,
                "message": "Action is blocked until human approval is granted.",
            }

        if approval.status == "executed":
            logger.warning(
                "approval_execution_blocked",
                approval_id=approval.id,
                approval_status=approval.status,
                reason="already_executed",
            )

            return {
                "success": False,
                "approval_id": approval.id,
                "status": approval.status,
                "message": "Approved action has already been executed.",
            }

        if approval.status != "approved":
            logger.warning(
                "approval_execution_blocked",
                approval_id=approval.id,
                approval_status=approval.status,
                reason="status_not_executable",
            )

            return {
                "success": False,
                "approval_id": approval.id,
                "status": approval.status,
                "message": "Approval status does not allow execution.",
            }

        if approval.action != "trigger_n8n_workflow":
            logger.warning(
                "approval_execution_blocked",
                approval_id=approval.id,
                approval_action=approval.action,
                reason="unsupported_action",
            )

            return {
                "success": False,
                "approval_id": approval.id,
                "status": approval.status,
                "message": f"Unsupported approved action: {approval.action}",
            }

        payload = approval.payload or {}

        workflow_action = payload.get("action")
        workflow_payload = payload.get("payload", {})
        request_id = payload.get("request_id")

        if not workflow_action:
            logger.warning(
                "approval_execution_blocked",
                approval_id=approval.id,
                reason="missing_workflow_action",
            )

            return {
                "success": False,
                "approval_id": approval.id,
                "message": "Approved workflow action is missing.",
            }

        request_body = {
            "action": workflow_action,
            "request_id": request_id or f"approval-{approval.id}",
            "payload": workflow_payload,
        }

        logger.info(
            "approved_action_execution_started",
            approval_id=approval.id,
            approval_action=approval.action,
            workflow_action=workflow_action,
        )

        try:
            response = httpx.post(
                settings.n8n_webhook_url,
                json=request_body,
                timeout=10.0,
            )
            response.raise_for_status()
        except httpx.RequestError as exc:
            logger.exception(
                "approved_action_execution_failed",
                approval_id=approval.id,
                error_type=type(exc).__name__,
            )

            return {
                "success": False,
                "approval_id": approval.id,
                "message": "n8n workflow service is unavailable.",
                "error_type": type(exc).__name__,
            }
        except httpx.HTTPStatusError:
            logger.error(
                "approved_action_execution_failed",
                approval_id=approval.id,
                status_code=response.status_code,
            )

            return {
                "success": False,
                "approval_id": approval.id,
                "message": "n8n workflow returned an error.",
                "status_code": response.status_code,
            }

        try:
            workflow_response = response.json()
        except ValueError:
            logger.error(
                "approved_action_execution_failed",
                approval_id=approval.id,
                reason="invalid_json_response",
            )

            return {
                "success": False,
                "approval_id": approval.id,
                "message": "n8n returned an invalid JSON response.",
            }

        approval.status = "executed"
        db.commit()
        db.refresh(approval)

        logger.info(
            "approved_action_executed",
            approval_id=approval.id,
            approval_status=approval.status,
            workflow_action=workflow_action,
        )

        return {
            "success": True,
            "approval_id": approval.id,
            "status": approval.status,
            "workflow_response": workflow_response,
        }
