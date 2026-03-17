from __future__ import annotations

import datetime as dt
import json
import sys
import time
import traceback
from typing import Any, Dict, List, Optional

import faust
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import text
from sqlmodel import Session

from packages.db.session import engine
from packages.db.models import Alert as AlertORM
from packages.db.models import EntityFeatures
from packages.risk_pipeline import MLTransactionEvent, score_single_transaction_event
from packages.validation import EventValidator, RejectedEvent


# =========================================================
# Structured JSON logging
# =========================================================

logger.remove()
logger.add(sys.stdout, format="{message}", level="INFO", serialize=True)


def log(level: str, event: str, **kwargs):
    record = {
        "event": event,
        "service": "risk-worker",
        "timestamp": dt.datetime.utcnow().isoformat(),
        **kwargs,
    }
    getattr(logger, level)(json.dumps(record))


# =========================================================
# Metrics
# =========================================================

class WorkerMetrics:
    def __init__(self):
        self.processed: int = 0
        self.rejected: int = 0
        self.errors: int = 0
        self.tx_inserted: int = 0
        self.tx_updated: int = 0
        self.alerts_inserted: int = 0
        self.features_upserted: int = 0
        self._started_at: float = time.time()

    def elapsed_seconds(self) -> float:
        return time.time() - self._started_at

    def log_summary(self):
        log("info", "worker_metrics_summary",
            processed=self.processed,
            rejected=self.rejected,
            errors=self.errors,
            tx_inserted=self.tx_inserted,
            tx_updated=self.tx_updated,
            alerts_inserted=self.alerts_inserted,
            features_upserted=self.features_upserted,
            elapsed_seconds=round(self.elapsed_seconds(), 1),
            rate_per_sec=round(self.processed / max(self.elapsed_seconds(), 1), 1),
        )


metrics = WorkerMetrics()
METRICS_LOG_INTERVAL = 500


# =========================================================
# Faust App
# =========================================================

app = faust.App(
    "safeflow-risk-worker",
    broker="kafka://redpanda:9092",
    topic_partitions=1,
)


# =========================================================
# Event Schemas
# =========================================================

class RawTransactionEvent(BaseModel):
    event_version: str = "v1"
    tenant_id: int
    transaction_id: int
    transaction_reference: str
    account_id: str
    amount: float
    currency: str
    direction: str
    status: str
    timestamp: dt.datetime
    vendor_code: Optional[str] = None
    employee_id: Optional[str] = None


class EnrichedTransactionEvent(BaseModel):
    event_version: str = "v1"
    tenant_id: int
    transaction_id: int
    transaction_reference: str
    account_id: str
    amount: float
    currency: str
    direction: str
    status: str
    timestamp: dt.datetime
    vendor_code: Optional[str] = None
    employee_id: Optional[str] = None


class AlertEvent(BaseModel):
    event_version: str = "v1"
    tenant_id: int
    transaction_id: int
    transaction_reference: str
    account_id: Optional[str] = None
    vendor_code: Optional[str] = None
    employee_id: Optional[str] = None
    risk_score: int
    rule_score: int
    ml_score: int
    graph_score: int
    triggered_rules: List[str] = []
    graph_motifs: Optional[str] = None
    scored_at: dt.datetime


# =========================================================
# Topics
# =========================================================

transactions_raw_topic = app.topic("transactions_raw")
transactions_enriched_topic = app.topic("transactions_enriched")
alerts_topic = app.topic("alerts")


# =========================================================
# Helpers
# =========================================================

TX_STATUS_ALLOWED = {"PENDING", "POSTED", "REVERSED", "CANCELLED"}
TX_DIRECTION_ALLOWED = {"DEBIT", "CREDIT"}

TX_STATUS_MAP = {
    "BOOKED": "PENDING", "AUTHORIZED": "PENDING", "AUTHORISED": "PENDING",
    "SETTLED": "POSTED", "COMPLETED": "POSTED", "SUCCESS": "POSTED",
    "FAILED": "CANCELLED", "DECLINED": "CANCELLED", "VOID": "CANCELLED",
}
TX_DIRECTION_MAP = {
    "DR": "DEBIT", "CR": "CREDIT", "IN": "CREDIT", "OUT": "DEBIT",
}

VELOCITY_24H_THRESHOLD = 20
HIGH_RISK_THRESHOLD = 500


def _to_dict(payload: Any) -> dict:
    if isinstance(payload, bytes):
        return json.loads(payload.decode("utf-8"))
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str):
        return json.loads(payload)
    raise ValueError(f"Unsupported payload type: {type(payload)!r}")


