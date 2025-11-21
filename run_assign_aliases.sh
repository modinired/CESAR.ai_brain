#!/bin/bash
cd "$(dirname "$0")"

# Load environment
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

python3 assign_mob_aliases.py
