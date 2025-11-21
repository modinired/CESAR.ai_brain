-- ==================================================================================
-- CESAR.AI COMPLETE DATA BRAIN SCHEMA (CockroachDB Edition)
-- ==================================================================================
-- VERSION: 3.0.0-COMPLETE
-- PURPOSE: Full implementation of the Living Data Brain architecture
-- COMPONENTS: Knowledge Graph, Neuroplasticity, Multi-Agent System, Financial Physics
-- ==================================================================================

-- ==================================================================================
-- SECTION 1: KNOWLEDGE GRAPH CORE (3D Semantic Vector Space)
-- ==================================================================================

-- Nodes: The atomic units of knowledge in the brain
CREATE TABLE IF NOT EXISTS graph_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_id VARCHAR(255) UNIQUE NOT NULL, -- External identifier (e.g., "n884")
    label TEXT NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'concept', 'entity', 'process', 'resource', 'wisdom', 'knowledge', 'information', 'raw_data'

    -- Spatial Context (3D Vector Space)
    x_coord DECIMAL(10,2) DEFAULT 0,
    y_coord DECIMAL(10,2) DEFAULT 0,
    z_index INTEGER DEFAULT 0, -- 0-100: Raw, 100-200: Info, 200-300: Knowledge, 300+: Wisdom

    -- Graph Theory Metrics
    mass DECIMAL(10,2) DEFAULT 10, -- Gravity/Importance (0-100)
    node_category VARCHAR(50) DEFAULT 'static', -- 'static' or 'ephemeral'

    -- Semantic Vector (Embedding representation)
    semantic_vector JSONB DEFAULT '[]', -- Array of trigrams for similarity

    -- Temporal Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed TIMESTAMPTZ DEFAULT NOW(),
    access_count INTEGER DEFAULT 1,

    -- Decay & Neuroplasticity
    cluster_id INTEGER DEFAULT 0,
    alert_level VARCHAR(20) DEFAULT 'stable', -- 'stable', 'warning', 'critical'

    -- Content
    description TEXT,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_graph_nodes_type ON graph_nodes(type);
CREATE INDEX idx_graph_nodes_z_index ON graph_nodes(z_index);
CREATE INDEX idx_graph_nodes_mass ON graph_nodes(mass DESC);
CREATE INDEX idx_graph_nodes_last_accessed ON graph_nodes(last_accessed DESC);
CREATE INDEX idx_graph_nodes_node_id ON graph_nodes(node_id);

-- Links: The synaptic connections between nodes
CREATE TABLE IF NOT EXISTS graph_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    link_id VARCHAR(255) UNIQUE NOT NULL,
    source_node_id VARCHAR(255) NOT NULL,
    target_node_id VARCHAR(255) NOT NULL,

    -- Link Properties
    strength DECIMAL(3,2) DEFAULT 0.5, -- 0.0 to 1.0
    link_type VARCHAR(50) DEFAULT 'semantic', -- 'semantic', 'causal', 'temporal', 'hierarchical'

    -- Temporal
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_traversed TIMESTAMPTZ,
    traversal_count INTEGER DEFAULT 0,

    -- Metadata
    weight DECIMAL(10,6) DEFAULT 1.0,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_graph_links_source ON graph_links(source_node_id);
CREATE INDEX idx_graph_links_target ON graph_links(target_node_id);
CREATE INDEX idx_graph_links_strength ON graph_links(strength DESC);

