"""
Atlas Prime — Neuro-Symbolic Kernel (v2.0 - Async/Vector Ready)
Monolithic router providing graph cortex, financial simulation, and telemetry.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import random
import uuid
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Header,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel, Field
from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, String, func, select, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Reuse existing DB config from main app
try:
    from database_v2 import SQLALCHEMY_DATABASE_URL
except Exception:
    SQLALCHEMY_DATABASE_URL = None
try:
    from database_async import DATABASE_URL as ASYNC_DATABASE_URL
except Exception:
    ASYNC_DATABASE_URL = None

try:
    from pgvector.sqlalchemy import Vector
    EMBEDDING_TYPE = Vector(1536)
    VECTOR_ENABLED = True
except ImportError:
    EMBEDDING_TYPE = JSON
    VECTOR_ENABLED = False

# ------------------------------------------------------------------------------
# Configuration & Environment
# ------------------------------------------------------------------------------

load_dotenv()
load_dotenv(".env.cockroach")


class Settings(BaseModel):
    database_url: str = Field(
        default_factory=lambda: os.getenv(
            "COCKROACH_DB_URL", os.getenv("DATABASE_URL", "sqlite+aiosqlite:///atlas_stack.db")
        )
    )
    secret_key: str = os.getenv("SECRET_KEY", "neuro-symbolic-secret")
    environment: str = os.getenv("ENV", "development")


# Settings and logger
settings = Settings()
logger = logging.getLogger("AtlasPrime")

# ------------------------------------------------------------------------------
# Database Layer (Async ORM + Vector Support)
# ------------------------------------------------------------------------------

def resolve_database_url() -> str:
    for candidate in [
        os.getenv("ATLAS_DB_URL"),
        ASYNC_DATABASE_URL,
        SQLALCHEMY_DATABASE_URL,
        os.getenv("DATABASE_URL"),
        os.getenv("COCKROACH_DB_URL"),
        SQLALCHEMY_DATABASE_URL,
    ]:
        if candidate:
            return candidate
    return "sqlite+aiosqlite:///atlas_stack.db"


# Normalize URL to async driver and handle sslmode for asyncpg
base_url = resolve_database_url()
raw_url = make_url(base_url)
connect_args: dict = {}

driver = raw_url.drivername
if driver.startswith("postgresql"):
    raw_url = raw_url.set(drivername="postgresql+asyncpg")
elif driver.startswith("cockroachdb"):
    raw_url = raw_url.set(drivername="cockroachdb+asyncpg")
elif driver.startswith("sqlite"):
    raw_url = raw_url.set(drivername="sqlite+aiosqlite")

query = dict(raw_url.query)
if "sslmode" in query:
    mode = query.pop("sslmode")
    if mode:
        connect_args["ssl"] = "require"
    raw_url = raw_url.set(query=query)


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    str(raw_url),
    echo=False,
    pool_size=int(os.getenv("DB_POOL_SIZE", "30")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
    pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "45")),
    pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "1800")),
    pool_pre_ping=True,
    connect_args=connect_args,
)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

# ------------------------------------------------------------------------------
# Schema Definitions (The Cortex)
# ------------------------------------------------------------------------------


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BrainNode(Base):
    """
    Fundamental neuron with optional semantic embedding for vector search.
    """

    __tablename__ = "brain_nodes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    type: Mapped[str] = mapped_column(String(64))
    label: Mapped[str] = mapped_column(String(255))
    payload: Mapped[dict] = mapped_column(JSON)
    embedding = mapped_column(EMBEDDING_TYPE, nullable=True)
    mass: Mapped[float] = mapped_column(default=10.0)
    x: Mapped[float] = mapped_column(default=0.0)
    y: Mapped[float] = mapped_column(default=0.0)
    z: Mapped[float] = mapped_column(default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BrainEdge(Base):
    __tablename__ = "brain_edges"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("brain_nodes.id"))
    target_id: Mapped[str] = mapped_column(ForeignKey("brain_nodes.id"))
    relation: Mapped[str] = mapped_column(String(64))
    weight: Mapped[float] = mapped_column(default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WorkflowDefinition(Base):
    __tablename__ = "workflow_definitions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36))
    name: Mapped[str] = mapped_column(String(255))
    dag_structure: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workflow_id: Mapped[str] = mapped_column(ForeignKey("workflow_definitions.id"))
    status: Mapped[str] = mapped_column(String(32))
    current_step: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    context: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WorkflowStep(Base):
    __tablename__ = "workflow_steps"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workflow_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(32))  # human/agent/system
    expected_duration_ms: Mapped[int] = mapped_column(default=0)
    step_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WorkflowEvent(Base):
    __tablename__ = "workflow_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workflow_id: Mapped[str] = mapped_column(String(64), index=True)
    step: Mapped[str] = mapped_column(String(255))
    actor_type: Mapped[str] = mapped_column(String(32))
    actor_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32))
    latency_ms: Mapped[Optional[int]] = mapped_column(default=None)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BottleneckScore(Base):
    __tablename__ = "bottleneck_scores"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workflow_id: Mapped[str] = mapped_column(String(64), index=True)
    step_id: Mapped[str] = mapped_column(String(64))
    score: Mapped[float] = mapped_column(Float, default=0.0)
    backlog_count: Mapped[int] = mapped_column(default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class VisionJob(Base):
    __tablename__ = "vision_jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    file_path: Mapped[str] = mapped_column(String(512))
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SelfReflection(Base):
    __tablename__ = "agent_self_reflections"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_id: Mapped[str] = mapped_column(String(64), index=True)
    reflection_date: Mapped[date] = mapped_column(Date, default=date.today, index=True)
    summary: Mapped[str] = mapped_column(String(1024))
    actions: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class OneOnOneSession(Base):
    __tablename__ = "agent_one_on_one"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    week_start: Mapped[date] = mapped_column(Date, index=True)
    agenda: Mapped[str] = mapped_column(String(1024))
    status: Mapped[str] = mapped_column(String(32), default="scheduled")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AgentTrace(Base):
    __tablename__ = "agent_traces"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_id: Mapped[str] = mapped_column(String(64), index=True)
    workflow_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    step: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32))
    latency_ms: Mapped[Optional[int]] = mapped_column(default=None)
    tokens: Mapped[Optional[int]] = mapped_column(default=None)
    cost: Mapped[Optional[float]] = mapped_column(default=None)
    error: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class APIKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), default="default")
    name: Mapped[str] = mapped_column(String(255))
    hashed_key: Mapped[str] = mapped_column(String(128), unique=True)
    scopes: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


# ------------------------------------------------------------------------------
# Pydantic DTOs
# ------------------------------------------------------------------------------


class NodeCreate(BaseModel):
    label: str
    type: str
    payload: Dict[str, Any] = {}
    mass: float = 10.0


class EdgeCreate(BaseModel):
    source_id: str
    target_id: str
    relation: str
    weight: float = 1.0


class SemanticQuery(BaseModel):
    query_text: str
    limit: int = 5


class WorkflowEventCreate(BaseModel):
    workflow_id: str
    step: str
    actor_type: str
    actor_id: Optional[str] = None
    status: str
    latency_ms: Optional[int] = None
    payload: Dict[str, Any] = {}


class WorkflowSwapRequest(BaseModel):
    workflow_id: str
    step: str
    new_actor_id: str
    new_actor_type: str = "agent"
    note: Optional[str] = None


class VisionJobResponse(BaseModel):
    job_id: str
    status: str
    result: Dict[str, Any] = {}
    error: Optional[str] = None


class APIKeyCreate(BaseModel):
    name: str
    scopes: List[str] = Field(default_factory=list)


class SelfReflectionCreate(BaseModel):
    summary: str
    actions: Dict[str, Any] = Field(default_factory=dict)


class OneOnOneCreate(BaseModel):
    user_id: str
    week_start: date
    agenda: str


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


# ------------------------------------------------------------------------------
# FastAPI Router
# ------------------------------------------------------------------------------

router = APIRouter(prefix="/atlas", tags=["Atlas Prime Kernel"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.on_event("startup")
async def startup_event():
    global engine, AsyncSessionLocal
    active_url = str(raw_url)

    async def ensure_vector_table(_engine):
        """Create vector_memory table if missing to satisfy hybrid memory checks."""
        dialect = _engine.dialect.name
        async with _engine.begin() as conn:
            if dialect in ("postgresql", "cockroachdb"):
                try:
                    await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                except Exception:
                    # extension may not exist in managed instances, tolerate
                    pass
                await conn.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS vector_memory (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            embedding vector(1536),
                            metadata JSONB,
                            created_at TIMESTAMPTZ DEFAULT now()
                        )
                        """
                    )
                )
            elif dialect == "sqlite":
                await conn.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS vector_memory (
                            id TEXT PRIMARY KEY,
                            embedding TEXT,
                            metadata TEXT,
                            created_at TEXT DEFAULT (datetime('now'))
                        )
                        """
                    )
                )

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await ensure_vector_table(engine)
        logger.info(f"🚀 ATLAS PRIME KERNEL: ONLINE (primary database) [{active_url}]")
    except Exception as primary_err:
        logger.warning(f"⚠️ Atlas Prime primary DB init failed: {primary_err}")
        logger.warning("   Falling back to local SQLite for availability.")
        fallback_url = "sqlite+aiosqlite:///atlas_stack.db"
        engine = create_async_engine(
            fallback_url, echo=False, pool_pre_ping=True
        )
        AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS vector_memory (
                        id TEXT PRIMARY KEY,
                        embedding TEXT,
                        metadata TEXT,
                        created_at TEXT DEFAULT (datetime('now'))
                    )
                    """
                )
            )
        logger.info(f"🚀 ATLAS PRIME KERNEL: ONLINE (fallback SQLite) [{fallback_url}]")


