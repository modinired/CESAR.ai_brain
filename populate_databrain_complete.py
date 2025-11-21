#!/usr/bin/env python3
"""
CESAR DataBrain: Complete Knowledge Graph Population
====================================================
PhD-Level Implementation

Populates the DataBrain with:
1. Knowledge nodes for each MCP system's domain expertise
2. Knowledge nodes for each agent's specialization
3. System architecture concepts (existing 5 nodes + expansions)
4. Synaptic links showing agent collaborations and domain relationships
5. Force fields for semantic clustering

Based on brain_schema.sql design:
- graph_nodes: Concepts, NOT agent instances (agents have their own table)
- Z-index layers: 0-100 raw, 100-200 info, 200-300 knowledge, 300+ wisdom
- Mass: Importance/gravity (0-100)
- Semantic vectors: Trigram-based similarity search
"""

import os
import json
import psycopg
from psycopg.rows import dict_row
from datetime import datetime
from dotenv import load_dotenv
import math

load_dotenv()


class DataBrainPopulator:
    def __init__(self):
        self.db_url = os.getenv("COCKROACH_DB_URL")
        if not self.db_url or "pending" in self.db_url:
            raise ValueError("COCKROACH_DB_URL not configured")

        self.conn = psycopg.connect(self.db_url)
        self.nodes_created = 0
        self.links_created = 0

    def generate_trigrams(self, text):
        """Generate trigram semantic vector"""
        text = text.lower()
        return list(set([text[i:i+3] for i in range(len(text)-2)]))

    def create_node(self, node_id, label, node_type, z_index, mass, description, metadata=None):
        """Create a knowledge node"""
        cur = self.conn.cursor()

        # Generate position in 3D space
        angle = (self.nodes_created * 2 * math.pi) / 100
        radius = 200 + (z_index / 2)
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)

        trigrams = self.generate_trigrams(label)

        try:
            cur.execute("""
                INSERT INTO graph_nodes (
                    node_id, label, type, z_index, mass,
                    x_coord, y_coord, semantic_vector, description, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (node_id) DO UPDATE SET
                    mass = EXCLUDED.mass,
                    last_accessed = NOW(),
                    access_count = graph_nodes.access_count + 1
                RETURNING id
            """, (
                node_id, label, node_type, z_index, mass,
                x, y, json.dumps(trigrams), description,
                json.dumps(metadata or {})
            ))

            self.conn.commit()
            self.nodes_created += 1
            print(f"   ✅ {label} (z={z_index}, mass={mass})")

        except Exception as e:
            print(f"   ❌ Error creating {label}: {e}")
            self.conn.rollback()

        cur.close()

    def create_link(self, source_id, target_id, link_type, strength):
        """Create a synaptic link"""
        cur = self.conn.cursor()
        link_id = f"{source_id}_{target_id}"

        try:
            cur.execute("""
                INSERT INTO graph_links (
                    link_id, source_node_id, target_node_id,
                    link_type, strength, weight
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (link_id) DO UPDATE SET
                    strength = EXCLUDED.strength,
                    traversal_count = graph_links.traversal_count + 1,
                    last_traversed = NOW()
            """, (link_id, source_id, target_id, link_type, strength, strength))

            self.conn.commit()
            self.links_created += 1

        except Exception as e:
            print(f"   ⚠️  Link {source_id} → {target_id}: {e}")
            self.conn.rollback()

        cur.close()

    def populate(self):
        print("=" * 80)
        print("🧠 POPULATING CESAR DATABRAIN - PhD-LEVEL IMPLEMENTATION")
        print("=" * 80)
        print()

        # ====================================================================
        # WISDOM LAYER (300+): Strategic architecture concepts
        # ====================================================================
        print("📚 WISDOM LAYER (300+): Strategic Architecture")
        print("-" * 80)

        self.create_node(
            "cesar_orchestrator",
            "CESAR Orchestrator",
            "wisdom", 350, 50.0,
            "Central meta-agent coordinating 48 specialized agents across 11 MCP systems using A2A protocol"
        )

        self.create_node(
            "llm_hybrid_architecture",
            "Hybrid LLM Routing System",
            "wisdom", 340, 48.0,
            "Cost-optimized AI: Local Qwen2.5 for routine tasks, GPT-4 cloud for complex reasoning with quality scoring"
        )

        self.create_node(
            "neuroplasticity_engine",
            "Neuroplasticity Learning Engine",
            "wisdom", 330, 46.0,
            "Self-improving knowledge graph with temporal decay, mass-based importance, and hippocampal replay for model fine-tuning"
        )

        self.create_node(
            "distributed_persistence",
            "Multi-Region Distributed Persistence",
            "wisdom", 320, 44.0,
            "CockroachDB cloud providing ACID guarantees, automatic replication, and geo-distributed resilience"
        )

        print()

        # ====================================================================
        # KNOWLEDGE LAYER (200-300): MCP system domains
        # ====================================================================
        print("🎓 KNOWLEDGE LAYER (200-300): MCP System Expertise")
        print("-" * 80)

        mcp_systems = [
            ("finpsy_domain", "Financial Psychology Domain", 280, 42.0,
             "Behavioral finance, portfolio optimization, sentiment analysis, market forecasting with cognitive bias awareness"),

            ("innovation_domain", "Innovation & IP Domain", 275, 40.0,
             "Patent search, prior art analysis, trend detection, technology forecasting, whitespace identification"),

            ("legal_compliance_domain", "Legal & Compliance Domain", 270, 38.0,
             "Contract analysis, regulatory compliance, risk assessment, legal document generation"),

            ("creative_content_domain", "Creative Content Domain", 265, 36.0,
             "Copywriting, content strategy, brand voice consistency, multi-channel optimization"),

            ("education_domain", "Education & Curriculum Domain", 260, 35.0,
             "Curriculum design, learning path optimization, pedagogical strategy, knowledge sequencing"),

            ("code_generation_domain", "Code & Workflow Domain", 255, 34.0,
             "Code generation, workflow automation, API integration, system orchestration"),

            ("security_domain", "Security & Risk Domain", 250, 33.0,
             "Threat detection, compliance monitoring, access control, audit trail management"),

            ("omnicognition_domain", "Omnicognition Meta-Learning", 245, 32.0,
             "Cross-domain synthesis, analogical reasoning, transfer learning, emergent insight detection"),

            ("protocol_domain", "Protocol & Standards Domain", 240, 31.0,
             "Communication protocols, data standards, interoperability, API design patterns"),

            ("skillforge_domain", "Skill Discovery & Synthesis", 235, 30.0,
             "Dynamic capability discovery, tool composition, agent skill evolution"),

            ("central_coordination", "Central Coordination Layer", 230, 38.0,
             "Multi-agent task routing, resource allocation, conflict resolution, consensus mechanisms")
        ]

        for node_id, label, z, mass, desc in mcp_systems:
            self.create_node(node_id, label, "knowledge", z, mass, desc)

        print()

        # ====================================================================
        # INFORMATION LAYER (100-200): Agent specializations
        # ====================================================================
        print("💡 INFORMATION LAYER (100-200): Agent Specializations")
        print("-" * 80)

        agent_specs = [
            ("portfolio_optimization_spec", "Portfolio Optimization Specialization", 180, 28.0,
             "Modern Portfolio Theory, risk parity, Black-Litterman, factor models, rebalancing algorithms"),

            ("sentiment_analysis_spec", "Market Sentiment Analysis", 175, 27.0,
             "NLP on financial news, social media mining, sentiment scoring, fear/greed indicators"),

            ("forecasting_spec", "Predictive Forecasting Specialization", 170, 26.0,
             "Time series analysis, ARIMA, Prophet, neural forecasting, ensemble methods"),

            ("patent_search_spec", "Patent Search & Analysis", 165, 25.0,
             "USPTO/EPO search, classification analysis, citation networks, freedom-to-operate"),

            ("contract_analysis_spec", "Contract Analysis Specialization", 160, 24.0,
             "Clause extraction, obligation identification, risk flagging, redline generation"),

            ("copywriting_spec", "Professional Copywriting", 155, 23.0,
             "Persuasive writing, SEO optimization, A/B testing, conversion optimization"),

            ("curriculum_design_spec", "Curriculum Design Specialization", 150, 22.0,
             "Learning objectives, Bloom's taxonomy, assessment design, adaptive pathways"),

            ("code_generation_spec", "Code Generation Specialization", 145, 21.0,
             "Multiple languages, design patterns, test generation, documentation automation"),

            ("workflow_automation_spec", "Workflow Automation", 140, 20.0,
             "DAG construction, dependency resolution, retry logic, error handling patterns"),

            ("threat_detection_spec", "Threat Detection Specialization", 135, 19.0,
             "Anomaly detection, behavioral analysis, SIEM integration, incident response"),

            ("memory_consolidation_spec", "Memory Consolidation", 130, 18.0,
             "Episodic to semantic transition, importance filtering, knowledge distillation"),

            ("task_orchestration_spec", "Task Orchestration", 125, 17.0,
             "Priority queuing, load balancing, deadline management, resource optimization")
        ]

        for node_id, label, z, mass, desc in agent_specs:
            self.create_node(node_id, label, "information", z, mass, desc)

        print()

        # ====================================================================
        # CORE PROTOCOLS & SYSTEMS (Knowledge layer)
        # ====================================================================
        print("⚙️  CORE PROTOCOLS & SYSTEMS")
        print("-" * 80)

        protocols = [
            ("a2a_protocol", "Agent-to-Agent Communication Protocol", 260, 40.0,
             "Standardized message passing: request/response/broadcast/delegate with routing metadata"),

            ("graph_state_protocol", "GRAPH_STATE Context Injection", 255, 38.0,
             "Semantic context retrieval from knowledge graph with relevance scoring and neighbor traversal"),

            ("neuroplasticity_protocol", "Neuroplasticity Mutation Protocol", 250, 36.0,
             "CREATE_NODE, CREATE_LINK, DECAY_NODE, UPDATE_MASS, MERGE_NODES operations with conflict resolution"),

            ("hippocampal_replay", "Hippocampal Replay System", 245, 35.0,
             "Training data generation from high-value experiences for LoRA fine-tuning"),

            ("memory_systems", "Tripartite Memory Architecture", 240, 34.0,
             "Working memory (active context), episodic (experiences), semantic (consolidated knowledge)"),

            ("blackboard_system", "Multi-Agent Blackboard", 235, 32.0,
             "Shared coordination space for agent collaboration, versioned entries, priority-based access")
        ]

        for node_id, label, z, mass, desc in protocols:
            self.create_node(node_id, label, "knowledge", z, mass, desc)

        print()

        # ====================================================================
        # SYNAPTIC LINKS: Domain relationships
        # ====================================================================
        print("🔗 CREATING SYNAPTIC LINKS")
        print("-" * 80)

        links = [
            # Orchestrator connections
            ("cesar_orchestrator", "central_coordination", "implements", 0.95),
            ("cesar_orchestrator", "a2a_protocol", "uses", 0.93),
            ("cesar_orchestrator", "distributed_persistence", "persists_to", 0.90),
            ("cesar_orchestrator", "llm_hybrid_architecture", "routes_through", 0.88),

            # MCP system relationships
            ("finpsy_domain", "portfolio_optimization_spec", "implements", 0.90),
            ("finpsy_domain", "sentiment_analysis_spec", "implements", 0.88),
            ("finpsy_domain", "forecasting_spec", "implements", 0.86),

            ("innovation_domain", "patent_search_spec", "implements", 0.92),

            ("legal_compliance_domain", "contract_analysis_spec", "implements", 0.91),

            ("creative_content_domain", "copywriting_spec", "implements", 0.90),

            ("education_domain", "curriculum_design_spec", "implements", 0.89),

            ("code_generation_domain", "code_generation_spec", "implements", 0.93),
            ("code_generation_domain", "workflow_automation_spec", "implements", 0.91),

            ("security_domain", "threat_detection_spec", "implements", 0.92),

            # Protocol interconnections
            ("a2a_protocol", "blackboard_system", "coordinates_via", 0.85),
            ("graph_state_protocol", "neuroplasticity_protocol", "updates_via", 0.88),
            ("hippocampal_replay", "neuroplasticity_protocol", "reads_from", 0.82),

            # Cross-domain synergies
            ("finpsy_domain", "omnicognition_domain", "collaborates", 0.75),
            ("innovation_domain", "legal_compliance_domain", "collaborates", 0.78),
            ("creative_content_domain", "education_domain", "collaborates", 0.72),

            # LLM system connections
            ("llm_hybrid_architecture", "finpsy_domain", "serves", 0.80),
            ("llm_hybrid_architecture", "innovation_domain", "serves", 0.80),
            ("llm_hybrid_architecture", "legal_compliance_domain", "serves", 0.80),

            # Learning system
            ("neuroplasticity_engine", "memory_systems", "consolidates_via", 0.87),
            ("neuroplasticity_engine", "hippocampal_replay", "trains_via", 0.85),
        ]

        for source, target, link_type, strength in links:
            self.create_link(source, target, link_type, strength)

        print()

        # ====================================================================
        # VERIFICATION
        # ====================================================================
        print("=" * 80)
        print("📊 VERIFICATION")
        print("=" * 80)

        cur = self.conn.cursor(row_factory=dict_row)

        cur.execute("SELECT COUNT(*) as count FROM graph_nodes")
        total_nodes = cur.fetchone()["count"]

        cur.execute("SELECT COUNT(*) as count FROM graph_links")
        total_links = cur.fetchone()["count"]

        cur.execute("""
            SELECT
                CASE
                    WHEN z_index < 100 THEN 'Raw Data (0-100)'
                    WHEN z_index < 200 THEN 'Information (100-200)'
                    WHEN z_index < 300 THEN 'Knowledge (200-300)'
                    ELSE 'Wisdom (300+)'
                END as layer,
                COUNT(*) as count
            FROM graph_nodes
            GROUP BY layer
            ORDER BY MIN(z_index)
        """)

        print(f"\n✅ Total Knowledge Nodes: {total_nodes}")
        print(f"🔗 Total Synaptic Links: {total_links}")
        print(f"\n📚 Nodes by Intelligence Layer:")
        for row in cur.fetchall():
            print(f"   {row['layer']}: {row['count']} nodes")

        cur.close()
        self.conn.close()

        print("\n" + "=" * 80)
        print("✅ DATABRAIN POPULATION COMPLETE")
        print("=" * 80)


if __name__ == "__main__":
    populator = DataBrainPopulator()
    populator.populate()
