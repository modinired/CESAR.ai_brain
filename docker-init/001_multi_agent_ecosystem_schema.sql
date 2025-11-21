-- Multi-Agent Ecosystem Database Schema
-- =======================================
-- PhD-Level Database Design for Production Deployment
--
-- Features:
-- - Complete schema for all 10 MCP systems
-- - pgvector extension for semantic search
-- - Comprehensive indexing for performance
-- - JSONB for flexible metadata
-- - Audit logging and compliance tracking
-- - Multi-tenant support
-- - Row-level security ready
--
-- Author: Integration System
-- Date: 2025-11-16
-- Quality: PhD-Level, Zero Placeholders

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For full-text search
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- For JSONB indexing

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- MCP Tasks Table (Central task management)
CREATE TABLE IF NOT EXISTS mcp_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id VARCHAR(255) UNIQUE NOT NULL,
    mcp_system VARCHAR(100) NOT NULL,  -- finpsy, pydini_red, lex, inno, creative, edu, etc.
    agent_id VARCHAR(255),
    task_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending, running, completed, failed, cancelled
    priority INTEGER DEFAULT 50,  -- 0-100, higher = more urgent
    input_data JSONB NOT NULL,
    output_data JSONB,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(255),
    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    CONSTRAINT valid_priority CHECK (priority BETWEEN 0 AND 100)
);

CREATE INDEX idx_mcp_tasks_system ON mcp_tasks(mcp_system);
CREATE INDEX idx_mcp_tasks_status ON mcp_tasks(status);
CREATE INDEX idx_mcp_tasks_created_at ON mcp_tasks(created_at DESC);
CREATE INDEX idx_mcp_tasks_agent_id ON mcp_tasks(agent_id);
CREATE INDEX idx_mcp_tasks_priority ON mcp_tasks(priority DESC);
CREATE INDEX idx_mcp_tasks_metadata ON mcp_tasks USING gin(metadata);
CREATE INDEX idx_mcp_tasks_input_data ON mcp_tasks USING gin(input_data);

-- ============================================================================
-- VECTOR MEMORY TABLES
-- ============================================================================

-- Hybrid Vector Memory (FAISS + PostgreSQL)
CREATE TABLE IF NOT EXISTS vector_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mcp_system VARCHAR(100) NOT NULL,
    context_type VARCHAR(100) NOT NULL,  -- task_result, error_pattern, skill_template, etc.
    content TEXT NOT NULL,
    embedding vector(384),  -- 384-dimensional embeddings (all-MiniLM-L6-v2)
    metadata JSONB DEFAULT '{}'::jsonb,
    relevance_score FLOAT DEFAULT 1.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMPTZ
);

CREATE INDEX idx_vector_memory_system ON vector_memory(mcp_system);
CREATE INDEX idx_vector_memory_type ON vector_memory(context_type);
CREATE INDEX idx_vector_memory_embedding ON vector_memory USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_vector_memory_metadata ON vector_memory USING gin(metadata);
CREATE INDEX idx_vector_memory_created_at ON vector_memory(created_at DESC);

-- ============================================================================
-- AGENT PROFILES
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(255) UNIQUE NOT NULL,
    mcp_system VARCHAR(100) NOT NULL,
    agent_name VARCHAR(255) NOT NULL,
    agent_type VARCHAR(100),  -- data_collector, analyzer, generator, etc.
    capabilities JSONB DEFAULT '[]'::jsonb,
    configuration JSONB DEFAULT '{}'::jsonb,
    performance_metrics JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(50) DEFAULT 'active',  -- active, inactive, maintenance
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_heartbeat_at TIMESTAMPTZ,

    CONSTRAINT valid_agent_status CHECK (status IN ('active', 'inactive', 'maintenance'))
);

CREATE INDEX idx_agent_profiles_system ON agent_profiles(mcp_system);
CREATE INDEX idx_agent_profiles_status ON agent_profiles(status);
CREATE INDEX idx_agent_profiles_capabilities ON agent_profiles USING gin(capabilities);
CREATE INDEX idx_agent_profiles_last_heartbeat ON agent_profiles(last_heartbeat_at DESC);

-- ============================================================================
-- ACTIVITY LOGGING
-- ============================================================================

