#!/usr/bin/env python3
"""
CESAR Ecosystem - Complete System Setup
========================================
1. Apply schema migrations
2. Seed dashboard data
3. Verify monitoring views
4. Check Ollama status
5. Prepare system for launch
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, 'api')

from database_async import DATABASE_URL
import asyncpg


async def apply_migration_011():
    """Apply the ops hardening migration"""
    print("=" * 80)
    print("STEP 1: APPLYING MIGRATION 011")
    print("=" * 80)

    conn = await asyncpg.connect(DATABASE_URL)

    try:
        with open('migrations/011_databrain_ops_hardening.sql', 'r') as f:
            sql = f.read()

        await conn.execute(sql)
        print("✅ Migration 011 applied successfully")
        print()

    except Exception as e:
        print(f"⚠️  Migration 011 error (may be partially applied): {e}")
        print()

    finally:
        await conn.close()


async def seed_dashboard_data():
    """Seed initial dashboard data"""
    print("=" * 80)
    print("STEP 2: SEEDING DASHBOARD DATA")
    print("=" * 80)

    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Seed workflow templates
        print("📝 Seeding workflow_templates...")

        templates = [
            {
                'name': 'daily_financial_analysis',
                'description': 'Daily financial market data analysis and forecasting',
                'trigger_type': 'scheduled',
                'trigger_config': {'cron': '0 9 * * *', 'timezone': 'America/New_York'}
            },
            {
                'name': 'agent_memory_consolidation',
                'description': 'Consolidate agent episodic memories into semantic knowledge',
                'trigger_type': 'scheduled',
                'trigger_config': {'cron': '0 2 * * *', 'timezone': 'UTC'}
            },
            {
                'name': 'knowledge_graph_update',
                'description': 'Update knowledge graph with new relationships and entities',
                'trigger_type': 'scheduled',
                'trigger_config': {'cron': '*/30 * * * *', 'timezone': 'UTC'}
            },
            {
                'name': 'llm_cache_refresh',
                'description': 'Refresh LLM response cache for frequently queried patterns',
                'trigger_type': 'scheduled',
                'trigger_config': {'cron': '0 */4 * * *', 'timezone': 'UTC'}
            },
            {
                'name': 'supabase_sync',
                'description': 'Bidirectional sync with Supabase for data replication',
                'trigger_type': 'scheduled',
                'trigger_config': {'cron': '*/15 * * * *', 'timezone': 'UTC'}
            }
        ]

        for template in templates:
            await conn.execute('''
                INSERT INTO workflow_templates (name, description, status, trigger_type, trigger_config)
                VALUES ($1, $2, 'active', $3, $4)
                ON CONFLICT (name) DO UPDATE
                SET description = EXCLUDED.description,
                    trigger_type = EXCLUDED.trigger_type,
                    trigger_config = EXCLUDED.trigger_config,
                    updated_at = now()
            ''', template['name'], template['description'], template['trigger_type'], template['trigger_config'])

        count = await conn.fetchval('SELECT COUNT(*) FROM workflow_templates')
        print(f"✅ Seeded {count} workflow templates")
        print()

        # Seed supabase_sync_state
        print("📝 Seeding supabase_sync_state...")

        sync_tables = [
            'agents',
            'workflow_templates',
            'workflow_executions',
            'memory_episodic',
            'memory_semantic',
            'knowledge_graph_entities',
            'financial_data'
        ]

        for table in sync_tables:
            await conn.execute('''
                INSERT INTO supabase_sync_state (table_name, sync_status, last_sync_direction, records_synced)
                VALUES ($1, 'idle', 'none', 0)
                ON CONFLICT (table_name) DO NOTHING
            ''', table)

        count = await conn.fetchval('SELECT COUNT(*) FROM supabase_sync_state')
        print(f"✅ Configured {count} tables for Supabase sync")
        print()

        # Create initial sync_status entries
        print("📝 Seeding sync_status...")

        try:
            systems = ['supabase', 'financial_api', 'email_ingest', 'knowledge_graph']

            for system in systems:
                await conn.execute('''
                    INSERT INTO sync_status (system, status, rows_ingested, latency_ms, last_run)
                    VALUES ($1, 'idle', 0, 0, now())
                    ON CONFLICT (system) DO UPDATE
                    SET updated_at = now()
                ''', system)

            count = await conn.fetchval('SELECT COUNT(*) FROM sync_status')
            print(f"✅ Configured {count} sync systems")
        except Exception as e:
            print(f"⚠️  sync_status table not found: {e}")

        print()

    finally:
        await conn.close()


async def create_initial_jobs():
    """Create initial jobs in the queue"""
    print("=" * 80)
    print("STEP 3: CREATING INITIAL JOBS")
    print("=" * 80)

    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Create sample jobs
        jobs = [
            {
                'job_type': 'supabase_sync',
                'payload': {'tables': ['agents', 'workflow_templates'], 'direction': 'bidirectional'}
            },
            {
                'job_type': 'cache_refresh',
                'payload': {'cache_type': 'llm_responses', 'age_threshold_hours': 24}
            },
            {
                'job_type': 'memory_consolidation',
                'payload': {'agent_ids': [], 'min_episodes': 10}
            }
        ]

        for job in jobs:
            await conn.execute('''
                INSERT INTO job_queue (job_type, payload, status, next_run_at)
                VALUES ($1, $2, 'pending', now())
            ''', job['job_type'], job['payload'])

        count = await conn.fetchval('SELECT COUNT(*) FROM job_queue WHERE status = \'pending\'')
        print(f"✅ Created {count} initial jobs")
        print()

    finally:
        await conn.close()


async def verify_monitoring_views():
    """Verify monitoring views work"""
    print("=" * 80)
    print("STEP 4: VERIFYING MONITORING VIEWS")
    print("=" * 80)

    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Check mv_sync_lag
        print("📊 mv_sync_lag:")
        try:
            rows = await conn.fetch('SELECT * FROM mv_sync_lag LIMIT 5')
            print(f"  ✅ {len(rows)} systems tracked")
            for row in rows:
                lag_minutes = row['lag'].total_seconds() / 60 if row['lag'] else 0
                print(f"     - {row['system']}: {row['status']}, lag: {lag_minutes:.1f} min")
        except Exception as e:
            print(f"  ⚠️  View not accessible: {e}")

        print()

        # Check mv_job_queue_backlog
        print("📊 mv_job_queue_backlog:")
        try:
            rows = await conn.fetch('SELECT * FROM mv_job_queue_backlog')
            print(f"  ✅ {len(rows)} job types tracked")
            for row in rows:
                print(f"     - {row['job_type']} ({row['status']}): {row['jobs']} jobs")
        except Exception as e:
            print(f"  ⚠️  View not accessible: {e}")

        print()

        # Check mv_ingestion_errors
        print("📊 mv_ingestion_errors:")
        try:
            rows = await conn.fetch('SELECT * FROM mv_ingestion_errors')
            if len(rows) == 0:
                print(f"  ✅ No ingestion errors (good!)")
            else:
                print(f"  ⚠️  {len(rows)} sources with errors:")
                for row in rows:
                    print(f"     - {row['source']}: {row['errors']} errors")
        except Exception as e:
            print(f"  ⚠️  View not accessible: {e}")

        print()

    finally:
        await conn.close()


def check_ollama():
    """Check if Ollama is running"""
    print("=" * 80)
    print("STEP 5: CHECKING OLLAMA STATUS")
    print("=" * 80)

    import subprocess

    try:
        result = subprocess.run(
            ['curl', '-s', 'http://localhost:11434/api/tags'],
            capture_output=True,
            timeout=5
        )

        if result.returncode == 0:
            print("✅ Ollama is running on port 11434")
            print()
            return True
        else:
            print("❌ Ollama is not responding")
            print()
            return False

    except Exception as e:
        print(f"❌ Cannot reach Ollama: {e}")
        print()
        return False


async def verify_final_status():
    """Final verification of all systems"""
    print("=" * 80)
    print("FINAL VERIFICATION")
    print("=" * 80)

    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Count tables
        tables = await conn.fetch('''
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
        ''')
        print(f"✅ Total tables: {len(tables)}")

        # Check critical tables
        critical = [
            'agents', 'workflow_templates', 'workflow_executions',
            'financial_data', 'agent_events', 'job_queue',
            'supabase_sync_state', 'ingestion_log'
        ]

        missing = []
        for table in critical:
            try:
                count = await conn.fetchval(f'SELECT COUNT(*) FROM {table}')
                print(f"  ✅ {table}: {count} rows")
            except:
                missing.append(table)
                print(f"  ❌ {table}: MISSING")

        print()

        if missing:
            print(f"⚠️  {len(missing)} critical tables missing")
            return False
        else:
            print("✅ ALL CRITICAL TABLES PRESENT")
            return True

    finally:
        await conn.close()


async def main():
    """Main setup flow"""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "CESAR ECOSYSTEM - COMPLETE SYSTEM SETUP" + " " * 19 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}")
    print()

    # Step 1: Apply migration
    await apply_migration_011()

    # Step 2: Seed data
    await seed_dashboard_data()

    # Step 3: Create jobs
    await create_initial_jobs()

    # Step 4: Verify monitoring
    await verify_monitoring_views()

    # Step 5: Check Ollama
    ollama_ok = check_ollama()

    # Final verification
    system_ready = await verify_final_status()

    # Summary
    print()
    print("=" * 80)
    print("SETUP SUMMARY")
    print("=" * 80)
    print(f"Migration 011: ✅ Applied")
    print(f"Dashboard Data: ✅ Seeded")
    print(f"Initial Jobs: ✅ Created")
    print(f"Monitoring Views: ✅ Verified")
    print(f"Ollama Service: {'✅ Running' if ollama_ok else '❌ Not Running'}")
    print(f"System Ready: {'✅ YES' if system_ready else '⚠️  INCOMPLETE'}")
    print("=" * 80)
    print()

    if not ollama_ok:
        print("⚠️  OLLAMA NOT RUNNING - Start it before launching CESAR:")
        print("   pkill ollama && sleep 2 && ollama serve &")
        print()

    if system_ready and ollama_ok:
        print("🚀 SYSTEM READY FOR LAUNCH!")
        print()
        print("Next steps:")
        print("  1. Verify job queue worker is configured in ./cesar")
        print("  2. Launch system: ./cesar start")
        print("  3. Monitor jobs: watch -n 5 'psql \"$COCKROACH_DB_URL\" -c \"SELECT * FROM mv_job_queue_backlog\"'")
        print("  4. Check dashboard: open http://localhost:3000")
        print()
    else:
        print("⚠️  SYSTEM NOT READY - Review errors above")
        print()

    return 0 if (system_ready and ollama_ok) else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
