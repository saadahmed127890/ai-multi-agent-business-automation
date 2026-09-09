from typing import Any, Literal

from pydantic import BaseModel, Field

AgentName = Literal["sales", "finance", "support", "operations"]


class AgentRunRequest(BaseModel):
    """Request for the multi-agent business automation system."""

    request: str = Field(
        min_length=1,
        max_length=5000,
        description="Business request to route to the appropriate specialist agent.",
    )


class ToolCallRecord(BaseModel):
    """Metadata describing a tool selected by a specialist agent."""

    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class AgentRunResponse(BaseModel):
    """Response returned by the multi-agent business automation system."""

    selected_agent: AgentName
    routing_reason: str
    final_response: str
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
