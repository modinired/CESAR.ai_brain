#!/usr/bin/env python3
"""
Seed Demo Data for Atlas Pro Dashboard
========================================
Populates database with sample data for visualization
"""

import os
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random

load_dotenv()

COCKROACH_DB_URL = os.getenv("COCKROACH_DB_URL")

def seed_graph_nodes():
    """Seed graph_nodes for 3D DataBrain"""
    print("🧠 Seeding graph nodes...")

    conn = psycopg2.connect(COCKROACH_DB_URL)
    cur = conn.cursor()

    # Node types and colors
    node_types = [
        ('concept', '#3B82F6'),
        ('skill', '#8B5CF6'),
        ('domain', '#EC4899'),
        ('pattern', '#10B981'),
        ('insight', '#F59E0B')
    ]

    nodes = []
    node_id_counter = 1

    # Generate 60 nodes distributed in 3D space
    for node_type, color in node_types:
        for i in range(12):  # 12 nodes per type = 60 total
            x = random.uniform(-10, 10)
            y = random.uniform(-10, 10)
            z = random.uniform(-10, 10)
            mass = random.uniform(2, 8)
            access_count = random.randint(10, 500)

            node_id = f"node_{node_id_counter}"
            label = f"{node_type.title()} {i+1}"
            description = f"Sample {node_type} node for knowledge graph"

            nodes.append((
                node_id, label, node_type, x, y, z, mass,
                description, datetime.now(), access_count
            ))

            node_id_counter += 1

    # Insert nodes
    execute_values(cur, """
        INSERT INTO graph_nodes
        (node_id, label, type, x_coord, y_coord, z_index, mass, description, last_accessed, access_count)
        VALUES %s
        ON CONFLICT (node_id) DO NOTHING
    """, nodes)

    conn.commit()
    print(f"✅ Inserted {len(nodes)} graph nodes")

    cur.close()
    conn.close()

def seed_graph_edges():
    """Seed graph_links for connections"""
    print("🔗 Seeding graph links...")

    conn = psycopg2.connect(COCKROACH_DB_URL)
    cur = conn.cursor()

    # Get all node IDs
    cur.execute("SELECT node_id FROM graph_nodes LIMIT 60")
    node_ids = [row[0] for row in cur.fetchall()]

    edges = []
    link_types = ['semantic', 'causal', 'temporal', 'hierarchical']

    # Create 80 random edges
    link_counter = 1
    for _ in range(80):
        if len(node_ids) < 2:
            break
        source = random.choice(node_ids)
        target = random.choice([n for n in node_ids if n != source])
        strength = random.uniform(0.3, 1.0)
        link_type = random.choice(link_types)
        link_id = f"{source}_{link_type}_{target}"

        edges.append((
            link_id,
            source,
            target,
            strength,
            link_type,
            datetime.now(),
            0  # traversal_count
        ))
        link_counter += 1

    execute_values(cur, """
        INSERT INTO graph_links
        (link_id, source_node_id, target_node_id, strength, link_type, created_at, traversal_count)
        VALUES %s
        ON CONFLICT (link_id) DO NOTHING
    """, edges)

    conn.commit()
    print(f"✅ Inserted {len(edges)} graph links")

    cur.close()
    conn.close()

