-- Phase E: Continual Learning System
-- Implements reflection analysis, capability evolution, and self-improving agent selection

-- Learning Episodes: Captures complete learning experiences
CREATE TABLE IF NOT EXISTS learning_episodes (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Episode identification
    episode_type text NOT NULL, -- 'task_execution', 'collaboration', 'error_recovery', 'user_interaction'
    session_id uuid REFERENCES sessions(id) ON DELETE SET NULL,
    agent_id text REFERENCES agents(agent_id) ON DELETE SET NULL,

    -- Episode content
    context_before jsonb NOT NULL,
    actions_taken jsonb NOT NULL,
    context_after jsonb NOT NULL,
    outcome text NOT NULL, -- 'success', 'partial_success', 'failure'

    -- Learning signals
    reward_signal numeric(10,6), -- Reinforcement learning reward
    temporal_difference numeric(10,6), -- TD error for value learning
    advantage numeric(10,6), -- Policy gradient advantage

    -- Episode metrics
    duration_seconds integer,
    complexity_score numeric(5,2),
    novelty_score numeric(5,2), -- How different from previous episodes

    -- References
    task_id uuid REFERENCES task_queue(id) ON DELETE SET NULL,
    routing_decision_id uuid REFERENCES routing_decisions(id) ON DELETE SET NULL,
    related_memories uuid[], -- Relevant episodic memories

    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_learning_episodes_type ON learning_episodes(episode_type);
CREATE INDEX IF NOT EXISTS idx_learning_episodes_agent ON learning_episodes(agent_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_learning_episodes_outcome ON learning_episodes(outcome);
CREATE INDEX IF NOT EXISTS idx_learning_episodes_reward ON learning_episodes(reward_signal DESC);

-- Agent Capability Evolution: Tracks how agent capabilities improve over time
CREATE TABLE IF NOT EXISTS capability_evolution (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id text NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,

    -- Capability identification
    capability_name text NOT NULL,
    capability_category text, -- 'technical', 'analytical', 'creative', 'coordination'

    -- Proficiency tracking
    proficiency_score numeric(5,2) NOT NULL, -- 0.0 to 1.0
    confidence_interval numeric(5,2), -- Uncertainty in the score

    -- Evidence
    supporting_episodes uuid[], -- Learning episodes that contributed
    task_count integer DEFAULT 0,
    success_count integer DEFAULT 0,
    failure_count integer DEFAULT 0,

    -- Improvement metrics
    learning_rate numeric(10,6), -- Rate of improvement
    plateau_detected boolean DEFAULT false,
    last_improvement_date timestamptz,

    -- Snapshot info
    snapshot_date timestamptz NOT NULL DEFAULT now(),

    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_capability_agent ON capability_evolution(agent_id, capability_name);
CREATE INDEX IF NOT EXISTS idx_capability_proficiency ON capability_evolution(proficiency_score DESC);
CREATE INDEX IF NOT EXISTS idx_capability_snapshot ON capability_evolution(snapshot_date DESC);

-- Reflection Analysis: Auto-generated insights from learning reflections
CREATE TABLE IF NOT EXISTS reflection_analysis (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Source reflections
    reflection_ids uuid[], -- IDs from learning_reflections
    analysis_scope text, -- 'single_reflection', 'session', 'agent', 'system_wide'

    -- Analysis results
    key_insights text[],
    patterns_detected jsonb, -- Detected patterns and trends
    anomalies jsonb, -- Unusual or unexpected findings
    recommendations jsonb, -- Actionable recommendations

    -- Sentiment and themes
    overall_sentiment numeric(5,2), -- -1.0 (negative) to 1.0 (positive)
    dominant_themes text[],
    emotional_patterns jsonb,

    -- Impact assessment
    impact_areas jsonb, -- {area: impact_score}
    priority_actions text[],

    -- Analysis metadata
    analysis_method text, -- 'llm_based', 'statistical', 'hybrid'
    confidence_score numeric(5,2),
    analyzed_by_agent_id text REFERENCES agents(agent_id) ON DELETE SET NULL,

    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_reflection_analysis_scope ON reflection_analysis(analysis_scope);
CREATE INDEX IF NOT EXISTS idx_reflection_analysis_time ON reflection_analysis(created_at DESC);

-- Performance Baselines: Establishes baseline performance metrics for comparison
CREATE TABLE IF NOT EXISTS performance_baselines (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Baseline identification
    baseline_name text NOT NULL,
    metric_name text NOT NULL,
    metric_category text, -- 'latency', 'accuracy', 'quality', 'cost', 'user_satisfaction'

    -- Baseline values
    baseline_value numeric(10,4) NOT NULL,
    stddev numeric(10,4),
    percentile_95 numeric(10,4),
    percentile_99 numeric(10,4),

    -- Context
    agent_id text REFERENCES agents(agent_id) ON DELETE CASCADE,
    task_type text,
    conditions jsonb, -- Environmental/contextual conditions

    -- Sample information
    sample_size integer,
    measurement_start timestamptz NOT NULL,
    measurement_end timestamptz NOT NULL,

    -- Baseline status
    is_current boolean DEFAULT true,
    superseded_by uuid REFERENCES performance_baselines(id) ON DELETE SET NULL,

    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_baseline_agent_metric ON performance_baselines(agent_id, metric_name);
CREATE INDEX IF NOT EXISTS idx_baseline_current ON performance_baselines(is_current) WHERE is_current;

-- Performance Improvements: Tracks detected performance improvements over baselines
CREATE TABLE IF NOT EXISTS performance_improvements (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Improvement identification
    improvement_type text NOT NULL, -- 'agent_capability', 'routing_efficiency', 'collaboration_quality'
    baseline_id uuid REFERENCES performance_baselines(id) ON DELETE SET NULL,

    -- Metrics
    metric_name text NOT NULL,
    old_value numeric(10,4) NOT NULL,
    new_value numeric(10,4) NOT NULL,
    improvement_percentage numeric(10,4), -- Percentage improvement
    improvement_absolute numeric(10,4), -- Absolute improvement

    -- Statistical significance
    confidence_level numeric(5,2), -- e.g., 0.95 for 95% confidence
    p_value numeric(10,6),
    is_significant boolean DEFAULT false,

    -- Attribution
    attributed_to jsonb, -- What caused the improvement
    learning_episodes uuid[], -- Episodes that contributed

    -- Validation
    validated boolean DEFAULT false,
    validation_method text,
    validation_date timestamptz,

    detected_at timestamptz NOT NULL DEFAULT now(),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_improvements_type ON performance_improvements(improvement_type);
CREATE INDEX IF NOT EXISTS idx_improvements_significant ON performance_improvements(is_significant) WHERE is_significant;
CREATE INDEX IF NOT EXISTS idx_improvements_detected ON performance_improvements(detected_at DESC);

-- Meta-Learning Parameters: Stores learned parameters for learning algorithms themselves
CREATE TABLE IF NOT EXISTS meta_learning_params (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Parameter identification
    param_name text NOT NULL,
    param_category text, -- 'learning_rate', 'exploration_rate', 'attention_weight', etc.
    scope text, -- 'global', 'agent_specific', 'task_specific'

    -- Current value
    current_value numeric(10,6) NOT NULL,
    value_history jsonb, -- Historical values with timestamps

    -- Adaptation tracking
    auto_adjusted boolean DEFAULT true,
    adjustment_strategy text, -- 'gradient_descent', 'evolutionary', 'grid_search'
    last_adjusted timestamptz,

    -- Performance correlation
    performance_impact numeric(5,2), -- Correlation with performance
    optimal_range_min numeric(10,6),
    optimal_range_max numeric(10,6),

    -- Constraints
    hard_min numeric(10,6),
    hard_max numeric(10,6),

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_meta_params_name ON meta_learning_params(param_name);
CREATE INDEX IF NOT EXISTS idx_meta_params_scope ON meta_learning_params(scope);

-- Experiment Tracking: A/B tests and controlled experiments
CREATE TABLE IF NOT EXISTS learning_experiments (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Experiment design
    experiment_name text NOT NULL,
    experiment_type text NOT NULL, -- 'ab_test', 'multivariate', 'bandit', 'parameter_sweep'
    hypothesis text,

    -- Experimental conditions
    control_condition jsonb NOT NULL,
    treatment_conditions jsonb NOT NULL, -- Array of treatment variants
    randomization_strategy text, -- 'random', 'stratified', 'blocked'

    -- Experiment state
    status text NOT NULL DEFAULT 'draft', -- 'draft', 'running', 'paused', 'completed', 'abandoned'
    start_date timestamptz,
    end_date timestamptz,
    planned_duration_days integer,

    -- Sample allocation
    control_group_ids text[],
    treatment_group_ids jsonb, -- {treatment_id: [agent_ids]}
    sample_size_target integer,
    sample_size_actual integer,

    -- Results
    primary_metric text,
    results jsonb,
    winner text, -- 'control', 'treatment_1', 'treatment_2', etc.
    statistical_significance numeric(5,2),

    -- Analysis
    analysis_notes text,
    conclusion text,
    recommendations text[],

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_experiments_status ON learning_experiments(status);
CREATE INDEX IF NOT EXISTS idx_experiments_type ON learning_experiments(experiment_type);

-- Knowledge Transfer: Tracks transfer of learned knowledge between agents
CREATE TABLE IF NOT EXISTS knowledge_transfer (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Transfer identification
    transfer_type text NOT NULL, -- 'capability', 'pattern', 'strategy', 'heuristic'
    source_agent_id text NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    target_agent_id text NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,

    -- Knowledge content
    knowledge_description text NOT NULL,
    knowledge_data jsonb NOT NULL,
    knowledge_format text, -- 'parameters', 'rules', 'embeddings', 'symbolic'

    -- Transfer metadata
    transfer_method text, -- 'distillation', 'imitation', 'direct_copy', 'ensemble'
    success_probability numeric(5,2),

    -- Transfer validation
    pre_transfer_performance numeric(5,2),
    post_transfer_performance numeric(5,2),
    performance_delta numeric(5,2),
    transfer_successful boolean,

    -- Source tracking
    source_episodes uuid[], -- Episodes where knowledge was learned
    source_capabilities text[], -- Capabilities being transferred

    transferred_at timestamptz NOT NULL DEFAULT now(),
    validated_at timestamptz,

    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_transfer_source ON knowledge_transfer(source_agent_id);
CREATE INDEX IF NOT EXISTS idx_transfer_target ON knowledge_transfer(target_agent_id);
CREATE INDEX IF NOT EXISTS idx_transfer_type ON knowledge_transfer(transfer_type);
CREATE INDEX IF NOT EXISTS idx_transfer_success ON knowledge_transfer(transfer_successful);

-- Curriculum: Structured learning paths for agent development
CREATE TABLE IF NOT EXISTS learning_curriculum (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Curriculum identification
    curriculum_name text NOT NULL,
    target_capability text NOT NULL,
    difficulty_level integer, -- 1 (beginner) to 10 (expert)

    -- Curriculum structure
    learning_stages jsonb NOT NULL, -- Ordered array of learning stages
    prerequisites jsonb, -- Required prior knowledge
    estimated_duration_hours integer,

    -- Progress tracking
    agents_enrolled text[],
    completion_stats jsonb, -- {agent_id: {stage: completion_percentage}}

    -- Effectiveness
    avg_completion_time_hours numeric(10,2),
    success_rate numeric(5,2),
    dropout_rate numeric(5,2),

    -- Curriculum evolution
    version integer DEFAULT 1,
    last_updated timestamptz NOT NULL DEFAULT now(),
    update_reason text,

    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_curriculum_capability ON learning_curriculum(target_capability);
CREATE INDEX IF NOT EXISTS idx_curriculum_difficulty ON learning_curriculum(difficulty_level);

-- Create materialized view for learning analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS learning_analytics_summary AS
SELECT
    (SELECT COUNT(*) FROM learning_episodes) as total_episodes,
    (SELECT COUNT(*) FROM learning_episodes WHERE outcome = 'success') as successful_episodes,
    (SELECT AVG(reward_signal) FROM learning_episodes) as avg_reward,
    (SELECT COUNT(DISTINCT agent_id) FROM capability_evolution) as agents_with_capabilities,
    (SELECT COUNT(*) FROM performance_improvements WHERE is_significant = true) as significant_improvements,
    (SELECT COUNT(*) FROM knowledge_transfer WHERE transfer_successful = true) as successful_transfers,
    (SELECT COUNT(*) FROM learning_experiments WHERE status = 'running') as active_experiments,
    now() as last_updated;

CREATE UNIQUE INDEX IF NOT EXISTS idx_learning_analytics_singleton ON learning_analytics_summary((1));

COMMENT ON TABLE learning_episodes IS 'Complete learning experiences with reward signals for RL';
COMMENT ON TABLE capability_evolution IS 'Tracks improvement of agent capabilities over time';
COMMENT ON TABLE reflection_analysis IS 'Auto-generated insights from learning reflections';
COMMENT ON TABLE performance_improvements IS 'Detected and validated performance improvements';
COMMENT ON TABLE meta_learning_params IS 'Self-adjusting parameters for learning algorithms';
COMMENT ON TABLE learning_experiments IS 'A/B tests and controlled experiments for optimization';
COMMENT ON TABLE knowledge_transfer IS 'Transfer of learned knowledge between agents';
COMMENT ON TABLE learning_curriculum IS 'Structured learning paths for capability development';
