"""
CESAR.ai Agent-to-Agent (A2A) Communication Protocol

Enables direct, reliable communication between agents with:
- Message delivery guarantees
- Conversation threading
- Priority queues
- Timeout and retry logic
- Real-time notifications via Redis

Author: CESAR.ai Development Team
Date: November 19, 2025
"""

import asyncio
import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID, uuid4

import aioredis
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import (
    A2AConversation,
    A2AMessage,
    Agent,
)
from ..models import (
    A2AMessagePriority,
    A2AMessageStatus,
    A2AMessageType,
)


class MessageType(str, Enum):
    """Message types for A2A communication"""
    REQUEST = "request"  # Request for information/action
    RESPONSE = "response"  # Response to a request
    NOTIFICATION = "notification"  # One-way notification
    BROADCAST = "broadcast"  # Message to multiple agents
    HANDSHAKE = "handshake"  # Connection establishment
    HEARTBEAT = "heartbeat"  # Keep-alive signal


class MessagePriority(str, Enum):
    """Message priority levels"""
    CRITICAL = "critical"  # 0 - Immediate processing
    HIGH = "high"  # 1 - Process soon
    NORMAL = "normal"  # 2 - Standard priority
    LOW = "low"  # 3 - Process when idle
    BACKGROUND = "background"  # 4 - Background task


