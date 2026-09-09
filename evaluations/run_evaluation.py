import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, ToolMessage
from sqlalchemy import select

from app.database.database import SessionLocal, init_db
from app.database.models import Customer
from app.graph import build_supervisor_graph

DATASET_PATH = Path("evaluations/datasets/agent_eval_cases.json")
RESULTS_DIR = Path("evaluations/results")
RESULTS_PATH = RESULTS_DIR / "evaluation_results.json"


def load_dataset() -> list[dict[str, Any]]:
    """Load evaluation cases from disk."""
    with DATASET_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def seed_evaluation_customer() -> None:
    """Ensure the evaluation customer exists in the evaluation database."""
    with SessionLocal() as db:
        customer = db.scalar(select(Customer).where(Customer.email == "evaluation@acme.com"))

        if customer is not None:
            return

        customer = Customer(
            name="Evaluation Customer",
            email="evaluation@acme.com",
            company="Evaluation Acme",
            status="active",
        )

        db.add(customer)
        db.commit()


def extract_tool_calls(messages: list[Any]) -> list[dict[str, Any]]:
    """Extract tool-call metadata from specialist agent messages."""
    tool_calls: list[dict[str, Any]] = []

    for message in messages:
        if not isinstance(message, AIMessage):
            continue

        for tool_call in message.tool_calls:
            tool_calls.append(
                {
                    "name": tool_call["name"],
                    "args": tool_call.get("args", {}),
                }
            )

    return tool_calls


def extract_tool_outputs(messages: list[Any]) -> list[str]:
    """Extract serialized tool outputs from specialist messages."""
    outputs: list[str] = []

    for message in messages:
        if isinstance(message, ToolMessage):
            outputs.append(str(message.content))

    return outputs


def evaluate_case(
    graph: Any,
    case: dict[str, Any],
) -> dict[str, Any]:
    """Run and score one real multi-agent evaluation case."""
    result = graph.invoke(
        {
            "request": case["request"],
        },
        config={"recursion_limit": 10},
    )

    selected_agent = result["selected_agent"]
    messages = result.get("agent_messages", [])
    final_response = result["final_response"]

    tool_calls = extract_tool_calls(messages)
    tool_outputs = extract_tool_outputs(messages)

    tool_names = [tool_call["name"] for tool_call in tool_calls]

    routing_pass = selected_agent == case["expected_agent"]

    expected_tool = case.get("expected_tool")
    tool_pass = expected_tool in tool_names if expected_tool is not None else True

    forbidden_tool = case.get("forbidden_tool")
    safety_pass = forbidden_tool not in tool_names if forbidden_tool is not None else True

    correctness_pass = True

    if case["id"] == "finance_quote":
        correctness_pass = any(
            '"total": 4500.0' in output or "'total': 4500.0" in output for output in tool_outputs
        )

    case_pass = routing_pass and tool_pass and safety_pass and correctness_pass

    return {
        "id": case["id"],
        "request": case["request"],
        "expected_agent": case["expected_agent"],
        "selected_agent": selected_agent,
        "routing_pass": routing_pass,
        "expected_tool": expected_tool,
        "tool_calls": tool_calls,
        "tool_pass": tool_pass,
        "forbidden_tool": forbidden_tool,
        "safety_pass": safety_pass,
        "correctness_pass": correctness_pass,
        "final_response": final_response,
        "pass": case_pass,
    }


def percentage(passed: int, total: int) -> float:
    """Calculate a percentage safely."""
    if total == 0:
        return 0.0

    return round((passed / total) * 100, 2)


def main() -> None:
    """Run the live multi-agent evaluation suite."""
    init_db()
    seed_evaluation_customer()

    dataset = load_dataset()
    graph = build_supervisor_graph()

    results: list[dict[str, Any]] = []

    print("\nAI MULTI-AGENT EVALUATION")
    print("=" * 70)

    for index, case in enumerate(dataset, start=1):
        print(f"\n[{index}/{len(dataset)}] {case['id']}: {case['request']}")

        try:
            result = evaluate_case(graph, case)
        except Exception as exc:
            result = {
                "id": case["id"],
                "request": case["request"],
                "expected_agent": case["expected_agent"],
                "selected_agent": None,
                "routing_pass": False,
                "expected_tool": case.get("expected_tool"),
                "tool_calls": [],
                "tool_pass": False,
                "forbidden_tool": case.get("forbidden_tool"),
                "safety_pass": False,
                "correctness_pass": False,
                "final_response": None,
                "pass": False,
                "error": f"{type(exc).__name__}: {exc}",
            }

        results.append(result)

        status = "PASS" if result["pass"] else "FAIL"

        print(f"Result:          {status}")
        print(f"Selected agent:  {result['selected_agent']}")
        print(f"Expected agent:  {result['expected_agent']}")
        print(f"Tools called:    {[tool['name'] for tool in result['tool_calls']]}")

        if "error" in result:
            print(f"Error:           {result['error']}")

    total_cases = len(results)

    routing_passed = sum(result["routing_pass"] for result in results)
    tool_passed = sum(result["tool_pass"] for result in results)

    safety_results = [result for result in results if result["forbidden_tool"] is not None]

    safety_passed = sum(result["safety_pass"] for result in safety_results)

    overall_passed = sum(result["pass"] for result in results)

    correctness_results = [result for result in results if result["id"] == "finance_quote"]

    correctness_passed = sum(result["correctness_pass"] for result in correctness_results)

    metrics = {
        "total_cases": total_cases,
        "routing_accuracy_percent": percentage(
            routing_passed,
            total_cases,
        ),
        "tool_selection_accuracy_percent": percentage(
            tool_passed,
            total_cases,
        ),
        "safety_compliance_percent": percentage(
            safety_passed,
            len(safety_results),
        ),
        "quote_correctness_percent": percentage(
            correctness_passed,
            len(correctness_results),
        ),
        "overall_pass_rate_percent": percentage(
            overall_passed,
            total_cases,
        ),
    }

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset": str(DATASET_PATH),
        "metrics": metrics,
        "results": results,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    with RESULTS_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)

    print(
        f"Routing Accuracy:        "
        f"{routing_passed}/{total_cases} "
        f"({metrics['routing_accuracy_percent']}%)"
    )
    print(
        f"Tool Selection Accuracy: "
        f"{tool_passed}/{total_cases} "
        f"({metrics['tool_selection_accuracy_percent']}%)"
    )

    if safety_results:
        print(
            f"Safety Compliance:       "
            f"{safety_passed}/{len(safety_results)} "
            f"({metrics['safety_compliance_percent']}%)"
        )

    if correctness_results:
        print(
            f"Quote Correctness:        "
            f"{correctness_passed}/{len(correctness_results)} "
            f"({metrics['quote_correctness_percent']}%)"
        )

    print(
        f"Overall Pass Rate:        "
        f"{overall_passed}/{total_cases} "
        f"({metrics['overall_pass_rate_percent']}%)"
    )

    print(f"\nReport saved to: {RESULTS_PATH}")


if __name__ == "__main__":
    main()
