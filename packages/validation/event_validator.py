"""
SafeFlow — Event Validator
===========================
Phase 4: Data Quality & Validation layer.

Validates raw transaction events before they enter the processing pipeline.
Invalid events are rejected with a structured reason code and the original
payload is preserved for investigation.

Rejection codes:
    SCHEMA_ERROR        — Pydantic validation failed (missing/wrong type fields)
    MISSING_FIELD       — Required field is None or empty string
    INVALID_AMOUNT      — Amount is zero, negative, or exceeds ceiling
    INVALID_CURRENCY    — Currency code not in allowed list
    INVALID_DIRECTION   — Direction not DEBIT/CREDIT (after normalization)
    INVALID_STATUS      — Status not in allowed values (after normalization)
    INVALID_TIMESTAMP   — Timestamp missing, unparseable, or too far in future
    STALE_EVENT         — Timestamp is too far in the past (configurable window)
    INVALID_TENANT      — tenant_id is missing or non-positive
"""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass, field
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Validation config — tune these thresholds as needed
# ---------------------------------------------------------------------------

MAX_AMOUNT = 10_000_000.00          # reject amounts above 10M
MIN_AMOUNT = 0.01                   # reject zero or negative amounts
MAX_FUTURE_SECONDS = 300            # reject timestamps > 5 min in future
MAX_PAST_DAYS = 365                 # reject timestamps > 1 year in past

VALID_CURRENCIES = {
    "MYR", "USD", "SGD", "EUR", "GBP", "JPY", "AUD", "CAD",
    "HKD", "CNY", "THB", "IDR", "PHP", "VND", "INR",
}

VALID_DIRECTIONS_RAW = {
    "DEBIT", "CREDIT", "DR", "CR", "IN", "OUT",
}

VALID_STATUSES_RAW = {
    "PENDING", "POSTED", "REVERSED", "CANCELLED",
    "BOOKED", "AUTHORIZED", "AUTHORISED", "SETTLED",
    "COMPLETED", "SUCCESS", "FAILED", "DECLINED", "VOID",
}


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    valid: bool
    rejection_code: Optional[str] = None
    rejection_reason: Optional[str] = None

    @classmethod
    def ok(cls) -> "ValidationResult":
        return cls(valid=True)

    @classmethod
    def reject(cls, code: str, reason: str) -> "ValidationResult":
        return cls(valid=False, rejection_code=code, rejection_reason=reason)


@dataclass
class RejectedEvent:
    pipeline_stage: str
    rejection_code: str
    rejection_reason: str
    raw_payload: str                 # JSON string of original event
    tenant_id: Optional[int] = None
    event_id: Optional[str] = None
    account_id: Optional[str] = None
    amount: Optional[float] = None
    rejected_at: dt.datetime = field(default_factory=dt.datetime.utcnow)


# ---------------------------------------------------------------------------
# Core validator
# ---------------------------------------------------------------------------

