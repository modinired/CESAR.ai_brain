-- ============================================================================
-- CESAR.ai Phase A: Foundation - Database Migration
-- ============================================================================
-- Version: 1.0
-- Date: November 18, 2025
-- Description: Implements Phase A of MCP Integration Plan
--
-- Components:
-- 1. Users & Sessions (identity and context management)
-- 2. LLM Registry (capability tracking)
-- 3. Tool Registry (MCP tool tracking)
-- 4. Routing Rules (capability-based routing engine)
-- 5. Event Audit Trail (complete event logging)
-- 6. Blackboard (multi-agent coordination)
-- 7. Enhanced Reflections (learning improvements)
--
-- Rollback: See 001_phase_a_rollback.sql
-- ============================================================================

BEGIN;

-- ============================================================================
-- Section 1: Users & Sessions
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id            uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_ref  text UNIQUE,
    email         text UNIQUE,
    display_name  text,
    metadata      jsonb DEFAULT '{}'::jsonb,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_users_external_ref ON users(external_ref);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

COMMENT ON TABLE users IS 'User identity management for multi-tenant support';
COMMENT ON COLUMN users.external_ref IS 'External system user ID (e.g., Auth0 sub)';
COMMENT ON COLUMN users.metadata IS 'Flexible user metadata (preferences, settings, etc.)';

-- Default system user for internal operations
INSERT INTO users (external_ref, email, display_name, metadata)
VALUES (
    'system',
    'system@cesar.ai',
    'CESAR System',
    '{"type": "system", "description": "Internal system user for automated operations"}'::jsonb
) ON CONFLICT (external_ref) DO NOTHING;

CREATE TABLE IF NOT EXISTS sessions (
    id            uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id       uuid REFERENCES users(id) ON DELETE SET NULL,
    label         text,
    context       jsonb DEFAULT '{}'::jsonb,
    status        text NOT NULL DEFAULT 'active', -- active, completed, expired, archived
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now(),
    expires_at    timestamptz,
    completed_at  timestamptz
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at) WHERE expires_at IS NOT NULL;

COMMENT ON TABLE sessions IS 'Conversation/context sessions for tracking multi-turn interactions';
COMMENT ON COLUMN sessions.context IS 'Session-specific context (goals, constraints, preferences)';
COMMENT ON COLUMN sessions.status IS 'Session lifecycle: active, completed, expired, archived';

