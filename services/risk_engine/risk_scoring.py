from __future__ import annotations

from typing import List, Sequence

from .rule_engine import RuleEvaluationContext, RuleResult, RuleFunc


# ---------------------------------------------------------
# 🟦 Example rules (safe, generic, v1)
# ---------------------------------------------------------
def _rule_high_amount(ctx: RuleEvaluationContext) -> RuleResult:
    """
    Trigger if transaction.amount is very large.
    Uses getattr() so it won't crash if the field is missing.
    """
    amount = getattr(ctx.transaction, "amount", 0) or 0
    try:
        amount_val = float(amount)
    except Exception:
        amount_val = 0.0

    triggered = amount_val >= 100_000
    score = 0.9 if triggered else 0.1
    reasons: List[str] = []

    if triggered:
        reasons.append(f"High amount detected: {amount_val}")

    return RuleResult(
        rule_name="high_amount",
        triggered=triggered,
        score=score,
        reasons=reasons,
    )


def _rule_vendor_risk(ctx: RuleEvaluationContext) -> RuleResult:
    """
    Example vendor-risk rule: if there is a vendor_risk_score field and it's high.
    """
    vendor_risk = getattr(ctx.transaction, "vendor_risk_score", None)

    triggered = bool(vendor_risk is not None and float(vendor_risk) >= 0.8)
    try:
        score = float(vendor_risk) if vendor_risk is not None else 0.05
    except Exception:
        score = 0.05

    reasons: List[str] = []
    if triggered:
        reasons.append(f"Vendor risk score={vendor_risk}")

    return RuleResult(
        rule_name="vendor_risk",
        triggered=triggered,
        score=score,
        reasons=reasons,
    )


def get_rules() -> List[RuleFunc]:
    """
    Return the active rule-set for Phase 1.
    Later we can swap this to a config-driven registry.
    """
    return [
        _rule_high_amount,
        _rule_vendor_risk,
    ]


# ---------------------------------------------------------
# 🟦 Aggregation & fusion helpers
# ---------------------------------------------------------
def compute_rule_score(results: Sequence[RuleResult]) -> float:
    """
    Aggregate individual RuleResult scores into a single [0, 1] rule_score.

    Simple approach:
      - triggered rules get weight 2.0
      - non-triggered rules get weight 1.0
    """
    if not results:
        return 0.0

    total = 0.0
    weight_sum = 0.0

    for res in results:
        weight = 2.0 if res.triggered else 1.0
        total += float(res.score) * weight
        weight_sum += weight

    if weight_sum <= 0:
        return 0.0

    value = total / weight_sum
    # Clamp to [0, 1]
    value = max(0.0, min(1.0, value))
    return value


def compute_fused_risk_0_999(rule_score: float, anomaly_score: float) -> int:
    """
    Combine rule_score and anomaly_score into an integer 0–999.

    Simple v1: 50/50 average, then scale.
    """
    r = float(rule_score)
    a = float(anomaly_score)

    fused = 0.5 * r + 0.5 * a
    fused = max(0.0, min(1.0, fused))

    return int(round(fused * 999))
