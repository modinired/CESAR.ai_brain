#!/bin/bash
###############################################################################
# CESAR.ai Hippocampal Replay Scheduler
###############################################################################
#
# Runs nightly to consolidate high-value memories into LLM training data.
#
# Schedule via cron:
#   0 2 * * * /path/to/schedule_hippocampal_replay.sh
#   (Runs every night at 2 AM)
#
# Or trigger via N8n workflow automation
#
###############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🧠 CESAR.ai Hippocampal Replay Scheduler"
echo "========================================"
echo ""

# Load environment
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
    echo "✓ Environment loaded"
else
    echo "❌ .env file not found"
    exit 1
fi

# Verify database connection
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not set in .env"
    exit 1
fi

# Create output directory
OUTPUT_DIR="$PROJECT_ROOT/replay_out"
mkdir -p "$OUTPUT_DIR"
echo "✓ Output directory: $OUTPUT_DIR"

# Run hippocampal replay
echo ""
echo "Starting memory consolidation..."
python3 "$PROJECT_ROOT/services/hippocampal_replay_service.py"

# Archive old training data (keep last 7 days)
echo ""
echo "Archiving old training data..."
find "$OUTPUT_DIR" -name "*.jsonl" -mtime +7 -exec rm {} \;

echo ""
echo "✅ Hippocampal replay complete"
echo "📁 Training data ready in: $OUTPUT_DIR"
echo ""

# Optional: Trigger fine-tune job (uncomment if you have automated fine-tuning)
# if [ -f "$PROJECT_ROOT/scripts/trigger_finetune.sh" ]; then
#     echo "🚀 Triggering automated fine-tune job..."
#     bash "$PROJECT_ROOT/scripts/trigger_finetune.sh"
# fi
