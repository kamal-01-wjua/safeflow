from __future__ import annotations

from pathlib import Path
import json
from typing import List, Optional

from .schemas import (
    MLTransactionEvent,
    MLScoreRequest,
    MLScoreResult,
    MLScoreResponse,
)
from .features import (
    FeatureVector,
    build_features_for_events,
)

__all__ = [
    "MLTransactionEvent",
    "MLScoreRequest",
    "MLScoreResult",
    "MLScoreResponse",
    "FeatureVector",
    "build_features_for_events",
    "predict_transaction_scores",
]

# --------------------------------------------------------------------
# XGBoost runtime config (optional, safe)
# --------------------------------------------------------------------

_MODEL_PATH = Path("models/xgboost_v2.json")
_FEATURE_SCHEMA_PATH = Path("models/feature_schema_v2.json")

_xgb_model = None          # will hold a Booster if loaded
_xgb_module = None         # will hold the xgboost module if available
_feature_names: Optional[List[str]] = None


def _load_xgb_if_available() -> None:
    """
    Try to lazily load XGBoost model + feature schema.

    Rules:
      - If xgboost is NOT installed -> keep dummy scoring.
      - If model files are missing -> keep dummy scoring.
      - Never raise; just log to stdout and fall back.
    """
    global _xgb_model, _feature_names, _xgb_module

    if _xgb_model is not None and _feature_names is not None and _xgb_module is not None:
        return

    try:
        import xgboost as xgb  # type: ignore
    except ImportError:
        print("[ml_engine] xgboost not installed; using dummy ML scorer.")
        return

    if not _MODEL_PATH.exists():
        print(f"[ml_engine] XGBoost model file not found at {_MODEL_PATH}; using dummy ML scorer.")
        return

    if not _FEATURE_SCHEMA_PATH.exists():
        print(f"[ml_engine] Feature schema not found at {_FEATURE_SCHEMA_PATH}; using dummy ML scorer.")
        return

    try:
        booster = xgb.Booster()
        booster.load_model(str(_MODEL_PATH))

        with open(_FEATURE_SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_records = json.load(f)
            feature_names = [row["feature_name"] for row in schema_records]

    except Exception as exc:  # noqa: BLE001
        print(f"[ml_engine] Failed to load XGBoost model or schema: {exc!r}")
        return

    _xgb_module = xgb
    _xgb_model = booster
    _feature_names = feature_names
    print("[ml_engine] Loaded XGBoost model + feature schema successfully.")


# --------------------------------------------------------------------
# Dummy scorer (used when no real model)
# --------------------------------------------------------------------


def _dummy_score_from_features(
    event: MLTransactionEvent,
    features: FeatureVector,
) -> MLScoreResult:
    """
    Temporary dummy scorer that uses the feature vector.

    This is the fallback when:
      - xgboost is not installed
      - model files are missing
      - loading fails for any reason
    """
    amount_raw = features.get("amount_raw", 0.0)
    base_prob = float(min(max(amount_raw / 10_000.0, 0.0), 1.0))

    xgb_score = base_prob
    ae_score = base_prob * 0.5
    ml_risk_score = int(base_prob * 999)

    return MLScoreResult(
        transaction_reference=event.transaction_reference,
        xgb_score=xgb_score,
        ae_score=ae_score,
        ml_risk_score=ml_risk_score,
        model_version="v2.0.0-dev",
    )


# --------------------------------------------------------------------
# Public entrypoint used by FastAPI
# --------------------------------------------------------------------


def predict_transaction_scores(payload: MLScoreRequest) -> MLScoreResponse:
    """
    Public function used by the FastAPI router.

    Logic:
      1. Build feature vectors from events.
      2. Try to load XGBoost model + schema (lazy).
      3. If model available -> use it to compute xgb_score.
      4. If not -> fall back to dummy scorer.
    """
    feature_vectors = build_features_for_events(payload.events)

    # Try to load model (no-op if already loaded or missing).
    _load_xgb_if_available()

    # If we don't have a model, use dummy for all
    if _xgb_model is None or _feature_names is None or _xgb_module is None:
        results = [
            _dummy_score_from_features(event, features)
            for event, features in zip(payload.events, feature_vectors)
        ]
        return MLScoreResponse(results=results)

    # Real XGBoost path (model + schema available)
    xgb = _xgb_module
    rows = [
        [features.get(name, 0.0) for name in _feature_names]
        for features in feature_vectors
    ]
    dmatrix = xgb.DMatrix(rows, feature_names=_feature_names)
    probs = _xgb_model.predict(dmatrix)

    results: List[MLScoreResult] = []
    for event, prob in zip(payload.events, probs):
        xgb_score = float(prob)
        ae_score = xgb_score * 0.5  # placeholder until real AE is plugged in
        ml_risk_score = int(max(0.0, min(1.0, xgb_score)) * 999)

        results.append(
            MLScoreResult(
                transaction_reference=event.transaction_reference,
                xgb_score=xgb_score,
                ae_score=ae_score,
                ml_risk_score=ml_risk_score,
                model_version="v2.0.0",  # will bump as needed
            )
        )

    return MLScoreResponse(results=results)