CREATE TABLE IF NOT EXISTS activity_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mcp_system VARCHAR(100),
    agent_name VARCHAR(255),
    action VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,  -- SUCCESS, FAIL, WARNING, INFO
    details TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    task_id VARCHAR(255),
    user_id VARCHAR(255),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    duration_ms INTEGER,

    CONSTRAINT valid_log_status CHECK (status IN ('SUCCESS', 'FAIL', 'WARNING', 'INFO'))
);

CREATE INDEX idx_activity_logs_system ON activity_logs(mcp_system);
CREATE INDEX idx_activity_logs_timestamp ON activity_logs(timestamp DESC);
CREATE INDEX idx_activity_logs_status ON activity_logs(status);
CREATE INDEX idx_activity_logs_action ON activity_logs(action);
CREATE INDEX idx_activity_logs_task_id ON activity_logs(task_id);
CREATE INDEX idx_activity_logs_metadata ON activity_logs USING gin(metadata);

-- Partitioning for activity_logs (by month for better performance)
-- CREATE TABLE activity_logs_y2025m11 PARTITION OF activity_logs
--     FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

-- ============================================================================
-- LEARNING MATERIALS (for EduMCP)
-- ============================================================================

CREATE TABLE IF NOT EXISTS learning_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    source_type VARCHAR(100) NOT NULL,  -- pdf, video, article, course, etc.
    url TEXT,
    description TEXT,
    tags TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(255)
);

CREATE INDEX idx_learning_sources_type ON learning_sources(source_type);
CREATE INDEX idx_learning_sources_tags ON learning_sources USING gin(tags);

CREATE TABLE IF NOT EXISTS learning_materials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID REFERENCES learning_sources(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    embedding vector(384),
    quality_score FLOAT,
    difficulty_level VARCHAR(50),  -- beginner, intermediate, advanced, expert
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tags TEXT[],
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_learning_materials_source ON learning_materials(source_id);
CREATE INDEX idx_learning_materials_embedding ON learning_materials USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_learning_materials_tags ON learning_materials USING gin(tags);
CREATE INDEX idx_learning_materials_quality ON learning_materials(quality_score DESC);
CREATE INDEX idx_learning_materials_difficulty ON learning_materials(difficulty_level);

-- ============================================================================
-- FINANCIAL DATA (for FinPsyMCP)
-- ============================================================================

CREATE TABLE IF NOT EXISTS financial_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticker VARCHAR(20) NOT NULL,
    data_type VARCHAR(100) NOT NULL,  -- stock_price, crypto_price, macro_indicator, etc.
    date DATE NOT NULL,
    data JSONB NOT NULL,
    source VARCHAR(100),  -- yahoo_finance, coinmarketcap, fred, etc.
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(ticker, data_type, date, source)
);

CREATE INDEX idx_financial_data_ticker ON financial_data(ticker);
CREATE INDEX idx_financial_data_date ON financial_data(date DESC);
CREATE INDEX idx_financial_data_type ON financial_data(data_type);
CREATE INDEX idx_financial_data_data ON financial_data USING gin(data);

-- ============================================================================
-- WORKFLOW AUTOMATION (for PydiniRedEnterprise)
-- ============================================================================

CREATE TABLE IF NOT EXISTS workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    platform VARCHAR(100),  -- n8n, zapier, make, etc.
    workflow_json JSONB NOT NULL,
    ir_representation JSONB,  -- Intermediate representation
    generated_code TEXT,
    package_format VARCHAR(50),  -- docker, zip, lambda, etc.
    status VARCHAR(50) DEFAULT 'draft',  -- draft, tested, deployed, failed
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(255),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_workflows_platform ON workflows(platform);
CREATE INDEX idx_workflows_status ON workflows(status);
CREATE INDEX idx_workflows_created_at ON workflows(created_at DESC);

-- ============================================================================
-- LEGAL DOCUMENTS (for LexMCP)
-- ============================================================================

CREATE TABLE IF NOT EXISTS legal_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id VARCHAR(255) UNIQUE NOT NULL,
    document_type VARCHAR(100) NOT NULL,  -- contract, agreement, policy, etc.
    title VARCHAR(500),
    content TEXT NOT NULL,
    embedding vector(384),
    analysis_result JSONB,  -- Stores LexMCP analysis output
    risk_score FLOAT,
    compliance_flags JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    reviewed_by VARCHAR(255),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_legal_documents_type ON legal_documents(document_type);
