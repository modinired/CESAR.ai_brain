#!/bin/bash
# CESAR Dashboard Launcher with Environment Variables
# Loads .env and launches PyQt6 dashboard with real database connections

cd "$(dirname "$0")"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Loaded environment variables from .env"
else
    echo "⚠️  Warning: .env file not found"
fi

# Launch dashboard
echo "🏛️  Launching CESAR Multi-Agent MCP Dashboard..."
echo "a Terry Dellmonaco Co."
echo ""

python3 cesar_mcp_dashboard_fixed.py
