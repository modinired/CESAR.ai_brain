-- Migration 012: Knowledge Enhancement System
-- Best-in-class connections, historical data, psychology/NLP, daily learnings
-- Created: November 21, 2025

-- ============================================================================
-- KNOWLEDGE DOMAIN TAXONOMY
-- ============================================================================

CREATE TABLE IF NOT EXISTS knowledge_domains (
    domain_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    category TEXT NOT NULL,  -- 'psychology', 'nlp', 'finance', 'technology', 'business', etc.
    description TEXT,
    parent_domain_id UUID REFERENCES knowledge_domains(domain_id),
    depth INT DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_knowledge_domains_category ON knowledge_domains(category);
CREATE INDEX idx_knowledge_domains_parent ON knowledge_domains(parent_domain_id);

-- ============================================================================
-- SKILLS & COMPETENCIES GRAPH
-- ============================================================================

CREATE TABLE IF NOT EXISTS skills (
    skill_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    domain_id UUID REFERENCES knowledge_domains(domain_id),
    skill_type TEXT NOT NULL,  -- 'technical', 'cognitive', 'interpersonal', 'domain_knowledge'
    proficiency_levels JSONB DEFAULT '["beginner", "intermediate", "advanced", "expert"]',
    prerequisites JSONB DEFAULT '[]',  -- Array of skill_ids
    learning_resources JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_skills_domain ON skills(domain_id);
CREATE INDEX idx_skills_type ON skills(skill_type);

-- Skill relationships and dependencies
CREATE TABLE IF NOT EXISTS skill_connections (
    connection_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_skill_id UUID REFERENCES skills(skill_id),
    to_skill_id UUID REFERENCES skills(skill_id),
    connection_type TEXT NOT NULL,  -- 'prerequisite', 'complementary', 'alternative', 'synergistic'
    strength DECIMAL(3,2) DEFAULT 0.5,  -- 0.0 to 1.0
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(from_skill_id, to_skill_id, connection_type)
);

CREATE INDEX idx_skill_connections_from ON skill_connections(from_skill_id);
CREATE INDEX idx_skill_connections_to ON skill_connections(to_skill_id);
CREATE INDEX idx_skill_connections_type ON skill_connections(connection_type);

-- ============================================================================
-- HISTORICAL LEARNING DATA
-- ============================================================================

CREATE TABLE IF NOT EXISTS learning_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id TEXT,
    user_id TEXT,
    skill_id UUID REFERENCES skills(skill_id),
    domain_id UUID REFERENCES knowledge_domains(domain_id),
    activity_type TEXT NOT NULL,  -- 'study', 'practice', 'reflection', 'application', 'teaching'
    content_type TEXT,  -- 'article', 'book', 'video', 'course', 'project', 'conversation'
    duration_minutes INT,
    proficiency_before DECIMAL(3,2),
    proficiency_after DECIMAL(3,2),
    insights_gained JSONB DEFAULT '[]',
    challenges_faced JSONB DEFAULT '[]',
    connections_made JSONB DEFAULT '[]',  -- Links to other skills/domains discovered
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_learning_history_agent ON learning_history(agent_id);
CREATE INDEX idx_learning_history_skill ON learning_history(skill_id);
CREATE INDEX idx_learning_history_domain ON learning_history(domain_id);
CREATE INDEX idx_learning_history_timestamp ON learning_history(timestamp DESC);

-- Time-series aggregation for trends
CREATE TABLE IF NOT EXISTS learning_trends (
    trend_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregation_period TEXT NOT NULL,  -- 'daily', 'weekly', 'monthly'
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    agent_id TEXT,
    skill_id UUID REFERENCES skills(skill_id),
    domain_id UUID REFERENCES knowledge_domains(domain_id),
    total_activities INT DEFAULT 0,
    total_duration_minutes INT DEFAULT 0,
    avg_proficiency_gain DECIMAL(5,2),
    top_insights JSONB DEFAULT '[]',
    trend_direction TEXT,  -- 'improving', 'stable', 'declining'
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(aggregation_period, period_start, agent_id, skill_id)
);

CREATE INDEX idx_learning_trends_period ON learning_trends(period_start DESC);
CREATE INDEX idx_learning_trends_agent ON learning_trends(agent_id);
CREATE INDEX idx_learning_trends_skill ON learning_trends(skill_id);

-- ============================================================================
-- PSYCHOLOGY & NLP KNOWLEDGE BASE
-- ============================================================================

CREATE TABLE IF NOT EXISTS psychological_concepts (
    concept_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,  -- 'cognitive', 'behavioral', 'developmental', 'social', 'clinical'
    theory_origin TEXT,
    key_researchers JSONB DEFAULT '[]',
    description TEXT,
    applications JSONB DEFAULT '[]',
    related_concepts JSONB DEFAULT '[]',
    evidence_strength TEXT,  -- 'strong', 'moderate', 'emerging', 'controversial'
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_psychological_concepts_category ON psychological_concepts(category);

CREATE TABLE IF NOT EXISTS nlp_techniques (
    technique_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,  -- 'tokenization', 'embedding', 'attention', 'generation', etc.
    approach TEXT,  -- 'statistical', 'neural', 'symbolic', 'hybrid'
    use_cases JSONB DEFAULT '[]',
    strengths JSONB DEFAULT '[]',
    limitations JSONB DEFAULT '[]',
    best_practices JSONB DEFAULT '[]',
    code_examples JSONB DEFAULT '[]',
    related_techniques JSONB DEFAULT '[]',
    sota_performance JSONB DEFAULT '{}',  -- State of the art benchmarks
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_nlp_techniques_category ON nlp_techniques(category);
CREATE INDEX idx_nlp_techniques_approach ON nlp_techniques(approach);

-- Cross-domain connections between psychology and NLP
CREATE TABLE IF NOT EXISTS psychology_nlp_bridges (
    bridge_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    psychological_concept_id UUID REFERENCES psychological_concepts(concept_id),
    nlp_technique_id UUID REFERENCES nlp_techniques(technique_id),
    connection_type TEXT NOT NULL,  -- 'inspired_by', 'implements', 'models', 'applies_to'
    description TEXT,
    practical_applications JSONB DEFAULT '[]',
    research_papers JSONB DEFAULT '[]',
    strength DECIMAL(3,2) DEFAULT 0.5,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_psych_nlp_bridges_concept ON psychology_nlp_bridges(psychological_concept_id);
CREATE INDEX idx_psych_nlp_bridges_technique ON psychology_nlp_bridges(nlp_technique_id);

-- ============================================================================
-- DAILY KEY ENHANCEMENTS & LEARNINGS
-- ============================================================================

CREATE TABLE IF NOT EXISTS daily_learnings (
    learning_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    agent_id TEXT,
    learning_type TEXT NOT NULL,  -- 'insight', 'skill_improvement', 'connection', 'breakthrough', 'pattern'
    domain_id UUID REFERENCES knowledge_domains(domain_id),
    skill_id UUID REFERENCES skills(skill_id),
    title TEXT NOT NULL,
    description TEXT,
    importance_score DECIMAL(3,2) DEFAULT 0.5,  -- 0.0 to 1.0
    confidence_level DECIMAL(3,2) DEFAULT 0.5,
    source_activities JSONB DEFAULT '[]',  -- References to learning_history entries
    related_learnings JSONB DEFAULT '[]',  -- Links to other daily_learnings
    action_items JSONB DEFAULT '[]',
    impact_areas JSONB DEFAULT '[]',  -- Domains/skills this learning affects
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_daily_learnings_date ON daily_learnings(date DESC);
CREATE INDEX idx_daily_learnings_agent ON daily_learnings(agent_id);
CREATE INDEX idx_daily_learnings_type ON daily_learnings(learning_type);
CREATE INDEX idx_daily_learnings_importance ON daily_learnings(importance_score DESC);

-- Aggregated daily summary
CREATE TABLE IF NOT EXISTS daily_learning_summary (
    summary_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL UNIQUE,
    total_learnings INT DEFAULT 0,
    top_learnings JSONB DEFAULT '[]',  -- Top 5-10 most important learnings
    domains_explored JSONB DEFAULT '[]',
    skills_improved JSONB DEFAULT '[]',
    key_connections_made JSONB DEFAULT '[]',
    breakthrough_moments JSONB DEFAULT '[]',
    challenges_identified JSONB DEFAULT '[]',
    next_focus_areas JSONB DEFAULT '[]',
    overall_progress_score DECIMAL(3,2),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_daily_summary_date ON daily_learning_summary(date DESC);

-- ============================================================================
-- BEST-IN-CLASS CONNECTIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS excellence_patterns (
    pattern_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    category TEXT NOT NULL,  -- 'mental_model', 'workflow', 'technique', 'framework'
    domain_id UUID REFERENCES knowledge_domains(domain_id),
    description TEXT,
    key_principles JSONB DEFAULT '[]',
    implementation_steps JSONB DEFAULT '[]',
    success_factors JSONB DEFAULT '[]',
    common_pitfalls JSONB DEFAULT '[]',
    real_world_examples JSONB DEFAULT '[]',
    measurable_outcomes JSONB DEFAULT '[]',
    required_skills JSONB DEFAULT '[]',  -- References to skill_ids
    effectiveness_rating DECIMAL(3,2),
    evidence_base JSONB DEFAULT '{}',  -- Research, case studies, etc.
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_excellence_patterns_domain ON excellence_patterns(domain_id);
CREATE INDEX idx_excellence_patterns_category ON excellence_patterns(category);
CREATE INDEX idx_excellence_patterns_rating ON excellence_patterns(effectiveness_rating DESC);

-- Cross-domain excellence connections
CREATE TABLE IF NOT EXISTS excellence_synergies (
    synergy_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern1_id UUID REFERENCES excellence_patterns(pattern_id),
    pattern2_id UUID REFERENCES excellence_patterns(pattern_id),
    synergy_type TEXT NOT NULL,  -- 'complementary', 'multiplicative', 'sequential', 'parallel'
    combined_effectiveness DECIMAL(3,2),
    use_cases JSONB DEFAULT '[]',
    implementation_notes TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(pattern1_id, pattern2_id)
);

CREATE INDEX idx_excellence_synergies_pattern1 ON excellence_synergies(pattern1_id);
CREATE INDEX idx_excellence_synergies_pattern2 ON excellence_synergies(pattern2_id);

-- ============================================================================
-- UNCONVENTIONAL INSIGHTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS unconventional_insights (
    insight_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    insight_type TEXT NOT NULL,  -- 'counter_intuitive', 'cross_domain', 'emerging', 'contrarian'
    domain_ids JSONB DEFAULT '[]',  -- Can span multiple domains
    description TEXT,
    conventional_wisdom TEXT,
    why_different TEXT,
    supporting_evidence JSONB DEFAULT '[]',
    practical_applications JSONB DEFAULT '[]',
    adoption_barriers JSONB DEFAULT '[]',
    risk_level TEXT,  -- 'low', 'medium', 'high'
    validation_status TEXT,  -- 'hypothesis', 'testing', 'validated', 'refuted'
    impact_potential DECIMAL(3,2),
    metadata JSONB DEFAULT '{}',
    discovered_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_unconventional_insights_type ON unconventional_insights(insight_type);
CREATE INDEX idx_unconventional_insights_validation ON unconventional_insights(validation_status);
CREATE INDEX idx_unconventional_insights_impact ON unconventional_insights(impact_potential DESC);

-- ============================================================================
-- MATERIALIZED VIEWS FOR FAST QUERIES
-- ============================================================================

-- Top skills by learning activity
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_trending_skills AS
SELECT
    s.skill_id,
    s.name as skill_name,
    s.domain_id,
    kd.name as domain_name,
    COUNT(lh.history_id) as activity_count,
    AVG(lh.proficiency_after - lh.proficiency_before) as avg_growth,
    COUNT(DISTINCT lh.agent_id) as agent_count,
    MAX(lh.timestamp) as last_activity
FROM skills s
LEFT JOIN knowledge_domains kd ON s.domain_id = kd.domain_id
LEFT JOIN learning_history lh ON s.skill_id = lh.skill_id
WHERE lh.timestamp > now() - interval '7 days'
GROUP BY s.skill_id, s.name, s.domain_id, kd.name
ORDER BY activity_count DESC;

-- Daily learning insights summary
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_insights AS
SELECT
    dl.date,
    COUNT(*) as total_insights,
    AVG(dl.importance_score) as avg_importance,
    COUNT(DISTINCT dl.domain_id) as domains_covered,
    COUNT(DISTINCT dl.agent_id) as active_agents,
    STRING_AGG(DISTINCT dl.learning_type, ', ') as learning_types,
    MAX(dl.importance_score) as top_importance
FROM daily_learnings dl
WHERE dl.date > CURRENT_DATE - interval '30 days'
GROUP BY dl.date
ORDER BY dl.date DESC;

-- Best practice patterns ranking
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_top_excellence_patterns AS
SELECT
    ep.pattern_id,
    ep.name,
    ep.category,
    kd.name as domain_name,
    ep.effectiveness_rating,
    COUNT(es1.synergy_id) + COUNT(es2.synergy_id) as synergy_count,
    JSONB_ARRAY_LENGTH(ep.real_world_examples) as example_count
FROM excellence_patterns ep
LEFT JOIN knowledge_domains kd ON ep.domain_id = kd.domain_id
LEFT JOIN excellence_synergies es1 ON ep.pattern_id = es1.pattern1_id
LEFT JOIN excellence_synergies es2 ON ep.pattern_id = es2.pattern2_id
GROUP BY ep.pattern_id, ep.name, ep.category, kd.name, ep.effectiveness_rating
ORDER BY ep.effectiveness_rating DESC, synergy_count DESC;

-- ============================================================================
-- REFRESH FUNCTIONS
-- ============================================================================

-- Daily refresh job (call from job queue)
CREATE OR REPLACE FUNCTION refresh_knowledge_enhancement_views()
RETURNS TEXT AS $$
BEGIN
    REFRESH MATERIALIZED VIEW mv_trending_skills;
    REFRESH MATERIALIZED VIEW mv_daily_insights;
    REFRESH MATERIALIZED VIEW mv_top_excellence_patterns;
    RETURN 'Knowledge enhancement views refreshed: ' || now()::TEXT;
END;
$$ LANGUAGE plpgsql;

-- Generate daily learning summary
CREATE OR REPLACE FUNCTION generate_daily_learning_summary(summary_date DATE DEFAULT CURRENT_DATE)
RETURNS UUID AS $$
DECLARE
    v_summary_id UUID;
    v_learnings JSONB;
    v_domains JSONB;
    v_skills JSONB;
BEGIN
    -- Aggregate top learnings
    SELECT JSONB_AGG(
        JSONB_BUILD_OBJECT(
            'title', title,
            'type', learning_type,
            'importance', importance_score,
            'description', description
        )
        ORDER BY importance_score DESC
    )
    INTO v_learnings
    FROM (
        SELECT * FROM daily_learnings
        WHERE date = summary_date
        ORDER BY importance_score DESC
        LIMIT 10
    ) top_learnings;

    -- Get domains explored
    SELECT JSONB_AGG(DISTINCT JSONB_BUILD_OBJECT('domain_id', domain_id, 'name', kd.name))
    INTO v_domains
    FROM daily_learnings dl
    JOIN knowledge_domains kd ON dl.domain_id = kd.domain_id
    WHERE dl.date = summary_date;

    -- Get skills improved
    SELECT JSONB_AGG(DISTINCT JSONB_BUILD_OBJECT('skill_id', skill_id, 'name', s.name))
    INTO v_skills
    FROM daily_learnings dl
    JOIN skills s ON dl.skill_id = s.skill_id
    WHERE dl.date = summary_date;

    -- Insert or update summary
    INSERT INTO daily_learning_summary (
        date,
        total_learnings,
        top_learnings,
        domains_explored,
        skills_improved,
        overall_progress_score
    )
    VALUES (
        summary_date,
        (SELECT COUNT(*) FROM daily_learnings WHERE date = summary_date),
        COALESCE(v_learnings, '[]'::JSONB),
        COALESCE(v_domains, '[]'::JSONB),
        COALESCE(v_skills, '[]'::JSONB),
        (SELECT AVG(importance_score) FROM daily_learnings WHERE date = summary_date)
    )
    ON CONFLICT (date) DO UPDATE SET
        total_learnings = EXCLUDED.total_learnings,
        top_learnings = EXCLUDED.top_learnings,
        domains_explored = EXCLUDED.domains_explored,
        skills_improved = EXCLUDED.skills_improved,
        overall_progress_score = EXCLUDED.overall_progress_score,
        updated_at = now()
    RETURNING summary_id INTO v_summary_id;

    RETURN v_summary_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TTL POLICIES
-- ============================================================================

-- Keep detailed learning history for 1 year, aggregate older data
-- (Implement via job queue worker periodic cleanup)

COMMENT ON TABLE knowledge_domains IS 'Hierarchical taxonomy of knowledge areas';
COMMENT ON TABLE skills IS 'Skills and competencies with relationships';
COMMENT ON TABLE learning_history IS 'Detailed time-series learning activity data';
COMMENT ON TABLE psychological_concepts IS 'Psychology knowledge base for AI understanding of human cognition';
COMMENT ON TABLE nlp_techniques IS 'NLP methods, techniques, and best practices';
COMMENT ON TABLE daily_learnings IS 'Key insights and learnings discovered each day';
COMMENT ON TABLE excellence_patterns IS 'Best-in-class patterns and frameworks';
COMMENT ON TABLE unconventional_insights IS 'Counter-intuitive and cross-domain discoveries';

-- ============================================================================
-- END MIGRATION 012
-- ============================================================================
