-- ============================================================================
-- CESAR.ai Phase H: Synthetic Organism Visualization System
-- ============================================================================
-- Version: 1.0
-- Date: November 20, 2025
-- Description: Spatial graph visualization with force-directed physics
-- Purpose: Enable 3D knowledge graph, workflow matrix, and agent network viz
-- Supabase Compatible: YES (uses PostGIS for spatial operations)
-- ============================================================================

BEGIN;

-- ============================================================================
-- Section 1: Enable Required Extensions
-- ============================================================================

-- Enable vector operations (already enabled, but ensure)
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable PostGIS for advanced spatial operations
CREATE EXTENSION IF NOT EXISTS postgis;

-- Enable pg_trgm for trigram similarity (fallback from embeddings)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================================================
-- Section 2: Spatial Coordinates for Knowledge Graph Nodes
-- ============================================================================

-- Add spatial coordinates to semantic memory (persistent node positions)
ALTER TABLE memory_semantic
ADD COLUMN IF NOT EXISTS node_x NUMERIC(10,2) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS node_y NUMERIC(10,2) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS node_z NUMERIC(10,2) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS node_vx NUMERIC(8,4) DEFAULT 0.0,  -- Velocity X
ADD COLUMN IF NOT EXISTS node_vy NUMERIC(8,4) DEFAULT 0.0,  -- Velocity Y
ADD COLUMN IF NOT EXISTS node_vz NUMERIC(8,4) DEFAULT 0.0,  -- Velocity Z
ADD COLUMN IF NOT EXISTS node_mass NUMERIC(8,2) DEFAULT 10.0,
ADD COLUMN IF NOT EXISTS node_type TEXT DEFAULT 'knowledge'
    CHECK (node_type IN ('raw_data', 'information', 'knowledge', 'wisdom')),
ADD COLUMN IF NOT EXISTS visual_metadata JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS force_field_ids TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS last_physics_update TIMESTAMPTZ DEFAULT now();

-- Index for spatial queries
CREATE INDEX IF NOT EXISTS idx_semantic_spatial ON memory_semantic(node_x, node_y, node_z)
WHERE node_x IS NOT NULL;

-- Index for physics updates
CREATE INDEX IF NOT EXISTS idx_semantic_physics_update ON memory_semantic(last_physics_update DESC);

COMMENT ON COLUMN memory_semantic.node_x IS 'X-coordinate in 3D visualization space (0-1200)';
COMMENT ON COLUMN memory_semantic.node_y IS 'Y-coordinate in 3D visualization space (0-800)';
COMMENT ON COLUMN memory_semantic.node_z IS 'Z-coordinate representing epistemic depth (0=data, 100=info, 200=knowledge, 300=wisdom)';
COMMENT ON COLUMN memory_semantic.visual_metadata IS 'Stores particle history, attraction weights, LOD levels';
COMMENT ON COLUMN memory_semantic.force_field_ids IS 'Array of semantic force fields this node belongs to';

-- ============================================================================
-- Section 3: Knowledge Graph Force Fields (Semantic Gravity Wells)
-- ============================================================================

