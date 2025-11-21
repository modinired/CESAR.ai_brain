#!/bin/bash
# Start CESAR.ai API Server Locally
# Runs from parent directory treating api as a proper Python package

cd "$(dirname "$0")" || exit 1

echo "🚀 Starting CESAR.ai API Server..."
echo "📂 Working directory: $(pwd)"
echo ""

# Override DATABASE_URL for local operation (postgres -> localhost)
export DATABASE_URL="postgresql://mcp_user:4392e1770d58b957825a74c690ee2559@localhost:5432/mcp"

echo "🔧 DATABASE_URL: $DATABASE_URL"
echo ""

# Start uvicorn using Python module syntax to enable relative imports
echo "▶️  Starting uvicorn with package imports..."
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

