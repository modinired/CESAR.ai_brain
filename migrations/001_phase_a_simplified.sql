-- ============================================================================
-- CESAR.ai Phase A: Foundation - Simplified Migration
-- ============================================================================
-- Version: 1.1 (Simplified - works with existing schema)
-- Date: November 18, 2025
-- Description: Adds only new tables, preserves existing users table
-- ============================================================================

BEGIN;

-- ============================================================================
-- Section 1: Sessions (uses existing users table)
-- ============================================================================

CREATE TABLE IF NOT EXISTS sessions (
    id            uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id       uuid REFERENCES users(id) ON DELETE SET NULL,
    label         text,
    context       jsonb DEFAULT '{}'::jsonb,
    status        text NOT NULL DEFAULT 'active',
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now(),
    expires_at    timestamptz,
    completed_at  timestamptz
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at) WHERE expires_at IS NOT NULL;

-- Link workflow_executions to sessions
ALTER TABLE workflow_executions
ADD COLUMN IF NOT EXISTS session_id uuid REFERENCES sessions(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_workflow_executions_session ON workflow_executions(session_id);

-- ============================================================================
-- Section 2: LLM Registry
-- ============================================================================

CREATE TABLE IF NOT EXISTS llms (
    id                  uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                text NOT NULL UNIQUE,
    provider            text NOT NULL,
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

-- Populate with common LLMs
INSERT INTO llms (name, provider, model_id, context_tokens, max_output_tokens, cost_per_1k_input, cost_per_1k_output, tags, capabilities) VALUES
('GPT-4o', 'openai', 'gpt-4o-2024-11-20', 128000, 16384, 2.50, 10.00, ARRAY['chat', 'code', 'vision', 'analysis'], '{"code": true, "vision": true, "function_calling": true}'::jsonb),
('GPT-4o-mini', 'openai', 'gpt-4o-mini', 128000, 16384, 0.15, 0.60, ARRAY['chat', 'code', 'fast'], '{"code": true, "function_calling": true}'::jsonb),
('Claude Sonnet 4.5', 'anthropic', 'claude-sonnet-4-5-20250929', 200000, 8192, 3.00, 15.00, ARRAY['chat', 'code', 'analysis'], '{"code": true, "vision": true, "tool_use": true}'::jsonb),
('Claude Haiku 3.5', 'anthropic', 'claude-3-5-haiku-20241022', 200000, 8192, 0.80, 4.00, ARRAY['chat', 'fast'], '{"code": true, "tool_use": true}'::jsonb),
('Gemini 2.0 Flash', 'google', 'gemini-2.0-flash-exp', 1000000, 8192, 0.00, 0.00, ARRAY['chat', 'code', 'vision'], '{"code": true, "vision": true, "multimodal": true}'::jsonb)
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
    updated_at        timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_tools_name_server ON tools(name, COALESCE(mcp_server, ''));

CREATE INDEX IF NOT EXISTS idx_tools_agent ON tools(agent_id);
CREATE INDEX IF NOT EXISTS idx_tools_mcp_system ON tools(mcp_system);
CREATE INDEX IF NOT EXISTS idx_tools_tags ON tools USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_tools_enabled ON tools(enabled) WHERE enabled = true;

-- ============================================================================
-- Section 4: Routing Rules
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
    status          text NOT NULL DEFAULT 'running',
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
CREATE INDEX IF NOT EXISTS idx_tool_invocations_tool ON tool_invocations(tool_id, created_at DESC);

-- ============================================================================
-- Section 6: Blackboard
-- ============================================================================

CREATE TABLE IF NOT EXISTS blackboard_entries (
    id            uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id    uuid REFERENCES sessions(id) ON DELETE CASCADE,
    user_id       uuid REFERENCES users(id) ON DELETE SET NULL,
    agent_id      text REFERENCES agents(agent_id) ON DELETE SET NULL,
    title         text,
    content       text NOT NULL,
    content_type  text DEFAULT 'text',
    tags          text[] DEFAULT '{}',
    priority      integer DEFAULT 0,
    expires_at    timestamptz,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_blackboard_session ON blackboard_entries(session_id, priority DESC, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_blackboard_expires ON blackboard_entries(expires_at) WHERE expires_at IS NOT NULL;

-- ============================================================================
-- Section 7: Enhanced Reflections
-- ============================================================================

ALTER TABLE learning_reflections
ADD COLUMN IF NOT EXISTS rating text,
ADD COLUMN IF NOT EXISTS tags text[],
ADD COLUMN IF NOT EXISTS session_id uuid REFERENCES sessions(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS run_id uuid REFERENCES agent_runs(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS metadata_extra jsonb DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS idx_reflections_rating ON learning_reflections(rating) WHERE rating IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_reflections_tags ON learning_reflections USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_reflections_session ON learning_reflections(session_id);

-- ============================================================================
-- Section 8: Functions
-- ============================================================================

CREATE OR REPLACE FUNCTION cleanup_expired_blackboard()
RETURNS integer AS $$
DECLARE
    deleted_count integer;
BEGIN
    DELETE FROM blackboard_entries
    WHERE expires_at IS NOT NULL AND expires_at < now();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMIT;

-- Success message
SELECT 'Phase A migration completed successfully!' as status;
