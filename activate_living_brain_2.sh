#!/bin/bash
# Living Brain 2.0 Activation Script
# Wires knowledge enhancement into Atlas Prime and starts the system

set -e

echo "=========================================="
echo "CESAR LIVING BRAIN 2.0 - ACTIVATION"
echo "=========================================="
echo ""

cd /Users/modini_red/CESAR.ai_brain/cesar_ecosystem_brain

# Check if routes file exists
if [ ! -f "api/knowledge_cognition_routes.py" ]; then
    echo "❌ ERROR: knowledge_cognition_routes.py not found!"
    exit 1
fi

echo "✅ Knowledge routes found"
echo ""

# Check if we need to wire the router
echo "1️⃣  Checking Atlas Prime integration..."

if grep -q "knowledge_cognition_routes" api/main.py 2>/dev/null; then
    echo "   ✅ Routes already wired in main.py"
elif grep -q "knowledge_cognition_routes" api/atlas_prime.py 2>/dev/null; then
    echo "   ✅ Routes already wired in atlas_prime.py"
else
    echo "   ⚠️  Routes not yet wired"
    echo ""
    echo "   To wire manually, add to api/main.py or api/atlas_prime.py:"
    echo "   ---"
    echo "   from knowledge_cognition_routes import router as knowledge_router"
    echo "   app.include_router(knowledge_router)"
    echo "   ---"
    echo ""
fi

# Check database
echo "2️⃣  Verifying database..."

TABLE_COUNT=$(psql "$COCKROACH_DB_URL" -t -c "SELECT COUNT(*) FROM pg_tables WHERE tablename IN ('knowledge_domains', 'skills', 'daily_learnings')" 2>/dev/null || echo "0")

if [ "$TABLE_COUNT" -eq "3" ]; then
    echo "   ✅ Knowledge tables present in database"
else
    echo "   ❌ Knowledge tables missing - run migration first:"
    echo "   ./apply_knowledge_migration.sh"
    exit 1
fi

# Check if data is seeded
DOMAIN_COUNT=$(psql "$COCKROACH_DB_URL" -t -c "SELECT COUNT(*) FROM knowledge_domains" 2>/dev/null || echo "0")

if [ "$DOMAIN_COUNT" -gt "10" ]; then
    echo "   ✅ Knowledge data seeded ($DOMAIN_COUNT domains)"
else
    echo "   ⚠️  Knowledge data not seeded - run:"
    echo "   python3 seed_knowledge_enhancement.py"
fi

echo ""

# Kill existing backend
echo "3️⃣  Restarting Atlas Prime backend..."

if lsof -ti:8011 > /dev/null 2>&1; then
    echo "   Stopping existing backend on port 8011..."
    lsof -ti:8011 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Start backend
echo "   Starting Atlas Prime on port 8011..."
cd api
nohup uvicorn main:app --reload --host 0.0.0.0 --port 8011 > ../logs/atlas_prime.log 2>&1 &
ATLAS_PID=$!

echo "   ✅ Backend starting (PID: $ATLAS_PID)"
echo ""

# Wait for startup
echo "4️⃣  Waiting for backend to be ready..."
sleep 5

# Test endpoints
echo ""
echo "5️⃣  Testing endpoints..."

# Health check
if curl -s http://localhost:8011/health > /dev/null 2>&1; then
    echo "   ✅ Health check passed"
else
    echo "   ⚠️  Health check failed - check logs/atlas_prime.log"
fi

# Test knowledge endpoints
if curl -s http://localhost:8011/atlas/knowledge/daily-summary > /dev/null 2>&1; then
    echo "   ✅ Knowledge endpoints responding"
else
    echo "   ⚠️  Knowledge endpoints not found - routes may not be wired yet"
    echo "   See instructions above to wire manually"
fi

echo ""
echo "=========================================="
echo "✅ LIVING BRAIN 2.0 ACTIVATION COMPLETE"
echo "=========================================="
echo ""
echo "📊 Available Endpoints:"
echo "  • http://localhost:8011/atlas/knowledge/daily-summary"
echo "  • http://localhost:8011/atlas/knowledge/trending-skills"
echo "  • http://localhost:8011/atlas/knowledge/excellence-patterns"
echo "  • http://localhost:8011/atlas/knowledge/psych-nlp-bridges"
echo "  • http://localhost:8011/atlas/agents/{agent_id}/knowledge-profile"
echo "  • http://localhost:8011/atlas/agents/{agent_id}/cognitive-knowledge-score"
echo ""
echo "📝 Logs:"
echo "  • tail -f logs/atlas_prime.log"
echo ""
echo "🚀 System ready for cognitive health + knowledge tracking!"
echo ""