@router.get("/")
async def root():
    return {
        "system": "CESAR.AI",
        "status": "active",
        "mode": "neuro-symbolic",
        "timestamp": datetime.utcnow(),
    }


@router.post("/keys")
async def create_api_key(
    payload: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
    x_bootstrap_key: Optional[str] = Header(default=None),
):
    bootstrap = os.getenv("ATLAS_BOOTSTRAP_KEY")
    if not bootstrap or x_bootstrap_key != bootstrap:
        raise HTTPException(status_code=401, detail="Bootstrap key required")

    raw_key = uuid.uuid4().hex + uuid.uuid4().hex
    hashed = hash_api_key(raw_key)
    record = APIKey(
        id=uuid.uuid4().hex,
        tenant_id="default",
        name=payload.name,
        hashed_key=hashed,
        scopes=payload.scopes or [],
    )
    db.add(record)
    await db.commit()
    return {"api_key": raw_key, "id": record.id, "scopes": record.scopes}


# --- A. Graph Operations -----------------------------------------------------


@router.post("/cortex/nodes", response_model=str)
async def create_node(
    node: NodeCreate, tenant_id: str = "default", db: AsyncSession = Depends(get_db)
):
    new_node = BrainNode(
        id=uuid.uuid4().hex,
        tenant_id=tenant_id,
        type=node.type,
        label=node.label,
        payload=node.payload,
        mass=node.mass,
    )
    db.add(new_node)
    await db.commit()
    return new_node.id


