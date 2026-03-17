from __future__ import annotations

from typing import Any


class IForestNotTrainedError(Exception):
    """Raised when the Isolation Forest model is not available (placeholder)."""


def score_transaction_iforest(tx: Any) -> float:
    """
    TEMP v1 stub implementation.

    For Phase 1 we just need a stable anomaly score in [0, 1] so that the
    endpoint works and the fusion logic can be tested.

    Later we will replace this with a real trained Isolation Forest model
    loaded from disk or a model service.
    """
    raw = getattr(tx, "id", None) or getattr(tx, "transaction_id", None) or 0

    try:
        raw_int = int(raw)
    except Exception:
        raw_int = 0

    # Deterministic pseudo-score in [0, 1]
    return (raw_int % 100) / 100.0
