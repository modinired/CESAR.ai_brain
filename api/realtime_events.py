"""
Real-Time Event Publishing Helper
==================================

Convenience functions for publishing real-time events to WebSocket clients
This module is imported by agents/services to push updates to the dashboard

Usage:
```python
from realtime_events import publish_agent_status, publish_workflow_update

# When agent status changes
await publish_agent_status(
    agent_id="agent_123",
    status="active",
    message="Processing task..."
)

# When workflow completes
await publish_workflow_update(
    workflow_id="wf_456",
    status="completed",
    result={"success": True}
)
```
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import redis.asyncio as aioredis

logger = logging.getLogger("RealtimeEvents")

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
REDIS_PUBSUB_CHANNEL = "cesar:events"

# Global Redis connection (initialized once)
_redis_client: Optional[aioredis.Redis] = None


async def get_redis_client() -> aioredis.Redis:
    """Get or create Redis client for event publishing"""
    global _redis_client

    if _redis_client is None:
        _redis_client = await aioredis.from_url(
            REDIS_URL, encoding="utf-8", decode_responses=True
        )
        logger.info(f"✅ Redis event publisher connected: {REDIS_URL}")

    return _redis_client


async def publish_event(
    event_type: str, data: Dict[str, Any], room: str = "all", priority: str = "normal"
) -> bool:
    """
    Publish generic event to WebSocket clients

    Args:
        event_type: Event category (e.g., "agent_status", "workflow_update")
        data: Event payload (must be JSON-serializable)
        room: Room to broadcast to (default: "all")
        priority: Event priority ("low", "normal", "high")

    Returns:
        True if published successfully, False otherwise
    """
    try:
        redis = await get_redis_client()

        event = {
            "type": event_type,
            "data": data,
            "room": room,
            "priority": priority,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Publish to Redis pub/sub channel
        await redis.publish(REDIS_PUBSUB_CHANNEL, json.dumps(event))

        logger.debug(f"Published event: {event_type} to room: {room}")
        return True

    except Exception as e:
        logger.error(f"Failed to publish event {event_type}: {e}")
        return False


# ============================================================================
# AGENT EVENTS
# ============================================================================


async def publish_agent_status(
    agent_id: str,
    status: str,
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Publish agent status change event

    Args:
        agent_id: Unique agent identifier
        status: New status ("active", "idle", "busy", "error", "offline")
        message: Optional status message
        metadata: Additional metadata (e.g., current task, progress)
    """
    data = {
        "agent_id": agent_id,
        "status": status,
        "message": message,
        "metadata": metadata or {},
    }

    await publish_event("agent_status", data, room="agents")


async def publish_agent_task_start(
    agent_id: str, task_id: str, task_type: str, description: Optional[str] = None
):
    """Publish event when agent starts a task"""
    data = {
        "agent_id": agent_id,
        "task_id": task_id,
        "task_type": task_type,
        "description": description,
        "action": "start",
    }

    await publish_event("agent_task", data, room="agents", priority="normal")


async def publish_agent_task_complete(
    agent_id: str,
    task_id: str,
    success: bool,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
):
    """Publish event when agent completes a task"""
    data = {
        "agent_id": agent_id,
        "task_id": task_id,
        "action": "complete",
        "success": success,
        "result": result or {},
        "error": error,
    }

    await publish_event("agent_task", data, room="agents", priority="high")


async def publish_agent_metric(
    agent_id: str, metric_name: str, value: float, unit: Optional[str] = None
):
    """
    Publish agent performance metric

    Examples:
    - publish_agent_metric("agent_123", "tasks_completed", 42)
    - publish_agent_metric("agent_456", "response_time", 125.5, "ms")
    """
    data = {
        "agent_id": agent_id,
        "metric_name": metric_name,
        "value": value,
        "unit": unit,
    }

    await publish_event("agent_metric", data, room="agents")


# ============================================================================
# WORKFLOW EVENTS
# ============================================================================


