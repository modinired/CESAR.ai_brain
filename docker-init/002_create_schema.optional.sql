-- Multi-Agent Learning Ecosystem Database Schema
-- Comprehensive schema for managing learning sources, agents, knowledge graphs, and workflows

-- ============================================================================
-- LEARNING SOURCES & MATERIALS
-- ============================================================================

-- Master table of all learning sources
CREATE TABLE IF NOT EXISTS learning_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT NOT NULL UNIQUE,
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN ('article', 'video', 'course', 'paper', 'book', 'podcast', 'financial_data', 'research')),
    category VARCHAR(100),
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    fetch_status VARCHAR(20) DEFAULT 'pending' CHECK (fetch_status IN ('pending', 'fetched', 'failed', 'archived')),
    last_fetched TIMESTAMPTZ,
    fetch_error TEXT,
    retry_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_learning_sources_status ON learning_sources(fetch_status);
CREATE INDEX idx_learning_sources_type ON learning_sources(source_type);
CREATE INDEX idx_learning_sources_priority ON learning_sources(priority DESC);
CREATE INDEX idx_learning_sources_metadata ON learning_sources USING GIN(metadata);

-- Processed learning materials with embeddings
CREATE TABLE IF NOT EXISTS learning_materials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID REFERENCES learning_sources(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    content TEXT NOT NULL,
    content_hash TEXT GENERATED ALWAYS AS (md5(content)) STORED,
    summary TEXT,
    vector vector(3072), -- OpenAI text-embedding-3-large dimension
    processed BOOLEAN DEFAULT FALSE,
    quality_score DECIMAL(3,2) DEFAULT 0.0 CHECK (quality_score BETWEEN 0 AND 1),
    relevance_score DECIMAL(3,2) DEFAULT 0.0 CHECK (relevance_score BETWEEN 0 AND 1),
    tags TEXT[] DEFAULT '{}',
    language VARCHAR(10) DEFAULT 'en',
    word_count INTEGER,
    metadata JSONB DEFAULT '{}',
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_learning_materials_source ON learning_materials(source_id);
CREATE INDEX idx_learning_materials_processed ON learning_materials(processed);
CREATE INDEX idx_learning_materials_quality ON learning_materials(quality_score DESC);
CREATE INDEX idx_learning_materials_tags ON learning_materials USING GIN(tags);
CREATE INDEX idx_learning_materials_content_hash ON learning_materials(content_hash);
-- Vector similarity search index
CREATE INDEX idx_learning_materials_vector ON learning_materials USING ivfflat (vector vector_cosine_ops) WITH (lists = 100);

-- Learning activity logs
CREATE TABLE IF NOT EXISTS learning_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    material_id UUID REFERENCES learning_materials(id) ON DELETE CASCADE,
    agent_id VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL CHECK (action IN ('fetched', 'processed', 'analyzed', 'reflected', 'reviewed', 'archived', 'failed')),
    status VARCHAR(20) DEFAULT 'success' CHECK (status IN ('success', 'warning', 'error')),
    notes JSONB DEFAULT '{}',
    duration_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_learning_logs_material ON learning_logs(material_id);
CREATE INDEX idx_learning_logs_agent ON learning_logs(agent_id);
CREATE INDEX idx_learning_logs_action ON learning_logs(action);
CREATE INDEX idx_learning_logs_created ON learning_logs(created_at DESC);

-- Learning progress tracking per agent
CREATE TABLE IF NOT EXISTS learning_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(100) NOT NULL,
    material_id UUID REFERENCES learning_materials(id) ON DELETE CASCADE,
    progress_percentage DECIMAL(5,2) DEFAULT 0.0 CHECK (progress_percentage BETWEEN 0 AND 100),
    status VARCHAR(20) DEFAULT 'not_started' CHECK (status IN ('not_started', 'in_progress', 'completed', 'reviewing', 'mastered')),
    time_spent_seconds INTEGER DEFAULT 0,
    last_accessed TIMESTAMPTZ,
    completion_date TIMESTAMPTZ,
    notes JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(agent_id, material_id)
);

CREATE INDEX idx_learning_progress_agent ON learning_progress(agent_id);
CREATE INDEX idx_learning_progress_status ON learning_progress(status);
CREATE INDEX idx_learning_progress_completion ON learning_progress(completion_date DESC);

