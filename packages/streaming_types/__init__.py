from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field


# -------------------------------------------------------------------
# RAW EVENT (as it comes from upstream systems)
# -------------------------------------------------------------------

class RawTransactionEvent(BaseModel):
    """
    Event produced into transactions_raw.

    This should match what an upstream payment/core system can send
    with minimal assumptions.
    """
    event_version: str = Field(
        default="v1",
        description="Schema version for compatibility.",
    )

    tenant_id: Optional[int] = Field(default=None)
    transaction_id: Optional[int] = Field(
        default=None,
        description="Internal ID if available (optional for external sources).",
    )

    transaction_reference: str = Field(
        description="External transaction reference from source system.",
    )
    account_id: str = Field(
        description="Account identifier.",
    )

    amount: Decimal = Field(description="Transaction amount.")
    currency: str = Field(max_length=3, description="ISO currency code.")

    direction: str = Field(
        description="CREDIT or DEBIT (UPPERCASE preferred).",
    )
    status: str = Field(
        description="BOOKED / PENDING / REVERSED etc.",
    )

    timestamp: datetime = Field(
        description="Event timestamp from source system.",
    )

    # Optional context if available upstream
    vendor_code: Optional[str] = Field(default=None)
    employee_id: Optional[str] = Field(default=None)


# -------------------------------------------------------------------
# ENRICHED EVENT (after DB lookups / joins)
# -------------------------------------------------------------------

class EnrichedTransactionEvent(BaseModel):
    """
    Event produced into transactions_enriched.

    This is what the risk scorer consumes. It maps very closely to
    RiskPreviewEvent / MLTransactionEvent schema.
    """
    event_version: str = Field(default="v1")

    # Core
    transaction_id: Optional[int]
    tenant_id: Optional[int]

    transaction_reference: str
    account_id: Optional[str]

    amount: Decimal
    currency: str
    direction: str
    status: str
    timestamp: datetime

    # Enrichment
    vendor_code: Optional[str]
    employee_id: Optional[str]

    vendor_risk_level: Optional[str] = Field(
        default=None,
        description="LOW / MEDIUM / HIGH / CRITICAL if known.",
    )
    vendor_country_code: Optional[str] = None
    is_high_risk_country: Optional[bool] = None


# -------------------------------------------------------------------
# ALERT EVENT (final output of streaming risk pipeline)
# -------------------------------------------------------------------

class AlertEvent(BaseModel):
    """
    Event produced into alerts topic.

    Represents one risk scoring decision for one transaction.
    """
    event_version: str = Field(default="v1")

    tenant_id: Optional[int]
    transaction_id: Optional[int]
    transaction_reference: str

    account_id: Optional[str]
    vendor_code: Optional[str]
    employee_id: Optional[str]

    # Scores
    risk_score: int = Field(description="Final fused risk in [0,999].")
    rule_score: int
    ml_score: int
    graph_score: int

    triggered_rules: List[str] = Field(default_factory=list)
    graph_motifs: Optional[str] = None

    # Timestamps
    scored_at: datetime = Field(
        description="When this alert was produced by the pipeline.",
    )