@router.post("/cortex/edges", response_model=str)
async def create_edge(
    edge: EdgeCreate, tenant_id: str = "default", db: AsyncSession = Depends(get_db)
):
    new_edge = BrainEdge(
        id=uuid.uuid4().hex,
        tenant_id=tenant_id,
        source_id=edge.source_id,
        target_id=edge.target_id,
        relation=edge.relation,
        weight=edge.weight,
    )
    db.add(new_edge)
    await db.commit()
    return new_edge.id


@router.get("/cortex/graph")
async def get_graph(tenant_id: str = "default", db: AsyncSession = Depends(get_db)):
    result_nodes = await db.execute(select(BrainNode).where(BrainNode.tenant_id == tenant_id))
    nodes = result_nodes.scalars().all()

    result_edges = await db.execute(select(BrainEdge).where(BrainEdge.tenant_id == tenant_id))
    edges = result_edges.scalars().all()

    return {
        "nodes": [
            {"id": n.id, "label": n.label, "type": n.type, "mass": n.mass, "val": n.mass}
            for n in nodes
        ],
        "links": [
            {"source": e.source_id, "target": e.target_id, "relation": e.relation, "weight": e.weight}
            for e in edges
        ],
    }


# --- B. Financial Engine (Monte Carlo Simulation) ---------------------------


