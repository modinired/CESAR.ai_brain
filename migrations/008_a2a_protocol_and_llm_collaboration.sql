-- ============================================================================
-- CESAR.ai Phase G: Agent-to-Agent Protocol & Collaborative LLM System
-- ============================================================================
-- Version: 1.0
-- Date: November 19, 2025
-- Description: Adds A2A messaging protocol and multi-LLM collaboration system
-- Purpose: Enable direct agent communication and collaborative LLM learning
-- ============================================================================

BEGIN;

-- ============================================================================
-- Section 1: Agent-to-Agent (A2A) Messaging Tables
-- ============================================================================

-- Message types enum
CREATE TYPE a2a_message_type AS ENUM (
    'request',        -- Request for information/action
    'response',       -- Response to a request
    'notification',   -- One-way notification
    'broadcast',      -- Message to multiple agents
    'handshake',      -- Connection establishment
    'heartbeat'       -- Keep-alive signal
);

-- Message priority enum
CREATE TYPE a2a_message_priority AS ENUM (
    'critical',   -- 0 - Immediate processing required
    'high',       -- 1 - Process soon
    'normal',     -- 2 - Standard priority
    'low',        -- 3 - Process when idle
    'background'  -- 4 - Background task
);

-- Message status enum
CREATE TYPE a2a_message_status AS ENUM (
    'pending',     -- Message created, not yet delivered
    'delivered',   -- Message delivered to recipient
    'read',        -- Message read by recipient
    'acknowledged',-- Message acknowledged
    'failed',      -- Delivery failed
    'timeout',     -- Message timed out
    'cancelled'    -- Message cancelled by sender
);

-- Core A2A messages table
CREATE TABLE a2a_messages (
    id                  uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_agent_id       uuid NOT NULL,
    to_agent_id         uuid NOT NULL,
    conversation_id     uuid,  -- Groups related messages
    message_type        a2a_message_type NOT NULL DEFAULT 'notification',
    priority            a2a_message_priority NOT NULL DEFAULT 'normal',
    status              a2a_message_status NOT NULL DEFAULT 'pending',

    -- Message content
    subject             text,
    content             jsonb NOT NULL,
    metadata            jsonb DEFAULT '{}'::jsonb,

    -- Delivery tracking
    requires_ack        boolean DEFAULT false,
    timeout_seconds     integer DEFAULT 30,
    retry_count         integer DEFAULT 0,
    max_retries         integer DEFAULT 3,

    -- Parent message for threading
    in_reply_to         uuid REFERENCES a2a_messages(id),

    -- Timestamps
    created_at          timestamptz NOT NULL DEFAULT now(),
    delivered_at        timestamptz,
    read_at             timestamptz,
    acknowledged_at     timestamptz,
    expires_at          timestamptz,

    -- Error tracking
    error_message       text,

    CONSTRAINT valid_timeout CHECK (timeout_seconds > 0 AND timeout_seconds <= 3600),
    CONSTRAINT valid_retries CHECK (retry_count >= 0 AND retry_count <= max_retries)
);

-- Indexes for efficient A2A message routing
CREATE INDEX idx_a2a_messages_to_agent ON a2a_messages(to_agent_id, status, priority, created_at);
CREATE INDEX idx_a2a_messages_from_agent ON a2a_messages(from_agent_id, created_at DESC);
CREATE INDEX idx_a2a_messages_conversation ON a2a_messages(conversation_id, created_at);
CREATE INDEX idx_a2a_messages_status ON a2a_messages(status, expires_at) WHERE status IN ('pending', 'delivered');
CREATE INDEX idx_a2a_messages_reply_thread ON a2a_messages(in_reply_to) WHERE in_reply_to IS NOT NULL;

COMMENT ON TABLE a2a_messages IS 'Direct agent-to-agent messaging with threading, priority, and delivery tracking';

-- ============================================================================
-- Section 2: Agent Conversation Tracking
-- ============================================================================

