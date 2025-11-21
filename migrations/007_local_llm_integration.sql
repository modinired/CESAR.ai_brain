-- ============================================================================
-- CESAR.ai Phase F: Local LLM Integration (Ollama)
-- ============================================================================
-- Version: 1.0
-- Date: November 19, 2025
-- Description: Adds local Ollama models for hybrid multi-LLM architecture
-- Purpose: Enable free, private, offline-capable local inference
-- ============================================================================

BEGIN;

-- ============================================================================
-- Section 1: Add Local Ollama Models to LLM Registry
-- ============================================================================

-- Add Qwen 2.5 Coder (7B) - Primary local code generation model
INSERT INTO llms (name, provider, model_id, context_tokens, max_output_tokens, cost_per_1k_input, cost_per_1k_output, tags, capabilities, metadata) VALUES
(
    'Qwen 2.5 Coder 7B (Local)',
    'ollama',
    'qwen2.5-coder:7b',
    32768,              -- 32K context window
    4096,               -- 4K max output
    0.00,               -- FREE - local inference
    0.00,               -- FREE - local inference
    ARRAY['local', 'code', 'fast', 'offline', 'privacy'],
    '{
        "code": true,
        "function_calling": false,
        "vision": false,
        "local": true,
        "offline": true,
        "languages": ["python", "javascript", "java", "c++", "rust", "go"],
        "specializations": ["code_generation", "code_explanation", "debugging", "refactoring"]
    }'::jsonb,
    '{
        "endpoint": "http://localhost:11434",
        "model_size_gb": 4.7,
        "quantization": "Q4_0",
        "recommended_use": "Development, testing, code generation",
        "privacy_level": "complete",
        "network_required": false
    }'::jsonb
)
ON CONFLICT (name) DO UPDATE SET
    model_id = EXCLUDED.model_id,
    context_tokens = EXCLUDED.context_tokens,
    capabilities = EXCLUDED.capabilities,
    metadata = EXCLUDED.metadata,
    updated_at = now();

-- Add Llama 3 (8B) - General-purpose local model
INSERT INTO llms (name, provider, model_id, context_tokens, max_output_tokens, cost_per_1k_input, cost_per_1k_output, tags, capabilities, metadata) VALUES
(
    'Llama 3 8B (Local)',
    'ollama',
    'llama3:8b',
    8192,               -- 8K context window
    2048,               -- 2K max output
    0.00,               -- FREE - local inference
    0.00,               -- FREE - local inference
    ARRAY['local', 'chat', 'fast', 'offline', 'privacy', 'general'],
    '{
        "code": true,
        "function_calling": false,
        "vision": false,
        "local": true,
        "offline": true,
        "chat": true,
        "reasoning": true,
        "specializations": ["general_qa", "summarization", "classification", "simple_tasks"]
    }'::jsonb,
    '{
        "endpoint": "http://localhost:11434",
        "model_size_gb": 4.7,
        "quantization": "Q4_0",
        "recommended_use": "General tasks, prototyping, offline work",
        "privacy_level": "complete",
        "network_required": false
    }'::jsonb
)
ON CONFLICT (name) DO UPDATE SET
    model_id = EXCLUDED.model_id,
    context_tokens = EXCLUDED.context_tokens,
    capabilities = EXCLUDED.capabilities,
    metadata = EXCLUDED.metadata,
    updated_at = now();

-- ============================================================================
-- Section 2: Add Routing Rules for Local Models
-- ============================================================================