-- Agent reflections on learning materials
CREATE TABLE IF NOT EXISTS learning_reflections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    material_id UUID REFERENCES learning_materials(id) ON DELETE CASCADE,
    agent_id VARCHAR(100) NOT NULL,
    reflection_text TEXT NOT NULL,
    reflection_type VARCHAR(50) DEFAULT 'general' CHECK (reflection_type IN ('general', 'critical', 'application', 'synthesis', 'evaluation')),
    reflection_score DECIMAL(3,2) DEFAULT 0.0 CHECK (reflection_score BETWEEN 0 AND 1),
    key_insights TEXT[],
    questions_raised TEXT[],
    action_items TEXT[],
    vector vector(3072),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_learning_reflections_material ON learning_reflections(material_id);
CREATE INDEX idx_learning_reflections_agent ON learning_reflections(agent_id);
CREATE INDEX idx_learning_reflections_type ON learning_reflections(reflection_type);
CREATE INDEX idx_learning_reflections_score ON learning_reflections(reflection_score DESC);
CREATE INDEX idx_learning_reflections_vector ON learning_reflections USING ivfflat (vector vector_cosine_ops) WITH (lists = 100);

-- Daily agent summary reports
CREATE TABLE IF NOT EXISTS daily_agent_summary (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(100) NOT NULL,
    summary_date DATE NOT NULL DEFAULT CURRENT_DATE,
    materials_processed INTEGER DEFAULT 0,
    reflections_created INTEGER DEFAULT 0,
    skills_improved INTEGER DEFAULT 0,
    total_learning_time_seconds INTEGER DEFAULT 0,
    key_learnings TEXT[],
    challenges_faced TEXT[],
    performance_metrics JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(agent_id, summary_date)
);

CREATE INDEX idx_daily_summary_agent ON daily_agent_summary(agent_id);
CREATE INDEX idx_daily_summary_date ON daily_agent_summary(summary_date DESC);

-- ============================================================================
-- MULTI-AGENT SKILLS & PROFILES
-- ============================================================================

-- Agent profiles
CREATE TABLE IF NOT EXISTS agent_profile (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(100) NOT NULL UNIQUE,
    agent_name VARCHAR(200) NOT NULL,
    agent_type VARCHAR(50) CHECK (agent_type IN ('scraper', 'analyzer', 'curator', 'reflector', 'coordinator', 'specialist')),
    description TEXT,
    specialization TEXT[],
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'maintenance', 'retired')),
    performance_score DECIMAL(3,2) DEFAULT 0.5 CHECK (performance_score BETWEEN 0 AND 1),
    total_tasks_completed INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0.0,
    configuration JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agent_profile_type ON agent_profile(agent_type);
CREATE INDEX idx_agent_profile_status ON agent_profile(status);
CREATE INDEX idx_agent_profile_performance ON agent_profile(performance_score DESC);

-- Agent skills tracking
CREATE TABLE IF NOT EXISTS agent_skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(100) NOT NULL REFERENCES agent_profile(agent_id) ON DELETE CASCADE,
    skill_name VARCHAR(200) NOT NULL,
    skill_category VARCHAR(100),
    skill_level DECIMAL(3,2) DEFAULT 0.0 CHECK (skill_level BETWEEN 0 AND 1),
    proficiency VARCHAR(20) DEFAULT 'beginner' CHECK (proficiency IN ('beginner', 'intermediate', 'advanced', 'expert', 'master')),
    practice_count INTEGER DEFAULT 0,
    last_practiced TIMESTAMPTZ,
    acquired_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    UNIQUE(agent_id, skill_name)
);

CREATE INDEX idx_agent_skills_agent ON agent_skills(agent_id);
CREATE INDEX idx_agent_skills_category ON agent_skills(skill_category);
CREATE INDEX idx_agent_skills_level ON agent_skills(skill_level DESC);

-- Agent task history
CREATE TABLE IF NOT EXISTS agent_task_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(100) NOT NULL REFERENCES agent_profile(agent_id) ON DELETE CASCADE,
    task_type VARCHAR(100) NOT NULL,
    task_description TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled')),
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    result JSONB,
    error_message TEXT,
    duration_seconds INTEGER,
    resources_used JSONB DEFAULT '{}',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_task_history_agent ON agent_task_history(agent_id);
CREATE INDEX idx_task_history_status ON agent_task_history(status);
CREATE INDEX idx_task_history_type ON agent_task_history(task_type);
CREATE INDEX idx_task_history_created ON agent_task_history(created_at DESC);

