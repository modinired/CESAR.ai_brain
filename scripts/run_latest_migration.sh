#!/usr/bin/env bash
# Apply the latest migration (010_enhanced_databrain.sql) to the configured Cockroach/Postgres URL.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

MIG="$ROOT_DIR/migrations/010_enhanced_databrain.sql"

if [ ! -f "$MIG" ]; then
  echo "Migration file not found: $MIG"
  exit 1
fi

if [ -z "${COCKROACH_DB_URL:-}" ] && [ -z "${DATABASE_URL:-}" ]; then
  echo "Set COCKROACH_DB_URL or DATABASE_URL to run migrations."
  exit 1
fi

DB_URL="${COCKROACH_DB_URL:-$DATABASE_URL}"

echo "Applying migration to: $DB_URL"
psql "$DB_URL" -f "$MIG"
