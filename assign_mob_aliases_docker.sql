-- Assign mob aliases to all CESAR agents
-- Mob names from classic mafia films

-- CESAR (Central Orchestrator) - The Boss
UPDATE agents SET metadata = metadata || '{"mob_alias": "CESAR Sheppardini", "specialization": "Boss - Primary Orchestrator", "voice_mode": "third_person", "hierarchy_role": "boss"}'::jsonb WHERE agent_id = 'central_orchestrator';

-- FinPsy Orchestrator
UPDATE agents SET metadata = metadata || '{"mob_alias": "Paulie Gualtieri", "specialization": "Financial Psychology Coordination", "voice_mode": "third_person", "hierarchy_role": "specialist"}'::jsonb WHERE agent_id = 'finpsy_orchestrator';

-- Data Collector
UPDATE agents SET metadata = metadata || '{"mob_alias": "Christopher Moltisanti", "specialization": "Data Collection & Processing", "voice_mode": "third_person", "hierarchy_role": "specialist"}'::jsonb WHERE agent_id = 'finpsy_data_collector';

-- Sentiment Analyzer
UPDATE agents SET metadata = metadata || '{"mob_alias": "Silvio Dante", "specialization": "Sentiment Analysis & Intelligence", "voice_mode": "third_person", "hierarchy_role": "specialist"}'::jsonb WHERE agent_id = 'finpsy_sentiment';

-- Forecaster
UPDATE agents SET metadata = metadata || '{"mob_alias": "Bobby Baccalieri", "specialization": "Forecasting & Prediction", "voice_mode": "third_person", "hierarchy_role": "specialist"}'::jsonb WHERE agent_id = 'finpsy_forecaster';

-- Portfolio Optimizer
UPDATE agents SET metadata = metadata || '{"mob_alias": "Vito Spatafore", "specialization": "Portfolio Optimization & Strategy", "voice_mode": "third_person", "hierarchy_role": "specialist"}'::jsonb WHERE agent_id = 'finpsy_portfolio';

-- PydiniRed Orchestrator
UPDATE agents SET metadata = metadata || '{"mob_alias": "Ralph Cifaretto", "specialization": "Workflow Orchestration", "voice_mode": "third_person", "hierarchy_role": "specialist"}'::jsonb WHERE agent_id = 'pydini_orchestrator';

-- Workflow Adapter
UPDATE agents SET metadata = metadata || '{"mob_alias": "Richie Aprile", "specialization": "Workflow Transformation", "voice_mode": "third_person", "hierarchy_role": "specialist"}'::jsonb WHERE agent_id = 'pydini_adapter';

-- Code Generator
UPDATE agents SET metadata = metadata || '{"mob_alias": "Furio Giunta", "specialization": "Code Generation", "voice_mode": "third_person", "hierarchy_role": "specialist"}'::jsonb WHERE agent_id = 'pydini_generator';

-- Lex Orchestrator
UPDATE agents SET metadata = metadata || '{"mob_alias": "Jimmy Conway", "specialization": "Legal Analysis Coordination", "voice_mode": "third_person", "hierarchy_role": "specialist"}'::jsonb WHERE agent_id = 'lex_orchestrator';

-- Contract Analyzer
UPDATE agents SET metadata = metadata || '{"mob_alias": "Tommy DeVito", "specialization": "Contract Analysis & Intelligence", "voice_mode": "third_person", "hierarchy_role": "specialist"}'::jsonb WHERE agent_id = 'lex_contract_analyzer';

-- Compliance Checker
UPDATE agents SET metadata = metadata || '{"mob_alias": "Frankie Carbone", "specialization": "Compliance & Validation", "voice_mode": "third_person", "hierarchy_role": "specialist"}'::jsonb WHERE agent_id = 'lex_compliance';

-- Innovation Orchestrator
UPDATE agents SET metadata = metadata || '{"mob_alias": "Billy Batts", "specialization": "Innovation Coordination", "voice_mode": "third_person", "hierarchy_role": "specialist"}'::jsonb WHERE agent_id = 'inno_orchestrator';

-- Patent Search Agent
UPDATE agents SET metadata = metadata || '{"mob_alias": "Tuddy Cicero", "specialization": "Patent Information Retrieval", "voice_mode": "third_person", "hierarchy_role": "specialist"}'::jsonb WHERE agent_id = 'inno_patent_search';

-- Trend Analyzer
UPDATE agents SET metadata = metadata || '{"mob_alias": "Nicky Santoro", "specialization": "Trend Analysis & Intelligence", "voice_mode": "third_person", "hierarchy_role": "specialist"}'::jsonb WHERE agent_id = 'inno_trend_analyzer';

-- Creative Orchestrator
UPDATE agents SET metadata = metadata || '{"mob_alias": "Ace Rothstein", "specialization": "Creative Coordination", "voice_mode": "third_person", "hierarchy_role": "specialist"}'::jsonb WHERE agent_id = 'creative_orchestrator';

-- Copywriter
UPDATE agents SET metadata = metadata || '{"mob_alias": "Ginger McKenna", "specialization": "Content Generation", "voice_mode": "third_person", "hierarchy_role": "specialist"}'::jsonb WHERE agent_id = 'creative_copywriter';

-- Education Orchestrator
UPDATE agents SET metadata = metadata || '{"mob_alias": "Frankie Marino", "specialization": "Education Coordination", "voice_mode": "third_person", "hierarchy_role": "specialist"}'::jsonb WHERE agent_id = 'edu_orchestrator';

-- Curriculum Designer
UPDATE agents SET metadata = metadata || '{"mob_alias": "Luca Brasi", "specialization": "Curriculum Generation", "voice_mode": "third_person", "hierarchy_role": "specialist"}'::jsonb WHERE agent_id = 'edu_curriculum';

-- OmniCognition
UPDATE agents SET metadata = metadata || '{"mob_alias": "Pete Clemenza", "specialization": "Multi-Agent Cognition", "voice_mode": "third_person", "hierarchy_role": "specialist"}'::jsonb WHERE agent_id = 'omnicognition';

-- Gambino Security
UPDATE agents SET metadata = metadata || '{"mob_alias": "Sal Tessio", "specialization": "Security & Protection", "voice_mode": "third_person", "hierarchy_role": "specialist"}'::jsonb WHERE agent_id = 'gambino_security';

-- Jules Protocol
UPDATE agents SET metadata = metadata || '{"mob_alias": "Rocco Lampone", "specialization": "Protocol Management", "voice_mode": "third_person", "hierarchy_role": "specialist"}'::jsonb WHERE agent_id = 'jules_protocol';

-- SkillForge
UPDATE agents SET metadata = metadata || '{"mob_alias": "Al Neri", "specialization": "Skill Development", "voice_mode": "third_person", "hierarchy_role": "specialist"}'::jsonb WHERE agent_id = 'skillforge';

-- Email Agent
UPDATE agents SET metadata = metadata || '{"mob_alias": "Moe Greene", "specialization": "External Communication", "voice_mode": "third_person", "hierarchy_role": "specialist"}'::jsonb WHERE agent_id = 'email_agent';

-- Verify updates
SELECT agent_id, name, metadata->>'mob_alias' as mob_alias, metadata->>'specialization' as specialization
FROM agents
ORDER BY created_at;