-- Local code generation routes (development/testing)
INSERT INTO routing_rules (name, priority, task_tags, preferred_llm, fallback_llm, description) VALUES
(
    'Local Code Generation Route',
    15,                 -- Higher priority than cloud for dev tasks
    ARRAY['local', 'code', 'dev', 'test', 'offline'],
    (SELECT id FROM llms WHERE name = 'Qwen 2.5 Coder 7B (Local)'),
    (SELECT id FROM llms WHERE name = 'Claude Sonnet 4.5'),
    'Use local Qwen for code generation in development/testing. Fallback to Claude for production.'
),
(
    'Local Quick Tasks Route',
    25,                 -- High priority for fast, simple tasks
    ARRAY['local', 'quick', 'simple', 'offline'],
    (SELECT id FROM llms WHERE name = 'Llama 3 8B (Local)'),
    (SELECT id FROM llms WHERE name = 'Claude Haiku 3.5'),
    'Use local Llama for quick, simple tasks. Fallback to Haiku if unavailable.'
),
(
    'Local Testing Route',
    35,
    ARRAY['test', 'prototype', 'experiment', 'local'],
    (SELECT id FROM llms WHERE name = 'Llama 3 8B (Local)'),
    (SELECT id FROM llms WHERE name = 'GPT-4o-mini'),
    'Use local Llama for testing and prototyping. Fallback to GPT-4o-mini.'
);

-- Privacy-first routes (sensitive data handling)
INSERT INTO routing_rules (name, priority, task_tags, preferred_llm, description) VALUES
(
    'Privacy-First Code Route',
    12,
    ARRAY['privacy', 'sensitive', 'confidential', 'code'],
    (SELECT id FROM llms WHERE name = 'Qwen 2.5 Coder 7B (Local)'),
    'Use local Qwen for sensitive code that must not leave the system.'
),
(
    'Privacy-First General Route',
    22,
    ARRAY['privacy', 'sensitive', 'confidential', 'pii'],
    (SELECT id FROM llms WHERE name = 'Llama 3 8B (Local)'),
    'Use local Llama for sensitive data processing (PII, confidential info).'
);

-- Offline operation routes
INSERT INTO routing_rules (name, priority, task_tags, preferred_llm, description) VALUES
(
    'Offline Code Route',
    18,
    ARRAY['offline', 'no_network', 'code'],
    (SELECT id FROM llms WHERE name = 'Qwen 2.5 Coder 7B (Local)'),
    'Use local Qwen when network is unavailable or unreliable.'
),
(
    'Offline General Route',
    28,
    ARRAY['offline', 'no_network', 'chat'],
    (SELECT id FROM llms WHERE name = 'Llama 3 8B (Local)'),
    'Use local Llama when network is unavailable or unreliable.'
);

-- ============================================================================
-- Section 3: Create Hybrid Routing Strategy View
-- ============================================================================

-- View showing all LLMs categorized by deployment type
CREATE OR REPLACE VIEW llm_deployment_strategy AS
SELECT
    l.name,
    l.provider,
    l.model_id,
    CASE
        WHEN l.provider = 'ollama' THEN 'local'
        ELSE 'cloud'
    END AS deployment_type,
    l.cost_per_1k_input,
    l.cost_per_1k_output,
    l.tags,
    l.capabilities,
    l.enabled,
    COUNT(rr.id) AS active_routes
FROM llms l
LEFT JOIN routing_rules rr ON rr.preferred_llm = l.id
WHERE l.enabled = true
GROUP BY l.id, l.name, l.provider, l.model_id, l.cost_per_1k_input, l.cost_per_1k_output, l.tags, l.capabilities, l.enabled
ORDER BY deployment_type, l.name;

COMMENT ON VIEW llm_deployment_strategy IS 'Overview of hybrid LLM deployment: local (Ollama) and cloud (API) models with routing distribution';