@router.post("/finance/simulate/runway")
async def simulate_runway(
    current_cash: float, monthly_burn: float, revenue_growth_rate: float = 0.05
):
    simulations = 1000
    months = 12
    results: List[List[float]] = []

    for _ in range(simulations):
        path: List[float] = []
        cash = current_cash
        burn = monthly_burn

        for _ in range(months):
            volatility = random.gauss(0, 0.1)
            effective_growth = revenue_growth_rate + volatility
            cash = cash - burn + (burn * 0.5 * (1 + effective_growth))
            path.append(max(0, cash))
        results.append(path)

    avg_path = [sum(x) / simulations for x in zip(*results)]

    return {
        "forecast": avg_path,
        "runway_months": next((i for i, x in enumerate(avg_path) if x == 0), months + 1),
        "confidence_score": 0.85,
    }


# --- C. Nervous System (Real-Time Telemetry) --------------------------------


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


async def require_api_key(
    x_api_key: Optional[str] = Header(default=None),
    required_scopes: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_db),
):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    hashed = hash_api_key(x_api_key)
    result = await db.execute(select(APIKey).where(APIKey.hashed_key == hashed, APIKey.status == "active"))
    key = result.scalars().first()
    if not key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    if required_scopes:
        scopes = set(key.scopes or [])
        missing = [s for s in required_scopes if s not in scopes]
        if missing:
            raise HTTPException(status_code=403, detail=f"Missing scopes: {missing}")
    key.last_used_at = datetime.utcnow()
    await db.commit()
    return key


