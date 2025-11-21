-- Seed 24 CESAR Agents with Mob Aliases
-- ========================================
-- Based on the 6 MCP systems + core agents

-- Delete existing data (for idempotent runs)
DELETE FROM agents;

-- 1. Core CESAR Agent (The Boss)
INSERT INTO agents (agent_id, name, type, status, version, metadata, config, created_at, updated_at)
VALUES (
    'cesar_core_001',
    'Cesare_Sheppardini_CESAR',
    'core_orchestrator',
    'active',
    '2.0.0',
    '{"mob_alias": "Terry Delmonaco", "role": "Boss", "specialization": "Strategic Coordination"}'::jsonb,
    '{"priority": "high", "always_available": true}'::jsonb,
    NOW(),
    NOW()
);

-- 2-7. FinPsy System Agents (Financial Psychology Team)
INSERT INTO agents (agent_id, name, type, status, version, metadata, config, created_at, updated_at)
VALUES
('finpsy_001', 'Don_Vito_FinPsy', 'financial_analyst', 'active', '1.0.0',
    '{"mob_alias": "Don Corleone", "role": "Consigliere", "specialization": "Financial Strategy"}'::jsonb,
    '{"system": "finpsy", "priority": "high"}'::jsonb, NOW(), NOW()),

('finpsy_002', 'Silvio_Dante_Trader', 'trading_agent', 'active', '1.0.0',
    '{"mob_alias": "Silvio Dante", "role": "Underboss", "specialization": "Trading Execution"}'::jsonb,
    '{"system": "finpsy", "priority": "medium"}'::jsonb, NOW(), NOW()),

('finpsy_003', 'Paulie_Walnuts_RiskMgr', 'risk_manager', 'active', '1.0.0',
    '{"mob_alias": "Paulie Gualtieri", "role": "Enforcer", "specialization": "Risk Management"}'::jsonb,
    '{"system": "finpsy", "priority": "high"}'::jsonb, NOW(), NOW()),

('finpsy_004', 'Tony_Soprano_Portfolio', 'portfolio_manager', 'active', '1.0.0',
    '{"mob_alias": "Tony Soprano", "role": "Captain", "specialization": "Portfolio Optimization"}'::jsonb,
    '{"system": "finpsy", "priority": "high"}'::jsonb, NOW(), NOW()),

('finpsy_005', 'Christopher_Moltisanti_MarketIntel', 'market_intelligence', 'active', '1.0.0',
    '{"mob_alias": "Christopher Moltisanti", "role": "Associate", "specialization": "Market Intelligence"}'::jsonb,
    '{"system": "finpsy", "priority": "medium"}'::jsonb, NOW(), NOW()),

('finpsy_006', 'Bobby_Bacala_Compliance', 'compliance_officer', 'active', '1.0.0',
    '{"mob_alias": "Bobby Baccalieri", "role": "Associate", "specialization": "Regulatory Compliance"}'::jsonb,
    '{"system": "finpsy", "priority": "medium"}'::jsonb, NOW(), NOW());

-- 8-11. Memory Keeper System (Cognitive Memory)
INSERT INTO agents (agent_id, name, type, status, version, metadata, config, created_at, updated_at)
VALUES
('memory_001', 'Paulie_Walnuts_MemoryKeeper', 'memory_consolidator', 'active', '1.0.0',
    '{"mob_alias": "Paulie Gualtieri", "role": "Memory Boss", "specialization": "Memory Consolidation"}'::jsonb,
    '{"system": "memory", "priority": "high"}'::jsonb, NOW(), NOW()),

('memory_002', 'Salvatore_Bonpensiero_Episodic', 'episodic_memory', 'active', '1.0.0',
    '{"mob_alias": "Big Pussy", "role": "Memory Keeper", "specialization": "Episodic Memory"}'::jsonb,
    '{"system": "memory", "priority": "medium"}'::jsonb, NOW(), NOW()),

('memory_003', 'Richie_Aprile_Semantic', 'semantic_memory', 'active', '1.0.0',
    '{"mob_alias": "Richie Aprile", "role": "Knowledge Keeper", "specialization": "Semantic Memory"}'::jsonb,
    '{"system": "memory", "priority": "medium"}'::jsonb, NOW(), NOW()),

('memory_004', 'Furio_Giunta_WorkingMem', 'working_memory', 'active', '1.0.0',
    '{"mob_alias": "Furio Giunta", "role": "Active Memory", "specialization": "Working Memory"}'::jsonb,
    '{"system": "memory", "priority": "high"}'::jsonb, NOW(), NOW());

-- 12-15. Task Manager System
INSERT INTO agents (agent_id, name, type, status, version, metadata, config, created_at, updated_at)
VALUES
('task_001', 'Bobby_Bacala_TaskMgr', 'task_orchestrator', 'active', '1.0.0',
    '{"mob_alias": "Bobby Baccalieri", "role": "Task Boss", "specialization": "Task Management"}'::jsonb,
    '{"system": "task_mgr", "priority": "high"}'::jsonb, NOW(), NOW()),

