-- Databrain & Ops Hardening
-- Indexing hot paths, TTL for high-churn tables, and operational views for monitoring.

-- Indexes for graph lookups and messaging (no-op if tables absent)
CREATE INDEX IF NOT EXISTS idx_graph_nodes_label_type ON graph_nodes (label, type);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_label ON graph_nodes (label);
CREATE INDEX IF NOT EXISTS idx_graph_links_source ON graph_links (source_node_id);
CREATE INDEX IF NOT EXISTS idx_graph_links_target ON graph_links (target_node_id);
CREATE INDEX IF NOT EXISTS idx_a2a_messages_created_at ON a2a_messages (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_llm_collaborations_created_at ON llm_collaborations (created_at DESC);

-- TTL policies for event/log tables (CockroachDB TTL)
ALTER TABLE IF EXISTS agent_events SET (ttl_expire_after = '30 days', ttl_job_cron = '@daily');
ALTER TABLE IF EXISTS ingestion_log SET (ttl_expire_after = '30 days', ttl_job_cron = '@daily');
ALTER TABLE IF EXISTS llm_cache_metrics SET (ttl_expire_after = '14 days', ttl_job_cron = '@daily');
ALTER TABLE IF EXISTS job_queue SET (ttl_expire_after = '30 days', ttl_job_cron = '@daily');
ALTER TABLE IF EXISTS email_ingest_state SET (ttl_expire_after = '30 days', ttl_job_cron = '@daily');

-- Observability views (skip if base tables absent)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_sync_lag AS
SELECT
    system,
    status,
    rows_ingested,
    latency_ms,
    now() - COALESCE(last_run, now()) AS lag,
    updated_at
FROM sync_status;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_job_queue_backlog AS
SELECT
    job_type,
    status,
    count(*) AS jobs,
    min(next_run_at) AS next_due,
    max(updated_at) AS last_touch
FROM job_queue
GROUP BY job_type, status;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_ingestion_errors AS
SELECT
    source,
    count(*) AS errors,
    max(finished_at) AS last_error_at
FROM ingestion_log
WHERE status = 'error' OR error IS NOT NULL
GROUP BY source;