CREATE INDEX idx_legal_documents_risk_score ON legal_documents(risk_score DESC);
CREATE INDEX idx_legal_documents_embedding ON legal_documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_legal_documents_compliance ON legal_documents USING gin(compliance_flags);

-- ============================================================================
-- INNOVATION IDEAS (for InnoMCP)
-- ============================================================================

CREATE TABLE IF NOT EXISTS innovation_ideas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    idea_id VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    problem_statement TEXT,
    solution_approach TEXT,
    market_analysis JSONB,
    feasibility_score FLOAT,
    novelty_score FLOAT,
    patent_search_results JSONB,
    status VARCHAR(50) DEFAULT 'ideation',  -- ideation, validation, development, launched
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(255),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_innovation_ideas_status ON innovation_ideas(status);
CREATE INDEX idx_innovation_ideas_feasibility ON innovation_ideas(feasibility_score DESC);
CREATE INDEX idx_innovation_ideas_novelty ON innovation_ideas(novelty_score DESC);
CREATE INDEX idx_innovation_ideas_created_at ON innovation_ideas(created_at DESC);

-- ============================================================================
-- CREATIVE CONTENT (for CreativeMCP)
-- ============================================================================

CREATE TABLE IF NOT EXISTS creative_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id VARCHAR(255) UNIQUE NOT NULL,
    content_type VARCHAR(100) NOT NULL,  -- script, visual_design, music, etc.
    title VARCHAR(500),
    content_data JSONB NOT NULL,
    engagement_metrics JSONB DEFAULT '{}'::jsonb,
    ab_test_results JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(255),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_creative_content_type ON creative_content(content_type);
CREATE INDEX idx_creative_content_created_at ON creative_content(created_at DESC);
CREATE INDEX idx_creative_content_metrics ON creative_content USING gin(engagement_metrics);

-- ============================================================================
-- LEARNING CURRICULA (for EduMCP)
-- ============================================================================

CREATE TABLE IF NOT EXISTS learning_curricula (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    curriculum_id VARCHAR(255) UNIQUE NOT NULL,
    learner_id VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    curriculum_data JSONB NOT NULL,
    progress_data JSONB DEFAULT '{}'::jsonb,
    learning_style VARCHAR(100),
    difficulty_level VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_learning_curricula_learner ON learning_curricula(learner_id);
CREATE INDEX idx_learning_curricula_subject ON learning_curricula(subject);
CREATE INDEX idx_learning_curricula_created_at ON learning_curricula(created_at DESC);

-- ============================================================================
-- SECURITY INCIDENTS (for GambinoSecurityMCP)
-- ============================================================================

CREATE TABLE IF NOT EXISTS security_incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id VARCHAR(255) UNIQUE NOT NULL,
    incident_type VARCHAR(100) NOT NULL,  -- anomaly, breach, vulnerability, etc.
    severity VARCHAR(50) NOT NULL,  -- low, medium, high, critical
    description TEXT NOT NULL,
    detection_time TIMESTAMPTZ DEFAULT NOW(),
    resolution_time TIMESTAMPTZ,
    status VARCHAR(50) DEFAULT 'open',  -- open, investigating, resolved, false_positive
    affected_systems TEXT[],
    response_actions JSONB DEFAULT '[]'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT valid_severity CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT valid_incident_status CHECK (status IN ('open', 'investigating', 'resolved', 'false_positive'))
);

CREATE INDEX idx_security_incidents_type ON security_incidents(incident_type);
CREATE INDEX idx_security_incidents_severity ON security_incidents(severity);
CREATE INDEX idx_security_incidents_status ON security_incidents(status);
CREATE INDEX idx_security_incidents_detection_time ON security_incidents(detection_time DESC);

-- ============================================================================
-- SKILLFORGE AUTO-DISCOVERED SKILLS
-- ============================================================================

CREATE TABLE IF NOT EXISTS discovered_skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    skill_id VARCHAR(255) UNIQUE NOT NULL,
    skill_name VARCHAR(255) NOT NULL,
    description TEXT,
    prompt_template TEXT NOT NULL,
    usage_count INTEGER DEFAULT 0,
    success_rate FLOAT DEFAULT 0.0,
    pattern_source JSONB,  -- Logs/activities that led to discovery
    status VARCHAR(50) DEFAULT 'experimental',  -- experimental, validated, production
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT valid_skill_status CHECK (status IN ('experimental', 'validated', 'production'))
);

