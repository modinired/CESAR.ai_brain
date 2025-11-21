#!/usr/bin/env python3
"""
CESAR Ecosystem → CockroachDB Cloud Sync
Syncs all 24 agents with mob aliases to CockroachDB Serverless
"""

import os
import sys
import json
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

# Local database (source)
# Use environment variables or fall back to current user/cesar_src database
LOCAL_DB = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "dbname": os.getenv("POSTGRES_DB", "cesar_src"),
    "user": os.getenv("POSTGRES_USER", os.getenv("USER", "modini_red")),
}

# CockroachDB (destination)
COCKROACH_URL = os.getenv("COCKROACH_DB_URL")


def create_tables_in_cockroach(conn):
    """Create all necessary tables in CockroachDB"""
    print("📋 Creating tables in CockroachDB...")

    with conn.cursor() as cur:
        # Agents table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                agent_id VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                type VARCHAR(100) NOT NULL,
                status VARCHAR(50) DEFAULT 'idle',
                version VARCHAR(50),
                capabilities JSONB DEFAULT '[]',
                skills JSONB DEFAULT '[]',
                protocols JSONB DEFAULT '[]',
                config JSONB DEFAULT '{}',
                environment JSONB DEFAULT '{}',
                metadata JSONB DEFAULT '{}',
                tasks_completed INT DEFAULT 0,
                tasks_failed INT DEFAULT 0,
                success_rate DECIMAL(5,2) DEFAULT 0.0,
                avg_response_time_ms INT,
                uptime_percentage DECIMAL(5,2),
                current_memory_mb INT,
                current_cpu_percent DECIMAL(5,2),
                max_concurrent_tasks INT DEFAULT 5,
                current_task_count INT DEFAULT 0,
                endpoint_url TEXT,
                health_check_url TEXT,
                last_heartbeat TIMESTAMPTZ,
                last_health_check TIMESTAMPTZ,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                created_by VARCHAR(255),
                mcp_system VARCHAR(100),
                tenant_id UUID
            )
        """)

        # A2A Messages
        cur.execute("""
            CREATE TABLE IF NOT EXISTS a2a_messages (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                conversation_id UUID,
                from_agent_id VARCHAR(255),
                to_agent_id VARCHAR(255),
                message_type VARCHAR(50),
                content TEXT,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        # A2A Conversations
        cur.execute("""
            CREATE TABLE IF NOT EXISTS a2a_conversations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                conversation_type VARCHAR(100),
                participants JSONB DEFAULT '[]',
                status VARCHAR(50) DEFAULT 'active',
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        # LLM Collaborations
        cur.execute("""
            CREATE TABLE IF NOT EXISTS llm_collaborations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id VARCHAR(255),
                agent_id VARCHAR(255),
                prompt TEXT,
                local_model VARCHAR(100),
                cloud_model VARCHAR(100),
                local_response TEXT,
                cloud_response TEXT,
                selected_model VARCHAR(100),
                quality_score DECIMAL(3,2),
                cost DECIMAL(10,6),
                latency_ms INT,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        # Sessions
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id VARCHAR(255) UNIQUE,
                user_id VARCHAR(255),
                agent_id VARCHAR(255),
                status VARCHAR(50) DEFAULT 'active',
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        # Tasks
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                task_id VARCHAR(255) UNIQUE,
                agent_id VARCHAR(255),
                title VARCHAR(500),
                description TEXT,
                status VARCHAR(50) DEFAULT 'pending',
                priority INT DEFAULT 5,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                completed_at TIMESTAMPTZ
            )
        """)

        # Create indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_agents_agent_id ON agents(agent_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_a2a_messages_conversation ON a2a_messages(conversation_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_agent_id ON tasks(agent_id)")

        conn.commit()
        print("✅ Tables created successfully")


def sync_agents(local_conn, cloud_conn):
    """Sync agents from local to CockroachDB"""
    print("🤖 Syncing agents...")

    with local_conn.cursor(row_factory=dict_row) as local_cur:
        local_cur.execute("""
            SELECT id, agent_id, name, type, status, version,
                   capabilities, skills, protocols, config, environment, metadata,
                   tasks_completed, tasks_failed, success_rate,
                   avg_response_time_ms, uptime_percentage, current_memory_mb,
                   created_at, updated_at
            FROM agents
        """)
        agents = local_cur.fetchall()

        print(f"   Found {len(agents)} agents in local database")

        with cloud_conn.cursor() as cloud_cur:
            for agent in agents:
                # Convert dict fields to Jsonb for psycopg3
                agent_data = dict(agent)
                for json_field in ['capabilities', 'skills', 'protocols', 'config', 'environment', 'metadata']:
                    if agent_data.get(json_field) is not None:
                        agent_data[json_field] = Jsonb(agent_data[json_field])

                cloud_cur.execute("""
                    INSERT INTO agents (
                        id, agent_id, name, type, status, version,
                        capabilities, skills, protocols, config, environment, metadata,
                        tasks_completed, tasks_failed, success_rate,
                        avg_response_time_ms, uptime_percentage, current_memory_mb,
                        created_at, updated_at
                    ) VALUES (
                        %(id)s, %(agent_id)s, %(name)s, %(type)s, %(status)s, %(version)s,
                        %(capabilities)s, %(skills)s, %(protocols)s, %(config)s, %(environment)s, %(metadata)s,
                        %(tasks_completed)s, %(tasks_failed)s, %(success_rate)s,
                        %(avg_response_time_ms)s, %(uptime_percentage)s, %(current_memory_mb)s,
                        %(created_at)s, %(updated_at)s
                    )
                    ON CONFLICT (agent_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        status = EXCLUDED.status,
                        metadata = EXCLUDED.metadata,
                        updated_at = NOW()
                """, agent_data)

            cloud_conn.commit()
            print(f"✅ Synced {len(agents)} agents to CockroachDB")


def verify_sync(conn):
    """Verify data was synced correctly"""
    print("\n🔍 Verifying sync...")

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT COUNT(*) as total FROM agents")
        count = cur.fetchone()['total']

        cur.execute("""
            SELECT agent_id, name, metadata->>'mob_alias' as mob_alias
            FROM agents
            WHERE metadata->>'mob_alias' IS NOT NULL
            LIMIT 5
        """)
        sample = cur.fetchall()

        print(f"\n✅ Total agents in CockroachDB: {count}")
        print("\n📋 Sample agents with mob aliases:")
        for agent in sample:
            print(f"   • {agent['name']:30} → {agent['mob_alias']}")


def main():
    if not COCKROACH_URL or COCKROACH_URL == "pending":
        print("❌ Error: COCKROACH_DB_URL not configured")
        print("   Please update .env with your CockroachDB connection string")
        print("   Format: postgresql://user:password@host:26257/defaultdb?sslmode=verify-full")
        sys.exit(1)

    print("=" * 80)
    print("CESAR ECOSYSTEM → COCKROACHDB SYNC")
    print("=" * 80)
    print()

    try:
        # Connect to local database
        print("🔌 Connecting to local PostgreSQL...")
        local_conn = psycopg.connect(**LOCAL_DB)
        print("✅ Connected to local database")

        # Connect to CockroachDB
        print("🔌 Connecting to CockroachDB...")
        cloud_conn = psycopg.connect(COCKROACH_URL)
        print("✅ Connected to CockroachDB")

        # Create tables
        create_tables_in_cockroach(cloud_conn)

        # Sync data
        sync_agents(local_conn, cloud_conn)

        # Verify
        verify_sync(cloud_conn)

        print("\n" + "=" * 80)
        print("🎉 SYNC COMPLETE!")
        print("=" * 80)
        print("\nYour 24 agents with mob aliases are now in CockroachDB Cloud!")
        print("Dashboard will automatically use this data once configured.")

        local_conn.close()
        cloud_conn.close()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
