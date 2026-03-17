from datetime import datetime
from enum import Enum
from typing import Optional, Any

from pydantic import BaseModel, Field, field_validator


class TransactionDirection(str, Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    POSTED = "POSTED"
    REVERSED = "REVERSED"
    CANCELLED = "CANCELLED"


class TransactionResponse(BaseModel):
    """
    Public-safe version of a Transaction.
    Returned by API endpoints (e.g. case detail, alerts).
    """

    id: int
    tx_id: str
    account_id: str
    customer_id: Optional[str] = None

    invoice_id: Optional[int] = None

    tx_time: datetime
    booking_time: Optional[datetime] = None

    amount: float = Field(description="Amount as float for clean JSON output.")
    currency: str

    direction: TransactionDirection
    status: TransactionStatus

    country_code: Optional[str] = None
    merchant_category: Optional[str] = None
    channel: Optional[str] = None
    description: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    # ---------- Normalizers for ORM values ----------

    @field_validator("amount", mode="before")
    def normalize_amount(cls, v: Any) -> float:
        """
        DB gives Decimal, we want a plain float in the response model.
        """
        if v is None:
            return 0.0
        return float(v)

    @field_validator("direction", mode="before")
    def normalize_direction(cls, v: Any) -> TransactionDirection:
        """
        Convert DB enum / raw string into our shared enum.
        """
        # Already our enum
        if isinstance(v, TransactionDirection):
            return v

        # Any Enum (e.g. SQLAlchemy enum) → take its .value
        if isinstance(v, Enum):
            v = v.value

        # Expect "DEBIT" or "CREDIT"
        return TransactionDirection(v)

    @field_validator("status", mode="before")
    def normalize_status(cls, v: Any) -> TransactionStatus:
        """
        Convert DB enum / raw string into our shared enum.
        """
        if isinstance(v, TransactionStatus):
            return v

        if isinstance(v, Enum):
            v = v.value

        # Expect "PENDING", "POSTED", "REVERSED", "CANCELLED"
        return TransactionStatus(v)

    class Config:
        from_attributes = True  # enables ORM → response model


class CreateTransactionRequest(BaseModel):
    """
    Data required to create a new Transaction.
    These fields map directly to columns, except ID/timestamps.
    """

    tx_id: str
    account_id: str
    customer_id: Optional[str] = None

    invoice_id: Optional[int] = None

    tx_time: datetime
    booking_time: Optional[datetime] = None

    amount: float = Field(
        description="Amount as float, will be stored as numeric/decimal in the DB."
    )
    currency: str = Field(max_length=3)

    direction: TransactionDirection
    status: TransactionStatus = TransactionStatus.POSTED

    country_code: Optional[str] = None
    merchant_category: Optional[str] = None
    channel: Optional[str] = None
    description: Optional[str] = None

    @field_validator("amount", mode="before")
    def convert_amount(cls, v: Any) -> float:
        # Normalize to float so JSON like "250.0" / "250" / 250 all work cleanly
        return float(v)

    class Config:
        json_schema_extra = {
            "example": {
                "tx_id": "TX-001",
                "account_id": "ACC-123",
                "customer_id": "CUST-999",
                "invoice_id": None,
                "tx_time": "2025-01-01T12:00:00Z",
                "booking_time": None,
                "amount": 249.50,
                "currency": "USD",
                "direction": "DEBIT",
                "status": "POSTED",
                "country_code": "US",
                "merchant_category": "5411",
                "channel": "ONLINE",
                "description": "Grocery purchase",
            }
        }
