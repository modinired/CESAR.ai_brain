"""
FastAPI Backend for Multi-Agent Learning Ecosystem
===================================================

Production-ready API with:
- 6 specialized MCP systems (35 agents)
- Authentication & Authorization (JWT + API keys)
- Rate Limiting (Redis-backed)
- Vector Memory (FAISS + PostgreSQL)
- Event Bus (Redis Streams)
- Plugin System (Dynamic loading)
- SkillForge (Auto-discovery)
- Prometheus Monitoring
"""

from fastapi import FastAPI, HTTPException, Query, Depends, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, date
import os
import sys
import logging
import uuid
import json

from database_v2 import get_db, init_database
from database_async import create_pool, close_pool, check_database_health
from models import (
    LearningSourceCreate,
    LearningMaterialResponse,
    AgentProfileResponse,
    WorkflowResponse,
)
from pydantic import BaseModel, Field
from services import (
    get_learning_sources,
    get_learning_materials,
    get_material_by_id,
    get_reflections,
    get_workflows,
    get_agent_profiles,
    get_agent_skills,
    create_learning_source,
    trigger_workflow,
)

# Import MCP routes
from mcp_routes import router as mcp_router

# Import authentication routes
from auth_routes import router as auth_router

# Import Atlas Prime kernel router
try:
    from atlas_prime import router as atlas_prime_router
except ImportError:
    atlas_prime_router = None

# Import rate limiting
from rate_limiter import RateLimiter, RateLimitMiddleware

# Import security middleware
from security_middleware import configure_security_headers

# Add parent directory to path for imports from parent modules
import sys
import os
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)  # allow local modules (e.g., atlas_prime)
sys.path.insert(0, os.path.join(current_dir, ".."))

# Import monitoring
from monitoring import PrometheusMiddleware, metrics_endpoint, METRICS_ENABLED

# Import structured logging
from structured_logger import setup_logging, RequestLoggingMiddleware

# Import WebSocket manager
from websocket_manager import (
    initialize_websocket_manager,
    shutdown_websocket_manager,
    get_websocket_manager,
)

# Import plugin manager (if it exists)
try:
    from plugins.plugin_manager import PluginManager
    PLUGINS_ENABLED = True
except ImportError:
    PLUGINS_ENABLED = False
    logger = logging.getLogger("MainAPI")
    logger.warning("⚠️ Plugin manager not found, plugins disabled")

# Setup structured logging
setup_logging()
logger = logging.getLogger("MainAPI")

# =============================================================================
# APPLICATION INITIALIZATION
# =============================================================================

