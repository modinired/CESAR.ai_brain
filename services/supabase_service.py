"""
CESAR.ai Supabase Real-Time Integration Service

Provides real-time synchronization and subscriptions between CESAR.ai and Supabase.

Features:
- Real-time subscriptions to database changes
- Bidirectional sync between local PostgreSQL and Supabase
- Agent state broadcasting
- Artifact storage in Supabase Storage
- Row-level security (RLS) for multi-tenancy

Author: CESAR.ai Development Team
Date: November 19, 2025
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID

from supabase import Client, create_client
from supabase.lib.client_options import ClientOptions

class SupabaseService:
    """
    Real-time Supabase integration for CESAR.ai.

    Capabilities:
    - Subscribe to real-time agent state changes
    - Sync local PostgreSQL tables to Supabase
    - Store/retrieve agent artifacts (files, outputs)
    - Broadcast events to connected clients
    - Multi-tenant row-level security
    """

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        local_db_url: Optional[str] = None,
    ):
        """
        Initialize Supabase service.

        Args:
            supabase_url: Supabase project URL (https://xxx.supabase.co)
            supabase_key: Supabase anon or service role key
            local_db_url: Optional local PostgreSQL URL for sync

        Example:
            >>> supabase = SupabaseService(
            ...     supabase_url="https://xxxxx.supabase.co",
            ...     supabase_key="your-anon-key",
            ... )
        """
        # Create Supabase client
        self.client: Client = create_client(supabase_url, supabase_key)
        self.local_db_url = local_db_url

        # Active subscriptions
        self.subscriptions: Dict[str, Any] = {}

        # Sync configuration
        self.sync_enabled = False
        self.sync_interval_seconds = 30

    # ============================================================================
    # Real-Time Subscriptions
    # ============================================================================

    async def subscribe_to_agent_updates(
        self, callback: Callable[[Dict[str, Any]], None]
    ) -> str:
        """
        Subscribe to real-time agent state changes.

        Receives notifications when:
        - Agent status changes (active, idle, busy, error)
        - Agent capabilities are updated
        - New agents are registered

        Args:
            callback: Async function called with change events

        Returns:
            Subscription ID for cleanup

        Example:
            >>> async def handle_agent_change(event):
            ...     agent_id = event['data']['id']
            ...     new_status = event['data']['status']
            ...     print(f"Agent {agent_id} is now {new_status}")
            ...
            >>> sub_id = await supabase.subscribe_to_agent_updates(handle_agent_change)
        """

        def handle_changes(payload):
            """Handle Supabase realtime payload"""
            event_type = payload.get("eventType")  # INSERT, UPDATE, DELETE
            data = (
                payload.get("new")
                if event_type in ["INSERT", "UPDATE"]
                else payload.get("old")
            )

            # Call user's callback in background
            asyncio.create_task(
                callback({
                    "event": event_type,
                    "table": "agents",
                    "data": data,
                    "timestamp": datetime.now(),
                })
            )

        # Subscribe to agents table
        subscription = (
            self.client.channel("agents_channel")
            .on_postgres_changes(
                event="*", schema="public", table="agents", callback=handle_changes
            )
            .subscribe()
        )

        sub_id = f"agents_{id(subscription)}"
        self.subscriptions[sub_id] = subscription

        return sub_id

    async def subscribe_to_tasks(
        self, callback: Callable[[Dict[str, Any]], None], agent_id: Optional[UUID] = None
    ) -> str:
        """
        Subscribe to real-time task updates.

        Args:
            callback: Async function called with task events
            agent_id: Optional filter for specific agent's tasks

        Returns:
            Subscription ID

        Example:
            >>> async def handle_new_task(event):
            ...     if event['event'] == 'INSERT':
            ...         task = event['data']
            ...         print(f"New task: {task['description']}")
            ...
            >>> sub_id = await supabase.subscribe_to_tasks(handle_new_task)
        """

        def handle_changes(payload):
            event_type = payload.get("eventType")
            data = (
                payload.get("new")
                if event_type in ["INSERT", "UPDATE"]
                else payload.get("old")
            )

            # Filter by agent if specified
            if agent_id is None or data.get("agent_id") == str(agent_id):
                asyncio.create_task(
                    callback({
                        "event": event_type,
                        "table": "tasks",
                        "data": data,
                        "timestamp": datetime.now(),
                    })
                )

        subscription = (
            self.client.channel("tasks_channel")
            .on_postgres_changes(
                event="*", schema="public", table="tasks", callback=handle_changes
            )
            .subscribe()
        )

        sub_id = f"tasks_{id(subscription)}"
        self.subscriptions[sub_id] = subscription

        return sub_id

    async def subscribe_to_a2a_messages(
        self, agent_id: UUID, callback: Callable[[Dict[str, Any]], None]
    ) -> str:
        """
        Subscribe to real-time A2A messages for an agent.

        Args:
            agent_id: Agent's UUID to monitor
            callback: Async function called when agent receives messages

        Returns:
            Subscription ID

        Example:
            >>> async def handle_message(event):
            ...     if event['event'] == 'INSERT':
            ...         msg = event['data']
            ...         print(f"New message from {msg['from_agent_id']}")
            ...
            >>> sub_id = await supabase.subscribe_to_a2a_messages(
            ...     agent_id=my_agent_id,
            ...     callback=handle_message,
            ... )
        """

        def handle_changes(payload):
            event_type = payload.get("eventType")
            data = (
                payload.get("new")
                if event_type in ["INSERT", "UPDATE"]
                else payload.get("old")
            )

            # Only process messages TO this agent
            if data.get("to_agent_id") == str(agent_id):
                asyncio.create_task(
                    callback({
                        "event": event_type,
                        "table": "a2a_messages",
                        "data": data,
                        "timestamp": datetime.now(),
                    })
                )

        subscription = (
            self.client.channel(f"a2a_{agent_id}")
            .on_postgres_changes(
                event="*",
                schema="public",
                table="a2a_messages",
                callback=handle_changes,
            )
            .subscribe()
        )

        sub_id = f"a2a_{agent_id}"
        self.subscriptions[sub_id] = subscription

        return sub_id

    async def subscribe_to_llm_collaborations(
        self, callback: Callable[[Dict[str, Any]], None]
    ) -> str:
        """
        Subscribe to LLM collaboration events.

        Args:
            callback: Async function called for collaboration completions

        Returns:
            Subscription ID

        Example:
            >>> async def track_collaborations(event):
            ...     if event['event'] == 'UPDATE':
            ...         collab = event['data']
            ...         if collab['status'] == 'completed':
            ...             print(f"Collaboration done: {collab['strategy']}")
            ...
            >>> sub_id = await supabase.subscribe_to_llm_collaborations(track_collaborations)
        """

        def handle_changes(payload):
            event_type = payload.get("eventType")
            data = (
                payload.get("new")
                if event_type in ["INSERT", "UPDATE"]
                else payload.get("old")
            )

            asyncio.create_task(
                callback({
                    "event": event_type,
                    "table": "llm_collaborations",
                    "data": data,
                    "timestamp": datetime.now(),
                })
            )

        subscription = (
            self.client.channel("llm_collabs")
            .on_postgres_changes(
                event="*",
                schema="public",
                table="llm_collaborations",
                callback=handle_changes,
            )
            .subscribe()
        )

        sub_id = f"llm_collabs_{id(subscription)}"
        self.subscriptions[sub_id] = subscription

        return sub_id

    def unsubscribe(self, subscription_id: str) -> None:
        """
        Unsubscribe from real-time updates.

        Args:
            subscription_id: ID returned from subscribe_* methods

        Example:
            >>> sub_id = await supabase.subscribe_to_agent_updates(handler)
            >>> # Later...
            >>> supabase.unsubscribe(sub_id)
        """
        if subscription_id in self.subscriptions:
            subscription = self.subscriptions[subscription_id]
            subscription.unsubscribe()
            del self.subscriptions[subscription_id]

    def unsubscribe_all(self) -> None:
        """Unsubscribe from all active subscriptions."""
        for sub_id in list(self.subscriptions.keys()):
            self.unsubscribe(sub_id)

    # ============================================================================
    # Broadcasting (Publish Events)
    # ============================================================================

    async def broadcast_agent_status(
        self, agent_id: UUID, status: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Broadcast agent status update to all subscribers.

        Args:
            agent_id: Agent's UUID
            status: New status (active, idle, busy, error)
            metadata: Optional additional data

        Example:
            >>> await supabase.broadcast_agent_status(
            ...     agent_id=my_agent_id,
            ...     status="busy",
            ...     metadata={"current_task": "analyzing_contract_123"},
            ... )
        """
        channel = self.client.channel("agent_status")
        await channel.send({
            "type": "broadcast",
            "event": "status_update",
            "payload": {
                "agent_id": str(agent_id),
                "status": status,
                "metadata": metadata or {},
                "timestamp": datetime.now().isoformat(),
            },
        })

    async def broadcast_task_completion(
        self, task_id: UUID, result: Dict[str, Any]
    ) -> None:
        """
        Broadcast task completion event.

        Args:
            task_id: Completed task's UUID
            result: Task result data

        Example:
            >>> await supabase.broadcast_task_completion(
            ...     task_id=task_id,
            ...     result={"status": "success", "output": {...}},
            ... )
        """
        channel = self.client.channel("task_updates")
        await channel.send({
            "type": "broadcast",
            "event": "task_completed",
            "payload": {
                "task_id": str(task_id),
                "result": result,
                "timestamp": datetime.now().isoformat(),
            },
        })

    # ============================================================================
    # Data Sync (Local PostgreSQL <-> Supabase)
    # ============================================================================

    async def sync_agents_to_supabase(self, agents_data: List[Dict[str, Any]]) -> int:
        """
        Sync agent data from local PostgreSQL to Supabase.

        Args:
            agents_data: List of agent records to sync

        Returns:
            Number of records synced

        Example:
            >>> agents = await local_db.query("SELECT * FROM agents")
            >>> count = await supabase.sync_agents_to_supabase(agents)
            >>> print(f"Synced {count} agents")
        """
        try:
            # Upsert agents (insert or update)
            result = self.client.table("agents").upsert(agents_data).execute()

            return len(result.data) if result.data else 0
        except Exception as e:
            print(f"Sync error: {e}")
            return 0

    async def sync_tasks_to_supabase(self, tasks_data: List[Dict[str, Any]]) -> int:
        """
        Sync task data to Supabase.

        Args:
            tasks_data: List of task records

        Returns:
            Number of records synced
        """
        try:
            result = self.client.table("tasks").upsert(tasks_data).execute()
            return len(result.data) if result.data else 0
        except Exception as e:
            print(f"Sync error: {e}")
            return 0

    async def sync_a2a_messages_to_supabase(
        self, messages_data: List[Dict[str, Any]]
    ) -> int:
        """
        Sync A2A messages to Supabase.

        Args:
            messages_data: List of message records

        Returns:
            Number of records synced
        """
        try:
            result = self.client.table("a2a_messages").upsert(messages_data).execute()
            return len(result.data) if result.data else 0
        except Exception as e:
            print(f"Sync error: {e}")
            return 0

    # ============================================================================
    # Storage (Artifacts, Files, Outputs)
    # ============================================================================

    async def upload_artifact(
        self,
        bucket_name: str,
        file_path: str,
        file_data: bytes,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """
        Upload agent artifact to Supabase Storage.

        Args:
            bucket_name: Storage bucket (e.g., 'agent-artifacts')
            file_path: Path within bucket (e.g., 'agent_123/output.json')
            file_data: File contents as bytes
            content_type: MIME type (e.g., 'application/json')
            metadata: Optional file metadata

        Returns:
            Public URL if successful, None otherwise

        Example:
            >>> url = await supabase.upload_artifact(
            ...     bucket_name="agent-artifacts",
            ...     file_path=f"agent_{agent_id}/result_{task_id}.json",
            ...     file_data=json.dumps(result).encode(),
            ...     content_type="application/json",
            ... )
            >>> if url:
            ...     print(f"Artifact uploaded: {url}")
        """
        try:
            # Upload file
            self.client.storage.from_(bucket_name).upload(
                path=file_path,
                file=file_data,
                file_options={
                    "content-type": content_type or "application/octet-stream",
                    "x-upsert": "true",  # Overwrite if exists
                },
            )

            # Get public URL
            public_url = self.client.storage.from_(bucket_name).get_public_url(file_path)

            return public_url

        except Exception as e:
            print(f"Upload error: {e}")
            return None

    async def download_artifact(
        self, bucket_name: str, file_path: str
    ) -> Optional[bytes]:
        """
        Download artifact from Supabase Storage.

        Args:
            bucket_name: Storage bucket
            file_path: File path within bucket

        Returns:
            File contents as bytes, or None if not found

        Example:
            >>> data = await supabase.download_artifact(
            ...     bucket_name="agent-artifacts",
            ...     file_path="agent_123/result.json",
            ... )
            >>> if data:
            ...     result = json.loads(data)
        """
        try:
            response = self.client.storage.from_(bucket_name).download(file_path)
            return response
        except Exception as e:
            print(f"Download error: {e}")
            return None

    async def list_artifacts(
        self, bucket_name: str, folder_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List artifacts in a bucket/folder.

        Args:
            bucket_name: Storage bucket
            folder_path: Optional folder path to list

        Returns:
            List of file objects

        Example:
            >>> files = await supabase.list_artifacts(
            ...     bucket_name="agent-artifacts",
            ...     folder_path="agent_123/",
            ... )
            >>> for file in files:
            ...     print(f"{file['name']}: {file['size']} bytes")
        """
        try:
            files = self.client.storage.from_(bucket_name).list(folder_path)
            return files
        except Exception as e:
            print(f"List error: {e}")
            return []

    # ============================================================================
    # Queries (Read from Supabase)
    # ============================================================================

    async def get_agent(self, agent_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get agent by ID from Supabase.

        Args:
            agent_id: Agent's UUID

        Returns:
            Agent data dict or None

        Example:
            >>> agent = await supabase.get_agent(agent_id)
            >>> if agent:
            ...     print(f"Agent: {agent['name']}, Status: {agent['status']}")
        """
        try:
            result = (
                self.client.table("agents")
                .select("*")
                .eq("id", str(agent_id))
                .limit(1)
                .execute()
            )

            return result.data[0] if result.data else None
        except Exception:
            return None

    async def get_active_agents(self) -> List[Dict[str, Any]]:
        """
        Get all active agents from Supabase.

        Returns:
            List of active agent dicts

        Example:
            >>> agents = await supabase.get_active_agents()
            >>> print(f"Active agents: {len(agents)}")
        """
        try:
            result = (
                self.client.table("agents")
                .select("*")
                .eq("status", "active")
                .execute()
            )

            return result.data if result.data else []
        except Exception:
            return []

    async def get_pending_tasks(
        self, agent_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Get pending tasks from Supabase.

        Args:
            agent_id: Optional agent filter

        Returns:
            List of pending task dicts

        Example:
            >>> tasks = await supabase.get_pending_tasks(agent_id=my_agent_id)
            >>> for task in tasks:
            ...     print(f"Task: {task['description']}")
        """
        try:
            query = self.client.table("tasks").select("*").eq("status", "pending")

            if agent_id:
                query = query.eq("agent_id", str(agent_id))

            result = query.execute()

            return result.data if result.data else []
        except Exception:
            return []

    # ============================================================================
    # Analytics & Monitoring
    # ============================================================================

    async def get_agent_stats(self, agent_id: UUID) -> Dict[str, Any]:
        """
        Get agent statistics from Supabase.

        Args:
            agent_id: Agent's UUID

        Returns:
            Statistics dict

        Example:
            >>> stats = await supabase.get_agent_stats(my_agent_id)
            >>> print(f"Tasks completed: {stats['tasks_completed']}")
        """
        try:
            # Query stats view
            result = (
                self.client.table("agent_stats")
                .select("*")
                .eq("agent_id", str(agent_id))
                .limit(1)
                .execute()
            )

            return result.data[0] if result.data else {}
        except Exception:
            return {}

    async def get_system_health(self) -> Dict[str, Any]:
        """
        Get overall system health metrics from Supabase.

        Returns:
            Health metrics dict

        Example:
            >>> health = await supabase.get_system_health()
            >>> print(f"Total agents: {health['total_agents']}")
            >>> print(f"Active tasks: {health['active_tasks']}")
        """
        try:
            # Get counts from various tables
            agents_count = len(
                self.client.table("agents").select("id", count="exact").execute().data
            )
            active_agents = len(
                self.client.table("agents")
                .select("id", count="exact")
                .eq("status", "active")
                .execute()
                .data
            )
            pending_tasks = len(
                self.client.table("tasks")
                .select("id", count="exact")
                .eq("status", "pending")
                .execute()
                .data
            )

            return {
                "total_agents": agents_count,
                "active_agents": active_agents,
                "pending_tasks": pending_tasks,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception:
            return {}


# Singleton instance
_supabase_instance: Optional[SupabaseService] = None


def get_supabase_service(
    supabase_url: Optional[str] = None, supabase_key: Optional[str] = None
) -> SupabaseService:
    """
    Get singleton Supabase service instance.

    Args:
        supabase_url: Supabase project URL (first call only)
        supabase_key: Supabase key (first call only)

    Returns:
        SupabaseService instance

    Example:
        >>> supabase = get_supabase_service(
        ...     supabase_url=os.getenv("SUPABASE_URL"),
        ...     supabase_key=os.getenv("SUPABASE_KEY"),
        ... )
    """
    global _supabase_instance

    if _supabase_instance is None:
        if not supabase_url or not supabase_key:
            raise ValueError("supabase_url and supabase_key required for first call")

        _supabase_instance = SupabaseService(
            supabase_url=supabase_url, supabase_key=supabase_key
        )

    return _supabase_instance