def _aware_utc(ts: dt.datetime) -> dt.datetime:
    if ts.tzinfo is None:
        return ts.replace(tzinfo=dt.timezone.utc)
    return ts.astimezone(dt.timezone.utc)


def _derive_severity(score: int) -> str:
    if score < 200: return "LOW"
    if score < 500: return "MEDIUM"
    if score < 800: return "HIGH"
    return "CRITICAL"


def _normalize_status(raw: str) -> str:
    if not raw: return "PENDING"
    s = raw.strip().upper()
    s = TX_STATUS_MAP.get(s, s)
    return s if s in TX_STATUS_ALLOWED else "PENDING"


def _normalize_direction(raw: str) -> str:
    if not raw: return "DEBIT"
    d = raw.strip().upper()
    d = TX_DIRECTION_MAP.get(d, d)
    return d if d in TX_DIRECTION_ALLOWED else "DEBIT"


def _build_tx_payload(evt: EnrichedTransactionEvent) -> Dict[str, Any]:
    ts = _aware_utc(evt.timestamp)
    return dict(
        tenant_id=evt.tenant_id,
        tx_id=str(evt.transaction_id),
        account_id=evt.account_id,
        customer_id=None,
        invoice_id=None,
        tx_time=ts,
        booking_time=ts,
        amount=float(evt.amount),
        currency=evt.currency,
        direction=_normalize_direction(evt.direction),
        status=_normalize_status(evt.status),
        country_code="XX",
        merchant_category="UNKNOWN",
        channel="KAFKA",
        description=f"ref={evt.transaction_reference}",
    )


# =========================================================
# Rejected event persistence
# =========================================================

INSERT_REJECTED_SQL = text("""
    INSERT INTO rejected_events (
        pipeline_stage, rejection_code, rejection_reason,
        raw_payload, tenant_id, event_id, account_id, amount,
        rejected_at, created_at, updated_at
    ) VALUES (
        :pipeline_stage, :rejection_code, :rejection_reason,
        :raw_payload, :tenant_id, :event_id, :account_id, :amount,
        NOW(), NOW(), NOW()
    )
""")


def _persist_rejection(session: Session, rejected: RejectedEvent) -> None:
    session.execute(INSERT_REJECTED_SQL, dict(
        pipeline_stage=rejected.pipeline_stage,
        rejection_code=rejected.rejection_code,
        rejection_reason=rejected.rejection_reason,
        raw_payload=rejected.raw_payload,
        tenant_id=rejected.tenant_id,
        event_id=rejected.event_id or None,
        account_id=rejected.account_id or None,
        amount=str(rejected.amount) if rejected.amount is not None else None,
    ))
    session.commit()


# =========================================================
# Idempotent transaction upsert
# =========================================================

UPSERT_TX_SQL = text("""
    INSERT INTO transactions (
        tenant_id, tx_id, account_id, customer_id, invoice_id,
        tx_time, booking_time, amount, currency, direction, status,
        country_code, merchant_category, channel, description,
        created_at, updated_at
    ) VALUES (
        :tenant_id, :tx_id, :account_id, :customer_id, :invoice_id,
        :tx_time, :booking_time, :amount, :currency, :direction, :status,
        :country_code, :merchant_category, :channel, :description,
        NOW(), NOW()
    )
    ON CONFLICT (tenant_id, tx_id) DO UPDATE SET
        account_id        = EXCLUDED.account_id,
        tx_time           = EXCLUDED.tx_time,
        booking_time      = EXCLUDED.booking_time,
        amount            = EXCLUDED.amount,
        currency          = EXCLUDED.currency,
        direction         = EXCLUDED.direction,
        status            = EXCLUDED.status,
        country_code      = EXCLUDED.country_code,
        merchant_category = EXCLUDED.merchant_category,
        channel           = EXCLUDED.channel,
        description       = EXCLUDED.description,
        updated_at        = NOW()
    RETURNING id, (xmax = 0) AS inserted
""")


def _upsert_transaction(session: Session, payload: Dict[str, Any]) -> tuple[int, bool]:
    result = session.execute(UPSERT_TX_SQL, payload)
    row = result.fetchone()
    return row.id, bool(row.inserted)


# =========================================================
# Feature upsert
# =========================================================

