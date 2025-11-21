-- MCP Ecosystem Extensions for Multi-Agent Learning System
-- Integrates all 6 MCP systems into the existing learning ecosystem

-- This extends the existing schema with MCP-specific tables while maintaining
-- compatibility with the original learning_sources, learning_materials, etc.

-- ============================================================================
-- MCP AGENT REGISTRY (Extends agent_profile)
-- ============================================================================

-- Add MCP-specific columns to existing agent_profile if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='agent_profile' AND column_name='mcp_system') THEN
        ALTER TABLE agent_profile ADD COLUMN mcp_system VARCHAR(50);
        ALTER TABLE agent_profile ADD COLUMN mcp_capabilities JSONB DEFAULT '{}';
        ALTER TABLE agent_profile ADD COLUMN mcp_config JSONB DEFAULT '{}';
    END IF;
END $$;

-- Create index for MCP system filtering
CREATE INDEX IF NOT EXISTS idx_agent_profile_mcp_system ON agent_profile(mcp_system);

-- Insert MCP-specific agents
INSERT INTO agent_profile (agent_id, agent_name, agent_type, description, specialization, mcp_system, status) VALUES
-- PydiniRed agents
('mcp_pydini_orchestrator', 'PydiniRed Orchestrator', 'coordinator', 'Workflow conversion orchestration', ARRAY['workflow_automation', 'multi_platform'], 'pydini_red', 'active'),
('mcp_pydini_adapter', 'Platform Adapter Agent', 'scraper', 'Multi-platform workflow parsing', ARRAY['n8n', 'zapier', 'make'], 'pydini_red', 'active'),
('mcp_pydini_ir', 'IR Validation Agent', 'analyzer', 'Intermediate representation validation', ARRAY['ir_validation', 'schema_checking'], 'pydini_red', 'active'),
('mcp_pydini_codegen', 'Code Generation Agent', 'specialist', 'Python script generation from IR', ARRAY['code_generation', 'templating'], 'pydini_red', 'active'),
('mcp_pydini_testing', 'Testing Agent', 'specialist', 'Automated script testing', ARRAY['testing', 'validation'], 'pydini_red', 'active'),
('mcp_pydini_packaging', 'Packaging Agent', 'specialist', 'Script packaging and distribution', ARRAY['packaging', 'deployment'], 'pydini_red', 'active'),

-- FinPsy agents
('mcp_finpsy_orchestrator', 'FinPsy Orchestrator', 'coordinator', 'Financial analysis coordination', ARRAY['finance', 'psychology', 'strategy'], 'finpsy', 'active'),
('mcp_finpsy_data_collector', 'Data Collector Agent', 'scraper', 'Multi-source financial data collection', ARRAY['stocks', 'crypto', 'macro'], 'finpsy', 'active'),
('mcp_finpsy_sentiment', 'Sentiment Analysis Agent', 'analyzer', 'Behavioral sentiment analysis', ARRAY['nlp', 'sentiment', 'psychology'], 'finpsy', 'active'),
('mcp_finpsy_analytics', 'Analytics Agent', 'analyzer', 'Statistical and quantitative analysis', ARRAY['statistics', 'correlation', 'volatility'], 'finpsy', 'active'),
('mcp_finpsy_forecast', 'Forecast Agent', 'specialist', 'Time-series forecasting', ARRAY['prophet', 'forecasting', 'ml'], 'finpsy', 'active'),
('mcp_finpsy_portfolio', 'Portfolio Optimization Agent', 'specialist', 'Portfolio optimization and allocation', ARRAY['optimization', 'risk_management'], 'finpsy', 'active'),
('mcp_finpsy_strategic', 'Strategic Decision Agent', 'coordinator', 'Strategic investment decisions', ARRAY['strategy', 'decision_making'], 'finpsy', 'active'),

-- Lex agents
('mcp_lex_parser', 'Legal Parser Agent', 'analyzer', 'Legal document parsing and extraction', ARRAY['nlp', 'legal', 'parsing'], 'lex', 'active'),
('mcp_lex_contract', 'Contract Analyzer Agent', 'analyzer', 'Contract analysis and clause extraction', ARRAY['contracts', 'compliance'], 'lex', 'active'),
('mcp_lex_risk', 'Risk Assessment Agent', 'specialist', 'Legal risk quantification', ARRAY['risk_assessment', 'compliance'], 'lex', 'active'),
('mcp_lex_regulatory', 'Regulatory Tracker Agent', 'scraper', 'Regulatory change monitoring', ARRAY['regulations', 'compliance', 'monitoring'], 'lex', 'active'),

