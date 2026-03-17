from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field

# Import enums from DB models
from packages.db.models import (
    TransactionDirection,
    TransactionStatus,
    InvoiceStatus,
    VendorRiskLevel,
    EmployeeExpenseStatus,
    EmployeeExpenseCategory,
)

# -------------------------------------------------------------------
# TRANSACTIONS
# -------------------------------------------------------------------

class CreateTransactionRequest(BaseModel):
    tenant_id: Optional[int] = Field(default=None)

    transaction_reference: str = Field(
        description="External transaction ID from source system."
    )
    amount: Decimal = Field(description="Transaction amount.")
    currency: str = Field(max_length=3, description="ISO currency code.")

    account_id: Optional[str] = Field(default=None)
    counterparty_account: Optional[str] = Field(default=None)
    direction: TransactionDirection
    status: TransactionStatus

    timestamp: datetime = Field(description="Timestamp of the transaction.")


class TransactionResponse(CreateTransactionRequest):
    id: int
    created_at: datetime
    updated_at: datetime


# -------------------------------------------------------------------
# INVOICES
# -------------------------------------------------------------------

class CreateInvoiceRequest(BaseModel):
    tenant_id: Optional[int] = Field(default=None)

    invoice_reference: str
    vendor_code: Optional[str] = Field(default=None)
    amount: Decimal
    currency: str
    invoice_date: date
    due_date: Optional[date] = None
    status: InvoiceStatus


class InvoiceResponse(CreateInvoiceRequest):
    id: int
    created_at: datetime
    updated_at: datetime


# -------------------------------------------------------------------
# ALERTS (keep existing)
# -------------------------------------------------------------------

class AlertResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    rule_id: str
    risk_score: int
    message: str
    created_at: datetime


# -------------------------------------------------------------------
# VENDORS
# -------------------------------------------------------------------

class VendorBase(BaseModel):
    tenant_id: Optional[int] = Field(default=None)

    vendor_code: str = Field(description="Vendor identifier from core systems.")
    name: str

    country_code: Optional[str] = Field(default=None, max_length=2)
    city: Optional[str] = Field(default=None, max_length=64)
    tax_id: Optional[str] = Field(default=None, max_length=64)
    industry: Optional[str] = Field(default=None, max_length=64)

    risk_level: Optional[VendorRiskLevel] = None
    onboarding_date: Optional[date] = None
    is_active: bool = True
    notes: Optional[str] = None


class CreateVendorRequest(VendorBase):
    pass


class VendorResponse(VendorBase):
    id: int
    created_at: datetime
    updated_at: datetime


# -------------------------------------------------------------------
# EMPLOYEE EXPENSES
# -------------------------------------------------------------------

class EmployeeExpenseBase(BaseModel):
    tenant_id: Optional[int] = Field(default=None)

    expense_reference: str
    employee_id: str

    invoice_id: Optional[int] = None
    transaction_id: Optional[int] = None

    expense_date: date
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None

    amount: Decimal
    currency: str

    category: EmployeeExpenseCategory
    status: EmployeeExpenseStatus

    country_code: Optional[str] = Field(default=None, max_length=2)
    merchant_name: Optional[str] = Field(default=None, max_length=128)
    cost_center_code: Optional[str] = Field(default=None, max_length=32)
    project_code: Optional[str] = Field(default=None, max_length=32)
    description: Optional[str] = None


class CreateEmployeeExpenseRequest(EmployeeExpenseBase):
    pass


class EmployeeExpenseResponse(EmployeeExpenseBase):
    id: int
    created_at: datetime
    updated_at: datetime

# -------------------------------------------------------------------
# RISK PREVIEW (Fusion: rule + ML + graph)
# -------------------------------------------------------------------

class RiskPreviewEvent(BaseModel):
    """
    Input for risk preview scoring.

    This mirrors MLTransactionEvent plus optional vendor/employee context.
    """
    transaction_id: Optional[int] = Field(
        default=None,
        description="Internal transaction ID if available.",
    )
    tenant_id: Optional[int] = Field(
        default=None,
        description="Tenant / organization identifier.",
    )

    transaction_reference: str = Field(
        description="External transaction reference.",
    )
    account_id: Optional[str] = Field(
        default=None,
        description="Account identifier.",
    )

    amount: Decimal = Field(
        description="Transaction amount.",
    )
    currency: str = Field(
        max_length=3,
        description="ISO 4217 currency code.",
    )

    direction: str = Field(
        description="Transaction direction (e.g. CREDIT, DEBIT).",
    )
    status: str = Field(
        description="Transaction status (e.g. BOOKED, PENDING).",
    )

    timestamp: datetime = Field(
        description="Timestamp of the transaction.",
    )

    # Extra context for graph/rules
    vendor_code: Optional[str] = Field(
        default=None,
        description="Vendor code if this transaction is related to a vendor.",
    )
    employee_id: Optional[str] = Field(
        default=None,
        description="Employee ID if linked via an expense.",
    )


class RiskPreviewRequest(BaseModel):
    events: List[RiskPreviewEvent]


class RiskPreviewItem(BaseModel):
    transaction_reference: str

    risk_score: int = Field(
        description="Final fused risk score in [0, 999].",
    )
    rule_score: int = Field(
        description="Deterministic rule engine score in [0, 999].",
    )
    ml_score: int = Field(
        description="ML engine combined score in [0, 999].",
    )
    graph_score: int = Field(
        description="Graph engine score in [0, 999].",
    )

    triggered_rules: List[str] = Field(
        description="List of rule IDs that triggered for this transaction.",
    )
    graph_motifs: Optional[str] = Field(
        default=None,
        description="Graph motifs / patterns contributing to risk.",
    )


class RiskPreviewResponse(BaseModel):
    results: List[RiskPreviewItem]


# -------------------------------------------------------------------
# EXPORT LIST
# -------------------------------------------------------------------

__all__ = [
    # Transactions
    "TransactionResponse",
    "TransactionDirection",
    "TransactionStatus",
    "CreateTransactionRequest",

    # Invoices
    "InvoiceResponse",
    "InvoiceStatus",
    "CreateInvoiceRequest",

    # Alerts
    "AlertResponse",

    # Vendors
    "VendorResponse",
    "VendorRiskLevel",
    "CreateVendorRequest",

    # Employee Expenses
    "EmployeeExpenseResponse",
    "EmployeeExpenseStatus",
    "EmployeeExpenseCategory",
    "CreateEmployeeExpenseRequest",

    # Risk Preview
    "RiskPreviewEvent",
    "RiskPreviewRequest",
    "RiskPreviewItem",
    "RiskPreviewResponse",
]
