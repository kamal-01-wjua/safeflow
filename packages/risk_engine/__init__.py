from __future__ import annotations

from typing import Optional

from .schemas import (
    RuleEngineOutput,
    MLEngineOutput,
    GraphEngineOutput,
    FusionConfig,
    FusionResult,
)

__all__ = [
    "RuleEngineOutput",
    "MLEngineOutput",
    "GraphEngineOutput",
    "FusionConfig",
    "FusionResult",
    "compute_fusion_score",
]


def _norm(score: Optional[int]) -> Optional[float]:
    """
    Normalize a 0–999 score to [0, 1].

    Returns None if score is None.
    """
    if score is None:
        return None
    # clamp to [0, 999] for safety
    s = max(0, min(999, score))
    return s / 999.0


def compute_fusion_score(
    rule_output: RuleEngineOutput,
    ml_output: MLEngineOutput,
    graph_output: GraphEngineOutput,
    config: Optional[FusionConfig] = None,
) -> FusionResult:
    """
    Compute the final fused risk score for a single entity.

    Rules:
      - Each source produces a score in [0, 999] or None.
      - We normalize to [0, 1], then combine with weights.
      - If a source is missing (score=None), its weight is
        removed and remaining weights are renormalized.
      - If *all* scores are missing, final risk_score = 0.

    This makes the engine robust:
      - You can roll out components gradually (e.g. rule+ML first, graph later).
      - If ML is down, rule+graph still work.
    """
    if config is None:
        config = FusionConfig()

    rule_norm = _norm(rule_output.score)
    ml_norm = _norm(ml_output.score)
    graph_norm = _norm(graph_output.score)

    # Collect available components
    components = []
    if rule_norm is not None:
        components.append(("rule", rule_norm, config.w_rule))
    if ml_norm is not None:
        components.append(("ml", ml_norm, config.w_ml))
    if graph_norm is not None:
        components.append(("graph", graph_norm, config.w_graph))

    if not components:
        # No scores at all -> default to 0
        return FusionResult(
            risk_score=0,
            rule_output=rule_output,
            ml_output=ml_output,
            graph_output=graph_output,
            explanation="No risk signals available; defaulting to low risk.",
        )

    # Renormalize weights only over available components
    total_weight = sum(weight for _, _, weight in components)
    if total_weight <= 0:
        # sanity fallback
        total_weight = 1.0

    fused_value = 0.0
    for name, score_norm, weight in components:
        weight_adj = weight / total_weight
        fused_value += score_norm * weight_adj

    fused_value_clamped = max(0.0, min(1.0, fused_value))
    fused_score_int = int(round(fused_value_clamped * 999))

    # Simple combined explanation stub (can be improved later)
    explanation_parts = []
    if rule_output.score is not None:
        explanation_parts.append(f"Rules={rule_output.score}")
    if ml_output.score is not None:
        explanation_parts.append(f"ML={ml_output.score}")
    if graph_output.score is not None:
        explanation_parts.append(f"Graph={graph_output.score}")
    explanation = " | ".join(explanation_parts) if explanation_parts else None

    return FusionResult(
        risk_score=fused_score_int,
        rule_output=rule_output,
        ml_output=ml_output,
        graph_output=graph_output,
        explanation=explanation,
    )
