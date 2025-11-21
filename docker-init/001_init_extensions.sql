-- Initialize PostgreSQL extensions required for multi-agent learning ecosystem
-- This runs automatically when the database container starts

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Enable vector similarity search (pgvector)
-- Note: Ensure pgvector is installed in your PostgreSQL image
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname='vector') THEN
        CREATE EXTENSION vector;
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'pgvector extension not available. Please install it for vector operations.';
END $$;

-- Enable full-text search enhancements
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Enable better JSON operations
CREATE EXTENSION IF NOT EXISTS btree_gin;

DO $$
BEGIN
    RAISE NOTICE 'Extensions initialized successfully';
END $$;
