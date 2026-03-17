from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, DateTime, Index, Numeric, UniqueConstraint
from sqlmodel import Field

from packages.db.base import BaseModel
from packages.db.mixins import IDMixin, TimestampMixin

if TYPE_CHECKING:
    from .invoices import Invoice


class TransactionDirection(str, Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    POSTED = "POSTED"
    REVERSED = "REVERSED"
    CANCELLED = "CANCELLED"


class Transaction(BaseModel, IDMixin, TimestampMixin, table=True):
    """
    Core transactions table.
    Designed for:
      - duplicate detection
      - frequency spikes
      - vendor/anomaly rules
      - ML + graph features
    """

    __tablename__ = "transactions"

    __table_args__ = (
        Index("ix_transactions_tenant_time", "tenant_id", "tx_time"),
        Index("ix_transactions_account_time", "account_id", "tx_time"),
        Index("ix_transactions_invoice_id", "invoice_id"),
        UniqueConstraint("tenant_id", "tx_id", name="uq_transactions_tenant_tx_id"),
    )

    # Multi-tenant ready
    tenant_id: Optional[int] = Field(default=None, index=True)

    # Business identifiers
    tx_id: str = Field(
        index=True,
        description="External/business transaction ID from source system.",
    )
    account_id: str = Field(index=True, description="Primary account affected.")
    customer_id: Optional[str] = Field(
        default=None,
        index=True,
        description="Optional customer identifier.",
    )

    # Link to invoice if any
    invoice_id: Optional[int] = Field(
        default=None,
        foreign_key="invoices.id",
    )

    # Time info
    tx_time: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            index=True,
        ),
        description="When the transaction occurred (UTC).",
    )

    booking_time: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
        description="When the transaction was booked/posted (UTC).",
    )

    # Monetary info
    amount: Decimal = Field(
        sa_column=Column(Numeric(18, 2), nullable=False),
        description="Signed amount.",
    )
    currency: str = Field(
        max_length=3,
        description="ISO 4217 currency code, e.g. 'USD', 'EUR'.",
    )

    direction: TransactionDirection = Field(
        description="DEBIT or CREDIT direction.",
    )

    status: TransactionStatus = Field(
        default=TransactionStatus.POSTED,
        description="Lifecycle status of the transaction.",
    )

    # Context for rules & graph
    country_code: Optional[str] = Field(
        default=None,
        max_length=2,
        description="ISO 3166-1 alpha-2 country code.",
    )
    merchant_category: Optional[str] = Field(
        default=None,
        max_length=8,
        description="Merchant category / GL code / MCC.",
    )
    channel: Optional[str] = Field(
        default=None,
        max_length=32,
        description="Channel: ONLINE, POS, ATM, MOBILE, INTERNAL, etc.",
    )
    description: Optional[str] = Field(
        default=None,
        description="Free-text description / narration.",
    )

    # Relationship intentionally left disabled for now to avoid typing issues.
    # invoice: Optional["Invoice"] = Relationship(back_populates="transactions")