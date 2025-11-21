import sys
sys.path.insert(0, '/app')

import psycopg2
import os
import json
from datetime import datetime

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://mcp_user:password@postgres:5432/mcp')

import re
match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
if match:
    user, password, host, port, dbname = match.groups()
else:
    print("❌ Could not parse DATABASE_URL")
    sys.exit(1)

WORKFLOWS = [
    {
        "name": "Financial Market Analysis",
        "description": "Comprehensive analysis of financial markets using FinPsyMCP",
        "mcp_system": "finpsy",
        "workflow_type": "analysis",
        "workflow_data": {
            "steps": [
                {"agent": "finpsy_data_collector", "action": "collect_market_data"},
                {"agent": "finpsy_sentiment", "action": "analyze_sentiment"},
                {"agent": "finpsy_forecaster", "action": "forecast_trends"},
                {"agent": "finpsy_portfolio", "action": "optimize_portfolio"}
            ]
        }
    },
    {
        "name": "Workflow Automation Conversion",
        "description": "Convert n8n/Zapier workflows to Python using PydiniRed",
        "mcp_system": "pydini",
        "workflow_type": "automation",
        "workflow_data": {
            "steps": [
                {"agent": "pydini_adapter", "action": "parse_workflow"},
                {"agent": "pydini_generator", "action": "generate_python_code"},
                {"agent": "pydini_generator", "action": "package_for_deployment"}
            ]
        }
    },
    {
        "name": "Contract Review & Compliance",
        "description": "Legal analysis and compliance checking using LexMCP",
        "mcp_system": "lex",
        "workflow_type": "analysis",
        "workflow_data": {
            "steps": [
                {"agent": "lex_contract_analyzer", "action": "extract_clauses"},
                {"agent": "lex_contract_analyzer", "action": "identify_risks"},
                {"agent": "lex_compliance", "action": "check_compliance"}
            ]
        }
    }
]

try:
    conn = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password)
    cursor = conn.cursor()

    created_count = 0
    for wf in WORKFLOWS:
        try:
            # Check if workflow exists
            cursor.execute("SELECT id FROM workflow_templates WHERE name = %s", (wf["name"],))
            if cursor.fetchone():
                print(f"⏭️  Skipping '{wf['name']}' (already exists)")
                continue
            
            cursor.execute("""
                INSERT INTO workflow_templates (name, description, mcp_system, workflow_type, workflow_data, 
                                              template_json, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, true, %s);
            """, (wf["name"], wf["description"], wf["mcp_system"], wf["workflow_type"], 
                  json.dumps(wf["workflow_data"]), json.dumps(wf["workflow_data"]), datetime.now()))
            created_count += 1
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"⚠️  Could not create workflow '{wf['name']}': {e}")

    print(f"✅ Created {created_count} workflow templates")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"❌ Error creating workflows: {e}")
    sys.exit(1)
