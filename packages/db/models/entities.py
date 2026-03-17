# packages/db/models/entities.py
from __future__ import annotations

from enum import Enum
from typing import Optional

from sqlalchemy import Index
from sqlmodel import Field

from packages.db.base import BaseModel
from packages.db.mixins import IDMixin, TimestampMixin


class EntityType(str, Enum):
    PERSON = "PERSON"
    ACCOUNT = "ACCOUNT"
    MERCHANT = "MERCHANT"
    VENDOR = "VENDOR"
    EMPLOYEE = "EMPLOYEE"
    COMPANY = "COMPANY"
    UNKNOWN = "UNKNOWN"


class Entity(BaseModel, IDMixin, TimestampMixin, table=True):
    """
    Entity 360 table.
    NOTE: This is aligned to your CURRENT Postgres schema:
      - entity_id, name, type, risk_score, created_at, updated_at
    """

    __tablename__ = "entities"

    __table_args__ = (
        Index("ix_entities_entity_id", "entity_id"),
        Index("ix_entities_name", "name"),
        Index("ix_entities_type", "type"),
        Index("ix_entities_risk_score", "risk_score"),
    )

    # Business identifier (not DB primary key)
    entity_id: Optional[str] = Field(default=None)

    name: Optional[str] = Field(default=None)

    # Stored as VARCHAR in your DB (character varying)
    type: str = Field(default=EntityType.UNKNOWN.value)

    # UI slider assumes 0–100
    risk_score: int = Field(default=0)
