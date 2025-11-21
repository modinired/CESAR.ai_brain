#!/bin/bash
# Launch Supabase Sync Scheduler
# Loads environment and runs the daily sync scheduler

cd "$(dirname "$0")"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Loaded environment variables from .env"
fi

# Launch scheduler
echo "🔄 Starting Supabase Sync Scheduler..."
python3 services/supabase_sync_scheduler.py
