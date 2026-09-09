from langchain.tools import tool

from app.services.approval_service import execute_approved_action


@tool
def execute_human_approved_action(approval_id: int) -> dict[str, object]:
    """Execute a sensitive business action only after human approval."""
    return execute_approved_action(approval_id)
