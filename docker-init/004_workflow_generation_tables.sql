-- Workflow Generation System Tables
-- Integrates workflow automation and generation capabilities

-- ============================================================================
-- WORKFLOW AUTOMATION TABLES
-- ============================================================================

-- Scraped sources for workflow discovery
CREATE TABLE IF NOT EXISTS scraped_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT NOT NULL UNIQUE,
    source_type VARCHAR(100),
    fetch_status VARCHAR(20) DEFAULT 'pending' CHECK (fetch_status IN ('pending', 'fetched', 'failed', 'archived')),
    last_fetched TIMESTAMPTZ,
    retry_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_scraped_sources_status ON scraped_sources(fetch_status);
CREATE INDEX idx_scraped_sources_url ON scraped_sources(url);

-- Workflow templates
CREATE TABLE IF NOT EXISTS workflow_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(300) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    platform VARCHAR(50),
    template_json JSONB NOT NULL,
    canonical_steps JSONB,
    required_api_keys TEXT[] DEFAULT '{}',
    required_skills TEXT[] DEFAULT '{}',
    complexity_score DECIMAL(3,2) DEFAULT 0.5,
    usage_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_workflow_templates_category ON workflow_templates(category);
CREATE INDEX idx_workflow_templates_platform ON workflow_templates(platform);
CREATE INDEX idx_workflow_templates_usage ON workflow_templates(usage_count DESC);

-- Generated workflows
CREATE TABLE IF NOT EXISTS generated_workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(300) NOT NULL,
    description TEXT,
    source_template_id UUID REFERENCES workflow_templates(id),
    job_id VARCHAR(200),
    canonical_steps JSONB NOT NULL,
    required_api_keys TEXT[] DEFAULT '{}',
    required_skills TEXT[] DEFAULT '{}',
    score DECIMAL(3,2) DEFAULT 0.0,
    metadata JSONB DEFAULT '{}',
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    deployed BOOLEAN DEFAULT FALSE,
    deployment_date TIMESTAMPTZ
);

CREATE INDEX idx_generated_workflows_template ON generated_workflows(source_template_id);
CREATE INDEX idx_generated_workflows_job ON generated_workflows(job_id);
CREATE INDEX idx_generated_workflows_generated ON generated_workflows(generated_at DESC);
CREATE INDEX idx_generated_workflows_deployed ON generated_workflows(deployed);

-- Workflow generation logs
CREATE TABLE IF NOT EXISTS workflow_generation_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    generated_workflow_id UUID REFERENCES generated_workflows(id) ON DELETE CASCADE,
    template_id UUID REFERENCES workflow_templates(id),
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    status VARCHAR(20) CHECK (status IN ('running', 'success', 'failed', 'cancelled')),
    details JSONB DEFAULT '{}',
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_workflow_gen_logs_workflow ON workflow_generation_logs(generated_workflow_id);
CREATE INDEX idx_workflow_gen_logs_status ON workflow_generation_logs(status);
CREATE INDEX idx_workflow_gen_logs_started ON workflow_generation_logs(started_at DESC);

-- ============================================================================
-- INTEGRATION WITH MCP SYSTEMS
-- ============================================================================

-- Link generated workflows to MCP PydiniRed workflows
ALTER TABLE mcp_pydini_workflows
ADD COLUMN IF NOT EXISTS source_template_id UUID REFERENCES workflow_templates(id),
ADD COLUMN IF NOT EXISTS generated_workflow_id UUID REFERENCES generated_workflows(id);

CREATE INDEX IF NOT EXISTS idx_pydini_workflows_template ON mcp_pydini_workflows(source_template_id);
CREATE INDEX IF NOT EXISTS idx_pydini_workflows_generated ON mcp_pydini_workflows(generated_workflow_id);

-- ============================================================================
-- VIEWS FOR WORKFLOW ANALYTICS
-- ============================================================================

-- Workflow generation success rate
CREATE OR REPLACE VIEW v_workflow_generation_stats AS
SELECT
    wt.id as template_id,
    wt.name as template_name,
    COUNT(gw.id) as total_generated,
    COUNT(gw.id) FILTER (WHERE gw.deployed = true) as deployed_count,
    COUNT(wgl.id) FILTER (WHERE wgl.status = 'success') as successful_generations,
    COUNT(wgl.id) FILTER (WHERE wgl.status = 'failed') as failed_generations,
    AVG(EXTRACT(EPOCH FROM (wgl.finished_at - wgl.started_at))) as avg_generation_time_seconds
FROM workflow_templates wt
LEFT JOIN generated_workflows gw ON wt.id = gw.source_template_id
LEFT JOIN workflow_generation_logs wgl ON gw.id = wgl.generated_workflow_id
GROUP BY wt.id, wt.name;

-- Scraped sources summary
CREATE OR REPLACE VIEW v_scraped_sources_summary AS
SELECT
    source_type,
    COUNT(*) as total_sources,
    COUNT(*) FILTER (WHERE fetch_status = 'fetched') as fetched_count,
    COUNT(*) FILTER (WHERE fetch_status = 'failed') as failed_count,
    COUNT(*) FILTER (WHERE fetch_status = 'pending') as pending_count,
    MAX(last_fetched) as last_fetch_time
