#!/bin/bash
# Email Agent Service Monitor

LOG_FILE="logs/email_agent.log"
mkdir -p logs

echo "Starting Email Agent Service Monitor"
echo "Logs: $LOG_FILE"
echo "Press Ctrl+C to stop"
echo ""

./run_email_agent.sh 2>&1 | tee -a "$LOG_FILE"
