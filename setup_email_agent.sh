#!/bin/bash
#
# Email Agent Service Setup Script
# Sets up the email-based agent communication system
#

set -e  # Exit on error

echo "========================================"
echo "CESAR.ai Email Agent Service Setup"
echo "========================================"
echo ""

# Check Python version
echo "1. Checking Python version..."
python3 --version || { echo "❌ Python 3 not found"; exit 1; }

# Install required Python packages
echo ""
echo "2. Installing Python dependencies..."
pip3 install --quiet --upgrade \
    httpx \
    psycopg[binary] \
    python-dotenv \
    || { echo "❌ Failed to install dependencies"; exit 1; }

echo "✅ Dependencies installed"

# Check if .env.email_agent exists
echo ""
echo "3. Checking email agent configuration..."
if [ ! -f ".env.email_agent" ]; then
    echo "⚠️  .env.email_agent not found"
    echo "   Creating from example..."
    cp .env.email_agent.example .env.email_agent
    echo "   ⚠️  IMPORTANT: Edit .env.email_agent and add EMAIL_AGENT_PASSWORD"
    echo "   To generate an App Password for Gmail:"
    echo "   1. Go to https://myaccount.google.com/apppasswords"
    echo "   2. Sign in with ace.llc.nyc@gmail.com"
    echo "   3. Create a new App Password for 'Mail'"
    echo "   4. Copy the 16-character password to .env.email_agent"
    echo ""
    read -p "   Press Enter after you've set EMAIL_AGENT_PASSWORD..."
fi

# Verify database connection
echo ""
echo "4. Verifying database connection..."
source .env.email_agent 2>/dev/null || true

PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "SELECT 1;" > /dev/null 2>&1 \
    && echo "✅ Database connection successful" \
    || { echo "❌ Database connection failed"; exit 1; }

# Verify required tables exist
echo ""
echo "5. Verifying database schema..."
REQUIRED_TABLES="sessions agent_runs events memory_episodic learning_reflections"
for table in $REQUIRED_TABLES; do
    PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
        -c "SELECT 1 FROM information_schema.tables WHERE table_name='$table';" | grep -q '1 row' \
        && echo "   ✅ Table: $table" \
        || { echo "   ❌ Missing table: $table"; exit 1; }
done

# Test email configuration
echo ""
echo "6. Testing email configuration..."
python3 -c "
import os
from dotenv import load_dotenv
from imaplib import IMAP4_SSL

load_dotenv('.env.email_agent')

user = os.getenv('EMAIL_AGENT_USER')
password = os.getenv('EMAIL_AGENT_PASSWORD')

if not password:
    print('❌ EMAIL_AGENT_PASSWORD not set')
    exit(1)

try:
    imap = IMAP4_SSL('imap.gmail.com')
    imap.login(user, password)
    imap.logout()
    print(f'✅ Email authentication successful for {user}')
except Exception as e:
    print(f'❌ Email authentication failed: {e}')
    exit(1)
" || { echo "⚠️  Email authentication failed - check credentials"; }

# Create systemd service file (optional)
echo ""
echo "7. Creating service launcher..."
cat > run_email_agent.sh << 'EOF'
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
EOF

chmod +x run_email_agent.sh
echo "✅ Created run_email_agent.sh"

# Create monitoring script
echo ""
echo "8. Creating monitoring script..."
cat > monitor_email_agent.sh << 'EOF'
#!/bin/bash
# Email Agent Service Monitor

LOG_FILE="logs/email_agent.log"
mkdir -p logs

echo "Starting Email Agent Service Monitor"
echo "Logs: $LOG_FILE"
echo "Press Ctrl+C to stop"
echo ""

./run_email_agent.sh 2>&1 | tee -a "$LOG_FILE"
EOF

chmod +x monitor_email_agent.sh
echo "✅ Created monitor_email_agent.sh"

# Summary
echo ""
echo "========================================"
echo "✅ Email Agent Service Setup Complete"
echo "========================================"
echo ""
echo "Email Configuration:"
echo "  - Email: ace.llc.nyc@gmail.com"
echo "  - Trigger: Subject contains 'CESAR.ai Agent'"
echo "  - Check Interval: 30 seconds"
echo ""
echo "To start the service:"
echo "  ./run_email_agent.sh"
echo ""
echo "To monitor with logs:"
echo "  ./monitor_email_agent.sh"
echo ""
echo "To test, send an email to ace.llc.nyc@gmail.com with:"
echo "  Subject: CESAR.ai Agent - Test my email integration"
echo "  Body: Please confirm you received this message."
echo ""
echo "The agent will:"
echo "  1. Detect the email with trigger subject"
echo "  2. Process the task with appropriate agent"
echo "  3. Send response via email"
echo "  4. Log interaction for continual learning"
echo ""