-- Force Fields: Semantic gravity wells for node clustering
CREATE TABLE IF NOT EXISTS force_fields (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_id VARCHAR(255) UNIQUE NOT NULL,
    label VARCHAR(255) NOT NULL,

    -- Spatial Position
    x_coord DECIMAL(10,2),
    y_coord DECIMAL(10,2),
    radius INTEGER DEFAULT 150,

    -- Semantic Attraction
    semantic_vector JSONB DEFAULT '[]',
    field_strength DECIMAL(3,2) DEFAULT 0.5,

    -- Visual
    color VARCHAR(50) DEFAULT 'rgba(59, 130, 246, 0.1)',

    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- ==================================================================================
-- SECTION 2: NEUROPLASTICITY ENGINE (Memory Consolidation)
-- ==================================================================================

-- Tracks all neuroplasticity operations (CREATE_NODE, CREATE_LINK, DECAY_NODE)
CREATE TABLE IF NOT EXISTS neuroplasticity_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action VARCHAR(50) NOT NULL, -- 'CREATE_NODE', 'CREATE_LINK', 'DECAY_NODE', 'UPDATE_MASS', 'MERGE_NODES'

    -- Action Details
    target_node_id VARCHAR(255),
    source_node_id VARCHAR(255),
    params JSONB,
    reason TEXT,

    -- Execution Context
    triggered_by VARCHAR(255), -- Agent or system that triggered
    session_id UUID,

    -- Outcome
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_neuroplasticity_log_action ON neuroplasticity_log(action, created_at DESC);
CREATE INDEX idx_neuroplasticity_log_target ON neuroplasticity_log(target_node_id);

-- Hippocampal Replay: Training data generation for LLM fine-tuning
CREATE TABLE IF NOT EXISTS hippocampal_replays (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Training Pair
    instruction TEXT NOT NULL,
    input TEXT,
    output TEXT NOT NULL,

    -- Source Context
    source_node_ids VARCHAR(255)[],
    z_layer VARCHAR(50), -- Which layer this knowledge came from
    confidence_score DECIMAL(3,2) DEFAULT 0.8,

    -- Export Status
    exported_to_jsonl BOOLEAN DEFAULT FALSE,
    export_batch VARCHAR(255),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_hippocampal_replays_exported ON hippocampal_replays(exported_to_jsonl, created_at DESC);

-- ==================================================================================
-- SECTION 3: MULTI-AGENT SYSTEM (MCP Integration)
-- ==================================================================================

-- Agents: The 24 mob-themed agents
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(255),
    type VARCHAR(100) NOT NULL,
    dept VARCHAR(100), -- Department/System

    -- Status
    status VARCHAR(50) DEFAULT 'idle', -- 'idle', 'active', 'busy', 'offline'
    version VARCHAR(50) DEFAULT '1.0.0',

    -- Capabilities
    capabilities JSONB DEFAULT '[]',
    skills JSONB DEFAULT '[]',
    protocols JSONB DEFAULT '[]',

    -- Configuration
    config JSONB DEFAULT '{}',
    environment JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',

    -- Metrics
    tasks_completed INT DEFAULT 0,
    tasks_failed INT DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0.0,
    avg_response_time_ms INT,
    uptime_percentage DECIMAL(5,2),
    current_memory_mb INT,

    -- Talent Map Metrics
    influence_score DECIMAL(5,2) DEFAULT 0, -- Network centrality
    burnout_index DECIMAL(5,2) DEFAULT 0, -- Workload indicator
    risk_level VARCHAR(20) DEFAULT 'Stable', -- 'Stable', 'At-Risk', 'Critical'

    -- Physics Position (for visualization)
    x_pos DECIMAL(10,2) DEFAULT 0,
    y_pos DECIMAL(10,2) DEFAULT 0,
    mass DECIMAL(10,2) DEFAULT 10,
    radius DECIMAL(10,2) DEFAULT 20,

    -- Temporal
    last_active_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agents_agent_id ON agents(agent_id);
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_dept ON agents(dept);
CREATE INDEX idx_agents_influence_score ON agents(influence_score DESC);

-- Agent Interactions: Communication links between agents
CREATE TABLE IF NOT EXISTS agent_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    link_id VARCHAR(255) UNIQUE NOT NULL,
    source_agent_id VARCHAR(255) NOT NULL,
    target_agent_id VARCHAR(255) NOT NULL,

    -- Interaction Metrics
    frequency INTEGER DEFAULT 1, -- 1-10 scale
    interaction_type VARCHAR(50) DEFAULT 'collaboration', -- 'collaboration', 'reporting', 'social'

    -- Temporal
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_interaction TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agent_interactions_source ON agent_interactions(source_agent_id);
CREATE INDEX idx_agent_interactions_target ON agent_interactions(target_agent_id);

-- ==================================================================================
-- SECTION 4: WORKFLOW & TASK MANAGEMENT
-- ==================================================================================

CREATE TABLE IF NOT EXISTS workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(500) NOT NULL,
    description TEXT,

    -- Definition
    definition JSONB, -- DAG structure
    triggers JSONB DEFAULT '[]',

    -- Status
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'paused', 'archived'
    priority INTEGER DEFAULT 5,

    -- Metrics
    execution_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    avg_duration_ms INTEGER,

    -- Temporal
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_executed_at TIMESTAMPTZ
);

CREATE INDEX idx_workflows_status ON workflows(status);
CREATE INDEX idx_workflows_priority ON workflows(priority DESC);

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR(255) UNIQUE NOT NULL,
    workflow_id VARCHAR(255),
    agent_id VARCHAR(255),

    -- Task Details
    title VARCHAR(500) NOT NULL,
    description TEXT,
    task_type VARCHAR(100),

    -- Status
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'failed', 'blocked'
    priority INT DEFAULT 5,

    -- Execution
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    -- Temporal
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    deadline TIMESTAMPTZ,

    -- Metadata
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_agent_id ON tasks(agent_id);
CREATE INDEX idx_tasks_workflow_id ON tasks(workflow_id);
CREATE INDEX idx_tasks_priority ON tasks(priority DESC, created_at ASC);

-- ==================================================================================
-- SECTION 5: FINANCIAL PHYSICS ENGINE (Liquidity Simulation)
-- ==================================================================================

-- Financial Nodes: Sources, Tanks, Drains
CREATE TABLE IF NOT EXISTS financial_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_id VARCHAR(255) UNIQUE NOT NULL,
    label VARCHAR(255) NOT NULL,
    node_type VARCHAR(50) NOT NULL, -- 'source' (revenue), 'tank' (bank), 'drain' (expense)

    -- Financial State
    balance DECIMAL(15,2) DEFAULT 0, -- Current cash ($)
    capacity DECIMAL(15,2), -- Max typical value
    flow_rate DECIMAL(10,2) DEFAULT 0, -- $/day impact

    -- Physics (for visualization)
    x_pos DECIMAL(10,2),
    y_pos DECIMAL(10,2),
    radius DECIMAL(10,2) DEFAULT 40,

    -- Status
    alert_level VARCHAR(20) DEFAULT 'stable', -- 'stable', 'warning', 'critical'

    -- Temporal
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_financial_nodes_type ON financial_nodes(node_type);
CREATE INDEX idx_financial_nodes_alert_level ON financial_nodes(alert_level);

-- Financial Links: Money flow pipes
CREATE TABLE IF NOT EXISTS financial_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    link_id VARCHAR(255) UNIQUE NOT NULL,
    source_node_id VARCHAR(255) NOT NULL,
    target_node_id VARCHAR(255) NOT NULL,

    -- Flow Properties
    width INTEGER DEFAULT 4, -- Visual pipe width
    flow_rate DECIMAL(10,2) DEFAULT 0, -- Current $/day

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Cash Particles: Individual transaction visualization
CREATE TABLE IF NOT EXISTS cash_particles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    particle_id VARCHAR(255) UNIQUE NOT NULL,
    link_id VARCHAR(255) NOT NULL,

    -- Particle State
    progress DECIMAL(3,2) DEFAULT 0.0, -- 0.0 to 1.0
    value DECIMAL(10,2), -- $ value
    color VARCHAR(50),

    -- Temporal
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Financial Metrics (Real-time dashboard)
CREATE TABLE IF NOT EXISTS financial_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Aggregates
    total_liquidity DECIMAL(15,2),
    burn_rate DECIMAL(10,2), -- $/month
    runway_days INTEGER,

    -- Alert State
    solvency_status VARCHAR(50), -- 'Healthy', 'Warning', 'Critical'

    -- Timestamp
    measured_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_financial_metrics_measured_at ON financial_metrics(measured_at DESC);

-- ==================================================================================
-- SECTION 6: MEMORY SYSTEMS (Cognitive Memory)
-- ==================================================================================

CREATE TABLE IF NOT EXISTS memory_episodic (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255),
    agent_id VARCHAR(255),

    -- Event Details
    event_type VARCHAR(100),
    content TEXT,
    context JSONB DEFAULT '{}',

    -- Importance
    importance_score DECIMAL(3,2) DEFAULT 0.5,
    tags TEXT[],

    -- Temporal
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

CREATE INDEX idx_memory_episodic_agent ON memory_episodic(agent_id, created_at DESC);
CREATE INDEX idx_memory_episodic_session ON memory_episodic(session_id);

CREATE TABLE IF NOT EXISTS memory_semantic (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255),

    -- Knowledge
    knowledge_type VARCHAR(100),
    content TEXT,
    metadata JSONB DEFAULT '{}',

    -- Confidence
    confidence_score DECIMAL(3,2) DEFAULT 0.8,

    -- Temporal
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_memory_semantic_agent ON memory_semantic(agent_id);

CREATE TABLE IF NOT EXISTS memory_working (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255),

    -- Active Context
    context_window JSONB DEFAULT '{}',
    active_goals JSONB DEFAULT '[]',
    current_state JSONB DEFAULT '{}',

    -- Temporal
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

CREATE INDEX idx_memory_working_agent ON memory_working(agent_id);
CREATE INDEX idx_memory_working_expires ON memory_working(expires_at);

CREATE TABLE IF NOT EXISTS memory_consolidations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255),

    -- Consolidation
    source_memories UUID[],
    consolidated_knowledge TEXT,
    consolidation_type VARCHAR(50), -- 'sleep', 'rehearsal', 'integration'

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==================================================================================
-- SECTION 7: LEARNING & COLLABORATION
-- ==================================================================================

