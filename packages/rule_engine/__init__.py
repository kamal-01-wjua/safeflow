from __future__ import annotations

from datetime import datetime
from typing import List

from packages.ml_engine import MLTransactionEvent
from packages.risk_engine.schemas import RuleEngineOutput

__all__ = [
    "evaluate_rules_for_event",
]


def _is_weekend(ts: datetime) -> bool:
    # Monday = 0, Sunday = 6
    return ts.weekday() >= 5


def evaluate_rules_for_event(event: MLTransactionEvent) -> RuleEngineOutput:
    """
    Very simple deterministic rule engine for a single transaction event.

    Phase 2 - step 1:
      - We only use basic properties (amount, time, direction).
      - Later, we will expand with vendor, employee, history windows, etc.

    Output:
      - score in [0, 999]
      - list of triggered rule IDs
      - short explanation string
    """
    triggered_rules: List[str] = []
    score = 0

    amount = float(event.amount)
    ts = event.timestamp
    direction = event.direction.upper()

    # R_HIGH_AMOUNT_10K: amount >= 10,000
    if amount >= 10_000:
        triggered_rules.append("R_HIGH_AMOUNT_10K")
        score += 300

    # R_WEEKEND_DEBIT: debit transactions on weekend
    if _is_weekend(ts) and direction == "DEBIT":
        triggered_rules.append("R_WEEKEND_DEBIT")
        score += 200

    # R_LARGE_NIGHT_TXN: high amount late at night
    if ts.hour >= 22 or ts.hour <= 5:
        if amount >= 5_000:
            triggered_rules.append("R_LARGE_NIGHT_TXN")
            score += 250

    # clamp to [0, 999]
    score = max(0, min(999, score))

    if triggered_rules:
        explanation = "; ".join(triggered_rules)
    else:
        explanation = "No deterministic rules triggered."

    return RuleEngineOutput(
        score=score if triggered_rules else 0,
        triggered_rules=triggered_rules,
        explanation=explanation,
    )
