"""
Sync Status API Routes
======================
Real-time endpoints for dashboard to monitor CockroachDB sync status.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import psycopg2
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/sync", tags=["sync"])


@router.get("/status")
async def get_sync_status() -> Dict[str, Any]:
    """
    Get real-time synchronization status between local PostgreSQL and CockroachDB.

    Returns:
        - Connection status
        - Record counts per table
        - Recent activity metrics
        - Sync health indicators
    """
    try:
        cockroach_url = os.getenv("COCKROACH_DB_URL")
        if not cockroach_url:
            return {
                "status": "not_configured",
                "message": "COCKROACH_DB_URL not set",
                "connected": False
            }

        conn = psycopg2.connect(cockroach_url)
        cur = conn.cursor()

        # Get table counts
        tables_status = {}
        tables = ['agents', 'a2a_messages', 'llm_collaborations', 'graph_nodes', 'graph_links',
                  'workflows', 'tasks', 'neuroplasticity_log']

        for table in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                tables_status[table] = {
                    "count": count,
                    "synced": True
                }
            except Exception as e:
                tables_status[table] = {
                    "count": 0,
                    "synced": False,
                    "error": str(e)
                }

        # Get recent activity (last hour)
        recent_activity = {}

        # A2A messages
        cur.execute("SELECT COUNT(*) FROM a2a_messages WHERE created_at > NOW() - INTERVAL '1 hour'")
        recent_activity['a2a_messages_hourly'] = cur.fetchone()[0]

        # LLM collaborations
        cur.execute("SELECT COUNT(*) FROM llm_collaborations WHERE created_at > NOW() - INTERVAL '1 hour'")
        recent_activity['llm_collaborations_hourly'] = cur.fetchone()[0]

        # Graph nodes activity
        cur.execute("SELECT COUNT(*) FROM neuroplasticity_log WHERE timestamp > NOW() - INTERVAL '1 hour'")
        recent_activity['brain_mutations_hourly'] = cur.fetchone()[0]

        conn.close()

        return {
            "status": "operational",
            "connected": True,
            "timestamp": datetime.utcnow().isoformat(),
            "tables": tables_status,
            "recent_activity": recent_activity,
            "health": {
                "total_agents": tables_status.get('agents', {}).get('count', 0),
                "knowledge_nodes": tables_status.get('graph_nodes', {}).get('count', 0),
                "active_workflows": tables_status.get('workflows', {}).get('count', 0)
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "connected": False,
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/brain/stats")
async def get_brain_stats() -> Dict[str, Any]:
    """
    Get DataBrain (knowledge graph) statistics.

    Returns:
        - Node counts by z-index layer
        - Most connected nodes
        - Recent learning activity
    """
    try:
        cockroach_url = os.getenv("COCKROACH_DB_URL")
        if not cockroach_url:
            raise HTTPException(status_code=503, detail="Database not configured")

        conn = psycopg2.connect(cockroach_url)
        cur = conn.cursor()

        # Nodes by layer
        cur.execute("""
            SELECT
                CASE
                    WHEN z_index < 100 THEN 'raw_data'
                    WHEN z_index < 200 THEN 'information'
                    WHEN z_index < 300 THEN 'knowledge'
                    ELSE 'wisdom'
                END as layer,
                COUNT(*) as count
            FROM graph_nodes
            GROUP BY layer
            ORDER BY layer
        """)
        layers = {row[0]: row[1] for row in cur.fetchall()}

        # Top nodes by mass (importance)
        cur.execute("""
            SELECT id, label, mass, z_index
            FROM graph_nodes
            ORDER BY mass DESC
            LIMIT 10
        """)
        top_nodes = [
            {"id": row[0], "label": row[1], "mass": float(row[2]), "z_index": float(row[3])}
            for row in cur.fetchall()
        ]

        # Recent mutations
        cur.execute("""
            SELECT action_type, COUNT(*) as count
            FROM neuroplasticity_log
            WHERE timestamp > NOW() - INTERVAL '24 hours'
            GROUP BY action_type
        """)
        recent_mutations = {row[0]: row[1] for row in cur.fetchall()}

        conn.close()

        return {
            "layers": layers,
            "top_nodes": top_nodes,
            "recent_mutations": recent_mutations,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/training/status")
async def get_training_status() -> Dict[str, Any]:
    """
    Get LoRA training preparation status.

    Returns:
        - Training samples collected
        - Quality distribution
        - Next training schedule
    """
    import json
    from pathlib import Path

    training_dir = Path("/Users/modini_red/CESAR.ai_Terry.Dells (Deploy)/cesar_ecosystem/training_data")

    # Find latest training files
    lora_files = list(training_dir.glob("lora_summary_*.json"))
    training_files = list(training_dir.glob("training_data_*.json"))

    latest_lora = None
    if lora_files:
        latest_lora_file = max(lora_files, key=lambda p: p.stat().st_mtime)
        with open(latest_lora_file) as f:
            latest_lora = json.load(f)

    # Count recent training samples
    recent_samples = len([f for f in training_files if
                         datetime.fromtimestamp(f.stat().st_mtime) > datetime.now() - timedelta(hours=24)])

    return {
        "latest_lora_prep": latest_lora,
        "training_samples_24h": recent_samples,
        "next_scheduled_training": "Sunday 02:00 AM",
        "training_active": False,
        "timestamp": datetime.utcnow().isoformat()
    }
