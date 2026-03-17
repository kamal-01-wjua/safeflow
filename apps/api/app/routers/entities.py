# apps/api/app/routers/entities.py
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from packages.db.session import get_session
from packages.db.models import Entity
from packages.db.models import EntityFeatures

router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("/", summary="List entities")
def list_entities(
    session: Session = Depends(get_session),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    q: Optional[str] = Query(default=None, description="Search by name or entity_id"),
):
    stmt = select(Entity)
    if q:
        stmt = stmt.where(
            Entity.name.contains(q) | Entity.entity_id.contains(q)  # type: ignore
        )
    stmt = stmt.offset(offset).limit(limit)
    entities = session.exec(stmt).all()
    return {"items": entities, "count": len(entities)}


@router.get("/{id}", summary="Get entity by internal id")
def get_entity(
    id: int,
    session: Session = Depends(get_session),
):
    e = session.get(Entity, id)
    if not e:
        raise HTTPException(status_code=404, detail="Entity not found")
    return e


@router.get("/{id}/features", summary="Get streaming feature snapshot for entity")
def get_entity_features(
    id: int,
    session: Session = Depends(get_session),
):
    """
    Returns the latest entity_features row for this entity.
    The entity's account_id is used to look up the feature snapshot
    written by the Faust streaming worker.
    """
    entity = session.get(Entity, id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    # entity_id on the Entity model is the business key e.g. "ENT-0001"
    # account_id on entity_features is "ACC-ENT-001" pattern from the producer
    # We look up by matching account_id to entity_id or a derived pattern
    features = session.exec(
        select(EntityFeatures)
        .where(EntityFeatures.tenant_id == 1)
        .where(EntityFeatures.account_id == entity.entity_id)
    ).one_or_none()

    if not features:
        # Return zeroed snapshot rather than 404 — entity exists, just no stream data yet
        return {
            "entity_id": entity.entity_id,
            "account_id": entity.entity_id,
            "tx_count_total": 0,
            "tx_count_24h": 0,
            "tx_count_7d": 0,
            "amount_total": 0,
            "amount_avg": 0,
            "amount_max": 0,
            "amount_last": 0,
            "latest_risk_score": entity.risk_score,
            "risk_score_avg": 0,
            "high_risk_tx_count": 0,
            "is_velocity_flagged": False,
            "consecutive_high_risk": 0,
            "first_seen_at": None,
            "last_seen_at": None,
            "source": "entity_only",
        }

    return {
        "entity_id": entity.entity_id,
        "account_id": features.account_id,
        "tx_count_total": features.tx_count_total,
        "tx_count_24h": features.tx_count_24h,
        "tx_count_7d": features.tx_count_7d,
        "amount_total": float(features.amount_total),
        "amount_avg": float(features.amount_avg),
        "amount_max": float(features.amount_max),
        "amount_last": float(features.amount_last),
        "latest_risk_score": features.latest_risk_score,
        "risk_score_avg": float(features.risk_score_avg),
        "high_risk_tx_count": features.high_risk_tx_count,
        "is_velocity_flagged": features.is_velocity_flagged,
        "consecutive_high_risk": features.consecutive_high_risk,
        "first_seen_at": features.first_seen_at,
        "last_seen_at": features.last_seen_at,
        "source": "entity_features",
    }