CREATE TABLE IF NOT EXISTS knowledge_force_fields (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Field identity
    field_name TEXT NOT NULL UNIQUE,
    field_category TEXT NOT NULL,  -- e.g., 'risk', 'compliance', 'innovation'

    -- Spatial positioning
    center_x NUMERIC(10,2) NOT NULL,
    center_y NUMERIC(10,2) NOT NULL,
    radius NUMERIC(8,2) DEFAULT 150.0,

    -- Semantic definition
    semantic_keywords TEXT[] NOT NULL,  -- Keywords that attract nodes
    semantic_vector vector(1536),       -- Embedding of field concept
    attraction_strength NUMERIC(5,4) DEFAULT 0.5 CHECK (attraction_strength >= 0 AND attraction_strength <= 1),

    -- Visual properties
    color_hex TEXT DEFAULT '#3b82f6',
    opacity NUMERIC(3,2) DEFAULT 0.1,
    is_active BOOLEAN DEFAULT true,

    -- Metadata
    created_by TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_force_fields_active ON knowledge_force_fields(is_active) WHERE is_active = true;
CREATE INDEX idx_force_fields_spatial ON knowledge_force_fields(center_x, center_y, radius);
CREATE INDEX idx_force_fields_keywords ON knowledge_force_fields USING gin(semantic_keywords);

COMMENT ON TABLE knowledge_force_fields IS 'Semantic gravity wells that cluster related knowledge nodes';

-- ============================================================================
-- Section 4: Graph Links with Weighted Strength
-- ============================================================================

CREATE TABLE IF NOT EXISTS knowledge_graph_links (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Graph structure
    source_memory_id uuid NOT NULL REFERENCES memory_semantic(id) ON DELETE CASCADE,
    target_memory_id uuid NOT NULL REFERENCES memory_semantic(id) ON DELETE CASCADE,

    -- Link properties
    link_strength NUMERIC(5,4) DEFAULT 0.5 CHECK (link_strength >= 0 AND link_strength <= 1),
    link_type TEXT DEFAULT 'association' CHECK (link_type IN (
        'association',      -- General semantic relationship
        'temporal',         -- Co-occurred in same session
        'causal',          -- Cause-effect relationship
        'hierarchical',    -- Parent-child concept
        'contradiction'    -- Opposing concepts
    )),

    -- Evidence tracking
    co_occurrence_count INTEGER DEFAULT 1,
    episodic_source_ids uuid[],  -- Episodes that created this link

    -- Temporal metadata
    first_linked TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_reinforced TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Visual properties
    is_visible BOOLEAN DEFAULT true,
    rendering_priority INTEGER DEFAULT 0,

    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT unique_link UNIQUE(source_memory_id, target_memory_id)
);

CREATE INDEX idx_graph_links_source ON knowledge_graph_links(source_memory_id, link_strength DESC);
CREATE INDEX idx_graph_links_target ON knowledge_graph_links(target_memory_id, link_strength DESC);
CREATE INDEX idx_graph_links_visible ON knowledge_graph_links(is_visible) WHERE is_visible = true;
CREATE INDEX idx_graph_links_strength ON knowledge_graph_links(link_strength DESC);

COMMENT ON TABLE knowledge_graph_links IS 'Weighted edges in the knowledge graph with evidence tracking';

-- ============================================================================
-- Section 5: Workflow Process Nodes (AutomationMatrix)
-- ============================================================================

CREATE TABLE IF NOT EXISTS workflow_process_nodes (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Process identity
    workflow_template_id uuid REFERENCES workflow_templates(id) ON DELETE CASCADE,
    node_name TEXT NOT NULL,
    node_label TEXT NOT NULL,

    -- Node type and properties
    node_type TEXT NOT NULL CHECK (node_type IN (
        'human',        -- Human actor
        'ai_agent',     -- AI-powered automation
        'database',     -- Data storage/retrieval
        'api_trigger',  -- External API call
        'client_input'  -- User input point
    )),

    -- Process metrics (updated from workflow_executions)
    cost_per_operation NUMERIC(10,6) DEFAULT 0.0,
    processing_speed_ms INTEGER DEFAULT 1000,
    current_queue_depth INTEGER DEFAULT 0,

    -- Spatial positioning
    position_x NUMERIC(10,2),
    position_y NUMERIC(10,2),
    position_z NUMERIC(10,2) DEFAULT 0,

    -- Status tracking
    status TEXT DEFAULT 'optimal' CHECK (status IN ('optimal', 'stressed', 'bottleneck')),
    bottleneck_threshold INTEGER DEFAULT 10,  -- Queue depth that triggers alert

    -- Performance tracking
    total_operations_processed BIGINT DEFAULT 0,
    avg_queue_wait_time_ms INTEGER DEFAULT 0,

    metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_workflow_nodes_template ON workflow_process_nodes(workflow_template_id);
CREATE INDEX idx_workflow_nodes_status ON workflow_process_nodes(status) WHERE status != 'optimal';
CREATE INDEX idx_workflow_nodes_type ON workflow_process_nodes(node_type);

COMMENT ON TABLE workflow_process_nodes IS 'Process nodes for workflow automation visualization (Digital Twin)';

-- ============================================================================
-- Section 6: Workflow Process Links (Data Flow Pipes)
-- ============================================================================

CREATE TABLE IF NOT EXISTS workflow_process_links (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    source_node_id uuid NOT NULL REFERENCES workflow_process_nodes(id) ON DELETE CASCADE,
    target_node_id uuid NOT NULL REFERENCES workflow_process_nodes(id) ON DELETE CASCADE,

    -- Flow metrics
    throughput_ops_per_sec NUMERIC(10,4) DEFAULT 1.0,
    avg_latency_ms INTEGER DEFAULT 100,

    -- Visual properties
    pipe_width INTEGER DEFAULT 2,  -- Visual thickness
    is_active BOOLEAN DEFAULT true,

    metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT unique_workflow_link UNIQUE(source_node_id, target_node_id)
);

CREATE INDEX idx_workflow_links_source ON workflow_process_links(source_node_id);
CREATE INDEX idx_workflow_links_target ON workflow_process_links(target_node_id);

COMMENT ON TABLE workflow_process_links IS 'Data flow connections between workflow process nodes';

-- ============================================================================
-- Section 7: Agent Network Nodes (TalentMap)
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_network_nodes (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Agent reference
    agent_id TEXT NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,

    -- Network metrics (computed from a2a_messages)
    influence_score NUMERIC(5,2) DEFAULT 50.0 CHECK (influence_score >= 0 AND influence_score <= 100),
    burnout_index NUMERIC(5,2) DEFAULT 20.0 CHECK (burnout_index >= 0 AND burnout_index <= 100),
    risk_level TEXT DEFAULT 'Stable' CHECK (risk_level IN ('Stable', 'At-Risk', 'Critical')),

    -- Communication patterns
    incoming_message_count INTEGER DEFAULT 0,
    outgoing_message_count INTEGER DEFAULT 0,
    avg_response_time_seconds NUMERIC(10,2) DEFAULT 0,

    -- Spatial positioning (force-directed layout)
    position_x NUMERIC(10,2),
    position_y NUMERIC(10,2),
    velocity_x NUMERIC(8,4) DEFAULT 0.0,
    velocity_y NUMERIC(8,4) DEFAULT 0.0,
    node_mass NUMERIC(8,2) DEFAULT 10.0,

    -- Department clustering
    department_gravity_x NUMERIC(10,2),
    department_gravity_y NUMERIC(10,2),

    -- Metadata
    last_metrics_update TIMESTAMPTZ DEFAULT now(),
    metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT unique_agent_network_node UNIQUE(agent_id)
);

CREATE INDEX idx_agent_network_agent ON agent_network_nodes(agent_id);
CREATE INDEX idx_agent_network_risk ON agent_network_nodes(risk_level) WHERE risk_level != 'Stable';
CREATE INDEX idx_agent_network_metrics_update ON agent_network_nodes(last_metrics_update DESC);

COMMENT ON TABLE agent_network_nodes IS 'Agent nodes with network centrality and burnout metrics';

-- ============================================================================
-- Section 8: Agent Communication Links
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_communication_links (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    source_agent_id TEXT NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    target_agent_id TEXT NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,

    -- Communication metrics (from a2a_messages)
    message_frequency INTEGER DEFAULT 0,
    link_type TEXT DEFAULT 'collaboration' CHECK (link_type IN (
        'collaboration',
        'reporting',
        'social'
    )),

    -- Relationship strength
    relationship_strength NUMERIC(5,4) DEFAULT 0.5 CHECK (relationship_strength >= 0 AND relationship_strength <= 1),

    -- Temporal tracking
    first_interaction TIMESTAMPTZ DEFAULT now(),
    last_interaction TIMESTAMPTZ DEFAULT now(),
    total_interactions INTEGER DEFAULT 0,

    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT unique_agent_comm_link UNIQUE(source_agent_id, target_agent_id)
);

CREATE INDEX idx_agent_comm_source ON agent_communication_links(source_agent_id, relationship_strength DESC);
CREATE INDEX idx_agent_comm_target ON agent_communication_links(target_agent_id, relationship_strength DESC);
CREATE INDEX idx_agent_comm_frequency ON agent_communication_links(message_frequency DESC);

COMMENT ON TABLE agent_communication_links IS 'Communication edges between agents with frequency and strength';

-- ============================================================================
-- Section 9: Neuroplasticity Actions Log (Graph Mutations)
-- ============================================================================

CREATE TYPE neuroplasticity_action_type AS ENUM (
    'CREATE_NODE',
    'UPDATE_NODE',
    'DELETE_NODE',
    'CREATE_LINK',
    'UPDATE_LINK',
    'DELETE_LINK',
    'CREATE_FORCE_FIELD',
    'DECAY_NODE'
);

CREATE TABLE IF NOT EXISTS neuroplasticity_actions (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Action details
    action_type neuroplasticity_action_type NOT NULL,
    target_id uuid,  -- ID of affected node/link

    -- Agent tracking
    initiated_by_agent_id TEXT REFERENCES agents(agent_id) ON DELETE SET NULL,
    session_id uuid REFERENCES sessions(id) ON DELETE SET NULL,

    -- Action parameters
    action_params JSONB NOT NULL,
    reason TEXT,

    -- Validation
    validation_status TEXT DEFAULT 'pending' CHECK (validation_status IN (
        'pending',
        'approved',
        'rejected',
        'executed'
    )),
    validation_errors TEXT[],

    -- Execution tracking
    executed_at TIMESTAMPTZ,
    rollback_params JSONB,  -- For undo operations

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_neuroplasticity_agent ON neuroplasticity_actions(initiated_by_agent_id, created_at DESC);
CREATE INDEX idx_neuroplasticity_status ON neuroplasticity_actions(validation_status) WHERE validation_status = 'pending';
CREATE INDEX idx_neuroplasticity_type ON neuroplasticity_actions(action_type, created_at DESC);

COMMENT ON TABLE neuroplasticity_actions IS 'Audit log of all graph modification actions (stigmergic memory mutations)';

-- ============================================================================
-- Section 10: Materialized Views for High-Performance Queries
-- ============================================================================

-- View: Complete knowledge graph state
CREATE MATERIALIZED VIEW IF NOT EXISTS knowledge_graph_snapshot AS
SELECT
    ms.id,
    ms.concept as label,
    ms.node_type as type,
    COALESCE(ms.node_x, RANDOM() * 1200) as x,
    COALESCE(ms.node_y, RANDOM() * 800) as y,
    COALESCE(ms.node_z,
        CASE ms.node_type
            WHEN 'raw_data' THEN 0
            WHEN 'information' THEN 100
            WHEN 'knowledge' THEN 200
            WHEN 'wisdom' THEN 300
            ELSE 100
        END
    ) as z,
    ms.node_vx as vx,
    ms.node_vy as vy,
    ms.node_vz as vz,
    ms.node_mass as mass,
    ms.confidence_score,
    ms.access_count,
    ms.force_field_ids,
    ms.created_at,
    ms.last_reinforced,
    ms.visual_metadata
FROM memory_semantic ms
WHERE ms.confidence_score > 0.3;

CREATE UNIQUE INDEX idx_knowledge_graph_snapshot_id ON knowledge_graph_snapshot(id);
CREATE INDEX idx_knowledge_graph_snapshot_type ON knowledge_graph_snapshot(type);

COMMENT ON MATERIALIZED VIEW knowledge_graph_snapshot IS 'Pre-computed knowledge graph state for fast visualization loading';

-- View: Workflow performance metrics aggregated
CREATE MATERIALIZED VIEW IF NOT EXISTS workflow_process_performance AS
SELECT
    wpn.id as node_id,
    wpn.workflow_template_id,
    wpn.node_name,
    wpn.node_type,
    wpn.cost_per_operation,
    wpn.processing_speed_ms,
    wpn.current_queue_depth,
    wpn.status,
    COUNT(we.id) FILTER (WHERE we.status = 'completed') as completed_executions,
    AVG(EXTRACT(EPOCH FROM (we.completed_at - we.started_at)) * 1000)::INTEGER as avg_execution_time_ms,
    SUM(we.total_cost_usd) as total_cost
FROM workflow_process_nodes wpn
LEFT JOIN workflow_executions we ON we.workflow_name = (
    SELECT workflow_name FROM workflow_templates WHERE id = wpn.workflow_template_id
)
WHERE we.started_at > NOW() - INTERVAL '30 days' OR we.id IS NULL
GROUP BY wpn.id, wpn.workflow_template_id, wpn.node_name, wpn.node_type,
         wpn.cost_per_operation, wpn.processing_speed_ms, wpn.current_queue_depth, wpn.status;

CREATE UNIQUE INDEX idx_workflow_performance_node ON workflow_process_performance(node_id);

COMMENT ON MATERIALIZED VIEW workflow_process_performance IS 'Aggregated workflow node performance for AutomationMatrix';

-- View: Agent network health metrics
CREATE MATERIALIZED VIEW IF NOT EXISTS agent_network_health AS
SELECT
    ann.id as node_id,
    ann.agent_id,
    a.name as agent_name,
    a.mcp_system as department,
    ann.influence_score,
    ann.burnout_index,
    ann.risk_level,
    ann.incoming_message_count,
    ann.outgoing_message_count,
    CASE
        WHEN ann.outgoing_message_count > 0
        THEN ROUND(ann.incoming_message_count::numeric / ann.outgoing_message_count, 2)
        ELSE ann.incoming_message_count::numeric
    END as communication_imbalance,
    COUNT(DISTINCT acl.id) as total_connections,
    ann.position_x,
    ann.position_y,
    ann.last_metrics_update
FROM agent_network_nodes ann
JOIN agents a ON a.agent_id = ann.agent_id
LEFT JOIN agent_communication_links acl ON acl.source_agent_id = ann.agent_id OR acl.target_agent_id = ann.agent_id
WHERE a.status = 'active'
GROUP BY ann.id, ann.agent_id, a.name, a.mcp_system, ann.influence_score, ann.burnout_index,
         ann.risk_level, ann.incoming_message_count, ann.outgoing_message_count,
         ann.position_x, ann.position_y, ann.last_metrics_update;

CREATE UNIQUE INDEX idx_agent_network_health_node ON agent_network_health(node_id);
CREATE INDEX idx_agent_network_health_risk ON agent_network_health(risk_level) WHERE risk_level != 'Stable';

COMMENT ON MATERIALIZED VIEW agent_network_health IS 'Real-time agent network health for TalentMap visualization';

-- ============================================================================
-- Section 11: Helper Functions
-- ============================================================================

-- Function: Initialize node positions using force-directed algorithm seed
CREATE OR REPLACE FUNCTION initialize_node_positions()
RETURNS void AS $$
DECLARE
    v_node RECORD;
    v_random_x NUMERIC;
    v_random_y NUMERIC;
    v_base_z NUMERIC;
BEGIN
    FOR v_node IN
        SELECT id, node_type FROM memory_semantic WHERE node_x IS NULL
    LOOP
        -- Random initial position
        v_random_x := (RANDOM() * 1000) + 100;  -- 100-1100 range
        v_random_y := (RANDOM() * 600) + 100;   -- 100-700 range

        -- Z-axis based on epistemic depth
        v_base_z := CASE v_node.node_type
            WHEN 'raw_data' THEN 0
            WHEN 'information' THEN 100
            WHEN 'knowledge' THEN 200
            WHEN 'wisdom' THEN 300
            ELSE 100
        END;

        UPDATE memory_semantic
        SET
            node_x = v_random_x,
            node_y = v_random_y,
            node_z = v_base_z,
            last_physics_update = now()
        WHERE id = v_node.id;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION initialize_node_positions IS 'Initialize random spatial positions for new knowledge nodes';

-- Function: Calculate force field membership
CREATE OR REPLACE FUNCTION update_force_field_membership(p_memory_id uuid)
RETURNS void AS $$
DECLARE
    v_concept TEXT;
    v_field RECORD;
    v_fields TEXT[] := ARRAY[]::TEXT[];
BEGIN
    -- Get the concept text
    SELECT concept INTO v_concept FROM memory_semantic WHERE id = p_memory_id;

    IF v_concept IS NULL THEN
        RETURN;
    END IF;

    -- Check against all active force fields
    FOR v_field IN
        SELECT field_name, semantic_keywords FROM knowledge_force_fields WHERE is_active = true
    LOOP
        -- Check if any keywords match (case-insensitive)
        IF EXISTS (
            SELECT 1 FROM unnest(v_field.semantic_keywords) kw
            WHERE LOWER(v_concept) LIKE '%' || LOWER(kw) || '%'
        ) THEN
            v_fields := array_append(v_fields, v_field.field_name);
        END IF;
    END LOOP;

    -- Update the node
    UPDATE memory_semantic
    SET force_field_ids = v_fields
    WHERE id = p_memory_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_force_field_membership IS 'Assign knowledge nodes to semantic force fields based on keyword matching';

-- Function: Compute graph links from episodic co-occurrence
CREATE OR REPLACE FUNCTION compute_knowledge_graph_links()
RETURNS INTEGER AS $$
DECLARE
    v_links_created INTEGER := 0;
BEGIN
    -- Create links from episodic co-occurrence
    INSERT INTO knowledge_graph_links (
        source_memory_id,
        target_memory_id,
        link_strength,
        link_type,
        co_occurrence_count,
        episodic_source_ids
    )
    SELECT
        e1.semantic_memory_id as source_id,
        e2.semantic_memory_id as target_id,
        LEAST(1.0, COUNT(*)::NUMERIC / 10.0) as strength,
        'temporal' as link_type,
        COUNT(*)::INTEGER as co_occurrence,
        ARRAY_AGG(DISTINCT e1.id) as episodes
    FROM memory_episodic e1
    JOIN memory_episodic e2 ON e1.session_id = e2.session_id
    WHERE e1.semantic_memory_id IS NOT NULL
      AND e2.semantic_memory_id IS NOT NULL
      AND e1.semantic_memory_id < e2.semantic_memory_id  -- Avoid duplicates
      AND e1.consolidated = true
      AND e2.consolidated = true
    GROUP BY e1.semantic_memory_id, e2.semantic_memory_id
    HAVING COUNT(*) >= 2  -- Minimum 2 co-occurrences
    ON CONFLICT (source_memory_id, target_memory_id)
    DO UPDATE SET
        co_occurrence_count = EXCLUDED.co_occurrence_count,
        link_strength = EXCLUDED.link_strength,
        last_reinforced = now();

    GET DIAGNOSTICS v_links_created = ROW_COUNT;

    RETURN v_links_created;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION compute_knowledge_graph_links IS 'Generate graph links from episodic memory co-occurrence patterns';

-- Function: Update agent network metrics from A2A messages
CREATE OR REPLACE FUNCTION update_agent_network_metrics()
RETURNS INTEGER AS $$
DECLARE
    v_updated INTEGER := 0;
BEGIN
    -- Update or insert agent network nodes
    INSERT INTO agent_network_nodes (
        agent_id,
        incoming_message_count,
        outgoing_message_count,
        avg_response_time_seconds,
        influence_score,
        burnout_index,
        risk_level
    )
    SELECT
        a.agent_id,
        COALESCE(recv.count, 0) as incoming,
        COALESCE(sent.count, 0) as outgoing,
        COALESCE(recv.avg_response, 0) as avg_response,
        LEAST(100, (COALESCE(recv.count, 0) + COALESCE(sent.count, 0)) * 5) as influence,
        CASE
            WHEN COALESCE(recv.count, 0) + COALESCE(sent.count, 0) > 12 THEN 95
            WHEN COALESCE(recv.count, 0) + COALESCE(sent.count, 0) > 8 THEN 70
            ELSE 20
        END as burnout,
        CASE
            WHEN COALESCE(recv.count, 0) + COALESCE(sent.count, 0) > 12 THEN 'Critical'
            WHEN COALESCE(recv.count, 0) + COALESCE(sent.count, 0) > 8 THEN 'At-Risk'
            ELSE 'Stable'
        END as risk
    FROM agents a
    LEFT JOIN (
        SELECT
            to_agent_id,
            COUNT(*) as count,
            AVG(EXTRACT(EPOCH FROM (acknowledged_at - created_at))) as avg_response
        FROM a2a_messages
        WHERE created_at > NOW() - INTERVAL '7 days'
        GROUP BY to_agent_id
    ) recv ON recv.to_agent_id = a.id
    LEFT JOIN (
        SELECT
            from_agent_id,
            COUNT(*) as count
        FROM a2a_messages
        WHERE created_at > NOW() - INTERVAL '7 days'
        GROUP BY from_agent_id
    ) sent ON sent.from_agent_id = a.id
    WHERE a.status = 'active'
    ON CONFLICT (agent_id)
    DO UPDATE SET
        incoming_message_count = EXCLUDED.incoming_message_count,
        outgoing_message_count = EXCLUDED.outgoing_message_count,
        avg_response_time_seconds = EXCLUDED.avg_response_time_seconds,
        influence_score = EXCLUDED.influence_score,
        burnout_index = EXCLUDED.burnout_index,
        risk_level = EXCLUDED.risk_level,
        last_metrics_update = now();

    GET DIAGNOSTICS v_updated = ROW_COUNT;

    RETURN v_updated;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_agent_network_metrics IS 'Recompute agent network centrality and burnout metrics from A2A messages';

-- ============================================================================
-- Section 12: Triggers for Automatic Updates
-- ============================================================================

-- Trigger: Auto-assign force fields when semantic memory is created/updated
CREATE OR REPLACE FUNCTION trigger_update_force_fields()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM update_force_field_membership(NEW.id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER semantic_memory_force_field_assignment
AFTER INSERT OR UPDATE OF concept ON memory_semantic
FOR EACH ROW
EXECUTE FUNCTION trigger_update_force_fields();

-- Trigger: Auto-refresh materialized views on major changes
CREATE OR REPLACE FUNCTION trigger_refresh_visualization_views()
RETURNS TRIGGER AS $$
BEGIN
    -- Refresh in background (non-blocking)
    PERFORM pg_notify('refresh_viz_views', 'triggered');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER refresh_viz_on_semantic_change
AFTER INSERT OR UPDATE OR DELETE ON memory_semantic
FOR EACH STATEMENT
EXECUTE FUNCTION trigger_refresh_visualization_views();

-- ============================================================================
-- Section 13: Row Level Security (RLS) for Supabase
-- ============================================================================

-- Enable RLS on all visualization tables
ALTER TABLE knowledge_force_fields ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_graph_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_process_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_process_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_network_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_communication_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE neuroplasticity_actions ENABLE ROW LEVEL SECURITY;

-- Policy: Allow authenticated users to read all visualization data
CREATE POLICY "Allow authenticated read access to force fields"
ON knowledge_force_fields FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Allow authenticated read access to graph links"
ON knowledge_graph_links FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Allow authenticated read access to workflow nodes"
ON workflow_process_nodes FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Allow authenticated read access to workflow links"
ON workflow_process_links FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Allow authenticated read access to agent network nodes"
ON agent_network_nodes FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Allow authenticated read access to agent comm links"
ON agent_communication_links FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Allow authenticated read access to neuroplasticity log"
ON neuroplasticity_actions FOR SELECT
TO authenticated
USING (true);

-- Policy: Only service role can write (mutations handled via API)
CREATE POLICY "Service role can manage force fields"
ON knowledge_force_fields FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Service role can manage graph links"
ON knowledge_graph_links FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- ============================================================================
-- Section 14: Seed Data - Default Force Fields
-- ============================================================================

INSERT INTO knowledge_force_fields (
    field_name,
    field_category,
    center_x,
    center_y,
    radius,
    semantic_keywords,
    color_hex,
    opacity,
    created_by
) VALUES
(
    'Risk & Fraud Detection',
    'risk',
    240,
    640,
    150,
    ARRAY['risk', 'fraud', 'attack', 'alert', 'danger', 'warning', 'threat', 'security', 'breach'],
    '#ef4444',
    0.1,
    'system'
),
(
    'Compliance & Legal',
    'compliance',
    960,
    640,
    150,
    ARRAY['audit', 'legal', 'compliance', 'regulation', 'policy', 'law', 'gdpr', 'contract'],
    '#3b82f6',
    0.1,
    'system'
),
(
    'Innovation & Research',
    'innovation',
    600,
    200,
    150,
    ARRAY['innovation', 'research', 'experiment', 'patent', 'discovery', 'invention', 'prototype'],
    '#10b981',
    0.1,
    'system'
),
(
    'Financial Operations',
    'finance',
    240,
    200,
    150,
    ARRAY['revenue', 'cost', 'profit', 'budget', 'invoice', 'payment', 'financial', 'accounting'],
    '#eab308',
    0.1,
    'system'
),
(
    'Customer Success',
    'customer',
    960,
    200,
    150,
    ARRAY['customer', 'client', 'support', 'satisfaction', 'feedback', 'retention', 'churn'],
    '#a855f7',
    0.1,
    'system'
)
ON CONFLICT (field_name) DO NOTHING;

-- ============================================================================
-- Section 15: Initial Data Population
-- ============================================================================

-- Initialize positions for existing semantic memories
SELECT initialize_node_positions();

-- Generate initial graph links
SELECT compute_knowledge_graph_links();

-- Update agent network metrics
SELECT update_agent_network_metrics();

-- Refresh materialized views
REFRESH MATERIALIZED VIEW knowledge_graph_snapshot;
REFRESH MATERIALIZED VIEW workflow_process_performance;
REFRESH MATERIALIZED VIEW agent_network_health;

-- ============================================================================
-- Section 16: Scheduled Jobs (via pg_cron or external scheduler)
-- ============================================================================

-- Note: These should be configured in Supabase dashboard or via cron service

-- Recommended schedule:
-- EVERY 5 minutes: REFRESH MATERIALIZED VIEW knowledge_graph_snapshot;
-- EVERY 10 minutes: SELECT compute_knowledge_graph_links();
-- EVERY 15 minutes: SELECT update_agent_network_metrics();
-- EVERY 1 hour: REFRESH MATERIALIZED VIEW CONCURRENTLY workflow_process_performance;

-- ============================================================================
-- Summary & Validation
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'CESAR.ai Phase H: Synthetic Organism Visualization - COMPLETE';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'Tables Created: 8';
    RAISE NOTICE '  ✓ knowledge_force_fields (semantic gravity wells)';
    RAISE NOTICE '  ✓ knowledge_graph_links (weighted edges)';
    RAISE NOTICE '  ✓ workflow_process_nodes (digital twin nodes)';
    RAISE NOTICE '  ✓ workflow_process_links (process flow pipes)';
    RAISE NOTICE '  ✓ agent_network_nodes (agent graph nodes)';
    RAISE NOTICE '  ✓ agent_communication_links (agent edges)';
    RAISE NOTICE '  ✓ neuroplasticity_actions (graph mutation log)';
    RAISE NOTICE '';
    RAISE NOTICE 'Materialized Views: 3';
    RAISE NOTICE '  ✓ knowledge_graph_snapshot (DataBrainV6 data)';
    RAISE NOTICE '  ✓ workflow_process_performance (AutomationMatrix data)';
    RAISE NOTICE '  ✓ agent_network_health (TalentMap data)';
    RAISE NOTICE '';
    RAISE NOTICE 'Helper Functions: 4';
    RAISE NOTICE '  ✓ initialize_node_positions()';
    RAISE NOTICE '  ✓ update_force_field_membership()';
    RAISE NOTICE '  ✓ compute_knowledge_graph_links()';
    RAISE NOTICE '  ✓ update_agent_network_metrics()';
    RAISE NOTICE '';
    RAISE NOTICE 'Row Level Security: ENABLED';
    RAISE NOTICE '  ✓ Authenticated users: READ access';
    RAISE NOTICE '  ✓ Service role: FULL access';
    RAISE NOTICE '';
    RAISE NOTICE 'Force Fields Seeded: 5';
    RAISE NOTICE '  ✓ Risk & Fraud Detection';
    RAISE NOTICE '  ✓ Compliance & Legal';
    RAISE NOTICE '  ✓ Innovation & Research';
    RAISE NOTICE '  ✓ Financial Operations';
    RAISE NOTICE '  ✓ Customer Success';
    RAISE NOTICE '';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '  1. Deploy API endpoints for visualization data adapters';
    RAISE NOTICE '  2. Implement React components with WebSocket streaming';
    RAISE NOTICE '  3. Configure scheduled jobs for materialized view refresh';
    RAISE NOTICE '============================================================================';
END $$;

COMMIT;