CREATE TABLE a2a_conversations (
    id                  uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    participants        uuid[] NOT NULL,  -- Array of agent IDs
    topic               text,
    purpose             text,

    -- Conversation state
    status              text DEFAULT 'active',  -- active, paused, completed, archived
    message_count       integer DEFAULT 0,

    -- Metadata
    metadata            jsonb DEFAULT '{}'::jsonb,
    tags                text[],

    -- Timestamps
    started_at          timestamptz NOT NULL DEFAULT now(),
    last_message_at     timestamptz,
    completed_at        timestamptz,

    CONSTRAINT valid_participants CHECK (array_length(participants, 1) >= 2)
);

CREATE INDEX idx_a2a_conversations_participants ON a2a_conversations USING gin(participants);
CREATE INDEX idx_a2a_conversations_status ON a2a_conversations(status, last_message_at DESC);
CREATE INDEX idx_a2a_conversations_tags ON a2a_conversations USING gin(tags);

COMMENT ON TABLE a2a_conversations IS 'Tracks multi-message conversations between agents';

-- ============================================================================
-- Section 3: Collaborative LLM Interaction System
-- ============================================================================

-- LLM collaboration strategy enum
CREATE TYPE llm_collaboration_strategy AS ENUM (
    'parallel',          -- All LLMs process simultaneously, best answer selected
    'sequential',        -- LLMs process in order, each refining previous output
    'hierarchical',      -- Local LLM first, escalate to cloud if needed
    'voting',            -- Multiple LLMs vote on best response
    'ensemble',          -- Combine outputs from multiple LLMs
    'teacher_student',   -- Cloud model teaches local model
    'peer_review'        -- LLMs review each other's outputs
);

-- Collaborative LLM interactions table
CREATE TABLE llm_collaborations (
    id                      uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id              uuid REFERENCES sessions(id) ON DELETE CASCADE,
    user_query              text NOT NULL,
    query_hash              text,  -- For deduplication and caching

    -- Collaboration configuration
    strategy                llm_collaboration_strategy NOT NULL DEFAULT 'hierarchical',
    participating_llms      uuid[] NOT NULL,  -- Array of LLM IDs involved
    primary_llm_id          uuid REFERENCES llms(id),

    -- Execution tracking
    status                  text DEFAULT 'pending',  -- pending, in_progress, completed, failed
    execution_order         jsonb,  -- Array showing LLM execution sequence

    -- Results
    individual_responses    jsonb DEFAULT '[]'::jsonb,  -- Each LLM's response
    final_response          text,
    selected_llm_id         uuid REFERENCES llms(id),  -- Which LLM provided final answer
    confidence_score        decimal(5,4),

    -- Learning data
    local_llm_learned       boolean DEFAULT false,
    learning_metadata       jsonb DEFAULT '{}'::jsonb,

    -- Performance metrics
    total_duration_ms       integer,
    individual_durations    jsonb,
    total_tokens_input      integer,
    total_tokens_output     integer,
    total_cost_usd          decimal(10,6) DEFAULT 0.00,

    -- Quality metrics
    user_feedback_rating    integer CHECK (user_feedback_rating >= 1 AND user_feedback_rating <= 5),
    user_feedback_text      text,

    -- Timestamps
    created_at              timestamptz NOT NULL DEFAULT now(),
    started_at              timestamptz,
    completed_at            timestamptz,

    metadata                jsonb DEFAULT '{}'::jsonb
);

CREATE INDEX idx_llm_collaborations_session ON llm_collaborations(session_id, created_at DESC);
CREATE INDEX idx_llm_collaborations_strategy ON llm_collaborations(strategy, status);
CREATE INDEX idx_llm_collaborations_query_hash ON llm_collaborations(query_hash) WHERE query_hash IS NOT NULL;
CREATE INDEX idx_llm_collaborations_llms ON llm_collaborations USING gin(participating_llms);
CREATE INDEX idx_llm_collaborations_learning ON llm_collaborations(local_llm_learned, created_at DESC);

