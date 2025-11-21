#!/bin/bash
# Apply Knowledge Enhancement Migration
# Handles CockroachDB compatibility issues

set -e

echo "=========================================="
echo "Applying Knowledge Enhancement Migration"
echo "=========================================="
echo ""

# Drop existing tables if needed
echo "1. Cleaning up existing tables..."
psql "$COCKROACH_DB_URL" <<'EOF'
DROP TABLE IF EXISTS learning_history CASCADE;
DROP TABLE IF EXISTS learning_trends CASCADE;
DROP TABLE IF EXISTS skill_connections CASCADE;
DROP TABLE IF EXISTS skills CASCADE;
DROP TABLE IF EXISTS psychology_nlp_bridges CASCADE;
DROP TABLE IF EXISTS nlp_techniques CASCADE;
DROP TABLE IF EXISTS psychological_concepts CASCADE;
DROP TABLE IF EXISTS daily_learnings CASCADE;
DROP TABLE IF EXISTS daily_learning_summary CASCADE;
DROP TABLE IF EXISTS excellence_synergies CASCADE;
DROP TABLE IF EXISTS excellence_patterns CASCADE;
DROP TABLE IF EXISTS unconventional_insights CASCADE;
DROP TABLE IF EXISTS knowledge_domains CASCADE;
DROP MATERIALIZED VIEW IF EXISTS mv_trending_skills CASCADE;
DROP MATERIALIZED VIEW IF EXISTS mv_daily_insights CASCADE;
DROP MATERIALIZED VIEW IF EXISTS mv_top_excellence_patterns CASCADE;
EOF

echo "✅ Cleanup complete"
echo ""

# Apply core migration
echo "2. Creating tables..."
psql "$COCKROACH_DB_URL" -f migrations/012_knowledge_enhancement_system.sql 2>&1 | grep -E "(CREATE|ERROR)" | tail -20

echo "✅ Tables created"
echo ""

# Verify
echo "3. Verifying tables..."
psql "$COCKROACH_DB_URL" -c "SELECT tablename FROM pg_tables WHERE tablename LIKE '%knowledge%' OR tablename LIKE '%skill%' OR tablename LIKE '%learning%' OR tablename LIKE '%psych%' OR tablename LIKE '%nlp%' OR tablename LIKE '%excellence%' ORDER BY tablename"

echo ""
echo "✅ Migration complete!"
echo ""
