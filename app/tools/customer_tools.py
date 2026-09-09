from langchain.tools import tool
from sqlalchemy import func, select

from app.database.database import SessionLocal
from app.database.models import Customer, Lead


@tool
def get_customer_by_email(email: str) -> dict[str, object]:
    """Look up a customer in the business database by email address."""
    normalized_email = email.strip().lower()

    with SessionLocal() as db:
        customer = db.scalar(select(Customer).where(func.lower(Customer.email) == normalized_email))

        if customer is None:
            return {
                "found": False,
                "email": normalized_email,
                "message": "Customer not found.",
            }

        return {
            "found": True,
            "customer": {
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
                "company": customer.company,
                "status": customer.status,
            },
        }


@tool
def create_sales_lead(
    email: str,
    source: str = "ai_agent",
    notes: str | None = None,
) -> dict[str, object]:
    """Create a sales lead for an existing customer identified by email."""
    normalized_email = email.strip().lower()

    with SessionLocal() as db:
        customer = db.scalar(select(Customer).where(func.lower(Customer.email) == normalized_email))

        if customer is None:
            return {
                "created": False,
                "email": normalized_email,
                "message": "Cannot create lead because the customer does not exist.",
            }

        lead = Lead(
            customer_id=customer.id,
            source=source,
            status="new",
            notes=notes,
        )

        db.add(lead)
        db.commit()
        db.refresh(lead)

        return {
            "created": True,
            "lead": {
                "id": lead.id,
                "customer_id": lead.customer_id,
                "customer_email": customer.email,
                "source": lead.source,
                "status": lead.status,
                "notes": lead.notes,
            },
        }
