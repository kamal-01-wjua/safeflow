from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AlertResponse(BaseModel):
    id: int
    transaction_id: int

    rule_score: float = Field(ge=0.0, le=1.0)
    anomaly_score: float = Field(ge=0.0, le=1.0)
    risk_score_0_999: int = Field(ge=0, le=999)

    top_rule_code: Optional[str] = None
    top_rule_message: Optional[str] = None
    severity: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
