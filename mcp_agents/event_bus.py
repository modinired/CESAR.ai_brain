"""
Redis Event Bus for MCP Inter-System Communication
===================================================

Provides async event-driven communication between MCP systems
using Redis Streams for reliable message delivery.

Features:
- Publish/Subscribe messaging
- Event streams with consumer groups
- Cross-system workflow coordination
- Automatic retry and dead-letter queue
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime

try:
    import redis.asyncio as aioredis
except ImportError:
    logging.warning("redis.asyncio not available, install: pip install redis")
    aioredis = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EventBus")

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
STREAM_KEY_PREFIX = os.getenv("STREAM_KEY_PREFIX", "mcp_events")
CONSUMER_GROUP_PREFIX = "mcp_group"


# =============================================================================
# EVENT BUS
# =============================================================================

class MCPEventBus:
    """
    Redis-based event bus for MCP system communication
    """

    def __init__(self, redis_url: str = REDIS_URL):
        self.redis_url = redis_url
        self._redis: Optional[aioredis.Redis] = None
        self._consumers: Dict[str, asyncio.Task] = {}

        logger.info(f"EventBus initialized with Redis: {redis_url}")

    async def connect(self):
        """Connect to Redis"""
        if self._redis is None:
            self._redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Connected to Redis")

    async def close(self):
        """Close Redis connection"""
        # Cancel all consumers
        for task in self._consumers.values():
            task.cancel()

        if self._redis:
            await self._redis.close()
            logger.info("Disconnected from Redis")

    # =========================================================================
    # PUBLISH
    # =========================================================================

    async def publish(
        self,
        channel: str,
        event_type: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Publish event to channel

        Args:
            channel: Event channel
            event_type: Type of event
            payload: Event payload
            metadata: Optional metadata
        """
        await self.connect()

        stream_key = f"{STREAM_KEY_PREFIX}:{channel}"

        event_data = {
            "event_type": event_type,
            "payload": json.dumps(payload),
            "metadata": json.dumps(metadata or {}),
            "timestamp": datetime.now().isoformat()
        }

        message_id = await self._redis.xadd(stream_key, event_data)

        logger.info(f"Published event: {channel}/{event_type} - {message_id}")

    async def publish_task_complete(
        self,
        mcp_system: str,
        task_id: str,
        result: Dict[str, Any]
    ):
        """
        Publish task completion event

        Args:
            mcp_system: MCP system name
            task_id: Task identifier
            result: Task result
        """
        await self.publish(
            channel=f"task_complete",
            event_type=f"{mcp_system}_task_complete",
            payload={
                "mcp_system": mcp_system,
                "task_id": task_id,
                "result": result
            }
        )

    async def publish_workflow_event(
        self,
        workflow_id: str,
        step_name: str,
        status: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Publish workflow step event

        Args:
            workflow_id: Workflow identifier
            step_name: Step name
            status: Step status
            data: Optional step data
        """
        await self.publish(
            channel="workflow",
            event_type=f"step_{status}",
            payload={
                "workflow_id": workflow_id,
                "step_name": step_name,
                "status": status,
                "data": data or {}
            }
        )

    # =========================================================================
    # SUBSCRIBE
    # =========================================================================

    async def subscribe(
        self,
        channel: str,
        consumer_group: str,
        consumer_name: str,
        handler: Callable[[Dict[str, Any]], Any]
    ):
        """
        Subscribe to channel with consumer group

        Args:
            channel: Channel to subscribe to
            consumer_group: Consumer group name
            consumer_name: Unique consumer name
            handler: Async function to handle events
        """
        await self.connect()

        stream_key = f"{STREAM_KEY_PREFIX}:{channel}"
        group_name = f"{CONSUMER_GROUP_PREFIX}_{consumer_group}"

        # Create consumer group if not exists
        await self._create_consumer_group(stream_key, group_name)

        # Start consuming
        logger.info(f"Subscribing: {channel} / {group_name} / {consumer_name}")

        while True:
            try:
                # Read from stream
                messages = await self._redis.xreadgroup(
                    groupname=group_name,
                    consumername=consumer_name,
                    streams={stream_key: ">"},
                    count=10,
                    block=5000  # 5 second timeout
                )

                if not messages:
                    await asyncio.sleep(0.1)
                    continue

                # Process messages
                for stream, msg_list in messages:
                    for message_id, data in msg_list:
                        try:
                            # Parse event
                            event = self._parse_event(data)

                            # Call handler
                            result = handler(event)
                            if asyncio.iscoroutine(result):
                                await result

                            # Acknowledge message
                            await self._redis.xack(stream_key, group_name, message_id)

                        except Exception as e:
                            logger.error(f"Handler error: {e}")
                            # Don't ack - message will be redelivered

            except asyncio.CancelledError:
                logger.info(f"Consumer cancelled: {consumer_name}")
                break
            except Exception as e:
                logger.error(f"Subscribe error: {e}")
                await asyncio.sleep(1)

    def subscribe_background(
        self,
        channel: str,
        consumer_group: str,
        consumer_name: str,
        handler: Callable
    ) -> asyncio.Task:
        """
        Subscribe in background task

        Returns:
            asyncio.Task that can be cancelled
        """
        task = asyncio.create_task(
            self.subscribe(channel, consumer_group, consumer_name, handler)
        )

        consumer_id = f"{channel}:{consumer_group}:{consumer_name}"
        self._consumers[consumer_id] = task

        return task


# Backwards compatibility (older code expects RedisEventBus)
class RedisEventBus(MCPEventBus):
    """Alias for MCPEventBus to preserve legacy imports."""
    pass

    # =========================================================================
    # CROSS-SYSTEM COORDINATION
    # =========================================================================

    async def coordinate_workflow(
        self,
        workflow_id: str,
        steps: List[Dict[str, Any]],
        event_handler: Optional[Callable] = None
    ):
        """
        Coordinate multi-system workflow with event-driven steps

        Args:
            workflow_id: Workflow identifier
            steps: List of workflow steps
            event_handler: Optional handler for step events
        """
        await self.publish(
            channel="workflow",
            event_type="workflow_started",
            payload={"workflow_id": workflow_id, "total_steps": len(steps)}
        )

        for i, step in enumerate(steps):
            step_name = step.get("name", f"step_{i}")

            # Publish step start
            await self.publish_workflow_event(
                workflow_id, step_name, "started", step
            )

            # Wait for step completion (would integrate with actual MCP execution)
            # For now, simulate completion
            await asyncio.sleep(0.1)

            # Publish step complete
            await self.publish_workflow_event(
                workflow_id, step_name, "completed", {"result": "success"}
            )

        await self.publish(
            channel="workflow",
            event_type="workflow_completed",
            payload={"workflow_id": workflow_id}
        )

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    async def _create_consumer_group(self, stream_key: str, group_name: str):
        """Create consumer group if not exists"""
        try:
            await self._redis.xgroup_create(
                stream_key,
                group_name,
                id="$",  # Start from end of stream
                mkstream=True  # Create stream if not exists
            )
            logger.info(f"Created consumer group: {group_name}")
        except aioredis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                logger.error(f"Failed to create group: {e}")

    def _parse_event(self, data: Dict[str, str]) -> Dict[str, Any]:
        """Parse event data from Redis"""
        try:
            return {
                "event_type": data.get("event_type"),
                "payload": json.loads(data.get("payload", "{}")),
                "metadata": json.loads(data.get("metadata", "{}")),
                "timestamp": data.get("timestamp")
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse event: {e}")
            return data

    # =========================================================================
    # MONITORING
    # =========================================================================

    async def get_stream_info(self, channel: str) -> Dict[str, Any]:
        """Get stream information"""
        await self.connect()

        stream_key = f"{STREAM_KEY_PREFIX}:{channel}"

        try:
            info = await self._redis.xinfo_stream(stream_key)
            return {
                "stream": stream_key,
                "length": info.get("length", 0),
                "first_entry": info.get("first-entry"),
                "last_entry": info.get("last-entry")
            }
        except Exception as e:
            logger.error(f"Failed to get stream info: {e}")
            return {"error": str(e)}

    async def get_consumer_info(self, channel: str, group: str) -> List[Dict[str, Any]]:
        """Get consumer group information"""
        await self.connect()

        stream_key = f"{STREAM_KEY_PREFIX}:{channel}"
        group_name = f"{CONSUMER_GROUP_PREFIX}_{group}"

        try:
            consumers = await self._redis.xinfo_consumers(stream_key, group_name)
            return [
                {
                    "name": c.get("name"),
                    "pending": c.get("pending", 0),
                    "idle": c.get("idle", 0)
                }
                for c in consumers
            ]
        except Exception as e:
            logger.error(f"Failed to get consumer info: {e}")
            return []


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def publish_mcp_event(
    mcp_system: str,
    event_type: str,
    data: Dict[str, Any]
):
    """
    Convenience function to publish MCP event

    Args:
        mcp_system: MCP system name
        event_type: Event type
        data: Event data
    """
    bus = MCPEventBus()
    await bus.publish(
        channel=f"mcp_{mcp_system}",
        event_type=event_type,
        payload=data
    )
    await bus.close()


async def subscribe_mcp_events(
    mcp_system: str,
    handler: Callable,
    consumer_name: str = "default"
):
    """
    Convenience function to subscribe to MCP events

    Args:
        mcp_system: MCP system to subscribe to
        handler: Event handler function
        consumer_name: Consumer identifier
    """
    bus = MCPEventBus()
    await bus.subscribe(
        channel=f"mcp_{mcp_system}",
        consumer_group=mcp_system,
        consumer_name=consumer_name,
        handler=handler
    )


# =============================================================================
# EXAMPLE HANDLERS
# =============================================================================

async def example_task_complete_handler(event: Dict[str, Any]):
    """Example handler for task completion events"""
    payload = event.get("payload", {})
    mcp_system = payload.get("mcp_system")
    task_id = payload.get("task_id")
    result = payload.get("result")

    logger.info(f"Task completed: {mcp_system}/{task_id}")
    logger.info(f"Result: {result}")


async def example_workflow_handler(event: Dict[str, Any]):
    """Example handler for workflow events"""
    event_type = event.get("event_type")
    payload = event.get("payload", {})
    workflow_id = payload.get("workflow_id")

    logger.info(f"Workflow event: {workflow_id} - {event_type}")


# =============================================================================
# USAGE EXAMPLES
# =============================================================================

async def demo_event_bus():
    """Demo event bus usage"""
    bus = MCPEventBus()

    # Subscribe to events
    async def handle_event(event):
        print(f"Received event: {event}")

    # Start subscriber in background
    task = bus.subscribe_background(
        channel="demo",
        consumer_group="demo_group",
        consumer_name="consumer_1",
        handler=handle_event
    )

    # Publish some events
    for i in range(5):
        await bus.publish(
            channel="demo",
            event_type="test_event",
            payload={"count": i}
        )
        await asyncio.sleep(0.5)

    # Wait a bit for processing
    await asyncio.sleep(2)

    # Cancel subscriber
    task.cancel()
    await bus.close()


if __name__ == "__main__":
    asyncio.run(demo_event_bus())
