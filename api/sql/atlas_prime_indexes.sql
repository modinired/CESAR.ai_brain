-- Indexes for graph, workflows, cognition, and vector memory

-- Graph
CREATE INDEX IF NOT EXISTS idx_brain_edges_tenant_source ON brain_edges (tenant_id, source_id);
CREATE INDEX IF NOT EXISTS idx_brain_edges_tenant_target ON brain_edges (tenant_id, target_id);
CREATE INDEX IF NOT EXISTS idx_brain_nodes_tenant_type ON brain_nodes (tenant_id, type);

-- Workflows / Automation
CREATE INDEX IF NOT EXISTS idx_workflow_events_wf_created ON workflow_events (workflow_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_workflow_events_status ON workflow_events (status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_workflow_steps_wf_type ON workflow_steps (workflow_id, type);
CREATE INDEX IF NOT EXISTS idx_bottleneck_scores_wf ON bottleneck_scores (workflow_id, updated_at DESC);

-- Cognition
CREATE INDEX IF NOT EXISTS idx_self_reflections_agent_date ON agent_self_reflections (agent_id, reflection_date);
CREATE INDEX IF NOT EXISTS idx_one_on_one_agent_user_week ON agent_one_on_one (agent_id, user_id, week_start);
CREATE INDEX IF NOT EXISTS idx_agent_traces_agent_created ON agent_traces (agent_id, created_at DESC);

-- API Keys
CREATE UNIQUE INDEX IF NOT EXISTS uq_api_keys_hash ON api_keys (hashed_key);

-- Vector memory
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS vector_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ivfflat_vector_memory_embedding ON vector_memory USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
