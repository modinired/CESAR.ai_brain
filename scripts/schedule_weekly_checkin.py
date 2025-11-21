#!/usr/bin/env python3
"""
Weekly One-on-One Scheduler
Creates agent check-in sessions every Monday
"""

import os
import sys
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

load_dotenv()

COCKROACH_DB_URL = os.getenv("COCKROACH_DB_URL")

# Key agents for weekly check-ins
AGENTS = [
    {"id": "portfolio_optimizer", "name": "Portfolio Optimizer", "focus": "Investment strategy and portfolio performance"},
    {"id": "financial_analyst", "name": "Financial Analyst", "focus": "Market analysis and insights"},
    {"id": "risk_manager", "name": "Risk Manager", "focus": "Risk assessment and mitigation"},
    {"id": "compliance_monitor", "name": "Compliance Monitor", "focus": "Regulatory compliance and governance"},
    {"id": "market_intelligence", "name": "Market Intelligence", "focus": "Market trends and competitive analysis"}
]

def schedule_weekly_one_on_one():
    """Schedule weekly 1:1 sessions for all agents"""
    print(f"\n{'='*60}")
    print(f"🗓️  SCHEDULING WEEKLY ONE-ON-ONE SESSIONS")
    print(f"{'='*60}")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    try:
        conn = psycopg2.connect(COCKROACH_DB_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()

        session_date = datetime.now().date()
        next_session = session_date + timedelta(days=7)

        sessions_created = 0

        for agent in AGENTS:
            # Check if session already exists for this week
            cur.execute("""
                SELECT session_id FROM agent_one_on_one
                WHERE agent_id = %s AND session_date = %s
            """, (agent['id'], session_date))

            if cur.fetchone():
                print(f"⏭️  {agent['name']}: Session already exists for {session_date}")
                continue

            # Create new session
            cur.execute("""
                INSERT INTO agent_one_on_one
                (session_date, agent_id, session_focus, next_session_date, outcome_summary)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING session_id
            """, (
                session_date,
                agent['id'],
                agent['focus'],
                next_session,
                f"Weekly check-in scheduled for {session_date}"
            ))

            session_id = cur.fetchone()['session_id']
            sessions_created += 1
            print(f"✅ {agent['name']}: Session {session_id} created")

        conn.commit()

        print(f"\n{'='*60}")
        print(f"✅ WEEKLY SCHEDULING COMPLETE")
        print(f"{'='*60}")
        print(f"   📊 Sessions Created: {sessions_created}")
        print(f"   📅 Session Date: {session_date}")
        print(f"   ⏭️  Next Session: {next_session}")
        print(f"{'='*60}\n")

        cur.close()
        conn.close()

        return True

    except Exception as e:
        print(f"\n❌ ERROR scheduling sessions: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    schedule_weekly_one_on_one()
