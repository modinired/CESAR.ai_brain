-- Phase B: Cognitive Memory System
-- Implements episodic memory, semantic memory, and memory consolidation

-- Episodic Memory: Stores specific conversation events with full context
CREATE TABLE IF NOT EXISTS memory_episodic (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id uuid REFERENCES sessions(id) ON DELETE CASCADE,
    user_id uuid REFERENCES users(id) ON DELETE SET NULL,
    agent_id text REFERENCES agents(agent_id) ON DELETE SET NULL,

    -- Episode content
    event_type text NOT NULL, -- 'user_message', 'agent_response', 'tool_invocation', etc.
    content text NOT NULL,
    context jsonb DEFAULT '{}'::jsonb,

    -- Temporal information
    timestamp timestamptz NOT NULL DEFAULT now(),
    sequence_number integer, -- Order within session

    -- Memory metadata
    importance_score numeric(5,2) DEFAULT 0.5, -- 0.0 to 1.0
    emotional_valence numeric(5,2), -- -1.0 (negative) to 1.0 (positive)
    tags text[] DEFAULT '{}',

    -- Consolidation tracking
    consolidated boolean DEFAULT false,
    consolidation_date timestamptz,
    semantic_memory_id uuid,

    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_episodic_session ON memory_episodic(session_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_episodic_agent ON memory_episodic(agent_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_episodic_importance ON memory_episodic(importance_score DESC);
CREATE INDEX IF NOT EXISTS idx_episodic_unconsolidated ON memory_episodic(consolidated) WHERE NOT consolidated;

-- Semantic Memory: Stores consolidated knowledge and patterns
CREATE TABLE IF NOT EXISTS memory_semantic (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Knowledge content
    concept text NOT NULL, -- Main concept/topic
    summary text NOT NULL, -- Consolidated summary
    details jsonb DEFAULT '{}'::jsonb,

    -- Source tracking
    source_episodes uuid[], -- IDs from memory_episodic
    source_count integer DEFAULT 1,

    -- Knowledge metadata
    confidence_score numeric(5,2) DEFAULT 0.5, -- 0.0 to 1.0
    category text, -- 'fact', 'procedure', 'preference', 'pattern'
    tags text[] DEFAULT '{}',

    -- Temporal tracking
    first_learned timestamptz NOT NULL DEFAULT now(),
    last_reinforced timestamptz NOT NULL DEFAULT now(),
    access_count integer DEFAULT 0,

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_semantic_concept ON memory_semantic(concept);
CREATE INDEX IF NOT EXISTS idx_semantic_category ON memory_semantic(category);
CREATE INDEX IF NOT EXISTS idx_semantic_confidence ON memory_semantic(confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_semantic_access ON memory_semantic(access_count DESC);

-- Semantic Memory Embeddings: Vector embeddings for semantic search
CREATE TABLE IF NOT EXISTS memory_semantic_embeddings (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    semantic_memory_id uuid REFERENCES memory_semantic(id) ON DELETE CASCADE,
    embedding vector(1536), -- OpenAI/Anthropic embedding dimension
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_semantic_embeddings_vector
    ON memory_semantic_embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Memory Consolidation Jobs: Tracks background consolidation tasks
CREATE TABLE IF NOT EXISTS memory_consolidations (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Consolidation scope
    session_id uuid REFERENCES sessions(id) ON DELETE CASCADE,
    agent_id text REFERENCES agents(agent_id) ON DELETE SET NULL,

    -- Job metadata
    status text NOT NULL DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    started_at timestamptz,
    completed_at timestamptz,

    -- Results
    episodes_processed integer DEFAULT 0,
    semantic_memories_created integer DEFAULT 0,
    semantic_memories_updated integer DEFAULT 0,
    error_message text,

    -- Configuration
    consolidation_strategy text DEFAULT 'similarity_clustering', -- 'similarity_clustering', 'temporal_clustering', 'topic_modeling'
    min_importance_threshold numeric(5,2) DEFAULT 0.3,

    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_consolidations_status ON memory_consolidations(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_consolidations_session ON memory_consolidations(session_id);

-- Working Memory: Short-term context for active conversations
CREATE TABLE IF NOT EXISTS memory_working (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id uuid REFERENCES sessions(id) ON DELETE CASCADE,
    agent_id text REFERENCES agents(agent_id) ON DELETE CASCADE,

    -- Working memory content
    context jsonb NOT NULL DEFAULT '{}'::jsonb,
    active_goals text[],
    recent_topics text[],

    -- Attention tracking
    attention_focus text, -- Current primary focus
    attention_weights jsonb, -- Weights for different memory systems

    -- Capacity management
    max_items integer DEFAULT 7, -- Miller's Law: 7±2 items
    current_load integer DEFAULT 0,

    -- Temporal management
    last_accessed timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz,

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_working_session_agent ON memory_working(session_id, agent_id);
CREATE INDEX IF NOT EXISTS idx_working_active ON memory_working(last_accessed DESC);

-- Memory Retrieval Log: Tracks which memories are accessed and why
CREATE TABLE IF NOT EXISTS memory_retrieval_log (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id uuid REFERENCES sessions(id) ON DELETE SET NULL,
    agent_id text REFERENCES agents(agent_id) ON DELETE SET NULL,

    -- Retrieval details
    query text NOT NULL,
    retrieval_type text NOT NULL, -- 'episodic', 'semantic', 'working', 'hybrid'

    -- Results
    memories_retrieved jsonb, -- Array of {memory_id, score, type}
    retrieval_strategy text, -- 'embedding', 'temporal', 'importance', 'hybrid'

    -- Performance metrics
    retrieval_time_ms numeric(10,2),
    relevance_scores jsonb,

    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_retrieval_session ON memory_retrieval_log(session_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_retrieval_agent ON memory_retrieval_log(agent_id, created_at DESC);

-- Update learning_reflections to link with episodic memory
ALTER TABLE learning_reflections
ADD COLUMN IF NOT EXISTS episodic_memory_id uuid REFERENCES memory_episodic(id) ON DELETE SET NULL;

-- Create view for unified memory access
CREATE OR REPLACE VIEW memory_unified AS
SELECT
    'episodic' as memory_type,
    id,
    session_id,
    agent_id,
    content,
    tags,
    importance_score as relevance_score,
    timestamp as created_at
FROM memory_episodic
UNION ALL
SELECT
    'semantic' as memory_type,
    id,
    NULL as session_id,
    NULL as agent_id,
    summary as content,
    tags,
    confidence_score as relevance_score,
    created_at
FROM memory_semantic;

COMMENT ON TABLE memory_episodic IS 'Episodic memory: specific conversation events and experiences';
COMMENT ON TABLE memory_semantic IS 'Semantic memory: consolidated knowledge and learned patterns';
COMMENT ON TABLE memory_consolidations IS 'Background jobs for episodic → semantic consolidation';
COMMENT ON TABLE memory_working IS 'Working memory: short-term context for active conversations';
COMMENT ON TABLE memory_retrieval_log IS 'Audit trail of memory system queries';
