from fastapi import APIRouter

from packages.shared_types import (
    RiskPreviewRequest,
    RiskPreviewResponse,
    RiskPreviewItem,
)
from packages.ml_engine import MLTransactionEvent
from packages.risk_pipeline import score_single_transaction_event

router = APIRouter()


@router.post(
    "/preview",
    response_model=RiskPreviewResponse,
    summary="Preview fused risk score (rules + ML + graph) for transactions",
)
def risk_preview(payload: RiskPreviewRequest) -> RiskPreviewResponse:
    """
    High-level risk preview endpoint.

    For each event:
      1. Convert to MLTransactionEvent.
      2. Run rule engine + ML engine + graph engine via risk_pipeline.
      3. Return fused risk_score and sub-scores.
    """
    results = []

    for evt in payload.events:
        ml_event = MLTransactionEvent(
            transaction_id=evt.transaction_id,
            tenant_id=evt.tenant_id,
            transaction_reference=evt.transaction_reference,
            account_id=evt.account_id,
            amount=evt.amount,
            currency=evt.currency,
            direction=evt.direction,
            status=evt.status,
            timestamp=evt.timestamp,
        )

        fusion = score_single_transaction_event(
            event=ml_event,
            vendor_code=evt.vendor_code,
            employee_id=evt.employee_id,
        )

        item = RiskPreviewItem(
            transaction_reference=evt.transaction_reference,
            risk_score=fusion.risk_score,
            rule_score=fusion.rule_output.score or 0,
            ml_score=fusion.ml_output.score or 0,
            graph_score=fusion.graph_output.score or 0,
            triggered_rules=fusion.rule_output.triggered_rules,
            graph_motifs=fusion.graph_output.motifs,
        )
        results.append(item)

    return RiskPreviewResponse(results=results)
