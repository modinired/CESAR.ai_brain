"""
Business logic and service functions
"""

from typing import Optional, List, Dict, Any
import httpx
import os
from models import LearningSourceCreate

PREFECT_API_URL = os.getenv("PREFECT_API_URL", "http://prefect:4200/api")

# ============================================================================
# LEARNING SOURCES
# ============================================================================

def get_learning_sources(
    db,
    status: Optional[str] = None,
    source_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict]:
    """Get learning sources with optional filters"""
    cursor = db.cursor()

    query = """
        SELECT id, url, source_type, category, priority, fetch_status,
               last_fetched, created_at
        FROM learning_sources
        WHERE 1=1
    """
    params = []

    if status:
        query += " AND fetch_status = %s"
        params.append(status)

    if source_type:
        query += " AND source_type = %s"
        params.append(source_type)

    query += " ORDER BY priority DESC, created_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()

    return [
        {
            "id": str(row[0]),
            "url": row[1],
            "source_type": row[2],
            "category": row[3],
            "priority": row[4],
            "fetch_status": row[5],
            "last_fetched": row[6].isoformat() if row[6] else None,
            "created_at": row[7].isoformat()
        }
        for row in results
    ]

def create_learning_source(db, source: LearningSourceCreate) -> Dict:
    """Create a new learning source"""
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO learning_sources (url, source_type, category, priority, metadata)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, url, source_type, category, priority, fetch_status, created_at
    """, (source.url, source.source_type.value, source.category, source.priority, source.metadata))

    result = cursor.fetchone()
    db.commit()
    cursor.close()

    return {
        "id": str(result[0]),
        "url": result[1],
        "source_type": result[2],
        "category": result[3],
        "priority": result[4],
        "fetch_status": result[5],
        "created_at": result[6].isoformat()
    }

# ============================================================================
# LEARNING MATERIALS
# ============================================================================

def get_learning_materials(
    db,
    processed: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict]:
    """Get learning materials"""
    cursor = db.cursor()

    query = """
        SELECT id, source_id, title, description, content, processed,
               quality_score, relevance_score, tags, fetched_at
        FROM learning_materials
        WHERE 1=1
    """
    params = []

    if processed is not None:
        query += " AND processed = %s"
        params.append(processed)

    query += " ORDER BY fetched_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()

    return [
        {
            "id": str(row[0]),
            "source_id": str(row[1]) if row[1] else None,
            "title": row[2],
            "description": row[3],
            "content": row[4][:500] + "..." if len(row[4]) > 500 else row[4],  # Truncate for list view
            "processed": row[5],
            "quality_score": float(row[6]) if row[6] else 0.0,
            "relevance_score": float(row[7]) if row[7] else 0.0,
            "tags": row[8] if row[8] else [],
            "fetched_at": row[9].isoformat()
        }
        for row in results
    ]

def get_material_by_id(db, material_id: str) -> Optional[Dict]:
    """Get a specific material by ID"""
    cursor = db.cursor()

    cursor.execute("""
        SELECT id, source_id, title, description, content, processed,
               quality_score, relevance_score, tags, fetched_at
        FROM learning_materials
        WHERE id = %s
    """, (material_id,))

    result = cursor.fetchone()
    cursor.close()

    if not result:
        return None

    return {
        "id": str(result[0]),
        "source_id": str(result[1]) if result[1] else None,
        "title": result[2],
        "description": result[3],
        "content": result[4],
        "processed": result[5],
        "quality_score": float(result[6]) if result[6] else 0.0,
        "relevance_score": float(result[7]) if result[7] else 0.0,
        "tags": result[8] if result[8] else [],
        "fetched_at": result[9].isoformat()
    }

# ============================================================================
# REFLECTIONS
# ============================================================================

def get_reflections(
    db,
    agent_id: Optional[str] = None,
    material_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict]:
    """Get learning reflections"""
    cursor = db.cursor()

    query = """
        SELECT id, material_id, agent_id, reflection_text, reflection_type,
               reflection_score, key_insights, created_at
        FROM learning_reflections
        WHERE 1=1
    """
    params = []

    if agent_id:
        query += " AND agent_id = %s"
        params.append(agent_id)

    if material_id:
        query += " AND material_id = %s"
        params.append(material_id)

    query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()

    return [
        {
            "id": str(row[0]),
            "material_id": str(row[1]),
            "agent_id": row[2],
            "reflection_text": row[3],
            "reflection_type": row[4],
            "reflection_score": float(row[5]) if row[5] else 0.0,
            "key_insights": row[6] if row[6] else [],
            "timestamp": row[7].isoformat()
        }
        for row in results
    ]

# ============================================================================
# AGENTS
# ============================================================================

def get_agent_profiles(
    db,
    agent_type: Optional[str] = None,
    status: Optional[str] = None
) -> List[Dict]:
    """Get agent profiles from agents table"""
    cursor = db.cursor()

    query = """
        SELECT id, agent_id, name, type,
               COALESCE(capabilities, '[]'::jsonb),
               status,
               COALESCE((tasks_completed::float / NULLIF(tasks_completed + tasks_failed, 0) * 100), 0.0) as performance_score,
               tasks_completed,
               success_rate,
               mcp_system
        FROM agents
        WHERE 1=1
    """
    params = []

    if agent_type:
        query += " AND type = %s"
        params.append(agent_type)

    if status:
        query += " AND status = %s"
        params.append(status)

    query += " ORDER BY tasks_completed DESC, success_rate DESC"

    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()

    return [
        {
            "id": str(row[0]),
            "agent_id": row[1],
            "agent_name": row[2],
            "agent_type": row[3],
            "description": f"{row[2]} - {row[9] or 'General'} system agent",
            "specialization": row[4] if isinstance(row[4], list) else [],
            "status": row[5],
            "performance_score": float(row[6]) if row[6] else 0.5,
            "total_tasks_completed": row[7] or 0,
            "success_rate": float(row[8]) if row[8] else 0.0
        }
        for row in results
    ]

def get_agent_skills(db, agent_id: str) -> List[Dict]:
    """Get skills for a specific agent"""
    cursor = db.cursor()

    cursor.execute("""
        SELECT id, agent_id, skill_name, skill_category, skill_level,
               proficiency, practice_count, last_practiced
        FROM agent_skills
        WHERE agent_id = %s
        ORDER BY skill_level DESC
    """, (agent_id,))

    results = cursor.fetchall()
    cursor.close()

    return [
        {
            "id": str(row[0]),
            "agent_id": row[1],
            "skill_name": row[2],
            "skill_category": row[3],
            "skill_level": float(row[4]) if row[4] else 0.0,
            "proficiency": row[5],
            "practice_count": row[6],
            "last_practiced": row[7].isoformat() if row[7] else None
        }
        for row in results
    ]

# ============================================================================
# WORKFLOWS
# ============================================================================

def get_workflows(
    db,
    workflow_name: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
) -> List[Dict]:
    """Get workflow executions"""
    cursor = db.cursor()

    query = """
        SELECT id, workflow_name, workflow_run_id, agent_id, status,
               start_time, end_time, duration_seconds,
               tasks_total, tasks_completed, tasks_failed
        FROM workflow_metrics
        WHERE 1=1
    """
    params = []

    if workflow_name:
        query += " AND workflow_name = %s"
        params.append(workflow_name)

    if status:
        query += " AND status = %s"
        params.append(status)

    query += " ORDER BY start_time DESC LIMIT %s"
    params.append(limit)

    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()

    return [
        {
            "id": str(row[0]),
            "workflow_name": row[1],
            "workflow_run_id": row[2],
            "agent_id": row[3],
            "status": row[4],
            "start_time": row[5].isoformat(),
            "end_time": row[6].isoformat() if row[6] else None,
            "duration_seconds": row[7],
            "tasks_total": row[8],
            "tasks_completed": row[9],
            "tasks_failed": row[10]
        }
        for row in results
    ]

async def trigger_workflow(workflow_name: str) -> Dict:
    """Trigger a Prefect workflow via API"""
    async with httpx.AsyncClient() as client:
        try:
            # This is a simplified version - actual Prefect API calls may vary
            response = await client.post(
                f"{PREFECT_API_URL}/deployments/name/{workflow_name}/create_flow_run",
                json={}
            )
            response.raise_for_status()
            return {
                "status": "triggered",
                "workflow_name": workflow_name,
                "message": "Workflow triggered successfully"
            }
        except httpx.HTTPError as e:
            return {
                "status": "error",
                "workflow_name": workflow_name,
                "message": f"Failed to trigger workflow: {str(e)}"
            }
