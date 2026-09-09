from sqlalchemy import select

from app.database.models import Customer, Lead
from app.tools import create_sales_lead, get_customer_by_email


def test_get_customer_by_email_is_case_insensitive(db_session) -> None:
    customer = Customer(
        name="Sales Test Customer",
        email="sales@test.com",
        company="Sales Company",
        status="active",
    )

    db_session.add(customer)
    db_session.commit()

    result = get_customer_by_email.invoke(
        {
            "email": "SALES@TEST.COM",
        }
    )

    assert result["found"] is True
    assert result["customer"]["email"] == "sales@test.com"


def test_create_sales_lead_for_existing_customer(db_session) -> None:
    customer = Customer(
        name="Lead Test Customer",
        email="lead@test.com",
        company="Lead Company",
        status="active",
    )

    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)

    result = create_sales_lead.invoke(
        {
            "email": "lead@test.com",
            "source": "pytest",
            "notes": "Created by automated test.",
        }
    )

    assert result["created"] is True
    assert result["lead"]["customer_id"] == customer.id
    assert result["lead"]["status"] == "new"

    lead = db_session.scalar(select(Lead).where(Lead.id == result["lead"]["id"]))

    assert lead is not None
    assert lead.customer_id == customer.id
    assert lead.source == "pytest"


def test_create_sales_lead_rejects_unknown_customer() -> None:
    result = create_sales_lead.invoke(
        {
            "email": "missing@test.com",
        }
    )

    assert result["created"] is False
    assert result["message"] == ("Cannot create lead because the customer does not exist.")
