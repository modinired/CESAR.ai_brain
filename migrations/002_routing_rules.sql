-- Populate routing rules for all 23 agents
-- Maps agents to optimal LLMs and tools based on capabilities

-- Analysis Agents (need strong reasoning)
INSERT INTO routing_rules (name, priority, task_tags, preferred_llm) VALUES
('Contract Analysis Route', 10, ARRAY['legal', 'contract', 'clause_extraction', 'risk_identification'],
 (SELECT id FROM llms WHERE name = 'Claude Sonnet 4.5')),
('Sentiment Analysis Route', 20, ARRAY['sentiment', 'news', 'social_media', 'market_analysis'],
 (SELECT id FROM llms WHERE name = 'GPT-4o')),
('Trend Analysis Route', 30, ARRAY['trends', 'technology', 'innovation'],
 (SELECT id FROM llms WHERE name = 'GPT-4o'));

-- Data Agents (fast, efficient)
INSERT INTO routing_rules (name, priority, task_tags, preferred_llm) VALUES
('Data Collection Route', 40, ARRAY['data_collection', 'yahoo_finance', 'fred_api', 'crypto'],
 (SELECT id FROM llms WHERE name = 'GPT-4o-mini'));

-- Generator Agents (creative/code generation)
INSERT INTO routing_rules (name, priority, task_tags, preferred_llm) VALUES
('Code Generation Route', 50, ARRAY['code', 'python', 'docker', 'generation'],
 (SELECT id FROM llms WHERE name = 'Claude Sonnet 4.5')),
('Creative Writing Route', 60, ARRAY['copywriting', 'marketing', 'advertising', 'creative'],
 (SELECT id FROM llms WHERE name = 'GPT-4o')),
('Curriculum Design Route', 70, ARRAY['education', 'curriculum', 'learning_paths'],
 (SELECT id FROM llms WHERE name = 'GPT-4o'));

-- Optimization Agents (mathematical/analytical)
INSERT INTO routing_rules (name, priority, task_tags, preferred_llm) VALUES
('Portfolio Optimization Route', 80, ARRAY['portfolio', 'optimization', 'risk_parity', 'mean_variance'],
 (SELECT id FROM llms WHERE name = 'Claude Sonnet 4.5'));

-- Orchestrator Agents (coordination and reasoning)
INSERT INTO routing_rules (name, priority, task_tags, preferred_llm) VALUES
('Central Orchestration Route', 90, ARRAY['orchestration', 'task_routing', 'workflow_coordination'],
 (SELECT id FROM llms WHERE name = 'Claude Sonnet 4.5')),
('Creative Orchestration Route', 100, ARRAY['creative_orchestration', 'content_generation', 'seo'],
 (SELECT id FROM llms WHERE name = 'GPT-4o')),
('Education Orchestration Route', 110, ARRAY['edu_orchestration', 'adaptive_learning', 'curriculum'],
 (SELECT id FROM llms WHERE name = 'GPT-4o')),
('Financial Orchestration Route', 120, ARRAY['financial_orchestration', 'portfolio', 'risk_assessment'],
 (SELECT id FROM llms WHERE name = 'Claude Sonnet 4.5')),
('Security Orchestration Route', 130, ARRAY['security', 'threat_detection', 'vulnerability_scanning'],
 (SELECT id FROM llms WHERE name = 'GPT-4o')),
('Innovation Orchestration Route', 140, ARRAY['innovation', 'patent_search', 'innovation_tracking'],
 (SELECT id FROM llms WHERE name = 'GPT-4o')),
('Protocol Orchestration Route', 150, ARRAY['protocol', 'api_integration', 'protocol_translation'],
 (SELECT id FROM llms WHERE name = 'Claude Haiku 3.5')),
('Legal Orchestration Route', 160, ARRAY['legal_orchestration', 'legal_analysis', 'compliance'],
 (SELECT id FROM llms WHERE name = 'Claude Sonnet 4.5')),
('Meta Cognition Route', 170, ARRAY['meta_cognition', 'advanced_reasoning', 'omnicognition'],
 (SELECT id FROM llms WHERE name = 'Claude Sonnet 4.5')),
('Workflow Automation Route', 180, ARRAY['workflow_automation', 'code_generation', 'automation'],
 (SELECT id FROM llms WHERE name = 'Claude Sonnet 4.5')),
('Skill Discovery Route', 190, ARRAY['skill_discovery', 'auto_deployment', 'skillforge'],
 (SELECT id FROM llms WHERE name = 'GPT-4o'));

-- Prediction Agents (statistical/ML)
INSERT INTO routing_rules (name, priority, task_tags, preferred_llm) VALUES
('Forecasting Route', 200, ARRAY['forecasting', 'prophet', 'arima', 'time_series'],
 (SELECT id FROM llms WHERE name = 'Claude Sonnet 4.5'));

-- Search Agents (fast retrieval)
INSERT INTO routing_rules (name, priority, task_tags, preferred_llm) VALUES
('Patent Search Route', 210, ARRAY['patent_search', 'patent_databases', 'prior_art'],
 (SELECT id FROM llms WHERE name = 'GPT-4o-mini'));

-- Transformer Agents (parsing/conversion)
INSERT INTO routing_rules (name, priority, task_tags, preferred_llm) VALUES
('Workflow Transformation Route', 220, ARRAY['transformation', 'n8n_parser', 'zapier_parser'],
 (SELECT id FROM llms WHERE name = 'Claude Haiku 3.5'));

-- Validation Agents (compliance/rules)
INSERT INTO routing_rules (name, priority, task_tags, preferred_llm) VALUES
('Compliance Validation Route', 230, ARRAY['compliance', 'regulatory_compliance', 'validation'],
 (SELECT id FROM llms WHERE name = 'Claude Sonnet 4.5'));

-- Catch-all fallback rule (lowest priority)
INSERT INTO routing_rules (name, priority, task_tags, preferred_llm) VALUES
('Default Route', 999, ARRAY[]::text[],
 (SELECT id FROM llms WHERE name = 'Claude Haiku 3.5'));
