#!/usr/bin/env python3
"""
CESAR Hourly Data Ingestion Service
====================================
Runs every hour to:
1. Collect agent interaction data
2. Ingest external data sources
3. Update knowledge graph
4. Prepare training data for LoRA fine-tuning
"""

import os
import json
import psycopg
from psycopg.rows import dict_row
from datetime import datetime, timedelta
import time
import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from services.brain_agent_integration import DataBrainAgent

# Load environment
load_dotenv()
load_dotenv(".env.cockroach")


class HourlyDataIngestion:
    """Hourly data collection and ingestion service"""

    def __init__(self):
        self.db_url = os.getenv("COCKROACH_DB_URL")
        if not self.db_url:
            raise ValueError("COCKROACH_DB_URL not configured")

        self.brain_agent = DataBrainAgent(agent_id="data_ingestion_service")
        self.training_data_dir = Path(__file__).parent.parent / "training_data"
        self.training_data_dir.mkdir(exist_ok=True)

    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")

    def collect_agent_interactions(self):
        """Collect recent agent interactions for training data"""
        self.log("📊 Collecting agent interactions from last hour...")

        conn = psycopg.connect(self.db_url)
        cur = conn.cursor(row_factory=dict_row)

        # Get A2A messages from last hour
        cur.execute("""
            SELECT
                m.id, m.from_agent_id, m.to_agent_id,
                m.message_type, m.content, m.metadata,
                m.created_at,
                c.conversation_type
            FROM a2a_messages m
            INNER JOIN a2a_conversations c ON m.conversation_id = c.id
            WHERE m.created_at > NOW() - INTERVAL '1 hour'
            ORDER BY m.created_at DESC
            LIMIT 100
        """)

        messages = cur.fetchall()

        # Get LLM collaborations from last hour
        cur.execute("""
            SELECT
                id, agent_id, prompt, local_model, cloud_model,
                local_response, cloud_response, selected_model,
                quality_score, cost, latency_ms, created_at
            FROM llm_collaborations
            WHERE created_at > NOW() - INTERVAL '1 hour'
            AND quality_score > 0.8
            ORDER BY quality_score DESC
            LIMIT 50
        """)

        collaborations = cur.fetchall()

        cur.close()
        conn.close()

        self.log(f"   ✅ Collected {len(messages)} messages and {len(collaborations)} LLM collaborations")

        return {
            "messages": messages,
            "collaborations": collaborations,
            "timestamp": datetime.now().isoformat()
        }

    def ingest_external_data(self):
        """Simulate ingestion of external data sources"""
        self.log("🌐 Ingesting external data sources...")

        # This is where you would integrate with:
        # - RSS feeds
        # - APIs (news, financial data, etc.)
        # - Email monitoring
        # - Document uploads

        # For now, we'll create sample knowledge nodes
        external_insights = [
            {
                "label": f"Market Update {datetime.now().strftime('%Y-%m-%d %H:00')}",
                "type": "information",
                "description": "Hourly market sentiment and trend analysis"
            },
            {
                "label": f"Agent Performance Metrics {datetime.now().strftime('%Y-%m-%d %H:00')}",
                "type": "knowledge",
                "description": "Aggregated agent efficiency and success rates"
            }
        ]

        actions = []
        for insight in external_insights:
            actions.append({
                "action": "CREATE_NODE",
                "params": {
                    "label": insight["label"],
                    "type": insight["type"],
                    "initial_mass": 15,
                    "description": insight["description"]
                }
            })

        result = self.brain_agent.apply_neuroplasticity(actions)
        self.log(f"   ✅ Ingested {result['applied']} external data points")

        return result

    def update_knowledge_graph(self):
        """Update knowledge graph based on agent learnings"""
        self.log("🧠 Updating knowledge graph...")

        conn = psycopg.connect(self.db_url)
        cur = conn.cursor(row_factory=dict_row)

        # Identify high-value knowledge: frequently accessed nodes
        cur.execute("""
            SELECT node_id, label, access_count, mass
            FROM graph_nodes
            WHERE last_accessed > NOW() - INTERVAL '1 hour'
            ORDER BY access_count DESC
            LIMIT 10
        """)

        active_nodes = cur.fetchall()

        # Boost mass for frequently accessed nodes
        actions = []
        for node in active_nodes:
            actions.append({
                "action": "UPDATE_MASS",
                "params": {
                    "target_id": node["node_id"],
                    "delta": 3.0
                }
            })

        cur.close()
        conn.close()

        if actions:
            result = self.brain_agent.apply_neuroplasticity(actions)
            self.log(f"   ✅ Updated {result['applied']} high-value knowledge nodes")
        else:
            self.log(f"   ℹ️  No active nodes to update")

    def prepare_training_data(self):
        """Prepare high-quality training data for LoRA fine-tuning"""
        self.log("📚 Preparing training data for model fine-tuning...")

        conn = psycopg.connect(self.db_url)
        cur = conn.cursor(row_factory=dict_row)

        # Select best interactions: high quality scores, completed tasks
        cur.execute("""
            SELECT
                l.prompt,
                CASE
                    WHEN l.quality_score > 0.9 THEN l.cloud_response
                    ELSE l.local_response
                END as response,
                l.quality_score,
                l.agent_id,
                l.created_at
            FROM llm_collaborations l
            WHERE
                l.created_at > NOW() - INTERVAL '7 days'
                AND l.quality_score > 0.85
            ORDER BY l.quality_score DESC, l.created_at DESC
            LIMIT 200
        """)

        training_samples = cur.fetchall()

        # Also get successful A2A interactions
        cur.execute("""
            SELECT
                m.content as prompt,
                (SELECT m2.content
                 FROM a2a_messages m2
                 WHERE m2.conversation_id = m.conversation_id
                 AND m2.created_at > m.created_at
                 AND m2.from_agent_id = m.to_agent_id
                 ORDER BY m2.created_at
                 LIMIT 1
                ) as response
            FROM a2a_messages m
            WHERE
                m.created_at > NOW() - INTERVAL '7 days'
                AND m.message_type = 'REQUEST'
            LIMIT 100
        """)

        a2a_samples = cur.fetchall()

        cur.close()
        conn.close()

        # Format for training
        training_dataset = []

        for sample in training_samples:
            if sample['response']:
                training_dataset.append({
                    "instruction": sample['prompt'],
                    "output": sample['response'],
                    "quality_score": float(sample['quality_score']),
                    "agent_id": sample['agent_id'],
                    "timestamp": sample['created_at'].isoformat()
                })

        for sample in a2a_samples:
            if sample['response']:
                training_dataset.append({
                    "instruction": sample['prompt'],
                    "output": sample['response'],
                    "quality_score": 0.85,  # Default for A2A
                    "agent_id": "a2a_protocol",
                    "timestamp": datetime.now().isoformat()
                })

        # Save to file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.training_data_dir / f"training_data_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump(training_dataset, f, indent=2)

        self.log(f"   ✅ Prepared {len(training_dataset)} training samples")
        self.log(f"   💾 Saved to: {output_file}")

        return {
            "samples": len(training_dataset),
            "file": str(output_file)
        }

    def run_ingestion_cycle(self):
        """Run complete ingestion cycle"""
        self.log("=" * 80)
        self.log("🚀 STARTING HOURLY DATA INGESTION CYCLE")
        self.log("=" * 80)

        try:
            # Step 1: Collect agent interactions
            interactions = self.collect_agent_interactions()

            # Step 2: Ingest external data
            external_result = self.ingest_external_data()

            # Step 3: Update knowledge graph
            self.update_knowledge_graph()

            # Step 4: Prepare training data
            training_result = self.prepare_training_data()

            self.log("=" * 80)
            self.log("✅ HOURLY INGESTION CYCLE COMPLETE")
            self.log("=" * 80)
            self.log(f"   📊 Agent Messages: {len(interactions['messages'])}")
            self.log(f"   🤖 LLM Collaborations: {len(interactions['collaborations'])}")
            self.log(f"   🌐 External Data Points: {external_result['applied']}")
            self.log(f"   📚 Training Samples: {training_result['samples']}")

            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "metrics": {
                    "messages_collected": len(interactions['messages']),
                    "collaborations": len(interactions['collaborations']),
                    "external_data": external_result['applied'],
                    "training_samples": training_result['samples']
                }
            }

        except Exception as e:
            self.log(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}


