"""
SafeFlow — Batch Recompute Job
==============================
Phase 3: Daily batch processing layer.

What this does:
  1. Recomputes entity_features from full transaction history
     - Fixes the approximate 24h/7d window counts from the streaming worker
     - Uses exact SQL window functions over real tx_time
  2. Upserts entity_daily_summary rows for each (account, date) pair
     - Idempotent: safe to re-run for any date range
  3. Updates entities.risk_score from latest feature data

Run modes:
    # Full recompute (all time)
    python tools/batch_recompute.py

    # Recompute last N days only (faster for daily cron)
    python tools/batch_recompute.py --days 7

    # Dry run — show what would be computed, no writes
    python tools/batch_recompute.py --dry-run

    # Specific date range
    python tools/batch_recompute.py --from-date 2026-01-01 --to-date 2026-03-17
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
import time
from typing import Optional

import psycopg2
import psycopg2.extras

# ---------------------------------------------------------------------------
# Config — matches docker-compose DATABASE_URL
# ---------------------------------------------------------------------------

DB_DSN = "postgresql://safeflow:safeflow@localhost:5432/safeflow"

HIGH_RISK_THRESHOLD = 500
VELOCITY_24H_THRESHOLD = 20


# ---------------------------------------------------------------------------
# DB connection
# ---------------------------------------------------------------------------

def get_conn():
    return psycopg2.connect(DB_DSN)


# ---------------------------------------------------------------------------
# Step 1: Recompute entity_features with exact window counts
# ---------------------------------------------------------------------------

RECOMPUTE_FEATURES_SQL = """
WITH base AS (
    SELECT
        tenant_id,
        account_id,
        COUNT(*)                                            AS tx_count_total,
        SUM(CASE WHEN tx_time >= NOW() - INTERVAL '24 hours'
                 THEN 1 ELSE 0 END)                        AS tx_count_24h,
        SUM(CASE WHEN tx_time >= NOW() - INTERVAL '7 days'
                 THEN 1 ELSE 0 END)                        AS tx_count_7d,
        SUM(amount)                                        AS amount_total,
        AVG(amount)                                        AS amount_avg,
        MAX(amount)                                        AS amount_max,
        MIN(tx_time AT TIME ZONE 'UTC')                    AS first_seen_at,
        MAX(tx_time AT TIME ZONE 'UTC')                    AS last_seen_at
    FROM transactions
    WHERE tenant_id IS NOT NULL
    GROUP BY tenant_id, account_id
),
alert_agg AS (
    SELECT
        t.tenant_id,
        t.account_id,
        ROUND(AVG(a.risk_score_0_999), 2)                 AS risk_score_avg,
        MAX(a.risk_score_0_999)                            AS latest_risk_score,
        SUM(CASE WHEN a.risk_score_0_999 >= %(high_risk_threshold)s
                 THEN 1 ELSE 0 END)                        AS high_risk_tx_count
    FROM alerts a
    JOIN transactions t ON t.id = a.transaction_id
    WHERE t.tenant_id IS NOT NULL
    GROUP BY t.tenant_id, t.account_id
)
INSERT INTO entity_features (
    tenant_id, account_id,
    tx_count_total, tx_count_24h, tx_count_7d,
    amount_total, amount_avg, amount_max, amount_last,
    latest_risk_score, risk_score_avg,
    high_risk_tx_count,
    is_velocity_flagged,
    consecutive_high_risk,
    first_seen_at, last_seen_at,
    created_at, updated_at
)
SELECT
    b.tenant_id,
    b.account_id,
    b.tx_count_total,
    b.tx_count_24h,
    b.tx_count_7d,
    ROUND(b.amount_total, 2),
    ROUND(b.amount_avg, 2),
    ROUND(b.amount_max, 2),
    ROUND(b.amount_max, 2),          -- amount_last approximated as max for batch
    COALESCE(aa.latest_risk_score, 0),
    COALESCE(aa.risk_score_avg, 0),
    COALESCE(aa.high_risk_tx_count, 0),
    b.tx_count_24h > %(velocity_threshold)s,
    0,                               -- consecutive_high_risk reset by batch; stream maintains live value
    b.first_seen_at,
    b.last_seen_at,
    NOW(),
    NOW()
FROM base b
LEFT JOIN alert_agg aa
    ON aa.tenant_id = b.tenant_id
    AND aa.account_id = b.account_id
ON CONFLICT (tenant_id, account_id) DO UPDATE SET
    tx_count_total        = EXCLUDED.tx_count_total,
    tx_count_24h          = EXCLUDED.tx_count_24h,
    tx_count_7d           = EXCLUDED.tx_count_7d,
    amount_total          = EXCLUDED.amount_total,
    amount_avg            = EXCLUDED.amount_avg,
    amount_max            = EXCLUDED.amount_max,
    latest_risk_score     = EXCLUDED.latest_risk_score,
    risk_score_avg        = EXCLUDED.risk_score_avg,
    high_risk_tx_count    = EXCLUDED.high_risk_tx_count,
    is_velocity_flagged   = EXCLUDED.is_velocity_flagged,
    first_seen_at         = EXCLUDED.first_seen_at,
    last_seen_at          = EXCLUDED.last_seen_at,
    updated_at            = NOW()
