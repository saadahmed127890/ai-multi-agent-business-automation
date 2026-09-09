from sqlalchemy import select

from app.database.models import Customer, Quote
from app.tools import calculate_margin, calculate_quote


def test_calculate_quote_without_persistence() -> None:
    result = calculate_quote.invoke(
        {
            "subtotal": 5000,
            "discount_percent": 10,
        }
    )

    assert result["success"] is True
    assert result["subtotal"] == 5000.0
    assert result["discount_amount"] == 500.0
    assert result["total"] == 4500.0
    assert result["saved"] is False


def test_calculate_margin() -> None:
    result = calculate_margin.invoke(
        {
            "revenue": 10000,
            "cost": 7000,
        }
    )

    assert result["success"] is True
    assert result["margin_amount"] == 3000.0
    assert result["margin_percent"] == 30.0


def test_calculate_quote_persists_to_database(db_session) -> None:
    customer = Customer(
        name="Finance Test Customer",
        email="finance@test.com",
        company="Test Company",
        status="active",
    )

    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)

    result = calculate_quote.invoke(
        {
            "subtotal": 2000,
            "discount_percent": 25,
            "customer_id": customer.id,
        }
    )

    assert result["success"] is True
    assert result["saved"] is True
    assert result["total"] == 1500.0

    quote = db_session.scalar(select(Quote).where(Quote.id == result["quote_id"]))

    assert quote is not None
    assert quote.customer_id == customer.id
    assert quote.total == 1500.0
    assert quote.status == "draft"
