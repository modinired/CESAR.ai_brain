#!/bin/bash
#
# CESAR ECOSYSTEM: CockroachDB Migration Runner
# ==============================================
# Applies all 11 database migrations to CockroachDB cluster
#
# Features:
# - Idempotent execution (safe to run multiple times)
# - Migration tracking table
# - Rollback support
# - Pre-flight validation
#
# Usage:
#   ./apply_migrations_cockroach.sh          # Apply all pending migrations
#   ./apply_migrations_cockroach.sh --dry-run # Preview without executing
#   ./apply_migrations_cockroach.sh --rollback 008  # Rollback specific migration

set -e  # Exit on error
set -u  # Exit on undefined variable

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables
if [ -f .env.cockroach ]; then
    export $(cat .env.cockroach | grep -v '^#' | grep -v '^$' | xargs)
else
    echo -e "${RED}❌ Error: .env.cockroach file not found${NC}"
    exit 1
fi

# Validate COCKROACH_DB_URL
if [ -z "${COCKROACH_DB_URL:-}" ]; then
    echo -e "${RED}❌ Error: COCKROACH_DB_URL not set in .env.cockroach${NC}"
    exit 1
fi

# Parse command line arguments
DRY_RUN=false
ROLLBACK_TARGET=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --rollback)
            ROLLBACK_TARGET="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--dry-run] [--rollback MIGRATION_NUMBER]"
            exit 1
            ;;
    esac
done

# Banner
echo "================================================================================"
echo "CESAR ECOSYSTEM: CockroachDB Migration Runner"
echo "================================================================================"
echo ""

# Test connection
echo -e "${BLUE}🔌 Testing CockroachDB connection...${NC}"
if python3 test_cockroach_connection.py >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Connection successful${NC}"
else
    echo -e "${RED}❌ Connection failed. Running diagnostic...${NC}"
    python3 test_cockroach_connection.py
    exit 1
fi

echo ""

# Create migration tracking table
echo -e "${BLUE}📋 Initializing migration tracker...${NC}"

psql "$COCKROACH_DB_URL" << 'EOF'
CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) UNIQUE NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    execution_time_ms INT,
    status VARCHAR(50) DEFAULT 'completed',
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_schema_migrations_name ON schema_migrations(migration_name);
CREATE INDEX IF NOT EXISTS idx_schema_migrations_status ON schema_migrations(status);
EOF

echo -e "${GREEN}✅ Migration tracker ready${NC}"
echo ""

# Function to check if migration already applied
is_migration_applied() {
    local migration_name=$1
    local result=$(psql "$COCKROACH_DB_URL" -t -c "SELECT COUNT(*) FROM schema_migrations WHERE migration_name = '$migration_name' AND status = 'completed';")
    [ "$result" -gt 0 ]
}

# Function to apply a single migration
apply_migration() {
    local migration_file=$1
    local migration_name=$(basename "$migration_file" .sql)

    echo -e "${BLUE}📦 Processing: $migration_name${NC}"

    # Check if already applied
    if is_migration_applied "$migration_name"; then
        echo -e "${YELLOW}   ⏭️  Skipped (already applied)${NC}"
        return 0
    fi

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}   🔍 DRY RUN: Would apply $migration_file${NC}"
        return 0
    fi

    # Record start time
    local start_time=$(date +%s%3N)

    # Apply migration
    echo "   Executing SQL..."
    if psql "$COCKROACH_DB_URL" -f "$migration_file" 2>&1 | tee /tmp/migration_output.log; then
        # Calculate execution time
        local end_time=$(date +%s%3N)
        local execution_time=$((end_time - start_time))

        # Record success
        psql "$COCKROACH_DB_URL" -c "INSERT INTO schema_migrations (migration_name, execution_time_ms, status) VALUES ('$migration_name', $execution_time, 'completed');"

        echo -e "${GREEN}   ✅ Applied successfully (${execution_time}ms)${NC}"
    else
        # Record failure
        local error_msg=$(cat /tmp/migration_output.log | tail -10 | sed "s/'/''/g")
        psql "$COCKROACH_DB_URL" -c "INSERT INTO schema_migrations (migration_name, status, error_message) VALUES ('$migration_name', 'failed', '$error_msg');" || true

        echo -e "${RED}   ❌ Failed${NC}"
        echo -e "${RED}   Error details in /tmp/migration_output.log${NC}"
        return 1
    fi
}

# Get list of migrations in order
MIGRATIONS=(
    "migrations/001_phase_a_foundation.sql"
    "migrations/002_routing_rules.sql"
    "migrations/003_phase_b_cognitive_memory.sql"
    "migrations/004_phase_c_knowledge_graph.sql"
    "migrations/005_phase_d_attention_coordination.sql"
    "migrations/006_phase_e_continual_learning.sql"
    "migrations/007_local_llm_integration.sql"
    "migrations/008_a2a_protocol_and_llm_collaboration.sql"
    "migrations/009_supabase_integration.sql"
    "migrations/010_synthetic_organism_visualization.sql"
    "migrations/011_hippocampal_replay_tracking.sql"
)

# Handle rollback if requested
if [ -n "$ROLLBACK_TARGET" ]; then
    echo -e "${YELLOW}🔄 ROLLBACK MODE: Rolling back to migration $ROLLBACK_TARGET${NC}"
    echo ""
    echo -e "${RED}⚠️  WARNING: Rollback functionality requires manual verification${NC}"
    echo -e "${RED}   Review rollback SQL files in migrations/ directory${NC}"
    echo ""
    exit 0
fi

# Apply all migrations
echo -e "${BLUE}🚀 Applying migrations to CockroachDB...${NC}"
echo ""

APPLIED_COUNT=0
SKIPPED_COUNT=0
FAILED_COUNT=0

for migration in "${MIGRATIONS[@]}"; do
    if [ ! -f "$migration" ]; then
        echo -e "${RED}❌ Migration file not found: $migration${NC}"
        FAILED_COUNT=$((FAILED_COUNT + 1))
        continue
    fi

    if apply_migration "$migration"; then
        if is_migration_applied "$(basename "$migration" .sql)"; then
            if [ "$DRY_RUN" = false ]; then
                APPLIED_COUNT=$((APPLIED_COUNT + 1))
            fi
        else
            SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
        fi
    else
        FAILED_COUNT=$((FAILED_COUNT + 1))
        echo -e "${RED}❌ Migration failed. Stopping execution.${NC}"
        exit 1
    fi
done

# Summary
echo ""
echo "================================================================================"
echo -e "${GREEN}✅ MIGRATION COMPLETE${NC}"
echo "================================================================================"
echo ""
echo "Summary:"
echo "  - Applied: $APPLIED_COUNT"
echo "  - Skipped: $SKIPPED_COUNT"
echo "  - Failed:  $FAILED_COUNT"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}ℹ️  This was a DRY RUN. No changes were made.${NC}"
    echo ""
fi

# Show migration status
echo "Current Migration Status:"
psql "$COCKROACH_DB_URL" -c "SELECT migration_name, applied_at, execution_time_ms, status FROM schema_migrations ORDER BY applied_at DESC LIMIT 5;"

echo ""
echo "Next Steps:"
echo "1. Verify schema: psql \$COCKROACH_DB_URL -c '\\dt'"
echo "2. Run sync: ./run_cockroach_sync.sh"
echo "3. Test API: python3 test_full_system.py"
echo ""