UPSERT_FEATURES_SQL = text("""
    INSERT INTO entity_features (
        tenant_id, account_id,
        tx_count_total, tx_count_24h, tx_count_7d,
        amount_total, amount_avg, amount_max, amount_last,
        latest_risk_score, risk_score_avg,
        high_risk_tx_count, is_velocity_flagged, consecutive_high_risk,
        first_seen_at, last_seen_at,
        created_at, updated_at
    ) VALUES (
        :tenant_id, :account_id,
        1, 1, 1,
        :amount, :amount, :amount, :amount,
        :risk_score, :risk_score,
        :high_risk_inc, false, :consec_init,
        NOW(), NOW(), NOW(), NOW()
    )
    ON CONFLICT (tenant_id, account_id) DO UPDATE SET
        tx_count_total        = entity_features.tx_count_total + 1,
        tx_count_24h          = entity_features.tx_count_24h + 1,
        tx_count_7d           = entity_features.tx_count_7d + 1,
        amount_total          = entity_features.amount_total + :amount,
        amount_avg            = (entity_features.amount_total + :amount)
                                / (entity_features.tx_count_total + 1),
        amount_max            = GREATEST(entity_features.amount_max, :amount),
        amount_last           = :amount,
        latest_risk_score     = :risk_score,
        risk_score_avg        = (
                                    entity_features.risk_score_avg * entity_features.tx_count_total
                                    + :risk_score
                                ) / (entity_features.tx_count_total + 1),
        high_risk_tx_count    = entity_features.high_risk_tx_count + :high_risk_inc,
        is_velocity_flagged   = (entity_features.tx_count_24h + 1) > :velocity_threshold,
        consecutive_high_risk = CASE
            WHEN :risk_score >= :high_risk_threshold
            THEN entity_features.consecutive_high_risk + 1
            ELSE 0
        END,
        last_seen_at          = NOW(),
        updated_at            = NOW()
""")


def _upsert_features(
    session: Session,
    tenant_id: int,
    account_id: str,
    amount: float,
    risk_score: int,
) -> None:
    is_high_risk = risk_score >= HIGH_RISK_THRESHOLD
    session.execute(UPSERT_FEATURES_SQL, dict(
        tenant_id=tenant_id,
        account_id=account_id,
        amount=str(round(amount, 2)),
        risk_score=risk_score,
        high_risk_inc=1 if is_high_risk else 0,
        consec_init=1 if is_high_risk else 0,
        velocity_threshold=VELOCITY_24H_THRESHOLD,
        high_risk_threshold=HIGH_RISK_THRESHOLD,
    ))


# =========================================================
# Agent 1: Raw → Validate → Enriched
# =========================================================

@app.agent(transactions_raw_topic)
async def enrich_raw_transactions(stream):
    async for payload in stream:
        try:
            raw_dict = _to_dict(payload)
        except Exception as e:
            metrics.errors += 1
            log("error", "raw_payload_parse_error", error=str(e))
            continue

        # --- Validation gate ---
        validator = EventValidator(raw_dict, stage="raw")
        result = validator.validate()

        if not result.valid:
            metrics.rejected += 1
            rejected = validator.build_rejection(result)
            log("warning", "event_rejected",
                stage="raw",
                rejection_code=rejected.rejection_code,
                rejection_reason=rejected.rejection_reason,
                event_id=rejected.event_id,
                account_id=rejected.account_id,
            )
            try:
                with Session(engine) as session:
                    _persist_rejection(session, rejected)
            except Exception as persist_err:
                log("error", "rejection_persist_failed", error=str(persist_err))
            continue

        # --- Valid: parse and forward ---
        try:
            evt = RawTransactionEvent.model_validate(raw_dict)
            log("info", "raw_event_received",
                tx_ref=evt.transaction_reference,
                account_id=evt.account_id,
                amount=evt.amount,
                tenant_id=evt.tenant_id,
            )
            enriched = EnrichedTransactionEvent(
                event_version=evt.event_version,
                tenant_id=evt.tenant_id,
                transaction_id=evt.transaction_id,
                transaction_reference=evt.transaction_reference,
                account_id=evt.account_id,
                amount=evt.amount,
                currency=evt.currency,
                direction=evt.direction,
                status=evt.status,
                timestamp=evt.timestamp,
                vendor_code=evt.vendor_code,
                employee_id=evt.employee_id,
            )
            await transactions_enriched_topic.send(value=enriched.model_dump())

        except Exception as e:
            metrics.errors += 1
            log("error", "raw_event_parse_error",
                error=str(e), traceback=traceback.format_exc())


# =========================================================
# Agent 2: Enriched → Score → Persist → Emit
# =========================================================

