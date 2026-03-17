# tests/unit/test_event_validator.py
"""
Unit tests for packages/validation/event_validator.py

Tests cover:
- Valid events pass through cleanly
- Each rejection code fires correctly
- Edge cases (boundary amounts, old timestamps, etc.)

These tests have no DB or network dependencies — pure logic.
"""

import datetime as dt
import pytest

from packages.validation.event_validator import (
    EventValidator,
    ValidationResult,
    RejectedEvent,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _base_event(**overrides) -> dict:
    """Return a minimal valid event, with optional field overrides."""
    now = dt.datetime.utcnow().replace(microsecond=0).isoformat()
    event = {
        "event_version": "v1",
        "tenant_id": 1,
        "transaction_id": 12345,
        "transaction_reference": "TEST-001",
        "account_id": "ACC-TEST-001",
        "amount": 500.00,
        "currency": "MYR",
        "direction": "DEBIT",
        "status": "BOOKED",
        "timestamp": now,
    }
    event.update(overrides)
    return event


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

class TestValidEventPasses:
    def test_valid_event_passes(self):
        result = EventValidator(_base_event()).validate()
        assert result.valid is True
        assert result.rejection_code is None

    def test_valid_event_credit_direction(self):
        result = EventValidator(_base_event(direction="CREDIT")).validate()
        assert result.valid is True

    def test_valid_event_all_currencies(self):
        for currency in ["MYR", "USD", "SGD", "EUR", "GBP"]:
            result = EventValidator(_base_event(currency=currency)).validate()
            assert result.valid is True, f"Expected {currency} to be valid"

    def test_valid_event_all_statuses(self):
        for status in ["BOOKED", "POSTED", "PENDING", "SETTLED", "COMPLETED"]:
            result = EventValidator(_base_event(status=status)).validate()
            assert result.valid is True, f"Expected status {status} to be valid"

    def test_valid_event_with_optional_fields(self):
        result = EventValidator(_base_event(
            vendor_code="VEND-001",
            employee_id="EMP-001",
        )).validate()
        assert result.valid is True

    def test_boundary_amount_minimum(self):
        """Exactly at minimum should pass."""
        result = EventValidator(_base_event(amount=0.01)).validate()
        assert result.valid is True

    def test_boundary_amount_maximum(self):
        """Exactly at ceiling should pass."""
        result = EventValidator(_base_event(amount=10_000_000.00)).validate()
        assert result.valid is True


# ---------------------------------------------------------------------------
# MISSING_FIELD
# ---------------------------------------------------------------------------

class TestMissingFields:
    @pytest.mark.parametrize("field", [
        "transaction_id",
        "transaction_reference",
        "account_id",
        "amount",
        "currency",
        "direction",
        "status",
        "timestamp",
    ])
    def test_missing_required_field(self, field):
        event = _base_event()
        del event[field]
        result = EventValidator(event).validate()
        assert result.valid is False
        assert result.rejection_code == "MISSING_FIELD"
        assert field in result.rejection_reason

    def test_empty_string_account_id(self):
        result = EventValidator(_base_event(account_id="")).validate()
        assert result.valid is False
        assert result.rejection_code == "MISSING_FIELD"

    def test_whitespace_only_account_id(self):
        result = EventValidator(_base_event(account_id="   ")).validate()
        assert result.valid is False
        assert result.rejection_code == "MISSING_FIELD"


# ---------------------------------------------------------------------------
# INVALID_TENANT
# ---------------------------------------------------------------------------

class TestInvalidTenant:
    def test_missing_tenant_id(self):
        event = _base_event()
        del event["tenant_id"]
        result = EventValidator(event).validate()
        assert result.valid is False
        assert result.rejection_code == "INVALID_TENANT"

    def test_tenant_id_zero(self):
        result = EventValidator(_base_event(tenant_id=0)).validate()
        assert result.valid is False
        assert result.rejection_code == "INVALID_TENANT"

    def test_tenant_id_negative(self):
        result = EventValidator(_base_event(tenant_id=-1)).validate()
        assert result.valid is False
        assert result.rejection_code == "INVALID_TENANT"

    def test_tenant_id_string_non_numeric(self):
        result = EventValidator(_base_event(tenant_id="abc")).validate()
        assert result.valid is False
        assert result.rejection_code == "INVALID_TENANT"

    def test_tenant_id_valid_positive(self):
        result = EventValidator(_base_event(tenant_id=99)).validate()
        assert result.valid is True


# ---------------------------------------------------------------------------
# INVALID_AMOUNT
# ---------------------------------------------------------------------------

class TestInvalidAmount:
    def test_zero_amount(self):
        result = EventValidator(_base_event(amount=0)).validate()
        assert result.valid is False
        assert result.rejection_code == "INVALID_AMOUNT"

    def test_negative_amount(self):
        result = EventValidator(_base_event(amount=-100)).validate()
        assert result.valid is False
        assert result.rejection_code == "INVALID_AMOUNT"

    def test_amount_above_ceiling(self):
        result = EventValidator(_base_event(amount=10_000_001)).validate()
        assert result.valid is False
        assert result.rejection_code == "INVALID_AMOUNT"

    def test_amount_as_string_number(self):
        """String numbers should be parsed as float."""
        result = EventValidator(_base_event(amount="500.00")).validate()
        assert result.valid is True

    def test_amount_non_numeric_string(self):
        result = EventValidator(_base_event(amount="abc")).validate()
        assert result.valid is False
        assert result.rejection_code == "INVALID_AMOUNT"

    def test_amount_none(self):
        result = EventValidator(_base_event(amount=None)).validate()
        assert result.valid is False


# ---------------------------------------------------------------------------
# INVALID_CURRENCY
# ---------------------------------------------------------------------------

class TestInvalidCurrency:
    def test_unknown_currency(self):
        result = EventValidator(_base_event(currency="XYZ")).validate()
        assert result.valid is False
        assert result.rejection_code == "INVALID_CURRENCY"

    def test_lowercase_valid_currency(self):
        """Lowercase should be normalized and accepted."""
        result = EventValidator(_base_event(currency="myr")).validate()
        assert result.valid is True

    def test_empty_currency(self):
        result = EventValidator(_base_event(currency="")).validate()
        assert result.valid is False
        # Empty string is caught by MISSING_FIELD check before currency check
        assert result.rejection_code in ("MISSING_FIELD", "INVALID_CURRENCY")

    def test_numeric_currency(self):
        result = EventValidator(_base_event(currency="123")).validate()
        assert result.valid is False
        assert result.rejection_code == "INVALID_CURRENCY"


# ---------------------------------------------------------------------------
# INVALID_DIRECTION
# ---------------------------------------------------------------------------

class TestInvalidDirection:
    def test_invalid_direction(self):
        result = EventValidator(_base_event(direction="SIDEWAYS")).validate()
        assert result.valid is False
        assert result.rejection_code == "INVALID_DIRECTION"

    def test_valid_abbreviated_direction_dr(self):
        """DR is in the allowed raw set."""
        result = EventValidator(_base_event(direction="DR")).validate()
        assert result.valid is True

    def test_valid_abbreviated_direction_cr(self):
        result = EventValidator(_base_event(direction="CR")).validate()
        assert result.valid is True

    def test_empty_direction(self):
        result = EventValidator(_base_event(direction="")).validate()
        assert result.valid is False
        # Empty string is caught by MISSING_FIELD check before direction check
        assert result.rejection_code in ("MISSING_FIELD", "INVALID_DIRECTION")


# ---------------------------------------------------------------------------
# INVALID_TIMESTAMP / STALE_EVENT
# ---------------------------------------------------------------------------

class TestTimestampValidation:
    def test_stale_event_over_1_year(self):
        old_ts = (dt.datetime.utcnow() - dt.timedelta(days=400)).isoformat()
        result = EventValidator(_base_event(timestamp=old_ts)).validate()
        assert result.valid is False
        assert result.rejection_code == "STALE_EVENT"

    def test_future_event_beyond_threshold(self):
        future_ts = (dt.datetime.utcnow() + dt.timedelta(seconds=400)).isoformat()
        result = EventValidator(_base_event(timestamp=future_ts)).validate()
        assert result.valid is False
        assert result.rejection_code == "INVALID_TIMESTAMP"

    def test_valid_recent_timestamp(self):
        recent_ts = (dt.datetime.utcnow() - dt.timedelta(hours=1)).isoformat()
        result = EventValidator(_base_event(timestamp=recent_ts)).validate()
        assert result.valid is True

    def test_valid_near_future_within_threshold(self):
        """Slightly in the future (within 5 min) should pass."""
        near_future = (dt.datetime.utcnow() + dt.timedelta(seconds=60)).isoformat()
        result = EventValidator(_base_event(timestamp=near_future)).validate()
        assert result.valid is True

    def test_unparseable_timestamp(self):
        result = EventValidator(_base_event(timestamp="not-a-date")).validate()
        assert result.valid is False
        assert result.rejection_code == "INVALID_TIMESTAMP"

    def test_missing_timestamp(self):
        event = _base_event()
        del event["timestamp"]
        result = EventValidator(event).validate()
        assert result.valid is False
        assert result.rejection_code in ("MISSING_FIELD", "INVALID_TIMESTAMP")


# ---------------------------------------------------------------------------
# RejectedEvent construction
# ---------------------------------------------------------------------------

class TestRejectedEventConstruction:
    def test_build_rejection_captures_payload(self):
        event = _base_event(amount=-50)
        validator = EventValidator(event, stage="raw")
        result = validator.validate()
        assert result.valid is False

        rejected = validator.build_rejection(result)
        assert isinstance(rejected, RejectedEvent)
        assert rejected.pipeline_stage == "raw"
        assert rejected.rejection_code == "INVALID_AMOUNT"
        assert rejected.account_id == "ACC-TEST-001"
        assert rejected.amount == -50.0
        assert "ACC-TEST-001" in rejected.raw_payload

    def test_build_rejection_missing_tenant(self):
        event = _base_event()
        del event["tenant_id"]
        validator = EventValidator(event, stage="raw")
        result = validator.validate()
        rejected = validator.build_rejection(result)
        assert rejected.rejection_code == "INVALID_TENANT"
        assert rejected.tenant_id is None
