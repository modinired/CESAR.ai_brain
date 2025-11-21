#!/bin/bash
# Setup CESAR.ai Living Brain Schedulers
# Adds daily summary (2 AM) and weekly 1:1 (Monday 9 AM)

echo "🔧 Setting up CESAR.ai Living Brain Schedulers..."

# Get current directory
SCRIPT_DIR="/Users/modini_red/CESAR.ai_brain/cesar_ecosystem_brain"

# Remove old related cron jobs
echo "📋 Cleaning old cron entries..."
crontab -l 2>/dev/null | grep -v "daily_learning_summary" | grep -v "weekly_one_on-one" | crontab - 2>/dev/null

# Add new cron jobs
echo "➕ Adding new scheduled jobs..."

(crontab -l 2>/dev/null; echo "# CESAR.ai Living Brain - Daily Summary (2 AM)"; echo "0 2 * * * cd $SCRIPT_DIR && python3 -c \"from scripts.generate_daily_summary import generate_daily_learning_summary; generate_daily_learning_summary()\" >> $SCRIPT_DIR/logs/daily_summary_cron.log 2>&1") | crontab -

(crontab -l 2>/dev/null; echo "# CESAR.ai Living Brain - Weekly 1:1 (Monday 9 AM)"; echo "0 9 * * 1 cd $SCRIPT_DIR && python3 -c \"from scripts.schedule_weekly_checkin import schedule_weekly_one_on_one; schedule_weekly_one_on_one()\" >> $SCRIPT_DIR/logs/weekly_checkin_cron.log 2>&1") | crontab -

echo ""
echo "✅ Schedulers configured!"
echo ""
echo "📅 Scheduled Jobs:"
echo "  • Daily Summary: 2:00 AM daily"
echo "  • Weekly 1:1: 9:00 AM every Monday"
echo ""
echo "📁 Log Files:"
echo "  • Daily: $SCRIPT_DIR/logs/daily_summary_cron.log"
echo "  • Weekly: $SCRIPT_DIR/logs/weekly_checkin_cron.log"
echo ""
echo "🔍 View crontab:"
echo "  crontab -l"
echo ""
