from sqlalchemy import select

from app.database.models import Customer, Task
from app.tools import create_support_task


def test_create_support_task_persists_real_task(db_session) -> None:
    customer = Customer(
        name="Support Test Customer",
        email="support@test.com",
        company="Support Company",
        status="active",
    )

    db_session.add(customer)
    db_session.commit()

    result = create_support_task.invoke(
        {
            "email": "support@test.com",
            "title": "Onboarding follow-up",
            "description": "Resolve customer onboarding issue.",
        }
    )

    assert result["created"] is True
    assert result["task"]["assigned_agent"] == "support"
    assert result["task"]["status"] == "pending"

    task = db_session.scalar(select(Task).where(Task.id == result["task"]["id"]))

    assert task is not None
    assert task.title == "Onboarding follow-up"
    assert task.assigned_agent == "support"
    assert task.status == "pending"


def test_create_support_task_requires_existing_customer() -> None:
    result = create_support_task.invoke(
        {
            "email": "unknown@test.com",
            "title": "Missing customer issue",
            "description": "This task must not be created.",
        }
    )

    assert result["created"] is False
    assert result["message"] == ("Cannot create support task because the customer does not exist.")
