-- Phase D: Attention-based Coordination
-- Implements priority scoring, dynamic task routing, and multi-agent collaboration

-- Attention Mechanisms: Tracks what agents should focus on
CREATE TABLE IF NOT EXISTS attention_mechanisms (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id text NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    session_id uuid REFERENCES sessions(id) ON DELETE CASCADE,

    -- Attention focus
    focus_type text NOT NULL, -- 'task', 'memory', 'entity', 'relationship', 'goal'
    focus_target_id uuid, -- ID of the target (task, memory, entity, etc.)
    focus_description text,

    -- Attention weights (learned via attention mechanism)
    attention_score numeric(10,6), -- Raw attention score
    normalized_weight numeric(5,4), -- Softmax-normalized weight
    priority_level integer, -- 1 (highest) to 10 (lowest)

    -- Context for attention
    context_vector vector(512), -- Learned context representation
    query_vector vector(512), -- Query for attention mechanism
    key_vector vector(512), -- Key for attention mechanism
    value_vector vector(512), -- Value for attention mechanism

    -- Temporal information
    attention_start timestamptz NOT NULL DEFAULT now(),
    attention_end timestamptz,
    duration_seconds integer,

    -- Effectiveness tracking
    outcome text, -- 'completed', 'abandoned', 'delegated', 'failed'
    effectiveness_score numeric(5,2), -- Post-hoc evaluation

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_attention_agent ON attention_mechanisms(agent_id, attention_start DESC);
CREATE INDEX IF NOT EXISTS idx_attention_session ON attention_mechanisms(session_id);
CREATE INDEX IF NOT EXISTS idx_attention_priority ON attention_mechanisms(priority_level ASC);
CREATE INDEX IF NOT EXISTS idx_attention_score ON attention_mechanisms(attention_score DESC);

-- Task Queue with Priority Scoring
CREATE TABLE IF NOT EXISTS task_queue (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Task identification
    task_id text UNIQUE NOT NULL,
    task_type text NOT NULL,
    task_description text NOT NULL,
    task_metadata jsonb DEFAULT '{}'::jsonb,

    -- Priority scoring (multi-factor)
    base_priority integer DEFAULT 5, -- User-assigned priority (1-10)
    urgency_score numeric(5,2) DEFAULT 0.5, -- Time-based urgency
    importance_score numeric(5,2) DEFAULT 0.5, -- Strategic importance
    complexity_score numeric(5,2) DEFAULT 0.5, -- Estimated complexity
    dependency_score numeric(5,2) DEFAULT 0.5, -- Dependencies on other tasks
    impact_score numeric(5,2) DEFAULT 0.5, -- Potential impact on goals

    -- Computed priority (weighted combination)
    computed_priority numeric(10,6), -- Final priority score
    priority_rank integer, -- Ranking among all tasks

    -- Task state
    status text NOT NULL DEFAULT 'pending', -- 'pending', 'assigned', 'in_progress', 'completed', 'failed', 'blocked'
    assigned_agent_id text REFERENCES agents(agent_id) ON DELETE SET NULL,
    assigned_llm_id uuid REFERENCES llms(id) ON DELETE SET NULL,

    -- Temporal constraints
    deadline timestamptz,
    estimated_duration_minutes integer,
    created_at timestamptz NOT NULL DEFAULT now(),
    assigned_at timestamptz,
    started_at timestamptz,
    completed_at timestamptz,

    -- Dependencies
    depends_on_tasks text[], -- Task IDs this task depends on
    blocks_tasks text[], -- Task IDs blocked by this task

    -- Results
    result jsonb,
    error_message text,

    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_task_queue_status ON task_queue(status);
CREATE INDEX IF NOT EXISTS idx_task_queue_priority ON task_queue(computed_priority DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_task_queue_deadline ON task_queue(deadline ASC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_task_queue_agent ON task_queue(assigned_agent_id);

-- Agent Workload: Tracks current and historical workload for each agent
CREATE TABLE IF NOT EXISTS agent_workload (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id text NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,

    -- Current workload
    active_tasks_count integer DEFAULT 0,
    queued_tasks_count integer DEFAULT 0,
    total_estimated_minutes integer DEFAULT 0,

    -- Capacity metrics
    max_concurrent_tasks integer DEFAULT 3,
    current_utilization numeric(5,2) DEFAULT 0.0, -- Percentage (0-100)
    availability_status text DEFAULT 'available', -- 'available', 'busy', 'overloaded', 'offline'

    -- Performance metrics (rolling window)
    avg_task_duration_minutes numeric(10,2),
    task_completion_rate numeric(5,2), -- Percentage of tasks completed successfully
    avg_quality_score numeric(5,2),

    -- Specialization scores (learned from history)
    specialization_scores jsonb DEFAULT '{}'::jsonb, -- {task_type: proficiency_score}

    -- Timestamp
    snapshot_time timestamptz NOT NULL DEFAULT now(),

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_workload_agent ON agent_workload(agent_id, snapshot_time DESC);
CREATE INDEX IF NOT EXISTS idx_workload_availability ON agent_workload(availability_status);
CREATE INDEX IF NOT EXISTS idx_workload_utilization ON agent_workload(current_utilization);

-- Multi-Agent Collaboration Sessions
CREATE TABLE IF NOT EXISTS collaboration_sessions (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Session identification
    session_name text,
    collaboration_type text NOT NULL, -- 'sequential', 'parallel', 'hierarchical', 'swarm'

    -- Participating agents
    agent_ids text[] NOT NULL,
    leader_agent_id text REFERENCES agents(agent_id) ON DELETE SET NULL,

    -- Collaboration goal
    goal_description text NOT NULL,
    success_criteria jsonb,

    -- Coordination mechanism
    coordination_strategy text, -- 'centralized', 'distributed', 'auction', 'voting'
    communication_protocol text, -- 'blackboard', 'message_passing', 'shared_memory'

    -- Session state
    status text NOT NULL DEFAULT 'active', -- 'active', 'completed', 'failed', 'paused'
    current_phase text, -- Custom phase tracking

    -- Results
    outcome jsonb,
    success_metrics jsonb,

    -- Temporal tracking
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    duration_seconds integer,

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_collab_status ON collaboration_sessions(status);
CREATE INDEX IF NOT EXISTS idx_collab_agents ON collaboration_sessions USING gin(agent_ids);

-- Coordination Messages: Communication between agents during collaboration
CREATE TABLE IF NOT EXISTS coordination_messages (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    collaboration_session_id uuid REFERENCES collaboration_sessions(id) ON DELETE CASCADE,

    -- Message routing
    from_agent_id text NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    to_agent_id text REFERENCES agents(agent_id) ON DELETE CASCADE, -- NULL for broadcast
    message_type text NOT NULL, -- 'request', 'response', 'notification', 'proposal', 'vote'

    -- Message content
    content jsonb NOT NULL,
    priority integer DEFAULT 5,

    -- Context
    in_reply_to uuid REFERENCES coordination_messages(id) ON DELETE SET NULL,
    thread_id uuid, -- For tracking conversation threads

    -- Delivery tracking
    sent_at timestamptz NOT NULL DEFAULT now(),
    received_at timestamptz,
    acknowledged_at timestamptz,
    processed_at timestamptz,

    -- Response
    response_id uuid REFERENCES coordination_messages(id) ON DELETE SET NULL,

    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_coord_msg_session ON coordination_messages(collaboration_session_id, sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_coord_msg_from ON coordination_messages(from_agent_id);
CREATE INDEX IF NOT EXISTS idx_coord_msg_to ON coordination_messages(to_agent_id);
CREATE INDEX IF NOT EXISTS idx_coord_msg_thread ON coordination_messages(thread_id);

-- Dynamic Routing Decisions: Logs all routing decisions made by the attention-based router
CREATE TABLE IF NOT EXISTS routing_decisions (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Decision context
    task_id uuid REFERENCES task_queue(id) ON DELETE SET NULL,
    session_id uuid REFERENCES sessions(id) ON DELETE SET NULL,

    -- Decision inputs
    available_agents text[], -- Agents considered
    available_llms uuid[], -- LLMs considered
    task_requirements jsonb, -- Requirements from the task

    -- Attention-based scoring
    agent_attention_scores jsonb, -- {agent_id: attention_score}
    llm_attention_scores jsonb, -- {llm_id: attention_score}
    capability_match_scores jsonb, -- Capability alignment scores
    workload_balance_scores jsonb, -- Workload considerations

    -- Final decision
    selected_agent_id text REFERENCES agents(agent_id) ON DELETE SET NULL,
    selected_llm_id uuid REFERENCES llms(id) ON DELETE SET NULL,
    routing_rule_id uuid REFERENCES routing_rules(id) ON DELETE SET NULL,

    -- Decision rationale
    decision_method text, -- 'rule_based', 'attention_based', 'hybrid', 'manual'
    confidence_score numeric(5,2),
    explanation text,

    -- Outcome tracking (for learning)
    actual_outcome text, -- 'success', 'failure', 'timeout', 'error'
    performance_metrics jsonb,
    feedback_score numeric(5,2),

    created_at timestamptz NOT NULL DEFAULT now(),
    outcome_recorded_at timestamptz
);

CREATE INDEX IF NOT EXISTS idx_routing_decision_task ON routing_decisions(task_id);
CREATE INDEX IF NOT EXISTS idx_routing_decision_method ON routing_decisions(decision_method);
CREATE INDEX IF NOT EXISTS idx_routing_decision_time ON routing_decisions(created_at DESC);

-- Attention Patterns: Learned patterns of effective attention allocation
CREATE TABLE IF NOT EXISTS attention_patterns (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Pattern identification
    pattern_name text NOT NULL,
    pattern_type text NOT NULL, -- 'successful', 'failed', 'optimal', 'suboptimal'

    -- Pattern description
    context_description text,
    trigger_conditions jsonb, -- Conditions that activate this pattern

    -- Attention allocation
    attention_allocation jsonb NOT NULL, -- {focus_type: weight_distribution}
    recommended_agents text[],
    recommended_llms uuid[],

    -- Pattern effectiveness
    success_rate numeric(5,2),
    avg_performance_score numeric(5,2),
    usage_count integer DEFAULT 0,
    last_used timestamptz,

    -- Pattern learning
    learned_from_sessions uuid[], -- Sessions this pattern was extracted from
    confidence_score numeric(5,2) DEFAULT 0.5,
    pattern_version integer DEFAULT 1,

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_attention_patterns_type ON attention_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_attention_patterns_success ON attention_patterns(success_rate DESC);

-- Goal Tracking: Tracks high-level goals and their decomposition
CREATE TABLE IF NOT EXISTS goals (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Goal identification
    goal_name text NOT NULL,
    goal_type text, -- 'user_goal', 'agent_goal', 'system_goal'
    description text NOT NULL,

    -- Goal hierarchy
    parent_goal_id uuid REFERENCES goals(id) ON DELETE CASCADE,
    subgoals uuid[], -- Child goal IDs

    -- Goal state
    status text NOT NULL DEFAULT 'active', -- 'active', 'completed', 'abandoned', 'blocked'
    priority integer DEFAULT 5,
    progress numeric(5,2) DEFAULT 0.0, -- Percentage (0-100)

    -- Associated entities
    session_id uuid REFERENCES sessions(id) ON DELETE SET NULL,
    owner_agent_id text REFERENCES agents(agent_id) ON DELETE SET NULL,
    related_tasks uuid[], -- Task IDs contributing to this goal

    -- Success criteria
    success_criteria jsonb,
    completion_conditions jsonb,

    -- Temporal tracking
    created_at timestamptz NOT NULL DEFAULT now(),
    target_completion timestamptz,
    completed_at timestamptz,
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status);
CREATE INDEX IF NOT EXISTS idx_goals_priority ON goals(priority ASC);
CREATE INDEX IF NOT EXISTS idx_goals_parent ON goals(parent_goal_id);

COMMENT ON TABLE attention_mechanisms IS 'Attention tracking: what agents focus on and why';
COMMENT ON TABLE task_queue IS 'Priority-scored task queue with multi-factor ranking';
COMMENT ON TABLE agent_workload IS 'Real-time and historical workload tracking per agent';
COMMENT ON TABLE collaboration_sessions IS 'Multi-agent collaboration coordination';
COMMENT ON TABLE routing_decisions IS 'Logged routing decisions for continual learning';
COMMENT ON TABLE attention_patterns IS 'Learned patterns of effective attention allocation';
COMMENT ON TABLE goals IS 'Hierarchical goal tracking and decomposition';