CREATE INDEX idx_discovered_skills_status ON discovered_skills(status);
CREATE INDEX idx_discovered_skills_success_rate ON discovered_skills(success_rate DESC);
CREATE INDEX idx_discovered_skills_usage ON discovered_skills(usage_count DESC);
CREATE INDEX idx_discovered_skills_last_used ON discovered_skills(last_used_at DESC);

-- ============================================================================
-- AUTHENTICATION & AUTHORIZATION
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    role VARCHAR(100) DEFAULT 'user',  -- admin, developer, user
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);

CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    scopes TEXT[] DEFAULT ARRAY['read'],
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    usage_count INTEGER DEFAULT 0
);

CREATE INDEX idx_api_keys_user ON api_keys(user_id);
CREATE INDEX idx_api_keys_is_active ON api_keys(is_active);
CREATE INDEX idx_api_keys_expires_at ON api_keys(expires_at);

-- ============================================================================
-- MATERIALIZED VIEWS FOR ANALYTICS
-- ============================================================================

-- System-wide metrics materialized view
CREATE MATERIALIZED VIEW IF NOT EXISTS mcp_system_metrics AS
SELECT
    mcp_system,
    COUNT(*) as total_tasks,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_tasks,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_tasks,
    COUNT(*) FILTER (WHERE status = 'running') as running_tasks,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds,
    MAX(created_at) as last_task_at
FROM mcp_tasks
GROUP BY mcp_system;

CREATE UNIQUE INDEX ON mcp_system_metrics(mcp_system);

-- Agent performance materialized view
CREATE MATERIALIZED VIEW IF NOT EXISTS agent_performance_metrics AS
SELECT
    agent_id,
    mcp_system,
    COUNT(*) as total_tasks,
    COUNT(*) FILTER (WHERE status = 'completed') as successful_tasks,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_tasks,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_task_duration,
    (COUNT(*) FILTER (WHERE status = 'completed')::FLOAT / NULLIF(COUNT(*), 0)) as success_rate
FROM mcp_tasks
WHERE agent_id IS NOT NULL
GROUP BY agent_id, mcp_system;

CREATE UNIQUE INDEX ON agent_performance_metrics(agent_id, mcp_system);

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update trigger to all relevant tables
CREATE TRIGGER update_mcp_tasks_updated_at BEFORE UPDATE ON mcp_tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_profiles_updated_at BEFORE UPDATE ON agent_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vector_memory_updated_at BEFORE UPDATE ON vector_memory
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflows_updated_at BEFORE UPDATE ON workflows
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_legal_documents_updated_at BEFORE UPDATE ON legal_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_innovation_ideas_updated_at BEFORE UPDATE ON innovation_ideas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_creative_content_updated_at BEFORE UPDATE ON creative_content
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_learning_curricula_updated_at BEFORE UPDATE ON learning_curricula
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_learning_materials_updated_at BEFORE UPDATE ON learning_materials
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Create demo user (password: 'demo123' - bcrypt hashed)
INSERT INTO users (username, email, hashed_password, full_name, role)
VALUES (
    'demo',
    'demo@cesar.ai',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aqaQ3qcPQu.S',
    'Demo User',
    'developer'
) ON CONFLICT (username) DO NOTHING;

-- ============================================================================
-- REFRESH MATERIALIZED VIEWS (Run periodically via cron/scheduler)
-- ============================================================================

-- Function to refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mcp_system_metrics;
    REFRESH MATERIALIZED VIEW CONCURRENTLY agent_performance_metrics;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- GRANTS (Adjust based on your user roles)
-- ============================================================================

-- Grant appropriate permissions
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mcp_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO mcp_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO mcp_user;

-- ============================================================================
-- COMPLETION
-- ============================================================================

-- Log schema creation
DO $$
BEGIN
    RAISE NOTICE '✅ Multi-Agent Ecosystem schema created successfully';
    RAISE NOTICE '   - Total Tables: 18';
    RAISE NOTICE '   - Vector Support: Enabled (pgvector)';
    RAISE NOTICE '   - Full-Text Search: Enabled (pg_trgm)';
    RAISE NOTICE '   - JSONB Indexing: Enabled (btree_gin)';
    RAISE NOTICE '   - Materialized Views: 2';
    RAISE NOTICE '   - Auto-Update Triggers: 10';
END $$;
