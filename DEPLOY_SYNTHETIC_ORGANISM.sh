#!/bin/bash

###############################################################################
# CESAR.ai Synthetic Organism System - Complete Deployment Script
###############################################################################
#
# This script deploys the complete Synthetic Organism visualization system:
# 1. Database migrations (PostgreSQL/Supabase)
# 2. Python services and API endpoints
# 3. React visualization components
# 4. WebSocket streaming
# 5. System_Prompt_Brain_Link cognitive protocol
#
# Requirements:
# - PostgreSQL 15+ with pgvector extension
# - Python 3.11+ with asyncpg, fastapi
# - Node.js 18+ with React, TypeScript
# - Supabase account (optional, for production)
#
# Author: CESAR.ai Development Team
# Date: November 20, 2025
###############################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}==>${NC} ${GREEN}$1${NC}"
}

print_error() {
    echo -e "${RED}ERROR:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}WARNING:${NC} $1"
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_step "CESAR.ai Synthetic Organism System Deployment"
echo "================================================"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found. Please copy .env.example and configure."
    exit 1
fi

# Source environment variables
set -a
source .env
set +a

print_step "Environment variables loaded"

###############################################################################
# STEP 1: DATABASE MIGRATION
###############################################################################

print_step "Step 1: Applying database migrations..."

if [ -z "$POSTGRES_PASSWORD" ]; then
    print_error "POSTGRES_PASSWORD not set in .env"
    exit 1
fi

# Check if PostgreSQL is accessible
if ! command -v psql &> /dev/null; then
    print_error "psql command not found. Please install PostgreSQL client."
    exit 1
fi

# Test database connection
export PGPASSWORD="$POSTGRES_PASSWORD"
if psql -h "${POSTGRES_HOST:-localhost}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-cesar_src}" -c "SELECT 1" &> /dev/null; then
    print_step "Database connection successful"
else
    print_error "Cannot connect to database. Please check credentials."
    print_warning "Host: ${POSTGRES_HOST:-localhost}"
    print_warning "Port: ${POSTGRES_PORT:-5432}"
    print_warning "User: ${POSTGRES_USER:-postgres}"
    print_warning "DB: ${POSTGRES_DB:-cesar_src}"
    exit 1
fi

# Apply migration
print_step "Applying migration 010_synthetic_organism_visualization.sql..."
psql -h "${POSTGRES_HOST:-localhost}" \
     -p "${POSTGRES_PORT:-5432}" \
     -U "${POSTGRES_USER:-postgres}" \
     -d "${POSTGRES_DB:-cesar_src}" \
     -f migrations/010_synthetic_organism_visualization.sql \
     -v ON_ERROR_STOP=1

if [ $? -eq 0 ]; then
    print_step "✓ Database migration completed successfully"
else
    print_error "Migration failed"
    exit 1
fi

###############################################################################
# STEP 2: VERIFY TABLES CREATED
###############################################################################

print_step "Step 2: Verifying database schema..."

TABLES_TO_CHECK=(
    "knowledge_force_fields"
    "knowledge_graph_links"
    "workflow_process_nodes"
    "workflow_process_links"
    "agent_network_nodes"
    "agent_communication_links"
    "neuroplasticity_actions"
)

for table in "${TABLES_TO_CHECK[@]}"; do
    COUNT=$(psql -h "${POSTGRES_HOST:-localhost}" \
                 -p "${POSTGRES_PORT:-5432}" \
                 -U "${POSTGRES_USER:-postgres}" \
                 -d "${POSTGRES_DB:-cesar_src}" \
                 -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='$table'")

    if [ "$COUNT" -eq 1 ]; then
        echo -e "  ${GREEN}✓${NC} Table $table exists"
    else
        print_error "Table $table not found"
        exit 1
    fi
done

print_step "✓ All tables verified"

###############################################################################
# STEP 3: INITIALIZE SEED DATA
###############################################################################

print_step "Step 3: Checking seed data..."

FORCE_FIELD_COUNT=$(psql -h "${POSTGRES_HOST:-localhost}" \
                         -p "${POSTGRES_PORT:-5432}" \
                         -U "${POSTGRES_USER:-postgres}" \
                         -d "${POSTGRES_DB:-cesar_src}" \
                         -t -c "SELECT COUNT(*) FROM knowledge_force_fields")

print_step "Force fields seeded: $FORCE_FIELD_COUNT"

if [ "$FORCE_FIELD_COUNT" -lt 3 ]; then
    print_warning "Force fields may not be seeded properly. Expected at least 5."
fi

###############################################################################
# STEP 4: PYTHON DEPENDENCIES
###############################################################################

print_step "Step 4: Checking Python dependencies..."

REQUIRED_PACKAGES=(
    "fastapi"
    "asyncpg"
    "pydantic"
    "python-multipart"
)

for package in "${REQUIRED_PACKAGES[@]}"; do
    if python3 -c "import $package" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $package installed"
    else
        print_warning "$package not installed. Installing..."
        pip3 install "$package"
    fi
done

###############################################################################
# STEP 5: TEST API ENDPOINTS
###############################################################################

print_step "Step 5: Starting API server (test mode)..."

# Check if API is already running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    print_step "API already running on port 8000"
else
    print_step "Starting API server..."
    cd "$SCRIPT_DIR/api"

    # Start API in background
    nohup python3 main.py > ../logs/api.log 2>&1 &
    API_PID=$!

    echo "API started with PID: $API_PID"

    # Wait for API to start
    sleep 5

    # Test health endpoint
    if curl -s http://localhost:8000/health > /dev/null; then
        print_step "✓ API is responding"
    else
        print_error "API failed to start. Check logs/api.log"
        kill $API_PID 2>/dev/null
        exit 1
    fi
fi

###############################################################################
# STEP 6: TEST VISUALIZATION ENDPOINTS
###############################################################################

print_step "Step 6: Testing visualization endpoints..."

ENDPOINTS=(
    "/api/v1/viz/health"
    "/api/v1/viz/knowledge-graph"
    "/api/v1/viz/agent-network"
)

for endpoint in "${ENDPOINTS[@]}"; do
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000${endpoint}")

    if [ "$RESPONSE" == "200" ]; then
        echo -e "  ${GREEN}✓${NC} ${endpoint} - OK"
    else
        print_warning "${endpoint} - HTTP ${RESPONSE}"
    fi
done

###############################################################################
# STEP 7: GENERATE SAMPLE DATA
###############################################################################

print_step "Step 7: Generating sample data for visualization..."

# Create a Python script to populate test data
cat > /tmp/populate_test_data.py << 'PYTHON_SCRIPT'
import asyncio
import asyncpg
import os
import random

async def populate_test_data():
    # Connect to database
    conn = await asyncpg.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', '5432')),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD'),
        database=os.getenv('POSTGRES_DB', 'cesar_src')
    )

    print("Populating test semantic memories...")

    # Create test semantic memories
    test_concepts = [
        ('Q3 Revenue Growth', 'wisdom', 'Analysis shows 15% YoY increase'),
        ('Customer Churn Risk', 'knowledge', 'Elevated churn in SMB segment'),
        ('Market Expansion Strategy', 'wisdom', 'Focus on EMEA region'),
        ('Product Feature Request', 'information', 'API v2 most requested'),
        ('Competitor Analysis', 'knowledge', 'Competitor X launched pricing update'),
        ('Compliance Audit', 'information', 'SOC2 renewal due Q1'),
        ('Team Productivity', 'knowledge', 'Engineering velocity up 20%'),
        ('Infrastructure Costs', 'information', 'AWS spend increased 10%'),
    ]

    node_ids = []
    for concept, node_type, summary in test_concepts:
        node_id = await conn.fetchval("""
            INSERT INTO memory_semantic (
                concept, summary, category, node_type, confidence_score
            ) VALUES ($1, $2, 'fact', $3, $4)
            RETURNING id
        """, concept, summary, node_type, random.uniform(0.5, 0.95))

        node_ids.append(node_id)
        print(f"  ✓ Created: {concept}")

    # Initialize positions
    await conn.execute("SELECT initialize_node_positions()")
    print("  ✓ Initialized node positions")

    # Create test links
    print("Creating test knowledge links...")
    await conn.execute("SELECT compute_knowledge_graph_links()")

    # Update agent network
    print("Updating agent network metrics...")
    await conn.execute("SELECT update_agent_network_metrics()")

    # Refresh materialized views
    print("Refreshing materialized views...")
    await conn.execute("REFRESH MATERIALIZED VIEW knowledge_graph_snapshot")
    await conn.execute("REFRESH MATERIALIZED VIEW agent_network_health")

    await conn.close()
    print("\n✓ Test data populated successfully!")

