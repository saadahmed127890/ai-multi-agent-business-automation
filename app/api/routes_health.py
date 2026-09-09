from fastapi import APIRouter

from app.config import get_settings
from app.schemas.system import HealthResponse, SystemInfoResponse

router = APIRouter(tags=["System"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Application health check",
)
def health_check() -> HealthResponse:
    """Return the current health status of the API."""

    settings = get_settings()

    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        environment=settings.app_env,
    )


@router.get(
    "/api/v1/system/info",
    response_model=SystemInfoResponse,
    summary="Get application information",
)
def system_info() -> SystemInfoResponse:
    """Return non-sensitive runtime information."""

    settings = get_settings()

    if settings.llm_provider == "ollama":
        model = settings.ollama_model
    else:
        model = settings.openai_model or "not-configured"

    return SystemInfoResponse(
        application=settings.app_name,
        environment=settings.app_env,
        llm_provider=settings.llm_provider,
        llm_model=model,
        human_approval_enabled=settings.require_human_approval,
    )
