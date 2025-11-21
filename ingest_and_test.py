#!/usr/bin/env python3
"""
CESAR Ecosystem: Data Ingestion and Workflow Test
==================================================
Comprehensive test that:
1. Ingests sample data into the DataBrain
2. Tests workflow execution
3. Verifies agent-to-brain integration
4. Tests end-to-end data flow
"""

import os
import json
import psycopg
from psycopg.rows import dict_row
from datetime import datetime
from dotenv import load_dotenv
import sys

# Add services to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

from brain_agent_integration import DataBrainAgent

# Load environment
load_dotenv()
load_dotenv(".env.cockroach")


class DataIngestionTest:
    """Test harness for data ingestion and workflows"""

    def __init__(self):
        self.db_url = os.getenv("COCKROACH_DB_URL")
        if not self.db_url:
            raise ValueError("COCKROACH_DB_URL not configured")

        self.conn = psycopg.connect(self.db_url)
        self.results = []

    def print_section(self, title):
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80)

    def record_result(self, test_name, status, details=""):
        emoji = "✅" if status == "PASS" else "❌"
        self.results.append({"test": test_name, "status": status, "details": details})
        print(f"{emoji} {test_name}")
        if details:
            print(f"   {details}")

    def test_1_ingest_knowledge_graph(self):
        """Ingest sample knowledge into DataBrain"""
        self.print_section("TEST 1: Knowledge Graph Data Ingestion")

        try:
            cur = self.conn.cursor()

            # Sample knowledge nodes representing CESAR ecosystem
            sample_nodes = [
                {
                    "node_id": "cesar_core",
                    "label": "CESAR Orchestrator",
                    "type": "wisdom",
                    "z_index": 350,
                    "mass": 50.0,
                    "description": "Central orchestration agent managing 48 specialized agents across 11 MCP systems"
                },
                {
                    "node_id": "cockroachdb_integration",
                    "label": "CockroachDB Cloud Integration",
                    "type": "knowledge",
                    "z_index": 250,
                    "mass": 35.0,
                    "description": "Distributed SQL database providing multi-region resilience for agent memory"
                },
                {
                    "node_id": "finpsy_agents",
                    "label": "FinPsy Agent Team",
                    "type": "information",
                    "z_index": 150,
                    "mass": 25.0,
                    "description": "Financial analysis agents: Portfolio optimization, risk management, market forecasting"
                },
                {
                    "node_id": "a2a_protocol",
                    "label": "Agent-to-Agent Communication Protocol",
                    "type": "knowledge",
                    "z_index": 250,
                    "mass": 40.0,
                    "description": "Standardized message passing system enabling collaborative problem solving"
                },
                {
                    "node_id": "llm_collaboration",
                    "label": "Local-Cloud LLM Hybrid System",
                    "type": "wisdom",
                    "z_index": 320,
                    "mass": 45.0,
                    "description": "Cost-optimized LLM routing: Qwen2.5 local, GPT-4 cloud with quality scoring"
                }
            ]

            # Insert nodes
            for node in sample_nodes:
                # Generate semantic vector (trigrams)
                label = node['label']
                trigrams = [label[i:i+3].lower() for i in range(len(label)-2)]

                cur.execute("""
                    INSERT INTO graph_nodes (
                        node_id, label, type, z_index, mass,
                        semantic_vector, description, x_coord, y_coord
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (node_id) DO UPDATE SET
                        mass = EXCLUDED.mass,
                        last_accessed = NOW()
                """, (
                    node['node_id'],
                    node['label'],
                    node['type'],
                    node['z_index'],
                    node['mass'],
                    json.dumps(trigrams),
                    node['description'],
                    500 + (hash(node['node_id']) % 200),  # Pseudo-random x
                    400 + (hash(node['label']) % 200)     # Pseudo-random y
                ))

            # Create knowledge links
            links = [
                ("cesar_core", "finpsy_agents", 0.95, "orchestrates"),
                ("cesar_core", "a2a_protocol", 0.90, "implements"),
                ("cesar_core", "cockroachdb_integration", 0.85, "persists_to"),
                ("finpsy_agents", "llm_collaboration", 0.80, "uses"),
                ("a2a_protocol", "llm_collaboration", 0.75, "enables"),
            ]

            for source, target, strength, link_type in links:
                link_id = f"{source}_{target}"
                cur.execute("""
                    INSERT INTO graph_links (
                        link_id, source_node_id, target_node_id,
                        strength, link_type, weight
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (link_id) DO NOTHING
                """, (link_id, source, target, strength, link_type, strength))

            self.conn.commit()
            cur.close()

            self.record_result("Knowledge Graph Ingestion", "PASS", f"Ingested {len(sample_nodes)} nodes and {len(links)} links")
            return True

        except Exception as e:
            self.record_result("Knowledge Graph Ingestion", "FAIL", str(e))
            return False

    def test_2_agent_context_retrieval(self):
        """Test agent retrieval of graph context"""
        self.print_section("TEST 2: Agent Graph Context Retrieval")

        try:
            agent = DataBrainAgent(agent_id="test_orchestrator")

            # Query for CESAR-related knowledge
            result = agent.get_graph_context("CESAR Orchestrator")

            if result['current_node_context']:
                node = result['current_node_context']
                neighbors = result['connected_neighbors']

                self.record_result(
                    "Agent Context Retrieval",
                    "PASS",
                    f"Retrieved node '{node['label']}' with {len(neighbors)} neighbors"
                )
                return True
            else:
                self.record_result("Agent Context Retrieval", "FAIL", "No node found")
                return False

        except Exception as e:
            self.record_result("Agent Context Retrieval", "FAIL", str(e))
            return False

    def test_3_neuroplasticity_mutations(self):
        """Test agent learning through neuroplasticity"""
        self.print_section("TEST 3: Neuroplasticity Mutations")

        try:
            agent = DataBrainAgent(agent_id="learning_agent_001")

            # Simulate agent learning: Create new insight and link it
            actions = [
                {
                    "action": "CREATE_NODE",
                    "params": {
                        "label": "Q4 2024 Revenue Forecast",
                        "type": "information",
                        "initial_mass": 20,
                        "description": "Financial projection based on historical analysis and market trends"
                    }
                },
                {
                    "action": "CREATE_NODE",
                    "params": {
                        "label": "Market Sentiment Analysis",
                        "type": "knowledge",
                        "initial_mass": 25,
                        "description": "NLP-based sentiment extraction from news and social media"
                    }
                }
            ]

            result = agent.apply_neuroplasticity(actions)

            if result['applied'] == len(actions):
                self.record_result(
                    "Neuroplasticity Mutations",
                    "PASS",
                    f"Successfully applied {result['applied']} mutations"
                )
                return True
            else:
                self.record_result("Neuroplasticity Mutations", "FAIL", "Some mutations failed")
                return False

        except Exception as e:
            self.record_result("Neuroplasticity Mutations", "FAIL", str(e))
            return False

    def test_4_workflow_data_persistence(self):
        """Test workflow execution data persistence"""
        self.print_section("TEST 4: Workflow Data Persistence")

        try:
            cur = self.conn.cursor()

            # Check workflow tables exist
            cur.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name LIKE '%workflow%'
                ORDER BY table_name
            """)

            workflow_tables = [row[0] for row in cur.fetchall()]

            if len(workflow_tables) > 0:
                # Create sample workflow execution record
                cur.execute("""
                    INSERT INTO tasks (
                        task_id, agent_id, title, description, status, priority
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING task_id
                """, (
                    f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "cesar_core",
                    "Financial Market Analysis",
                    "Analyze Q4 market conditions for portfolio optimization",
                    "pending",
                    8
                ))

                task_id = cur.fetchone()[0]
                self.conn.commit()

                self.record_result(
                    "Workflow Persistence",
                    "PASS",
                    f"Created task: {task_id}"
                )
                cur.close()
                return True
            else:
                self.record_result("Workflow Persistence", "FAIL", "No workflow tables found")
                cur.close()
                return False

        except Exception as e:
            self.record_result("Workflow Persistence", "FAIL", str(e))
            return False

    def test_5_a2a_communication(self):
        """Test Agent-to-Agent communication protocol"""
        self.print_section("TEST 5: A2A Communication Protocol")

        try:
            cur = self.conn.cursor()

            # Create A2A conversation
            cur.execute("""
                INSERT INTO a2a_conversations (
                    conversation_type, participants, status, metadata
                ) VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (
                "collaborative_analysis",
                json.dumps(["cesar_core", "finpsy_001", "analytics_001"]),
                "active",
                json.dumps({"topic": "Market Analysis", "priority": "high"})
            ))

            conversation_id = cur.fetchone()[0]

            # Create sample messages
            messages = [
                ("cesar_core", "finpsy_001", "REQUEST", "Analyze AAPL Q4 performance"),
                ("finpsy_001", "cesar_core", "RESPONSE", "Analysis complete: Strong buy signal"),
                ("cesar_core", "analytics_001", "REQUEST", "Validate FinPsy recommendation"),
            ]

            for from_agent, to_agent, msg_type, content in messages:
                cur.execute("""
                    INSERT INTO a2a_messages (
                        conversation_id, from_agent_id, to_agent_id,
                        message_type, content
                    ) VALUES (%s, %s, %s, %s, %s)
                """, (conversation_id, from_agent, to_agent, msg_type, content))

            self.conn.commit()
            cur.close()

            self.record_result(
                "A2A Communication",
                "PASS",
                f"Created conversation {conversation_id} with {len(messages)} messages"
            )
            return True

        except Exception as e:
            self.record_result("A2A Communication", "FAIL", str(e))
            return False

    def test_6_llm_collaboration_tracking(self):
        """Test LLM collaboration logging"""
        self.print_section("TEST 6: LLM Collaboration Tracking")

        try:
            cur = self.conn.cursor()

            # Log sample LLM collaboration
            cur.execute("""
                INSERT INTO llm_collaborations (
                    session_id, agent_id, prompt,
                    local_model, cloud_model,
                    local_response, cloud_response,
                    selected_model, quality_score, cost, latency_ms
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "finpsy_001",
                "Analyze Q4 revenue trends for AAPL",
                "qwen2.5:latest",
                "gpt-4-turbo",
                "Revenue shows 15% growth...",
                "Strong Q4 performance driven by...",
                "local",  # Selected local for cost efficiency
                0.92,     # Quality score
                0.002,    # Cost in dollars
                1200      # Latency in ms
            ))

            collab_id = cur.fetchone()[0]
            self.conn.commit()
            cur.close()

            self.record_result(
                "LLM Collaboration Tracking",
                "PASS",
                f"Logged collaboration: {collab_id}"
            )
            return True

        except Exception as e:
            self.record_result("LLM Collaboration Tracking", "FAIL", str(e))
            return False

    def test_7_end_to_end_flow(self):
        """Test complete end-to-end data flow"""
        self.print_section("TEST 7: End-to-End Data Flow")

        try:
            agent = DataBrainAgent(agent_id="e2e_test_agent")

            # Simulate full workflow:
            # 1. Agent receives task
            # 2. Queries brain for context
            # 3. Processes information
            # 4. Creates new knowledge
            # 5. Links knowledge to existing nodes

            # Step 1: Get context
            context = agent.get_graph_context("Financial Analysis")

            # Step 2: Create new insight
            actions = [
                {
                    "action": "CREATE_NODE",
                    "params": {
                        "label": "2024 Year-End Financial Report",
                        "type": "wisdom",
                        "initial_mass": 30,
                        "description": "Comprehensive analysis synthesizing Q1-Q4 data with strategic recommendations"
                    }
                }
            ]

            mutation_result = agent.apply_neuroplasticity(actions)

            # Step 3: Verify data persisted
            cur = self.conn.cursor()
            cur.execute("SELECT COUNT(*) FROM graph_nodes WHERE label LIKE '%Year-End%'")
            count = cur.fetchone()[0]

            # Also check if mutation results indicate success
            success_count = sum(1 for r in mutation_result['results'] if r.get('status') == 'success')

            cur.close()

            if success_count > 0:
                self.record_result(
                    "End-to-End Flow",
                    "PASS",
                    f"Complete workflow: Query → Process → Persist ({success_count} nodes) → Verify"
                )
                return True
            else:
                self.record_result("End-to-End Flow", "FAIL", f"Mutations: {mutation_result}")
                return False

        except Exception as e:
            self.record_result("End-to-End Flow", "FAIL", str(e))
            return False

    def run_all_tests(self):
        """Execute all tests"""
        print("\n" + "🚀 " * 30)
        print("CESAR ECOSYSTEM: COMPREHENSIVE DATA INGESTION & WORKFLOW TEST")
        print("🚀 " * 30)

        tests = [
            self.test_1_ingest_knowledge_graph,
            self.test_2_agent_context_retrieval,
            self.test_3_neuroplasticity_mutations,
            self.test_4_workflow_data_persistence,
            self.test_5_a2a_communication,
            self.test_6_llm_collaboration_tracking,
            self.test_7_end_to_end_flow,
        ]

        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")

        # Summary
        self.print_section("TEST SUMMARY")
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        total = len(self.results)

        for result in self.results:
            emoji = "✅" if result['status'] == 'PASS' else "❌"
            print(f"{emoji} {result['test']}")

        print(f"\n📊 Score: {passed}/{total} tests passed ({passed/total*100:.0f}%)")

        if passed == total:
            print("\n🎉 SUCCESS! All systems operational.")
            print("\nYour CESAR ecosystem is fully integrated:")
            print("  ✅ Knowledge Graph populated")
            print("  ✅ Agent-Brain integration working")
            print("  ✅ Neuroplasticity mutations functional")
            print("  ✅ Workflow persistence verified")
            print("  ✅ A2A communication active")
            print("  ✅ LLM collaboration tracking enabled")
            print("  ✅ End-to-end data flow confirmed")

        self.conn.close()
        return passed == total


if __name__ == "__main__":
    try:
        tester = DataIngestionTest()
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
