-- ============================================================================
-- CESAR.ai Phase A: Foundation - ROLLBACK Script
-- ============================================================================
-- Version: 1.0
-- Date: November 18, 2025
-- Description: Rolls back Phase A migration (001_phase_a_foundation.sql)
--
-- WARNING: This will delete all data in Phase A tables!
-- Take a backup before running this rollback.
-- ============================================================================

BEGIN;

-- Drop materialized views
DROP MATERIALIZED VIEW IF EXISTS routing_effectiveness CASCADE;
DROP MATERIALIZED VIEW IF EXISTS agent_activity_summary CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
DROP FUNCTION IF EXISTS cleanup_expired_blackboard() CASCADE;
DROP FUNCTION IF EXISTS refresh_all_materialized_views() CASCADE;

-- Drop Phase A tables in reverse dependency order
DROP TABLE IF EXISTS tool_invocations CASCADE;
DROP TABLE IF EXISTS events CASCADE;
DROP TABLE IF EXISTS agent_runs CASCADE;
DROP TABLE IF EXISTS blackboard_entries CASCADE;
DROP TABLE IF EXISTS routing_rules CASCADE;
DROP TABLE IF EXISTS tools CASCADE;
DROP TABLE IF EXISTS llms CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Remove added columns from existing tables
ALTER TABLE workflow_executions DROP COLUMN IF EXISTS session_id;

ALTER TABLE learning_reflections
DROP COLUMN IF EXISTS rating,
DROP COLUMN IF EXISTS tags,
DROP COLUMN IF EXISTS session_id,
DROP COLUMN IF EXISTS run_id,
DROP COLUMN IF EXISTS metadata;

COMMIT;

-- Verify rollback
DO $$
BEGIN
    RAISE NOTICE '✅ Phase A rollback completed';
    RAISE NOTICE 'Run SELECT table_name FROM information_schema.tables WHERE table_schema = ''public'' to verify';
END;
$$ LANGUAGE plpgsql;
