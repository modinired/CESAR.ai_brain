#!/usr/bin/env python3
"""
Database Migration Script
=========================
Applies all SQL migrations to CockroachDB/PostgreSQL in order.
Tracks migration status and provides rollback capability.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import asyncpg

# Load environment
load_dotenv()
load_dotenv(".env.cockroach")

# Add api directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "api"))

# Import database config
from database_async import DATABASE_URL, USE_COCKROACH

# Migration files in order
MIGRATIONS = [
    "000_databrain_schema.sql",
    "001_phase_a_simplified.sql",
    "002_routing_rules.sql",
    "003_phase_b_cognitive_memory.sql",
    "004_phase_c_knowledge_graph.sql",
    "005_phase_d_attention_coordination.sql",
    "006_phase_e_continual_learning.sql",
    "007_local_llm_integration.sql",
    "008_a2a_protocol_and_llm_collaboration.sql",
    "009_supabase_integration.sql",
    "010_enhanced_databrain.sql",
    "010_synthetic_organism_visualization.sql",
    "011_hippocampal_replay_tracking.sql",
    "011_databrain_ops_hardening.sql",
    "012_agent_reputation_scoring.sql",
]

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


async def create_migration_tracking_table(conn):
    """Create table to track applied migrations"""
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id SERIAL PRIMARY KEY,
            migration_name TEXT NOT NULL UNIQUE,
            applied_at TIMESTAMPTZ DEFAULT now(),
            status TEXT DEFAULT 'applied',
            error_message TEXT
        )
    """)
    print("✅ Migration tracking table ready")


async def get_applied_migrations(conn):
    """Get list of already applied migrations"""
    try:
        rows = await conn.fetch("""
            SELECT migration_name
            FROM schema_migrations
            WHERE status = 'applied'
            ORDER BY id
        """)
        return {row['migration_name'] for row in rows}
    except Exception as e:
        print(f"⚠️  Could not read migration history: {e}")
        return set()


async def apply_migration(conn, migration_name):
    """Apply a single migration file"""
    migration_path = MIGRATIONS_DIR / migration_name

    if not migration_path.exists():
        print(f"⚠️  Migration file not found: {migration_name}")
        return False

    try:
        # Read migration SQL
        with open(migration_path, 'r') as f:
            sql = f.read()

        # Apply migration in transaction
        async with conn.transaction():
            await conn.execute(sql)
            await conn.execute("""
                INSERT INTO schema_migrations (migration_name, status)
                VALUES ($1, 'applied')
                ON CONFLICT (migration_name) DO NOTHING
            """, migration_name)

        print(f"✅ Applied: {migration_name}")
        return True

    except Exception as e:
        print(f"❌ Failed to apply {migration_name}: {e}")

        # Record failure
        try:
            await conn.execute("""
                INSERT INTO schema_migrations (migration_name, status, error_message)
                VALUES ($1, 'failed', $2)
                ON CONFLICT (migration_name)
                DO UPDATE SET status = 'failed', error_message = $2, applied_at = now()
            """, migration_name, str(e))
        except:
            pass

        return False


async def verify_schema(conn):
    """Verify critical tables exist"""
    critical_tables = [
        'agents',
        'workflow_templates',
        'workflow_executions',
        'financial_data',
        'agent_events',
        'memory_episodic',
        'memory_semantic',
    ]

    print("\n" + "=" * 80)
    print("SCHEMA VERIFICATION")
    print("=" * 80)

    tables = await conn.fetch("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)

    existing_tables = {row['table_name'] for row in tables}

    print(f"\n✅ Total tables: {len(existing_tables)}")

    missing = []
    for table in critical_tables:
        if table in existing_tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            print(f"  ✅ {table}: {count} rows")
        else:
            print(f"  ❌ {table}: MISSING")
            missing.append(table)

    if missing:
        print(f"\n⚠️  Warning: {len(missing)} critical tables missing: {missing}")
        return False

    print("\n✅ All critical tables present!")
    return True


async def main():
    """Main migration execution"""
    print("=" * 80)
    print("CESAR ECOSYSTEM - DATABASE MIGRATION TOOL")
    print("=" * 80)
    print(f"Database: {'CockroachDB' if USE_COCKROACH else 'PostgreSQL'}")
    print(f"Endpoint: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}")
    print("=" * 80)
    print()

    # Connect to database
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected to database")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return 1

    try:
        # Create migration tracking table
        await create_migration_tracking_table(conn)

        # Get already applied migrations
        applied = await get_applied_migrations(conn)
        print(f"📋 Previously applied migrations: {len(applied)}")

        # Apply pending migrations
        print("\n" + "=" * 80)
        print("APPLYING MIGRATIONS")
        print("=" * 80)

        pending = [m for m in MIGRATIONS if m not in applied]

        if not pending:
            print("✅ No pending migrations - database is up to date!")
        else:
            print(f"📝 Found {len(pending)} pending migrations\n")

            success_count = 0
            for migration in pending:
                if await apply_migration(conn, migration):
                    success_count += 1
                else:
                    print(f"\n⚠️  Migration failed. Stopping here to prevent cascading failures.")
                    break

            print(f"\n✅ Successfully applied {success_count}/{len(pending)} migrations")

        # Verify schema
        schema_ok = await verify_schema(conn)

        # Summary
        print("\n" + "=" * 80)
        print("MIGRATION SUMMARY")
        print("=" * 80)

        all_tables = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)

        print(f"Total tables in database: {len(all_tables)}")
        print(f"Schema verification: {'✅ PASS' if schema_ok else '❌ FAIL'}")
        print(f"Database ready: {'✅ YES' if schema_ok else '⚠️  INCOMPLETE'}")
        print("=" * 80)

        return 0 if schema_ok else 1

    finally:
        await conn.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
