from fastapi import APIRouter, HTTPException, status

from app.schemas.agents import AgentRunRequest, AgentRunResponse
from app.services.agent_service import run_business_agent

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.post(
    "/run",
    response_model=AgentRunResponse,
    status_code=status.HTTP_200_OK,
)
def run_agent(request: AgentRunRequest) -> AgentRunResponse:
    """Route a business request through the multi-agent system."""
    try:
        return run_business_agent(request.request)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent execution failed.",
        ) from exc
