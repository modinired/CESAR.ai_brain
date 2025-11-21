#!/bin/bash
# ============================================================================
# Atlas Capital Automations - CESAR.ai Enhanced Desktop Launcher V2
# Beige/Cream Theme with Live Financial Data & Forecasting
# a Terry Dellmonaco Co.
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  Atlas Capital Automations - CESAR.ai Desktop Console V2${NC}"
echo -e "${BLUE}  Enhanced: Beige Theme + Live Financial Data + Forecasting${NC}"
echo -e "${BLUE}  a Terry Dellmonaco Co.${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Check if API is running
echo -e "${YELLOW}Checking API status...${NC}"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API is running on http://localhost:8000${NC}"
else
    echo -e "${YELLOW}⚠ API is not responding. Starting Docker services...${NC}"
    cd "$(dirname "$0")"
    docker-compose up -d
    echo -e "${GREEN}✓ Docker services started${NC}"
    echo "Waiting for API to be ready..."
    sleep 10
fi

echo ""
echo -e "${GREEN}✓ All systems ready${NC}"
echo ""
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  Launching Enhanced Native Desktop Application...${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo -e "  API endpoint: ${GREEN}http://localhost:8000${NC}"
echo ""
echo -e "  Features:"
echo -e "  ${GREEN}✓${NC} Beige/Cream professional theme"
echo -e "  ${GREEN}✓${NC} Live financial data from Yahoo Finance"
echo -e "  ${GREEN}✓${NC} 14-day price forecasting"
echo -e "  ${GREEN}✓${NC} Technical analysis (RSI, SMA, Volume)"
echo -e "  ${GREEN}✓${NC} All 12 agents with mob character names"
echo -e "  ${GREEN}✓${NC} Paulie Walnuts financial advice"
echo ""
echo -e "  Press ${YELLOW}Cmd+Q${NC} to quit the application"
echo ""

# Kill old versions
pkill -f "streamlit run atlas_dashboard.py" 2>/dev/null || true
pkill -f "python3 atlas_desktop.py" 2>/dev/null || true

# Launch enhanced desktop app
cd "$(dirname "$0")"
python3 atlas_desktop_v2.py