@app.agent(transactions_enriched_topic)
async def score_enriched_transactions(stream):
    async for payload in stream:
        t_start = time.time()

        try:
            raw_dict = _to_dict(payload)
            evt = EnrichedTransactionEvent.model_validate(raw_dict)
        except Exception as e:
            metrics.errors += 1
            log("error", "enriched_event_parse_error", error=str(e))
            continue

        log("info", "enriched_event_received",
            tx_ref=evt.transaction_reference,
            account_id=evt.account_id,
            amount=evt.amount,
        )

        # --- Scoring ---
        try:
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
        except Exception as e:
            metrics.errors += 1
            log("error", "scoring_error",
                tx_ref=evt.transaction_reference,
                error=str(e), traceback=traceback.format_exc())
            continue

        severity = _derive_severity(fusion.risk_score)
        alert_evt: Optional[AlertEvent] = None

        # --- DB persistence ---
        try:
            with Session(engine) as session:
                tx_payload = _build_tx_payload(evt)
                tx_pk, was_inserted = _upsert_transaction(session, tx_payload)
                session.commit()

                if was_inserted:
                    metrics.tx_inserted += 1
                    log("info", "tx_inserted",
                        tx_id=tx_payload["tx_id"], pk=tx_pk,
                        account_id=evt.account_id, amount=evt.amount)
                else:
                    metrics.tx_updated += 1
                    log("info", "tx_updated",
                        tx_id=tx_payload["tx_id"], pk=tx_pk)

                _upsert_features(
                    session=session,
                    tenant_id=evt.tenant_id,
                    account_id=evt.account_id,
                    amount=evt.amount,
                    risk_score=fusion.risk_score,
                )
                session.commit()
                metrics.features_upserted += 1

                alert_evt = AlertEvent(
                    event_version="v1",
                    tenant_id=evt.tenant_id,
                    transaction_id=tx_pk,
                    transaction_reference=evt.transaction_reference,
                    account_id=evt.account_id,
                    vendor_code=evt.vendor_code,
                    employee_id=evt.employee_id,
                    risk_score=fusion.risk_score,
                    rule_score=fusion.rule_output.score or 0,
                    ml_score=fusion.ml_output.score or 0,
                    graph_score=fusion.graph_output.score or 0,
                    triggered_rules=fusion.rule_output.triggered_rules or [],
                    graph_motifs=fusion.graph_output.motifs,
                    scored_at=dt.datetime.utcnow(),
                )
                db_alert = AlertORM(
                    tenant_id=alert_evt.tenant_id,
                    transaction_id=alert_evt.transaction_id,
                    transaction_reference=alert_evt.transaction_reference,
                    account_id=alert_evt.account_id,
                    vendor_code=alert_evt.vendor_code,
                    employee_id=alert_evt.employee_id,
                    risk_score_0_999=alert_evt.risk_score,
                    severity=severity,
                    rule_score=alert_evt.rule_score,
                    ml_score=alert_evt.ml_score,
                    graph_score=alert_evt.graph_score,
                    triggered_rules=",".join(alert_evt.triggered_rules or []),
                    graph_motifs=alert_evt.graph_motifs,
                    rule_results_json=None,
                    scored_at=alert_evt.scored_at,
                )
                session.add(db_alert)
                session.commit()
                session.refresh(db_alert)
                metrics.alerts_inserted += 1

                latency_ms = round((time.time() - t_start) * 1000, 1)
                log("info", "event_processed",
                    tx_ref=evt.transaction_reference,
                    tx_pk=tx_pk,
                    alert_id=db_alert.id,
                    risk_score=fusion.risk_score,
                    severity=severity,
                    account_id=evt.account_id,
                    latency_ms=latency_ms,
                )

        except Exception:
            metrics.errors += 1
            log("error", "db_persist_error",
                tx_ref=evt.transaction_reference,
                traceback=traceback.format_exc())

        metrics.processed += 1
        if metrics.processed % METRICS_LOG_INTERVAL == 0:
            metrics.log_summary()

        if alert_evt is None:
            alert_evt = AlertEvent(
                event_version="v1",
                tenant_id=evt.tenant_id,
                transaction_id=-1,
                transaction_reference=evt.transaction_reference,
                account_id=evt.account_id,
                vendor_code=evt.vendor_code,
                employee_id=evt.employee_id,
                risk_score=fusion.risk_score,
                rule_score=fusion.rule_output.score or 0,
                ml_score=fusion.ml_output.score or 0,
                graph_score=fusion.graph_output.score or 0,
                triggered_rules=fusion.rule_output.triggered_rules or [],
                graph_motifs=fusion.graph_output.motifs,
                scored_at=dt.datetime.utcnow(),
            )

        await alerts_topic.send(value=alert_evt.model_dump())


if __name__ == "__main__":
    app.main()
