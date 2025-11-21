#!/bin/bash
#
# CESAR Ecosystem: Service Launcher
# ==================================
# Starts all core services for the live system:
# 1. API Server (CockroachDB backend)
# 2. Bidirectional Sync
# 3. Hourly Data Ingestion
# 4. Weekly LoRA Training Prep

set -e

ECOSYSTEM_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$ECOSYSTEM_DIR/logs"

# Create log directory
mkdir -p "$LOG_DIR"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  CESAR ECOSYSTEM: STARTING ALL SERVICES                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Function to check if a service is already running
check_running() {
    local name=$1
    local pattern=$2
    if pgrep -f "$pattern" > /dev/null; then
        echo "⚠️  $name is already running (PID: $(pgrep -f "$pattern"))"
        return 0
    else
        return 1
    fi
}

# 1. Start API Server
echo "[1/4] Starting API Server..."
if ! check_running "API Server" "api/main.py"; then
    cd "$ECOSYSTEM_DIR"
    nohup python3 api/main.py > "$LOG_DIR/api_server.log" 2>&1 &
    API_PID=$!
    echo "   ✅ API Server started (PID: $API_PID)"
    echo "   📋 Logs: $LOG_DIR/api_server.log"
    sleep 3

    # Check if it started successfully
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "   ✅ API health check passed"
    else
        echo "   ⚠️  API health check failed (may still be starting...)"
    fi
else
    echo "   ℹ️  Skipping API Server (already running)"
fi

# 2. Start Bidirectional Sync
echo ""
echo "[2/4] Starting Bidirectional Sync..."
if ! check_running "Bidirectional Sync" "sync_bidirectional.py"; then
    cd "$ECOSYSTEM_DIR"
    nohup python3 sync_bidirectional.py > "$LOG_DIR/sync_bidirectional.log" 2>&1 &
    SYNC_PID=$!
    echo "   ✅ Sync daemon started (PID: $SYNC_PID)"
    echo "   📋 Logs: $LOG_DIR/sync_bidirectional.log"
else
    echo "   ℹ️  Skipping Sync (already running)"
fi

# 3. Start Hourly Data Ingestion
echo ""
echo "[3/4] Starting Hourly Data Ingestion..."
if ! check_running "Hourly Ingestion" "services/hourly_data_ingestion.py"; then
    cd "$ECOSYSTEM_DIR"
    nohup python3 services/hourly_data_ingestion.py > "$LOG_DIR/hourly_ingestion.log" 2>&1 &
    INGEST_PID=$!
    echo "   ✅ Ingestion service started (PID: $INGEST_PID)"
    echo "   📋 Logs: $LOG_DIR/hourly_ingestion.log"
    echo "   ⏰ Runs every hour"
else
    echo "   ℹ️  Skipping Ingestion (already running)"
fi

# 4. Schedule Weekly LoRA Training (using cron)
echo ""
echo "[4/4] Setting up LoRA Training Schedule..."

# Check if crontab entry exists
CRON_ENTRY="0 2 * * 0 cd $ECOSYSTEM_DIR && python3 services/brain_lora_trainer.py >> $LOG_DIR/lora_training.log 2>&1"

if crontab -l 2>/dev/null | grep -q "brain_lora_trainer.py"; then
    echo "   ℹ️  LoRA training already scheduled in crontab"
else
    echo "   📅 Adding weekly LoRA training to crontab (Sundays at 2 AM)..."
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    echo "   ✅ Scheduled weekly training"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  ✅ ALL SERVICES STARTED                                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Service Status:"
echo "   1. API Server:      http://localhost:8000"
echo "   2. API Docs:        http://localhost:8000/docs"
echo "   3. Health Check:    http://localhost:8000/health"
echo ""
echo "📋 Logs:"
echo "   tail -f $LOG_DIR/api_server.log"
echo "   tail -f $LOG_DIR/sync_bidirectional.log"
echo "   tail -f $LOG_DIR/hourly_ingestion.log"
echo ""
echo "🛑 To stop all services:"
echo "   pkill -f 'python3 api/main.py'"
echo "   pkill -f 'python3 sync_bidirectional.py'"
echo "   pkill -f 'python3 services/hourly_data_ingestion.py'"
echo ""
echo "📅 Scheduled Tasks:"
echo "   - Hourly: Data ingestion (runs continuously)"
echo "   - Weekly: LoRA training prep (Sundays 2 AM)"
echo ""