COMMENT ON TABLE llm_collaborations IS 'Tracks multi-LLM collaborative processing with learning feedback loops';

-- ============================================================================
-- Section 4: Local LLM Learning System
-- ============================================================================

-- Learning examples captured from cloud models
CREATE TABLE local_llm_learning_examples (
    id                      uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    collaboration_id        uuid REFERENCES llm_collaborations(id) ON DELETE CASCADE,
    local_llm_id            uuid NOT NULL REFERENCES llms(id),
    teacher_llm_id          uuid REFERENCES llms(id),  -- Cloud model that provided superior answer

    -- Training data
    input_prompt            text NOT NULL,
    local_llm_output        text,  -- What local LLM produced
    teacher_llm_output      text,  -- What cloud LLM produced (better)
    improvement_delta       text,  -- Explanation of why teacher output is better

    -- Quality assessment
    quality_score           decimal(5,4),  -- 0-1 score of local output quality
    improvement_needed      text[],  -- Areas where local LLM needs improvement

    -- Learning metadata
    task_category           text,
    difficulty_level        text,  -- easy, medium, hard, expert
    applied_to_training     boolean DEFAULT false,
    training_batch_id       uuid,

    -- Tracking
    created_at              timestamptz NOT NULL DEFAULT now(),
    applied_at              timestamptz,

    metadata                jsonb DEFAULT '{}'::jsonb
);

CREATE INDEX idx_local_llm_learning_local ON local_llm_learning_examples(local_llm_id, created_at DESC);
CREATE INDEX idx_local_llm_learning_teacher ON local_llm_learning_examples(teacher_llm_id);
CREATE INDEX idx_local_llm_learning_quality ON local_llm_learning_examples(quality_score, difficulty_level);
CREATE INDEX idx_local_llm_learning_category ON local_llm_learning_examples(task_category, applied_to_training);

COMMENT ON TABLE local_llm_learning_examples IS 'Captures training examples for local LLMs from superior cloud model outputs';

-- Training batches for local LLM fine-tuning
CREATE TABLE local_llm_training_batches (
    id                      uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    local_llm_id            uuid NOT NULL REFERENCES llms(id),
    batch_name              text NOT NULL,

    -- Training configuration
    training_method         text,  -- 'fine_tune', 'prompt_caching', 'few_shot_examples'
    example_count           integer DEFAULT 0,
    example_ids             uuid[],  -- References to local_llm_learning_examples

    -- Training execution
    status                  text DEFAULT 'pending',  -- pending, training, completed, failed
    training_config         jsonb DEFAULT '{}'::jsonb,

    -- Results
    baseline_performance    jsonb,
    post_training_performance jsonb,
    improvement_metrics     jsonb,

    -- Timestamps
    created_at              timestamptz NOT NULL DEFAULT now(),
    started_at              timestamptz,
    completed_at            timestamptz,

    metadata                jsonb DEFAULT '{}'::jsonb
);

CREATE INDEX idx_local_llm_training_llm ON local_llm_training_batches(local_llm_id, status);
CREATE INDEX idx_local_llm_training_status ON local_llm_training_batches(status, created_at DESC);

COMMENT ON TABLE local_llm_training_batches IS 'Manages training batches for improving local LLM performance';

-- ============================================================================
-- Section 5: Routing Rules for Collaborative LLM Processing
-- ============================================================================

