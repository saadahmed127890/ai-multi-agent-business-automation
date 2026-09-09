from typing import Any, Literal, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from app.agents import (
    build_finance_agent,
    build_operations_agent,
    build_sales_agent,
    build_support_agent,
)
from app.llm.factory import get_llm

AgentName = Literal["sales", "finance", "support", "operations"]


class RoutingDecision(BaseModel):
    """Structured supervisor routing decision."""

    agent: AgentName = Field(description="The specialist agent that should handle the request.")
    reason: str = Field(description="A short explanation for why this specialist was selected.")


class SupervisorState(TypedDict, total=False):
    """State shared across the multi-agent LangGraph workflow."""

    request: str
    selected_agent: AgentName
    routing_reason: str
    final_response: str
    agent_messages: list[BaseMessage]


SUPERVISOR_PROMPT = """
You are the Supervisor Agent for an AI-powered business automation platform.

Your only job is to route each business request to exactly one specialist.

Available specialists:

sales
- customer lookup
- sales leads
- prospects
- sales-related customer actions

finance
- quotes
- discounts
- pricing calculations
- revenue
- costs
- profit
- margins

support
- customer issues
- onboarding problems
- support follow-ups
- customer assistance

operations
- internal operational tasks
- workflow coordination
- n8n business automation workflows
- external logistics vendor status checks
- external REST API lookups
- sensitive external actions
- actions requiring human approval

Routing examples:

"Run the business operations workflow to create a delayed shipment follow-up."
→ operations

"Check the operational status of vendor ACME-LOGISTICS."
→ operations

"Calculate a quote for $5000 with a 10 percent discount."
→ finance

"Create a sales lead for john@example.com."
→ sales

"Customer john@example.com has an unresolved onboarding issue."
→ support

"Prepare an external email and request human approval."
→ operations

Choose exactly one specialist.
Do not perform the specialist's work yourself.
""".strip()


def _invoke_specialist(
    agent: Any,
    state: SupervisorState,
) -> dict[str, object]:
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": state["request"],
                }
            ]
        },
        config={"recursion_limit": 6},
    )

    messages = result["messages"]
    final_message = messages[-1]

    return {
        "agent_messages": messages,
        "final_response": str(final_message.content),
    }


def build_supervisor_graph():
    """Build and compile the LangGraph multi-agent supervisor."""
    router_model = get_llm().with_structured_output(RoutingDecision)

    sales_agent = build_sales_agent()
    finance_agent = build_finance_agent()
    support_agent = build_support_agent()
    operations_agent = build_operations_agent()

    def supervisor_node(state: SupervisorState) -> dict[str, object]:
        decision = router_model.invoke(
            [
                {
                    "role": "system",
                    "content": SUPERVISOR_PROMPT,
                },
                {
                    "role": "user",
                    "content": state["request"],
                },
            ]
        )

        return {
            "selected_agent": decision.agent,
            "routing_reason": decision.reason,
        }

    def sales_node(state: SupervisorState) -> dict[str, object]:
        return _invoke_specialist(sales_agent, state)

    def finance_node(state: SupervisorState) -> dict[str, object]:
        return _invoke_specialist(finance_agent, state)

    def support_node(state: SupervisorState) -> dict[str, object]:
        return _invoke_specialist(support_agent, state)

    def operations_node(state: SupervisorState) -> dict[str, object]:
        return _invoke_specialist(operations_agent, state)

    def route_to_specialist(state: SupervisorState) -> AgentName:
        return state["selected_agent"]

    workflow = StateGraph(SupervisorState)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("sales", sales_node)
    workflow.add_node("finance", finance_node)
    workflow.add_node("support", support_node)
    workflow.add_node("operations", operations_node)

    workflow.add_edge(START, "supervisor")

    workflow.add_conditional_edges(
        "supervisor",
        route_to_specialist,
        {
            "sales": "sales",
            "finance": "finance",
            "support": "support",
            "operations": "operations",
        },
    )

    workflow.add_edge("sales", END)
    workflow.add_edge("finance", END)
    workflow.add_edge("support", END)
    workflow.add_edge("operations", END)

    return workflow.compile()
