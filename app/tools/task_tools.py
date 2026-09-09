from typing import Any

from langchain.tools import tool
from sqlalchemy import func, select

from app.database.database import SessionLocal
from app.database.models import Approval, Customer, Task


@tool
def create_business_task(
    title: str,
    description: str,
    assigned_agent: str = "operations",
) -> dict[str, object]:
    """Create and persist a business task for an agent or team."""
    title = title.strip()
    description = description.strip()
    assigned_agent = assigned_agent.strip().lower()

    if not title:
        return {
            "created": False,
            "message": "Task title cannot be empty.",
        }

    with SessionLocal() as db:
        task = Task(
            title=title,
            description=description,
            assigned_agent=assigned_agent,
            status="pending",
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        return {
            "created": True,
            "task": {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "assigned_agent": task.assigned_agent,
                "status": task.status,
            },
        }


@tool
def request_human_approval(
    action: str,
    payload: dict[str, Any],
) -> dict[str, object]:
    """Create a pending human approval request for a sensitive action."""
    action = action.strip()

    if not action:
        return {
            "created": False,
            "message": "Approval action cannot be empty.",
        }

    with SessionLocal() as db:
        approval = Approval(
            action=action,
            payload=payload,
            status="pending",
        )

        db.add(approval)
        db.commit()
        db.refresh(approval)

        return {
            "created": True,
            "approval": {
                "id": approval.id,
                "action": approval.action,
                "payload": approval.payload,
                "status": approval.status,
            },
            "message": "Human approval is required before execution.",
        }


@tool
def create_support_task(
    email: str,
    title: str,
    description: str,
) -> dict[str, object]:
    """Verify a customer by email and create a support follow-up task."""
    normalized_email = email.strip().lower()
    title = title.strip()
    description = description.strip()

    if not title:
        return {
            "created": False,
            "message": "Task title cannot be empty.",
        }

    with SessionLocal() as db:
        customer = db.scalar(select(Customer).where(func.lower(Customer.email) == normalized_email))

        if customer is None:
            return {
                "created": False,
                "email": normalized_email,
                "message": ("Cannot create support task because the customer does not exist."),
            }

        task = Task(
            title=title,
            description=description,
            assigned_agent="support",
            status="pending",
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        return {
            "created": True,
            "customer": {
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
            },
            "task": {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "assigned_agent": task.assigned_agent,
                "status": task.status,
            },
        }
