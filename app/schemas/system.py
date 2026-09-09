from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response returned by the health-check endpoint."""

    status: str
    service: str
    environment: str


class SystemInfoResponse(BaseModel):
    """Public information about the running application."""

    application: str
    environment: str
    llm_provider: Literal["ollama", "openai"]
    llm_model: str
    human_approval_enabled: bool
