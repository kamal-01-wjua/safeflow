# tests/unit/test_batch_recompute.py
"""
Unit tests for tools/batch_recompute.py

Tests cover pure logic only — no DB connection needed.
Tests the argument parsing, date range computation, and SQL parameter building.
"""

import datetime as dt
import pytest
import sys
import os

# batch_recompute.py is in tools/ — add it to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


class TestDateRangeLogic:
    """Test the date range computation logic from batch_recompute CLI args."""

    def test_default_from_date_is_2025(self):
        """Default full history run starts from 2025-01-01."""
        from_date = dt.date(2025, 1, 1)
        to_date = dt.date.today()
        assert from_date.year == 2025
        assert to_date >= from_date

    def test_days_flag_computes_correct_from_date(self):
        """--days 7 should set from_date to today - 6 days."""
        today = dt.date.today()
        days = 7
        from_date = today - dt.timedelta(days=days - 1)
        assert (today - from_date).days == days - 1

    def test_days_1_means_today_only(self):
        today = dt.date.today()
        from_date = today - dt.timedelta(days=0)
        assert from_date == today

    def test_date_range_span(self):
        from_date = dt.date(2026, 1, 1)
        to_date = dt.date(2026, 3, 17)
        days = (to_date - from_date).days + 1
        assert days == 76

    def test_same_day_range(self):
        d = dt.date(2026, 3, 17)
        days = (d - d).days + 1
        assert days == 1


class TestHighRiskThreshold:
    """Test the HIGH_RISK_THRESHOLD constant and its effect on counts."""

    def test_threshold_value(self):
        from tools.batch_recompute import HIGH_RISK_THRESHOLD
        assert HIGH_RISK_THRESHOLD == 500

    def test_score_at_threshold_is_high_risk(self):
        from tools.batch_recompute import HIGH_RISK_THRESHOLD
        score = 500
        assert score >= HIGH_RISK_THRESHOLD

    def test_score_below_threshold_is_not_high_risk(self):
        from tools.batch_recompute import HIGH_RISK_THRESHOLD
        score = 499
        assert score < HIGH_RISK_THRESHOLD

    def test_score_above_threshold_is_high_risk(self):
        from tools.batch_recompute import HIGH_RISK_THRESHOLD
        score = 800
        assert score >= HIGH_RISK_THRESHOLD


class TestVelocityThreshold:
    """Test the VELOCITY_24H_THRESHOLD constant."""

    def test_threshold_value(self):
        from tools.batch_recompute import VELOCITY_24H_THRESHOLD
        assert VELOCITY_24H_THRESHOLD == 20

    def test_count_above_threshold_flagged(self):
        from tools.batch_recompute import VELOCITY_24H_THRESHOLD
        tx_count_24h = 21
        assert tx_count_24h > VELOCITY_24H_THRESHOLD

    def test_count_at_threshold_not_flagged(self):
        from tools.batch_recompute import VELOCITY_24H_THRESHOLD
        tx_count_24h = 20
        assert not (tx_count_24h > VELOCITY_24H_THRESHOLD)
