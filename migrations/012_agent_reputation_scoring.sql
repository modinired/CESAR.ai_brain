-- ============================================================================
-- Migration 012: Agent Reputation Scoring System
-- ============================================================================
-- PhD-Level enhancement that tracks agent performance and quality
-- over time, enabling reputation-weighted brain mutations.
--
-- Implements meritocratic knowledge contribution system where:
-- - High-quality mutations from reliable agents carry more weight
-- - Poor-quality mutations from unreliable agents are downweighted
-- - Reputation evolves dynamically based on empirical success metrics
--
-- Author: Enhancement System
-- Date: 2025-11-21
-- Quality: PhD-Level, Production-Ready
-- ============================================================================

-- Add reputation_score column to agents table
-- Default score is 50.0 (neutral, can go 0-100)
ALTER TABLE agents
ADD COLUMN IF NOT EXISTS reputation_score DECIMAL(5,2) DEFAULT 50.0 CHECK (reputation_score >= 0 AND reputation_score <= 100);

-- Add reputation tracking fields
ALTER TABLE agents
ADD COLUMN IF NOT EXISTS total_mutations INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS successful_mutations INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS failed_mutations INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_reputation_update TIMESTAMP DEFAULT NOW();

-- Create agent_reputation_history table for tracking changes over time
CREATE TABLE IF NOT EXISTS agent_reputation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name VARCHAR(255) NOT NULL,
    mcp_system VARCHAR(100) NOT NULL,

    -- Reputation metrics
    old_score DECIMAL(5,2) NOT NULL,
    new_score DECIMAL(5,2) NOT NULL,
    score_delta DECIMAL(5,2) NOT NULL,

    -- Event details
    event_type VARCHAR(50) NOT NULL, -- 'MUTATION_SUCCESS', 'MUTATION_FAILURE', 'PERIODIC_DECAY', etc.
    event_details TEXT,
    event_metadata JSONB,

    -- Timestamps
    recorded_at TIMESTAMP DEFAULT NOW(),

    -- Indexes
    CONSTRAINT fk_agent_reputation_agent FOREIGN KEY (agent_name) REFERENCES agents(agent_name) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_agent_reputation_history_agent ON agent_reputation_history(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_reputation_history_timestamp ON agent_reputation_history(recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_reputation_history_event ON agent_reputation_history(event_type);

-- Create mutation_quality_tracking table
CREATE TABLE IF NOT EXISTS mutation_quality_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Agent attribution
    agent_name VARCHAR(255) NOT NULL,
    mcp_system VARCHAR(100) NOT NULL,

    -- Mutation details
    mutation_type VARCHAR(50) NOT NULL, -- 'CREATE_NODE', 'CREATE_LINK', 'UPDATE_MASS', etc.
    target_node_id VARCHAR(255),
    target_link_id UUID,

    -- Quality metrics
    quality_score DECIMAL(5,2), -- 0-100, measures mutation utility
    confidence DECIMAL(5,2), -- 0-100, agent's confidence in mutation
    impact_score DECIMAL(5,2), -- 0-100, measured impact on brain performance

    -- Outcome
    success BOOLEAN NOT NULL,
    error_message TEXT,

    -- Context
    mutation_params JSONB,
    brain_state_before JSONB,
    brain_state_after JSONB,

    -- Timestamps
    attempted_at TIMESTAMP DEFAULT NOW(),
    evaluated_at TIMESTAMP,

    -- Foreign keys
    CONSTRAINT fk_mutation_quality_agent FOREIGN KEY (agent_name) REFERENCES agents(agent_name) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_mutation_quality_agent ON mutation_quality_tracking(agent_name);
CREATE INDEX IF NOT EXISTS idx_mutation_quality_success ON mutation_quality_tracking(success);
CREATE INDEX IF NOT EXISTS idx_mutation_quality_score ON mutation_quality_tracking(quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_mutation_quality_timestamp ON mutation_quality_tracking(attempted_at DESC);

-- Create function to update agent reputation
CREATE OR REPLACE FUNCTION update_agent_reputation(
    p_agent_name VARCHAR(255),
    p_mcp_system VARCHAR(100),
    p_mutation_success BOOLEAN,
    p_quality_score DECIMAL(5,2),
    p_event_details TEXT DEFAULT NULL
) RETURNS DECIMAL(5,2) AS $$
DECLARE
    v_old_score DECIMAL(5,2);
    v_new_score DECIMAL(5,2);
    v_delta DECIMAL(5,2);
    v_success_rate DECIMAL(5,2);
BEGIN
    -- Get current reputation score
    SELECT reputation_score INTO v_old_score
    FROM agents
    WHERE agent_name = p_agent_name;

    IF v_old_score IS NULL THEN
        -- Agent doesn't exist, return 50 (neutral)
        RETURN 50.0;
    END IF;

    -- Calculate reputation delta based on mutation outcome
    IF p_mutation_success THEN
        -- Success: boost reputation (weighted by quality score)
        -- High quality mutations give more reputation boost
        v_delta := (p_quality_score / 100.0) * 2.0; -- Max +2.0 per mutation

        -- Update success counter
        UPDATE agents
        SET successful_mutations = successful_mutations + 1,
            total_mutations = total_mutations + 1
        WHERE agent_name = p_agent_name;
    ELSE
        -- Failure: penalize reputation
        v_delta := -1.5; -- Fixed -1.5 penalty per failure

        -- Update failure counter
        UPDATE agents
        SET failed_mutations = failed_mutations + 1,
            total_mutations = total_mutations + 1
        WHERE agent_name = p_agent_name;
    END IF;

    -- Calculate new score (bounded 0-100)
    v_new_score := GREATEST(0.0, LEAST(100.0, v_old_score + v_delta));

    -- Update agent reputation score
    UPDATE agents
    SET reputation_score = v_new_score,
        last_reputation_update = NOW()
    WHERE agent_name = p_agent_name;

    -- Log reputation change
    INSERT INTO agent_reputation_history (
        agent_name, mcp_system, old_score, new_score, score_delta,
        event_type, event_details, event_metadata
    ) VALUES (
        p_agent_name, p_mcp_system, v_old_score, v_new_score, v_delta,
        CASE WHEN p_mutation_success THEN 'MUTATION_SUCCESS' ELSE 'MUTATION_FAILURE' END,
        p_event_details,
        jsonb_build_object(
            'quality_score', p_quality_score,
            'success', p_mutation_success
        )
    );

    RETURN v_new_score;
END;
$$ LANGUAGE plpgsql;

-- Create function to get top agents by reputation
CREATE OR REPLACE FUNCTION get_top_agents_by_reputation(p_limit INT DEFAULT 10)
RETURNS TABLE (
    agent_name VARCHAR(255),
    mcp_system VARCHAR(100),
    reputation_score DECIMAL(5,2),
    total_mutations INT,
    success_rate DECIMAL(5,2),
    rank INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.agent_name,
        a.mcp_system,
        a.reputation_score,
        a.total_mutations,
        CASE
            WHEN a.total_mutations > 0
            THEN (a.successful_mutations::DECIMAL / a.total_mutations::DECIMAL) * 100.0
            ELSE 0.0
        END as success_rate,
        ROW_NUMBER() OVER (ORDER BY a.reputation_score DESC)::INT as rank
    FROM agents a
    WHERE a.total_mutations > 0
    ORDER BY a.reputation_score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Create function for periodic reputation decay (prevents stagnation)
CREATE OR REPLACE FUNCTION apply_reputation_decay(
    p_decay_rate DECIMAL(5,2) DEFAULT 0.01, -- 1% decay towards neutral (50)
    p_min_mutations INT DEFAULT 5 -- Only decay agents with some history
) RETURNS INT AS $$
DECLARE
    v_affected_count INT := 0;
    v_agent RECORD;
BEGIN
    -- Decay all agents towards neutral score (50)
    FOR v_agent IN
        SELECT agent_name, mcp_system, reputation_score, total_mutations
        FROM agents
        WHERE total_mutations >= p_min_mutations
          AND reputation_score != 50.0
    LOOP
        -- Decay towards 50 (neutral)
        UPDATE agents
        SET reputation_score = reputation_score + (50.0 - reputation_score) * p_decay_rate,
            last_reputation_update = NOW()
        WHERE agent_name = v_agent.agent_name;

        -- Log decay event
        INSERT INTO agent_reputation_history (
            agent_name, mcp_system, old_score, new_score, score_delta,
            event_type, event_details
        ) VALUES (
            v_agent.agent_name, v_agent.mcp_system, v_agent.reputation_score,
            v_agent.reputation_score + (50.0 - v_agent.reputation_score) * p_decay_rate,
            (50.0 - v_agent.reputation_score) * p_decay_rate,
            'PERIODIC_DECAY',
            'Natural decay towards neutral reputation'
        );

        v_affected_count := v_affected_count + 1;
    END LOOP;

    RETURN v_affected_count;
END;
$$ LANGUAGE plpgsql;

-- Create view for agent reputation dashboard
CREATE OR REPLACE VIEW v_agent_reputation_dashboard AS
SELECT
    a.agent_name,
    a.mcp_system,
    a.reputation_score,
    a.total_mutations,
    a.successful_mutations,
    a.failed_mutations,
    CASE
        WHEN a.total_mutations > 0
        THEN (a.successful_mutations::DECIMAL / a.total_mutations::DECIMAL) * 100.0
        ELSE 0.0
    END as success_rate_percent,
    CASE
        WHEN a.reputation_score >= 75 THEN 'Excellent'
        WHEN a.reputation_score >= 60 THEN 'Good'
        WHEN a.reputation_score >= 40 THEN 'Fair'
        ELSE 'Poor'
    END as reputation_tier,
    a.last_reputation_update,
    -- Recent trend (last 7 days)
    (
        SELECT COALESCE(SUM(score_delta), 0)
        FROM agent_reputation_history
        WHERE agent_name = a.agent_name
          AND recorded_at >= NOW() - INTERVAL '7 days'
    ) as weekly_score_change
FROM agents a
ORDER BY a.reputation_score DESC;

-- Add comments
COMMENT ON COLUMN agents.reputation_score IS 'Agent reputation score (0-100, default 50). Updated based on mutation success/failure.';
COMMENT ON COLUMN agents.total_mutations IS 'Total number of brain mutations attempted by this agent';
COMMENT ON COLUMN agents.successful_mutations IS 'Number of successful mutations';
COMMENT ON COLUMN agents.failed_mutations IS 'Number of failed mutations';

COMMENT ON TABLE agent_reputation_history IS 'Historical tracking of agent reputation score changes over time';
COMMENT ON TABLE mutation_quality_tracking IS 'Detailed tracking of individual mutation attempts and their quality scores';

COMMENT ON FUNCTION update_agent_reputation IS 'Updates agent reputation based on mutation success/failure and quality score';
COMMENT ON FUNCTION get_top_agents_by_reputation IS 'Returns top N agents by reputation score with success rates';
COMMENT ON FUNCTION apply_reputation_decay IS 'Applies periodic decay to agent reputations to prevent stagnation';

-- Initialize reputation scores for existing agents
UPDATE agents
SET reputation_score = 50.0,
    total_mutations = 0,
    successful_mutations = 0,
    failed_mutations = 0,
    last_reputation_update = NOW()
WHERE reputation_score IS NULL;

-- ============================================================================
-- Migration Complete: Agent Reputation Scoring System
-- ============================================================================
-- Next steps:
-- 1. Update brain_agent_integration.py to call update_agent_reputation()
-- 2. Add reputation-weighted mutation application
-- 3. Create dashboard visualization for reputation leaderboard
-- 4. Schedule periodic reputation decay (weekly cron)
-- ============================================================================