-- Inno agents
('mcp_inno_patent', 'Patent Scout Agent', 'scraper', 'Patent database search and analysis', ARRAY['patents', 'ip', 'research'], 'inno', 'active'),
('mcp_inno_market', 'Market Trend Agent', 'analyzer', 'Market trend identification', ARRAY['market_analysis', 'trends'], 'inno', 'active'),
('mcp_inno_competitor', 'Competitor Analysis Agent', 'analyzer', 'Competitive intelligence gathering', ARRAY['competitive_intelligence', 'analysis'], 'inno', 'active'),
('mcp_inno_ideagen', 'Idea Generator Agent', 'specialist', 'AI-powered idea generation', ARRAY['innovation', 'creativity', 'ideation'], 'inno', 'active'),
('mcp_inno_feasibility', 'Feasibility Scorer Agent', 'specialist', 'Innovation feasibility assessment', ARRAY['feasibility', 'scoring', 'evaluation'], 'inno', 'active'),

-- Creative agents
('mcp_creative_script', 'Script Generation Agent', 'specialist', 'Creative script writing', ARRAY['scriptwriting', 'content'], 'creative', 'active'),
('mcp_creative_visual', 'Visual Style Agent', 'specialist', 'Visual design and style recommendations', ARRAY['design', 'visuals', 'branding'], 'creative', 'active'),
('mcp_creative_music', 'Music Composer Agent', 'specialist', 'Music composition suggestions', ARRAY['music', 'audio', 'composition'], 'creative', 'active'),
('mcp_creative_engagement', 'Engagement Optimizer Agent', 'analyzer', 'Content engagement optimization', ARRAY['optimization', 'engagement', 'analytics'], 'creative', 'active'),

-- Edu agents
('mcp_edu_profiler', 'Learner Profiler Agent', 'analyzer', 'Learner skill profiling', ARRAY['profiling', 'assessment', 'education'], 'edu', 'active'),
('mcp_edu_curriculum', 'Curriculum Agent', 'specialist', 'Adaptive curriculum design', ARRAY['curriculum', 'learning_paths', 'education'], 'edu', 'active'),
('mcp_edu_content', 'Content Recommendation Agent', 'curator', 'Educational content curation', ARRAY['content', 'recommendation', 'education'], 'edu', 'active'),
('mcp_edu_feedback', 'Feedback Loop Agent', 'analyzer', 'Learning feedback and adaptation', ARRAY['feedback', 'adaptation', 'personalization'], 'edu', 'active'),
('mcp_edu_benchmark', 'Benchmark Agent', 'analyzer', 'Progress benchmarking and comparison', ARRAY['benchmarking', 'analytics', 'progress'], 'edu', 'active')
ON CONFLICT (agent_id) DO NOTHING;

-- ============================================================================
-- MCP-SPECIFIC TABLES (Integrated with learning ecosystem)
-- ============================================================================

-- MCP Tasks (extends learning_logs with MCP-specific task tracking)
CREATE TABLE IF NOT EXISTS mcp_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id VARCHAR(200) UNIQUE NOT NULL,
    mcp_system VARCHAR(50) NOT NULL,
    agent_id VARCHAR(100) REFERENCES agent_profile(agent_id),
    task_type VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    input_data JSONB,
    output_data JSONB,
    related_material_id UUID REFERENCES learning_materials(id),
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_mcp_tasks_system ON mcp_tasks(mcp_system);
CREATE INDEX idx_mcp_tasks_agent ON mcp_tasks(agent_id);
CREATE INDEX idx_mcp_tasks_status ON mcp_tasks(status);
CREATE INDEX idx_mcp_tasks_material ON mcp_tasks(related_material_id);

-- MCP Workflows (PydiniRed)
CREATE TABLE IF NOT EXISTS mcp_pydini_workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id VARCHAR(200) UNIQUE NOT NULL,
    task_id UUID REFERENCES mcp_tasks(id),
    platform VARCHAR(50) NOT NULL,
    name VARCHAR(300),
    workflow_json JSONB NOT NULL,
    workflow_ir JSONB,
    generated_script TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    logs TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Financial Analysis Results (FinPsy)
CREATE TABLE IF NOT EXISTS mcp_finpsy_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES mcp_tasks(id),
    ticker VARCHAR(20),
    analysis_type VARCHAR(100),
    decision VARCHAR(20) CHECK (decision IN ('BUY', 'SELL', 'HOLD')),
    confidence DECIMAL(3,2),
    momentum_score DECIMAL(5,4),
    sentiment_score DECIMAL(5,4),
    volatility_score DECIMAL(5,4),
    reasoning TEXT,
    forecast_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Legal Analysis Results (Lex)
CREATE TABLE IF NOT EXISTS mcp_lex_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES mcp_tasks(id),
    document_text TEXT,
    document_type VARCHAR(100),
    extracted_clauses TEXT[],
    risk_flags TEXT[],
    risk_score INTEGER CHECK (risk_score BETWEEN 0 AND 100),
    mitigation_plan TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Innovation Ideas (Inno)
CREATE TABLE IF NOT EXISTS mcp_inno_ideas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES mcp_tasks(id),
    idea_title VARCHAR(500),
    description TEXT,
    category VARCHAR(100),
    feasibility_score DECIMAL(3,2),
    innovation_score DECIMAL(3,2),
    market_trends TEXT[],
    patents_reviewed TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Creative Content (Creative)