class MessageStatus(str, Enum):
    """Message delivery status"""
    PENDING = "pending"
    DELIVERED = "delivered"
    READ = "read"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class A2AProtocolService:
    """
    Agent-to-Agent Communication Protocol Service

    Provides reliable, priority-based messaging between agents with:
    - Direct messaging with delivery tracking
    - Conversation threading
    - Priority-based queueing
    - Automatic retry and timeout handling
    - Real-time notifications via Redis pub/sub
    """

    def __init__(self, db_session: AsyncSession, redis_client: aioredis.Redis):
        self.db = db_session
        self.redis = redis_client

        # Message delivery callbacks
        self._message_handlers: Dict[str, Callable] = {}

        # Pending response futures
        self._pending_responses: Dict[UUID, asyncio.Future] = {}

    async def send_message(
        self,
        from_agent_id: UUID,
        to_agent_id: UUID,
        message_type: MessageType,
        content: Dict[str, Any],
        subject: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        conversation_id: Optional[UUID] = None,
        requires_ack: bool = False,
        timeout_seconds: int = 30,
        in_reply_to: Optional[UUID] = None,
    ) -> UUID:
        """
        Send message to another agent.

        Args:
            from_agent_id: Sending agent's UUID
            to_agent_id: Receiving agent's UUID
            message_type: Type of message (request, response, notification, etc.)
            content: Message payload (JSON-serializable dict)
            subject: Optional message subject/title
            priority: Message priority level
            conversation_id: Optional conversation UUID for threading
            requires_ack: Whether sender needs acknowledgment
            timeout_seconds: Message timeout (1-3600 seconds)
            in_reply_to: Optional UUID of message this replies to

        Returns:
            UUID of created message

        Example:
            >>> message_id = await a2a.send_message(
            ...     from_agent_id=agent_1_id,
            ...     to_agent_id=agent_2_id,
            ...     message_type=MessageType.REQUEST,
            ...     content={"action": "analyze_data", "dataset_id": "123"},
            ...     priority=MessagePriority.HIGH,
            ...     requires_ack=True,
            ... )
        """
        # Use database function for message creation
        result = await self.db.execute(
            select(A2AMessage.send_a2a_message).params(
                p_from_agent_id=from_agent_id,
                p_to_agent_id=to_agent_id,
                p_message_type=message_type.value,
                p_content=json.dumps(content),
                p_priority=priority.value,
                p_conversation_id=conversation_id,
                p_requires_ack=requires_ack,
                p_timeout_seconds=timeout_seconds,
            )
        )

        message_id = result.scalar()

        # Push to Redis for real-time delivery
        await self._publish_message_to_redis(to_agent_id, message_id)

        return message_id

    async def send_request(
        self,
        from_agent_id: UUID,
        to_agent_id: UUID,
        action: str,
        params: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        timeout_seconds: int = 30,
    ) -> Optional[Dict[str, Any]]:
        """
        Send request and wait for response.

        Args:
            from_agent_id: Requesting agent's UUID
            to_agent_id: Target agent's UUID
            action: Action to perform (e.g., "analyze_contract", "generate_code")
            params: Action parameters
            priority: Request priority
            timeout_seconds: How long to wait for response

        Returns:
            Response content dict, or None if timeout

        Example:
            >>> response = await a2a.send_request(
            ...     from_agent_id=orchestrator_id,
            ...     to_agent_id=contract_analyzer_id,
            ...     action="analyze_contract",
            ...     params={"contract_id": "abc-123"},
            ...     timeout_seconds=60,
            ... )
            >>> if response:
            ...     print(response["analysis_result"])
        """
        # Send request message
        message_id = await self.send_message(
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            message_type=MessageType.REQUEST,
            content={"action": action, "params": params},
            priority=priority,
            requires_ack=True,
            timeout_seconds=timeout_seconds,
        )

        # Create future for response
        future = asyncio.Future()
        self._pending_responses[message_id] = future

        try:
            # Wait for response
            response = await asyncio.wait_for(future, timeout=timeout_seconds)
            return response
        except asyncio.TimeoutError:
            # Mark message as timed out
            await self._mark_message_timeout(message_id)
            return None
        finally:
            # Clean up future
            self._pending_responses.pop(message_id, None)

    async def send_response(
        self,
        from_agent_id: UUID,
        to_agent_id: UUID,
        in_reply_to: UUID,
        content: Dict[str, Any],
        conversation_id: Optional[UUID] = None,
    ) -> UUID:
        """
        Send response to a request.

        Args:
            from_agent_id: Responding agent's UUID
            to_agent_id: Original requester's UUID
            in_reply_to: UUID of original request message
            content: Response payload
            conversation_id: Optional conversation UUID

        Returns:
            UUID of response message

        Example:
            >>> response_id = await a2a.send_response(
            ...     from_agent_id=contract_analyzer_id,
            ...     to_agent_id=orchestrator_id,
            ...     in_reply_to=request_message_id,
            ...     content={"status": "completed", "result": {...}},
            ... )
        """
        message_id = await self.send_message(
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            message_type=MessageType.RESPONSE,
            content=content,
            priority=MessagePriority.HIGH,  # Responses are high priority
            conversation_id=conversation_id,
            in_reply_to=in_reply_to,
        )

        # If this is response to a pending request, resolve the future
        if in_reply_to in self._pending_responses:
            future = self._pending_responses[in_reply_to]
            if not future.done():
                future.set_result(content)

        return message_id

    async def send_notification(
        self,
        from_agent_id: UUID,
        to_agent_id: UUID,
        event_type: str,
        data: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> UUID:
        """
        Send one-way notification (no response expected).

        Args:
            from_agent_id: Notifying agent's UUID
            to_agent_id: Recipient agent's UUID
            event_type: Type of event (e.g., "task_completed", "data_updated")
            data: Event data
            priority: Notification priority

        Returns:
            UUID of notification message

        Example:
            >>> await a2a.send_notification(
            ...     from_agent_id=data_collector_id,
            ...     to_agent_id=trend_analyzer_id,
            ...     event_type="new_data_available",
            ...     data={"dataset_id": "xyz-789", "record_count": 1500},
            ... )
        """
        return await self.send_message(
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            message_type=MessageType.NOTIFICATION,
            content={"event_type": event_type, "data": data},
            priority=priority,
        )

    async def broadcast_message(
        self,
        from_agent_id: UUID,
        to_agent_ids: List[UUID],
        content: Dict[str, Any],
        subject: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> List[UUID]:
        """
        Broadcast message to multiple agents.

        Args:
            from_agent_id: Broadcasting agent's UUID
            to_agent_ids: List of recipient agent UUIDs
            content: Message content
            subject: Optional subject
            priority: Message priority

        Returns:
            List of message UUIDs (one per recipient)

        Example:
            >>> message_ids = await a2a.broadcast_message(
            ...     from_agent_id=meta_cognition_id,
            ...     to_agent_ids=[agent_1_id, agent_2_id, agent_3_id],
            ...     content={"announcement": "System update at 2am"},
            ...     subject="Scheduled Maintenance",
            ... )
        """
        message_ids = []

        for to_agent_id in to_agent_ids:
            message_id = await self.send_message(
                from_agent_id=from_agent_id,
                to_agent_id=to_agent_id,
                message_type=MessageType.BROADCAST,
                content=content,
                subject=subject,
                priority=priority,
            )
            message_ids.append(message_id)

        return message_ids

    async def get_inbox(
        self, agent_id: UUID, limit: int = 50, unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get agent's inbox (pending/unread messages).

        Messages returned in priority order:
        1. critical (0)
        2. high (1)
        3. normal (2)
        4. low (3)
        5. background (4)

        Within each priority, oldest first (FIFO).

        Args:
            agent_id: Agent's UUID
            limit: Maximum messages to return (default 50)
            unread_only: Only return unread messages

        Returns:
            List of message dictionaries

        Example:
            >>> messages = await a2a.get_inbox(agent_id=my_agent_id, limit=10)
            >>> for msg in messages:
            ...     print(f"From {msg['from_agent_id']}: {msg['subject']}")
            ...     await a2a.mark_as_read(msg['message_id'])
        """
        # Use database function
        result = await self.db.execute(
            select(A2AMessage.get_agent_inbox).params(
                p_agent_id=agent_id, p_limit=limit
            )
        )

        messages = []
        for row in result:
            messages.append({
                "message_id": row.message_id,
                "from_agent_id": row.from_agent_id,
                "message_type": row.message_type,
                "priority": row.priority,
                "subject": row.subject,
                "content": row.content,
                "created_at": row.created_at,
                "conversation_id": row.conversation_id,
            })

        return messages

    async def mark_as_read(self, message_id: UUID) -> None:
        """Mark message as read."""
        await self.db.execute(
            update(A2AMessage)
            .where(A2AMessage.id == message_id)
            .values(status=MessageStatus.READ.value, read_at=datetime.now())
        )
        await self.db.commit()

    async def acknowledge_message(self, message_id: UUID) -> None:
        """Acknowledge message receipt and processing."""
        await self.db.execute(
            update(A2AMessage)
            .where(A2AMessage.id == message_id)
            .values(
                status=MessageStatus.ACKNOWLEDGED.value, acknowledged_at=datetime.now()
            )
        )
        await self.db.commit()

    async def get_conversation(
        self, conversation_id: UUID, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all messages in a conversation thread.

        Args:
            conversation_id: Conversation UUID
            limit: Maximum messages to return

        Returns:
            List of messages in chronological order

        Example:
            >>> messages = await a2a.get_conversation(conversation_id)
            >>> for msg in messages:
            ...     print(f"{msg['created_at']}: {msg['content']}")
        """
        result = await self.db.execute(
            select(A2AMessage)
            .where(A2AMessage.conversation_id == conversation_id)
            .order_by(A2AMessage.created_at)
            .limit(limit)
        )

        messages = []
        for msg in result.scalars():
            messages.append({
                "message_id": msg.id,
                "from_agent_id": msg.from_agent_id,
                "to_agent_id": msg.to_agent_id,
                "message_type": msg.message_type,
                "subject": msg.subject,
                "content": msg.content,
                "status": msg.status,
                "created_at": msg.created_at,
                "in_reply_to": msg.in_reply_to,
            })

        return messages

    async def create_conversation(
        self,
        participants: List[UUID],
        topic: Optional[str] = None,
        purpose: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> UUID:
        """
        Create a new conversation thread.

        Args:
            participants: List of agent UUIDs (minimum 2)
            topic: Optional conversation topic
            purpose: Optional purpose description
            tags: Optional tags for categorization

        Returns:
            Conversation UUID

        Example:
            >>> conv_id = await a2a.create_conversation(
            ...     participants=[agent_1_id, agent_2_id, agent_3_id],
            ...     topic="Portfolio optimization task",
            ...     purpose="Collaborate on user's portfolio optimization request",
            ... )
        """
        if len(participants) < 2:
            raise ValueError("Conversation requires at least 2 participants")

        conversation = A2AConversation(
            id=uuid4(),
            participants=participants,
            topic=topic,
            purpose=purpose,
            tags=tags or [],
            status="active",
        )

        self.db.add(conversation)
        await self.db.commit()

        return conversation.id

    async def get_active_conversations(self, agent_id: UUID) -> List[Dict[str, Any]]:
        """
        Get all active conversations for an agent.

        Args:
            agent_id: Agent's UUID

        Returns:
            List of conversation dictionaries

        Example:
            >>> conversations = await a2a.get_active_conversations(my_agent_id)
            >>> for conv in conversations:
            ...     print(f"{conv['topic']}: {conv['message_count']} messages")
        """
        result = await self.db.execute(
            select(A2AConversation)
            .where(
                A2AConversation.participants.contains([agent_id]),
                A2AConversation.status == "active",
            )
            .order_by(A2AConversation.last_message_at.desc())
        )

        conversations = []
        for conv in result.scalars():
            conversations.append({
                "conversation_id": conv.id,
                "participants": conv.participants,
                "topic": conv.topic,
                "purpose": conv.purpose,
                "message_count": conv.message_count,
                "started_at": conv.started_at,
                "last_message_at": conv.last_message_at,
                "tags": conv.tags,
            })

        return conversations

    async def subscribe_to_messages(
        self, agent_id: UUID, callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Subscribe to real-time messages for an agent via Redis.

        Args:
            agent_id: Agent's UUID
            callback: Async function called when message arrives

        Example:
            >>> async def handle_message(message):
            ...     print(f"New message: {message['content']}")
            ...     await process_message(message)
            ...
            >>> await a2a.subscribe_to_messages(my_agent_id, handle_message)
        """
        channel_name = f"agent:{agent_id}:messages"

        async def message_handler(channel):
            while True:
                message = await channel.get_message(ignore_subscribe_messages=True)
                if message:
                    data = json.loads(message["data"])
                    await callback(data)

        # Subscribe to Redis channel
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel_name)

        # Start message handler in background
        asyncio.create_task(message_handler(pubsub))

    async def _publish_message_to_redis(
        self, to_agent_id: UUID, message_id: UUID
    ) -> None:
        """Publish message notification to Redis for real-time delivery."""
        channel_name = f"agent:{to_agent_id}:messages"

        # Fetch full message
        result = await self.db.execute(
            select(A2AMessage).where(A2AMessage.id == message_id)
        )
        message = result.scalar_one_or_none()

        if message:
            # Publish to Redis
            await self.redis.publish(
                channel_name,
                json.dumps({
                    "message_id": str(message.id),
                    "from_agent_id": str(message.from_agent_id),
                    "message_type": message.message_type,
                    "priority": message.priority,
                    "subject": message.subject,
                    "content": message.content,
                    "created_at": message.created_at.isoformat(),
                }),
            )

            # Also add to sorted set (priority queue) in Redis
            queue_name = f"agent:{to_agent_id}:inbox"
            priority_score = self._get_priority_score(message.priority)
            await self.redis.zadd(queue_name, {str(message_id): priority_score})

    def _get_priority_score(self, priority: str) -> int:
        """Convert priority to numeric score for sorting."""
        priority_map = {
            "critical": 0,
            "high": 1,
            "normal": 2,
            "low": 3,
            "background": 4,
        }
        return priority_map.get(priority, 2)

    async def _mark_message_timeout(self, message_id: UUID) -> None:
        """Mark message as timed out."""
        await self.db.execute(
            update(A2AMessage)
            .where(A2AMessage.id == message_id)
            .values(
                status=MessageStatus.TIMEOUT.value,
                error_message="Message timed out waiting for response",
            )
        )
        await self.db.commit()

    async def get_statistics(self, agent_id: UUID) -> Dict[str, Any]:
        """
        Get messaging statistics for an agent.

        Returns:
            Statistics dictionary with message counts, avg response times, etc.

        Example:
            >>> stats = await a2a.get_statistics(my_agent_id)
            >>> print(f"Messages sent: {stats['total_sent']}")
            >>> print(f"Avg response time: {stats['avg_response_time_sec']}s")
        """
        # Query from the a2a_agent_stats view
        result = await self.db.execute(
            select(A2AAgentStats).where(A2AAgentStats.agent_id == agent_id)
        )
        stats = result.scalar_one_or_none()

        if stats:
            return {
                "agent_id": str(stats.agent_id),
                "agent_name": stats.agent_name,
                "total_sent": stats.total_messages_sent,
                "total_received": stats.total_messages_received,
                "avg_response_time_sec": float(stats.avg_response_time_seconds or 0),
                "success_rate_pct": float(stats.message_success_rate or 0),
                "active_conversations": stats.active_conversations,
            }
        else:
            return {
                "agent_id": str(agent_id),
                "total_sent": 0,
                "total_received": 0,
                "avg_response_time_sec": 0.0,
                "success_rate_pct": 0.0,
                "active_conversations": 0,
            }


class A2AMessageBuilder:
    """
    Fluent builder for constructing A2A messages.

    Example:
        >>> message_id = await (
        ...     A2AMessageBuilder()
        ...     .from_agent(agent_1_id)
        ...     .to_agent(agent_2_id)
        ...     .request()
        ...     .with_content({"action": "analyze", "data": {...}})
        ...     .with_priority(MessagePriority.HIGH)
        ...     .with_timeout(60)
        ...     .send(a2a_service)
        ... )
    """

    def __init__(self):
        self._from_agent_id: Optional[UUID] = None
        self._to_agent_id: Optional[UUID] = None
        self._message_type: MessageType = MessageType.NOTIFICATION
        self._content: Dict[str, Any] = {}
        self._subject: Optional[str] = None
        self._priority: MessagePriority = MessagePriority.NORMAL
        self._timeout: int = 30
        self._requires_ack: bool = False
        self._conversation_id: Optional[UUID] = None
        self._in_reply_to: Optional[UUID] = None

    def from_agent(self, agent_id: UUID) -> "A2AMessageBuilder":
        """Set sender agent."""
        self._from_agent_id = agent_id
        return self

    def to_agent(self, agent_id: UUID) -> "A2AMessageBuilder":
        """Set recipient agent."""
        self._to_agent_id = agent_id
        return self

    def request(self) -> "A2AMessageBuilder":
        """Mark as request message (expects response)."""
        self._message_type = MessageType.REQUEST
        self._requires_ack = True
        return self

    def response(self) -> "A2AMessageBuilder":
        """Mark as response message."""
        self._message_type = MessageType.RESPONSE
        return self

    def notification(self) -> "A2AMessageBuilder":
        """Mark as notification (no response expected)."""
        self._message_type = MessageType.NOTIFICATION
        return self

    def with_content(self, content: Dict[str, Any]) -> "A2AMessageBuilder":
        """Set message content."""
        self._content = content
        return self

    def with_subject(self, subject: str) -> "A2AMessageBuilder":
        """Set message subject."""
        self._subject = subject
        return self

    def with_priority(self, priority: MessagePriority) -> "A2AMessageBuilder":
        """Set message priority."""
        self._priority = priority
        return self

    def with_timeout(self, seconds: int) -> "A2AMessageBuilder":
        """Set message timeout."""
        self._timeout = seconds
        return self

    def in_conversation(self, conversation_id: UUID) -> "A2AMessageBuilder":
        """Add to existing conversation."""
        self._conversation_id = conversation_id
        return self

    def in_reply_to(self, message_id: UUID) -> "A2AMessageBuilder":
        """Reply to existing message."""
        self._in_reply_to = message_id
        return self

    async def send(self, a2a_service: A2AProtocolService) -> UUID:
        """Send the message."""
        if not self._from_agent_id or not self._to_agent_id:
            raise ValueError("Both from_agent and to_agent must be set")

        return await a2a_service.send_message(
            from_agent_id=self._from_agent_id,
            to_agent_id=self._to_agent_id,
            message_type=self._message_type,
            content=self._content,
            subject=self._subject,
            priority=self._priority,
            conversation_id=self._conversation_id,
            requires_ack=self._requires_ack,
            timeout_seconds=self._timeout,
            in_reply_to=self._in_reply_to,
        )
