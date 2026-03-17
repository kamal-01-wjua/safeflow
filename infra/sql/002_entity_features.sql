-- =============================================================
-- SafeFlow Migration: Add entity_features table
-- Run: docker exec -i safeflow-postgres psql -U safeflow -d safeflow < infra/sql/002_entity_features.sql
-- =============================================================

CREATE TABLE IF NOT EXISTS entity_features (
    id                    SERIAL PRIMARY KEY,
    tenant_id             INTEGER NOT NULL,
    account_id            VARCHAR NOT NULL,

    -- Volume
    tx_count_total        INTEGER NOT NULL DEFAULT 0,
    tx_count_24h          INTEGER NOT NULL DEFAULT 0,
    tx_count_7d           INTEGER NOT NULL DEFAULT 0,

    -- Amount
    amount_total          NUMERIC(18, 2) NOT NULL DEFAULT 0.00,
    amount_avg            NUMERIC(18, 2) NOT NULL DEFAULT 0.00,
    amount_max            NUMERIC(18, 2) NOT NULL DEFAULT 0.00,
    amount_last           NUMERIC(18, 2) NOT NULL DEFAULT 0.00,

    -- Risk
    latest_risk_score     INTEGER NOT NULL DEFAULT 0,
    risk_score_avg        NUMERIC(6, 2)  NOT NULL DEFAULT 0.00,
    high_risk_tx_count    INTEGER NOT NULL DEFAULT 0,

    -- Velocity flags
    is_velocity_flagged   BOOLEAN NOT NULL DEFAULT FALSE,
    consecutive_high_risk INTEGER NOT NULL DEFAULT 0,

    -- Temporal
    first_seen_at         TIMESTAMPTZ,
    last_seen_at          TIMESTAMPTZ,

    -- Standard timestamps
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT uq_entity_features_tenant_account UNIQUE (tenant_id, account_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS ix_entity_features_tenant_account
    ON entity_features (tenant_id, account_id);

CREATE INDEX IF NOT EXISTS ix_entity_features_risk_score
    ON entity_features (latest_risk_score);

CREATE INDEX IF NOT EXISTS ix_entity_features_last_seen
    ON entity_features (last_seen_at DESC);
