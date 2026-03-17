-- =============================================================
-- SafeFlow Migration 005: rejected_events table
-- Phase 4 — Data Quality & Validation
--
-- Run:
--   Get-Content infra\sql\005_rejected_events.sql | docker exec -i safeflow-postgres psql -U safeflow -d safeflow
-- =============================================================

CREATE TABLE IF NOT EXISTS rejected_events (
    id              SERIAL PRIMARY KEY,

    -- When and where
    rejected_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    pipeline_stage  VARCHAR(32)  NOT NULL,   -- 'raw' | 'enriched'
    tenant_id       INTEGER,

    -- Why it was rejected
    rejection_code  VARCHAR(64)  NOT NULL,   -- MISSING_FIELD | INVALID_AMOUNT | etc.
    rejection_reason TEXT        NOT NULL,   -- human-readable explanation

    -- Original payload preserved for investigation / replay
    raw_payload     TEXT        NOT NULL,    -- JSON string of the original event

    -- Optional tracing fields (populated when available)
    event_id        VARCHAR(128),            -- transaction_reference or transaction_id
    account_id      VARCHAR(128),
    amount          NUMERIC(18, 2),

    -- Standard timestamps
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_rejected_events_rejected_at
    ON rejected_events (rejected_at DESC);

CREATE INDEX IF NOT EXISTS ix_rejected_events_rejection_code
    ON rejected_events (rejection_code);

CREATE INDEX IF NOT EXISTS ix_rejected_events_tenant_id
    ON rejected_events (tenant_id);

CREATE INDEX IF NOT EXISTS ix_rejected_events_event_id
    ON rejected_events (event_id);

-- updated_at trigger
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'trg_rejected_events_updated_at'
    ) THEN
        CREATE TRIGGER trg_rejected_events_updated_at
            BEFORE UPDATE ON rejected_events
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
        RAISE NOTICE 'Added updated_at trigger to rejected_events';
    END IF;
END $$;

SELECT 'rejected_events created' AS status;