class EventValidator:
    """
    Validates a raw transaction event dict.
    Call validate() — returns ValidationResult.
    If invalid, build_rejection() constructs the RejectedEvent for persistence.
    """

    def __init__(self, payload: dict, stage: str = "raw"):
        self.payload = payload
        self.stage = stage

    def validate(self) -> ValidationResult:
        """Run all checks in order. Return first failure."""

        # 1. Tenant
        result = self._check_tenant()
        if not result.valid:
            return result

        # 2. Required fields present
        result = self._check_required_fields()
        if not result.valid:
            return result

        # 3. Amount
        result = self._check_amount()
        if not result.valid:
            return result

        # 4. Currency
        result = self._check_currency()
        if not result.valid:
            return result

        # 5. Direction
        result = self._check_direction()
        if not result.valid:
            return result

        # 6. Status
        result = self._check_status()
        if not result.valid:
            return result

        # 7. Timestamp
        result = self._check_timestamp()
        if not result.valid:
            return result

        return ValidationResult.ok()

    def build_rejection(self, result: ValidationResult) -> RejectedEvent:
        """Build a RejectedEvent from a failed ValidationResult."""
        p = self.payload
        return RejectedEvent(
            pipeline_stage=self.stage,
            rejection_code=result.rejection_code or "UNKNOWN",
            rejection_reason=result.rejection_reason or "Unknown rejection reason",
            raw_payload=_safe_json(p),
            tenant_id=_safe_int(p.get("tenant_id")),
            event_id=str(p.get("transaction_reference") or p.get("transaction_id") or ""),
            account_id=str(p.get("account_id") or ""),
            amount=_safe_float(p.get("amount")),
            rejected_at=dt.datetime.utcnow(),
        )

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _check_tenant(self) -> ValidationResult:
        tenant_id = self.payload.get("tenant_id")
        if tenant_id is None:
            return ValidationResult.reject(
                "INVALID_TENANT",
                "tenant_id is missing",
            )
        try:
            t = int(tenant_id)
            if t <= 0:
                return ValidationResult.reject(
                    "INVALID_TENANT",
                    f"tenant_id must be positive integer, got {tenant_id!r}",
                )
        except (TypeError, ValueError):
            return ValidationResult.reject(
                "INVALID_TENANT",
                f"tenant_id is not a valid integer: {tenant_id!r}",
            )
        return ValidationResult.ok()

    def _check_required_fields(self) -> ValidationResult:
        required = [
            "transaction_id",
            "transaction_reference",
            "account_id",
            "amount",
            "currency",
            "direction",
            "status",
            "timestamp",
        ]
        for f in required:
            v = self.payload.get(f)
            if v is None or (isinstance(v, str) and not v.strip()):
                return ValidationResult.reject(
                    "MISSING_FIELD",
                    f"Required field '{f}' is missing or empty",
                )
        return ValidationResult.ok()

    def _check_amount(self) -> ValidationResult:
        raw = self.payload.get("amount")
        amount = _safe_float(raw)
        if amount is None:
            return ValidationResult.reject(
                "INVALID_AMOUNT",
                f"amount is not a valid number: {raw!r}",
            )
        if amount < MIN_AMOUNT:
            return ValidationResult.reject(
                "INVALID_AMOUNT",
                f"amount {amount} is below minimum {MIN_AMOUNT} "
                "(zero or negative amounts rejected)",
            )
        if amount > MAX_AMOUNT:
            return ValidationResult.reject(
                "INVALID_AMOUNT",
                f"amount {amount:,.2f} exceeds ceiling {MAX_AMOUNT:,.2f}",
            )
        return ValidationResult.ok()

    def _check_currency(self) -> ValidationResult:
        raw = self.payload.get("currency")
        if not raw or not isinstance(raw, str):
            return ValidationResult.reject(
                "INVALID_CURRENCY",
                f"currency is missing or not a string: {raw!r}",
            )
        code = raw.strip().upper()
        if code not in VALID_CURRENCIES:
            return ValidationResult.reject(
                "INVALID_CURRENCY",
                f"currency '{code}' is not in the allowed list. "
                f"Allowed: {sorted(VALID_CURRENCIES)}",
            )
        return ValidationResult.ok()

    def _check_direction(self) -> ValidationResult:
        raw = self.payload.get("direction")
        if not raw or not isinstance(raw, str):
            return ValidationResult.reject(
                "INVALID_DIRECTION",
                f"direction is missing or not a string: {raw!r}",
            )
        if raw.strip().upper() not in VALID_DIRECTIONS_RAW:
            return ValidationResult.reject(
                "INVALID_DIRECTION",
                f"direction '{raw}' is not valid. "
                f"Allowed: {sorted(VALID_DIRECTIONS_RAW)}",
            )
        return ValidationResult.ok()

    def _check_status(self) -> ValidationResult:
        raw = self.payload.get("status")
        if not raw or not isinstance(raw, str):
            return ValidationResult.reject(
                "INVALID_STATUS",
                f"status is missing or not a string: {raw!r}",
            )
        if raw.strip().upper() not in VALID_STATUSES_RAW:
            return ValidationResult.reject(
                "INVALID_STATUS",
                f"status '{raw}' is not valid. "
                f"Allowed: {sorted(VALID_STATUSES_RAW)}",
            )
        return ValidationResult.ok()

    def _check_timestamp(self) -> ValidationResult:
        raw = self.payload.get("timestamp")
        if not raw:
            return ValidationResult.reject(
                "INVALID_TIMESTAMP",
                "timestamp is missing",
            )
        try:
            if isinstance(raw, dt.datetime):
                ts = raw
            else:
                ts = dt.datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except (ValueError, TypeError) as e:
            return ValidationResult.reject(
                "INVALID_TIMESTAMP",
                f"timestamp '{raw}' could not be parsed: {e}",
            )

        now = dt.datetime.now(dt.timezone.utc)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=dt.timezone.utc)

        # Too far in future
        if ts > now + dt.timedelta(seconds=MAX_FUTURE_SECONDS):
            return ValidationResult.reject(
                "INVALID_TIMESTAMP",
                f"timestamp {ts.isoformat()} is {(ts - now).seconds}s in the future "
                f"(max allowed: {MAX_FUTURE_SECONDS}s)",
            )

        # Too far in past
        if ts < now - dt.timedelta(days=MAX_PAST_DAYS):
            return ValidationResult.reject(
                "STALE_EVENT",
                f"timestamp {ts.isoformat()} is more than {MAX_PAST_DAYS} days in the past",
            )

        return ValidationResult.ok()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_float(v: Any) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _safe_int(v: Any) -> Optional[int]:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _safe_json(v: Any) -> str:
    try:
        return json.dumps(v, default=str)
    except Exception:
        return str(v)
