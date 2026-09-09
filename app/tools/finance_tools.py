from langchain.tools import tool

from app.database.database import SessionLocal
from app.database.models import Customer, Quote


@tool
def calculate_quote(
    subtotal: float,
    discount_percent: float = 0.0,
    customer_id: int | None = None,
) -> dict[str, object]:
    """Calculate a discounted quote and optionally save it for a customer."""
    if subtotal < 0:
        return {
            "success": False,
            "message": "Subtotal cannot be negative.",
        }

    if not 0 <= discount_percent <= 100:
        return {
            "success": False,
            "message": "Discount percent must be between 0 and 100.",
        }

    subtotal = round(subtotal, 2)
    discount_percent = round(discount_percent, 2)

    discount_amount = round(subtotal * (discount_percent / 100), 2)
    total = round(subtotal - discount_amount, 2)

    result: dict[str, object] = {
        "success": True,
        "subtotal": subtotal,
        "discount_percent": discount_percent,
        "discount_amount": discount_amount,
        "total": total,
        "saved": False,
    }

    if customer_id is None:
        return result

    with SessionLocal() as db:
        customer = db.get(Customer, customer_id)

        if customer is None:
            return {
                **result,
                "success": False,
                "message": (
                    "Quote was calculated but could not be saved because "
                    "the customer does not exist."
                ),
            }

        quote = Quote(
            customer_id=customer_id,
            subtotal=subtotal,
            discount_percent=discount_percent,
            total=total,
            status="draft",
        )

        db.add(quote)
        db.commit()
        db.refresh(quote)

        result["saved"] = True
        result["quote_id"] = quote.id
        result["customer_id"] = customer_id
        result["status"] = quote.status

    return result


@tool
def calculate_margin(
    revenue: float,
    cost: float,
) -> dict[str, object]:
    """Calculate gross profit and gross margin percentage."""
    if revenue <= 0:
        return {
            "success": False,
            "message": "Revenue must be greater than zero.",
        }

    if cost < 0:
        return {
            "success": False,
            "message": "Cost cannot be negative.",
        }

    revenue = round(revenue, 2)
    cost = round(cost, 2)

    margin_amount = round(revenue - cost, 2)
    margin_percent = round((margin_amount / revenue) * 100, 2)

    return {
        "success": True,
        "revenue": revenue,
        "cost": cost,
        "margin_amount": margin_amount,
        "margin_percent": margin_percent,
    }
