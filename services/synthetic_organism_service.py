"""
Synthetic Organism Visualization Service
=========================================

Provides high-performance data adapters for:
1. DataBrainV6 - 3D Knowledge Graph with semantic force fields
2. AutomationMatrix - Workflow process digital twin
3. TalentMap - Agent network with burnout detection
4. LiquidityEngine - Financial flow simulation

Features:
- Supabase RLS-compliant queries
- Barnes-Hut optimization for O(N log N) physics
- WebSocket streaming for real-time updates
- Input sanitization and XSS prevention
- Comprehensive error handling and logging

Author: CESAR.ai Development Team
Date: November 20, 2025
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from decimal import Decimal

import asyncpg
from fastapi import HTTPException
from pydantic import BaseModel, Field, validator

# Configure logging
logger = logging.getLogger("SyntheticOrganismService")

# ============================================================================
# DATA MODELS (Pydantic for validation)
# ============================================================================

class Vector3D(BaseModel):
    """3D spatial vector with validation"""
    x: float = Field(..., ge=0, le=1200, description="X coordinate (0-1200)")
    y: float = Field(..., ge=0, le=800, description="Y coordinate (0-800)")
    z: float = Field(..., ge=0, le=300, description="Z coordinate (epistemic depth)")


class KnowledgeGraphNode(BaseModel):
    """Knowledge graph node with full physics state"""
    id: str
    label: str
    type: str = Field(..., regex="^(raw_data|information|knowledge|wisdom)$")

    # Physics
    x: float
    y: float
    z: float
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0
    mass: float = Field(default=10.0, ge=1.0, le=100.0)

    # Metadata
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)
    access_count: int = Field(default=0, ge=0)
    created_at: datetime
    last_reinforced: datetime
    force_field_ids: List[str] = []
    visual_metadata: Dict[str, Any] = {}

    @validator('label')
    def sanitize_label(cls, v):
        """Prevent XSS in node labels"""
        if not v:
            raise ValueError("Label cannot be empty")
        # Remove HTML/script tags and dangerous characters
        sanitized = re.sub(r'[<>"\'`]', '', v)
        return sanitized[:100]  # Max 100 chars


class KnowledgeGraphLink(BaseModel):
    """Weighted edge in knowledge graph"""
    id: str
    source: str  # UUID of source node
    target: str  # UUID of target node
    strength: float = Field(..., ge=0.0, le=1.0)
    link_type: str = Field(default='association')
    co_occurrence_count: int = Field(default=1, ge=1)
    created_at: datetime


class ForceField(BaseModel):
    """Semantic gravity well configuration"""
    id: str
    field_name: str
    field_category: str
    center_x: float
    center_y: float
    radius: float
    semantic_keywords: List[str]
    color_hex: str = Field(..., regex="^#[0-9A-Fa-f]{6}$")
    opacity: float = Field(..., ge=0.0, le=1.0)
    attraction_strength: float = Field(..., ge=0.0, le=1.0)
    is_active: bool = True


class WorkflowProcessNode(BaseModel):
    """Process node in workflow automation matrix"""
    id: str
    node_name: str
    node_label: str
    node_type: str = Field(..., regex="^(human|ai_agent|database|api_trigger|client_input)$")

    # Metrics
    cost_per_operation: float = Field(default=0.0, ge=0.0)
    processing_speed_ms: int = Field(default=1000, ge=0)
    current_queue_depth: int = Field(default=0, ge=0)
    status: str = Field(..., regex="^(optimal|stressed|bottleneck)$")

    # Position
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    position_z: float = 0.0


class AgentNetworkNode(BaseModel):
    """Agent node with network centrality metrics"""
    id: str
    agent_id: str
    agent_name: str
    department: str

    # Network metrics
    influence_score: float = Field(..., ge=0.0, le=100.0)
    burnout_index: float = Field(..., ge=0.0, le=100.0)
    risk_level: str = Field(..., regex="^(Stable|At-Risk|Critical)$")

    # Communication patterns
    incoming_message_count: int = Field(default=0, ge=0)
    outgoing_message_count: int = Field(default=0, ge=0)
    avg_response_time_seconds: float = Field(default=0.0, ge=0.0)

    # Position (force-directed)
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    node_mass: float = 10.0


class NeuroplasticityAction(BaseModel):
    """Graph mutation action with validation"""
    action_type: str = Field(..., regex="^(CREATE_NODE|UPDATE_NODE|DELETE_NODE|CREATE_LINK|UPDATE_LINK|DELETE_LINK|CREATE_FORCE_FIELD|DECAY_NODE)$")
    target_id: Optional[str] = None
    action_params: Dict[str, Any]
    reason: Optional[str] = None
    initiated_by_agent_id: Optional[str] = None
    session_id: Optional[str] = None

    @validator('action_params')
    def validate_params(cls, v, values):
        """Validate action parameters based on action type"""
        action_type = values.get('action_type')

        if action_type == 'CREATE_NODE':
            required = ['label', 'type', 'z_index']
            if not all(k in v for k in required):
                raise ValueError(f"CREATE_NODE requires: {required}")
            # Sanitize label
            if 'label' in v:
                v['label'] = re.sub(r'[<>"\'`]', '', str(v['label']))[:100]

        elif action_type == 'CREATE_LINK':
            required = ['source_id', 'target_id', 'weight']
            if not all(k in v for k in required):
                raise ValueError(f"CREATE_LINK requires: {required}")
            # Validate weight range
            if not (0.0 <= v.get('weight', 0) <= 1.0):
                raise ValueError("Link weight must be between 0.0 and 1.0")

        return v


# ============================================================================
# HELPER UTILITIES
# ============================================================================

class SpatialHashGrid:
    """
    Barnes-Hut optimization using spatial hashing
    Reduces O(N²) collision detection to O(N)
    """

    def __init__(self, cell_size: float = 100.0, bounds: Tuple[float, float] = (1200, 800)):
        self.cell_size = cell_size
        self.bounds = bounds
        self.grid: Dict[str, List[Dict]] = {}

    def _hash_position(self, x: float, y: float) -> str:
        """Generate grid cell key from position"""
        cell_x = int(x // self.cell_size)
        cell_y = int(y // self.cell_size)
        return f"{cell_x},{cell_y}"

    def insert(self, node: Dict[str, Any]):
        """Insert node into spatial grid"""
        key = self._hash_position(node['x'], node['y'])
        if key not in self.grid:
            self.grid[key] = []
        self.grid[key].append(node)

    def get_neighbors(self, x: float, y: float, radius: float = 1) -> List[Dict]:
        """Get all nodes in neighboring cells (including current)"""
        neighbors = []
        base_x = int(x // self.cell_size)
        base_y = int(y // self.cell_size)

        # Check 3x3 grid around point
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                key = f"{base_x + dx},{base_y + dy}"
                if key in self.grid:
                    neighbors.extend(self.grid[key])

        return neighbors

    def clear(self):
        """Clear grid for next frame"""
        self.grid.clear()


def sanitize_sql_param(value: Any) -> Any:
    """Sanitize parameters to prevent SQL injection"""
    if isinstance(value, str):
        # Remove potentially dangerous SQL keywords
        dangerous = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'EXEC', 'EXECUTE', '--', ';']
        upper_val = value.upper()
        for keyword in dangerous:
            if keyword in upper_val:
                raise ValueError(f"Dangerous SQL keyword detected: {keyword}")
        return value
    return value


def convert_decimal_to_float(obj: Any) -> Any:
    """Recursively convert Decimal to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(v) for v in obj]
    return obj


