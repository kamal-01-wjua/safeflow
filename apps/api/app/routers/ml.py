from fastapi import APIRouter

from packages.ml_engine import (
    MLScoreRequest,
    MLScoreResponse,
    predict_transaction_scores,
)

router = APIRouter()


@router.post(
    "/score",
    response_model=MLScoreResponse,
    summary="Score transactions with the ML engine (v2 stub)",
)
def score_transactions(payload: MLScoreRequest) -> MLScoreResponse:
    """
    ML scoring endpoint.

    Phase 2 (step 1): returns dummy scores from a simple heuristic.
    Later:
      - call real XGBoost + Autoencoder models
      - add SHAP explanations
      - integrate with fusion engine.
    """
    return predict_transaction_scores(payload)
