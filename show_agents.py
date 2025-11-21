#!/usr/bin/env python3
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(os.getenv('COCKROACH_DB_URL'))
cur = conn.cursor()

print('='*70)
print('🎯 CESAR ECOSYSTEM: COMPLETE AGENT ROSTER')
print('='*70)
print()

# Get all agents grouped by MCP system
cur.execute('''
    SELECT mcp_system, name, type, status,
           tasks_completed, success_rate,
           endpoint_url
    FROM agents
    ORDER BY mcp_system, name
''')

agents = cur.fetchall()

from collections import defaultdict
by_system = defaultdict(list)

for agent in agents:
    system = agent[0] or 'unassigned'
    by_system[system].append({
        'name': agent[1],
        'type': agent[2],
        'status': agent[3],
        'tasks': agent[4] or 0,
        'success_rate': float(agent[5]) if agent[5] else 0.0,
        'endpoint': agent[6]
    })

print(f'📊 TOTAL AGENTS: {len(agents)}')
mcp_count = len([k for k in by_system.keys() if k != 'unassigned'])
print(f'📦 MCP SYSTEMS: {mcp_count}')
print()

# Display by system
for system in sorted(by_system.keys()):
    agents_list = by_system[system]
    print(f'\n▶ {system.upper()} ({len(agents_list)} agents)')
    print('  ' + '-'*66)

    for agent in agents_list:
        status_icon = '✅' if agent['status'] == 'active' else '⚠️'
        print(f"  {status_icon} {agent['name']:<30} | Type: {agent['type']:<15}")
        if agent['tasks'] > 0:
            print(f"     └─ Tasks: {agent['tasks']}, Success: {agent['success_rate']:.1f}%")

conn.close()

print()
print('='*70)
print('\n📋 SYSTEM ARCHITECTURE:')
print('   • Each MCP system is a specialized capability domain')
print('   • Agents within systems collaborate via A2A protocol')
print('   • Central orchestrator coordinates cross-system workflows')
print('   • Knowledge graph (DataBrain) stores shared learnings')
print('='*70)