FROM scraped_sources
GROUP BY source_type;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to auto-create workflow template from generated workflow
CREATE OR REPLACE FUNCTION promote_generated_workflow_to_template(
    p_generated_workflow_id UUID,
    p_template_name VARCHAR DEFAULT NULL,
    p_template_description TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_template_id UUID;
    v_workflow RECORD;
BEGIN
    -- Get generated workflow details
    SELECT * INTO v_workflow
    FROM generated_workflows
    WHERE id = p_generated_workflow_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Generated workflow not found';
    END IF;

    -- Create template
    INSERT INTO workflow_templates (
        name,
        description,
        canonical_steps,
        required_api_keys,
        required_skills,
        complexity_score,
        metadata
    ) VALUES (
        COALESCE(p_template_name, v_workflow.name || ' (Template)'),
        COALESCE(p_template_description, v_workflow.description),
        v_workflow.canonical_steps,
        v_workflow.required_api_keys,
        v_workflow.required_skills,
        v_workflow.score,
        jsonb_build_object(
            'promoted_from', p_generated_workflow_id,
            'original_score', v_workflow.score,
            'promoted_at', NOW()
        )
    ) RETURNING id INTO v_template_id;

    -- Mark generated workflow as deployed
    UPDATE generated_workflows
    SET deployed = true, deployment_date = NOW()
    WHERE id = p_generated_workflow_id;

    RETURN v_template_id;
END;
$$ LANGUAGE plpgsql;

-- Function to sync generated workflow with MCP Pydini system
CREATE OR REPLACE FUNCTION sync_workflow_to_mcp_pydini(
    p_generated_workflow_id UUID,
    p_platform VARCHAR DEFAULT 'auto_generated'
) RETURNS UUID AS $$
DECLARE
    v_workflow RECORD;
    v_mcp_workflow_id UUID;
BEGIN
    -- Get generated workflow
    SELECT * INTO v_workflow
    FROM generated_workflows
    WHERE id = p_generated_workflow_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Generated workflow not found';
    END IF;

    -- Create or update MCP Pydini workflow
    INSERT INTO mcp_pydini_workflows (
        workflow_id,
        platform,
        name,
        workflow_json,
        workflow_ir,
        source_template_id,
        generated_workflow_id,
        status,
        logs
    ) VALUES (
        'pydini_' || gen_random_uuid(),
        p_platform,
        v_workflow.name,
        jsonb_build_object(
            'steps', v_workflow.canonical_steps,
            'metadata', v_workflow.metadata
        ),
        v_workflow.canonical_steps,
        v_workflow.source_template_id,
        p_generated_workflow_id,
        'pending',
        ARRAY['Synced from workflow generation system']
    ) RETURNING id INTO v_mcp_workflow_id;

    RETURN v_mcp_workflow_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update timestamp triggers
CREATE TRIGGER update_scraped_sources_timestamp BEFORE UPDATE ON scraped_sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflow_templates_timestamp BEFORE UPDATE ON workflow_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-increment usage count when workflow is generated from template
CREATE OR REPLACE FUNCTION increment_template_usage()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.source_template_id IS NOT NULL THEN
        UPDATE workflow_templates
        SET usage_count = usage_count + 1
        WHERE id = NEW.source_template_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER increment_template_usage_on_generation
    AFTER INSERT ON generated_workflows
    FOR EACH ROW EXECUTE FUNCTION increment_template_usage();

-- ============================================================================
-- SEED DATA
-- ============================================================================

-- Insert sample workflow templates
INSERT INTO workflow_templates (name, description, category, platform, template_json, canonical_steps) VALUES
('Data Collection Workflow', 'Basic data collection and storage', 'data_collection', 'generic',
 '{"steps": [{"name": "fetch_data", "type": "http_request"}, {"name": "store_data", "type": "database_insert"}]}'::jsonb,
 '[{"name": "fetch_data", "type": "http_request", "params": {}}, {"name": "store_data", "type": "database_insert", "params": {}}]'::jsonb),

('Email Notification Workflow', 'Send email notifications based on triggers', 'notification', 'generic',
 '{"steps": [{"name": "check_condition", "type": "condition"}, {"name": "send_email", "type": "email"}]}'::jsonb,
 '[{"name": "check_condition", "type": "condition", "params": {}}, {"name": "send_email", "type": "email", "params": {}}]'::jsonb),

('Data Transformation Pipeline', 'ETL pipeline for data transformation', 'data_processing', 'generic',
 '{"steps": [{"name": "extract", "type": "data_source"}, {"name": "transform", "type": "processor"}, {"name": "load", "type": "data_sink"}]}'::jsonb,
 '[{"name": "extract", "type": "data_source", "params": {}}, {"name": "transform", "type": "processor", "params": {}}, {"name": "load", "type": "data_sink", "params": {}}]'::jsonb)
ON CONFLICT DO NOTHING;

RAISE NOTICE 'Workflow generation tables created and integrated with MCP systems';
