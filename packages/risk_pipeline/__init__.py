from __future__ import annotations

from typing import Optional

from packages.ml_engine import (
    MLTransactionEvent,
    MLScoreRequest,
)
from packages.rule_engine import evaluate_rules_for_event
from packages.graph_engine import (
    TransactionGraphContext,
    estimate_graph_risk_for_transaction,
)
from packages.risk_engine import (
    RuleEngineOutput,
    MLEngineOutput,
    GraphEngineOutput,
    FusionResult,
    compute_fusion_score,
)

__all__ = [
    "score_single_transaction_event",
]


def _build_ml_output_from_single_event(
    event: MLTransactionEvent,
) -> MLEngineOutput:
    """
    Helper: call the ML engine for a single event and convert
    the response into an MLEngineOutput.
    """
    request = MLScoreRequest(events=[event])
    from packages.ml_engine import predict_transaction_scores  # local import to avoid cycles

    response = predict_transaction_scores(request)
    result = response.results[0]

    return MLEngineOutput(
        score=result.ml_risk_score,
        xgb_score=result.xgb_score,
        ae_score=result.ae_score,
        explanation=None,  # future: summarize SHAP, etc.
    )


def _build_graph_context_from_event(
    event: MLTransactionEvent,
    vendor_code: Optional[str] = None,
    employee_id: Optional[str] = None,
) -> TransactionGraphContext:
    """
    Build a TransactionGraphContext from the MLTransactionEvent.

    For now, we don't yet have vendor_code / employee_id in the event schema,
    so they are passed as optional arguments (to be extended in Phase 2.5+).
    """
    return TransactionGraphContext(
        tenant_id=event.tenant_id,
        transaction_id=event.transaction_id,
        transaction_reference=event.transaction_reference,
        account_id=event.account_id,
        vendor_code=vendor_code,
        employee_id=employee_id,
    )


def score_single_transaction_event(
    event: MLTransactionEvent,
    vendor_code: Optional[str] = None,
    employee_id: Optional[str] = None,
) -> FusionResult:
    """
    High-level scoring pipeline for a single transaction event.

    Steps:
      1. Run deterministic rule engine.
      2. Run ML engine (XGBoost + AE or dummy).
      3. Run graph engine (dummy or real).
      4. Fuse all three into a final risk_score via compute_fusion_score.

    Returns:
      FusionResult containing:
        - final risk_score (0–999)
        - rule_output, ml_output, graph_output
        - combined explanation
    """
    # 1) Rules
    rule_output: RuleEngineOutput = evaluate_rules_for_event(event)

    # 2) ML
    ml_output: MLEngineOutput = _build_ml_output_from_single_event(event)

    # 3) Graph
    graph_ctx = _build_graph_context_from_event(
        event=event,
        vendor_code=vendor_code,
        employee_id=employee_id,
    )
    graph_output: GraphEngineOutput = estimate_graph_risk_for_transaction(graph_ctx)

    # 4) Fusion
    fusion: FusionResult = compute_fusion_score(
        rule_output=rule_output,
        ml_output=ml_output,
        graph_output=graph_output,
    )

    return fusion
