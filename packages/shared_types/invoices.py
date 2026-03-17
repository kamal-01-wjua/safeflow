from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class InvoiceStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class InvoiceResponse(BaseModel):
    """
    Public-safe invoice DTO.
    Used for Analyst Case View and Invoice endpoints.
    """

    id: int
    invoice_number: str
    vendor_id: str
    employee_id: Optional[str] = None

    invoice_date: date
    due_date: Optional[date] = None

    currency: str

    subtotal_amount: float
    tax_amount: float
    total_amount: float

    status: InvoiceStatus

    cost_center_code: Optional[str] = None
    purchase_order_number: Optional[str] = None

    description: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CreateInvoiceRequest(BaseModel):
    """
    Data needed to create a new Invoice.
    Clean input model for POST /invoices.
    """

    invoice_number: str
    vendor_id: str
    employee_id: Optional[str] = None

    invoice_date: date
    due_date: Optional[date] = None

    currency: str = Field(max_length=3)

    subtotal_amount: float
    tax_amount: float
    total_amount: float

    status: InvoiceStatus = InvoiceStatus.PENDING_APPROVAL

    cost_center_code: Optional[str] = None
    purchase_order_number: Optional[str] = None
    description: Optional[str] = None

    @field_validator("subtotal_amount", "tax_amount", "total_amount", mode="before")
    def convert_decimal_fields(cls, v):
        # Normalize to float for clean JSON inputs
        return float(v)

    class Config:
        json_schema_extra = {
            "example": {
                "invoice_number": "INV-2025-001",
                "vendor_id": "VENDOR-101",
                "employee_id": "EMP-44",
                "invoice_date": "2025-01-10",
                "due_date": "2025-02-10",
                "currency": "USD",
                "subtotal_amount": 500.00,
                "tax_amount": 30.00,
                "total_amount": 530.00,
                "status": "PENDING_APPROVAL",
                "cost_center_code": "IT-OPS",
                "purchase_order_number": "PO-8891",
                "description": "Cloud infrastructure usage for Jan 2025",
            }
        }
