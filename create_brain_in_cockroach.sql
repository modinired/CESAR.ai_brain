-- CESAR Living Brain Architecture in CockroachDB
-- Complete memory, learning, and collaboration system

-- 1. Memory Tables (The Brain's Memory Systems)
CREATE TABLE IF NOT EXISTS memory_episodic (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255),
    agent_id VARCHAR(255),
    event_type VARCHAR(100),
    content TEXT,
    context JSONB DEFAULT '{}',
    importance_score DECIMAL(3,2),
    tags TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS memory_semantic (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255),
    knowledge_type VARCHAR(100),
    content TEXT,
    metadata JSONB DEFAULT '{}',
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS memory_working (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255),
    context_window JSONB DEFAULT '{}',
    active_goals JSONB DEFAULT '[]',
    current_state JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS memory_consolidations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255),
    source_memories UUID[],
    consolidated_knowledge TEXT,
    consolidation_type VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Learning System (Continual Learning)
CREATE TABLE IF NOT EXISTS learning_episodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    episode_type VARCHAR(100),
    session_id VARCHAR(255),
    agent_id VARCHAR(255),
    context_before JSONB,
    actions_taken JSONB,
    context_after JSONB,
    outcome VARCHAR(50),
    reward_signal DECIMAL(5,2),
    complexity_score DECIMAL(3,2),
    novelty_score DECIMAL(3,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS llm_collaborations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255),
    agent_id VARCHAR(255),
    prompt TEXT,
    local_model VARCHAR(100),
    cloud_model VARCHAR(100),
    local_response TEXT,
    cloud_response TEXT,
    selected_model VARCHAR(100),
    quality_score DECIMAL(3,2),
    cost DECIMAL(10,6),
    latency_ms INT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Agent Communication (A2A Protocol)
CREATE TABLE IF NOT EXISTS a2a_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_type VARCHAR(100),
    participants JSONB DEFAULT '[]',
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS a2a_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID,
    from_agent_id VARCHAR(255),
    to_agent_id VARCHAR(255),
    message_type VARCHAR(50),
    content TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Workflows & Tasks
CREATE TABLE IF NOT EXISTS workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id VARCHAR(255) UNIQUE,
    name VARCHAR(500),
    description TEXT,
    definition JSONB,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR(255) UNIQUE,
    agent_id VARCHAR(255),
    title VARCHAR(500),
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    priority INT DEFAULT 5,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) UNIQUE,
    user_id VARCHAR(255),
    agent_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_memory_episodic_agent ON memory_episodic(agent_id);
CREATE INDEX IF NOT EXISTS idx_memory_episodic_session ON memory_episodic(session_id);
CREATE INDEX IF NOT EXISTS idx_memory_semantic_agent ON memory_semantic(agent_id);
CREATE INDEX IF NOT EXISTS idx_learning_episodes_agent ON learning_episodes(agent_id);
CREATE INDEX IF NOT EXISTS idx_llm_collab_agent ON llm_collaborations(agent_id);
CREATE INDEX IF NOT EXISTS idx_a2a_messages_conversation ON a2a_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_tasks_agent ON tasks(agent_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id);
