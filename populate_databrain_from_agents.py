#!/usr/bin/env python3
"""
Populate DataBrain Knowledge Graph from All 48 Agents
======================================================
Creates knowledge nodes for each agent, their specializations, and interconnections.
"""

import psycopg2
from dotenv import load_dotenv
import os
import json

load_dotenv()

def populate_databrain():
    """Create knowledge nodes for all agents in the ecosystem"""

    cockroach_url = os.getenv("COCKROACH_DB_URL")
    if not cockroach_url or "pending" in cockroach_url:
        print("❌ COCKROACH_DB_URL not configured properly")
        return

    conn = psycopg2.connect(cockroach_url)
    cur = conn.cursor()

    # Get all agents
    cur.execute("SELECT id, name, specialization, capabilities FROM agents")
    agents = cur.fetchall()

    print(f"📊 Found {len(agents)} agents")
    print("🧠 Populating DataBrain with agent knowledge nodes...\n")

    nodes_created = 0
    links_created = 0

    for agent_id, name, specialization, capabilities in agents:
        # Parse capabilities
        caps = json.loads(capabilities) if isinstance(capabilities, str) else capabilities or {}

        # Determine z-index based on agent role
        if "orchestrator" in name.lower() or "coordinator" in name.lower():
            z_index = 350  # Wisdom layer - strategic
            mass = 50.0
        elif "research" in specialization.lower() or "analysis" in specialization.lower():
            z_index = 250  # Knowledge layer
            mass = 35.0
        elif "specialist" in specialization.lower() or "expert" in specialization.lower():
            z_index = 220  # Knowledge layer
            mass = 30.0
        else:
            z_index = 150  # Information layer
            mass = 20.0

        # Create node for this agent
        label = f"{name} Agent"
        content = f"Specialization: {specialization}. Capabilities: {', '.join(caps.keys()) if caps else 'General purpose'}"

        # Position in 3D space (distribute evenly)
        import math
        angle = (nodes_created * 2 * math.pi) / len(agents)
        radius = 100 + (z_index / 10)
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        z = z_index

        try:
            cur.execute("""
                INSERT INTO graph_nodes (
                    label, content, x, y, z, z_index, mass,
                    created_at, updated_at, metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)
                ON CONFLICT (label) DO UPDATE
                SET content = EXCLUDED.content,
                    x = EXCLUDED.x,
                    y = EXCLUDED.y,
                    z = EXCLUDED.z,
                    z_index = EXCLUDED.z_index,
                    mass = EXCLUDED.mass,
                    updated_at = NOW()
                RETURNING id
            """, (
                label, content, x, y, z, z_index, mass,
                json.dumps({"agent_id": agent_id, "specialization": specialization})
            ))

            node_id = cur.fetchone()[0]
            nodes_created += 1
            print(f"   ✅ Created node: {label} (z={z_index:.0f}, mass={mass})")

        except Exception as e:
            print(f"   ❌ Error creating node for {name}: {e}")
            conn.rollback()
            continue

    # Create links between related agents
    print(f"\n🔗 Creating synaptic links between related agents...")

    # Get all nodes we just created
    cur.execute("""
        SELECT id, label, metadata
        FROM graph_nodes
        WHERE metadata->>'agent_id' IS NOT NULL
    """)
    nodes = cur.fetchall()

    # Create links based on specialization overlap
    specialization_groups = {}
    for node_id, label, metadata in nodes:
        meta = json.loads(metadata) if isinstance(metadata, str) else metadata
        spec = meta.get('specialization', '').lower()

        # Group by domain keywords
        for keyword in ['financial', 'research', 'communication', 'coordination', 'data', 'workflow']:
            if keyword in spec:
                if keyword not in specialization_groups:
                    specialization_groups[keyword] = []
                specialization_groups[keyword].append(node_id)

    # Create links within each group
    for group_name, node_ids in specialization_groups.items():
        for i, source_id in enumerate(node_ids):
            for target_id in node_ids[i+1:]:
                try:
                    cur.execute("""
                        INSERT INTO graph_links (source_id, target_id, weight, link_type, created_at)
                        VALUES (%s, %s, %s, %s, NOW())
                        ON CONFLICT DO NOTHING
                    """, (source_id, target_id, 0.7, f"{group_name}_collaboration"))

                    if cur.rowcount > 0:
                        links_created += 1

                except Exception as e:
                    print(f"   ⚠️  Could not create link: {e}")
                    conn.rollback()
                    continue

    conn.commit()

    # Verify final counts
    cur.execute("SELECT COUNT(*) FROM graph_nodes")
    total_nodes = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM graph_links")
    total_links = cur.fetchone()[0]

    conn.close()

    print(f"\n" + "="*60)
    print("✅ DATABRAIN POPULATION COMPLETE")
    print("="*60)
    print(f"   📊 Total knowledge nodes: {total_nodes}")
    print(f"   🔗 Total synaptic links: {total_links}")
    print(f"   ➕ Newly created nodes: {nodes_created}")
    print(f"   ➕ Newly created links: {links_created}")
    print("="*60)

if __name__ == "__main__":
    populate_databrain()