CREATE TABLE IF NOT EXISTS learning_episodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    episode_type VARCHAR(100),
    session_id VARCHAR(255),
    agent_id VARCHAR(255),

    -- Episode Data
    context_before JSONB,
    actions_taken JSONB,
    context_after JSONB,

    -- Outcome
    outcome VARCHAR(50), -- 'success', 'failure', 'partial'
    reward_signal DECIMAL(5,2),

    -- Complexity
    complexity_score DECIMAL(3,2),
    novelty_score DECIMAL(3,2),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_learning_episodes_agent ON learning_episodes(agent_id, created_at DESC);

CREATE TABLE IF NOT EXISTS llm_collaborations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255),
    agent_id VARCHAR(255),

    -- Prompt & Models
    prompt TEXT,
    local_model VARCHAR(100),
    cloud_model VARCHAR(100),

    -- Responses
    local_response TEXT,
    cloud_response TEXT,
    selected_model VARCHAR(100),

    -- Metrics
    quality_score DECIMAL(3,2),
    cost DECIMAL(10,6),
    latency_ms INT,

    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_llm_collaborations_agent ON llm_collaborations(agent_id, created_at DESC);

-- ==================================================================================
-- SECTION 8: A2A PROTOCOL (Agent-to-Agent Communication)
-- ==================================================================================

