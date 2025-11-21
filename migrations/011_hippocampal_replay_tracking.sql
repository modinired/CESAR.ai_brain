-- ============================================================================
-- CESAR.ai Phase I: Hippocampal Replay Tracking
-- ============================================================================
-- Migration: 011_hippocampal_replay_tracking.sql
-- Purpose: Track LLM fine-tuning dataset generation (memory consolidation)
-- Dependencies: 010_synthetic_organism_visualization.sql
-- Author: CESAR.ai Development Team
-- Date: November 20, 2025
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. MEMORY CONSOLIDATIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS memory_consolidations (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    consolidation_type TEXT NOT NULL CHECK (consolidation_type IN (
        'hippocampal_replay',
        'knowledge_distillation',
        'curriculum_learning',
        'continual_learning'
    )),

    -- Metrics
    memories_processed INTEGER NOT NULL DEFAULT 0,
    training_pairs_generated INTEGER NOT NULL DEFAULT 0,

    -- Status
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed')),

    -- Metadata
    metadata JSONB,
    output_files JSONB, -- {model_id: filepath}

    -- Timestamps
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_consolidations_type_status ON memory_consolidations(consolidation_type, status);
CREATE INDEX idx_consolidations_started_at ON memory_consolidations(started_at DESC);
CREATE INDEX idx_consolidations_metadata ON memory_consolidations USING gin(metadata);

COMMENT ON TABLE memory_consolidations IS 'Tracks LLM fine-tuning dataset generation events';

-- ============================================================================
-- 2. MODEL REGISTRY TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS model_registry (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id TEXT NOT NULL UNIQUE,

    -- Model Details
    model_name TEXT NOT NULL,
    description TEXT,
    format TEXT NOT NULL, -- 'alpaca', 'chatml', etc.
    max_seq_len INTEGER NOT NULL,
    specialization TEXT, -- 'code_generation', 'general_reasoning', etc.

    -- Training Stats
    total_training_pairs INTEGER DEFAULT 0,
    last_trained_at TIMESTAMPTZ,

    -- Configuration
    config JSONB,

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_model_registry_active ON model_registry(is_active);
CREATE INDEX idx_model_registry_model_id ON model_registry(model_id);

COMMENT ON TABLE model_registry IS 'Registry of local LLMs available for fine-tuning';

-- Seed default models
INSERT INTO model_registry (model_id, model_name, description, format, max_seq_len, specialization, config)
VALUES
    (
        'qwen2_5_coder',
        'Qwen2.5 Coder',
        'Local Qwen2.5 Coder model (code-focused)',
        'alpaca',
        4096,
        'code_generation',
        '{"lora_rank": 16, "lora_alpha": 32, "learning_rate": 0.0002}'::jsonb
    ),
    (
        'llama_3',
        'Llama 3',
        'Local Llama 3 base / instruct model',
        'alpaca',
        8192,
        'general_reasoning',
        '{"lora_rank": 16, "lora_alpha": 32, "learning_rate": 0.0001}'::jsonb
    )
ON CONFLICT (model_id) DO NOTHING;

-- ============================================================================
-- 3. TRAINING DATASET SAMPLES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS training_dataset_samples (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    consolidation_id uuid REFERENCES memory_consolidations(id) ON DELETE CASCADE,
    model_id TEXT REFERENCES model_registry(model_id),

    -- Training Sample (Alpaca format)
    instruction TEXT NOT NULL,
    input TEXT,
    output TEXT NOT NULL,

    -- Source Metadata
    source_node_id uuid REFERENCES memory_semantic(id),
    specialization TEXT,

    -- Quality Metrics
    confidence_score NUMERIC(5,4),
    validation_loss NUMERIC(10,6),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_training_samples_consolidation ON training_dataset_samples(consolidation_id);
CREATE INDEX idx_training_samples_model ON training_dataset_samples(model_id);
CREATE INDEX idx_training_samples_source ON training_dataset_samples(source_node_id);

COMMENT ON TABLE training_dataset_samples IS 'Individual training samples for validation and analysis';

-- ============================================================================
-- 4. MATERIALIZED VIEW: CONSOLIDATION SUMMARY
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS consolidation_summary AS
SELECT
    model_id,
    COUNT(DISTINCT consolidation_id) as total_consolidations,
    SUM(memories_processed) as total_memories_processed,
    SUM(training_pairs_generated) as total_training_pairs,
    MAX(started_at) as last_consolidation_at,
    AVG(training_pairs_generated) as avg_pairs_per_run
FROM memory_consolidations mc
JOIN model_registry mr ON true
WHERE mc.status = 'completed'
GROUP BY model_id;

CREATE UNIQUE INDEX idx_consolidation_summary_model ON consolidation_summary(model_id);

COMMENT ON MATERIALIZED VIEW consolidation_summary IS 'Aggregated consolidation statistics per model';

-- ============================================================================
-- 5. FUNCTIONS & TRIGGERS
-- ============================================================================

-- Auto-update timestamp trigger
CREATE OR REPLACE FUNCTION update_consolidation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();

    -- Auto-set completed_at when status changes to completed
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        NEW.completed_at = NOW();
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_consolidation_timestamp
    BEFORE UPDATE ON memory_consolidations
    FOR EACH ROW
    EXECUTE FUNCTION update_consolidation_timestamp();

-- Update model registry stats after consolidation
CREATE OR REPLACE FUNCTION update_model_training_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' THEN
        -- Update each model's training stats
        UPDATE model_registry
        SET
            total_training_pairs = total_training_pairs + (
                SELECT COUNT(*)
                FROM training_dataset_samples
                WHERE consolidation_id = NEW.id
                  AND model_id = model_registry.model_id
            ),
            last_trained_at = NEW.completed_at
        WHERE model_id IN (
            SELECT DISTINCT model_id
            FROM training_dataset_samples
            WHERE consolidation_id = NEW.id
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_model_stats
    AFTER UPDATE ON memory_consolidations
    FOR EACH ROW
    WHEN (NEW.status = 'completed' AND OLD.status != 'completed')
    EXECUTE FUNCTION update_model_training_stats();

-- ============================================================================
-- 6. ROW LEVEL SECURITY (Supabase Compatible)
-- ============================================================================

ALTER TABLE memory_consolidations ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_registry ENABLE ROW LEVEL SECURITY;
ALTER TABLE training_dataset_samples ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read
CREATE POLICY "Allow authenticated read access to consolidations"
ON memory_consolidations FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow authenticated read access to model registry"
ON model_registry FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow authenticated read access to training samples"
ON training_dataset_samples FOR SELECT TO authenticated USING (true);

-- Service role can do everything
CREATE POLICY "Service role can manage consolidations"
ON memory_consolidations FOR ALL TO service_role
USING (true) WITH CHECK (true);

CREATE POLICY "Service role can manage model registry"
ON model_registry FOR ALL TO service_role
USING (true) WITH CHECK (true);

CREATE POLICY "Service role can manage training samples"
ON training_dataset_samples FOR ALL TO service_role
USING (true) WITH CHECK (true);

-- ============================================================================
-- 7. HELPER FUNCTIONS
-- ============================================================================

-- Function to initiate a new consolidation
CREATE OR REPLACE FUNCTION initiate_consolidation(
    p_consolidation_type TEXT,
    p_metadata JSONB DEFAULT '{}'::jsonb
)
RETURNS uuid AS $$
DECLARE
    v_consolidation_id uuid;
BEGIN
    INSERT INTO memory_consolidations (consolidation_type, status, metadata)
    VALUES (p_consolidation_type, 'running', p_metadata)
    RETURNING id INTO v_consolidation_id;

    RETURN v_consolidation_id;
END;
$$ LANGUAGE plpgsql;

-- Function to complete a consolidation
CREATE OR REPLACE FUNCTION complete_consolidation(
    p_consolidation_id uuid,
    p_memories_processed INTEGER,
    p_training_pairs_generated INTEGER,
    p_output_files JSONB
)
RETURNS void AS $$
BEGIN
    UPDATE memory_consolidations
    SET
        status = 'completed',
        memories_processed = p_memories_processed,
        training_pairs_generated = p_training_pairs_generated,
        output_files = p_output_files,
        completed_at = NOW()
    WHERE id = p_consolidation_id;

    -- Refresh materialized view
    REFRESH MATERIALIZED VIEW CONCURRENTLY consolidation_summary;
END;
$$ LANGUAGE plpgsql;

COMMIT;

-- ============================================================================
-- VERIFICATION NOTICE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'CESAR.ai Phase I: Hippocampal Replay Tracking - COMPLETE';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'Tables Created: 3';
    RAISE NOTICE '  - memory_consolidations';
    RAISE NOTICE '  - model_registry';
    RAISE NOTICE '  - training_dataset_samples';
    RAISE NOTICE '';
    RAISE NOTICE 'Materialized Views: 1';
    RAISE NOTICE '  - consolidation_summary';
    RAISE NOTICE '';
    RAISE NOTICE 'Models Registered: 2';
    RAISE NOTICE '  - qwen2_5_coder (code generation)';
    RAISE NOTICE '  - llama_3 (general reasoning)';
    RAISE NOTICE '';
    RAISE NOTICE 'Row Level Security: ENABLED';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'Ready for: Nightly Memory Consolidation → LLM Fine-Tuning Pipeline';
    RAISE NOTICE '============================================================================';
END $$;
