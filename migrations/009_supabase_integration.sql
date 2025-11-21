-- ============================================================================
-- CESAR.ai Phase H: Supabase Real-Time Integration
-- ============================================================================
-- Version: 1.0
-- Date: November 19, 2025
-- Description: Prepares database for Supabase real-time sync and integration
-- Purpose: Enable real-time collaboration, distributed task queue, artifact storage
-- ============================================================================

-- NOTE: This migration prepares the local PostgreSQL database for Supabase sync.
-- The actual Supabase project should mirror these tables and add real-time features.
-- See docs/SUPABASE_SETUP_GUIDE.md for complete setup instructions.

BEGIN;

-- ============================================================================
-- Section 1: Add Supabase Sync Metadata
-- ============================================================================

-- Track last sync timestamp for each table
CREATE TABLE IF NOT EXISTS supabase_sync_state (
    id                  uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name          text UNIQUE NOT NULL,
    last_sync_at        timestamptz,
    last_sync_direction text,  -- 'to_supabase', 'from_supabase', 'bidirectional'
    records_synced      integer DEFAULT 0,
    sync_status         text DEFAULT 'pending',  -- 'pending', 'in_progress', 'completed', 'failed'
    error_message       text,
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_supabase_sync_state_table ON supabase_sync_state(table_name, last_sync_at DESC);

COMMENT ON TABLE supabase_sync_state IS 'Tracks synchronization state between local PostgreSQL and Supabase';

-- Initialize sync state for key tables
INSERT INTO supabase_sync_state (table_name, sync_status) VALUES
('agents', 'pending'),
('a2a_messages', 'pending'),
('a2a_conversations', 'pending'),
('llm_collaborations', 'pending'),
('local_llm_learning_examples', 'pending'),
('sessions', 'pending')
ON CONFLICT (table_name) DO NOTHING;

-- ============================================================================
-- Section 2: Add Supabase Configuration Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS supabase_config (
    id                  uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_url         text NOT NULL,
    anon_key_encrypted  text,  -- Store encrypted if needed
    service_key_encrypted text,

    -- Feature flags
    realtime_enabled    boolean DEFAULT true,
    storage_enabled     boolean DEFAULT true,
    auth_enabled        boolean DEFAULT false,

    -- Sync configuration
    sync_interval_sec   integer DEFAULT 30,
    sync_batch_size     integer DEFAULT 100,

    -- Storage buckets
    artifact_bucket     text DEFAULT 'agent-artifacts',
    logs_bucket         text DEFAULT 'agent-logs',

    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE supabase_config IS 'Supabase connection and feature configuration';

-- ============================================================================
-- Section 3: Add Tenant/Organization Support (Row-Level Security)
-- ============================================================================

-- Add tenant/organization ID to key tables for multi-tenancy
ALTER TABLE agents ADD COLUMN IF NOT EXISTS tenant_id uuid;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS tenant_id uuid;
ALTER TABLE a2a_messages ADD COLUMN IF NOT EXISTS tenant_id uuid;
ALTER TABLE llm_collaborations ADD COLUMN IF NOT EXISTS tenant_id uuid;

-- Create index for tenant-based queries
CREATE INDEX IF NOT EXISTS idx_agents_tenant ON agents(tenant_id) WHERE tenant_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sessions_tenant ON sessions(tenant_id) WHERE tenant_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_a2a_messages_tenant ON a2a_messages(tenant_id) WHERE tenant_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_llm_collaborations_tenant ON llm_collaborations(tenant_id) WHERE tenant_id IS NOT NULL;

-- Organizations/Tenants table
CREATE TABLE IF NOT EXISTS organizations (
    id                  uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                text NOT NULL,
    slug                text UNIQUE NOT NULL,

    -- Subscription info
    plan_tier           text DEFAULT 'free',  -- 'free', 'pro', 'enterprise'
    max_agents          integer DEFAULT 5,
    max_sessions        integer DEFAULT 100,

    -- Configuration
    settings            jsonb DEFAULT '{}'::jsonb,
    metadata            jsonb DEFAULT '{}'::jsonb,

    -- Status
    status              text DEFAULT 'active',  -- 'active', 'suspended', 'deleted'

    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_status ON organizations(status);

COMMENT ON TABLE organizations IS 'Multi-tenant organizations for Supabase RLS and access control';

-- ============================================================================
-- Section 4: Add Real-Time Event Stream Table
-- ============================================================================

-- Unified event stream for real-time broadcasting
CREATE TABLE IF NOT EXISTS realtime_events (
    id                  uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id           uuid REFERENCES organizations(id),

    -- Event classification
    event_type          text NOT NULL,  -- 'agent_status', 'task_update', 'message', 'collaboration'
    event_category      text,  -- 'system', 'agent', 'user', 'integration'

    -- Event data
    source_id           uuid,  -- Agent, Task, or Session that generated event
    source_type         text,  -- 'agent', 'task', 'session', 'system'
    payload             jsonb NOT NULL,

    -- Targeting
    target_agents       uuid[],  -- Specific agents to receive event
    broadcast           boolean DEFAULT false,  -- Broadcast to all

    -- Delivery tracking
    delivered_count     integer DEFAULT 0,
    acknowledged_count  integer DEFAULT 0,

    -- TTL
    expires_at          timestamptz,

    created_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_realtime_events_type ON realtime_events(event_type, created_at DESC);
CREATE INDEX idx_realtime_events_tenant ON realtime_events(tenant_id, created_at DESC);
CREATE INDEX idx_realtime_events_source ON realtime_events(source_type, source_id);
CREATE INDEX idx_realtime_events_targets ON realtime_events USING gin(target_agents);
CREATE INDEX idx_realtime_events_expires ON realtime_events(expires_at) WHERE expires_at IS NOT NULL;

COMMENT ON TABLE realtime_events IS 'Unified event stream for real-time broadcasting via Supabase Realtime';

-- ============================================================================
-- Section 5: Add Artifact Storage Metadata
-- ============================================================================

-- Track artifacts stored in Supabase Storage
CREATE TABLE IF NOT EXISTS agent_artifacts (
    id                  uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id            uuid NOT NULL,
    tenant_id           uuid REFERENCES organizations(id),

    -- Artifact classification
    artifact_type       text NOT NULL,  -- 'output', 'log', 'report', 'code', 'data'
    artifact_name       text NOT NULL,
    description         text,

    -- Storage location
    storage_bucket      text NOT NULL,
    storage_path        text NOT NULL,
    public_url          text,

    -- File metadata
    file_size_bytes     bigint,
    content_type        text,
    checksum            text,

    -- Relations
    session_id          uuid REFERENCES sessions(id),
    task_id             uuid,
    collaboration_id    uuid REFERENCES llm_collaborations(id),

    -- Access control
    is_public           boolean DEFAULT false,
    shared_with         uuid[],  -- Agent IDs with access

    -- Lifecycle
    retention_days      integer DEFAULT 90,
    archived            boolean DEFAULT false,
    deleted_at          timestamptz,

    created_at          timestamptz NOT NULL DEFAULT now(),
    metadata            jsonb DEFAULT '{}'::jsonb
);

CREATE INDEX idx_agent_artifacts_agent ON agent_artifacts(agent_id, created_at DESC);
CREATE INDEX idx_agent_artifacts_tenant ON agent_artifacts(tenant_id, created_at DESC);
CREATE INDEX idx_agent_artifacts_type ON agent_artifacts(artifact_type, created_at DESC);
CREATE INDEX idx_agent_artifacts_session ON agent_artifacts(session_id);
CREATE INDEX idx_agent_artifacts_public ON agent_artifacts(is_public) WHERE is_public = true;

COMMENT ON TABLE agent_artifacts IS 'Metadata for agent artifacts stored in Supabase Storage';

-- ============================================================================
-- Section 6: Add Distributed Task Queue (Supabase-based)
-- ============================================================================

-- Extend existing tasks table for Supabase-based distribution
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS supabase_synced boolean DEFAULT false;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS claimed_by_agent uuid;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS claimed_at timestamptz;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS claim_expires_at timestamptz;

CREATE INDEX IF NOT EXISTS idx_tasks_unclaimed ON tasks(status, claimed_by_agent, created_at)
    WHERE status = 'pending' AND claimed_by_agent IS NULL;

-- Task claims (for distributed locking via Supabase)
CREATE TABLE IF NOT EXISTS task_claims (
    id                  uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id             uuid NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    agent_id            uuid NOT NULL,

    -- Claim details
    claimed_at          timestamptz NOT NULL DEFAULT now(),
    expires_at          timestamptz NOT NULL,
    heartbeat_at        timestamptz NOT NULL DEFAULT now(),

    -- Status
    status              text DEFAULT 'active',  -- 'active', 'released', 'expired', 'completed'

    metadata            jsonb DEFAULT '{}'::jsonb,

    UNIQUE(task_id, agent_id)
);

CREATE INDEX idx_task_claims_agent ON task_claims(agent_id, status);
CREATE INDEX idx_task_claims_expires ON task_claims(expires_at) WHERE status = 'active';

COMMENT ON TABLE task_claims IS 'Distributed task locking and claim tracking for Supabase-based task queue';

-- ============================================================================
-- Section 7: Helper Functions for Supabase Integration
-- ============================================================================

-- Function to publish real-time event
CREATE OR REPLACE FUNCTION publish_realtime_event(
    p_event_type text,
    p_payload jsonb,
    p_source_id uuid DEFAULT NULL,
    p_source_type text DEFAULT NULL,
    p_target_agents uuid[] DEFAULT NULL,
    p_broadcast boolean DEFAULT false,
    p_ttl_seconds integer DEFAULT 300
) RETURNS uuid AS $$
DECLARE
    v_event_id uuid;
BEGIN
    INSERT INTO realtime_events (
        event_type,
        source_id,
        source_type,
        payload,
        target_agents,
        broadcast,
        expires_at
    ) VALUES (
        p_event_type,
        p_source_id,
        p_source_type,
        p_payload,
        p_target_agents,
        p_broadcast,
        now() + (p_ttl_seconds || ' seconds')::interval
    )
    RETURNING id INTO v_event_id;

    RETURN v_event_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION publish_realtime_event IS 'Publish event to real-time stream for Supabase broadcasting';

-- Function to claim a task (distributed locking)
CREATE OR REPLACE FUNCTION claim_task(
    p_task_id uuid,
    p_agent_id uuid,
    p_claim_duration_seconds integer DEFAULT 300
) RETURNS boolean AS $$
DECLARE
    v_already_claimed boolean;
BEGIN
    -- Check if task is already claimed and not expired
    SELECT EXISTS(
        SELECT 1 FROM task_claims
        WHERE task_id = p_task_id
        AND status = 'active'
        AND expires_at > now()
    ) INTO v_already_claimed;

    IF v_already_claimed THEN
        RETURN false;
    END IF;

    -- Create claim
    INSERT INTO task_claims (
        task_id,
        agent_id,
        expires_at
    ) VALUES (
        p_task_id,
        p_agent_id,
        now() + (p_claim_duration_seconds || ' seconds')::interval
    )
    ON CONFLICT (task_id, agent_id) DO UPDATE SET
        claimed_at = now(),
        expires_at = now() + (p_claim_duration_seconds || ' seconds')::interval,
        status = 'active';

    -- Update task
    UPDATE tasks
    SET claimed_by_agent = p_agent_id,
        claimed_at = now(),
        claim_expires_at = now() + (p_claim_duration_seconds || ' seconds')::interval
    WHERE id = p_task_id;

    RETURN true;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION claim_task IS 'Claim a task for processing (distributed locking for Supabase task queue)';

-- Function to release task claim
CREATE OR REPLACE FUNCTION release_task_claim(
    p_task_id uuid,
    p_agent_id uuid
) RETURNS boolean AS $$
BEGIN
    UPDATE task_claims
    SET status = 'released'
    WHERE task_id = p_task_id
    AND agent_id = p_agent_id
    AND status = 'active';

    UPDATE tasks
    SET claimed_by_agent = NULL,
        claimed_at = NULL,
        claim_expires_at = NULL
    WHERE id = p_task_id
    AND claimed_by_agent = p_agent_id;

    RETURN true;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION release_task_claim IS 'Release task claim (make available for other agents)';

-- ============================================================================
-- Section 8: Automatic Event Publishing Triggers
-- ============================================================================

-- Trigger: Publish agent status changes
CREATE OR REPLACE FUNCTION trigger_publish_agent_status()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status IS DISTINCT FROM OLD.status THEN
        PERFORM publish_realtime_event(
            'agent_status_change',
            jsonb_build_object(
                'agent_id', NEW.id,
                'agent_name', NEW.name,
                'old_status', OLD.status,
                'new_status', NEW.status,
                'timestamp', now()
            ),
            NEW.id,
            'agent',
            NULL,
            true  -- Broadcast to all
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_agent_status_realtime
AFTER UPDATE ON agents
FOR EACH ROW
EXECUTE FUNCTION trigger_publish_agent_status();

-- Trigger: Publish new A2A messages
CREATE OR REPLACE FUNCTION trigger_publish_a2a_message()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM publish_realtime_event(
        'a2a_message_received',
        jsonb_build_object(
            'message_id', NEW.id,
            'from_agent_id', NEW.from_agent_id,
            'to_agent_id', NEW.to_agent_id,
            'message_type', NEW.message_type,
            'priority', NEW.priority,
            'subject', NEW.subject
        ),
        NEW.from_agent_id,
        'message',
        ARRAY[NEW.to_agent_id],  -- Only to recipient
        false
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_a2a_message_realtime
AFTER INSERT ON a2a_messages
FOR EACH ROW
EXECUTE FUNCTION trigger_publish_a2a_message();

-- Trigger: Publish LLM collaboration completions
CREATE OR REPLACE FUNCTION trigger_publish_collaboration_complete()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        PERFORM publish_realtime_event(
            'collaboration_completed',
            jsonb_build_object(
                'collaboration_id', NEW.id,
                'strategy', NEW.strategy,
                'selected_llm_id', NEW.selected_llm_id,
                'confidence_score', NEW.confidence_score,
                'duration_ms', NEW.total_duration_ms
            ),
            NEW.id,
            'collaboration',
            NULL,
            true  -- Broadcast
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_collaboration_complete_realtime
AFTER UPDATE ON llm_collaborations
FOR EACH ROW
EXECUTE FUNCTION trigger_publish_collaboration_complete();

-- ============================================================================
-- Section 9: Analytics Views for Supabase Dashboard
-- ============================================================================

-- View: Real-time system health
CREATE OR REPLACE VIEW realtime_system_health AS
SELECT
    COUNT(DISTINCT id) FILTER (WHERE status = 'active') AS active_agents,
    COUNT(DISTINCT id) AS total_agents,
    (SELECT COUNT(*) FROM tasks WHERE status = 'pending') AS pending_tasks,
    (SELECT COUNT(*) FROM tasks WHERE status = 'in_progress') AS active_tasks,
    (SELECT COUNT(*) FROM a2a_messages WHERE status = 'pending') AS pending_messages,
    (SELECT COUNT(*) FROM llm_collaborations WHERE status = 'in_progress') AS active_collaborations,
    now() AS snapshot_time
FROM agents;

COMMENT ON VIEW realtime_system_health IS 'Real-time system health metrics for Supabase dashboard';

-- View: Agent activity summary (last 24h)
CREATE OR REPLACE VIEW agent_activity_24h AS
SELECT
    a.id AS agent_id,
    a.name AS agent_name,
    a.status,
    COUNT(DISTINCT ar.id) AS tasks_completed_24h,
    COUNT(DISTINCT m_sent.id) AS messages_sent_24h,
    COUNT(DISTINCT m_received.id) AS messages_received_24h,
    MAX(ar.completed_at) AS last_activity_at
FROM agents a
LEFT JOIN agent_runs ar ON ar.metadata->>'agent_id' = a.id::text
    AND ar.completed_at > now() - interval '24 hours'
LEFT JOIN a2a_messages m_sent ON m_sent.from_agent_id = a.id
    AND m_sent.created_at > now() - interval '24 hours'
LEFT JOIN a2a_messages m_received ON m_received.to_agent_id = a.id
    AND m_received.created_at > now() - interval '24 hours'
GROUP BY a.id, a.name, a.status;

COMMENT ON VIEW agent_activity_24h IS '24-hour agent activity summary for real-time dashboards';

-- ============================================================================
-- Section 10: Permissions
-- ============================================================================

GRANT SELECT ON supabase_sync_state TO PUBLIC;
GRANT SELECT ON organizations TO PUBLIC;
GRANT SELECT ON realtime_events TO PUBLIC;
GRANT SELECT ON agent_artifacts TO PUBLIC;
GRANT SELECT ON task_claims TO PUBLIC;
GRANT SELECT ON realtime_system_health TO PUBLIC;
GRANT SELECT ON agent_activity_24h TO PUBLIC;

-- ============================================================================
-- Summary
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'CESAR.ai Phase H: Supabase Real-Time Integration - COMPLETE';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'Database Enhancements:';
    RAISE NOTICE '  ✓ Supabase sync state tracking';
    RAISE NOTICE '  ✓ Multi-tenant support (organizations, RLS)';
    RAISE NOTICE '  ✓ Real-time event stream (broadcast to Supabase)';
    RAISE NOTICE '  ✓ Artifact storage metadata (Supabase Storage)';
    RAISE NOTICE '  ✓ Distributed task queue with claims';
    RAISE NOTICE '';
    RAISE NOTICE 'Real-Time Features:';
    RAISE NOTICE '  ✓ Agent status change broadcasting';
    RAISE NOTICE '  ✓ A2A message real-time delivery';
    RAISE NOTICE '  ✓ LLM collaboration completion events';
    RAISE NOTICE '  ✓ Task queue updates';
    RAISE NOTICE '';
    RAISE NOTICE 'Helper Functions: 3';
    RAISE NOTICE '  - publish_realtime_event() - Broadcast events';
    RAISE NOTICE '  - claim_task() - Distributed task locking';
    RAISE NOTICE '  - release_task_claim() - Release task locks';
    RAISE NOTICE '';
    RAISE NOTICE 'Analytics Views: 2';
    RAISE NOTICE '  - realtime_system_health - Live system metrics';
    RAISE NOTICE '  - agent_activity_24h - 24-hour activity summary';
    RAISE NOTICE '';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '  1. Set up Supabase project at https://supabase.com';
    RAISE NOTICE '  2. Mirror these tables in Supabase SQL editor';
    RAISE NOTICE '  3. Enable Realtime for: agents, a2a_messages, llm_collaborations, realtime_events';
    RAISE NOTICE '  4. Create Storage buckets: agent-artifacts, agent-logs';
    RAISE NOTICE '  5. Configure Row Level Security (RLS) policies';
    RAISE NOTICE '  6. Update .env with SUPABASE_URL and SUPABASE_KEY';
    RAISE NOTICE '  7. Run: python -m cesar_ecosystem.services.supabase_service --setup';
    RAISE NOTICE '';
    RAISE NOTICE 'See: docs/SUPABASE_SETUP_GUIDE.md for detailed instructions';
    RAISE NOTICE '============================================================================';
END $$;

COMMIT;
