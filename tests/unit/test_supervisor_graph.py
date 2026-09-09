import pytest
from langchain_core.messages import AIMessage

from app.graph import supervisor as supervisor_module


class FakeRouterModel:
    def invoke(self, messages):
        user_request = messages[-1]["content"].lower()

        if "quote" in user_request or "discount" in user_request:
            agent = "finance"
        elif "sales lead" in user_request:
            agent = "sales"
        elif "onboarding" in user_request or "support" in user_request:
            agent = "support"
        else:
            agent = "operations"

        return supervisor_module.RoutingDecision(
            agent=agent,
            reason=f"pytest selected {agent}",
        )


class FakeLLM:
    def with_structured_output(self, schema):
        return FakeRouterModel()


class FakeSpecialistAgent:
    def __init__(self, name: str) -> None:
        self.name = name

    def invoke(self, input_data, config=None):
        return {"messages": [AIMessage(content=f"{self.name} specialist completed the request.")]}


@pytest.mark.parametrize(
    ("user_request", "expected_agent"),
    [
        (
            "Calculate a quote for $5000 with a 10 percent discount.",
            "finance",
        ),
        (
            "Create a sales lead for customer@example.com.",
            "sales",
        ),
        (
            "Customer has an unresolved onboarding support issue.",
            "support",
        ),
        (
            "Run the internal business operations workflow.",
            "operations",
        ),
    ],
)
def test_supervisor_routes_to_correct_specialist(
    monkeypatch,
    user_request: str,
    expected_agent: str,
) -> None:
    monkeypatch.setattr(
        supervisor_module,
        "get_llm",
        lambda: FakeLLM(),
    )

    monkeypatch.setattr(
        supervisor_module,
        "build_sales_agent",
        lambda: FakeSpecialistAgent("sales"),
    )
    monkeypatch.setattr(
        supervisor_module,
        "build_finance_agent",
        lambda: FakeSpecialistAgent("finance"),
    )
    monkeypatch.setattr(
        supervisor_module,
        "build_support_agent",
        lambda: FakeSpecialistAgent("support"),
    )
    monkeypatch.setattr(
        supervisor_module,
        "build_operations_agent",
        lambda: FakeSpecialistAgent("operations"),
    )

    graph = supervisor_module.build_supervisor_graph()

    result = graph.invoke(
        {
            "request": user_request,
        }
    )

    assert result["selected_agent"] == expected_agent
    assert result["routing_reason"] == f"pytest selected {expected_agent}"
    assert expected_agent in result["final_response"]
