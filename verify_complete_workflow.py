#!/usr/bin/env python3
"""
Complete End-to-End Workflow Verification
Verifies all components are ready for production data flow
"""

import asyncio
import sys
from datetime import datetime
sys.path.insert(0, 'api')

async def main():
    from database_async import create_pool, get_db_connection, close_pool

    print('=' * 80)
    print('CESAR ECOSYSTEM - 100% END-TO-END WORKFLOW VERIFICATION')
    print('=' * 80)
    print(f'Timestamp: {datetime.now().isoformat()}')
    print()

    await create_pool()

    results = {}

    async with get_db_connection() as conn:
        # 1. DATABASE SCHEMA
        print('1️⃣  DATABASE SCHEMA')
        print('-' * 80)

        critical_tables = [
            'agents', 'workflow_templates', 'workflow_executions',
            'job_queue', 'financial_data', 'agent_events',
            'memory_episodic', 'memory_semantic',
            'supabase_sync_state', 'sync_status'
        ]

        schema_ok = True
        for table in critical_tables:
            try:
                count = await conn.fetchval(f'SELECT COUNT(*) FROM {table}')
                print(f'  ✅ {table}: {count} rows')
            except:
                print(f'  ❌ {table}: MISSING')
                schema_ok = False

        results['schema'] = schema_ok
        print()

        # 2. WORKFLOW CONFIGURATION
        print('2️⃣  WORKFLOW CONFIGURATION')
        print('-' * 80)

        templates = await conn.fetch('SELECT name, status FROM workflow_templates')
        print(f'  ✅ Workflow Templates: {len(templates)} configured')
        for t in templates:
            print(f'     - {t["name"]}: {t["status"]}')

        results['workflows'] = len(templates) >= 3
        print()

        # 3. JOB QUEUE
        print('3️⃣  JOB QUEUE')
        print('-' * 80)

        total_jobs = await conn.fetchval('SELECT COUNT(*) FROM job_queue')
        pending = await conn.fetchval("SELECT COUNT(*) FROM job_queue WHERE status='pending'")

        print(f'  Total jobs: {total_jobs}')
        print(f'  Pending jobs: {pending}')

        if pending > 0:
            jobs = await conn.fetch("SELECT job_type FROM job_queue WHERE status='pending'")
            print(f'  Ready to execute:')
            for j in jobs:
                print(f'     - {j["job_type"]}')

        results['jobs'] = total_jobs >= 1
        print()

        # 4. MONITORING VIEWS
        print('4️⃣  MONITORING VIEWS')
        print('-' * 80)

        views = ['mv_sync_lag', 'mv_job_queue_backlog', 'mv_ingestion_errors']
        views_ok = True
        for view in views:
            try:
                count = await conn.fetchval(f'SELECT COUNT(*) FROM {view}')
                print(f'  ✅ {view}: operational ({count} entries)')
            except Exception as e:
                print(f'  ❌ {view}: {e}')
                views_ok = False

        results['monitoring'] = views_ok
        print()

        # 5. AGENT ECOSYSTEM
        print('5️⃣  AGENT ECOSYSTEM')
        print('-' * 80)

        total_agents = await conn.fetchval('SELECT COUNT(*) FROM agents')
        active_agents = await conn.fetchval("SELECT COUNT(*) FROM agents WHERE status='active'")

        print(f'  Total agents: {total_agents}')
        print(f'  Active agents: {active_agents}')

        if total_agents > 0:
            sample = await conn.fetch('SELECT name, type FROM agents LIMIT 3')
            print(f'  Sample agents:')
            for a in sample:
                print(f'     - {a["name"]} ({a["type"]})')

        results['agents'] = total_agents >= 10
        print()

        # 6. DATA FLOW READINESS
        print('6️⃣  DATA FLOW READINESS')
        print('-' * 80)

        sync_configs = await conn.fetchval('SELECT COUNT(*) FROM supabase_sync_state')
        sync_systems = await conn.fetchval('SELECT COUNT(*) FROM sync_status')

        print(f'  Sync configurations: {sync_configs} tables')
        print(f'  Sync systems: {sync_systems} active')

        results['data_flow'] = sync_configs >= 3 and sync_systems >= 2
        print()

    await close_pool()

    # FINAL ASSESSMENT
    print('=' * 80)
    print('FINAL ASSESSMENT')
    print('=' * 80)
    print()

    all_pass = all(results.values())

    for component, status in results.items():
        emoji = '✅' if status else '❌'
        print(f'{emoji} {component.upper()}: {"PASS" if status else "FAIL"}')

    print()
    print('=' * 80)

    if all_pass:
        print('🎉 100% COMPLETE - SYSTEM READY FOR END-TO-END WORKFLOW!')
        print()
        print('Expected Data Flow:')
        print('  1. Launch: ./cesar start')
        print('  2. Job Worker: Picks up pending jobs from job_queue')
        print('  3. Jobs Execute: sync, cache refresh, memory consolidation')
        print('  4. Workflows Trigger: On schedule (cron)')
        print('  5. Agents Process: Financial data, memories, knowledge graph')
        print('  6. Data Persists: Results saved to CockroachDB')
        print('  7. Views Update: Monitoring views reflect real-time activity')
        print('  8. Dashboard Shows: Live metrics and agent activity')
        print()
        print('🚀 READY TO LAUNCH!')
        return 0
    else:
        print('⚠️  NOT FULLY READY - Address failures above')
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
