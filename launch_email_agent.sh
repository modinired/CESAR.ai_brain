#!/bin/bash
# Email Agent Launcher
cd "$(dirname "$0")"

# Load environment
if [ -f .env.email_agent ]; then
    export $(cat .env.email_agent | grep -v '^#' | xargs)
fi

python3 services/email_agent_service.py