@router.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    """
    Streams live production metrics from the Atlas Prime kernel for dashboards.
    """

    await manager.connect(websocket)
    try:
        while True:
            async with AsyncSessionLocal() as db:
                try:
                    result_agents = await db.execute(
                        select(func.count()).select_from(BrainNode).where(BrainNode.type == "agent")
                    )
                    active_agents = result_agents.scalar() or 0

                    result_tasks = await db.execute(select(func.count()).select_from(WorkflowExecution))
                    total_tasks = result_tasks.scalar() or 0

                    telemetry = {
                        "status": "operational",
                        "active_agents": active_agents,
                        "tasks_processed": total_tasks,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    await websocket.send_json(telemetry)
                except Exception as db_err:
                    error_telemetry = {
                        "status": "degraded",
                        "error": str(db_err),
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    await websocket.send_json(error_telemetry)

            await asyncio.sleep(5)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# --- D. Automation Matrix ----------------------------------------------------


@router.post("/automation/matrix/events")
async def append_workflow_event(
    event: WorkflowEventCreate,
    db: AsyncSession = Depends(get_db),
):
    await require_api_key(required_scopes=["automation:write"], db=db)
    new_event = WorkflowEvent(
        id=uuid.uuid4().hex,
        workflow_id=event.workflow_id,
        step=event.step,
        actor_type=event.actor_type,
        actor_id=event.actor_id,
        status=event.status,
        latency_ms=event.latency_ms,
        payload=event.payload,
    )
    db.add(new_event)
    await db.commit()
    return {"status": "ok", "id": new_event.id}


@router.get("/automation/matrix/{workflow_id}")
async def get_workflow_matrix(workflow_id: str, db: AsyncSession = Depends(get_db)):
    steps_res = await db.execute(select(WorkflowStep).where(WorkflowStep.workflow_id == workflow_id))
    steps = steps_res.scalars().all()

    events_res = await db.execute(
        select(
            WorkflowEvent.step,
            func.count().label("count"),
            func.avg(WorkflowEvent.latency_ms).label("avg_latency"),
            func.max(WorkflowEvent.created_at).label("last_seen"),
        )
        .where(WorkflowEvent.workflow_id == workflow_id)
        .group_by(WorkflowEvent.step)
    )
    aggregates = {row.step: {"count": row.count, "avg_latency": row.avg_latency, "last_seen": row.last_seen} for row in events_res}

    bottleneck_res = await db.execute(select(BottleneckScore).where(BottleneckScore.workflow_id == workflow_id))
    bottlenecks = bottleneck_res.scalars().all()

    return {
        "workflow_id": workflow_id,
        "steps": [
            {
                "id": s.id,
                "name": s.name,
                "type": s.type,
                "expected_duration_ms": s.expected_duration_ms,
                "metadata": s.step_metadata,
                "stats": aggregates.get(s.name, {}),
            }
            for s in steps
        ],
        "bottlenecks": [
            {"step_id": b.step_id, "score": b.score, "backlog_count": b.backlog_count, "updated_at": b.updated_at}
            for b in bottlenecks
        ],
    }


@router.get("/automation/matrix/{workflow_id}/events")
async def list_workflow_events(workflow_id: str, limit: int = 25, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(
            WorkflowEvent.id,
            WorkflowEvent.step,
            WorkflowEvent.actor_type,
            WorkflowEvent.actor_id,
            WorkflowEvent.status,
            WorkflowEvent.latency_ms,
            WorkflowEvent.created_at,
        )
        .where(WorkflowEvent.workflow_id == workflow_id)
        .order_by(WorkflowEvent.created_at.desc())
        .limit(limit)
    )
    events = res.fetchall()
    return [
        {
            "id": row.id,
            "step": row.step,
            "actor_type": row.actor_type,
            "actor_id": row.actor_id,
            "status": row.status,
            "latency_ms": row.latency_ms,
            "created_at": row.created_at,
        }
        for row in events
    ]


@router.post("/automation/matrix/swap")
async def swap_actor(request: WorkflowSwapRequest, db: AsyncSession = Depends(get_db)):
    # Record swap as event and return patch guidance
    swap_event = WorkflowEvent(
        id=uuid.uuid4().hex,
        workflow_id=request.workflow_id,
        step=request.step,
        actor_type=request.new_actor_type,
        actor_id=request.new_actor_id,
        status="swapped",
        payload={"note": request.note},
    )
    db.add(swap_event)
    await db.commit()
    return {"status": "ok", "workflow_id": request.workflow_id, "step": request.step, "new_actor_id": request.new_actor_id}


@router.get("/automation/workflows")
async def list_workflows(db: AsyncSession = Depends(get_db), limit: int = 20):
    wf_res = await db.execute(select(WorkflowStep.workflow_id).distinct().limit(limit))
    ids = [row[0] for row in wf_res.fetchall() if row[0]]
    if not ids:
        evt_res = await db.execute(select(WorkflowEvent.workflow_id).distinct().limit(limit))
        ids = [row[0] for row in evt_res.fetchall() if row[0]]
    return {"workflows": ids}


# --- E. Optic Nerve (Vision Ingestion) --------------------------------------


async def process_vision_job(job_id: str, file_path: str, db_factory=AsyncSessionLocal):
    """
    Mock vision parser: derives simple nodes/edges from filename.
    """
    try:
        nodes = [
            {"label": f"vision_{Path(file_path).stem}", "type": "raw_data", "mass": 10.0},
            {"label": "parsed_concept", "type": "information", "mass": 20.0},
        ]
        edges = [{"source_index": 0, "target_index": 1, "relation": "derives"}]

        async with db_factory() as db:
            created_nodes: List[BrainNode] = []
            for n in nodes:
                # Deduplicate by tenant + label to avoid duplicate optic nodes
                existing = await db.execute(
                    select(BrainNode).where(BrainNode.tenant_id == "default", BrainNode.label == n["label"])
                )
                node = existing.scalars().first()
                if not node:
                    node = BrainNode(
                        id=uuid.uuid4().hex,
                        tenant_id="default",
                        type=n["type"],
                        label=n["label"],
                        payload={"source": "optic_nerve"},
                        mass=n["mass"],
                    )
                    db.add(node)
                created_nodes.append(node)
            for e in edges:
                edge = BrainEdge(
                    id=uuid.uuid4().hex,
                    tenant_id="default",
                    source_id=created_nodes[e["source_index"]].id,
                    target_id=created_nodes[e["target_index"]].id,
                    relation=e["relation"],
                )
                db.add(edge)
            # Update job
            job_res = await db.execute(select(VisionJob).where(VisionJob.id == job_id))
            job = job_res.scalars().first()
            if job:
                job.status = "completed"
                job.result = {"nodes": nodes, "edges": edges}
                job.updated_at = datetime.utcnow()
            await db.commit()
    except Exception as err:
        async with db_factory() as db:
            job_res = await db.execute(select(VisionJob).where(VisionJob.id == job_id))
            job = job_res.scalars().first()
            if job:
                job.status = "failed"
                job.error = str(err)
                job.updated_at = datetime.utcnow()
                await db.commit()


@router.post("/senses/optic/upload", response_model=VisionJobResponse)
async def upload_visual_context(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    storage_dir = Path(os.getenv("VISION_STORAGE_DIR", "/tmp/cesar_vision"))
    storage_dir.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4().hex
    file_path = storage_dir / f"{file_id}_{file.filename}"
    data = await file.read()
    file_path.write_bytes(data)

    job = VisionJob(id=uuid.uuid4().hex, status="queued", file_path=str(file_path), result={}, error=None)
    db.add(job)
    await db.commit()

    background_tasks.add_task(process_vision_job, job.id, str(file_path))
    return VisionJobResponse(job_id=job.id, status=job.status, result={}, error=None)


@router.get("/senses/optic/jobs/{job_id}", response_model=VisionJobResponse)
async def get_vision_job(job_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(VisionJob).where(VisionJob.id == job_id))
    job = res.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return VisionJobResponse(job_id=job.id, status=job.status, result=job.result or {}, error=job.error)


@router.get("/senses/optic/jobs")
async def list_vision_jobs(limit: int = 20, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(VisionJob).order_by(VisionJob.created_at.desc()).limit(limit)
    )
    jobs = res.scalars().all()
    return [
        {"job_id": j.id, "status": j.status, "created_at": j.created_at, "result": j.result, "error": j.error}
        for j in jobs
    ]


# --- F. Agent Self-Reflection & 1:1 -----------------------------------------


@router.post("/agents/{agent_id}/self_reflection")
async def create_self_reflection(
    agent_id: str,
    payload: SelfReflectionCreate,
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    res = await db.execute(
        select(SelfReflection).where(SelfReflection.agent_id == agent_id, SelfReflection.reflection_date == today)
    )
    existing = res.scalars().first()
    if existing:
        existing.summary = payload.summary
        existing.actions = payload.actions
        existing.updated_at = datetime.utcnow()
        await db.commit()
        return {"status": "updated", "id": existing.id, "date": str(today)}

    record = SelfReflection(
        id=uuid.uuid4().hex,
        agent_id=agent_id,
        reflection_date=today,
        summary=payload.summary,
        actions=payload.actions,
    )
    db.add(record)
    await db.commit()
    return {"status": "created", "id": record.id, "date": str(today)}


@router.post("/agents/{agent_id}/one_on_one")
async def schedule_one_on_one(
    agent_id: str,
    payload: OneOnOneCreate,
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(OneOnOneSession).where(
            OneOnOneSession.agent_id == agent_id,
            OneOnOneSession.user_id == payload.user_id,
            OneOnOneSession.week_start == payload.week_start,
        )
    )
    existing = res.scalars().first()
    if existing:
        existing.agenda = payload.agenda
        existing.updated_at = datetime.utcnow()
        await db.commit()
        return {"status": "updated", "id": existing.id, "week_start": str(payload.week_start)}

    sess = OneOnOneSession(
        id=uuid.uuid4().hex,
        agent_id=agent_id,
        user_id=payload.user_id,
        week_start=payload.week_start,
        agenda=payload.agenda,
    )
    db.add(sess)
    await db.commit()
    return {"status": "scheduled", "id": sess.id, "week_start": str(payload.week_start)}


@router.get("/agents/{agent_id}/cognition")
async def agent_cognition(agent_id: str, db: AsyncSession = Depends(get_db)):
    today = datetime.utcnow().date()
    start = today - timedelta(days=7)
    prev_start = start - timedelta(days=7)

    # Workflow events (current window)
    events_res = await db.execute(
        select(WorkflowEvent.status, WorkflowEvent.latency_ms, WorkflowEvent.workflow_id, WorkflowEvent.step).where(
            WorkflowEvent.actor_id == agent_id, WorkflowEvent.created_at >= start
        )
    )
    events = events_res.all()

    # Workflow events (previous window)
    prev_events_res = await db.execute(
        select(WorkflowEvent.status, WorkflowEvent.latency_ms).where(
            WorkflowEvent.actor_id == agent_id,
            WorkflowEvent.created_at >= prev_start,
            WorkflowEvent.created_at < start,
        )
    )
    prev_events = prev_events_res.all()

    # Agent traces (current window)
    traces_res = await db.execute(
        select(AgentTrace.workflow_id, AgentTrace.step, AgentTrace.status, AgentTrace.latency_ms).where(
            AgentTrace.agent_id == agent_id, AgentTrace.created_at >= start
        )
    )
    traces = traces_res.all()

    # Reflections (current window)
    refl_res = await db.execute(
        select(SelfReflection.reflection_date).where(
            SelfReflection.agent_id == agent_id, SelfReflection.reflection_date >= start
        )
    )
    reflections = {r[0] for r in refl_res.all()}

    # 1:1 sessions (current week)
    week_start = today - timedelta(days=today.weekday())
    one_res = await db.execute(
        select(OneOnOneSession).where(
            OneOnOneSession.agent_id == agent_id,
            OneOnOneSession.week_start == week_start,
            OneOnOneSession.status.in_(["scheduled", "completed"]),
        )
    )
    one_on_one = one_res.scalars().first()

    # Quality
    def _counts(evts):
        success = sum(1 for s, *_ in evts if s in ("completed", "success"))
        failure = sum(1 for s, *_ in evts if s in ("failed", "error"))
        retry = sum(1 for s, *_ in evts if s == "retry")
        total = success + failure + retry
        return success, failure, retry, total

    success, failure, retry, total = _counts(events)
    prev_success, prev_failure, prev_retry, prev_total = _counts(prev_events)
    quality = _clamp(success / total) if total else 0.0

    # Efficiency (latency improvement)
    def _avg_latency(evts):
        vals = [lat for (_, lat, *_) in evts if lat is not None]
        return sum(vals) / len(vals) if vals else None

    curr_latency = _avg_latency(events)
    prev_latency = _avg_latency(prev_events)
    if prev_latency and curr_latency:
        efficiency = _clamp((prev_latency - curr_latency) / prev_latency + 0.5)
    else:
        efficiency = 0.5  # neutral baseline

    # Breadth/novelty
    workflows = {w for (_, _, w, _) in events if w}
    steps = {st for (_, _, _, st) in events if st}
    trace_wf = {w for (w, _, _, _) in traces if w}
    breadth = _clamp((len(workflows) / 5) + (len(steps) / 10) + (len(trace_wf) / 5))

    # Reflections (daily adherence)
    reflections_ratio = _clamp(len(reflections) / 7)

    # 1:1 adherence
    one_on_one_score = 1.0 if one_on_one else 0.0

    # Stability (invert error rate)
    error_rate = _clamp(failure / total) if total else 0.0
    stability = 1.0 - error_rate

    # Composite score
    score = (
        0.30 * quality
        + 0.25 * efficiency
        + 0.15 * breadth
        + 0.10 * reflections_ratio
        + 0.10 * one_on_one_score
        + 0.10 * stability
    )
    score = round(score * 100, 1)

    return {
        "agent_id": agent_id,
        "score": score,
        "window_start": str(start),
        "window_end": str(today),
        "subscores": {
            "quality": round(quality, 3),
            "efficiency": round(efficiency, 3),
            "breadth": round(breadth, 3),
            "reflections": round(reflections_ratio, 3),
            "one_on_one": round(one_on_one_score, 3),
            "stability": round(stability, 3),
        },
        "metrics": {
            "events_total": total,
            "success": success,
            "failure": failure,
            "retry": retry,
            "curr_latency_ms": curr_latency,
            "prev_latency_ms": prev_latency,
            "unique_workflows": len(workflows),
            "unique_steps": len(steps),
        },
    }
