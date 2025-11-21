#!/bin/bash
#
# Update CockroachDB Connection String
# =====================================

echo "Current connection string in .env.cockroach:"
cat .env.cockroach

echo ""
echo "Please paste your NEW CockroachDB connection string:"
echo "(Format: postgresql://user:password@host:26257/defaultdb?sslmode=verify-full)"
read -r NEW_URL

# Backup old file
cp .env.cockroach .env.cockroach.backup

# Write new URL
cat > .env.cockroach << EOF
# CockroachDB Connection
COCKROACH_DB_URL=$NEW_URL
EOF

echo ""
echo "✅ Updated .env.cockroach"
echo ""
echo "Testing new connection..."
python3 test_cockroach_connection.py
