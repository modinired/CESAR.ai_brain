-- ============================================================================
-- DataBrain Schema - Missing Tables for graph_nodes, graph_links, agents
-- ============================================================================
-- This creates the tables that populate_databrain_complete.py and other
-- services expect but were never defined in the original migrations
-- ============================================================================

BEGIN;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- AGENTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS agents (
    id                      uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name              varchar(255) UNIQUE NOT NULL,
    mcp_system              varchar(100) NOT NULL,
    description             text,
    status                  varchar(50) DEFAULT 'active',
    mass                    decimal(10,2) DEFAULT 50.0,
    created_at              timestamptz DEFAULT NOW(),
    last_active             timestamptz DEFAULT NOW(),
    metadata                jsonb DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_agents_name ON agents(agent_name);
CREATE INDEX IF NOT EXISTS idx_agents_mcp ON agents(mcp_system);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);

-- ============================================================================
-- GRAPH_NODES TABLE (DataBrain Knowledge Graph)
-- ============================================================================
CREATE TABLE IF NOT EXISTS graph_nodes (
    id                      uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_id                 varchar(255) UNIQUE NOT NULL,
    label                   text NOT NULL,
    type                    varchar(100) NOT NULL,
    z_index                 integer DEFAULT 0,
    mass                    decimal(10,2) DEFAULT 10.0,
    x_coord                 decimal(10,4) DEFAULT 0.0,
    y_coord                 decimal(10,4) DEFAULT 0.0,
    semantic_vector         text,
    description             text,
    metadata                jsonb DEFAULT '{}'::jsonb,

    -- Activity tracking
    access_count            integer DEFAULT 0,
    last_accessed           timestamptz DEFAULT NOW(),
    last_mutated            timestamptz DEFAULT NOW(),

    -- Timestamps
    created_at              timestamptz DEFAULT NOW(),
    updated_at              timestamptz DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_graph_nodes_node_id ON graph_nodes(node_id);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_type ON graph_nodes(type);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_z_index ON graph_nodes(z_index);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_mass ON graph_nodes(mass DESC);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_last_accessed ON graph_nodes(last_accessed);

-- ============================================================================
-- GRAPH_LINKS TABLE (DataBrain Connections)
-- ============================================================================
CREATE TABLE IF NOT EXISTS graph_links (
    id                      uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id               varchar(255) NOT NULL,
    target_id               varchar(255) NOT NULL,
    relationship            varchar(100),
    strength                decimal(5,4) DEFAULT 0.5,

    -- Activity tracking
    traversal_count         integer DEFAULT 0,
    last_traversed          timestamptz DEFAULT NOW(),

    -- Timestamps
    created_at              timestamptz DEFAULT NOW(),
    updated_at              timestamptz DEFAULT NOW(),

    CONSTRAINT unique_link UNIQUE(source_id, target_id)
);

CREATE INDEX IF NOT EXISTS idx_graph_links_source ON graph_links(source_id);
CREATE INDEX IF NOT EXISTS idx_graph_links_target ON graph_links(target_id);
CREATE INDEX IF NOT EXISTS idx_graph_links_strength ON graph_links(strength DESC);

-- ============================================================================
-- ACTIVITY_LOGS TABLE (for tracking agent actions)
-- ============================================================================
CREATE TABLE IF NOT EXISTS activity_logs (
    id                      uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    mcp_system              varchar(100),
    agent_name              varchar(255),
    action                  varchar(100) NOT NULL,
    status                  varchar(50) NOT NULL,
    details                 text,
    metadata                jsonb DEFAULT '{}'::jsonb,
    created_at              timestamptz DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_activity_logs_agent ON activity_logs(agent_name, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_logs_action ON activity_logs(action);
CREATE INDEX IF NOT EXISTS idx_activity_logs_status ON activity_logs(status);
CREATE INDEX IF NOT EXISTS idx_activity_logs_created ON activity_logs(created_at DESC);

-- ============================================================================
-- WORKFLOWS TABLE (for automation tracking)
-- ============================================================================
CREATE TABLE IF NOT EXISTS workflows (
    id                      uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_name           varchar(255) NOT NULL,
    description             text,
    status                  varchar(50) DEFAULT 'pending',
    priority                integer DEFAULT 5,
    assigned_agent          varchar(255),
    progress_percent        integer DEFAULT 0,
    started_at              timestamptz,
    completed_at            timestamptz,
    created_at              timestamptz DEFAULT NOW(),
    metadata                jsonb DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status);
CREATE INDEX IF NOT EXISTS idx_workflows_agent ON workflows(assigned_agent);
CREATE INDEX IF NOT EXISTS idx_workflows_created ON workflows(created_at DESC);

-- ============================================================================
-- TASKS TABLE (for workflow tasks)
-- ============================================================================
CREATE TABLE IF NOT EXISTS tasks (
    id                      uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id             uuid REFERENCES workflows(id) ON DELETE CASCADE,
    task_name               varchar(255) NOT NULL,
    description             text,
    status                  varchar(50) DEFAULT 'pending',
    assigned_agent          varchar(255),
    started_at              timestamptz,
    completed_at            timestamptz,
    created_at              timestamptz DEFAULT NOW(),
    metadata                jsonb DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_tasks_workflow ON tasks(workflow_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_agent ON tasks(assigned_agent);

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON TABLE agents IS 'MCP agents registry with reputation tracking';
COMMENT ON TABLE graph_nodes IS 'DataBrain knowledge graph nodes';
COMMENT ON TABLE graph_links IS 'DataBrain knowledge graph connections';
COMMENT ON TABLE activity_logs IS 'Agent activity and mutation logs';
COMMENT ON TABLE workflows IS 'Automated workflow tracking';
COMMENT ON TABLE tasks IS 'Individual tasks within workflows';

COMMIT;

-- ============================================================================
-- Verification
-- ============================================================================
SELECT 'DataBrain schema created successfully!' as status;