CREATE TABLE IF NOT EXISTS a2a_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_type VARCHAR(100),

    -- Participants
    participants JSONB DEFAULT '[]', -- Array of agent_ids

    -- Status
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'completed', 'archived'

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Temporal
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS a2a_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID,

    -- Routing
    from_agent_id VARCHAR(255),
    to_agent_id VARCHAR(255),

    -- Message
    message_type VARCHAR(50), -- 'request', 'response', 'broadcast', 'notification'
    content TEXT,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_a2a_messages_conversation ON a2a_messages(conversation_id, created_at ASC);
CREATE INDEX idx_a2a_messages_agent ON a2a_messages(to_agent_id, created_at DESC);

-- ==================================================================================
-- SECTION 9: SESSIONS & USERS
-- ==================================================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_ref TEXT UNIQUE,
    email TEXT UNIQUE,
    display_name TEXT,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Temporal
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_external_ref ON users(external_ref);
CREATE INDEX idx_users_email ON users(email);

CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    agent_id VARCHAR(255),

    -- Session Context
    label TEXT,
    context JSONB DEFAULT '{}',

    -- Status
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'completed', 'expired', 'archived'

    -- Temporal
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

CREATE INDEX idx_sessions_user ON sessions(user_id, created_at DESC);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_session_id ON sessions(session_id);

