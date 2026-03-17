from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class MLTransactionEvent(BaseModel):
    """
    Minimal transaction context sent to the ML engine.

    Later we can extend this with more fields (vendor_code, expense_reference, etc.).
    """
    transaction_id: Optional[int] = Field(
        default=None,
        description="Internal transaction ID if available.",
    )
    tenant_id: Optional[int] = Field(
        default=None,
        description="Tenant identifier for multi-tenant setups.",
    )

    transaction_reference: str = Field(
        description="External transaction reference from source system.",
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
        description="Transaction direction, e.g. CREDIT or DEBIT.",
    )
    status: str = Field(
        description="Transaction status, e.g. BOOKED or PENDING.",
    )

    timestamp: datetime = Field(
        description="Timestamp of the transaction.",
    )


class MLScoreRequest(BaseModel):
    """
    Request payload for /ml/score.
    """
    events: List[MLTransactionEvent]


class MLScoreResult(BaseModel):
    transaction_reference: str

    xgb_score: float = Field(
        description="XGBoost probability score in [0, 1].",
    )
    ae_score: float = Field(
        description="Autoencoder anomaly score (scaled to [0, 1] for now).",
    )
    ml_risk_score: int = Field(
        description="Combined ML risk score in [0, 999].",
    )
    model_version: str = Field(
        description="Version identifier of the ML engine.",
    )


class MLScoreResponse(BaseModel):
    results: List[MLScoreResult]
