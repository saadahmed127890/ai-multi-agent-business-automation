from functools import lru_cache
from uuid import uuid4

from langchain_core.messages import AIMessage

from app.core.logging import get_logger
from app.graph import build_supervisor_graph
from app.schemas.agents import AgentRunResponse, ToolCallRecord

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_supervisor_graph():
    """Return a reusable compiled supervisor graph."""
    return build_supervisor_graph()


def run_business_agent(request: str) -> AgentRunResponse:
    """Run a business request through the multi-agent supervisor."""
    execution_id = str(uuid4())

    execution_logger = logger.bind(
        execution_id=execution_id,
    )

    execution_logger.info(
        "agent_execution_started",
        request_length=len(request),
    )

    try:
        graph = get_supervisor_graph()

        result = graph.invoke(
            {"request": request},
            config={"recursion_limit": 10},
        )

        tool_calls: list[ToolCallRecord] = []

        for message in result.get("agent_messages", []):
            if not isinstance(message, AIMessage):
                continue

            for tool_call in message.tool_calls:
                record = ToolCallRecord(
                    name=tool_call["name"],
                    arguments=tool_call.get("args", {}),
                )

                tool_calls.append(record)

                execution_logger.info(
                    "agent_tool_called",
                    selected_agent=result["selected_agent"],
                    tool_name=record.name,
                )

        execution_logger.info(
            "agent_execution_completed",
            selected_agent=result["selected_agent"],
            routing_reason=result["routing_reason"],
            tool_count=len(tool_calls),
        )

        return AgentRunResponse(
            selected_agent=result["selected_agent"],
            routing_reason=result["routing_reason"],
            final_response=result["final_response"],
            tool_calls=tool_calls,
        )

    except Exception:
        execution_logger.exception(
            "agent_execution_failed",
        )
        raise