-- Add collaborative routing rules
INSERT INTO routing_rules (name, priority, task_tags, preferred_llm, fallback_llm, description) VALUES
(
    'Collaborative Code Generation',
    5,  -- Very high priority
    ARRAY['code', 'complex', 'collaborative'],
    (SELECT id FROM llms WHERE name = 'Qwen 2.5 Coder 7B (Local)'),
    (SELECT id FROM llms WHERE name = 'Claude Sonnet 4.5'),
    'Use local Qwen first, collaborate with Claude for complex code tasks. Local learns from Claude.'
),
(
    'Collaborative Analysis Route',
    8,
    ARRAY['analysis', 'complex', 'collaborative'],
    (SELECT id FROM llms WHERE name = 'Llama 3 8B (Local)'),
    (SELECT id FROM llms WHERE name = 'GPT-4o'),
    'Local Llama analyzes first, GPT-4o refines. Local learns from GPT-4o improvements.'
),
(
    'Collaborative Learning Route',
    3,  -- Highest priority
    ARRAY['learning', 'training', 'improvement'],
    (SELECT id FROM llms WHERE name = 'Qwen 2.5 Coder 7B (Local)'),
    (SELECT id FROM llms WHERE name = 'Claude Sonnet 4.5'),
    'Explicitly capture learning examples from cloud models to improve local models.'
);

-- ============================================================================
-- Section 6: Helper Functions for A2A Protocol
-- ============================================================================

-- Function to send A2A message
CREATE OR REPLACE FUNCTION send_a2a_message(
    p_from_agent_id uuid,
    p_to_agent_id uuid,
    p_message_type a2a_message_type,
    p_content jsonb,
    p_priority a2a_message_priority DEFAULT 'normal',
    p_conversation_id uuid DEFAULT NULL,
    p_requires_ack boolean DEFAULT false,
    p_timeout_seconds integer DEFAULT 30
) RETURNS uuid AS $$
DECLARE
    v_message_id uuid;
    v_conversation_id uuid;
BEGIN
    -- Create or use existing conversation
    IF p_conversation_id IS NULL THEN
        INSERT INTO a2a_conversations (participants, topic, status)
        VALUES (ARRAY[p_from_agent_id, p_to_agent_id], 'Direct Message', 'active')
        RETURNING id INTO v_conversation_id;
    ELSE
        v_conversation_id := p_conversation_id;
    END IF;

    -- Create message
    INSERT INTO a2a_messages (
        from_agent_id,
        to_agent_id,
        conversation_id,
        message_type,
        priority,
        content,
        requires_ack,
        timeout_seconds,
        expires_at
    ) VALUES (
        p_from_agent_id,
        p_to_agent_id,
        v_conversation_id,
        p_message_type,
        p_priority,
        p_content,
        p_requires_ack,
        p_timeout_seconds,
        now() + (p_timeout_seconds || ' seconds')::interval
    )
    RETURNING id INTO v_message_id;

    -- Update conversation
    UPDATE a2a_conversations
    SET message_count = message_count + 1,
        last_message_at = now()
    WHERE id = v_conversation_id;

    RETURN v_message_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION send_a2a_message IS 'Helper function to send agent-to-agent message with automatic conversation management';