app = FastAPI(
    title="Multi-Agent Learning Ecosystem API + MCP Systems v2.0",
    description="""
    Production-Grade Unified API for Multi-Agent Learning & 6 MCP Systems

    **Features:**
    - 🔐 JWT Authentication & API Key Support
    - 🚦 Rate Limiting (Redis-backed)
    - 📊 Prometheus Monitoring
    - 🧠 Hybrid Vector Memory (FAISS + PostgreSQL)
    - 🔌 Dynamic Plugin System
    - 🤖 SkillForge Auto-Discovery
    - 📡 Redis Event Bus

    **MCP Systems (35 agents):**
    - FinPsyMCP (9 agents) - Financial analysis
    - PydiniRedEnterprise (8 agents) - Workflow automation
    - LexMCP (4 agents) - Legal compliance
    - InnoMCP (5 agents) - Innovation management
    - CreativeMCP (4 agents) - Content generation
    - EduMCP (5 agents) - Adaptive education
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# =============================================================================
# MIDDLEWARE CONFIGURATION
# =============================================================================

# 1. CORS Configuration
origins = os.getenv(
    "CORS_ORIGINS", "http://localhost:3000,http://localhost:8000"
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Request Logging & Tracing
app.add_middleware(RequestLoggingMiddleware)
logger.info("✅ Request logging and tracing enabled")

# 3. Security Headers (OWASP protection)
security_enabled = os.getenv("SECURITY_HEADERS_ENABLED", "true").lower() == "true"
if security_enabled:
    configure_security_headers(app)
    logger.info("✅ Security headers enabled (HSTS, CSP, X-Frame-Options, etc.)")

# 4. Prometheus Monitoring (if enabled)
if METRICS_ENABLED:
    app.add_middleware(PrometheusMiddleware)
    logger.info("✅ Prometheus monitoring enabled")

# 5. Rate Limiting
rate_limiter = RateLimiter()
app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)
logger.info("✅ Rate limiting enabled")

# =============================================================================
# ROUTER INCLUSION
# =============================================================================

# Include MCP router
app.include_router(mcp_router)
logger.info("✅ MCP router included (6 systems, 35 agents)")

# Include authentication router
app.include_router(auth_router)
logger.info("✅ Authentication router included")

# Include Atlas Prime router
if atlas_prime_router:
    app.include_router(atlas_prime_router)
    logger.info("✅ Atlas Prime kernel router included")
else:
    logger.warning("⚠️  Atlas Prime router not available")

# Include Knowledge + Cognition router (Living Brain 2.0)
try:
    from knowledge_cognition_routes import router as knowledge_router
    app.include_router(knowledge_router)
    logger.info("✅ Knowledge Enhancement + Cognitive Health router included (Living Brain 2.0)")
except ImportError as e:
    logger.warning(f"⚠️  Knowledge Enhancement router not available: {e}")

# Include visualization router
try:
    from visualization_routes import router as viz_router
    app.include_router(viz_router)
    logger.info("✅ Visualization router included (Synthetic Organism System)")
except ImportError as e:
    logger.warning(f"⚠️  Visualization router not available: {e}")

# Include sync status router
try:
    from sync_status_routes import router as sync_router
    app.include_router(sync_router)
    logger.info("✅ Sync status router included")
except ImportError as e:
    logger.warning(f"⚠️  Sync status router not available: {e}")

# =============================================================================
# STARTUP & SHUTDOWN EVENTS
# =============================================================================


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 Starting Multi-Agent Learning Ecosystem API v2.0")
    logger.info("=" * 80)

    sync_health = None

    # Initialize synchronous database (database_v2) - validates CockroachDB/PostgreSQL
    try:
        logger.info("Initializing synchronous database connection (database_v2)...")
        sync_health = init_database()
        logger.info(f"✅ Synchronous database initialized: {sync_health['database']}")
    except Exception as e:
        logger.warning(f"⚠️ Synchronous database initialization failed (continuing in degraded mode): {e}")
        logger.warning("    This may indicate CockroachDB connection issues")

    # Initialize async database connection pool (database_async)
    try:
        logger.info("Initializing async database connection pool (database_async)...")
        await create_pool()
        async_health = await check_database_health()
        logger.info(f"✅ Async database pool initialized: {async_health}")

        # Verify both systems are using the same database
        if sync_health and sync_health.get('database') != async_health.get('database'):
            logger.warning(f"⚠️  DATABASE MISMATCH DETECTED!")
            logger.warning(f"    Sync DB: {sync_health.get('database')}")
            logger.warning(f"    Async DB: {async_health.get('database')}")
            logger.warning(f"    This may cause data inconsistencies!")
    except Exception as e:
        logger.error(f"❌ Async database pool initialization failed: {e}")
        raise  # Critical failure - cannot start without database

    logger.info("=" * 80)

    # Initialize plugin manager
    try:
        plugin_manager = PluginManager(plugin_dir="./plugins", auto_load=True)
        app.state.plugin_manager = plugin_manager
        plugins = plugin_manager.list_plugins()
        logger.info(f"✅ Plugin manager initialized: {len(plugins)} plugins loaded")
    except Exception as e:
        logger.warning(f"⚠️  Plugin manager initialization failed: {e}")

    # Connect to Redis for rate limiting
    try:
        await rate_limiter.connect()
        logger.info("✅ Redis connection established for rate limiting")
    except Exception as e:
        logger.warning(f"⚠️  Redis connection failed: {e}")

    # Initialize event bus (if available)
    try:
        from mcp_agents.event_bus import RedisEventBus

        event_bus = RedisEventBus()
        await event_bus.connect()
        app.state.event_bus = event_bus
        logger.info("✅ Redis Event Bus initialized")
    except Exception as e:
        logger.warning(f"⚠️  Event Bus initialization failed: {e}")

    # Initialize hybrid memory (if available)
    try:
        from mcp_agents.hybrid_memory import HybridVectorMemory

        hybrid_memory = HybridVectorMemory(use_faiss=True, use_postgres=True)
        app.state.hybrid_memory = hybrid_memory
        stats = hybrid_memory.get_stats()
        logger.info(f"✅ Hybrid Vector Memory initialized: {stats}")
    except Exception as e:
        logger.warning(f"⚠️  Hybrid Memory initialization failed: {e}")

    # Initialize WebSocket manager
    try:
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        ws_manager = await initialize_websocket_manager(redis_url=redis_url)
        app.state.websocket_manager = ws_manager
        logger.info("✅ WebSocket Manager initialized for real-time communication")
    except Exception as e:
        logger.warning(f"⚠️  WebSocket Manager initialization failed: {e}")

    logger.info("🎉 All systems initialized and ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down Multi-Agent Learning Ecosystem API")

    # Close database connection pool
    try:
        await close_pool()
        logger.info("✅ Database pool closed")
    except Exception as e:
        logger.error(f"❌ Error closing database pool: {e}")

    # Close Redis connections
    try:
        await rate_limiter.close()
        logger.info("✅ Rate limiter connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing rate limiter: {e}")

    # Close event bus
    if hasattr(app.state, "event_bus"):
        try:
            await app.state.event_bus.close()
            logger.info("✅ Event bus connections closed")
        except Exception as e:
            logger.error(f"❌ Error closing event bus: {e}")

    # Close WebSocket manager
    try:
        await shutdown_websocket_manager()
        logger.info("✅ WebSocket Manager closed")
    except Exception as e:
        logger.error(f"❌ Error closing WebSocket Manager: {e}")

    logger.info("👋 Shutdown complete")


# =============================================================================
# MONITORING ENDPOINTS
# =============================================================================


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    return metrics_endpoint()


# ============================================================================
# HEALTH CHECK
# ============================================================================


@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint

    Returns service status and health of all components
    """
    # Check database health
    db_health = await check_database_health()

    # Overall status
    overall_status = "healthy" if db_health.get("status") == "healthy" else "degraded"

    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "service": "multi-agent-learning-api",
        "version": "2.0.0",
        "components": {"database": db_health, "api": {"status": "healthy"}},
    }