def seed_workflows():
    """Seed workflows for Automation Matrix"""
    print("⚡ Seeding workflows...")

    conn = psycopg2.connect(COCKROACH_DB_URL)
    cur = conn.cursor()

    workflow_templates = [
        ("Portfolio Rebalancing", "portfolio_optimizer", "Automatically rebalances portfolio based on risk tolerance"),
        ("Market Analysis", "financial_analyst", "Analyzes market trends and generates insights"),
        ("Risk Assessment", "risk_manager", "Evaluates portfolio risk metrics"),
        ("Compliance Check", "compliance_monitor", "Monitors regulatory compliance"),
        ("Data Collection", "market_intelligence", "Collects and processes market data"),
        ("Performance Report", "financial_analyst", "Generates performance analytics"),
        ("Trade Execution", "portfolio_optimizer", "Executes optimized trades"),
        ("Alert Monitoring", "risk_manager", "Monitors and triggers risk alerts"),
        ("Document Processing", "compliance_monitor", "Processes regulatory documents"),
        ("Sentiment Analysis", "market_intelligence", "Analyzes market sentiment")
    ]

    workflows = []
    statuses = ['running', 'completed', 'pending', 'failed']

    for i, (name, agent_id, description) in enumerate(workflow_templates):
        status = random.choices(statuses, weights=[0.3, 0.5, 0.15, 0.05])[0]

        if status == 'completed':
            progress_percent = 100
        elif status == 'running':
            progress_percent = int(random.uniform(20, 90))
        else:
            progress_percent = 0

        created_at = datetime.now() - timedelta(hours=random.randint(1, 48))
        started_at = created_at + timedelta(minutes=5) if status != 'pending' else None
        completed_at = datetime.now() if status == 'completed' else None

        workflows.append((
            name,
            description,
            status,
            progress_percent,
            created_at,
            started_at,
            completed_at,
            agent_id
        ))

    # Use individual inserts to avoid column caching issues
    for wf in workflows:
        cur.execute("""
            INSERT INTO workflows
            (workflow_name, description, status, progress_percent, created_at, started_at, completed_at, assigned_agent)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, wf)

    conn.commit()
    print(f"✅ Inserted {len(workflows)} workflows")

    cur.close()
    conn.close()

def seed_sync_status():
    """Seed sync_status for Database Sync monitor"""
    print("🔄 Seeding sync status...")

    conn = psycopg2.connect(COCKROACH_DB_URL)
    cur = conn.cursor()

    tables_info = [
        ('agents', 'Operational', '5 min', 245),
        ('workflows', 'Operational', '5 min', 150),
        ('agent_cognition', 'Analytics', '15 min', 1200),
        ('performance_logs', 'Analytics', '15 min', 3500),
        ('graph_nodes', 'Knowledge', '30 min', 850),
        ('graph_edges', 'Knowledge', '30 min', 1200),
        ('knowledge_domains', 'Knowledge', '30 min', 95),
        ('memory_vectors', 'Memory', '60 min', 5000),
        ('context_history', 'Memory', '60 min', 8500)
    ]

    sync_data = []
    for table_name, data_type, frequency, records in tables_info:
        last_sync = datetime.now() - timedelta(minutes=random.randint(1, 30))

        # Parse frequency to calculate next sync
        freq_minutes = int(frequency.split()[0])
        next_sync = last_sync + timedelta(minutes=freq_minutes)

        sync_data.append((
            table_name, last_sync, records, frequency, next_sync, data_type
        ))

    execute_values(cur, """
        INSERT INTO sync_status
        (table_name, last_sync, records_synced, sync_frequency, next_sync, data_type)
        VALUES %s
        ON CONFLICT (table_name) DO UPDATE SET
            last_sync = EXCLUDED.last_sync,
            records_synced = EXCLUDED.records_synced,
            next_sync = EXCLUDED.next_sync
    """, sync_data)

    conn.commit()
    print(f"✅ Inserted {len(sync_data)} sync status records")

    cur.close()
    conn.close()

def seed_optic_nerve_jobs():
    """Seed optic nerve jobs"""
    print("👁️ Seeding optic nerve jobs...")

    conn = psycopg2.connect(COCKROACH_DB_URL)
    cur = conn.cursor()

    jobs = []
    for i in range(15):
        created_at = datetime.now() - timedelta(hours=random.randint(1, 24))
        processed_at = created_at + timedelta(seconds=random.randint(2, 30))

        jobs.append((
            f"optic_job_{i+1}",
            f"/uploads/image_{i+1}.jpg",
            random.choice(['completed', 'completed', 'completed', 'running']),
            random.uniform(0.85, 0.99),
            created_at,
            processed_at,
            f"Detected {random.randint(3, 12)} objects with high confidence"
        ))

    execute_values(cur, """
        INSERT INTO optic_nerve_jobs
        (id, image_path, status, confidence_score, created_at, processed_at, result_summary)
        VALUES %s
        ON CONFLICT (id) DO NOTHING
    """, jobs)

    conn.commit()
    print(f"✅ Inserted {len(jobs)} optic nerve jobs")

    cur.close()
    conn.close()

def main():
    """Seed all demo data"""
    print("🌱 Starting demo data seed...")
    print(f"Database: {COCKROACH_DB_URL[:50]}...")

    try:
        seed_graph_nodes()
        seed_graph_edges()
        seed_workflows()
        seed_sync_status()
        seed_optic_nerve_jobs()

        print("\n✅ ALL DEMO DATA SEEDED SUCCESSFULLY!")
        print("\n📊 Summary:")
        print("  • 60 knowledge graph nodes (3D DataBrain)")
        print("  • 80 graph edges (connections)")
        print("  • 10 workflows (Automation Matrix)")
        print("  • 9 sync status records (Database Sync)")
        print("  • 15 optic nerve jobs (Visual Intelligence)")
        print("\n🚀 Ready to launch Atlas Pro Dashboard!")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
