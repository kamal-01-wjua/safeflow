from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class TimestampMixin(SQLModel):
    """
    Mixin that adds timestamp fields to a model.
    Each table gets its own created_at / updated_at columns.
    """

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
    )


class IDMixin(SQLModel):
    """
    Simple integer primary key mixin.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