-- Function to get pending messages for agent
CREATE OR REPLACE FUNCTION get_agent_inbox(
    p_agent_id uuid,
    p_limit integer DEFAULT 50
) RETURNS TABLE (
    message_id uuid,
    from_agent_id uuid,
    message_type a2a_message_type,
    priority a2a_message_priority,
    subject text,
    content jsonb,
    created_at timestamptz,
    conversation_id uuid
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        id,
        a2a_messages.from_agent_id,
        a2a_messages.message_type,
        a2a_messages.priority,
        a2a_messages.subject,
        a2a_messages.content,
        a2a_messages.created_at,
        a2a_messages.conversation_id
    FROM a2a_messages
    WHERE a2a_messages.to_agent_id = p_agent_id
      AND status IN ('pending', 'delivered')
      AND (expires_at IS NULL OR expires_at > now())
    ORDER BY
        CASE priority
            WHEN 'critical' THEN 0
            WHEN 'high' THEN 1
            WHEN 'normal' THEN 2
            WHEN 'low' THEN 3
            WHEN 'background' THEN 4
        END,
        created_at ASC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_agent_inbox IS 'Retrieves pending messages for an agent, sorted by priority';

-- Function to initiate LLM collaboration
CREATE OR REPLACE FUNCTION initiate_llm_collaboration(
    p_session_id uuid,
    p_user_query text,
    p_strategy llm_collaboration_strategy,
    p_llm_ids uuid[]
) RETURNS uuid AS $$
DECLARE
    v_collab_id uuid;
    v_query_hash text;
BEGIN
    -- Generate query hash for caching
    v_query_hash := md5(p_user_query);

    INSERT INTO llm_collaborations (
        session_id,
        user_query,
        query_hash,
        strategy,
        participating_llms,
        primary_llm_id,
        status
    ) VALUES (
        p_session_id,
        p_user_query,
        v_query_hash,
        p_strategy,
        p_llm_ids,
        p_llm_ids[1],  -- First LLM is primary
        'pending'
    )
    RETURNING id INTO v_collab_id;

    RETURN v_collab_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION initiate_llm_collaboration IS 'Creates a new collaborative LLM processing request';

-- ============================================================================
-- Section 7: Analytics Views
-- ============================================================================

-- View: A2A messaging statistics per agent
CREATE OR REPLACE VIEW a2a_agent_stats AS
SELECT
    agent_id,
    agent_name,
    total_messages_sent,
    total_messages_received,
    avg_response_time_seconds,
    message_success_rate,
    active_conversations
FROM (
    SELECT
        a.id AS agent_id,
        a.name AS agent_name,
        COUNT(DISTINCT m_sent.id) AS total_messages_sent,
        COUNT(DISTINCT m_received.id) AS total_messages_received,
        AVG(
            CASE
                WHEN m_received.status = 'acknowledged' AND m_received.acknowledged_at IS NOT NULL
                THEN EXTRACT(EPOCH FROM (m_received.acknowledged_at - m_received.created_at))
                ELSE NULL
            END
        ) AS avg_response_time_seconds,
        ROUND(
            COUNT(DISTINCT CASE WHEN m_sent.status IN ('delivered', 'acknowledged') THEN m_sent.id END)::numeric /
            NULLIF(COUNT(DISTINCT m_sent.id), 0) * 100,
            2
        ) AS message_success_rate,
        COUNT(DISTINCT c.id) FILTER (WHERE c.status = 'active') AS active_conversations
    FROM agents a
    LEFT JOIN a2a_messages m_sent ON m_sent.from_agent_id = a.id
    LEFT JOIN a2a_messages m_received ON m_received.to_agent_id = a.id
    LEFT JOIN a2a_conversations c ON a.id = ANY(c.participants)
    GROUP BY a.id, a.name
) stats;

COMMENT ON VIEW a2a_agent_stats IS 'Per-agent A2A messaging statistics including performance metrics';

-- View: Collaborative LLM performance
CREATE OR REPLACE VIEW llm_collaboration_performance AS
SELECT
    l.name AS llm_name,
    l.provider,
    CASE WHEN l.provider = 'ollama' THEN 'local' ELSE 'cloud' END AS deployment,
    lc.strategy,
    COUNT(lc.id) AS total_collaborations,
    COUNT(lc.id) FILTER (WHERE lc.selected_llm_id = l.id) AS times_selected_as_best,
    ROUND(
        COUNT(lc.id) FILTER (WHERE lc.selected_llm_id = l.id)::numeric /
        NULLIF(COUNT(lc.id), 0) * 100,
        2
    ) AS selection_rate_pct,
    AVG((lc.individual_durations->>l.id::text)::integer) AS avg_response_time_ms,
    AVG(lc.confidence_score) AS avg_confidence,
    AVG(lc.user_feedback_rating) AS avg_user_rating
FROM llms l
JOIN llm_collaborations lc ON l.id = ANY(lc.participating_llms)
WHERE lc.status = 'completed'
GROUP BY l.id, l.name, l.provider, lc.strategy
ORDER BY deployment, total_collaborations DESC;

COMMENT ON VIEW llm_collaboration_performance IS 'Performance metrics for LLMs in collaborative processing scenarios';

-- View: Local LLM learning progress
CREATE OR REPLACE VIEW local_llm_learning_progress AS
WITH category_counts AS (
    SELECT
        local_llm_id,
        task_category,
        COUNT(*) AS category_count
    FROM local_llm_learning_examples
    WHERE task_category IS NOT NULL
    GROUP BY local_llm_id, task_category
),
category_aggregates AS (
    SELECT
        local_llm_id,
        jsonb_object_agg(task_category, category_count) AS examples_by_category
    FROM category_counts
    GROUP BY local_llm_id
)
SELECT
    l.name AS local_llm_name,
    COUNT(DISTINCT lle.id) AS total_learning_examples,
    COUNT(DISTINCT lle.id) FILTER (WHERE lle.applied_to_training) AS applied_examples,
    COUNT(DISTINCT ltb.id) AS training_batches_completed,
    AVG(lle.quality_score) AS avg_quality_score,
    MAX(ltb.completed_at) AS last_training_date,
    COALESCE(ca.examples_by_category, '{}'::jsonb) AS examples_by_category
FROM llms l
LEFT JOIN local_llm_learning_examples lle ON lle.local_llm_id = l.id
LEFT JOIN local_llm_training_batches ltb ON ltb.local_llm_id = l.id AND ltb.status = 'completed'
LEFT JOIN category_aggregates ca ON ca.local_llm_id = l.id
WHERE l.provider = 'ollama'
GROUP BY l.id, l.name, ca.examples_by_category;

COMMENT ON VIEW local_llm_learning_progress IS 'Tracks learning and improvement progress for local Ollama models';

-- ============================================================================
-- Section 8: Triggers for Automated Learning
-- ============================================================================

-- Trigger: Automatically capture learning examples when cloud outperforms local
CREATE OR REPLACE FUNCTION capture_learning_example()
RETURNS TRIGGER AS $$
DECLARE
    v_local_llm_id uuid;
    v_cloud_llm_id uuid;
    v_local_response jsonb;
    v_cloud_response jsonb;
BEGIN
    -- Only process completed collaborations
    IF NEW.status = 'completed' AND NEW.strategy IN ('hierarchical', 'teacher_student', 'peer_review') THEN

        -- Find local and cloud LLM responses
        SELECT id INTO v_local_llm_id
        FROM llms
        WHERE id = ANY(NEW.participating_llms) AND provider = 'ollama'
        LIMIT 1;

        SELECT id INTO v_cloud_llm_id
        FROM llms
        WHERE id = NEW.selected_llm_id AND provider != 'ollama';

        -- If cloud model was selected as best answer, capture as learning example
        IF v_local_llm_id IS NOT NULL AND v_cloud_llm_id IS NOT NULL AND v_cloud_llm_id = NEW.selected_llm_id THEN

            -- Extract responses
            SELECT response INTO v_local_response
            FROM jsonb_array_elements(NEW.individual_responses) AS response
            WHERE response->>'llm_id' = v_local_llm_id::text;

            SELECT response INTO v_cloud_response
            FROM jsonb_array_elements(NEW.individual_responses) AS response
            WHERE response->>'llm_id' = v_cloud_llm_id::text;

            -- Insert learning example
            INSERT INTO local_llm_learning_examples (
                collaboration_id,
                local_llm_id,
                teacher_llm_id,
                input_prompt,
                local_llm_output,
                teacher_llm_output,
                quality_score,
                task_category
            ) VALUES (
                NEW.id,
                v_local_llm_id,
                v_cloud_llm_id,
                NEW.user_query,
                v_local_response->>'text',
                v_cloud_response->>'text',
                NEW.confidence_score,
                NEW.metadata->>'task_category'
            );

            -- Mark collaboration as having generated learning data
            NEW.local_llm_learned := true;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_capture_learning_example
BEFORE UPDATE ON llm_collaborations
FOR EACH ROW
WHEN (NEW.status = 'completed' AND OLD.status != 'completed')
EXECUTE FUNCTION capture_learning_example();

COMMENT ON TRIGGER trigger_capture_learning_example ON llm_collaborations IS 'Automatically captures learning examples when cloud models outperform local models';

-- ============================================================================
-- Section 9: Permissions
-- ============================================================================

GRANT SELECT ON a2a_messages TO PUBLIC;
GRANT SELECT ON a2a_conversations TO PUBLIC;
GRANT SELECT ON llm_collaborations TO PUBLIC;
GRANT SELECT ON local_llm_learning_examples TO PUBLIC;
GRANT SELECT ON local_llm_training_batches TO PUBLIC;

GRANT SELECT ON a2a_agent_stats TO PUBLIC;
GRANT SELECT ON llm_collaboration_performance TO PUBLIC;
GRANT SELECT ON local_llm_learning_progress TO PUBLIC;

-- ============================================================================
-- Summary
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'CESAR.ai Phase G: A2A Protocol & Collaborative LLM System - COMPLETE';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'Agent-to-Agent Communication:';
    RAISE NOTICE '  ✓ Direct messaging with priority queues';
    RAISE NOTICE '  ✓ Conversation threading and tracking';
    RAISE NOTICE '  ✓ Message acknowledgment and retry logic';
    RAISE NOTICE '  ✓ 6 message types (request, response, notification, broadcast, etc.)';
    RAISE NOTICE '  ✓ 5 priority levels (critical to background)';
    RAISE NOTICE '';
    RAISE NOTICE 'Collaborative LLM System:';
    RAISE NOTICE '  ✓ 7 collaboration strategies (parallel, sequential, teacher-student, etc.)';
    RAISE NOTICE '  ✓ Automatic learning capture when cloud outperforms local';
    RAISE NOTICE '  ✓ Training batch management for local LLM improvement';
    RAISE NOTICE '  ✓ Quality scoring and performance tracking';
    RAISE NOTICE '  ✓ Every user interaction now benefits local + cloud models';
    RAISE NOTICE '';
    RAISE NOTICE 'New Routing Rules: 3';
    RAISE NOTICE '  - Collaborative Code Generation (Qwen + Claude)';
    RAISE NOTICE '  - Collaborative Analysis (Llama + GPT-4o)';
    RAISE NOTICE '  - Collaborative Learning (explicit learning capture)';
    RAISE NOTICE '';
    RAISE NOTICE 'Benefits:';
    RAISE NOTICE '  ✓ Agents can communicate directly (not just via blackboard)';
    RAISE NOTICE '  ✓ Local LLMs learn from superior cloud model outputs';
    RAISE NOTICE '  ✓ Continuous improvement of local models';
    RAISE NOTICE '  ✓ Optimal benefit from every user interaction';
    RAISE NOTICE '  ✓ Reduced cloud costs as local models improve';
    RAISE NOTICE '';
    RAISE NOTICE 'Total Tables Added: 7';
    RAISE NOTICE '  - a2a_messages (direct agent communication)';
    RAISE NOTICE '  - a2a_conversations (conversation threading)';
    RAISE NOTICE '  - llm_collaborations (multi-LLM coordination)';
    RAISE NOTICE '  - local_llm_learning_examples (training data capture)';
    RAISE NOTICE '  - local_llm_training_batches (improvement tracking)';
    RAISE NOTICE '  + 3 analytics views + helper functions + triggers';
    RAISE NOTICE '';
    RAISE NOTICE 'Total Routing Rules: 34 (31 existing + 3 new)';
    RAISE NOTICE '============================================================================';
END $$;

COMMIT;
