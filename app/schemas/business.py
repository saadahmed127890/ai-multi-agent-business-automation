from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    company: str | None = None


class CustomerResponse(CustomerCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    created_at: datetime


class LeadCreate(BaseModel):
    customer_id: int
    source: str = "manual"
    notes: str | None = None


class LeadResponse(LeadCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    created_at: datetime


class QuoteCreate(BaseModel):
    customer_id: int
    subtotal: float = Field(gt=0)
    discount_percent: float = Field(default=0, ge=0, le=100)


class QuoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    subtotal: float
    discount_percent: float
    total: float
    status: str
    created_at: datetime


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    assigned_agent: str | None = None


class TaskResponse(TaskCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    created_at: datetime


class ApprovalCreate(BaseModel):
    action: str = Field(min_length=1, max_length=200)
    payload: dict[str, Any]


class ApprovalResponse(ApprovalCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    created_at: datetime
