from __future__ import annotations

from datetime import datetime
from math import log1p
from typing import Dict, List

from .schemas import MLTransactionEvent

# Simple alias for now; later we can make this a TypedDict or Pydantic model
FeatureVector = Dict[str, float]


def build_feature_vector(event: MLTransactionEvent) -> FeatureVector:
    """
    Build a numeric feature vector for a single transaction event.

    This is the *single source of truth* for ML features.
    Training and inference must both use this logic.
    """
    ts: datetime = event.timestamp

    hour = ts.hour
    day_of_week = ts.weekday()  # Monday=0, Sunday=6
    is_weekend = 1.0 if day_of_week >= 5 else 0.0

    # Amount features
    amount_raw = float(event.amount)
    amount_non_negative = max(amount_raw, 0.0)
    amount_log = float(log1p(amount_non_negative))

    # Direction
    direction_upper = event.direction.upper()
    direction_is_credit = 1.0 if direction_upper == "CREDIT" else 0.0

    # Placeholders for future context features (vendor, employee, etc.)
    vendor_risk_level_num = 0.0
    has_employee_expense_link = 0.0

    return {
        "amount_raw": amount_raw,
        "amount_log": amount_log,
        "hour_of_day": float(hour),
        "day_of_week": float(day_of_week),
        "is_weekend": is_weekend,
        "direction_is_credit": direction_is_credit,
        # Future extension points:
        "vendor_risk_level_num": vendor_risk_level_num,
        "has_employee_expense_link": has_employee_expense_link,
    }


def build_features_for_events(events: List[MLTransactionEvent]) -> List[FeatureVector]:
    """
    Build feature vectors for a batch of events.
    """
    return [build_feature_vector(evt) for evt in events]