CREATE TABLE IF NOT EXISTS mcp_creative_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES mcp_tasks(id),
    content_type VARCHAR(100),
    generated_script TEXT,
    visual_styles TEXT[],
    music_suggestions TEXT[],
    engagement_score DECIMAL(3,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Learning Paths (Edu)
CREATE TABLE IF NOT EXISTS mcp_edu_learning_paths (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES mcp_tasks(id),
    learner_profile JSONB,
    recommended_path TEXT[],
    content_recommendations TEXT[],
    estimated_duration_hours INTEGER,
    difficulty VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INTEGRATION VIEWS
-- ============================================================================

-- Unified agent view combining original and MCP agents
CREATE OR REPLACE VIEW v_all_agents AS
SELECT
    agent_id,
    agent_name,
    agent_type,
    description,
    specialization,
    status,
    performance_score,
    total_tasks_completed,
    COALESCE(mcp_system, 'learning_core') as system,
    created_at
FROM agent_profile
ORDER BY mcp_system NULLS FIRST, agent_name;

-- Unified task view combining learning logs and MCP tasks
CREATE OR REPLACE VIEW v_all_tasks AS
SELECT
    ll.id,
    ll.material_id,
    ll.agent_id,
    ll.action as task_type,
    'learning_core' as system,
    'completed' as status,
    ll.created_at
FROM learning_logs ll
UNION ALL
SELECT
    mt.id,
    mt.related_material_id as material_id,
    mt.agent_id,
    mt.task_type,
    mt.mcp_system as system,
    mt.status,
    mt.created_at
FROM mcp_tasks mt
ORDER BY created_at DESC;

-- MCP system activity summary
CREATE OR REPLACE VIEW v_mcp_activity_summary AS
SELECT
    mcp_system,
    COUNT(*) as total_tasks,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_tasks,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_tasks,
    COUNT(*) FILTER (WHERE status = 'running') as running_tasks,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds
FROM mcp_tasks
GROUP BY mcp_system;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Update timestamp trigger for MCP tasks
CREATE TRIGGER update_mcp_tasks_timestamp BEFORE UPDATE ON mcp_tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-create task log when MCP task completes
CREATE OR REPLACE FUNCTION log_mcp_task_completion()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        IF NEW.related_material_id IS NOT NULL THEN
            INSERT INTO learning_logs (material_id, agent_id, action, notes)
            VALUES (
                NEW.related_material_id,
                NEW.agent_id,
                CONCAT('mcp_', NEW.mcp_system, '_', NEW.task_type),
                jsonb_build_object(
                    'task_id', NEW.task_id,
                    'duration_seconds', EXTRACT(EPOCH FROM (NEW.completed_at - NEW.started_at)),
                    'mcp_system', NEW.mcp_system
                )
            );
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER mcp_task_completion_log AFTER UPDATE ON mcp_tasks
    FOR EACH ROW EXECUTE FUNCTION log_mcp_task_completion();

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to create MCP task and link to learning material
CREATE OR REPLACE FUNCTION create_mcp_task(
    p_mcp_system VARCHAR,
    p_task_type VARCHAR,
    p_agent_id VARCHAR,
    p_input_data JSONB,
    p_material_id UUID DEFAULT NULL,
    p_priority INTEGER DEFAULT 5
) RETURNS UUID AS $$
DECLARE
    v_task_id UUID;
    v_generated_task_id VARCHAR;
BEGIN
    v_generated_task_id := CONCAT(p_mcp_system, '_', p_task_type, '_', gen_random_uuid());

    INSERT INTO mcp_tasks (
        task_id, mcp_system, agent_id, task_type,
        input_data, related_material_id, priority, status
    ) VALUES (
        v_generated_task_id, p_mcp_system, p_agent_id, p_task_type,
        p_input_data, p_material_id, p_priority, 'pending'
    ) RETURNING id INTO v_task_id;

    RETURN v_task_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get MCP system statistics
CREATE OR REPLACE FUNCTION get_mcp_stats(p_mcp_system VARCHAR DEFAULT NULL)
RETURNS TABLE (
    mcp_system VARCHAR,
    total_tasks BIGINT,
    completed_tasks BIGINT,
    failed_tasks BIGINT,
    avg_duration_seconds NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        mt.mcp_system,
        COUNT(*)::BIGINT,
        COUNT(*) FILTER (WHERE mt.status = 'completed')::BIGINT,
        COUNT(*) FILTER (WHERE mt.status = 'failed')::BIGINT,
        AVG(EXTRACT(EPOCH FROM (mt.completed_at - mt.started_at)))
    FROM mcp_tasks mt
    WHERE p_mcp_system IS NULL OR mt.mcp_system = p_mcp_system
    GROUP BY mt.mcp_system;
END;
$$ LANGUAGE plpgsql;

RAISE NOTICE 'MCP Extensions integrated successfully with Multi-Agent Learning Ecosystem';