-- Agent feedback and ratings
CREATE TABLE IF NOT EXISTS agent_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(100) NOT NULL REFERENCES agent_profile(agent_id) ON DELETE CASCADE,
    task_id UUID REFERENCES agent_task_history(id) ON DELETE SET NULL,
    feedback_type VARCHAR(50) CHECK (feedback_type IN ('performance', 'quality', 'efficiency', 'accuracy', 'collaboration')),
    rating DECIMAL(3,2) CHECK (rating BETWEEN 0 AND 5),
    feedback_text TEXT,
    provided_by VARCHAR(100),
    actionable_items TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agent_feedback_agent ON agent_feedback(agent_id);
CREATE INDEX idx_agent_feedback_type ON agent_feedback(feedback_type);
CREATE INDEX idx_agent_feedback_rating ON agent_feedback(rating DESC);

-- Inter-agent interactions and collaborations
CREATE TABLE IF NOT EXISTS agent_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    initiator_agent_id VARCHAR(100) NOT NULL REFERENCES agent_profile(agent_id) ON DELETE CASCADE,
    responder_agent_id VARCHAR(100) NOT NULL REFERENCES agent_profile(agent_id) ON DELETE CASCADE,
    interaction_type VARCHAR(50) CHECK (interaction_type IN ('request', 'response', 'collaboration', 'delegation', 'consultation', 'feedback')),
    context TEXT,
    payload JSONB,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'acknowledged', 'completed', 'rejected')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE INDEX idx_interactions_initiator ON agent_interactions(initiator_agent_id);
CREATE INDEX idx_interactions_responder ON agent_interactions(responder_agent_id);
CREATE INDEX idx_interactions_type ON agent_interactions(interaction_type);
CREATE INDEX idx_interactions_status ON agent_interactions(status);

-- ============================================================================
-- KNOWLEDGE GRAPH
-- ============================================================================

-- Concepts extracted from learning materials
CREATE TABLE IF NOT EXISTS concepts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    concept_name VARCHAR(300) NOT NULL UNIQUE,
    concept_type VARCHAR(100),
    definition TEXT,
    importance_score DECIMAL(3,2) DEFAULT 0.5 CHECK (importance_score BETWEEN 0 AND 1),
    mention_count INTEGER DEFAULT 1,
    related_materials UUID[] DEFAULT '{}',
    vector vector(3072),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_concepts_name ON concepts(concept_name);
CREATE INDEX idx_concepts_type ON concepts(concept_type);
CREATE INDEX idx_concepts_importance ON concepts(importance_score DESC);
CREATE INDEX idx_concepts_vector ON concepts USING ivfflat (vector vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_concepts_metadata ON concepts USING GIN(metadata);

-- Relationships between concepts
CREATE TABLE IF NOT EXISTS concept_relations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    target_concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    relation_type VARCHAR(100) NOT NULL CHECK (relation_type IN ('is_a', 'part_of', 'related_to', 'prerequisite', 'equivalent', 'contradicts', 'applies_to', 'example_of')),
    strength DECIMAL(3,2) DEFAULT 0.5 CHECK (strength BETWEEN 0 AND 1),
    evidence TEXT[],
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source_concept_id, target_concept_id, relation_type)
);

CREATE INDEX idx_concept_relations_source ON concept_relations(source_concept_id);
CREATE INDEX idx_concept_relations_target ON concept_relations(target_concept_id);
CREATE INDEX idx_concept_relations_type ON concept_relations(relation_type);
CREATE INDEX idx_concept_relations_strength ON concept_relations(strength DESC);

-- ============================================================================
-- WORKFLOW METRICS & MONITORING
-- ============================================================================

-- Workflow execution metrics
CREATE TABLE IF NOT EXISTS workflow_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_name VARCHAR(200) NOT NULL,
    workflow_run_id VARCHAR(200),
    agent_id VARCHAR(100),
    status VARCHAR(20) CHECK (status IN ('started', 'running', 'completed', 'failed', 'timeout')),
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    duration_seconds INTEGER,
    tasks_total INTEGER DEFAULT 0,
    tasks_completed INTEGER DEFAULT 0,
    tasks_failed INTEGER DEFAULT 0,
    resources_used JSONB DEFAULT '{}',
    error_log TEXT[],
    performance_metrics JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_workflow_metrics_name ON workflow_metrics(workflow_name);
CREATE INDEX idx_workflow_metrics_status ON workflow_metrics(status);
CREATE INDEX idx_workflow_metrics_start ON workflow_metrics(start_time DESC);
CREATE INDEX idx_workflow_metrics_agent ON workflow_metrics(agent_id);

