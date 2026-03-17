from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session

from packages.db.session import get_session
from packages.db.models import Transaction

from services.risk_engine.rule_engine import (
    RuleEvaluationContext,
    RuleResult,
    evaluate_rules,
)
from services.risk_engine.ml_engine import (
    score_transaction_iforest,
    IForestNotTrainedError,
)
from services.risk_engine.risk_scoring import (
    get_rules,
    compute_rule_score,
    compute_fused_risk_0_999,
)

router = APIRouter()


# ---------------------------------------------------------
# 🟦 Response models
# ---------------------------------------------------------
class RiskScoreResponse(BaseModel):
    transaction_id: int = Field(..., description="Internal transaction ID")
    rule_score: float = Field(
        ..., ge=0.0, le=1.0, description="Aggregated rule-based risk score (0-1)"
    )
    results: List[RuleResult]


class MLRiskScoreResponse(BaseModel):
    transaction_id: int = Field(..., description="Internal transaction ID")
    anomaly_score: float = Field(
        ..., ge=0.0, le=1.0, description="ML anomaly score (0-1, higher = more anomalous)"
    )


class CombinedRiskResponse(BaseModel):
    """
    v1 fusion output:
      - rule_score: [0,1]
      - anomaly_score: [0,1]
      - risk_score_0_999: integer 0–999 for UI display
    """

    transaction_id: int

    rule_score: float = Field(
        ..., ge=0.0, le=1.0, description="Rule-based risk score (0-1)"
    )
    anomaly_score: float = Field(
        ..., ge=0.0, le=1.0, description="ML anomaly score (0-1)"
    )
    risk_score_0_999: int = Field(
        ..., ge=0, le=999, description="Fused overall risk score (0–999)"
    )

    rule_results: List[RuleResult]


# ---------------------------------------------------------
# 🟦 Endpoint: rule-based risk for a transaction
# ---------------------------------------------------------
@router.get(
    "/transactions/{tx_id}",
    response_model=RiskScoreResponse,
    summary="Compute rule-based risk score for a transaction",
)
def risk_score_for_transaction(
    tx_id: int,
    session: Session = Depends(get_session),
):
    tx = session.get(Transaction, tx_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    rules = get_rules()
    ctx = RuleEvaluationContext(
        transaction=tx,
        invoice=tx.invoice,
        session=session,
    )

    results = evaluate_rules(rules, ctx)
    rule_score = compute_rule_score(results)

    return RiskScoreResponse(
        transaction_id=tx_id,
        rule_score=rule_score,
        results=results,
    )


# ---------------------------------------------------------
# 🟦 Endpoint: ML-based anomaly score for a transaction
# ---------------------------------------------------------
@router.get(
    "/ml/transactions/{tx_id}",
    response_model=MLRiskScoreResponse,
    summary="Compute ML-based anomaly score (Isolation Forest) for a transaction",
)
def ml_risk_score_for_transaction(
    tx_id: int,
    session: Session = Depends(get_session),
):
    tx = session.get(Transaction, tx_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    try:
        anomaly_score = score_transaction_iforest(tx)
    except IForestNotTrainedError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Isolation Forest model not available: {e}",
        )

    return MLRiskScoreResponse(
        transaction_id=tx_id,
        anomaly_score=anomaly_score,
    )


# ---------------------------------------------------------
# 🟦 Endpoint: Combined rule + ML risk for a transaction
# ---------------------------------------------------------
@router.get(
    "/combined/transactions/{tx_id}",
    response_model=CombinedRiskResponse,
    summary="Compute combined (rule + ML) risk score for a transaction",
)
def combined_risk_for_transaction(
    tx_id: int,
    session: Session = Depends(get_session),
):
    tx = session.get(Transaction, tx_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # 1) Rule engine
    rules = get_rules()
    ctx = RuleEvaluationContext(
        transaction=tx,
        invoice=tx.invoice,
        session=session,
    )
    rule_results = evaluate_rules(rules, ctx)
    rule_score = compute_rule_score(rule_results)

    # 2) ML engine
    try:
        anomaly_score = score_transaction_iforest(tx)
    except IForestNotTrainedError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Isolation Forest model not available: {e}",
        )

    # 3) Fusion
    fused_0_999 = compute_fused_risk_0_999(rule_score, anomaly_score)

    return CombinedRiskResponse(
        transaction_id=tx_id,
        rule_score=rule_score,
        anomaly_score=anomaly_score,
        risk_score_0_999=fused_0_999,
        rule_results=rule_results,
    )