def run_continuous_ingestion(interval_seconds=3600):
    """Run ingestion service continuously"""
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║  CESAR ECOSYSTEM: HOURLY DATA INGESTION SERVICE               ║
    ║  Running continuously every hour                               ║
    ║  Press Ctrl+C to stop                                          ║
    ╚════════════════════════════════════════════════════════════════╝
    """)

    ingestion = HourlyDataIngestion()

    while True:
        try:
            # Run ingestion cycle
            result = ingestion.run_ingestion_cycle()

            # Wait until next cycle
            next_run = datetime.now() + timedelta(seconds=interval_seconds)
            ingestion.log(f"\n⏰ Next cycle at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            ingestion.log(f"💤 Sleeping for {interval_seconds/60:.0f} minutes...\n")

            time.sleep(interval_seconds)

        except KeyboardInterrupt:
            ingestion.log("\n🛑 Stopping ingestion service...")
            break
        except Exception as e:
            ingestion.log(f"❌ Cycle error: {e}")
            ingestion.log("⏰ Retrying in 5 minutes...")
            time.sleep(300)


def run_once():
    """Run ingestion once (for testing or manual runs)"""
    ingestion = HourlyDataIngestion()
    return ingestion.run_ingestion_cycle()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Run once for testing
        result = run_once()
        sys.exit(0 if result['status'] == 'success' else 1)
    else:
        # Run continuously
        run_continuous_ingestion(interval_seconds=3600)  # Every hour