-- ============================================================================
-- Section 4: Create Local Model Health Check Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS local_llm_health (
    id                  uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    llm_id              uuid NOT NULL REFERENCES llms(id) ON DELETE CASCADE,
    endpoint            text NOT NULL,
    status              text NOT NULL, -- 'online', 'offline', 'degraded'
    response_time_ms    integer,
    last_check_at       timestamptz NOT NULL DEFAULT now(),
    error_message       text,
    metadata            jsonb DEFAULT '{}'::jsonb,
    created_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_local_llm_health_llm ON local_llm_health(llm_id, last_check_at DESC);
CREATE INDEX IF NOT EXISTS idx_local_llm_health_status ON local_llm_health(status, last_check_at DESC);

COMMENT ON TABLE local_llm_health IS 'Health check history for local Ollama models to track availability';

-- ============================================================================
-- Section 5: Update Stats View to Include Local LLMs
-- ============================================================================

CREATE OR REPLACE VIEW llm_usage_stats AS
SELECT
    l.name,
    l.provider,
    CASE WHEN l.provider = 'ollama' THEN 'local' ELSE 'cloud' END AS deployment,
    COUNT(DISTINCT rr.id) AS routing_rules_count,
    COUNT(DISTINCT ar.id) AS agent_runs_count,
    SUM(CASE WHEN ar.status = 'completed' THEN 1 ELSE 0 END) AS successful_runs,
    AVG(CASE WHEN ar.status = 'completed' THEN EXTRACT(EPOCH FROM (ar.completed_at - ar.created_at)) ELSE NULL END) AS avg_duration_seconds,
    l.cost_per_1k_input,
    l.cost_per_1k_output,
    -- Estimated cost (0 for local models)
    CASE
        WHEN l.provider = 'ollama' THEN 0.00
        ELSE COALESCE(
            SUM(
                CASE WHEN ar.status = 'completed' THEN
                    (COALESCE(ar.metadata->>'input_tokens', '0')::numeric / 1000.0 * l.cost_per_1k_input) +
                    (COALESCE(ar.metadata->>'output_tokens', '0')::numeric / 1000.0 * l.cost_per_1k_output)
                ELSE 0 END
            ), 0.00
        )
    END AS total_cost_usd,
    l.enabled
FROM llms l
LEFT JOIN routing_rules rr ON rr.preferred_llm = l.id
LEFT JOIN agent_runs ar ON ar.metadata->>'llm_used' = l.name
GROUP BY l.id, l.name, l.provider, l.cost_per_1k_input, l.cost_per_1k_output, l.enabled
ORDER BY deployment, total_cost_usd DESC;

COMMENT ON VIEW llm_usage_stats IS 'Comprehensive LLM usage statistics showing local vs cloud deployment costs and performance';

-- ============================================================================
-- Section 6: Grant Permissions
-- ============================================================================

-- Grant read access to health check table
GRANT SELECT ON local_llm_health TO PUBLIC;

-- Grant access to views
GRANT SELECT ON llm_deployment_strategy TO PUBLIC;
GRANT SELECT ON llm_usage_stats TO PUBLIC;

-- ============================================================================
-- Summary
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'CESAR.ai Phase F: Local LLM Integration - COMPLETE';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'Added Models:';
    RAISE NOTICE '  - Qwen 2.5 Coder 7B (Local) - Code generation, development, testing';
    RAISE NOTICE '  - Llama 3 8B (Local) - General tasks, prototyping, offline work';
    RAISE NOTICE '';
    RAISE NOTICE 'Added Routes: 7 new routing rules';
    RAISE NOTICE '  - 2 local development routes (higher priority for dev/test)';
    RAISE NOTICE '  - 2 privacy-first routes (sensitive data stays local)';
    RAISE NOTICE '  - 2 offline routes (network-independent operation)';
    RAISE NOTICE '  - 1 quick tasks route (fast local inference)';
    RAISE NOTICE '';
    RAISE NOTICE 'Benefits:';
    RAISE NOTICE '  ✓ Zero cost inference for development/testing';
    RAISE NOTICE '  ✓ Complete data privacy (no external API calls)';
    RAISE NOTICE '  ✓ Offline capability (no internet required)';
    RAISE NOTICE '  ✓ Fast response times (no network latency)';
    RAISE NOTICE '  ✓ Hybrid architecture (best of local + cloud)';
    RAISE NOTICE '';
    RAISE NOTICE 'Configuration Required:';
    RAISE NOTICE '  1. Install Ollama: https://ollama.ai';
    RAISE NOTICE '  2. Pull models: ollama pull qwen2.5-coder:7b';
    RAISE NOTICE '  3. Pull models: ollama pull llama3:8b';
    RAISE NOTICE '  4. Start server: ollama serve (default: localhost:11434)';
    RAISE NOTICE '';
    RAISE NOTICE 'Total LLMs in System: 7 (5 cloud + 2 local)';
    RAISE NOTICE 'Total Routing Rules: 31 (24 existing + 7 new)';
    RAISE NOTICE '============================================================================';
END $$;

COMMIT;
