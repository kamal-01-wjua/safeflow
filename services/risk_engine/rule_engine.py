from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, List, Sequence

from pydantic import BaseModel
from sqlmodel import Session


@dataclass
class RuleEvaluationContext:
    """
    Context passed into each rule.

    We keep this very generic so it won't crash even if the Transaction / Invoice
    models change – rules must defensively use getattr().
    """

    transaction: Any
    invoice: Any | None = None
    session: Session | None = None


class RuleResult(BaseModel):
    """
    Result of a single rule evaluation.
    This is what the API serialises back to the client.
    """

    rule_name: str
    triggered: bool
    score: float
    reasons: List[str] = []


# A rule is any callable that takes a context and returns a RuleResult
RuleFunc = Callable[[RuleEvaluationContext], RuleResult]


def evaluate_rules(
    rules: Sequence[RuleFunc],
    ctx: RuleEvaluationContext,
) -> List[RuleResult]:
    """
    Safely evaluate all rules and collect their results.

    If a rule crashes, we catch the exception and return a synthetic RuleResult
    instead of killing the whole request.
    """
    results: List[RuleResult] = []

    for rule in rules:
        try:
            result = rule(ctx)
        except Exception as exc:  # pragma: no cover - defensive fallback
            result = RuleResult(
                rule_name=getattr(rule, "__name__", "unknown_rule"),
                triggered=False,
                score=0.0,
                reasons=[f"rule_error: {exc}"],
            )
        results.append(result)

    return results
