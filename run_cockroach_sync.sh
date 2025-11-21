#!/bin/bash
cd "$(dirname "$0")"

# Load environment from both .env and .env.cockroach
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
fi

if [ -f .env.cockroach ]; then
    export $(cat .env.cockroach | grep -v '^#' | grep -v '^$' | xargs)
fi

echo "Starting CockroachDB sync..."
python3 sync_to_cockroach.py
