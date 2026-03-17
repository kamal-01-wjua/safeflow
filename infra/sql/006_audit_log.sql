-- =============================================================
-- SafeFlow Migration 006: audit_log table
-- Phase 5 — Backend Engineering Upgrade
--
-- Stores write actions performed by authenticated users.
-- Used for future case management and compliance trail.
--
-- Run:
--   Get-Content infra\sql\006_audit_log.sql | docker exec -i safeflow-postgres psql -U safeflow -d safeflow
-- =============================================================

CREATE TABLE IF NOT EXISTS audit_log (
    id              SERIAL PRIMARY KEY,

    -- Who
    username        VARCHAR(128) NOT NULL,
    role            VARCHAR(32)  NOT NULL,

    -- What
    action          VARCHAR(64)  NOT NULL,   -- e.g. CREATE_TRANSACTION, UPDATE_ENTITY
    resource_type   VARCHAR(64)  NOT NULL,   -- e.g. transaction, alert, entity
    resource_id     VARCHAR(128),            -- DB id of affected resource

    -- Context
    endpoint        VARCHAR(256),            -- API path
    http_method     VARCHAR(8),              -- GET, POST, PUT, DELETE
    request_body    TEXT,                    -- JSON snapshot of request (sanitized)
    status_code     INTEGER,                 -- HTTP response code

    -- When
    performed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_audit_log_username
    ON audit_log (username);

CREATE INDEX IF NOT EXISTS ix_audit_log_performed_at
    ON audit_log (performed_at DESC);

CREATE INDEX IF NOT EXISTS ix_audit_log_resource
    ON audit_log (resource_type, resource_id);

CREATE INDEX IF NOT EXISTS ix_audit_log_action
    ON audit_log (action);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'trg_audit_log_updated_at'
    ) THEN
        CREATE TRIGGER trg_audit_log_updated_at
            BEFORE UPDATE ON audit_log
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
        RAISE NOTICE 'Added updated_at trigger to audit_log';
    END IF;
END $$;

SELECT 'audit_log created' AS status;
