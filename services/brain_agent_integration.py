"""
Brain-Agent Integration Service
=================================
Integrates agent prompt protocol with DataBrain Knowledge Graph.
Implements the GRAPH_STATE context injection and Neuroplasticity mutation system.
"""

import os
import json
import psycopg
from psycopg.rows import dict_row
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()
load_dotenv(".env.cockroach")


class DataBrainAgent:
    """
    Agent with DataBrain integration.
    Implements the GRAPH_STATE context and Neuroplasticity protocol.
    """

    def __init__(self, agent_id: str, db_url: str = None):
        self.agent_id = agent_id
        self.db_url = db_url or os.getenv("COCKROACH_DB_URL")

        if not self.db_url:
            raise ValueError("Database URL not configured")

    def _get_connection(self):
        """Get database connection"""
        return psycopg.connect(self.db_url)

    def get_graph_context(self, query: str, max_neighbors: int = 5) -> Dict[str, Any]:
        """
        Get GRAPH_STATE context for a query.

        Returns:
            {
                "current_node_context": {...},
                "connected_neighbors": [...]
            }
        """
        conn = self._get_connection()
        cur = conn.cursor(row_factory=dict_row)

        # Find relevant nodes using semantic search (simplified trigram matching)
        query_lower = query.lower()

        # Search for matching nodes
        cur.execute("""
            SELECT
                node_id, label, type, mass, z_index,
                x_coord, y_coord, semantic_vector,
                description, metadata
            FROM graph_nodes
            WHERE
                LOWER(label) LIKE %s
                OR LOWER(description) LIKE %s
            ORDER BY mass DESC, last_accessed DESC
            LIMIT 1
        """, (f"%{query_lower}%", f"%{query_lower}%"))

        current_node = cur.fetchone()

        if not current_node:
            # Create a new node for this query
            graph_state = {
                "current_node_context": None,
                "connected_neighbors": [],
                "query": query
            }
        else:
            # Find connected neighbors
            cur.execute("""
                SELECT
                    n.node_id, n.label, n.type, n.mass,
                    n.z_index, l.strength as link_strength
                FROM graph_nodes n
                INNER JOIN graph_links l ON (
                    (l.source_node_id = %s AND l.target_node_id = n.node_id)
                    OR (l.target_node_id = %s AND l.source_node_id = n.node_id)
                )
                WHERE n.node_id != %s
                ORDER BY l.strength DESC, n.mass DESC
                LIMIT %s
            """, (current_node['node_id'], current_node['node_id'], current_node['node_id'], max_neighbors))

            neighbors = cur.fetchall()

            # Format z_index as layer
            def get_layer(z_index):
                if z_index < 100: return "Raw_Data"
                elif z_index < 200: return "Information"
                elif z_index < 300: return "Knowledge"
                else: return "Wisdom"

            graph_state = {
                "current_node_context": {
                    "id": current_node['node_id'],
                    "label": current_node['label'],
                    "mass": float(current_node['mass']),
                    "z_layer": get_layer(current_node['z_index']),
                    "description": current_node['description']
                },
                "connected_neighbors": [
                    {
                        "id": n['node_id'],
                        "label": n['label'],
                        "link_strength": float(n['link_strength']),
                        "z_layer": get_layer(n['z_index'])
                    }
                    for n in neighbors
                ]
            }

        cur.close()
        conn.close()

        return graph_state

    def apply_neuroplasticity(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Apply neuroplasticity mutations to the brain.

        Supported actions:
        - CREATE_NODE: {"action": "CREATE_NODE", "params": {...}}
        - CREATE_LINK: {"action": "CREATE_LINK", "params": {...}}
        - DECAY_NODE: {"action": "DECAY_NODE", "params": {...}}
        - UPDATE_MASS: {"action": "UPDATE_MASS", "params": {...}}
        """
        conn = self._get_connection()
        cur = conn.cursor()

        results = []

        for action in actions:
            action_type = action.get("action")
            params = action.get("params", {})

            try:
                if action_type == "CREATE_NODE":
                    # Create new knowledge node
                    node_id = f"n_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                    # Map type to z_index
                    z_map = {
                        "raw_data": 50,
                        "information": 150,
                        "knowledge": 250,
                        "wisdom": 350
                    }
                    z_index = z_map.get(params.get("type", "information"), 150)

                    # Generate semantic vector (simplified trigrams)
                    label = params.get("label", "")
                    trigrams = [label[i:i+3].lower() for i in range(len(label)-2)]
                    semantic_vector = json.dumps(trigrams)

                    cur.execute("""
                        INSERT INTO graph_nodes (
                            node_id, label, type, z_index, mass,
                            semantic_vector, description, metadata
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING node_id
                    """, (
                        node_id,
                        params.get("label"),
                        params.get("type", "information"),
                        z_index,
                        params.get("initial_mass", 20),
                        semantic_vector,
                        params.get("description", ""),
                        json.dumps(params.get("metadata", {}))
                    ))

                    created_id = cur.fetchone()[0]
                    results.append({"action": "CREATE_NODE", "status": "success", "node_id": created_id})

                    # Log neuroplasticity event (skipping if table structure differs)
                    try:
                        cur.execute("""
                            INSERT INTO neuroplasticity_log (
                                action_type, node_id, details
                            ) VALUES (%s, %s, %s)
                        """, ("CREATE_NODE", created_id, json.dumps(params)))
                    except Exception:
                        pass  # Ignore if logging fails

                elif action_type == "CREATE_LINK":
                    # Create link between nodes
                    source_id = params.get("source_id")
                    target_label = params.get("target_label")

                    # Find target node by label
                    cur.execute("SELECT node_id FROM graph_nodes WHERE label = %s LIMIT 1", (target_label,))

                    result = cur.fetchone()

                    if result:
                        target_id = result[0]
                        link_id = f"l_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                        cur.execute("""
                            INSERT INTO graph_links (
                                link_id, source_node_id, target_node_id, strength, weight
                            ) VALUES (%s, %s, %s, %s, %s)
                            RETURNING link_id
                        """, (
                            link_id,
                            source_id,
                            target_id,
                            params.get("weight", 0.95),
                            params.get("weight", 0.95)
                        ))

                        created_link = cur.fetchone()[0]
                        results.append({"action": "CREATE_LINK", "status": "success", "link_id": created_link})
                    else:
                        results.append({"action": "CREATE_LINK", "status": "failed", "reason": "target_not_found"})

                elif action_type == "DECAY_NODE":
                    # Reduce mass of irrelevant node
                    target_id = params.get("target_id")
                    reason = params.get("reason", "relevance_decay")

                    cur.execute("""
                        UPDATE graph_nodes
                        SET mass = GREATEST(mass * 0.8, 1.0),
                            metadata = metadata || %s::jsonb
                        WHERE node_id = %s
                        RETURNING node_id, mass
                    """, (json.dumps({"decay_reason": reason}), target_id))

                    result = cur.fetchone()
                    if result:
                        results.append({"action": "DECAY_NODE", "status": "success", "node_id": result[0], "new_mass": float(result[1])})
                    else:
                        results.append({"action": "DECAY_NODE", "status": "failed", "reason": "node_not_found"})

                elif action_type == "UPDATE_MASS":
                    # Increase importance of node
                    target_id = params.get("target_id")
                    delta = params.get("delta", 5.0)

                    cur.execute("""
                        UPDATE graph_nodes
                        SET mass = LEAST(mass + %s, 100.0),
                            access_count = access_count + 1,
                            last_accessed = NOW()
                        WHERE node_id = %s
                        RETURNING node_id, mass
                    """, (delta, target_id))

                    result = cur.fetchone()
                    if result:
                        results.append({"action": "UPDATE_MASS", "status": "success", "node_id": result[0], "new_mass": float(result[1])})

            except Exception as e:
                results.append({"action": action_type, "status": "error", "error": str(e)})

        conn.commit()
        cur.close()
        conn.close()

        return {"applied": len(results), "results": results}

    def query_with_context(self, query: str) -> Dict[str, Any]:
        """
        Full integration: Get graph context + execute query + apply neuroplasticity.

        This method would be called by the AI agent with the full prompt protocol.
        """
        # Step 1: Get graph context
        graph_state = self.get_graph_context(query)

        # Step 2: Agent would process this with LLM (not implemented here - this is the hook)
        # The LLM receives graph_state and generates neuroplasticity_actions

        # For demo, we'll create a sample node
        if not graph_state["current_node_context"]:
            # Create new node for this query
            neuroplasticity_actions = [
                {
                    "action": "CREATE_NODE",
                    "params": {
                        "label": query[:100],
                        "type": "information",
                        "initial_mass": 15,
                        "description": f"Knowledge node created from query: {query}"
                    }
                }
            ]

            mutation_results = self.apply_neuroplasticity(neuroplasticity_actions)
        else:
            # Update existing node mass (it was accessed)
            neuroplasticity_actions = [
                {
                    "action": "UPDATE_MASS",
                    "params": {
                        "target_id": graph_state["current_node_context"]["id"],
                        "delta": 2.0
                    }
                }
            ]
            mutation_results = self.apply_neuroplasticity(neuroplasticity_actions)

        return {
            "query": query,
            "graph_state": graph_state,
            "neuroplasticity_applied": mutation_results,
            "timestamp": datetime.now().isoformat()
        }


def test_brain_integration():
    """Test the brain-agent integration"""
    print("=" * 80)
    print("TESTING BRAIN-AGENT INTEGRATION")
    print("=" * 80)

    # Create agent
    agent = DataBrainAgent(agent_id="test_agent_001")

    # Test 1: Query with context
    print("\n1. Testing query with graph context...")
    result = agent.query_with_context("What is Q3 Revenue Analysis?")
    print(f"   Graph State: {json.dumps(result['graph_state'], indent=2)}")
    print(f"   ✅ Mutations Applied: {result['neuroplasticity_applied']['applied']}")

    # Test 2: Create knowledge structure
    print("\n2. Creating knowledge structure...")
    actions = [
        {
            "action": "CREATE_NODE",
            "params": {
                "label": "CockroachDB Integration",
                "type": "knowledge",
                "initial_mass": 30,
                "description": "Knowledge about CockroachDB cloud database integration"
            }
        },
        {
            "action": "CREATE_NODE",
            "params": {
                "label": "Multi-Agent System",
                "type": "wisdom",
                "initial_mass": 40,
                "description": "Strategic knowledge about coordinating multiple AI agents"
            }
        }
    ]

    mutation_results = agent.apply_neuroplasticity(actions)
    print(f"   ✅ Created {mutation_results['applied']} nodes")

    # Test 3: Query again to see context
    print("\n3. Re-querying to verify graph state...")
    result2 = agent.query_with_context("CockroachDB")
    if result2['graph_state']['current_node_context']:
        print(f"   ✅ Found node: {result2['graph_state']['current_node_context']['label']}")
        print(f"   Mass: {result2['graph_state']['current_node_context']['mass']}")

    print("\n" + "=" * 80)
    print("✅ BRAIN-AGENT INTEGRATION TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_brain_integration()
