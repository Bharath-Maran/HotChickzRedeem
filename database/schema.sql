-- Hot Chickz Redemption Schema
-- Run this in your Supabase SQL Editor (or any PostgreSQL instance)
-- Supabase: Dashboard → SQL Editor → New Query → paste & run

CREATE TABLE IF NOT EXISTS slider_claims (
    contact_id      VARCHAR(255) PRIMARY KEY,
    status          VARCHAR(50)  NOT NULL DEFAULT 'unclaimed'
                    CHECK (status IN ('unclaimed', 'active_timer', 'claimed', 'expired')),
    timer_started_at TIMESTAMP WITH TIME ZONE,
    expires_at      TIMESTAMP WITH TIME ZONE,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Speed up status-based lookups (e.g. admin dashboards, bulk expiry jobs)
CREATE INDEX IF NOT EXISTS idx_slider_claims_status
    ON slider_claims (status);

-- Speed up expiry sweeps
CREATE INDEX IF NOT EXISTS idx_slider_claims_expires_at
    ON slider_claims (expires_at)
    WHERE expires_at IS NOT NULL;
