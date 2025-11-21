"""
Base MCP Agent - Foundation for all MCP system agents
Integrates with the Multi-Agent Learning Ecosystem and Supabase
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import psycopg2
from psycopg2.extras import Json
import uuid
from datetime import datetime
import logging
import os
import hashlib
import json

# Import Supabase integration (optional - graceful degradation)
try:
    import sys
    from pathlib import Path
    # Dynamically find the repository root
    repo_root = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(repo_root))
    from cesar.integrations.supabase_integration import SupabaseIntegration, SupabaseConfig
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

# Import DataBrain integration (optional - graceful degradation)
try:
    services_path = Path(__file__).resolve().parent.parent / "services"
    sys.path.insert(0, str(services_path))
    from brain_agent_integration import DataBrainAgent
    DATABRAIN_AVAILABLE = True
except ImportError as e:
    logging.warning(f"DataBrain integration not available: {e}")
    DATABRAIN_AVAILABLE = False

# Import Response Cache Service (optional - graceful degradation)
try:
    from response_cache_service import get_response_cache
    RESPONSE_CACHE_AVAILABLE = True
except ImportError:
    logging.info("Response cache service not available, running without cache")
    RESPONSE_CACHE_AVAILABLE = False

class BaseMCPAgent(ABC):
    """
    Base class for all MCP agents that integrates with the learning ecosystem
    and Supabase for daily data refresh and real-time updates
    """

    def __init__(
        self,
        agent_id: str,
        mcp_system: str,
        db_dsn: str = None,
        enable_supabase: bool = None,
        enable_databrain: bool = None
    ):
        """
        Initialize base MCP agent

        Args:
            agent_id: Unique agent identifier
            mcp_system: MCP system name (pydini_red, finpsy, lex, etc.)
            db_dsn: PostgreSQL connection string
            enable_supabase: Enable Supabase integration (defaults to env var)
            enable_databrain: Enable DataBrain GRAPH_STATE integration (defaults to env var)
        """
        self.agent_id = agent_id
        self.mcp_system = mcp_system
        self.db_dsn = db_dsn or "postgresql://mcp_user:change-this-in-production-use-strong-password@postgres:5432/mcp"
        self.logger = logging.getLogger(f"mcp.{mcp_system}.{agent_id}")

        # Supabase integration
        self.supabase: Optional[SupabaseIntegration] = None
        self._enable_supabase = enable_supabase if enable_supabase is not None else os.getenv("ENABLE_SUPABASE", "false").lower() == "true"

        if self._enable_supabase and SUPABASE_AVAILABLE:
            self._initialize_supabase()

        # DataBrain integration
        self.databrain: Optional[DataBrainAgent] = None
        self._enable_databrain = enable_databrain if enable_databrain is not None else os.getenv("ENABLE_DATABRAIN", "true").lower() == "true"

        if self._enable_databrain and DATABRAIN_AVAILABLE:
            self._initialize_databrain()

        # Response Cache integration
        self.response_cache = None
        self._enable_cache = os.getenv("ENABLE_RESPONSE_CACHE", "true").lower() == "true"

        if self._enable_cache and RESPONSE_CACHE_AVAILABLE:
            self._initialize_response_cache()

    def _initialize_supabase(self):
        """Initialize Supabase integration if configured"""
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")

            if supabase_url and supabase_key:
                config = SupabaseConfig(
                    url=supabase_url,
                    key=supabase_key,
                    auto_refresh=True
                )
                self.supabase = SupabaseIntegration(config)
                self.logger.info(f"Supabase integration enabled for {self.agent_id}")
            else:
                self.logger.warning("Supabase credentials not found in environment")
        except Exception as e:
            self.logger.error(f"Failed to initialize Supabase: {e}")
            self.supabase = None

    def _initialize_databrain(self):
        """Initialize DataBrain GRAPH_STATE integration"""
        try:
            cockroach_url = os.getenv("COCKROACH_DB_URL")
            if not cockroach_url or "pending" in cockroach_url:
                self.logger.warning("COCKROACH_DB_URL not configured, DataBrain disabled")
                return

            self.databrain = DataBrainAgent(
                agent_id=self.agent_id,
                db_url=cockroach_url
            )
            self.logger.info(f"✅ DataBrain GRAPH_STATE integration enabled for {self.agent_id}")
        except Exception as e:
            self.logger.error(f"Failed to initialize DataBrain: {e}")
            self.databrain = None

    def _initialize_response_cache(self):
        """Initialize Response Cache for LLM query optimization"""
        try:
            self.response_cache = get_response_cache()
            self.logger.info(f"✅ Response cache enabled for {self.agent_id} (20-30% cost savings)")
        except Exception as e:
            self.logger.error(f"Failed to initialize response cache: {e}")
            self.response_cache = None

    async def initialize_async(self):
        """Initialize async components (Supabase)"""
        if self.supabase:
            await self.supabase.initialize()
            self.logger.info(f"Supabase initialized for {self.agent_id}")

    def get_connection(self) -> psycopg2.extensions.connection:
        """Get database connection"""
        return psycopg2.connect(self.db_dsn)

    async def sync_to_supabase(self, table: str, data: Dict[str, Any]) -> bool:
        """
        Sync data to Supabase table

        Args:
            table: Supabase table name
            data: Data to sync

        Returns:
            Success status
        """
        if not self.supabase:
            self.logger.debug("Supabase not enabled, skipping sync")
            return False

        try:
            result = await self.supabase.insert_record(
                table=table,
                data={
                    **data,
                    "mcp_system": self.mcp_system,
                    "agent_id": self.agent_id,
                    "synced_at": datetime.now().isoformat()
                },
                upsert=True
            )
            return result is not None
        except Exception as e:
            self.logger.error(f"Failed to sync to Supabase: {e}")
            return False

    async def get_from_supabase(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get data from Supabase table

        Args:
            table: Table name
            filters: Optional filters

        Returns:
            List of records
        """
        if not self.supabase:
            self.logger.debug("Supabase not enabled")
            return []

        try:
            agent_filters = filters or {}
            agent_filters["mcp_system"] = self.mcp_system

            return await self.supabase.query_table(
                table=table,
                filters=agent_filters
            )
        except Exception as e:
            self.logger.error(f"Failed to get from Supabase: {e}")
            return []

    def get_brain_context(self, query: str, max_neighbors: int = 5) -> Dict[str, Any]:
        """
        Get GRAPH_STATE context from DataBrain for a query.
        This provides semantic context from the living knowledge graph.

        Args:
            query: Query string to search for related knowledge
            max_neighbors: Maximum number of connected neighbors to return

        Returns:
            Dict with current_node_context and connected_neighbors
        """
        if not self.databrain:
            self.logger.debug("DataBrain not enabled, returning empty context")
            return {"current_node_context": None, "connected_neighbors": [], "query": query}

        try:
            return self.databrain.get_graph_context(query, max_neighbors)
        except Exception as e:
            self.logger.error(f"Failed to get brain context: {e}")
            return {"current_node_context": None, "connected_neighbors": [], "query": query, "error": str(e)}

    def mutate_brain(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Apply neuroplasticity mutations to the DataBrain.
        Use this after processing to update the knowledge graph.

        Supported actions:
        - CREATE_NODE: Add new knowledge node
        - CREATE_LINK: Connect related concepts
        - DECAY_NODE: Reduce importance of stale knowledge
        - UPDATE_MASS: Boost importance of relevant knowledge

        Args:
            actions: List of neuroplasticity actions to apply

        Returns:
            Dict with mutation results
        """
        if not self.databrain:
            self.logger.debug("DataBrain not enabled, skipping mutations")
            return {"applied": 0, "results": []}

        try:
            return self.databrain.apply_neuroplasticity(actions)
        except Exception as e:
            self.logger.error(f"Failed to mutate brain: {e}")
            return {"applied": 0, "results": [], "error": str(e)}

    def get_cached_llm_response(
        self,
        query: str,
        llm_callable: callable,
        context_hash: Optional[str] = None,
        ttl_seconds: Optional[int] = None
    ) -> Any:
        """
        Get LLM response with transparent caching.
        This sits ABOVE the LLM adapter and does NOT modify routing logic.

        Workflow:
        1. Check cache for existing response
        2. If hit, return cached response (saves cost + latency)
        3. If miss, call LLM
        4. Store response in cache for future requests

        Args:
            query: Query string (used for cache key)
            llm_callable: Function to call if cache misses (e.g., lambda: adapter.generate(...))
            context_hash: Optional hash of contextual data (for cache isolation)
            ttl_seconds: Custom TTL (uses default if None)

        Returns:
            LLM response (from cache or fresh call)
        """
        if not self.response_cache:
            # Cache disabled, call LLM directly
            return llm_callable()

        # Step 1: Check cache
        cached = self.response_cache.get(
            query=query,
            context_hash=context_hash,
            agent_name=self.agent_id
        )

        if cached:
            # Cache HIT - return cached response
            self.logger.debug(f"Cache HIT for query: {query[:50]}...")
            # Remove cache metadata before returning
            cached.pop("_cache_metadata", None)
            return cached

        # Step 2: Cache MISS - call LLM
        self.logger.debug(f"Cache MISS for query: {query[:50]}...")
        response = llm_callable()

        # Step 3: Store in cache
        # Convert LLMResponse object to dict if needed
        if hasattr(response, '__dict__'):
            response_dict = {
                "content": response.content,
                "model_used": response.model_used,
                "confidence": response.confidence,
                "cost": response.cost,
                "latency_ms": response.latency_ms,
                "metadata": response.metadata
            }
        else:
            response_dict = response

        self.response_cache.set(
            query=query,
            response=response_dict,
            context_hash=context_hash,
            agent_name=self.agent_id,
            ttl_seconds=ttl_seconds
        )

        return response

    def process_with_brain(self, query: str, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced processing with DataBrain integration.
        This is the recommended method to use for brain-aware agents.

        Workflow:
        1. Get GRAPH_STATE context from DataBrain
        2. Inject context into processing
        3. Call process() with enriched input
        4. Apply neuroplasticity mutations based on results

        Args:
            query: Query string for context retrieval
            task_input: Original task input

        Returns:
            Dict with output and brain integration metadata
        """
        # Step 1: Get graph context
        graph_state = self.get_brain_context(query)

        # Step 2: Enrich input with context
        enriched_input = {
            **task_input,
            "GRAPH_STATE": graph_state,
            "brain_enhanced": True
        }

        # Step 3: Process with enriched context
        output = self.process(enriched_input)

        # Step 4: Apply neuroplasticity (boost accessed nodes)
        if graph_state.get("current_node_context"):
            mutations = [
                {
                    "action": "UPDATE_MASS",
                    "params": {
                        "target_id": graph_state["current_node_context"]["id"],
                        "delta": 2.0
                    }
                }
            ]
            mutation_result = self.mutate_brain(mutations)
            output["brain_mutation"] = mutation_result

        return output

    def create_task(
        self,
        task_type: str,
        input_data: Dict[str, Any],
        material_id: Optional[uuid.UUID] = None,
        priority: int = 5
    ) -> uuid.UUID:
        """
        Create an MCP task in the database

        Args:
            task_type: Type of task to create
            input_data: Input data for the task
            material_id: Optional related learning material ID
            priority: Task priority (1-10)

        Returns:
            UUID of created task
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            task_id_str = f"{self.mcp_system}_{task_type}_{uuid.uuid4()}"

            cursor.execute("""
                INSERT INTO mcp_tasks (
                    task_id, mcp_system, agent_id, task_type,
                    input_data, related_material_id, priority, status,
                    started_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                task_id_str,
                self.mcp_system,
                self.agent_id,
                task_type,
                Json(input_data),
                material_id,
                priority,
                'running',
                datetime.now()
            ))

            task_id = cursor.fetchone()[0]
            conn.commit()

            self.logger.info(f"Created task {task_id_str} (UUID: {task_id})")
            return task_id

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Failed to create task: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    def update_task_status(
        self,
        task_id: uuid.UUID,
        status: str,
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ):
        """
        Update task status in the database

        Args:
            task_id: Task UUID
            status: New status (running, completed, failed)
            output_data: Output data if completed
            error_message: Error message if failed
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            if status == 'completed' or status == 'failed':
                cursor.execute("""
                    UPDATE mcp_tasks
                    SET status = %s,
                        output_data = %s,
                        error_message = %s,
                        completed_at = %s
                    WHERE id = %s
                """, (
                    status,
                    Json(output_data) if output_data else None,
                    error_message,
                    datetime.now(),
                    task_id
                ))
            else:
                cursor.execute("""
                    UPDATE mcp_tasks
                    SET status = %s
                    WHERE id = %s
                """, (status, task_id))

            conn.commit()
            self.logger.info(f"Updated task {task_id} to status: {status}")

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Failed to update task status: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    def log_activity(
        self,
        action: str,
        status: str = "SUCCESS",
        details: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log agent activity to activity_logs table

        Args:
            action: Action performed
            status: Status (SUCCESS, FAIL, WARNING, INFO)
            details: Additional details
            metadata: Optional metadata as JSON
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO activity_logs (
                    mcp_system, agent_name, action, status, details, metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                self.mcp_system,
                self.agent_id,
                action,
                status,
                details,
                Json(metadata) if metadata else None
            ))

            conn.commit()

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Failed to log activity: {e}")
        finally:
            cursor.close()
            conn.close()

    def add_to_vector_memory(
        self,
        content: str,
        context_type: str,
        vector: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add content to embedding memory

        Args:
            content: Text content
            context_type: Type of context
            vector: Pre-computed embedding (if None, needs to be computed)
            metadata: Optional metadata
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO vector_memory (
                    mcp_system, context_type, content, embedding, metadata
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                self.mcp_system,
                context_type,
                content,
                vector,
                Json(metadata) if metadata else None
            ))

            conn.commit()
            self.logger.info(f"Added to vector memory: {context_type}")

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Failed to add to vector memory: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    def get_similar_from_memory(
        self,
        vector: List[float],
        context_type: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query vector memory for similar content

        Args:
            vector: Query vector
            context_type: Optional filter by context type
            limit: Maximum number of results

        Returns:
            List of similar content with similarity scores
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            if context_type:
                cursor.execute("""
                    SELECT content, metadata,
                           1 - (embedding <=> %s::vector) as similarity
                    FROM vector_memory
                    WHERE mcp_system = %s AND context_type = %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """, (vector, self.mcp_system, context_type, vector, limit))
            else:
                cursor.execute("""
                    SELECT content, metadata,
                           1 - (embedding <=> %s::vector) as similarity
                    FROM vector_memory
                    WHERE mcp_system = %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """, (vector, self.mcp_system, vector, limit))

            results = cursor.fetchall()
            return [
                {
                    "content": row[0],
                    "metadata": row[1],
                    "similarity": float(row[2])
                }
                for row in results
            ]

        except Exception as e:
            self.logger.error(f"Failed to query vector memory: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

    @abstractmethod
    def process(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a task - must be implemented by subclasses

        Args:
            task_input: Input data for the task

        Returns:
            Dict containing task output
        """
        pass

    def execute_task(
        self,
        task_type: str,
        task_input: Dict[str, Any],
        material_id: Optional[uuid.UUID] = None,
        priority: int = 5
    ) -> Dict[str, Any]:
        """
        Complete task execution workflow: create, process, update

        Args:
            task_type: Type of task
            task_input: Input data
            material_id: Optional related material
            priority: Task priority

        Returns:
            Dict with task_id and output
        """
        task_id = None
        try:
            # Create task
            task_id = self.create_task(task_type, task_input, material_id, priority)

            # Process task
            self.log_activity(
                action=f"started_{task_type}",
                status="INFO",
                details=f"Processing task {task_id}"
            )

            output = self.process(task_input)

            # Update as completed
            self.update_task_status(task_id, 'completed', output)

            self.log_activity(
                action=f"completed_{task_type}",
                status="SUCCESS",
                details=f"Task {task_id} completed successfully"
            )

            return {
                "task_id": str(task_id),
                "status": "completed",
                "output": output
            }

        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")

            if task_id:
                self.update_task_status(
                    task_id,
                    'failed',
                    error_message=str(e)
                )

            self.log_activity(
                action=f"failed_{task_type}",
                status="FAIL",
                details=str(e)
            )

            return {
                "task_id": str(task_id) if task_id else None,
                "status": "failed",
                "error": str(e)
            }

    def get_task_status(self, task_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get current status of a task

        Args:
            task_id: Task UUID

        Returns:
            Dict with task details
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT task_id, status, output_data, error_message,
                       started_at, completed_at
                FROM mcp_tasks
                WHERE id = %s
            """, (task_id,))

            row = cursor.fetchone()
            if not row:
                return {"error": "Task not found"}

            return {
                "task_id": row[0],
                "status": row[1],
                "output": row[2],
                "error": row[3],
                "started_at": row[4].isoformat() if row[4] else None,
                "completed_at": row[5].isoformat() if row[5] else None
            }

        except Exception as e:
            self.logger.error(f"Failed to get task status: {e}")
            return {"error": str(e)}
        finally:
            cursor.close()
            conn.close()
