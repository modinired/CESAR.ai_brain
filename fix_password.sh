#!/bin/bash
#
# Quick Fix: Update CockroachDB Password
# =======================================

echo "════════════════════════════════════════════════════════════════"
echo "🔐 CockroachDB Password Update Tool"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Please follow these steps:"
echo ""
echo "1. Go to: https://cockroachlabs.cloud/"
echo "2. Click on your cluster: cesar-ecosystem-10552"
echo "3. Click 'Connect' button"
echo "4. Click 'General connection string'"
echo "5. Copy the ENTIRE connection string"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Paste your FULL connection string here:"
echo "(It should start with: postgresql://modini:...)"
echo ""
read -r FULL_URL

# Validate format
if [[ ! "$FULL_URL" =~ ^postgresql:// ]]; then
    echo ""
    echo "❌ Error: Invalid format. Must start with 'postgresql://'"
    echo "   Example: postgresql://modini:password@host:26257/defaultdb"
    exit 1
fi

# Backup old file
cp .env.cockroach .env.cockroach.backup.$(date +%Y%m%d_%H%M%S)
echo "✅ Backed up old .env.cockroach"

# Write new connection string
cat > .env.cockroach << EOF
# CockroachDB Connection
# Updated: $(date)
COCKROACH_DB_URL=$FULL_URL
EOF

echo "✅ Updated .env.cockroach"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🧪 Testing new connection..."
echo "════════════════════════════════════════════════════════════════"
echo ""

# Test connection
if python3 test_cockroach_connection.py; then
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "✅ SUCCESS! Connection works!"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "Next steps:"
    echo "1. Run: ./apply_migrations_cockroach.sh"
    echo "2. Run: ./run_cockroach_sync.sh"
    echo ""
else
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "❌ Connection still failing. Check the error above."
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "Your old .env.cockroach has been backed up."
    echo "You can restore it with:"
    echo "  cp .env.cockroach.backup.* .env.cockroach"
    echo ""
    exit 1
fi
