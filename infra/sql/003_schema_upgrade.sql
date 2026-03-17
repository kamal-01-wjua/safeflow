-- =============================================================
-- SafeFlow Migration 003: Schema Upgrade
-- Phase 2 — constraints, indexes, type fixes, triggers
--
-- Safe to run on existing data.
-- All changes use IF NOT EXISTS / DO blocks to be idempotent.
--
-- Run:
--   Get-Content infra\sql\003_schema_upgrade.sql | docker exec -i safeflow-postgres psql -U safeflow -d safeflow
-- =============================================================

-- -------------------------------------------------------------
-- 1. Unique constraint on transactions(tenant_id, tx_id)
--    Enforces idempotency at the DB level.
--    Worker uses ON CONFLICT DO UPDATE after this exists.
-- -------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_transactions_tenant_tx_id'
    ) THEN
        -- Remove duplicates first (keep lowest id per tenant+tx_id pair)
        DELETE FROM transactions t1
        USING transactions t2
        WHERE t1.tenant_id = t2.tenant_id
          AND t1.tx_id = t2.tx_id
          AND t1.id > t2.id;

        ALTER TABLE transactions
            ADD CONSTRAINT uq_transactions_tenant_tx_id
            UNIQUE (tenant_id, tx_id);

        RAISE NOTICE 'Added uq_transactions_tenant_tx_id';
    ELSE
        RAISE NOTICE 'uq_transactions_tenant_tx_id already exists, skipping';
    END IF;
END $$;


-- -------------------------------------------------------------
-- 2. Foreign key: alerts.transaction_id -> transactions.id
--    Use DEFERRABLE so bulk inserts don't fail on ordering.
--    NULL values allowed (alerts can exist without a tx row).
-- -------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'alerts_transaction_id_fkey'
    ) THEN
        -- Null out any alert transaction_ids that reference non-existent transactions
        UPDATE alerts
        SET transaction_id = NULL
        WHERE transaction_id IS NOT NULL
          AND transaction_id NOT IN (SELECT id FROM transactions);

        ALTER TABLE alerts
            ADD CONSTRAINT alerts_transaction_id_fkey
            FOREIGN KEY (transaction_id)
            REFERENCES transactions(id)
            ON DELETE SET NULL
            DEFERRABLE INITIALLY DEFERRED;

        RAISE NOTICE 'Added alerts_transaction_id_fkey';
    ELSE
        RAISE NOTICE 'alerts_transaction_id_fkey already exists, skipping';
    END IF;
END $$;


-- -------------------------------------------------------------
-- 3. Unique constraint on entities.entity_id
--    Prevents duplicate business keys.
-- -------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_entities_entity_id'
    ) THEN
        -- Remove duplicate entity_ids (keep lowest id)
        DELETE FROM entities e1
        USING entities e2
        WHERE e1.entity_id = e2.entity_id
          AND e1.entity_id IS NOT NULL
          AND e1.id > e2.id;

        ALTER TABLE entities
            ADD CONSTRAINT uq_entities_entity_id
            UNIQUE (entity_id);

        RAISE NOTICE 'Added uq_entities_entity_id';
    ELSE
        RAISE NOTICE 'uq_entities_entity_id already exists, skipping';
    END IF;
END $$;


-- -------------------------------------------------------------
-- 4. Fix entities.risk_score type: double precision -> integer
-- -------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'entities'
          AND column_name = 'risk_score'
          AND data_type = 'double precision'
    ) THEN
        ALTER TABLE entities
            ALTER COLUMN risk_score TYPE integer
            USING ROUND(COALESCE(risk_score, 0))::integer;

        RAISE NOTICE 'Fixed entities.risk_score to integer';
    ELSE
        RAISE NOTICE 'entities.risk_score already correct type, skipping';
    END IF;
END $$;


-- -------------------------------------------------------------
-- 5. Fix alerts score columns: double precision -> integer
--    rule_score, ml_score, graph_score are 0-999 integers.
-- -------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'alerts'
          AND column_name = 'rule_score'
          AND data_type = 'double precision'
    ) THEN
        ALTER TABLE alerts
            ALTER COLUMN rule_score  TYPE integer USING ROUND(COALESCE(rule_score,  0))::integer,
            ALTER COLUMN ml_score    TYPE integer USING ROUND(COALESCE(ml_score,    0))::integer,
            ALTER COLUMN graph_score TYPE integer USING ROUND(COALESCE(graph_score, 0))::integer;

        RAISE NOTICE 'Fixed alerts score columns to integer';
    ELSE
        RAISE NOTICE 'alerts score columns already correct type, skipping';
    END IF;
END $$;


-- -------------------------------------------------------------
-- 6. Add updated_at auto-update trigger function (shared)
-- -------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- Apply trigger to each table
DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOREACH tbl IN ARRAY ARRAY[
        'transactions',
        'alerts',
        'entities',
        'vendors',
        'invoices',
        'employee_expenses',
        'entity_features'
    ] LOOP
        IF NOT EXISTS (
            SELECT 1 FROM pg_trigger
            WHERE tgname = 'trg_' || tbl || '_updated_at'
        ) THEN
            EXECUTE format(
                'CREATE TRIGGER trg_%I_updated_at
                 BEFORE UPDATE ON %I
                 FOR EACH ROW EXECUTE FUNCTION set_updated_at()',
                tbl, tbl
            );
            RAISE NOTICE 'Added updated_at trigger to %', tbl;
        ELSE
            RAISE NOTICE 'updated_at trigger on % already exists, skipping', tbl;
        END IF;
    END LOOP;
END $$;


-- -------------------------------------------------------------
-- 7. Additional performance indexes (IF NOT EXISTS)
-- -------------------------------------------------------------

-- Alerts: composite for dashboard queries (tenant + severity + scored_at)
CREATE INDEX IF NOT EXISTS ix_alerts_tenant_severity_scored
    ON alerts (tenant_id, severity, scored_at DESC);

-- Alerts: composite for entity investigation (account + scored_at)
CREATE INDEX IF NOT EXISTS ix_alerts_account_scored
    ON alerts (account_id, scored_at DESC);

-- Transactions: composite for entity timeline queries
CREATE INDEX IF NOT EXISTS ix_transactions_tenant_account_time
    ON transactions (tenant_id, account_id, tx_time DESC);

-- Entity features: for high-risk entity queries
CREATE INDEX IF NOT EXISTS ix_entity_features_high_risk_count
    ON entity_features (high_risk_tx_count DESC);

-- Entity features: velocity flagged filter
CREATE INDEX IF NOT EXISTS ix_entity_features_velocity_flagged
    ON entity_features (is_velocity_flagged)
    WHERE is_velocity_flagged = TRUE;


-- -------------------------------------------------------------
-- 8. Verification summary
-- -------------------------------------------------------------
SELECT
    'constraints' AS category,
    conname       AS name,
    contype       AS type
FROM pg_constraint
WHERE conname IN (
    'uq_transactions_tenant_tx_id',
    'alerts_transaction_id_fkey',
    'uq_entities_entity_id'
)
ORDER BY conname;