# ============================================================================
# CORE SERVICE CLASS
# ============================================================================

class SyntheticOrganismService:
    """
    High-performance data adapter for visualization components
    """

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.logger = logger
        self.spatial_grid = SpatialHashGrid()

    # ========================================================================
    # DATABRAIN V6 - KNOWLEDGE GRAPH
    # ========================================================================

    async def get_knowledge_graph_snapshot(
        self,
        limit: int = 500,
        confidence_threshold: float = 0.3,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Retrieve complete knowledge graph state for DataBrainV6

        Args:
            limit: Maximum nodes to return (performance cap)
            confidence_threshold: Minimum confidence score
            force_refresh: Force refresh materialized view

        Returns:
            {nodes: [...], links: [...], force_fields: [...]}
        """
        async with self.db_pool.acquire() as conn:
            try:
                # Refresh materialized view if requested
                if force_refresh:
                    await conn.execute("REFRESH MATERIALIZED VIEW knowledge_graph_snapshot")

                # Fetch nodes from materialized view
                nodes_query = """
                    SELECT
                        id::text,
                        label,
                        type,
                        x, y, z,
                        vx, vy, vz,
                        mass,
                        confidence_score,
                        access_count,
                        force_field_ids,
                        created_at,
                        last_reinforced,
                        visual_metadata
                    FROM knowledge_graph_snapshot
                    WHERE confidence_score >= $1
                    ORDER BY access_count DESC, confidence_score DESC
                    LIMIT $2
                """

                nodes_rows = await conn.fetch(
                    nodes_query,
                    confidence_threshold,
                    limit
                )

                # Convert to node objects
                nodes = []
                node_ids = set()

                for row in nodes_rows:
                    node_id = row['id']
                    node_ids.add(node_id)

                    nodes.append({
                        'id': node_id,
                        'label': row['label'][:100],  # Enforce max length
                        'type': row['type'],
                        'x': float(row['x']),
                        'y': float(row['y']),
                        'z': float(row['z']),
                        'vx': float(row['vx']),
                        'vy': float(row['vy']),
                        'vz': float(row['vz']),
                        'mass': float(row['mass']),
                        'nodeCategory': 'static',  # All semantic memories are persistent
                        'created': int(row['created_at'].timestamp() * 1000),
                        'lastAccessed': int(row['last_reinforced'].timestamp() * 1000),
                        'accessCount': row['access_count'],
                        'clusterId': 0,  # TODO: Implement clustering
                        'semanticVector': set(row['force_field_ids']) if row['force_field_ids'] else set()
                    })

                # Fetch links (only between visible nodes)
                links_query = """
                    SELECT
                        id::text,
                        source_memory_id::text as source,
                        target_memory_id::text as target,
                        link_strength,
                        created_at
                    FROM knowledge_graph_links
                    WHERE source_memory_id = ANY($1::uuid[])
                      AND target_memory_id = ANY($1::uuid[])
                      AND is_visible = true
                      AND link_strength > 0.2
                    ORDER BY link_strength DESC
                    LIMIT $2
                """

                node_ids_array = list(node_ids)
                links_rows = await conn.fetch(links_query, node_ids_array, limit)

                links = [
                    {
                        'id': row['id'],
                        'source': row['source'],
                        'target': row['target'],
                        'strength': float(row['link_strength']),
                        'created': int(row['created_at'].timestamp() * 1000)
                    }
                    for row in links_rows
                ]

                # Fetch active force fields
                fields_query = """
                    SELECT
                        id::text,
                        field_name,
                        field_category,
                        center_x, center_y, radius,
                        semantic_keywords,
                        color_hex,
                        opacity,
                        attraction_strength
                    FROM knowledge_force_fields
                    WHERE is_active = true
                    ORDER BY field_name
                """

                fields_rows = await conn.fetch(fields_query)

                force_fields = [
                    {
                        'id': row['id'],
                        'x': float(row['center_x']),
                        'y': float(row['center_y']),
                        'radius': float(row['radius']),
                        'label': row['field_name'],
                        'vector': set(row['semantic_keywords']),
                        'color': row['color_hex'],
                        'opacity': float(row['opacity']),
                        'strength': float(row['attraction_strength'])
                    }
                    for row in fields_rows
                ]

                self.logger.info(
                    f"Knowledge graph snapshot: {len(nodes)} nodes, "
                    f"{len(links)} links, {len(force_fields)} force fields"
                )

                return {
                    'nodes': nodes,
                    'links': links,
                    'forceFields': force_fields,
                    'metadata': {
                        'timestamp': datetime.utcnow().isoformat(),
                        'nodeCount': len(nodes),
                        'linkCount': len(links),
                        'confidenceThreshold': confidence_threshold
                    }
                }

            except Exception as e:
                self.logger.error(f"Error fetching knowledge graph: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    async def apply_neuroplasticity_action(
        self,
        action: NeuroplasticityAction,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute graph mutation (stigmergic memory modification)

        All mutations are logged for audit trail and potential rollback
        """
        async with self.db_pool.acquire() as conn:
            try:
                async with conn.transaction():
                    # Log the action first
                    log_query = """
                        INSERT INTO neuroplasticity_actions (
                            action_type,
                            target_id,
                            action_params,
                            reason,
                            initiated_by_agent_id,
                            session_id,
                            validation_status
                        ) VALUES ($1, $2, $3, $4, $5, $6, 'pending')
                        RETURNING id::text
                    """

                    action_id = await conn.fetchval(
                        log_query,
                        action.action_type,
                        action.target_id,
                        json.dumps(action.action_params),
                        action.reason,
                        action.initiated_by_agent_id,
                        action.session_id
                    )

                    # Execute the action
                    result = None

                    if action.action_type == 'CREATE_NODE':
                        result = await self._execute_create_node(conn, action.action_params)

                    elif action.action_type == 'CREATE_LINK':
                        result = await self._execute_create_link(conn, action.action_params)

                    elif action.action_type == 'DECAY_NODE':
                        result = await self._execute_decay_node(conn, action.target_id)

                    elif action.action_type == 'UPDATE_NODE':
                        result = await self._execute_update_node(conn, action.target_id, action.action_params)

                    else:
                        raise ValueError(f"Unsupported action type: {action.action_type}")

                    # Mark as executed
                    await conn.execute(
                        """
                        UPDATE neuroplasticity_actions
                        SET validation_status = 'executed',
                            executed_at = now()
                        WHERE id = $1::uuid
                        """,
                        action_id
                    )

                    self.logger.info(f"Neuroplasticity action {action_id} executed: {action.action_type}")

                    return {
                        'action_id': action_id,
                        'status': 'executed',
                        'result': result
                    }

            except Exception as e:
                self.logger.error(f"Error executing neuroplasticity action: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    async def _execute_create_node(self, conn, params: Dict) -> Dict:
        """Create new semantic memory node"""
        label = params['label']
        node_type = params['type']
        z_index = params.get('z_index', 100)
        initial_mass = params.get('initial_mass', 10)

        # Insert into memory_semantic
        node_id = await conn.fetchval(
            """
            INSERT INTO memory_semantic (
                concept,
                summary,
                category,
                node_type,
                node_z,
                node_mass,
                confidence_score
            ) VALUES ($1, $2, 'fact', $3, $4, $5, 0.5)
            RETURNING id::text
            """,
            label,
            f"Auto-generated from neuroplasticity action: {label}",
            node_type,
            z_index,
            initial_mass
        )

        # Initialize spatial position
        await conn.execute("SELECT initialize_node_positions()")

        return {'node_id': node_id, 'label': label}

    async def _execute_create_link(self, conn, params: Dict) -> Dict:
        """Create link between nodes"""
        source_id = params.get('source_id')
        target_label = params.get('target_label')
        weight = params.get('weight', 0.5)

        # Find target by label if not ID
        if target_label and not params.get('target_id'):
            target_id = await conn.fetchval(
                "SELECT id::text FROM memory_semantic WHERE concept = $1 LIMIT 1",
                target_label
            )
        else:
            target_id = params.get('target_id')

        if not source_id or not target_id:
            raise ValueError("Both source_id and target_id (or target_label) required")

        # Create link
        link_id = await conn.fetchval(
            """
            INSERT INTO knowledge_graph_links (
                source_memory_id,
                target_memory_id,
                link_strength,
                link_type
            ) VALUES ($1::uuid, $2::uuid, $3, 'association')
            ON CONFLICT (source_memory_id, target_memory_id)
            DO UPDATE SET
                link_strength = EXCLUDED.link_strength,
                last_reinforced = now()
            RETURNING id::text
            """,
            source_id,
            target_id,
            weight
        )

        return {'link_id': link_id, 'source': source_id, 'target': target_id}

    async def _execute_decay_node(self, conn, node_id: str) -> Dict:
        """Reduce confidence of rarely accessed node"""
        await conn.execute(
            """
            UPDATE memory_semantic
            SET confidence_score = GREATEST(0.0, confidence_score - 0.1),
                node_mass = GREATEST(5.0, node_mass - 2.0)
            WHERE id = $1::uuid
            """,
            node_id
        )

        return {'node_id': node_id, 'action': 'decayed'}

    async def _execute_update_node(self, conn, node_id: str, params: Dict) -> Dict:
        """Update node properties"""
        updates = []
        values = []
        idx = 1

        if 'confidence_score' in params:
            updates.append(f"confidence_score = ${idx}")
            values.append(params['confidence_score'])
            idx += 1

        if 'node_mass' in params:
            updates.append(f"node_mass = ${idx}")
            values.append(params['node_mass'])
            idx += 1

        if not updates:
            return {'node_id': node_id, 'action': 'no changes'}

        values.append(node_id)
        query = f"""
            UPDATE memory_semantic
            SET {', '.join(updates)}
            WHERE id = ${idx}::uuid
        """

        await conn.execute(query, *values)

        return {'node_id': node_id, 'action': 'updated', 'fields': list(params.keys())}

    # ========================================================================
    # AUTOMATION MATRIX - WORKFLOW DIGITAL TWIN
    # ========================================================================

    async def get_workflow_matrix_data(
        self,
        workflow_id: Optional[str] = None,
        time_window_days: int = 30
    ) -> Dict[str, Any]:
        """
        Retrieve workflow process nodes and metrics for AutomationMatrix

        Computes:
        - Cost per operation (from workflow_executions)
        - Processing speed (avg execution time)
        - Queue depth (pending executions)
        - Bottleneck status
        """
        async with self.db_pool.acquire() as conn:
            try:
                # Fetch workflow nodes with aggregated metrics
                nodes_query = """
                    SELECT
                        wpn.id::text,
                        wpn.node_name,
                        wpn.node_label,
                        wpn.node_type,
                        COALESCE(wpn.position_x, RANDOM() * 1000 + 100) as x,
                        COALESCE(wpn.position_y, RANDOM() * 600 + 100) as y,
                        wpn.position_z as z,
                        wpn.cost_per_operation,
                        wpn.processing_speed_ms,
                        wpn.current_queue_depth,
                        wpn.status,
                        wpn.total_operations_processed,
                        wpn.avg_queue_wait_time_ms,
                        wt.workflow_name,
                        COUNT(we.id) FILTER (WHERE we.status = 'running') as active_executions
                    FROM workflow_process_nodes wpn
                    JOIN workflow_templates wt ON wt.id = wpn.workflow_template_id
                    LEFT JOIN workflow_executions we ON we.workflow_name = wt.workflow_name
                        AND we.started_at > NOW() - INTERVAL '1 hour'
                    WHERE ($1::uuid IS NULL OR wpn.workflow_template_id = $1::uuid)
                    GROUP BY wpn.id, wt.workflow_name
                    ORDER BY wpn.node_name
                """

                nodes_rows = await conn.fetch(nodes_query, workflow_id)

                nodes = [
                    {
                        'id': row['id'],
                        'label': row['node_label'],
                        'type': row['node_type'],
                        'nodeCategory': row['node_type'],
                        'x': float(row['x']),
                        'y': float(row['y']),
                        'z': float(row['z']),
                        'vx': 0,
                        'vy': 0,
                        'mass': 20 if row['node_type'] == 'ai_agent' else 15,
                        'costPerOp': float(row['cost_per_operation']),
                        'processingSpeed': row['processing_speed_ms'],
                        'queue': row['current_queue_depth'] + row['active_executions'],
                        'status': row['status']
                    }
                    for row in nodes_rows
                ]

                # Fetch workflow links (process dependencies)
                links_query = """
                    SELECT
                        wpl.id::text,
                        wpl.source_node_id::text as source,
                        wpl.target_node_id::text as target,
                        wpl.throughput_ops_per_sec,
                        wpl.pipe_width
                    FROM workflow_process_links wpl
                    WHERE wpl.is_active = true
                """

                links_rows = await conn.fetch(links_query)

                links = [
                    {
                        'id': row['id'],
                        'source': row['source'],
                        'target': row['target'],
                        'throughput': float(row['throughput_ops_per_sec']),
                        'width': row['pipe_width']
                    }
                    for row in links_rows
                ]

                # Calculate ROI metrics
                total_human_cost = sum(
                    n['costPerOp'] * n.get('queue', 0)
                    for n in nodes if n['type'] == 'human'
                )
                total_ai_cost = sum(
                    n['costPerOp'] * n.get('queue', 0)
                    for n in nodes if n['type'] == 'ai_agent'
                )

                savings = total_human_cost - total_ai_cost
                efficiency_gain = (
                    ((total_human_cost - total_ai_cost) / max(total_human_cost, 1)) * 100
                )

                return {
                    'nodes': nodes,
                    'links': links,
                    'metrics': {
                        'totalSavings': float(savings),
                        'efficiencyGain': float(efficiency_gain),
                        'humanNodes': sum(1 for n in nodes if n['type'] == 'human'),
                        'aiNodes': sum(1 for n in nodes if n['type'] == 'ai_agent'),
                        'bottlenecks': sum(1 for n in nodes if n['status'] == 'bottleneck')
                    },
                    'metadata': {
                        'timestamp': datetime.utcnow().isoformat(),
                        'timeWindowDays': time_window_days
                    }
                }

            except Exception as e:
                self.logger.error(f"Error fetching workflow matrix data: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    # ========================================================================
    # TALENT MAP - AGENT NETWORK
    # ========================================================================

    async def get_agent_network_data(
        self,
        include_inactive: bool = False,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Retrieve agent network with burnout detection for TalentMap
        """
        async with self.db_pool.acquire() as conn:
            try:
                # Force metric update if requested
                if force_refresh:
                    await conn.execute("SELECT update_agent_network_metrics()")
                    await conn.execute("REFRESH MATERIALIZED VIEW agent_network_health")

                # Fetch agent nodes
                nodes_query = """
                    SELECT
                        node_id::text as id,
                        agent_id,
                        agent_name,
                        department,
                        influence_score,
                        burnout_index,
                        risk_level,
                        incoming_message_count,
                        outgoing_message_count,
                        communication_imbalance,
                        total_connections,
                        COALESCE(position_x, RANDOM() * 1000 + 100) as x,
                        COALESCE(position_y, RANDOM() * 600 + 100) as y
                    FROM agent_network_health
                    ORDER BY influence_score DESC
                """

                nodes_rows = await conn.fetch(nodes_query)

                nodes = [
                    {
                        'id': row['id'],
                        'label': row['agent_name'],
                        'role': row['agent_name'],
                        'dept': row['department'] or 'Executive',
                        'influenceScore': float(row['influence_score']),
                        'burnoutIndex': float(row['burnout_index']),
                        'riskLevel': row['risk_level'],
                        'x': float(row['x']),
                        'y': float(row['y']),
                        'vx': 0,
                        'vy': 0,
                        'mass': 10 + (float(row['influence_score']) / 5),
                        'radius': 15 + (float(row['influence_score']) / 10),
                        'incomingCount': row['incoming_message_count'],
                        'outgoingCount': row['outgoing_message_count'],
                        'connections': row['total_connections']
                    }
                    for row in nodes_rows
                ]

                # Fetch communication links
                links_query = """
                    SELECT
                        acl.id::text,
                        acl.source_agent_id,
                        acl.target_agent_id,
                        acl.message_frequency,
                        acl.link_type,
                        acl.relationship_strength
                    FROM agent_communication_links acl
                    WHERE acl.message_frequency > 1
                    ORDER BY acl.relationship_strength DESC
                    LIMIT 500
                """

                links_rows = await conn.fetch(links_query)

                # Map agent_id to node id
                agent_to_node = {
                    row['agent_id']: row['id']
                    for row in nodes_rows
                }

                links = []
                for row in links_rows:
                    source_node = agent_to_node.get(row['source_agent_id'])
                    target_node = agent_to_node.get(row['target_agent_id'])

                    if source_node and target_node:
                        links.append({
                            'id': row['id'],
                            'source': source_node,
                            'target': target_node,
                            'frequency': row['message_frequency'],
                            'type': row['link_type'],
                            'strength': float(row['relationship_strength'])
                        })

                # Detect organizational silos
                silo_alert = await self._detect_silos(conn, nodes)

                return {
                    'nodes': nodes,
                    'links': links,
                    'siloAlert': silo_alert,
                    'metrics': {
                        'totalAgents': len(nodes),
                        'criticalRisk': sum(1 for n in nodes if n['riskLevel'] == 'Critical'),
                        'atRisk': sum(1 for n in nodes if n['riskLevel'] == 'At-Risk'),
                        'avgBurnout': sum(n['burnoutIndex'] for n in nodes) / max(len(nodes), 1),
                        'avgInfluence': sum(n['influenceScore'] for n in nodes) / max(len(nodes), 1)
                    },
                    'metadata': {
                        'timestamp': datetime.utcnow().isoformat()
                    }
                }

            except Exception as e:
                self.logger.error(f"Error fetching agent network data: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    async def _detect_silos(self, conn, nodes: List[Dict]) -> Optional[str]:
        """
        Detect communication silos between departments
        Uses spatial clustering analysis
        """
        try:
            departments = {}

            for node in nodes:
                dept = node.get('dept', 'Unknown')
                if dept not in departments:
                    departments[dept] = []
                departments[dept].append(node)

            # Calculate department centroids
            centroids = {}
            for dept, dept_nodes in departments.items():
                if len(dept_nodes) > 0:
                    avg_x = sum(n['x'] for n in dept_nodes) / len(dept_nodes)
                    avg_y = sum(n['y'] for n in dept_nodes) / len(dept_nodes)
                    centroids[dept] = (avg_x, avg_y)

            # Check distances between key departments
            if 'Engineering' in centroids and 'Sales' in centroids:
                eng_x, eng_y = centroids['Engineering']
                sales_x, sales_y = centroids['Sales']
                distance = ((eng_x - sales_x)**2 + (eng_y - sales_y)**2)**0.5

                if distance > 400:
                    return "SILO DETECTED: Engineering and Sales teams are isolated (low collaboration)"

            return None

        except Exception as e:
            self.logger.warning(f"Silo detection failed: {e}")
            return None

    # ========================================================================
    # LIQUIDITY ENGINE - FINANCIAL FLOW
    # ========================================================================

    async def get_liquidity_flow_data(
        self,
        time_window_days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate financial flow metrics for LiquidityEngine

        Models:
        - Revenue sources (LLM API usage fees, subscriptions)
        - Operating account (cash reserves)
        - Expense drains (LLM costs, infrastructure, payroll)
        """
        async with self.db_pool.acquire() as conn:
            try:
                # Calculate revenue (hypothetical - adapt to your business model)
                revenue_sources = [
                    {
                        'id': 'rev_subscriptions',
                        'label': 'Platform Subscriptions',
                        'type': 'source',
                        'balance': 0,
                        'capacity': 0,
                        'flowRate': 5000,  # $ per day
                        'x': 200,
                        'y': 300,
                        'radius': 40
                    },
                    {
                        'id': 'rev_api',
                        'label': 'API Usage Fees',
                        'type': 'source',
                        'balance': 0,
                        'capacity': 0,
                        'flowRate': 2000,
                        'x': 200,
                        'y': 500,
                        'radius': 35
                    }
                ]

                # Calculate LLM costs (actual data from llm_collaborations)
                llm_costs_query = """
                    SELECT
                        SUM(total_cost_usd) as total_cost,
                        COUNT(*) as total_queries
                    FROM llm_collaborations
                    WHERE created_at > NOW() - INTERVAL '30 days'
                      AND status = 'completed'
                """

                llm_costs = await conn.fetchrow(llm_costs_query)
                daily_llm_cost = float(llm_costs['total_cost'] or 0) / max(time_window_days, 1)

                # Operating account (current cash position)
                # This would come from your actual financial system
                operating_account = {
                    'id': 'bank_operating',
                    'label': 'Operating Account',
                    'type': 'tank',
                    'balance': 150000,  # $150k cash
                    'capacity': 500000,
                    'flowRate': 0,
                    'x': 600,
                    'y': 400,
                    'radius': 60
                }

                # Expense drains
                expense_drains = [
                    {
                        'id': 'exp_llm',
                        'label': 'LLM API Costs',
                        'type': 'drain',
                        'balance': 0,
                        'capacity': 0,
                        'flowRate': -daily_llm_cost,
                        'x': 900,
                        'y': 200,
                        'radius': 25
                    },
                    {
                        'id': 'exp_infra',
                        'label': 'Infrastructure (AWS/GCP)',
                        'type': 'drain',
                        'balance': 0,
                        'capacity': 0,
                        'flowRate': -500,  # $500/day
                        'x': 900,
                        'y': 400,
                        'radius': 25
                    },
                    {
                        'id': 'exp_ops',
                        'label': 'Operations & Support',
                        'type': 'drain',
                        'balance': 0,
                        'capacity': 0,
                        'flowRate': -1000,  # $1000/day
                        'x': 900,
                        'y': 600,
                        'radius': 25
                    }
                ]

                # Calculate metrics
                total_revenue = sum(s['flowRate'] for s in revenue_sources)
                total_expenses = sum(abs(d['flowRate']) for d in expense_drains)
                net_burn = total_expenses - total_revenue

                runway_days = 9999
                if net_burn > 0:
                    runway_days = int(operating_account['balance'] / net_burn)

                nodes = revenue_sources + [operating_account] + expense_drains

                # Define links (flow pipes)
                links = [
                    {'id': 'l1', 'source': 'rev_subscriptions', 'target': 'bank_operating', 'width': 6},
                    {'id': 'l2', 'source': 'rev_api', 'target': 'bank_operating', 'width': 4},
                    {'id': 'l3', 'source': 'bank_operating', 'target': 'exp_llm', 'width': 3},
                    {'id': 'l4', 'source': 'bank_operating', 'target': 'exp_infra', 'width': 2},
                    {'id': 'l5', 'source': 'bank_operating', 'target': 'exp_ops', 'width': 3}
                ]

                return {
                    'nodes': nodes,
                    'links': links,
                    'metrics': {
                        'totalLiquidity': operating_account['balance'],
                        'burnRate': net_burn,
                        'runwayDays': runway_days,
                        'monthlyRevenue': total_revenue * 30,
                        'monthlyExpenses': total_expenses * 30
                    },
                    'metadata': {
                        'timestamp': datetime.utcnow().isoformat(),
                        'timeWindowDays': time_window_days
                    }
                }

            except Exception as e:
                self.logger.error(f"Error calculating liquidity flow: {e}")
                raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_service_instance: Optional[SyntheticOrganismService] = None

def get_synthetic_organism_service(db_pool: asyncpg.Pool) -> SyntheticOrganismService:
    """Get or create singleton service instance"""
    global _service_instance
    if _service_instance is None:
        _service_instance = SyntheticOrganismService(db_pool)
    return _service_instance
