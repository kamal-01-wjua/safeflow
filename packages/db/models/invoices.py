from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional, List

from sqlalchemy import Column, Date, Index, Numeric, UniqueConstraint
from sqlmodel import SQLModel, Field, Relationship

from packages.db.base import BaseModel
from packages.db.mixins import IDMixin, TimestampMixin


class InvoiceStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class Invoice(BaseModel, IDMixin, TimestampMixin, table=True):
    """
    Invoices table.
    Optimized for:
      - duplicate invoice rules
      - windowed checks (same vendor, same amount, similar dates)
      - cost center / budget rules
    """

    __tablename__ = "invoices"

    __table_args__ = (
        # ️️For duplicate detection and windowed rules
        Index(
            "ix_invoices_tenant_vendor_date",
            "tenant_id",
            "vendor_id",
            "invoice_date",
        ),
        UniqueConstraint(
            "tenant_id",
            "invoice_number",
            name="uq_invoices_tenant_invoice_number",
        ),
    )

    tenant_id: Optional[int] = Field(default=None, index=True)

    invoice_number: str = Field(
        index=True,
        description="Invoice number as provided by the vendor.",
    )

    vendor_id: str = Field(
        index=True,
        description="Vendor identifier/code.",
    )

    employee_id: Optional[str] = Field(
        default=None,
        index=True,
        description="Employee who submitted/owns this invoice.",
    )

    invoice_date: date = Field(
        sa_column=Column(Date, nullable=False),
        description="Date on the invoice.",
    )
    due_date: Optional[date] = Field(
        default=None,
        sa_column=Column(Date, nullable=True),
        description="Due date for payment.",
    )

    currency: str = Field(
        max_length=3,
        description="ISO 4217 currency code.",
    )

    subtotal_amount: Decimal = Field(
        sa_column=Column(Numeric(18, 2), nullable=False),
        description="Amount before tax.",
    )
    tax_amount: Decimal = Field(
        sa_column=Column(Numeric(18, 2), nullable=False),
        description="Tax amount.",
    )
    total_amount: Decimal = Field(
        sa_column=Column(Numeric(18, 2), nullable=False),
        description="Total amount including tax.",
    )

    status: InvoiceStatus = Field(
        default=InvoiceStatus.PENDING_APPROVAL,
        description="Lifecycle status of the invoice.",
    )

    cost_center_code: Optional[str] = Field(
        default=None,
        max_length=32,
        description="Cost center / department code.",
    )
    purchase_order_number: Optional[str] = Field(
        default=None,
        max_length=64,
        description="Related PO number if any.",
    )

    description: Optional[str] = Field(
        default=None,
        description="Free-text description.",
    )

    # Relationships
    # Temporarily disabled; see Transaction model comment.
    # transactions: List["Transaction"] = Relationship(back_populates="invoice")

