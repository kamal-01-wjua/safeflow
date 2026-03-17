-- =============================================================
-- SafeFlow Migration 004: entity_daily_summary table
-- Phase 3 — Batch Processing Layer
--
-- Run:
--   Get-Content infra\sql\004_entity_daily_summary.sql | docker exec -i safeflow-postgres psql -U safeflow -d safeflow
-- =============================================================

CREATE TABLE IF NOT EXISTS entity_daily_summary (
    id                  SERIAL PRIMARY KEY,
    tenant_id           INTEGER NOT NULL,
    account_id          VARCHAR NOT NULL,
    summary_date        DATE NOT NULL,         -- UTC date this row covers

    -- Volume
    tx_count            INTEGER NOT NULL DEFAULT 0,
    tx_count_debit      INTEGER NOT NULL DEFAULT 0,
    tx_count_credit     INTEGER NOT NULL DEFAULT 0,

    -- Amounts
    amount_total        NUMERIC(18, 2) NOT NULL DEFAULT 0.00,
    amount_avg          NUMERIC(18, 2) NOT NULL DEFAULT 0.00,
    amount_max          NUMERIC(18, 2) NOT NULL DEFAULT 0.00,
    amount_min          NUMERIC(18, 2) NOT NULL DEFAULT 0.00,

    -- Risk
    risk_score_avg      NUMERIC(6, 2)  NOT NULL DEFAULT 0.00,
    risk_score_max      INTEGER        NOT NULL DEFAULT 0,
    high_risk_tx_count  INTEGER        NOT NULL DEFAULT 0,

    -- Metadata
    batch_run_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- One row per (tenant, account, date)
    CONSTRAINT uq_entity_daily_summary UNIQUE (tenant_id, account_id, summary_date)
);

CREATE INDEX IF NOT EXISTS ix_entity_daily_summary_tenant_account
    ON entity_daily_summary (tenant_id, account_id);

CREATE INDEX IF NOT EXISTS ix_entity_daily_summary_date
    ON entity_daily_summary (summary_date DESC);

CREATE INDEX IF NOT EXISTS ix_entity_daily_summary_account_date
    ON entity_daily_summary (account_id, summary_date DESC);

-- updated_at trigger
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'trg_entity_daily_summary_updated_at'
    ) THEN
        CREATE TRIGGER trg_entity_daily_summary_updated_at
            BEFORE UPDATE ON entity_daily_summary
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
        RAISE NOTICE 'Added updated_at trigger to entity_daily_summary';
    END IF;
END $$;

SELECT 'entity_daily_summary created' AS status;
