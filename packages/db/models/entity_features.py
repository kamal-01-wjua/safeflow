from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, DateTime, Index, Numeric
from sqlmodel import Field

from packages.db.base import BaseModel
from packages.db.mixins import IDMixin, TimestampMixin


class EntityFeatures(BaseModel, IDMixin, TimestampMixin, table=True):
    """
    Per-entity feature snapshot updated by the streaming worker on every
    processed transaction.

    Represents the LATEST known state of an entity's behavior — not a
    historical log. Use entity_daily_summary (Phase 3) for time-series.

    Upsert key: (tenant_id, account_id)
    """

    __tablename__ = "entity_features"

    __table_args__ = (
        Index("ix_entity_features_tenant_account", "tenant_id", "account_id", unique=True),
        Index("ix_entity_features_risk_score", "latest_risk_score"),
    )

    # Identity
    tenant_id: int = Field(index=True)
    account_id: str = Field(index=True)

    # --- Volume features ---
    tx_count_total: int = Field(
        default=0,
        description="Total number of transactions processed for this entity.",
    )
    tx_count_24h: int = Field(
        default=0,
        description="Transactions in the last 24 hours (approximated from stream).",
    )
    tx_count_7d: int = Field(
        default=0,
        description="Transactions in the last 7 days (approximated from stream).",
    )

    # --- Amount features ---
    amount_total: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(18, 2), nullable=False, server_default="0.00"),
        description="Cumulative transaction amount.",
    )
    amount_avg: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(18, 2), nullable=False, server_default="0.00"),
        description="Rolling average transaction amount.",
    )
    amount_max: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(18, 2), nullable=False, server_default="0.00"),
        description="Maximum single transaction amount seen.",
    )
    amount_last: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(18, 2), nullable=False, server_default="0.00"),
        description="Amount of the most recent transaction.",
    )

    # --- Risk features ---
    latest_risk_score: int = Field(
        default=0,
        description="Risk score from the most recently processed transaction (0-999).",
    )
    risk_score_avg: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(6, 2), nullable=False, server_default="0.00"),
        description="Rolling average risk score across all transactions.",
    )
    high_risk_tx_count: int = Field(
        default=0,
        description="Count of transactions with risk_score >= 500.",
    )

    # --- Velocity flags ---
    is_velocity_flagged: bool = Field(
        default=False,
        description="True if tx_count_24h exceeds velocity threshold.",
    )
    consecutive_high_risk: int = Field(
        default=0,
        description="Number of consecutive high-risk transactions (resets on low-risk).",
    )

    # --- Temporal ---
    first_seen_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
        description="Timestamp of first transaction processed for this entity.",
    )
    last_seen_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
        description="Timestamp of most recently processed transaction.",
    )