-- ============================================================================
-- TRIGGERS FOR AUTO-UPDATES
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to relevant tables
CREATE TRIGGER update_learning_sources_updated_at BEFORE UPDATE ON learning_sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_learning_materials_updated_at BEFORE UPDATE ON learning_materials
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_learning_progress_updated_at BEFORE UPDATE ON learning_progress
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_learning_reflections_updated_at BEFORE UPDATE ON learning_reflections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_profile_updated_at BEFORE UPDATE ON agent_profile
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_concepts_updated_at BEFORE UPDATE ON concepts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_concept_relations_updated_at BEFORE UPDATE ON concept_relations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View for agent performance overview
CREATE OR REPLACE VIEW agent_performance_overview AS
SELECT
    ap.agent_id,
    ap.agent_name,
    ap.agent_type,
    ap.status,
    ap.performance_score,
    ap.total_tasks_completed,
    ap.success_rate,
    COUNT(DISTINCT as2.id) as skill_count,
    AVG(as2.skill_level) as avg_skill_level,
    COUNT(DISTINCT lp.material_id) as materials_studied,
    COUNT(DISTINCT lr.id) as reflections_created
FROM agent_profile ap
LEFT JOIN agent_skills as2 ON ap.agent_id = as2.agent_id
LEFT JOIN learning_progress lp ON ap.agent_id = lp.agent_id
LEFT JOIN learning_reflections lr ON ap.agent_id = lr.agent_id
GROUP BY ap.agent_id, ap.agent_name, ap.agent_type, ap.status,
         ap.performance_score, ap.total_tasks_completed, ap.success_rate;

-- View for material quality metrics
CREATE OR REPLACE VIEW material_quality_metrics AS
SELECT
    lm.id,
    lm.title,
    lm.quality_score,
    lm.relevance_score,
    lm.processed,
    COUNT(DISTINCT lr.id) as reflection_count,
    AVG(lr.reflection_score) as avg_reflection_score,
    COUNT(DISTINCT lp.agent_id) as agents_studying
FROM learning_materials lm
LEFT JOIN learning_reflections lr ON lm.id = lr.material_id
LEFT JOIN learning_progress lp ON lm.id = lp.material_id
GROUP BY lm.id, lm.title, lm.quality_score, lm.relevance_score, lm.processed;

-- View for workflow status
CREATE OR REPLACE VIEW workflow_status_summary AS
SELECT
    workflow_name,
    COUNT(*) as total_runs,
    COUNT(*) FILTER (WHERE status = 'completed') as successful_runs,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_runs,
    AVG(duration_seconds) as avg_duration_seconds,
    MAX(start_time) as last_run_time
FROM workflow_metrics
GROUP BY workflow_name;

-- ============================================================================
-- SEED DATA FOR TESTING
-- ============================================================================

-- Insert default agent profiles
INSERT INTO agent_profile (agent_id, agent_name, agent_type, description, specialization) VALUES
('agent_main', 'Main Coordinator Agent', 'coordinator', 'Primary coordinator for all learning workflows', ARRAY['orchestration', 'coordination', 'monitoring']),
('agent_scraper_finance', 'Financial Data Scraper', 'scraper', 'Specializes in scraping financial data sources', ARRAY['finance', 'data_extraction', 'market_analysis']),
('agent_scraper_education', 'Educational Content Scraper', 'scraper', 'Collects educational materials and courses', ARRAY['education', 'content_curation', 'learning_materials']),
('agent_scraper_research', 'Research Paper Scraper', 'scraper', 'Fetches academic papers and research articles', ARRAY['research', 'academia', 'scholarly_articles']),
('agent_analyzer', 'Content Analyzer', 'analyzer', 'Analyzes and processes learning materials', ARRAY['nlp', 'content_analysis', 'quality_assessment']),
('agent_reflector', 'Reflection Generator', 'reflector', 'Generates insights and reflections on materials', ARRAY['critical_thinking', 'synthesis', 'insight_generation'])
ON CONFLICT (agent_id) DO NOTHING;

-- Insert sample learning sources
INSERT INTO learning_sources (url, source_type, category, priority) VALUES
('https://arxiv.org/list/cs.AI/recent', 'research', 'AI Research', 9),
('https://www.coursera.org/browse/data-science', 'course', 'Data Science', 8),
('https://finance.yahoo.com/quote/AAPL', 'financial_data', 'Stock Market', 7),
('https://www.becker.com/cpa-review', 'course', 'Accounting', 8)
ON CONFLICT (url) DO NOTHING;

RAISE NOTICE 'Database schema created successfully with all tables, indexes, triggers, and views';
