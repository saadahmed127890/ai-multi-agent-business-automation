from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import Approval, Customer, Lead, Quote, Task
from app.schemas.business import (
    ApprovalCreate,
    ApprovalResponse,
    CustomerCreate,
    CustomerResponse,
    LeadCreate,
    LeadResponse,
    QuoteCreate,
    QuoteResponse,
    TaskCreate,
    TaskResponse,
)

router = APIRouter(prefix="/api/v1", tags=["Business"])

DBSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/customers",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer(
    payload: CustomerCreate,
    db: DBSession,
) -> Customer:
    customer = Customer(**payload.model_dump())

    db.add(customer)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A customer with this email already exists.",
        ) from exc

    db.refresh(customer)
    return customer


@router.get("/customers", response_model=list[CustomerResponse])
def list_customers(
    db: DBSession,
) -> list[Customer]:
    return list(db.scalars(select(Customer).order_by(Customer.id)).all())


@router.post(
    "/leads",
    response_model=LeadResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_lead(
    payload: LeadCreate,
    db: DBSession,
) -> Lead:
    if db.get(Customer, payload.customer_id) is None:
        raise HTTPException(status_code=404, detail="Customer not found.")

    lead = Lead(**payload.model_dump())

    db.add(lead)
    db.commit()
    db.refresh(lead)

    return lead


@router.get("/leads", response_model=list[LeadResponse])
def list_leads(
    db: DBSession,
) -> list[Lead]:
    return list(db.scalars(select(Lead).order_by(Lead.id)).all())


@router.post(
    "/quotes",
    response_model=QuoteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quote(
    payload: QuoteCreate,
    db: DBSession,
) -> Quote:
    if db.get(Customer, payload.customer_id) is None:
        raise HTTPException(status_code=404, detail="Customer not found.")

    discount = payload.subtotal * payload.discount_percent / 100
    total = round(payload.subtotal - discount, 2)

    quote = Quote(
        customer_id=payload.customer_id,
        subtotal=payload.subtotal,
        discount_percent=payload.discount_percent,
        total=total,
    )

    db.add(quote)
    db.commit()
    db.refresh(quote)

    return quote


@router.get("/quotes", response_model=list[QuoteResponse])
def list_quotes(
    db: DBSession,
) -> list[Quote]:
    return list(db.scalars(select(Quote).order_by(Quote.id)).all())


@router.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    payload: TaskCreate,
    db: DBSession,
) -> Task:
    task = Task(**payload.model_dump())

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.get("/tasks", response_model=list[TaskResponse])
def list_tasks(
    db: DBSession,
) -> list[Task]:
    return list(db.scalars(select(Task).order_by(Task.id)).all())


@router.post(
    "/approvals",
    response_model=ApprovalResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_approval(
    payload: ApprovalCreate,
    db: DBSession,
) -> Approval:
    approval = Approval(**payload.model_dump())

    db.add(approval)
    db.commit()
    db.refresh(approval)

    return approval


@router.get("/approvals", response_model=list[ApprovalResponse])
def list_approvals(
    db: DBSession,
) -> list[Approval]:
    return list(db.scalars(select(Approval).order_by(Approval.id)).all())


@router.post(
    "/approvals/{approval_id}/approve",
    response_model=ApprovalResponse,
)
def approve_action(
    approval_id: int,
    db: DBSession,
) -> Approval:
    approval = db.get(Approval, approval_id)

    if approval is None:
        raise HTTPException(status_code=404, detail="Approval not found.")

    approval.status = "approved"

    db.commit()
    db.refresh(approval)

    return approval