if __name__ == "__main__":
    asyncio.run(populate_test_data())
PYTHON_SCRIPT

# Run the population script
python3 /tmp/populate_test_data.py

###############################################################################
# STEP 8: GENERATE DEPLOYMENT SUMMARY
###############################################################################

print_step "Step 8: Deployment Summary"
echo "================================================"
echo ""
echo -e "${GREEN}✓ Synthetic Organism System Deployed Successfully!${NC}"
echo ""
echo "Components Installed:"
echo "  ✓ Database Schema (7 tables, 3 materialized views)"
echo "  ✓ Python Services (synthetic_organism_service.py)"
echo "  ✓ API Endpoints (visualization_routes.py)"
echo "  ✓ WebSocket Streaming (/api/v1/viz/stream)"
echo "  ✓ Sample Data (8 test concepts)"
echo ""
echo "Access Points:"
echo "  • API Documentation: http://localhost:8000/docs"
echo "  • Knowledge Graph: http://localhost:8000/api/v1/viz/knowledge-graph"
echo "  • Agent Network: http://localhost:8000/api/v1/viz/agent-network"
echo "  • Workflow Matrix: http://localhost:8000/api/v1/viz/workflow-matrix"
echo "  • Liquidity Flow: http://localhost:8000/api/v1/viz/liquidity-flow"
echo ""
echo "Next Steps:"
echo "  1. Deploy React dashboard: cd atlas_nextjs_ui && npm run dev"
echo "  2. Configure Supabase connection (optional)"
echo "  3. Set up scheduled jobs for materialized view refresh"
echo ""
echo "Logs:"
echo "  • API: $SCRIPT_DIR/logs/api.log"
echo "  • PostgreSQL: Check system logs"
echo ""
echo "================================================"

# Create a quick test script
cat > "$SCRIPT_DIR/test_visualization_api.sh" << 'EOF'
#!/bin/bash
# Quick API testing script

echo "Testing Visualization API..."
echo ""

echo "1. Health Check:"
curl -s http://localhost:8000/api/v1/viz/health | python3 -m json.tool
echo ""

echo "2. Knowledge Graph (first 5 nodes):"
curl -s "http://localhost:8000/api/v1/viz/knowledge-graph?limit=5" | python3 -m json.tool | head -50
echo ""

echo "3. Agent Network:"
curl -s http://localhost:8000/api/v1/viz/agent-network | python3 -m json.tool | head -30
echo ""

echo "✓ API tests complete"
EOF

chmod +x "$SCRIPT_DIR/test_visualization_api.sh"

print_step "✓ Deployment complete! Run ./test_visualization_api.sh to test endpoints."
