from __future__ import annotations

import datetime as dt
from typing import Optional

from sqlalchemy import Column, Text
from sqlmodel import Field

from packages.db.base import BaseModel
from packages.db.mixins import IDMixin, TimestampMixin


class Alert(BaseModel, IDMixin, TimestampMixin, table=True):
    """
    Stored alerts produced by the streaming risk pipeline.
    Backed by the 'alerts' table in Postgres.
    """

    __tablename__ = "alerts"

    # Core identifiers
    tenant_id: int = Field(index=True)
    transaction_id: Optional[int] = Field(default=None, index=True)
    transaction_reference: str = Field(index=True)
    account_id: Optional[str] = Field(default=None, index=True)

    vendor_code: Optional[str] = Field(default=None, index=True)
    employee_id: Optional[str] = Field(default=None, index=True)

    # Fused risk score used across the app (0–999)
    risk_score_0_999: int = Field(
        index=True,
        description="Final fused risk score 0–999",
    )

    # Optional severity band for quick filtering
    severity: Optional[str] = Field(
        default=None,
        index=True,
        description="Optional severity label derived from risk_score_0_999",
    )

    # Engine-level scores aligned to current DB schema
    rule_score: Optional[int] = Field(
        default=None,
        description="Rule engine score stored as integer.",
    )
    ml_score: Optional[int] = Field(
        default=None,
        description="ML engine score stored as integer.",
    )
    graph_score: Optional[int] = Field(
        default=None,
        description="Graph engine score stored as integer.",
    )

    # Explanation fields
    triggered_rules: Optional[str] = Field(
        default=None,
        description="Comma-separated rule IDs: 'R_HIGH_AMOUNT_10K,R_WEEKEND_DEBIT'",
    )

    graph_motifs: Optional[str] = Field(
        default=None,
        description="Short natural-language description of graph motifs",
    )

    # Full rule results, stored as JSON string for Case Detail View
    rule_results_json: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Raw JSON of rule results (list[RuleResult])",
    )

    scored_at: dt.datetime = Field(
        default_factory=dt.datetime.utcnow,
        nullable=False,
        index=True,
        description="When the alert was generated",
    )