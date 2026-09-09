from typing import Any
from uuid import uuid4

import httpx
from langchain.tools import tool

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@tool
def trigger_n8n_workflow(
    action: str,
    payload: dict[str, Any],
    request_id: str | None = None,
) -> dict[str, object]:
    """Trigger the configured n8n business operations workflow via webhook."""
    settings = get_settings()

    action = action.strip()

    normalized_request_id = (
        request_id.strip()
        if isinstance(request_id, str) and request_id.strip().lower() not in {"", "null", "none"}
        else None
    )

    workflow_request_id = normalized_request_id or str(uuid4())

    if not action:
        logger.warning(
            "n8n_workflow_rejected",
            reason="empty_action",
        )

        return {
            "success": False,
            "message": "Workflow action cannot be empty.",
        }

    request_body = {
        "action": action,
        "request_id": workflow_request_id,
        "payload": payload,
    }

    logger.info(
        "n8n_workflow_started",
        workflow="business_operations",
        workflow_action=action,
        workflow_request_id=workflow_request_id,
    )

    try:
        response = httpx.post(
            settings.n8n_webhook_url,
            json=request_body,
            timeout=10.0,
        )
    except httpx.RequestError as exc:
        logger.exception(
            "n8n_workflow_failed",
            workflow="business_operations",
            workflow_action=action,
            workflow_request_id=workflow_request_id,
            error_type=type(exc).__name__,
        )

        return {
            "success": False,
            "request_id": workflow_request_id,
            "message": "n8n workflow service is unavailable.",
            "error_type": type(exc).__name__,
        }

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError:
        logger.error(
            "n8n_workflow_failed",
            workflow="business_operations",
            workflow_action=action,
            workflow_request_id=workflow_request_id,
            status_code=response.status_code,
        )

        return {
            "success": False,
            "request_id": workflow_request_id,
            "message": "n8n workflow returned an error.",
            "status_code": response.status_code,
        }

    try:
        workflow_response = response.json()
    except ValueError:
        logger.error(
            "n8n_workflow_invalid_response",
            workflow="business_operations",
            workflow_action=action,
            workflow_request_id=workflow_request_id,
        )

        return {
            "success": False,
            "request_id": workflow_request_id,
            "message": "n8n returned an invalid JSON response.",
        }

    logger.info(
        "n8n_workflow_completed",
        workflow="business_operations",
        workflow_action=action,
        workflow_request_id=workflow_request_id,
        workflow_status=workflow_response.get("status"),
        side_effect_performed=workflow_response.get("side_effect_performed"),
    )

    return {
        "success": True,
        "request_id": workflow_request_id,
        "workflow_response": workflow_response,
    }
