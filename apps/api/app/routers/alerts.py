from typing import List, Optional
import datetime as dt
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session, select, func

from packages.db.session import get_session
from packages.db.models import Alert, Transaction
from packages.shared_types.transactions import TransactionResponse
from services.risk_engine.rule_engine import RuleResult


router = APIRouter()


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------


def _parse_triggered_rules(value: Optional[str]) -> List[str]:
    """
    DB stores triggered_rules as string (e.g. "A,B,C" or "").
    API returns it as list[str] for clean UI rendering.
    Also tolerates JSON list strings if that ever happens.
    """
    if not value:
        return []

    v = value.strip()

    # tolerate JSON list
    if v.startswith("[") and v.endswith("]"):
        try:
            raw = json.loads(v)
            if isinstance(raw, list):
                return [str(x).strip() for x in raw if str(x).strip()]
        except Exception:
            pass

    # CSV
    parts = [p.strip() for p in v.split(",")]
    return [p for p in parts if p]


def _to_alert_response(a: Alert) -> "AlertResponse":
    """
    Convert ORM Alert -> AlertResponse (and normalize triggered_rules).
    """
    return AlertResponse(
        id=a.id,
        tenant_id=a.tenant_id,
        transaction_id=a.transaction_id,
        transaction_reference=a.transaction_reference,
        account_id=a.account_id,
        vendor_code=a.vendor_code,
        employee_id=a.employee_id,
        risk_score_0_999=a.risk_score_0_999,
        severity=a.severity,
        rule_score=a.rule_score,
        ml_score=a.ml_score,
        graph_score=a.graph_score,
        triggered_rules=_parse_triggered_rules(a.triggered_rules),
        graph_motifs=a.graph_motifs,
        scored_at=a.scored_at,
        created_at=a.created_at,
    )


def _to_transaction_response(tx: Transaction) -> TransactionResponse:
    """
    Make TransactionResponse validation robust across:
    - Pydantic BaseModel expecting dict
    - Pydantic v2 from_attributes mode
    - SQLModel objects
    """
    # This is the path we proved works in the REPL
    try:
        return TransactionResponse.model_validate(tx, from_attributes=True)
    except Exception:
        pass

    # Fallback: if tx has model_dump (SQLModel), try that
    try:
        return TransactionResponse.model_validate(tx.model_dump())
    except Exception as e:
        # If this fails, we raise a clean 500 with a clear message
        raise HTTPException(
            status_code=500,
            detail=f"TransactionResponse validation failed: {type(e).__name__}",
        )


# ---------------------------------------------------------
# DTOs / Response Models
# ---------------------------------------------------------


class AlertSummaryResponse(BaseModel):
    total_alerts: int = Field(..., description="Total number of alerts in the system")
    high_risk_alerts: int = Field(..., description="Alerts with risk_score_0_999 >= 700")
    critical_alerts: int = Field(..., description="Alerts with risk_score_0_999 >= 850")
    avg_risk_score: Optional[float] = Field(
        default=None,
        description="Average risk_score_0_999 across all alerts (or null if none)",
    )


class AlertResponse(BaseModel):
    id: int
    tenant_id: int
    transaction_id: int
    transaction_reference: str

    account_id: Optional[str] = None
    vendor_code: Optional[str] = None
    employee_id: Optional[str] = None

    risk_score_0_999: int
    severity: str

    rule_score: Optional[int] = None
    ml_score: Optional[int] = None
    graph_score: Optional[int] = None

    triggered_rules: List[str] = Field(default_factory=list)
    graph_motifs: Optional[str] = None

    scored_at: Optional[dt.datetime] = None
    created_at: Optional[dt.datetime] = None


class AlertDetailResponse(BaseModel):
    alert: AlertResponse
    transaction: TransactionResponse
    rule_results: List[RuleResult]


# ---------------------------------------------------------
# Summary (keep before /{id})
# ---------------------------------------------------------


@router.get(
    "/summary",
    response_model=AlertSummaryResponse,
    summary="Summary stats for alerts (for KPI header)",
)
def alerts_summary(session: Session = Depends(get_session)):
    total_alerts = session.exec(select(func.count()).select_from(Alert)).one()

    high_risk_alerts = session.exec(
        select(func.count()).select_from(Alert).where(Alert.risk_score_0_999 >= 700)
    ).one()

    critical_alerts = session.exec(
        select(func.count()).select_from(Alert).where(Alert.risk_score_0_999 >= 850)
    ).one()

    avg_risk = session.exec(select(func.avg(Alert.risk_score_0_999))).one()
    avg_risk_value: Optional[float] = float(avg_risk) if avg_risk is not None else None

    return AlertSummaryResponse(
        total_alerts=total_alerts,
        high_risk_alerts=high_risk_alerts,
        critical_alerts=critical_alerts,
        avg_risk_score=avg_risk_value,
    )


# ---------------------------------------------------------
# List alerts
# ---------------------------------------------------------


@router.get(
    "/",
    response_model=List[AlertResponse],
    summary="List alerts for Analyst Dashboard",
)
def list_alerts(
    session: Session = Depends(get_session),
    min_risk: Optional[int] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    stmt = select(Alert)

    if min_risk is not None:
        stmt = stmt.where(Alert.risk_score_0_999 >= min_risk)

    if severity is not None:
        stmt = stmt.where(Alert.severity == severity)

    stmt = stmt.order_by(Alert.risk_score_0_999.desc(), Alert.created_at.desc())
    stmt = stmt.offset(offset).limit(limit)

    alerts = session.exec(stmt).all()
    return [_to_alert_response(a) for a in alerts]


# ---------------------------------------------------------
# Get single alert
# ---------------------------------------------------------


@router.get(
    "/{alert_id}",
    response_model=AlertResponse,
    summary="Get a single alert by ID (summary)",
)
def get_alert(alert_id: int, session: Session = Depends(get_session)):
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return _to_alert_response(alert)


# ---------------------------------------------------------
# Get alert + transaction + rules
# ---------------------------------------------------------


@router.get(
    "/{alert_id}/detail",
    response_model=AlertDetailResponse,
    summary="Get alert + transaction + rule breakdown",
)
def get_alert_detail(alert_id: int, session: Session = Depends(get_session)):
    # 1) Load alert
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # 2) Load the linked transaction as a proper ORM row
    tx = session.get(Transaction, alert.transaction_id)
    if not tx:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction with id={alert.transaction_id} linked to alert not found",
        )

    # 3) Convert to clean response models
    alert_resp = _to_alert_response(alert)
    tx_resp = _to_transaction_response(tx)

    # 4) Parse rule_results_json into List[RuleResult]
    rule_results: List[RuleResult] = []
    raw_rr = alert.rule_results_json

    if raw_rr:
        try:
            parsed = json.loads(raw_rr)
            if isinstance(parsed, list):
                for item in parsed:
                    try:
                        rule_results.append(RuleResult.model_validate(item))
                    except Exception:
                        # Ignore bad entries instead of killing the whole endpoint
                        continue
        except Exception:
            # If JSON is broken, just return an empty list instead of 500
            rule_results = []

    return AlertDetailResponse(
        alert=alert_resp,
        transaction=tx_resp,
        rule_results=rule_results,
    )
