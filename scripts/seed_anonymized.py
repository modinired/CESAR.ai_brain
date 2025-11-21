"""
Anonymized seed data for CESAR.AI ecosystem.
Populates agents, workflows, events, self-reflections, 1:1s, vision jobs, API keys (hashed), and optional vector memory entries.
Safe for sharing with testers (no PII). Idempotent for known IDs.
"""

import asyncio
import os
import random
import uuid
from datetime import datetime, date, timedelta

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# Use atlas_prime models
from atlas_prime import (
    AgentTrace,
    APIKey,
    BottleneckScore,
    BrainEdge,
    BrainNode,
    VisionJob,
    WorkflowEvent,
    WorkflowExecution,
    WorkflowStep,
    SelfReflection,
    OneOnOneSession,
    hash_api_key,
    Base,
)


def resolve_db_url() -> str:
    url = (
        os.getenv("ATLAS_DB_URL")
        or os.getenv("COCKROACH_DB_URL")
        or os.getenv("DATABASE_URL")
        or "sqlite+aiosqlite:///atlas_stack.db"
    )
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("cockroachdb://"):
        url = url.replace("cockroachdb://", "cockroachdb+asyncpg://", 1)
    elif url.startswith("sqlite:///"):
        url = url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    return url


DB_URL = resolve_db_url()
engine = create_async_engine(DB_URL, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def upsert(session, model, pk_field, pk_value, values: dict):
    existing = await session.execute(select(model).where(pk_field == pk_value))
    obj = existing.scalars().first()
    if obj:
        for k, v in values.items():
            setattr(obj, k, v)
    else:
        obj = model(**values)
        session.add(obj)
    return obj


async def seed_agents(session):
    agents = [
        {"id": "agent_alpha", "type": "orchestrator"},
        {"id": "agent_beta", "type": "analyst"},
        {"id": "agent_gamma", "type": "executor"},
    ]
    today = datetime.utcnow().date()
    for agent in agents:
        # traces
        for i in range(10):
            trace = AgentTrace(
                id=uuid.uuid4().hex,
                agent_id=agent["id"],
                workflow_id=random.choice(["wf_pipeline_opt", "wf_finance_close", "wf_incident_triage"]),
                step=random.choice(["ingest", "analyze", "execute", "review"]),
                status=random.choice(["completed", "completed", "failed", "retry"]),
                latency_ms=random.randint(200, 2000),
                tokens=random.randint(200, 2000),
                cost=round(random.random() * 0.05, 4),
            )
            session.add(trace)

        # reflections for last 3 days
        for d in range(3):
            rd = today - timedelta(days=d)
            await upsert(
                session,
                SelfReflection,
                SelfReflection.id,
                f"{agent['id']}-{rd}",
                {
                    "id": f"{agent['id']}-{rd}",
                    "agent_id": agent["id"],
                    "reflection_date": rd,
                    "summary": f"Reflection day {d} for {agent['id']}",
                    "actions": {"focus": "quality", "next": "reduce latency"},
                },
            )

        # 1:1 current week
        week_start = today - timedelta(days=today.weekday())
        await upsert(
            session,
            OneOnOneSession,
            OneOnOneSession.id,
            f"{agent['id']}-{week_start}",
            {
                "id": f"{agent['id']}-{week_start}",
                "agent_id": agent["id"],
                "user_id": "user_demo",
                "week_start": week_start,
                "agenda": "Status check and improvements",
                "status": "scheduled",
            },
        )


async def seed_workflows(session):
    workflows = [
        ("wf_pipeline_opt", ["ingest", "analyze", "optimize", "deploy"]),
        ("wf_finance_close", ["ingest", "reconcile", "approve", "report"]),
        ("wf_incident_triage", ["detect", "classify", "mitigate", "review"]),
    ]
    for wf_id, steps in workflows:
        wf_exec = WorkflowExecution(
            id=wf_id,
            workflow_id=wf_id,
            status="completed",
            current_step=None,
            context={},
        )
        await upsert(session, WorkflowExecution, WorkflowExecution.id, wf_id, wf_exec.__dict__)

        for s in steps:
            step_id = f"{wf_id}-{s}"
            await upsert(
                session,
                WorkflowStep,
                WorkflowStep.id,
                step_id,
                {
                    "id": step_id,
                    "workflow_id": wf_id,
                    "name": s,
                    "type": random.choice(["human", "agent", "system"]),
                    "expected_duration_ms": random.randint(500, 3000),
                    "metadata": {"demo": True},
                },
            )

        # events over last 7 days
        for d in range(7):
            ts = datetime.utcnow() - timedelta(days=d, hours=random.randint(0, 12))
            evt = WorkflowEvent(
                id=uuid.uuid4().hex,
                workflow_id=wf_id,
                step=random.choice(steps),
                actor_type=random.choice(["agent", "human"]),
                actor_id=random.choice(["agent_alpha", "agent_beta", "agent_gamma"]),
                status=random.choice(["completed", "completed", "failed", "retry"]),
                latency_ms=random.randint(400, 2500),
                payload={"demo": True},
                created_at=ts,
            )
            session.add(evt)

        # bottleneck
        b = BottleneckScore(
            id=uuid.uuid4().hex,
            workflow_id=wf_id,
            step_id=f"{wf_id}-{random.choice(steps)}",
            score=round(random.random(), 3),
            backlog_count=random.randint(0, 5),
        )
        session.add(b)


async def seed_graph(session):
    labels = [
        ("data_ingest", "raw_data", 10),
        ("etl_transform", "information", 20),
        ("risk_insight", "wisdom", 30),
        ("agent_alpha", "agent", 15),
        ("agent_beta", "agent", 15),
    ]
    node_map = {}
    for label, ntype, mass in labels:
        existing = await session.execute(select(BrainNode).where(BrainNode.label == label, BrainNode.tenant_id == "default"))
        node = existing.scalars().first()
        if not node:
            node = BrainNode(
                id=uuid.uuid4().hex,
                tenant_id="default",
                type=ntype,
                label=label,
                payload={"source": "seed"},
                mass=mass,
            )
            session.add(node)
        node_map[label] = node

    edges = [
        ("data_ingest", "etl_transform", "flows_to"),
        ("etl_transform", "risk_insight", "produces"),
        ("risk_insight", "agent_alpha", "advises"),
        ("risk_insight", "agent_beta", "advises"),
    ]
    for src_label, tgt_label, rel in edges:
        edge = BrainEdge(
            id=uuid.uuid4().hex,
            tenant_id="default",
            source_id=node_map[src_label].id,
            target_id=node_map[tgt_label].id,
            relation=rel,
        )
        session.add(edge)


async def seed_vision_jobs(session):
    for i in range(2):
        job = VisionJob(
            id=f"vision_seed_{i}",
            status="completed",
            file_path=f"/tmp/seed_vision_{i}.png",
            result={"nodes": [], "edges": []},
        )
        await upsert(session, VisionJob, VisionJob.id, job.id, job.__dict__)


async def seed_api_keys(session):
    ro_raw = uuid.uuid4().hex + uuid.uuid4().hex
    rw_raw = uuid.uuid4().hex + uuid.uuid4().hex
    keys = [
        ("guest_ro", ro_raw, ["automation:read", "optic:read"]),
        ("guest_rw", rw_raw, ["automation:write", "automation:read", "optic:read"]),
    ]
    for name, raw, scopes in keys:
        record = APIKey(
            id=uuid.uuid4().hex,
            tenant_id="default",
            name=name,
            hashed_key=hash_api_key(raw),
            scopes=scopes,
            status="active",
        )
        session.add(record)
        print(f"{name} api_key (save securely): {raw}")


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        await seed_agents(session)
        await seed_workflows(session)
        await seed_graph(session)
        await seed_vision_jobs(session)
        await seed_api_keys(session)
        await session.commit()
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(main())
