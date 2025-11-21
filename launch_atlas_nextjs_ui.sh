#!/bin/bash

# ============================================================================
#  Atlas Capital Automations - CESAR.ai Next.js UI Launcher
#  a Terry Dellmonaco Co.
# ============================================================================

echo -e "\033[0;34m============================================================================\033[0m"
echo -e "\033[0;34m  Atlas Capital Automations - CESAR.ai Next.js UI\033[0m"
echo -e "\033[0;34m  Enhanced Multi-Agent Dashboard with AI Capabilities\033[0m"
echo -e "\033[0;34m  a Terry Dellmonaco Co.\033[0m"
echo -e "\033[0;34m============================================================================\033[0m"
echo ""

# Change to the Next.js UI directory
cd "$(dirname "$0")/atlas_nextjs_ui"

# Check if API is running
echo -e "\033[1;33mChecking CESAR.ai API status...\033[0m"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "\033[0;32m✓ CESAR.ai API is running on http://localhost:8000\033[0m"
else
    echo -e "\033[0;31m✗ Warning: CESAR.ai API is not running\033[0m"
    echo -e "\033[1;33m  Please start the API first with: docker-compose up -d\033[0m"
fi

echo ""
echo -e "\033[0;32m✓ CPU Slowdown Multiplier: 2.0x (calibrated)\033[0m"
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "\033[1;33mInstalling dependencies...\033[0m"
    npm install
fi

echo ""
echo -e "\033[0;34m============================================================================\033[0m"
echo -e "\033[0;34m  Starting Atlas Next.js Dashboard...\033[0m"
echo -e "\033[0;34m============================================================================\033[0m"
echo ""
echo -e "  Dashboard will open at: \033[0;32mhttp://localhost:9002\033[0m"
echo -e "  API endpoint: \033[0;32mhttp://localhost:8000\033[0m"
echo ""
echo -e "  Features:"
echo -e "  \033[0;32m✓\033[0m CESAR Agent Ecosystem Dashboard"
echo -e "  \033[0;32m✓\033[0m AI-Powered Financial Forecasting"
echo -e "  \033[0;32m✓\033[0m Anomaly Detection System"
echo -e "  \033[0;32m✓\033[0m Real-time Agent Monitoring"
echo -e "  \033[0;32m✓\033[0m Workflow Management"
echo -e "  \033[0;32m✓\033[0m AI Chat Interface"
echo ""
echo -e "  Press \033[1;33mCtrl+C\033[0m to stop the dashboard"
echo ""
echo -e "\033[0;34m============================================================================\033[0m"
echo ""

# Start the Next.js development server
npm run dev
