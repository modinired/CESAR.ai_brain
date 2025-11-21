#!/bin/bash
# Email Agent Service Launcher

cd "$(dirname "$0")"
source .env.email_agent 2>/dev/null || true

export EMAIL_AGENT_USER
export EMAIL_AGENT_PASSWORD
export POSTGRES_HOST
export POSTGRES_PORT
export POSTGRES_DB
export POSTGRES_USER
export POSTGRES_PASSWORD
export ORCHESTRATOR_API

python3 services/email_agent_service.py