"""


def step1_recompute_features(conn, dry_run: bool) -> int:
    print("\n[Step 1] Recomputing entity_features from full transaction history...")
    print("         Using exact 24h/7d window counts from tx_time column.")

    if dry_run:
        # Just count what would be affected
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(DISTINCT account_id) FROM transactions WHERE tenant_id IS NOT NULL")
            n = cur.fetchone()[0]
        print(f"         DRY RUN: would recompute features for {n} entities.")
        return n

    with conn.cursor() as cur:
        cur.execute(
            RECOMPUTE_FEATURES_SQL,
            {"high_risk_threshold": HIGH_RISK_THRESHOLD, "velocity_threshold": VELOCITY_24H_THRESHOLD},
        )
        rows_affected = cur.rowcount
    conn.commit()
    print(f"         ✓ Upserted {rows_affected} entity_features rows.")
    return rows_affected


# ---------------------------------------------------------------------------
# Step 2: Upsert entity_daily_summary
# ---------------------------------------------------------------------------

DAILY_SUMMARY_SQL = """
INSERT INTO entity_daily_summary (
    tenant_id, account_id, summary_date,
    tx_count, tx_count_debit, tx_count_credit,
    amount_total, amount_avg, amount_max, amount_min,
    risk_score_avg, risk_score_max, high_risk_tx_count,
    batch_run_at, created_at, updated_at
)
SELECT
    t.tenant_id,
    t.account_id,
    DATE(t.tx_time AT TIME ZONE 'UTC')              AS summary_date,
    COUNT(*)                                         AS tx_count,
    SUM(CASE WHEN t.direction = 'DEBIT'  THEN 1 ELSE 0 END) AS tx_count_debit,
    SUM(CASE WHEN t.direction = 'CREDIT' THEN 1 ELSE 0 END) AS tx_count_credit,
    ROUND(SUM(t.amount), 2)                          AS amount_total,
    ROUND(AVG(t.amount), 2)                          AS amount_avg,
    ROUND(MAX(t.amount), 2)                          AS amount_max,
    ROUND(MIN(t.amount), 2)                          AS amount_min,
    ROUND(COALESCE(AVG(a.risk_score_0_999), 0), 2)  AS risk_score_avg,
    COALESCE(MAX(a.risk_score_0_999), 0)             AS risk_score_max,
    SUM(CASE WHEN COALESCE(a.risk_score_0_999, 0) >= %(high_risk_threshold)s
             THEN 1 ELSE 0 END)                      AS high_risk_tx_count,
    NOW()                                            AS batch_run_at,
    NOW()                                            AS created_at,
    NOW()                                            AS updated_at
FROM transactions t
LEFT JOIN alerts a ON a.transaction_id = t.id
WHERE t.tenant_id IS NOT NULL
  AND DATE(t.tx_time AT TIME ZONE 'UTC') >= %(from_date)s
  AND DATE(t.tx_time AT TIME ZONE 'UTC') <= %(to_date)s
GROUP BY t.tenant_id, t.account_id, DATE(t.tx_time AT TIME ZONE 'UTC')
ON CONFLICT (tenant_id, account_id, summary_date) DO UPDATE SET
    tx_count           = EXCLUDED.tx_count,
    tx_count_debit     = EXCLUDED.tx_count_debit,
    tx_count_credit    = EXCLUDED.tx_count_credit,
    amount_total       = EXCLUDED.amount_total,
    amount_avg         = EXCLUDED.amount_avg,
    amount_max         = EXCLUDED.amount_max,
    amount_min         = EXCLUDED.amount_min,
    risk_score_avg     = EXCLUDED.risk_score_avg,
    risk_score_max     = EXCLUDED.risk_score_max,
    high_risk_tx_count = EXCLUDED.high_risk_tx_count,
    batch_run_at       = NOW(),
    updated_at         = NOW()
"""


def step2_daily_summary(
    conn,
    dry_run: bool,
    from_date: dt.date,
    to_date: dt.date,
) -> int:
    days = (to_date - from_date).days + 1
    print(f"\n[Step 2] Computing entity_daily_summary for {days} days "
          f"({from_date} → {to_date})...")

    if dry_run:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT COUNT(DISTINCT (account_id, DATE(tx_time AT TIME ZONE 'UTC')))
                   FROM transactions
                   WHERE DATE(tx_time AT TIME ZONE 'UTC') BETWEEN %s AND %s""",
                (from_date, to_date),
            )
            n = cur.fetchone()[0]
        print(f"         DRY RUN: would upsert ~{n} daily summary rows.")
        return n

    with conn.cursor() as cur:
        cur.execute(
            DAILY_SUMMARY_SQL,
            {
                "high_risk_threshold": HIGH_RISK_THRESHOLD,
                "from_date": from_date,
                "to_date": to_date,
            },
        )
        rows_affected = cur.rowcount
    conn.commit()
    print(f"         ✓ Upserted {rows_affected} entity_daily_summary rows.")
    return rows_affected


