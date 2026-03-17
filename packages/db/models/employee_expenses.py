from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import Column, Date, DateTime, Index, Numeric
from sqlmodel import Field

from packages.db.base import BaseModel
from packages.db.mixins import IDMixin, TimestampMixin


class EmployeeExpenseStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class EmployeeExpenseCategory(str, Enum):
    TRAVEL = "TRAVEL"
    MEALS = "MEALS"
    ACCOMMODATION = "ACCOMMODATION"
    OFFICE_SUPPLIES = "OFFICE_SUPPLIES"
    CLIENT_ENTERTAINMENT = "CLIENT_ENTERTAINMENT"
    OTHER = "OTHER"


class EmployeeExpense(BaseModel, IDMixin, TimestampMixin, table=True):
    """
    Employee expenses table.

    Optimized for:
      - per-employee spending patterns
      - category/cost center anomalies
      - linkage with vendor + invoice + transaction in later phases
    """

    __tablename__ = "employee_expenses"

    __table_args__ = (
        Index(
            "ix_employee_expenses_tenant_employee_date",
            "tenant_id",
            "employee_id",
            "expense_date",
        ),
    )

    tenant_id: Optional[int] = Field(default=None, index=True)

    # Business / external identifiers
    expense_reference: str = Field(
        index=True,
        description="External expense claim ID/reference from source system.",
    )
    employee_id: str = Field(
        index=True,
        description="Employee identifier/number.",
    )

    # Optional linkage into other tables
    invoice_id: Optional[int] = Field(
        default=None,
        foreign_key="invoices.id",
        description="Optional link to an associated invoice.",
    )
    transaction_id: Optional[int] = Field(
        default=None,
        foreign_key="transactions.id",
        description="Optional link to the payment transaction.",
    )

    # Time fields
    expense_date: date = Field(
        sa_column=Column(Date, nullable=False),
        description="Date when the expense occurred.",
    )
    submitted_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
        description="When the expense was submitted.",
    )
    approved_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
        description="When the expense was approved.",
    )
    paid_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
        description="When the expense was reimbursed/paid.",
    )

    # Monetary info
    amount: Decimal = Field(
        sa_column=Column(Numeric(18, 2), nullable=False),
        description="Expense amount in the original currency.",
    )
    currency: str = Field(
        max_length=3,
        description="ISO 4217 currency code.",
    )

    category: EmployeeExpenseCategory = Field(
        description="High-level expense category.",
    )

    status: EmployeeExpenseStatus = Field(
        default=EmployeeExpenseStatus.SUBMITTED,
        description="Lifecycle status of the expense.",
    )

    # Context fields for rules & graph
    country_code: Optional[str] = Field(
        default=None,
        max_length=2,
        description="Country where the expense occurred.",
    )
    merchant_name: Optional[str] = Field(
        default=None,
        max_length=128,
        description="Merchant or vendor name on the receipt.",
    )
    cost_center_code: Optional[str] = Field(
        default=None,
        max_length=32,
        description="Cost center / department code.",
    )
    project_code: Optional[str] = Field(
        default=None,
        max_length=32,
        description="Project code if applicable.",
    )
    description: Optional[str] = Field(
        default=None,
        description="Free-text description of the expense.",
    )

    # Relationships (off for now, can be enabled later)
    # invoice: Optional["Invoice"] = Relationship(back_populates="employee_expenses")
    # transaction: Optional["Transaction"] = Relationship(back_populates="employee_expense")