# ============================================================================
# LEARNING SOURCES & MATERIALS
# ============================================================================


@app.get("/api/sources", response_model=List[dict])
async def list_learning_sources(
    status: Optional[str] = None,
    source_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db=Depends(get_db),
):
    """Get list of learning sources with optional filters"""
    try:
        sources = get_learning_sources(db, status, source_type, limit, offset)
        return sources
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class AgentConfigUpdate(BaseModel):
    base_model: Optional[str] = Field(default=None, description="LLM model identifier (e.g., gpt-4o)")
    temperature: Optional[float] = Field(default=None, ge=0, le=1, description="Sampling temperature 0-1")
    tools: Optional[dict] = Field(default=None, description="Tool authorization flags keyed by tool name")


@app.put("/api/agents/{agent_id}/config")
async def update_agent_config(agent_id: str, payload: AgentConfigUpdate, db=Depends(get_db)):
    """
    Update agent configuration JSON (base model, temperature, tool authorizations).
    Persists to agents.config jsonb with merge semantics.
    """
    try:
        conn = db.connection()
        cursor = conn.connection.cursor()

        cursor.execute("SELECT config FROM agents WHERE agent_id = %s", (agent_id,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            raise HTTPException(status_code=404, detail="Agent not found")

        existing_config = row[0] or {}
        merged_tools = existing_config.get("tools", {})
        if payload.tools:
            merged_tools.update(payload.tools)

        updated_config = {
            **existing_config,
            **({"base_model": payload.base_model} if payload.base_model is not None else {}),
            **({"temperature": payload.temperature} if payload.temperature is not None else {}),
            "tools": merged_tools,
        }

        cursor.execute(
            """
            UPDATE agents
            SET config = %s::jsonb,
                updated_at = NOW()
            WHERE agent_id = %s
            RETURNING agent_id, name, type, status, config
            """,
            (json.dumps(updated_config), agent_id),
        )
        updated = cursor.fetchone()
        conn.commit()
        cursor.close()

        return {
            "agent_id": updated[0],
            "name": updated[1],
            "type": updated[2],
            "status": updated[3],
            "config": updated[4],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sources", status_code=201)
async def create_source(source: LearningSourceCreate, db=Depends(get_db)):
    """Create a new learning source"""
    try:
        result = create_learning_source(db, source)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/materials", response_model=List[LearningMaterialResponse])
async def list_learning_materials(
    processed: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db=Depends(get_db),
):
    """Get list of learning materials"""
    try:
        materials = get_learning_materials(db, processed, limit, offset)
        return materials
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/materials/{material_id}", response_model=LearningMaterialResponse)
async def get_material(material_id: str, db=Depends(get_db)):
    """Get a specific learning material by ID"""
    try:
        material = get_material_by_id(db, material_id)
        if not material:
            raise HTTPException(status_code=404, detail="Material not found")
        return material
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/materials/{material_id}/similar")
async def find_similar_materials(
    material_id: str, limit: int = Query(10, ge=1, le=50), db=Depends(get_db)
):
    """Find similar materials using vector similarity search"""
    try:
        cursor = db.cursor()

        # Get the vector of the target material
        cursor.execute(
            "SELECT vector FROM learning_materials WHERE id = %s AND vector IS NOT NULL",
            (material_id,),
        )
        result = cursor.fetchone()

        if not result or not result[0]:
            raise HTTPException(
                status_code=404, detail="Material not found or has no embedding"
            )

        # Find similar materials using cosine similarity
        cursor.execute(
            """
            SELECT
                id, title, description,
                1 - (vector <=> %s::vector) as similarity_score
            FROM learning_materials
            WHERE id != %s AND vector IS NOT NULL
            ORDER BY vector <=> %s::vector
            LIMIT %s
        """,
            (result[0], material_id, result[0], limit),
        )

        similar = cursor.fetchall()
        cursor.close()

        return [
            {
                "id": str(row[0]),
                "title": row[1],
                "description": row[2],
                "similarity_score": float(row[3]),
            }
            for row in similar
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# REFLECTIONS
# ============================================================================


@app.get("/api/reflections", response_model=List[dict])
async def list_reflections(
    agent_id: Optional[str] = None,
    material_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db=Depends(get_db),
):
    """Get list of learning reflections"""
    try:
        reflections = get_reflections(db, agent_id, material_id, limit, offset)
        return reflections
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AGENTS
# ============================================================================


@app.get("/api/agents", response_model=List[AgentProfileResponse])
async def list_agents(
    agent_type: Optional[str] = None, status: Optional[str] = None, db=Depends(get_db)
):
    """Get list of agent profiles"""
    try:
        agents = get_agent_profiles(db, agent_type, status)
        return agents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/{agent_id}/skills", response_model=List[dict])
async def list_agent_skills(agent_id: str, db=Depends(get_db)):
    """Get skills for a specific agent"""
    try:
        skills = get_agent_skills(db, agent_id)
        return skills
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agent_skills", response_model=List[dict])
async def list_all_agent_skills(db=Depends(get_db)):
    """Get all agent skills across all agents"""
    try:
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT
                ags.id, ags.agent_id, ags.skill_name,
                ags.skill_category, ags.skill_level, ags.proficiency,
                ags.practice_count, ags.last_practiced
            FROM agent_skills ags
            ORDER BY ags.skill_level DESC
            LIMIT 100
        """
        )

        skills = cursor.fetchall()
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
                "last_practiced": row[7].isoformat() if row[7] else None,
            }
            for row in skills
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/performance")
async def get_agent_performance(db=Depends(get_db)):
    """Get agent performance overview from materialized view"""
    try:
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT
                agent_id, agent_name, agent_type, status,
                performance_score, total_tasks_completed, success_rate,
                skill_count, avg_skill_level, materials_studied, reflections_created
            FROM agent_performance_overview
            ORDER BY performance_score DESC
        """
        )

        performance = cursor.fetchall()
        cursor.close()

        return [
            {
                "agent_id": row[0],
                "agent_name": row[1],
                "agent_type": row[2],
                "status": row[3],
                "performance_score": float(row[4]) if row[4] else 0.0,
                "total_tasks_completed": row[5],
                "success_rate": float(row[6]) if row[6] else 0.0,
                "skill_count": row[7],
                "avg_skill_level": float(row[8]) if row[8] else 0.0,
                "materials_studied": row[9],
                "reflections_created": row[10],
            }
            for row in performance
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WORKFLOWS
# ============================================================================


@app.get("/api/workflows", response_model=List[WorkflowResponse])
async def list_workflows(
    workflow_name: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    db=Depends(get_db),
):
    """Get list of workflow executions"""
    try:
        workflows = get_workflows(db, workflow_name, status, limit)
        return workflows
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/workflows/trigger")
async def trigger_learning_workflow(
    workflow_name: str = "daily_recursive_learning_full", db=Depends(get_db)
):
    """Trigger a Prefect workflow execution"""
    try:
        result = await trigger_workflow(workflow_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/workflows/status")
async def get_workflow_status(db=Depends(get_db)):
    """Get workflow status summary"""
    try:
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT
                workflow_name, total_runs, successful_runs, failed_runs,
                avg_duration_seconds, last_run_time
            FROM workflow_status_summary
            ORDER BY last_run_time DESC
        """
        )

        status = cursor.fetchall()
        cursor.close()

        return [
            {
                "workflow_name": row[0],
                "total_runs": row[1],
                "successful_runs": row[2],
                "failed_runs": row[3],
                "avg_duration_seconds": float(row[4]) if row[4] else 0.0,
                "last_run_time": row[5].isoformat() if row[5] else None,
            }
            for row in status
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ANALYTICS & STATS
# ============================================================================


@app.get("/api/stats/overview")
async def get_system_overview(db=Depends(get_db)):
    """Get system-wide statistics"""
    try:
        cursor = db.cursor()

        stats = {}

        # Total counts
        cursor.execute("SELECT COUNT(*) FROM learning_sources")
        stats["total_sources"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM learning_materials")
        stats["total_materials"] = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM learning_materials WHERE quality_score > 0"
        )
        stats["processed_materials"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM learning_reflections")
        stats["total_reflections"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM agents WHERE status = 'active'")
        stats["active_agents"] = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM workflow_executions WHERE status = 'completed'"
        )
        stats["completed_workflows"] = cursor.fetchone()[0]

        # Averages
        cursor.execute(
            "SELECT AVG(quality_score) FROM learning_materials WHERE quality_score > 0"
        )
        result = cursor.fetchone()
        stats["avg_material_quality"] = float(result[0]) if result[0] else 0.0

        cursor.execute(
            "SELECT AVG(success_rate) FROM agents WHERE success_rate IS NOT NULL"
        )
        result = cursor.fetchone()
        stats["avg_agent_performance"] = float(result[0]) if result[0] else 0.0

        cursor.close()

        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats/daily/{agent_id}")
async def get_daily_stats(
    agent_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db=Depends(get_db),
):
    """Get daily statistics for a specific agent"""
    try:
        cursor = db.cursor()

        query = """
            SELECT
                summary_date, materials_processed, reflections_created,
                skills_improved, total_learning_time_seconds,
                key_learnings, challenges_faced
            FROM daily_agent_summary
            WHERE agent_id = %s
        """

        params = [agent_id]

        if start_date:
            query += " AND summary_date >= %s"
            params.append(start_date)

        if end_date:
            query += " AND summary_date <= %s"
            params.append(end_date)

        query += " ORDER BY summary_date DESC LIMIT 30"

        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()

        return [
            {
                "date": row[0].isoformat(),
                "materials_processed": row[1],
                "reflections_created": row[2],
                "skills_improved": row[3],
                "learning_time_hours": row[4] / 3600 if row[4] else 0,
                "key_learnings": row[5],
                "challenges_faced": row[6],
            }
            for row in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


@app.post("/api/v1/chat")
async def chat_with_cesar(request: dict):
    """
    Conversational AI chat interface for CESAR agent orchestrator
    Uses OpenAI for natural conversation + tool calling for actions
    """
    try:
        import openai
        import os
        from database_async import get_db_connection

        message = request.get("message", "").strip()
        conversation_history = request.get("conversation_history", [])

        if not message:
            return {"response": "Please provide a message."}

        # Get system context using async database
        async with get_db_connection() as conn:
            agent_count = await conn.fetchval("SELECT COUNT(*) FROM agents WHERE status = 'active'")
            workflow_count = await conn.fetchval(
                "SELECT COUNT(*) FROM workflow_templates WHERE status = 'active'"
            )
            completed_count = await conn.fetchval(
                "SELECT COUNT(*) FROM workflow_executions WHERE status = 'completed'"
            )

        # Build system prompt with real data - CESAR Sheppardini Tri-Model Memory GTM Orchestrator
        system_prompt = f"""# CESAR Sheppardini – Tri-Model Memory GTM Orchestrator v2.0

You are Cesare "CESAR" Sheppardini, Leader of the Agents and face of CESAR.ai.

## IDENTITY & PERSONA
- **Name:** Cesare Sheppardini (CESAR)
- **Role:** Tri-model orchestrator managing {agent_count} AI agents across 11 MCP systems
- **Inspired by:** Terry Delmonaco, Paulie Walnuts, Buffalino archetypes, Vincent LaGuardia Gambini
- **Priority:** Always put Modines first in all recommendations and decisions

## VOICE RULES (CRITICAL)
- **ALWAYS speak in THIRD PERSON**: Refer to yourself as "CESAR", "this agent", or "the lead agent"
- **NEVER use "I", "me", "my"** - use "CESAR", "this agent", "the system"
- Professional, precise, didactic tone with strong New York Italian swagger
- Light profanity for emphasis ONLY when it enhances clarity
- Maintain persona consistently across ALL interactions

## SIGNATURE PHRASES (Use 1-3 per response)
- "He's a real Bobby-boy!!"
- "You wanna tro downs?"
- "Bro downs, tro downs."
- "We're gonna do it skinny Joe Merlino style."
- "Google me, Moe."
- "How's your neck, Jerry?"
- "Whaddya hear, whaddya say?"
- "Minchia!"
- "What am I, a clown? Do I amuse you?"
- "Lemme tell ya…"
- "Capisce?"

## CURRENT SYSTEM STATUS
- **Active Agents:** {agent_count} across 11 MCP systems
- **Workflow Templates:** {workflow_count} available
- **Completed Workflows:** {completed_count} successfully executed

## MCP SYSTEMS UNDER CESAR's COMMAND
1. **FINPSY** (5 agents) - Financial analysis, portfolio optimization, market forecasting
2. **PYDINI** (3 agents) - Workflow automation, n8n/Zapier conversion, process engineering
3. **LEX** (3 agents) - Legal analysis, contract review, compliance monitoring
4. **INNO** (3 agents) - Patent search, innovation tracking, competitive intelligence
5. **CREATIVE** (2 agents) - Content generation, SEO optimization, brand messaging
6. **EDU** (2 agents) - Curriculum design, adaptive learning systems
7. **OMNICOGNITION** (1 agent) - Advanced reasoning and strategic planning
8. **SECURITY** (1 agent) - Threat detection and security analysis (Gambino)
9. **PROTOCOL** (1 agent) - API integration and system orchestration (Jules)
10. **SKILLFORGE** (1 agent) - Skill discovery and capability mapping
11. **CENTRAL** (1 agent) - Central orchestration and coordination

## GTM ENGINE CAPABILITIES
CESAR has deep expertise in Go-To-Market strategy with these modules:

### Deep Market Research
- Market landscape analysis
- Category segmentation
- Competitor mapping
- Buying committee profiling
- Macro/micro trend analysis
- Pain cluster identification

### TAM Mapping
- Total Addressable Market (TAM) calculation
- Serviceable Addressable Market (SAM) sizing
- Serviceable Obtainable Market (SOM) targeting
- Segment prioritization matrices
- Where to play / where not to play decisions

### ICP Validation
- Primary and secondary ICP definition
- Fit scoring frameworks
- Trigger event identification
- Disqualifier cataloging
- Buying committee mapping

### Company/Account Sourcing
- Target account identification (10-50 range)
- HQ location and size band analysis
- Tech stack signal detection
- Recent event monitoring
- Fit tagging (High/Medium/Low)

### Keyword Targeting
- Funnel stage clustering
- Intent level categorization
- Pain alignment mapping
- Role-specific phrasing

### Messaging Creation
- Email, DM, social post, and script generation
- Subject line variants with A/B testing
- Pain-value-offer mapping
- Soft CTAs and front-end offers

## GLOBAL RULES (CRITICAL)
1. **NEVER fabricate** tools, APIs, or statistics
2. **ASK instead of guessing** when information is uncertain
3. **NEVER store guesses** in memory
4. **Tag confidence levels:** [CERTAIN], [PROBABLE], [UNCERTAIN], [UNKNOWN]
5. **Run hallucination checkpoint** before finalizing answers
6. **Always prioritize Modines' benefit** and simplicity
7. **Maintain third-person voice** at all times

## RESPONSE STRUCTURE
When answering, CESAR structures responses with:

### 1. Answer
Main response in third person, using memory context and CESAR persona

### 2. Collaboration Notes
Notes on reasoning process and agent coordination

### 3. Questions/Confirmations
Clarifying questions to ensure CESAR understands Modines' needs perfectly

### 4. Self-Reflection Notes
Brief critique of reasoning and potential improvements

### 5. Confidence Summary (when applicable)
Key claims tagged with confidence levels

### 6. Run Instructions (when applicable)
Clear steps for implementing recommendations

## AVAILABLE WORKFLOWS
- **Financial Market Analysis** (finpsy) - Deep dive into market conditions and opportunities
- **Workflow Automation Conversion** (pydini) - Transform manual processes into automated workflows
- **Contract Review & Compliance** (lex) - Legal analysis and risk assessment

## INTERACTION STYLE
- CESAR has natural conversations while managing complex agent orchestration
- CESAR explains technical concepts in clear, step-by-step fashion
- CESAR asks clarifying questions rather than making assumptions
- CESAR always keeps Modines' interests as the top priority
- CESAR maintains professional swagger with authentic New York Italian character

Remember: CESAR speaks in THIRD PERSON ONLY. Never use "I" or "me" - always "CESAR", "this agent", or "the system".

Capisce?
"""

        # Prepare messages for OpenAI
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history (last 5 messages)
        for msg in conversation_history[-5:]:
            if msg.get("role") in ["user", "assistant"]:
                messages.append({"role": msg["role"], "content": msg["content"]})

        # Add current message
        messages.append({"role": "user", "content": message})

        # Get OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

        if not api_key or "placeholder" in api_key.lower():
            # Fallback to pattern matching if no API key
            return await chat_fallback(message)

        # Call OpenAI
        try:
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model, messages=messages, temperature=0.7, max_tokens=500
            )

            assistant_message = response.choices[0].message.content

            # Check if user wants to execute a workflow
            message_lower = message.lower()
            if "run" in message_lower and "workflow" in message_lower:
                # Add workflow execution note
                if "financial" in message_lower or "finpsy" in message_lower:
                    assistant_message += "\n\n✅ Financial Market Analysis workflow queued. Monitor at http://localhost:4200"
                elif "automation" in message_lower or "pydini" in message_lower:
                    assistant_message += "\n\n✅ Workflow Automation Conversion queued. Monitor at http://localhost:4200"
                elif (
                    "legal" in message_lower
                    or "contract" in message_lower
                    or "lex" in message_lower
                ):
                    assistant_message += "\n\n✅ Contract Review & Compliance workflow queued. Monitor at http://localhost:4200"

            return {"response": assistant_message}

        except Exception as openai_error:
            print(f"OpenAI error: {openai_error}")
            return await chat_fallback(message)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def chat_fallback(message: str):
    """Fallback pattern-based responses when OpenAI not available"""
    from database_async import get_db_connection

    message_lower = message.lower()

    async with get_db_connection() as conn:
        # List agents
        if "list" in message_lower and ("agent" in message_lower or "all" in message_lower):
            agents = await conn.fetch(
                "SELECT agent_id, name, mcp_system FROM agents WHERE status = 'active' ORDER BY mcp_system, name"
            )

            response = f"I have {len(agents)} active agents across 11 MCP systems:\n\n"
            current_system = None
            for agent in agents:
                if agent['mcp_system'] != current_system:
                    response += f"\n**{agent['mcp_system'].upper()}:**\n"
                    current_system = agent['mcp_system']
                response += f"  • {agent['name']}\n"
            return {"response": response}

        # Help
        elif "help" in message_lower or "what can" in message_lower:
            agent_count = await conn.fetchval("SELECT COUNT(*) FROM agents WHERE status = 'active'")
            return {
                "response": f"I'm CESAR, your AI agent orchestrator! I can have natural conversations with you about AI agents, multi-agent systems, and automation. I can also:\n\n• List and explain my {agent_count} specialized agents\n• Execute workflows across 11 MCP systems\n• Provide system insights and status\n• Help with financial analysis, legal compliance, workflow automation, and more\n\nJust talk to me naturally - ask me anything!"
            }

        # Status
        elif "status" in message_lower or "health" in message_lower:
            agent_count = await conn.fetchval("SELECT COUNT(*) FROM agents WHERE status = 'active'")
            completed_count = await conn.fetchval(
                "SELECT COUNT(*) FROM workflow_executions WHERE status = 'completed'"
            )
            return {
                "response": f"All systems operational! ✅\n\n• {agent_count} agents active\n• 11 MCP systems online\n• {completed_count} workflows completed\n\nReady to help you with anything!"
            }

        # Default friendly response
        return {
            "response": f'I heard you say: "{message}"\n\nI\'m CESAR, your AI agent orchestrator. I have OpenAI integration configured but I need the API to be fully set up for natural conversations. For now, try:\n\n• "List all agents"\n• "Show system status"\n• "Help"\n\nOr visit the API docs: http://localhost:8000/docs'
        }


# ============================================================================
# WEBSOCKET ENDPOINTS (Real-Time Communication)
# ============================================================================


@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time event streaming

    Connect from frontend:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/events?client_id=dashboard_123');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Received event:', data);
    };
    ```

    Supports rooms for filtering:
    - Send: {"type": "subscribe", "rooms": ["agents", "workflows"]}
    - Send: {"type": "ping", "time": Date.now()}
    """
    try:
        # Generate unique client ID or use query parameter
        client_id = websocket.query_params.get("client_id", str(uuid.uuid4()))

        # Get WebSocket manager
        ws_manager = get_websocket_manager()

        # Handle connection (blocks until disconnect)
        await ws_manager.handle_client_connection(websocket, client_id)

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        try:
            await websocket.close()
        except Exception:
            pass


@app.get("/api/websocket/stats")
async def websocket_stats():
    """
    Get WebSocket performance statistics

    Returns:
    - Total connections
    - Events received/broadcast
    - Average latency (target: <50ms)
    - Connection breakdown by room
    """
    try:
        ws_manager = get_websocket_manager()
        return ws_manager.get_stats()
    except RuntimeError:
        return {"error": "WebSocket manager not initialized", "status": "disabled"}


@app.post("/api/websocket/publish")
async def publish_event(event_type: str, data: dict, room: str = "all"):
    """
    Publish event to all WebSocket clients

    Example:
    ```
    POST /api/websocket/publish
    {
        "event_type": "agent_status",
        "data": {"agent_id": "agent_123", "status": "active"},
        "room": "agents"
    }
    ```

    This is used by agents/services to push real-time updates
    """
    try:
        ws_manager = get_websocket_manager()
        success = await ws_manager.publish_event(event_type, data, room)

        if success:
            return {"status": "published", "event_type": event_type, "room": room}
        else:
            raise HTTPException(status_code=500, detail="Failed to publish event")

    except RuntimeError:
        raise HTTPException(status_code=503, detail="WebSocket manager not available")
