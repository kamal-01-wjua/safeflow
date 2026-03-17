from __future__ import annotations

from typing import Optional

from packages.risk_engine.schemas import (
    GraphEngineOutput,
)

from .schemas import (
    TransactionGraphContext,
    GraphMetrics,
)

__all__ = [
    "TransactionGraphContext",
    "GraphMetrics",
    "estimate_graph_risk_for_transaction",
]


def _dummy_graph_metrics(ctx: TransactionGraphContext) -> GraphMetrics:
    """
    Placeholder logic that pretends to compute graph metrics.

    For Phase 2 step 1, we just derive a few basic signals:
      - if vendor_code present -> assume some degree / community size
      - if employee_id present -> tweak numbers a bit
    Later:
      - this will be replaced with real queries to Neo4j / graph DB.
    """
    base_degree = 1
    community_size = 1
    pagerank = 0.01
    avg_neighbor_risk = 0.0

    if ctx.vendor_code:
        base_degree += 3
        community_size += 10
        pagerank += 0.05
        avg_neighbor_risk += 0.2

    if ctx.employee_id:
        base_degree += 2
        community_size += 5
        pagerank += 0.03
        avg_neighbor_risk += 0.1

    return GraphMetrics(
        degree=base_degree,
        community_size=community_size,
        pagerank=pagerank,
        avg_neighbor_risk=avg_neighbor_risk,
    )


def _graph_metrics_to_score(metrics: GraphMetrics) -> GraphEngineOutput:
    """
    Convert raw graph metrics into a 0–999 graph risk score.

    Very simple heuristic for now:
      - larger degree + community_size + neighbor_risk => higher score
    """
    degree = metrics.degree or 0
    community_size = metrics.community_size or 0
    pagerank = metrics.pagerank or 0.0
    avg_neighbor_risk = metrics.avg_neighbor_risk or 0.0

    # Very rough scoring formula; will be replaced in Phase 3
    base_score = (
        degree * 5
        + community_size * 2
        + pagerank * 200
        + avg_neighbor_risk * 400
    )

    score_clamped = int(max(0.0, min(999.0, base_score)))

    motifs_parts = []
    if degree >= 5:
        motifs_parts.append(f"High-degree node (degree={degree})")
    if community_size >= 10:
        motifs_parts.append(f"In dense community (size={community_size})")
    if avg_neighbor_risk > 0.1:
        motifs_parts.append("Neighbors show elevated risk")

    motifs = " | ".join(motifs_parts) if motifs_parts else None

    return GraphEngineOutput(
        score=score_clamped,
        motifs=motifs,
    )


def estimate_graph_risk_for_transaction(
    ctx: TransactionGraphContext,
) -> GraphEngineOutput:
    """
    Public function used by the risk pipeline.

    Step 1 (Phase 2):
      - Use dummy metrics derived from simple context fields.
    Later:
      - Replace _dummy_graph_metrics with real graph DB queries.
    """
    metrics = _dummy_graph_metrics(ctx)
    return _graph_metrics_to_score(metrics)