-- Link existing workflow_executions to sessions (add column, don't break existing data)
ALTER TABLE workflow_executions
ADD COLUMN IF NOT EXISTS session_id uuid REFERENCES sessions(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_workflow_executions_session ON workflow_executions(session_id);

-- ============================================================================
-- Section 2: LLM Registry
-- ============================================================================

CREATE TABLE IF NOT EXISTS llms (
    id                  uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                text NOT NULL UNIQUE,
    provider            text NOT NULL, -- openai, anthropic, google, local, etc.
    model_id            text NOT NULL,
    context_tokens      integer,
    max_output_tokens   integer,
    cost_per_1k_input   numeric(10,6),
    cost_per_1k_output  numeric(10,6),
    tags                text[] DEFAULT '{}',
    capabilities        jsonb DEFAULT '{}'::jsonb,
    metadata            jsonb DEFAULT '{}'::jsonb,
    enabled             boolean DEFAULT true,
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_llms_provider ON llms(provider);
CREATE INDEX IF NOT EXISTS idx_llms_enabled ON llms(enabled) WHERE enabled = true;
CREATE INDEX IF NOT EXISTS idx_llms_tags ON llms USING gin(tags);

COMMENT ON TABLE llms IS 'Registry of available LLMs with capabilities and cost tracking';
COMMENT ON COLUMN llms.capabilities IS 'JSON: {code: true, vision: true, function_calling: true, etc.}';
COMMENT ON COLUMN llms.metadata IS 'Additional provider-specific metadata';

-- Populate with common LLMs
INSERT INTO llms (name, provider, model_id, context_tokens, max_output_tokens, cost_per_1k_input, cost_per_1k_output, tags, capabilities) VALUES
('GPT-4o', 'openai', 'gpt-4o-2024-11-20', 128000, 16384, 2.50, 10.00, ARRAY['chat', 'code', 'vision', 'analysis'], '{"code": true, "vision": true, "function_calling": true, "structured_output": true}'::jsonb),
('GPT-4o-mini', 'openai', 'gpt-4o-mini', 128000, 16384, 0.15, 0.60, ARRAY['chat', 'code', 'fast'], '{"code": true, "function_calling": true, "structured_output": true}'::jsonb),
('Claude Sonnet 4.5', 'anthropic', 'claude-sonnet-4-5-20250929', 200000, 8192, 3.00, 15.00, ARRAY['chat', 'code', 'analysis', 'reasoning'], '{"code": true, "vision": true, "tool_use": true, "extended_thinking": true}'::jsonb),
('Claude Haiku 3.5', 'anthropic', 'claude-3-5-haiku-20241022', 200000, 8192, 0.80, 4.00, ARRAY['chat', 'fast'], '{"code": true, "tool_use": true}'::jsonb),
('Gemini 2.0 Flash', 'google', 'gemini-2.0-flash-exp', 1000000, 8192, 0.00, 0.00, ARRAY['chat', 'code', 'vision', 'experimental'], '{"code": true, "vision": true, "multimodal": true, "long_context": true}'::jsonb)
ON CONFLICT (name) DO UPDATE SET
    model_id = EXCLUDED.model_id,
    context_tokens = EXCLUDED.context_tokens,
    capabilities = EXCLUDED.capabilities,
    updated_at = now();

-- ============================================================================
-- Section 3: Tool Registry
-- ============================================================================

CREATE TABLE IF NOT EXISTS tools (
    id                uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    name              text NOT NULL,
    mcp_server        text,
    endpoint          text,
    description       text,
    parameters_schema jsonb,
    tags              text[] DEFAULT '{}',
    agent_id          text REFERENCES agents(agent_id) ON DELETE SET NULL,
    mcp_system        text,
    enabled           boolean DEFAULT true,
    created_at        timestamptz NOT NULL DEFAULT now(),
    updated_at        timestamptz NOT NULL DEFAULT now(),
    UNIQUE(name, mcp_server)
);

CREATE INDEX IF NOT EXISTS idx_tools_agent ON tools(agent_id);
CREATE INDEX IF NOT EXISTS idx_tools_mcp_system ON tools(mcp_system);
CREATE INDEX IF NOT EXISTS idx_tools_tags ON tools USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_tools_enabled ON tools(enabled) WHERE enabled = true;

COMMENT ON TABLE tools IS 'Registry of all available tools/functions across MCP systems';
COMMENT ON COLUMN tools.parameters_schema IS 'JSON Schema for tool parameters';
COMMENT ON COLUMN tools.mcp_server IS 'MCP server hosting this tool (if applicable)';
COMMENT ON COLUMN tools.agent_id IS 'Agent providing this tool (if agent-specific)';

-- ============================================================================
-- Section 4: Routing Rules (Capability-Based Routing Engine)
-- ============================================================================

CREATE TABLE IF NOT EXISTS routing_rules (
    id                uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    name              text NOT NULL UNIQUE,
    description       text,
    priority          integer NOT NULL DEFAULT 100,
    task_tags         text[] NOT NULL DEFAULT '{}',
    preferred_llm     uuid REFERENCES llms(id) ON DELETE SET NULL,
    preferred_agent   text REFERENCES agents(agent_id) ON DELETE SET NULL,
    preferred_tools   uuid[],
    constraints       jsonb DEFAULT '{}'::jsonb,
    enabled           boolean DEFAULT true,
    success_count     integer DEFAULT 0,
    failure_count     integer DEFAULT 0,
    avg_duration_ms   numeric(10,2),
    created_at        timestamptz NOT NULL DEFAULT now(),
    updated_at        timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_routing_priority ON routing_rules(priority ASC, created_at ASC) WHERE enabled = true;
CREATE INDEX IF NOT EXISTS idx_routing_tags ON routing_rules USING gin(task_tags);
CREATE INDEX IF NOT EXISTS idx_routing_llm ON routing_rules(preferred_llm);
CREATE INDEX IF NOT EXISTS idx_routing_agent ON routing_rules(preferred_agent);

COMMENT ON TABLE routing_rules IS 'Capability-based routing rules for intelligent task assignment';
COMMENT ON COLUMN routing_rules.priority IS 'Lower number = higher priority (1 is highest)';
COMMENT ON COLUMN routing_rules.task_tags IS 'Tags that trigger this rule (e.g., [finance, analysis])';
COMMENT ON COLUMN routing_rules.constraints IS 'Additional constraints (cost, latency, etc.)';
COMMENT ON COLUMN routing_rules.success_count IS 'Tracks routing effectiveness for continual learning';

-- ============================================================================
-- Section 5: Event Audit Trail
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_runs (
    id              uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      uuid REFERENCES sessions(id) ON DELETE SET NULL,
    user_id         uuid REFERENCES users(id) ON DELETE SET NULL,
    agent_id        text REFERENCES agents(agent_id) ON DELETE SET NULL,
    workflow_id     uuid REFERENCES workflow_executions(id) ON DELETE SET NULL,
    routing_rule_id uuid REFERENCES routing_rules(id) ON DELETE SET NULL,
    status          text NOT NULL DEFAULT 'running', -- running, completed, failed, cancelled
    input_summary   text,
    output_summary  text,
    error_message   text,
    metadata        jsonb DEFAULT '{}'::jsonb,
    created_at      timestamptz NOT NULL DEFAULT now(),
    started_at      timestamptz,
    completed_at    timestamptz,
    duration_ms     integer
);

CREATE INDEX IF NOT EXISTS idx_agent_runs_session ON agent_runs(session_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_runs_agent ON agent_runs(agent_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_runs_status ON agent_runs(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_runs_workflow ON agent_runs(workflow_id);

COMMENT ON TABLE agent_runs IS 'Tracks individual agent execution runs for audit trail';
COMMENT ON COLUMN agent_runs.routing_rule_id IS 'Which routing rule selected this agent (if applicable)';
COMMENT ON COLUMN agent_runs.duration_ms IS 'Total execution time in milliseconds';

CREATE TABLE IF NOT EXISTS events (
    id            uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id        uuid REFERENCES agent_runs(id) ON DELETE CASCADE,
    session_id    uuid REFERENCES sessions(id) ON DELETE SET NULL,
    agent_id      text REFERENCES agents(agent_id) ON DELETE SET NULL,
    event_type    text NOT NULL,
    payload       jsonb,
    metadata      jsonb DEFAULT '{}'::jsonb,
    created_at    timestamptz NOT NULL DEFAULT now(),
    handled_by    uuid[] DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_events_run ON events(run_id, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_agent ON events(agent_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at DESC);

-- Partition events by month for performance (optional, can be enabled later)
-- CREATE TABLE events_2025_11 PARTITION OF events FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

COMMENT ON TABLE events IS 'Complete audit trail of all system events (persisted + real-time)';
COMMENT ON COLUMN events.handled_by IS 'Array of agent IDs that have processed this event';

CREATE TABLE IF NOT EXISTS tool_invocations (
    id            uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id      uuid REFERENCES events(id) ON DELETE CASCADE,
    run_id        uuid REFERENCES agent_runs(id) ON DELETE CASCADE,
    tool_id       uuid REFERENCES tools(id) ON DELETE SET NULL,
    agent_id      text REFERENCES agents(agent_id) ON DELETE SET NULL,
    request       jsonb,
    response      jsonb,
    error         text,
    duration_ms   integer,
    created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tool_invocations_event ON tool_invocations(event_id);
CREATE INDEX IF NOT EXISTS idx_tool_invocations_run ON tool_invocations(run_id);
CREATE INDEX IF NOT EXISTS idx_tool_invocations_tool ON tool_invocations(tool_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tool_invocations_agent ON tool_invocations(agent_id, created_at DESC);

COMMENT ON TABLE tool_invocations IS 'Tracks all tool/function calls for analytics and debugging';

-- ============================================================================
-- Section 6: Blackboard (Multi-Agent Coordination)
-- ============================================================================

CREATE TABLE IF NOT EXISTS blackboard_entries (
    id            uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id    uuid REFERENCES sessions(id) ON DELETE CASCADE,
    user_id       uuid REFERENCES users(id) ON DELETE SET NULL,
    agent_id      text REFERENCES agents(agent_id) ON DELETE SET NULL,
    title         text,
    content       text NOT NULL,
    content_type  text DEFAULT 'text', -- text, json, markdown, etc.
    tags          text[] DEFAULT '{}',
    priority      integer DEFAULT 0,
    version       integer DEFAULT 1,
    parent_id     uuid REFERENCES blackboard_entries(id) ON DELETE SET NULL,
    expires_at    timestamptz,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_blackboard_session ON blackboard_entries(session_id, priority DESC, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_blackboard_agent ON blackboard_entries(agent_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_blackboard_expires ON blackboard_entries(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_blackboard_tags ON blackboard_entries USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_blackboard_parent ON blackboard_entries(parent_id);

COMMENT ON TABLE blackboard_entries IS 'Temporary shared state for multi-agent coordination (blackboard pattern)';
COMMENT ON COLUMN blackboard_entries.priority IS 'Higher number = higher priority (for sorting)';
COMMENT ON COLUMN blackboard_entries.version IS 'Optimistic concurrency control';
COMMENT ON COLUMN blackboard_entries.parent_id IS 'For threaded/nested entries';

-- ============================================================================
-- Section 7: Enhanced Reflections
-- ============================================================================

-- Enhance existing learning_reflections table
ALTER TABLE learning_reflections
ADD COLUMN IF NOT EXISTS rating text,
ADD COLUMN IF NOT EXISTS tags text[],
ADD COLUMN IF NOT EXISTS session_id uuid REFERENCES sessions(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS run_id uuid REFERENCES agent_runs(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS metadata jsonb DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS idx_reflections_rating ON learning_reflections(rating) WHERE rating IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_reflections_tags ON learning_reflections USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_reflections_session ON learning_reflections(session_id);
CREATE INDEX IF NOT EXISTS idx_reflections_run ON learning_reflections(run_id);

COMMENT ON COLUMN learning_reflections.rating IS 'Quality rating: positive, negative, neutral, excellent';
COMMENT ON COLUMN learning_reflections.tags IS 'Categorization tags for querying';
COMMENT ON COLUMN learning_reflections.session_id IS 'Link to session context';
COMMENT ON COLUMN learning_reflections.run_id IS 'Link to specific agent run';

-- ============================================================================
-- Section 8: Materialized Views for Performance
-- ============================================================================

-- Routing effectiveness view
CREATE MATERIALIZED VIEW IF NOT EXISTS routing_effectiveness AS
SELECT
    rr.id as rule_id,
    rr.name as rule_name,
    rr.priority,
    rr.task_tags,
    rr.success_count,
    rr.failure_count,
    CASE
        WHEN (rr.success_count + rr.failure_count) > 0
        THEN (rr.success_count::float / (rr.success_count + rr.failure_count) * 100)
        ELSE 0
    END as success_rate,
    rr.avg_duration_ms,
    COUNT(ar.id) as total_uses,
    rr.created_at
FROM routing_rules rr
LEFT JOIN agent_runs ar ON ar.routing_rule_id = rr.id
WHERE rr.enabled = true
GROUP BY rr.id, rr.name, rr.priority, rr.task_tags, rr.success_count, rr.failure_count, rr.avg_duration_ms, rr.created_at
ORDER BY rr.priority ASC;

CREATE UNIQUE INDEX IF NOT EXISTS idx_routing_effectiveness_rule ON routing_effectiveness(rule_id);

COMMENT ON MATERIALIZED VIEW routing_effectiveness IS 'Real-time routing rule effectiveness metrics';

-- Agent activity summary
CREATE MATERIALIZED VIEW IF NOT EXISTS agent_activity_summary AS
SELECT
    a.agent_id,
    a.name as agent_name,
    a.type as agent_type,
    a.mcp_system,
    COUNT(DISTINCT ar.id) as total_runs,
    COUNT(DISTINCT ar.id) FILTER (WHERE ar.status = 'completed') as completed_runs,
    COUNT(DISTINCT ar.id) FILTER (WHERE ar.status = 'failed') as failed_runs,
    AVG(ar.duration_ms) as avg_duration_ms,
    COUNT(DISTINCT ti.id) as total_tool_invocations,
    MAX(ar.created_at) as last_run_at
FROM agents a
LEFT JOIN agent_runs ar ON ar.agent_id = a.agent_id
LEFT JOIN tool_invocations ti ON ti.agent_id = a.agent_id
GROUP BY a.agent_id, a.name, a.type, a.mcp_system;

CREATE UNIQUE INDEX IF NOT EXISTS idx_agent_activity_agent ON agent_activity_summary(agent_id);

COMMENT ON MATERIALIZED VIEW agent_activity_summary IS 'Agent activity and performance summary';

-- ============================================================================
-- Section 9: Functions & Triggers
-- ============================================================================

-- Function to auto-update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to all relevant tables
DO $$
DECLARE
    t text;
BEGIN
    FOR t IN
        SELECT table_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND column_name = 'updated_at'
          AND table_name NOT LIKE '%_old'
    LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS update_%I_updated_at ON %I;
            CREATE TRIGGER update_%I_updated_at
                BEFORE UPDATE ON %I
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        ', t, t, t, t);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup expired blackboard entries
CREATE OR REPLACE FUNCTION cleanup_expired_blackboard()
RETURNS integer AS $$
DECLARE
    deleted_count integer;
BEGIN
    DELETE FROM blackboard_entries
    WHERE expires_at IS NOT NULL
      AND expires_at < now();

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_expired_blackboard IS 'Removes expired blackboard entries. Run periodically via cron or background job.';

-- Function to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY routing_effectiveness;
    REFRESH MATERIALIZED VIEW CONCURRENTLY agent_activity_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY agent_performance_overview;
    REFRESH MATERIALIZED VIEW CONCURRENTLY workflow_status_summary;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_all_materialized_views IS 'Refreshes all materialized views. Run periodically for up-to-date analytics.';

-- ============================================================================
-- Section 10: Grants & Permissions
-- ============================================================================

-- Grant appropriate permissions (adjust based on your user setup)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO current_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO current_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO current_user;

-- ============================================================================
-- Section 11: Data Validation
-- ============================================================================

-- Verify all tables were created
DO $$
DECLARE
    expected_tables text[] := ARRAY[
        'users', 'sessions', 'llms', 'tools', 'routing_rules',
        'agent_runs', 'events', 'tool_invocations', 'blackboard_entries'
    ];
    missing_tables text[];
    t text;
BEGIN
    SELECT array_agg(table_name)
    INTO missing_tables
    FROM unnest(expected_tables) AS table_name
    WHERE NOT EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = table_name
    );

    IF array_length(missing_tables, 1) > 0 THEN
        RAISE EXCEPTION 'Missing tables: %', array_to_string(missing_tables, ', ');
    ELSE
        RAISE NOTICE '✅ All Phase A tables created successfully';
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMIT;

-- ============================================================================
-- Post-Migration Instructions
-- ============================================================================

-- Run this after migration:
-- 1. Refresh materialized views:
--    SELECT refresh_all_materialized_views();
--
-- 2. Verify data:
--    SELECT COUNT(*) FROM users;
--    SELECT COUNT(*) FROM llms;
--    SELECT * FROM routing_effectiveness;
--
-- 3. Set up cron job for blackboard cleanup (every 5 minutes):
--    SELECT cron.schedule('cleanup-blackboard', '*/5 * * * *', 'SELECT cleanup_expired_blackboard()');
--
-- 4. Set up cron job for materialized view refresh (every hour):
--    SELECT cron.schedule('refresh-views', '0 * * * *', 'SELECT refresh_all_materialized_views()');
--
-- ============================================================================
