#!/usr/bin/env python3
"""Quick dashboard data seeding"""

import asyncio
import sys
import json
sys.path.insert(0, 'api')

async def seed_all():
    from database_async import create_pool, get_db_connection, close_pool

    print("Seeding dashboard data...")
    print()

    await create_pool()
    async with get_db_connection() as conn:
        # Clear existing data for fresh start
        await conn.execute('DELETE FROM workflow_templates')
        await conn.execute('DELETE FROM supabase_sync_state')
        await conn.execute("DELETE FROM job_queue WHERE status = 'pending'")

        # Seed workflow_templates
        templates = [
            ('daily_financial_analysis', 'Daily financial market data analysis', 'scheduled', {'cron': '0 9 * * *'}),
            ('memory_consolidation', 'Agent memory consolidation', 'scheduled', {'cron': '0 2 * * *'}),
            ('knowledge_graph_update', 'Update knowledge graph', 'scheduled', {'cron': '*/30 * * * *'}),
            ('llm_cache_refresh', 'Refresh LLM cache', 'scheduled', {'cron': '0 */4 * * *'}),
            ('supabase_sync', 'Sync with Supabase', 'scheduled', {'cron': '*/15 * * * *'}),
        ]

        for name, desc, trigger_type, trigger_config in templates:
            await conn.execute('''
                INSERT INTO workflow_templates (name, description, status, trigger_type, trigger_config)
                VALUES ($1, $2, 'active', $3, $4::jsonb)
            ''', name, desc, trigger_type, json.dumps(trigger_config))

        count = await conn.fetchval('SELECT COUNT(*) FROM workflow_templates')
        print(f'✅ Seeded {count} workflow templates')

        # Seed supabase_sync_state
        tables = ['agents', 'workflow_templates', 'memory_episodic', 'memory_semantic', 'financial_data']

        for table in tables:
            await conn.execute('''
                INSERT INTO supabase_sync_state (table_name, sync_status, last_sync_direction, records_synced)
                VALUES ($1, 'idle', 'none', 0)
            ''', table)

        count = await conn.fetchval('SELECT COUNT(*) FROM supabase_sync_state')
        print(f'✅ Seeded {count} sync state entries')

        # Seed sync_status
        try:
            systems = ['supabase', 'financial_api', 'email_ingest']
            for system in systems:
                await conn.execute('''
                    INSERT INTO sync_status (system, status, rows_ingested, latency_ms, last_run)
                    VALUES ($1, 'idle', 0, 0, now())
                ''', system)
            count = await conn.fetchval('SELECT COUNT(*) FROM sync_status')
            print(f'✅ Seeded {count} sync systems')
        except Exception as e:
            print(f'⚠️  sync_status: {e}')

        # Seed initial jobs
        jobs = [
            ('supabase_sync', {'tables': ['agents'], 'direction': 'pull'}),
            ('cache_refresh', {'cache_type': 'llm_responses'}),
            ('memory_consolidation', {'min_episodes': 10}),
        ]

        for job_type, payload in jobs:
            await conn.execute('''
                INSERT INTO job_queue (job_type, payload, status, next_run_at)
                VALUES ($1, $2::jsonb, 'pending', now())
            ''', job_type, json.dumps(payload))

        count = await conn.fetchval("SELECT COUNT(*) FROM job_queue WHERE status = 'pending'")
        print(f'✅ Created {count} pending jobs')

        print()
        print('✅ Dashboard seeding complete!')

    await close_pool()

asyncio.run(seed_all())
