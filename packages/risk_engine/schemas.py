from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class RuleEngineOutput:
    """
    Output of the deterministic rule engine for a single entity (e.g. transaction).
    """
    score: Optional[int]  # 0–999 or None if not available
    triggered_rules: List[str]  # e.g. ["R_DUPLICATE_INVOICE", "R_HIGH_RISK_VENDOR"]
    explanation: Optional[str] = None  # short human summary


@dataclass
class MLEngineOutput:
    """
    Output of the ML engine (XGBoost + Autoencoder) for a single entity.
    """
    score: Optional[int]  # 0–999 combined ML risk score, or None
    xgb_score: Optional[float] = None  # raw probability [0, 1]
    ae_score: Optional[float] = None   # AE anomaly score, normalized [0, 1]
    explanation: Optional[str] = None  # future: SHAP-based summary


@dataclass
class GraphEngineOutput:
    """
    Output of the graph engine for a single entity.

    Think: relational risk, suspicious communities, high-risk neighbors, etc.
    """
    score: Optional[int]  # 0–999 graph risk score, or None
    motifs: Optional[str] = None  # e.g. "Connected to 3 high-risk vendors"


@dataclass
class FusionConfig:
    """
    Weights for combining rule, ML, and graph scores.

    All weights are optional; missing scores will be handled safely.
    """
    w_rule: float = 0.4
    w_ml: float = 0.4
    w_graph: float = 0.2


@dataclass
class FusionResult:
    """
    Final fused risk outcome for a single entity.
    """
    risk_score: int  # final 0–999 hybrid score

    rule_output: RuleEngineOutput
    ml_output: MLEngineOutput
    graph_output: GraphEngineOutput

    # Optional: short combined explanation (Phase 2.5+)
    explanation: Optional[str] = None