-- ==================================================================================
-- SECTION 10: TOOLS & ROUTING
-- ==================================================================================

CREATE TABLE IF NOT EXISTS tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    mcp_server TEXT,
    endpoint TEXT,

    -- Definition
    description TEXT,
    parameters_schema JSONB,

    -- Tags
    tags TEXT[] DEFAULT '{}',

    -- Ownership
    agent_id VARCHAR(255),
    mcp_system TEXT,

    -- Status
    enabled BOOLEAN DEFAULT TRUE,

    -- Temporal
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(name, mcp_server)
);

CREATE INDEX idx_tools_agent ON tools(agent_id);
CREATE INDEX idx_tools_tags ON tools USING gin(tags);
CREATE INDEX idx_tools_enabled ON tools(enabled) WHERE enabled = TRUE;

CREATE TABLE IF NOT EXISTS routing_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    description TEXT,

    -- Priority
    priority INTEGER NOT NULL DEFAULT 100, -- Lower = higher priority

    -- Matching
    task_tags TEXT[] NOT NULL DEFAULT '{}',

    -- Routing Targets
    preferred_llm UUID, -- References llms table (not included, add if needed)
    preferred_agent VARCHAR(255),
    preferred_tools UUID[],

    -- Constraints
    constraints JSONB DEFAULT '{}',

    -- Status
    enabled BOOLEAN DEFAULT TRUE,

    -- Metrics
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    avg_duration_ms DECIMAL(10,2),

    -- Temporal
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_routing_priority ON routing_rules(priority ASC, created_at ASC) WHERE enabled = TRUE;
CREATE INDEX idx_routing_tags ON routing_rules USING gin(task_tags);

-- ==================================================================================
-- SECTION 11: BLACKBOARD (Multi-Agent Coordination)
-- ==================================================================================

