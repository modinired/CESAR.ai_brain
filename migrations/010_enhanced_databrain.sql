-- Enhanced DataBrain & Dashboard Support
-- Adds missing tables for dashboard queries and improves observability/state tracking.

-- Financial intelligence
CREATE TABLE IF NOT EXISTS financial_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_type TEXT NOT NULL,
    value DECIMAL(18,4),
    metadata JSONB DEFAULT '{}'::jsonb,
    source TEXT DEFAULT 'unknown',
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_financial_data_created_at ON financial_data (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_financial_data_type ON financial_data (data_type);

-- Workflow templates referenced by dashboard
CREATE TABLE IF NOT EXISTS workflow_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'active',
    trigger_type TEXT,
    trigger_config JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_workflow_templates_status ON workflow_templates (status);
CREATE INDEX IF NOT EXISTS idx_workflow_templates_updated_at ON workflow_templates (updated_at DESC);

-- Supabase sync tracking
CREATE TABLE IF NOT EXISTS supabase_sync_state (
    table_name TEXT PRIMARY KEY,
    sync_status TEXT DEFAULT 'idle',
    last_sync_at TIMESTAMPTZ,
    last_sync_direction TEXT,
    records_synced INT DEFAULT 0,
    error_message TEXT,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Agent event/audit log
CREATE TABLE IF NOT EXISTS agent_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id TEXT,
    event_type TEXT NOT NULL,
    payload JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_agent_events_agent_id_created_at ON agent_events (agent_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_events_type_created_at ON agent_events (event_type, created_at DESC);

-- Workflow run history
CREATE TABLE IF NOT EXISTS workflow_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID,
    status TEXT NOT NULL DEFAULT 'pending',
    started_at TIMESTAMPTZ DEFAULT now(),
    finished_at TIMESTAMPTZ,
    metrics JSONB DEFAULT '{}'::jsonb,
    error_message TEXT
);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_status_started_at ON workflow_runs (status, started_at DESC);

-- Ingestion logging with idempotency
CREATE TABLE IF NOT EXISTS ingestion_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT,
    item_id TEXT,
    status TEXT DEFAULT 'pending',
    error TEXT,
    started_at TIMESTAMPTZ DEFAULT now(),
    finished_at TIMESTAMPTZ,
    retries INT DEFAULT 0
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_ingestion_log_source_item ON ingestion_log (source, item_id);
CREATE INDEX IF NOT EXISTS idx_ingestion_log_status_started_at ON ingestion_log (status, started_at DESC);

-- System sync/health status
CREATE TABLE IF NOT EXISTS sync_status (
    system TEXT PRIMARY KEY,
    last_run TIMESTAMPTZ,
    status TEXT,
    rows_ingested INT DEFAULT 0,
    latency_ms DECIMAL(12,3) DEFAULT 0,
    error TEXT,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- LLM cache metrics
CREATE TABLE IF NOT EXISTS llm_cache_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_prefix TEXT,
    hits INT DEFAULT 0,
    misses INT DEFAULT 0,
    evictions INT DEFAULT 0,
    recorded_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_llm_cache_metrics_prefix ON llm_cache_metrics (key_prefix);
CREATE INDEX IF NOT EXISTS idx_llm_cache_metrics_recorded_at ON llm_cache_metrics (recorded_at DESC);

-- Email ingest dedup/state
CREATE TABLE IF NOT EXISTS email_ingest_state (
    message_hash TEXT PRIMARY KEY,
    message_id TEXT,
    status TEXT DEFAULT 'processed',
    error TEXT,
    processed_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_email_ingest_state_processed_at ON email_ingest_state (processed_at DESC);

-- Lightweight job queue for retries/background work
CREATE TABLE IF NOT EXISTS job_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type TEXT NOT NULL,
    payload JSONB DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'pending',
    attempts INT DEFAULT 0,
    next_run_at TIMESTAMPTZ DEFAULT now(),
    last_error TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_job_queue_status_next_run ON job_queue (status, next_run_at);
