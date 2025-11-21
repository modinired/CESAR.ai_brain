import sys
sys.path.insert(0, '/app')

import psycopg2
from psycopg2.extras import Json
from datetime import datetime
import os
import json

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://mcp_user:password@postgres:5432/mcp')

import re
match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
if match:
    user, password, host, port, dbname = match.groups()
else:
    print("❌ Could not parse DATABASE_URL")
    sys.exit(1)

AGENTS = [
    {"agent_id": "finpsy_orchestrator", "name": "FinPsy Orchestrator", "type": "orchestrator", "mcp_system": "finpsy", "capabilities": ["financial_analysis", "portfolio_optimization", "risk_assessment"]},
    {"agent_id": "finpsy_data_collector", "name": "Data Collector", "type": "data", "mcp_system": "finpsy", "capabilities": ["yahoo_finance", "fred_api", "crypto_data"]},
    {"agent_id": "finpsy_sentiment", "name": "Sentiment Analyzer", "type": "analysis", "mcp_system": "finpsy", "capabilities": ["news_sentiment", "social_media", "market_fear_greed"]},
    {"agent_id": "finpsy_forecaster", "name": "Forecaster", "type": "prediction", "mcp_system": "finpsy", "capabilities": ["prophet", "arima", "time_series"]},
    {"agent_id": "finpsy_portfolio", "name": "Portfolio Optimizer", "type": "optimization", "mcp_system": "finpsy", "capabilities": ["mean_variance", "risk_parity", "black_litterman"]},
    {"agent_id": "pydini_orchestrator", "name": "PydiniRed Orchestrator", "type": "orchestrator", "mcp_system": "pydini", "capabilities": ["workflow_automation", "code_generation"]},
    {"agent_id": "pydini_adapter", "name": "Workflow Adapter", "type": "transformer", "mcp_system": "pydini", "capabilities": ["n8n_parser", "zapier_parser"]},
    {"agent_id": "pydini_generator", "name": "Code Generator", "type": "generator", "mcp_system": "pydini", "capabilities": ["python_generation", "docker_packaging"]},
    {"agent_id": "lex_orchestrator", "name": "Lex Orchestrator", "type": "orchestrator", "mcp_system": "lex", "capabilities": ["legal_analysis", "compliance_checking"]},
    {"agent_id": "lex_contract_analyzer", "name": "Contract Analyzer", "type": "analysis", "mcp_system": "lex", "capabilities": ["clause_extraction", "risk_identification"]},
    {"agent_id": "lex_compliance", "name": "Compliance Checker", "type": "validation", "mcp_system": "lex", "capabilities": ["regulatory_compliance"]},
    {"agent_id": "inno_orchestrator", "name": "Innovation Orchestrator", "type": "orchestrator", "mcp_system": "inno", "capabilities": ["patent_search", "innovation_tracking"]},
    {"agent_id": "inno_patent_search", "name": "Patent Search Agent", "type": "search", "mcp_system": "inno", "capabilities": ["patent_databases", "prior_art"]},
    {"agent_id": "inno_trend_analyzer", "name": "Trend Analyzer", "type": "analysis", "mcp_system": "inno", "capabilities": ["technology_trends"]},
    {"agent_id": "creative_orchestrator", "name": "Creative Orchestrator", "type": "orchestrator", "mcp_system": "creative", "capabilities": ["content_generation", "seo_optimization"]},
    {"agent_id": "creative_copywriter", "name": "Copywriter", "type": "generator", "mcp_system": "creative", "capabilities": ["marketing_copy", "ad_text"]},
    {"agent_id": "edu_orchestrator", "name": "Education Orchestrator", "type": "orchestrator", "mcp_system": "edu", "capabilities": ["curriculum_design", "adaptive_learning"]},
    {"agent_id": "edu_curriculum", "name": "Curriculum Designer", "type": "generator", "mcp_system": "edu", "capabilities": ["learning_paths"]},
    {"agent_id": "omnicognition", "name": "OmniCognition", "type": "orchestrator", "mcp_system": "omnicognition", "capabilities": ["advanced_reasoning", "meta_cognition"]},
    {"agent_id": "gambino_security", "name": "Gambino Security", "type": "orchestrator", "mcp_system": "security", "capabilities": ["threat_detection", "vulnerability_scanning"]},
    {"agent_id": "jules_protocol", "name": "Jules Protocol", "type": "orchestrator", "mcp_system": "protocol", "capabilities": ["api_integration", "protocol_translation"]},
    {"agent_id": "skillforge", "name": "SkillForge", "type": "orchestrator", "mcp_system": "skillforge", "capabilities": ["skill_discovery", "auto_deployment"]},
    {"agent_id": "central_orchestrator", "name": "Central Orchestrator", "type": "orchestrator", "mcp_system": "central", "capabilities": ["task_routing", "workflow_coordination"]},
]

try:
    conn = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password)
    cursor = conn.cursor()

    registered_count = 0
    for agent in AGENTS:
        try:
            cursor.execute("""
                INSERT INTO agents (agent_id, name, type, mcp_system, capabilities, status, created_at)
                VALUES (%s, %s, %s, %s, %s::jsonb, 'active', %s)
                ON CONFLICT (agent_id) DO UPDATE
                SET name = EXCLUDED.name, type = EXCLUDED.type, mcp_system = EXCLUDED.mcp_system,
                    capabilities = EXCLUDED.capabilities, status = 'active', updated_at = NOW();
            """, (agent["agent_id"], agent["name"], agent["type"], agent["mcp_system"], 
                  json.dumps(agent["capabilities"]), datetime.now()))
            registered_count += 1
        except Exception as e:
            conn.rollback()
            print(f"⚠️  {agent['agent_id']}: {e}")
            continue

    conn.commit()
    print(f"✅ Registered {registered_count} MCP agents")

    cursor.execute("SELECT mcp_system, COUNT(*) FROM agents WHERE mcp_system IS NOT NULL GROUP BY mcp_system ORDER BY mcp_system;")
    print("\n📊 Agent Distribution:")
    for row in cursor.fetchall():
        print(f"  • {row[0]}: {row[1]} agents")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
