from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional

from sqlalchemy import Column, Date, Index, UniqueConstraint
from sqlmodel import Field

from packages.db.base import BaseModel
from packages.db.mixins import IDMixin, TimestampMixin


class VendorRiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Vendor(BaseModel, IDMixin, TimestampMixin, table=True):
    """
    Vendors master table.

    Optimized for:
      - duplicate invoice rules (same vendor, same amount, windowed)
      - vendor risk profiling (country, category, sanctions in future phases)
      - graph engine (vendor <-> employee <-> transaction relationships)
    """

    __tablename__ = "vendors"

    __table_args__ = (
        # Fast lookup by tenant + vendor_code (used in invoices/expenses/transactions)
        Index(
            "ix_vendors_tenant_vendor_code",
            "tenant_id",
            "vendor_code",
        ),
        UniqueConstraint(
            "tenant_id",
            "vendor_code",
            name="uq_vendors_tenant_vendor_code",
        ),
    )

    # Multi-tenant alignment with other tables
    tenant_id: Optional[int] = Field(default=None, index=True)

    # Business identifiers
    vendor_code: str = Field(
        index=True,
        description="Business/vendor code as used in source systems and invoices.",
    )

    name: str = Field(
        description="Official vendor name.",
    )

    # Basic profile
    country_code: Optional[str] = Field(
        default=None,
        max_length=2,
        description="ISO 3166-1 alpha-2 country code.",
    )
    city: Optional[str] = Field(
        default=None,
        max_length=64,
        description="City where the vendor is registered or primarily operates.",
    )
    tax_id: Optional[str] = Field(
        default=None,
        max_length=64,
        description="Tax/VAT registration number where applicable.",
    )

    industry: Optional[str] = Field(
        default=None,
        max_length=64,
        description="High-level industry or category (e.g. IT_SERVICES, CONSTRUCTION).",
    )

    # Governance & risk
    risk_level: Optional[VendorRiskLevel] = Field(
        default=None,
        description="Internal risk classification for this vendor.",
    )
    onboarding_date: Optional[date] = Field(
        default=None,
        sa_column=Column(Date, nullable=True),
        description="Date vendor was onboarded/approved.",
    )
    is_active: bool = Field(
        default=True,
        description="Whether the vendor is currently active/allowed.",
    )

    notes: Optional[str] = Field(
        default=None,
        description="Free-text notes (e.g. risk comments, watchlist hits in Phase 3).",
    )

    # Relationships
    # In Phase 2/3 we may enable relationships to invoices/expenses
    # while keeping SQLAlchemy 2.0 typing issues in mind.
    # invoices: list["Invoice"] = Relationship(back_populates="vendor")