CREATE TABLE IF NOT EXISTS blackboard_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID,
    user_id UUID,
    agent_id VARCHAR(255),

    -- Content
    title TEXT,
    content TEXT NOT NULL,
    content_type TEXT DEFAULT 'text', -- 'text', 'json', 'markdown'

    -- Organization
    tags TEXT[] DEFAULT '{}',
    priority INTEGER DEFAULT 0, -- Higher = more important
    version INTEGER DEFAULT 1,
    parent_id UUID, -- For threaded entries

    -- Temporal
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_blackboard_session ON blackboard_entries(session_id, priority DESC, created_at DESC);
CREATE INDEX idx_blackboard_agent ON blackboard_entries(agent_id, created_at DESC);
CREATE INDEX idx_blackboard_expires ON blackboard_entries(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX idx_blackboard_tags ON blackboard_entries USING gin(tags);

-- ==================================================================================
-- SECTION 12: LLMS REGISTRY
-- ==================================================================================

CREATE TABLE IF NOT EXISTS llms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    provider TEXT NOT NULL, -- 'openai', 'anthropic', 'google', 'local'
    model_id TEXT NOT NULL,

    -- Capacity
    context_tokens INTEGER,
    max_output_tokens INTEGER,

    -- Pricing
    cost_per_1k_input DECIMAL(10,6),
    cost_per_1k_output DECIMAL(10,6),

    -- Capabilities
    tags TEXT[] DEFAULT '{}',
    capabilities JSONB DEFAULT '{}',

    -- Status
    enabled BOOLEAN DEFAULT TRUE,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Temporal
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_llms_provider ON llms(provider);
CREATE INDEX idx_llms_enabled ON llms(enabled) WHERE enabled = TRUE;
CREATE INDEX idx_llms_tags ON llms USING gin(tags);

-- ==================================================================================
-- SECTION 13: SYNC STATE TRACKING
-- ==================================================================================

CREATE TABLE IF NOT EXISTS sync_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(255) UNIQUE NOT NULL,

    -- Sync Status
    last_sync_at TIMESTAMPTZ,
    last_sync_direction VARCHAR(20), -- 'up' (local->cloud), 'down' (cloud->local), 'both'
    records_synced INTEGER DEFAULT 0,

    -- Conflict Resolution
    conflicts_detected INTEGER DEFAULT 0,
    conflicts_resolved INTEGER DEFAULT 0,

    -- Errors
    last_error TEXT,
    error_count INTEGER DEFAULT 0,

    -- Metadata
    metadata JSONB DEFAULT '{}'
);

-- ==================================================================================
-- SECTION 14: VISUALIZATION METADATA
-- ==================================================================================

-- Store visualization snapshots for replay/audit
CREATE TABLE IF NOT EXISTS visualization_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_type VARCHAR(50), -- 'brain', 'talent_map', 'liquidity_engine', 'workflow_matrix'

    -- Snapshot Data
    nodes JSONB,
    links JSONB,
    metrics JSONB,

    -- Context
    session_id UUID,
    user_id UUID,

    -- Temporal
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_visualization_snapshots_type ON visualization_snapshots(snapshot_type, created_at DESC);

-- ==================================================================================
-- SUMMARY
-- ==================================================================================
-- TOTAL TABLES: 35
--
-- 1. graph_nodes                  - Knowledge graph nodes (3D semantic space)
-- 2. graph_links                  - Synaptic connections between nodes
-- 3. force_fields                 - Semantic gravity wells
-- 4. neuroplasticity_log          - Brain update operations log
-- 5. hippocampal_replays          - LLM training data generation
-- 6. agents                       - 24 mob-themed agents
-- 7. agent_interactions           - Agent communication links
-- 8. workflows                    - Workflow definitions
-- 9. tasks                        - Task execution tracking
-- 10. financial_nodes             - Revenue/Bank/Expense nodes
-- 11. financial_links             - Money flow pipes
-- 12. cash_particles              - Transaction visualization
-- 13. financial_metrics           - Real-time financial dashboard
-- 14. memory_episodic             - Episodic memory system
-- 15. memory_semantic             - Semantic memory system
-- 16. memory_working              - Working memory system
-- 17. memory_consolidations       - Memory consolidation tracking
-- 18. learning_episodes           - Learning event tracking
-- 19. llm_collaborations          - Local vs Cloud LLM selection
-- 20. a2a_conversations           - Agent-to-agent conversations
-- 21. a2a_messages                - A2A protocol messages
-- 22. users                       - User identity management
-- 23. sessions                    - Session context tracking
-- 24. tools                       - MCP tool registry
-- 25. routing_rules               - Capability-based routing
-- 26. blackboard_entries          - Multi-agent coordination
-- 27. llms                        - LLM registry
-- 28. sync_state                  - Bi-directional sync tracking
-- 29. visualization_snapshots     - Visualization replay data
--
-- Plus migration tracking (schema_migrations) already exists
-- ==================================================================================