# ---------------------------------------------------------------------------
# Step 3: Update entities.risk_score from feature data
# ---------------------------------------------------------------------------

UPDATE_ENTITY_RISK_SQL = """
UPDATE entities e
SET
    risk_score = LEAST(ROUND(ef.latest_risk_score / 10.0), 100),
    updated_at = NOW()
FROM entity_features ef
WHERE ef.account_id = e.entity_id
  AND ef.tenant_id  = 1
  AND LEAST(ROUND(ef.latest_risk_score / 10.0), 100) != COALESCE(e.risk_score, -1)
"""


def step3_update_entity_risk(conn, dry_run: bool) -> int:
    print("\n[Step 3] Syncing entities.risk_score from entity_features...")

    if dry_run:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM entities e
                JOIN entity_features ef ON ef.account_id = e.entity_id
                WHERE LEAST(ROUND(ef.latest_risk_score / 10.0), 100) != COALESCE(e.risk_score, -1)
            """)
            n = cur.fetchone()[0]
        print(f"         DRY RUN: would update risk_score for {n} entities.")
        return n

    with conn.cursor() as cur:
        cur.execute(UPDATE_ENTITY_RISK_SQL)
        rows_affected = cur.rowcount
    conn.commit()
    print(f"         ✓ Updated risk_score for {rows_affected} entities.")
    return rows_affected


# ---------------------------------------------------------------------------
# Verification query
# ---------------------------------------------------------------------------

def print_summary(conn):
    print("\n[Summary] Post-batch state:")
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT
                account_id,
                tx_count_total,
                tx_count_24h,
                tx_count_7d,
                ROUND(amount_avg, 2) AS amount_avg,
                latest_risk_score,
                is_velocity_flagged
            FROM entity_features
            ORDER BY tx_count_total DESC
            LIMIT 10
        """)
        rows = cur.fetchall()

    header = f"{'account_id':<15} {'total':>6} {'24h':>5} {'7d':>6} {'avg_amt':>12} {'risk':>5} {'vel':>5}"
    print(f"\n  {header}")
    print(f"  {'-'*len(header)}")
    for r in rows:
        print(
            f"  {r['account_id']:<15}"
            f" {r['tx_count_total']:>6}"
            f" {r['tx_count_24h']:>5}"
            f" {r['tx_count_7d']:>6}"
            f" {float(r['amount_avg']):>12,.2f}"
            f" {r['latest_risk_score']:>5}"
            f" {'Y' if r['is_velocity_flagged'] else 'N':>5}"
        )

    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM entity_daily_summary")
        daily_count = cur.fetchone()[0]
        cur.execute("SELECT MIN(summary_date), MAX(summary_date) FROM entity_daily_summary")
        date_range = cur.fetchone()

    print(f"\n  entity_daily_summary: {daily_count} rows "
          f"({date_range[0]} → {date_range[1]})")


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(description="SafeFlow batch recompute job")
    parser.add_argument("--days", type=int, default=None,
                        help="Recompute last N days only (default: all time)")
    parser.add_argument("--from-date", type=str, default=None,
                        help="Start date YYYY-MM-DD (overrides --days)")
    parser.add_argument("--to-date", type=str, default=None,
                        help="End date YYYY-MM-DD (default: today)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be computed without writing")
    return parser.parse_args()


def main():
    args = parse_args()

    today = dt.date.today()
    to_date = dt.date.fromisoformat(args.to_date) if args.to_date else today

    if args.from_date:
        from_date = dt.date.fromisoformat(args.from_date)
    elif args.days:
        from_date = today - dt.timedelta(days=args.days - 1)
    else:
        from_date = dt.date(2025, 1, 1)  # full history

    print("=" * 60)
    print("SafeFlow Batch Recompute Job")
    print(f"  Mode:      {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"  Date range: {from_date} → {to_date}")
    print(f"  DB:         {DB_DSN}")
    print("=" * 60)

    t_start = time.time()

    try:
        conn = get_conn()
    except Exception as e:
        print(f"\n[ERROR] Cannot connect to DB: {e}")
        print("        Is Docker running? Is postgres healthy?")
        sys.exit(1)

    try:
        step1_recompute_features(conn, args.dry_run)
        step2_daily_summary(conn, args.dry_run, from_date, to_date)
        step3_update_entity_risk(conn, args.dry_run)

        if not args.dry_run:
            print_summary(conn)

    except Exception as e:
        print(f"\n[ERROR] Batch job failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

    elapsed = time.time() - t_start
    print(f"\n{'DRY RUN ' if args.dry_run else ''}Batch complete in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