async def publish_workflow_update(
    workflow_id: str,
    status: str,
    progress: Optional[float] = None,
    message: Optional[str] = None,
    result: Optional[Dict[str, Any]] = None,
):
    """
    Publish workflow execution update

    Args:
        workflow_id: Workflow execution ID
        status: Status ("queued", "running", "completed", "failed")
        progress: Progress percentage (0-100)
        message: Status message
        result: Workflow result (if completed)
    """
    data = {
        "workflow_id": workflow_id,
        "status": status,
        "progress": progress,
        "message": message,
        "result": result or {},
    }

    priority = "high" if status in ["completed", "failed"] else "normal"
    await publish_event("workflow_update", data, room="workflows", priority=priority)


async def publish_workflow_step(
    workflow_id: str, step_name: str, step_status: str, agent_id: Optional[str] = None
):
    """Publish workflow step progress"""
    data = {
        "workflow_id": workflow_id,
        "step_name": step_name,
        "step_status": step_status,
        "agent_id": agent_id,
    }

    await publish_event("workflow_step", data, room="workflows")


# ============================================================================
# MEMORY/LEARNING EVENTS
# ============================================================================


async def publish_learning_event(
    agent_id: str,
    event_type: str,  # "material_processed", "reflection_created", "skill_improved"
    details: Dict[str, Any],
):
    """
    Publish learning/memory event

    Examples:
    - publish_learning_event("agent_123", "material_processed", {...})
    - publish_learning_event("agent_456", "skill_improved", {"skill": "python", "level": 8.5})
    """
    data = {"agent_id": agent_id, "event_type": event_type, "details": details}

    await publish_event("learning", data, room="memory")


async def publish_memory_consolidation(
    agent_id: str,
    episodic_count: int,
    semantic_count: int,
    insights: Optional[list] = None,
):
    """Publish memory consolidation event (episodic → semantic)"""
    data = {
        "agent_id": agent_id,
        "episodic_count": episodic_count,
        "semantic_count": semantic_count,
        "insights": insights or [],
    }

    await publish_event("memory_consolidation", data, room="memory", priority="high")


# ============================================================================
# SYSTEM EVENTS
# ============================================================================


async def publish_system_alert(
    severity: str,  # "info", "warning", "error", "critical"
    message: str,
    component: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
):
    """
    Publish system alert/notification

    Used for:
    - Performance warnings (high latency, low memory)
    - Error notifications
    - System status changes
    """
    data = {
        "severity": severity,
        "message": message,
        "component": component,
        "details": details or {},
    }

    priority = "high" if severity in ["error", "critical"] else "normal"
    await publish_event("system_alert", data, room="all", priority=priority)


async def publish_system_metric(
    metric_name: str,
    value: float,
    unit: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
):
    """
    Publish system-wide metric

    Examples:
    - publish_system_metric("api_requests_per_second", 425.3)
    - publish_system_metric("database_connections", 45)
    - publish_system_metric("memory_usage_percent", 67.2, "%")
    """
    data = {
        "metric_name": metric_name,
        "value": value,
        "unit": unit,
        "tags": tags or {},
    }

    await publish_event("system_metric", data, room="all")


# ============================================================================
# COLLABORATION EVENTS (Multi-Agent Coordination)
# ============================================================================


async def publish_collaboration_request(
    requesting_agent_id: str,
    target_agent_id: str,
    request_type: str,
    details: Dict[str, Any],
):
    """
    Publish collaboration request between agents

    Examples:
    - Agent A requests help from Agent B
    - Agent coordination for workflow execution
    """
    data = {
        "requesting_agent": requesting_agent_id,
        "target_agent": target_agent_id,
        "request_type": request_type,
        "details": details,
    }

    await publish_event("collaboration_request", data, room="agents", priority="high")


async def publish_collaboration_response(
    responding_agent_id: str,
    original_request_id: str,
    accepted: bool,
    response: Optional[Dict[str, Any]] = None,
):
    """Publish response to collaboration request"""
    data = {
        "responding_agent": responding_agent_id,
        "request_id": original_request_id,
        "accepted": accepted,
        "response": response or {},
    }

    await publish_event("collaboration_response", data, room="agents", priority="high")


# ============================================================================
# CLEANUP
# ============================================================================


async def close_redis_client():
    """Close Redis client (call on shutdown)"""
    global _redis_client

    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis event publisher closed")