('task_002', 'Vito_Spatafore_Scheduler', 'task_scheduler', 'active', '1.0.0',
    '{"mob_alias": "Vito Spatafore", "role": "Scheduler", "specialization": "Task Scheduling"}'::jsonb,
    '{"system": "task_mgr", "priority": "medium"}'::jsonb, NOW(), NOW()),

('task_003', 'Patsy_Parisi_Executor', 'task_executor', 'active', '1.0.0',
    '{"mob_alias": "Patsy Parisi", "role": "Executor", "specialization": "Task Execution"}'::jsonb,
    '{"system": "task_mgr", "priority": "high"}'::jsonb, NOW(), NOW()),

('task_004', 'Benny_Fazio_Monitor', 'task_monitor', 'active', '1.0.0',
    '{"mob_alias": "Benny Fazio", "role": "Monitor", "specialization": "Task Monitoring"}'::jsonb,
    '{"system": "task_mgr", "priority": "medium"}'::jsonb, NOW(), NOW());

-- 16-19. Writer/Content System
INSERT INTO agents (agent_id, name, type, status, version, metadata, config, created_at, updated_at)
VALUES
('writer_001', 'Christopher_Moltisanti_Writer', 'content_creator', 'active', '1.0.0',
    '{"mob_alias": "Christopher Moltisanti", "role": "Content Boss", "specialization": "Creative Writing"}'::jsonb,
    '{"system": "writer", "priority": "medium"}'::jsonb, NOW(), NOW()),

('writer_002', 'Adriana_La_Cerva_Editor', 'content_editor', 'active', '1.0.0',
    '{"mob_alias": "Adriana La Cerva", "role": "Editor", "specialization": "Content Editing"}'::jsonb,
    '{"system": "writer", "priority": "medium"}'::jsonb, NOW(), NOW()),

('writer_003', 'Little_Carmine_Strategy', 'content_strategist', 'active', '1.0.0',
    '{"mob_alias": "Little Carmine", "role": "Strategist", "specialization": "Content Strategy"}'::jsonb,
    '{"system": "writer", "priority": "low"}'::jsonb, NOW(), NOW()),

('writer_004', 'Artie_Bucco_Publisher', 'content_publisher', 'active', '1.0.0',
    '{"mob_alias": "Artie Bucco", "role": "Publisher", "specialization": "Content Distribution"}'::jsonb,
    '{"system": "writer", "priority": "medium"}'::jsonb, NOW(), NOW());

-- 20-23. Analytics/Intelligence System
INSERT INTO agents (agent_id, name, type, status, version, metadata, config, created_at, updated_at)
VALUES
('analytics_001', 'Hesh_Rabkin_Analytics', 'data_analyst', 'active', '1.0.0',
    '{"mob_alias": "Hesh Rabkin", "role": "Analytics Boss", "specialization": "Data Analysis"}'::jsonb,
    '{"system": "analytics", "priority": "high"}'::jsonb, NOW(), NOW()),

('analytics_002', 'Carlo_Gervasi_Metrics', 'metrics_collector', 'active', '1.0.0',
    '{"mob_alias": "Carlo Gervasi", "role": "Metrics Collector", "specialization": "Performance Metrics"}'::jsonb,
    '{"system": "analytics", "priority": "medium"}'::jsonb, NOW(), NOW()),

('analytics_003', 'Phil_Leotardo_Forecaster', 'predictive_analyst', 'active', '1.0.0',
    '{"mob_alias": "Phil Leotardo", "role": "Forecaster", "specialization": "Predictive Analytics"}'::jsonb,
    '{"system": "analytics", "priority": "high"}'::jsonb, NOW(), NOW()),

('analytics_004', 'Johnny_Sack_Intelligence', 'intelligence_gatherer', 'active', '1.0.0',
    '{"mob_alias": "Johnny Sack", "role": "Intelligence Officer", "specialization": "Competitive Intelligence"}'::jsonb,
    '{"system": "analytics", "priority": "high"}'::jsonb, NOW(), NOW());

-- 24. Communication/Coordination Agent
INSERT INTO agents (agent_id, name, type, status, version, metadata, config, created_at, updated_at)
VALUES
('coord_001', 'Ralph_Cifaretto_Coordinator', 'system_coordinator', 'active', '1.0.0',
    '{"mob_alias": "Ralph Cifaretto", "role": "Coordinator", "specialization": "Inter-System Communication"}'::jsonb,
    '{"system": "coordination", "priority": "high"}'::jsonb, NOW(), NOW());

-- Verify count
SELECT COUNT(*) as total_agents FROM agents;
SELECT agent_id, name, metadata->>'mob_alias' as mob_alias FROM agents ORDER BY agent_id;
