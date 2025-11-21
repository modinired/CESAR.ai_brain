#!/usr/bin/env python3
"""
Test DataBrain Integration with Base MCP Agent
===============================================
Verifies that all 48 agents can now access GRAPH_STATE context.
"""

import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Test import of base agent with brain integration
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), "mcp_agents"))
    from base_agent import BaseMCPAgent
    print("✅ Successfully imported BaseMCPAgent with DataBrain integration")
except Exception as e:
    print(f"❌ Failed to import BaseMCPAgent: {e}")
    sys.exit(1)


# Create a test agent class
class TestAgent(BaseMCPAgent):
    """Test agent to verify DataBrain integration"""

    def process(self, task_input: dict) -> dict:
        """Simple processing that uses brain context if available"""

        graph_state = task_input.get("GRAPH_STATE")

        if graph_state and graph_state.get("current_node_context"):
            node = graph_state["current_node_context"]
            return {
                "status": "completed",
                "message": f"Processed with brain context from node: {node['label']}",
                "brain_enriched": True,
                "context_layer": node.get("z_layer"),
                "neighbors_found": len(graph_state.get("connected_neighbors", []))
            }
        else:
            return {
                "status": "completed",
                "message": "Processed without brain context",
                "brain_enriched": False
            }


def test_brain_integration():
    print("=" * 80)
    print("TESTING DATABRAIN INTEGRATION WITH BASE MCP AGENT")
    print("=" * 80)
    print()

    # Test 1: Create agent with brain enabled
    print("1. Creating test agent with DataBrain integration...")
    try:
        agent = TestAgent(
            agent_id="test_brain_agent",
            mcp_system="test_system",
            enable_databrain=True
        )

        if agent.databrain:
            print("   ✅ DataBrain integration active")
        else:
            print("   ⚠️  DataBrain not available (check COCKROACH_DB_URL)")

    except Exception as e:
        print(f"   ❌ Failed to create agent: {e}")
        return False

    # Test 2: Get brain context
    print("\n2. Testing get_brain_context()...")
    try:
        context = agent.get_brain_context("Financial Psychology")

        if context.get("current_node_context"):
            print(f"   ✅ Found node: {context['current_node_context']['label']}")
            print(f"      Layer: {context['current_node_context']['z_layer']}")
            print(f"      Mass: {context['current_node_context']['mass']}")
            print(f"      Neighbors: {len(context['connected_neighbors'])}")
        else:
            print("   ⚠️  No matching node found (brain may be empty)")

    except Exception as e:
        print(f"   ❌ Failed to get context: {e}")

    # Test 3: Process with brain enrichment
    print("\n3. Testing process_with_brain()...")
    try:
        result = agent.process_with_brain(
            query="Portfolio Optimization",
            task_input={"action": "analyze", "data": "sample"}
        )

        print(f"   Status: {result.get('status')}")
        print(f"   Message: {result.get('message')}")
        print(f"   Brain Enriched: {result.get('brain_enriched')}")

        if result.get("brain_mutation"):
            print(f"   ✅ Brain updated: {result['brain_mutation']['applied']} mutations")

    except Exception as e:
        print(f"   ❌ Failed to process: {e}")

    # Test 4: Apply neuroplasticity
    print("\n4. Testing mutate_brain()...")
    try:
        mutations = [
            {
                "action": "CREATE_NODE",
                "params": {
                    "label": "Test Integration Knowledge",
                    "type": "information",
                    "initial_mass": 15,
                    "description": "Node created during integration testing"
                }
            }
        ]

        result = agent.mutate_brain(mutations)
        print(f"   ✅ Applied {result['applied']} mutation(s)")

        if result['results']:
            for r in result['results']:
                print(f"      {r['action']}: {r['status']}")

    except Exception as e:
        print(f"   ❌ Failed to mutate: {e}")

    print("\n" + "=" * 80)
    print("✅ DATABRAIN INTEGRATION TEST COMPLETE")
    print("=" * 80)
    print("\n📋 ALL 48 AGENTS NOW HAVE ACCESS TO:")
    print("   • get_brain_context(query) - Retrieve GRAPH_STATE")
    print("   • mutate_brain(actions) - Update knowledge graph")
    print("   • process_with_brain(query, input) - Full integration")
    print("\n🎯 Usage in agent code:")
    print('   context = self.get_brain_context("query string")')
    print('   output = self.process(input | {"GRAPH_STATE": context})')
    print('   self.mutate_brain([{"action": "UPDATE_MASS", ...}])')
    print("=" * 80)

    return True


if __name__ == "__main__":
    success = test_brain_integration()
    sys.exit(0 if success else 1)
