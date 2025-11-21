#!/usr/bin/env python3
"""
Seed Knowledge Enhancement System
Populates psychology, NLP, skills, and domain knowledge
"""

import asyncio
import json
import sys
from datetime import date, datetime
from uuid import UUID, uuid4

sys.path.insert(0, 'api')

async def seed_knowledge_system():
    from database_async import create_pool, get_db_connection, close_pool

    print("=" * 80)
    print("KNOWLEDGE ENHANCEMENT SYSTEM - SEEDING")
    print("=" * 80)
    print()

    await create_pool()

    async with get_db_connection() as conn:

        # ====================================================================
        # 1. KNOWLEDGE DOMAINS
        # ====================================================================
        print("1️⃣  Seeding Knowledge Domains...")

        domains = [
            # Core domains
            ('psychology', 'psychology', 'The scientific study of mind and behavior', None),
            ('nlp', 'nlp', 'Natural Language Processing and computational linguistics', None),
            ('cognitive_science', 'cognitive_science', 'Interdisciplinary study of mind and intelligence', None),
            ('neuroscience', 'neuroscience', 'Study of the nervous system and brain', None),
            ('machine_learning', 'technology', 'Algorithms that learn from data', None),
            ('business_strategy', 'business', 'Strategic planning and execution', None),
            ('financial_markets', 'finance', 'Trading, investment, and market analysis', None),

            # Psychology subdomains
            ('cognitive_psychology', 'psychology', 'Mental processes: memory, perception, thinking', 'psychology'),
            ('behavioral_psychology', 'psychology', 'Observable behavior and conditioning', 'psychology'),
            ('social_psychology', 'psychology', 'How people influence and relate to each other', 'psychology'),
            ('developmental_psychology', 'psychology', 'Psychological growth across lifespan', 'psychology'),
            ('clinical_psychology', 'psychology', 'Mental health assessment and treatment', 'psychology'),

            # NLP subdomains
            ('text_generation', 'nlp', 'Automated text creation and completion', 'nlp'),
            ('sentiment_analysis', 'nlp', 'Emotional tone detection in text', 'nlp'),
            ('named_entity_recognition', 'nlp', 'Identification of entities in text', 'nlp'),
            ('machine_translation', 'nlp', 'Automatic translation between languages', 'nlp'),
            ('question_answering', 'nlp', 'Systems that answer natural language questions', 'nlp'),

            # Cross-domain
            ('computational_psycholinguistics', 'cognitive_science', 'Computational models of language processing', 'cognitive_science'),
            ('affective_computing', 'technology', 'Computing that relates to emotions', 'cognitive_science'),
        ]

        domain_map = {}
        for name, category, desc, parent_name in domains:
            parent_id = domain_map.get(parent_name) if parent_name else None
            depth = 1 if parent_id else 0

            domain_id = await conn.fetchval('''
                INSERT INTO knowledge_domains (name, category, description, parent_domain_id, depth)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT DO NOTHING
                RETURNING domain_id
            ''', name, category, desc, parent_id, depth)

            if domain_id:
                domain_map[name] = domain_id

        print(f"   ✅ Seeded {len(domain_map)} knowledge domains")
        print()

        # ====================================================================
        # 2. SKILLS
        # ====================================================================
        print("2️⃣  Seeding Skills...")

        skills = [
            # Cognitive skills
            ('Critical Thinking', 'cognitive_psychology', 'cognitive', 'Analysis and evaluation of information'),
            ('Pattern Recognition', 'cognitive_psychology', 'cognitive', 'Identifying patterns in data'),
            ('Mental Models', 'cognitive_psychology', 'cognitive', 'Internal representations of how things work'),
            ('Metacognition', 'cognitive_psychology', 'cognitive', 'Thinking about thinking'),
            ('Working Memory Management', 'cognitive_psychology', 'cognitive', 'Managing information in active attention'),

            # Technical NLP skills
            ('Transformer Architecture', 'nlp', 'technical', 'Understanding and implementing transformers'),
            ('Attention Mechanisms', 'nlp', 'technical', 'Self-attention and cross-attention'),
            ('Prompt Engineering', 'nlp', 'technical', 'Crafting effective prompts for LLMs'),
            ('Fine-tuning LLMs', 'nlp', 'technical', 'Adapting pre-trained models'),
            ('RAG Systems', 'nlp', 'technical', 'Retrieval-Augmented Generation'),
            ('Tokenization', 'nlp', 'technical', 'Text-to-token conversion'),
            ('Embedding Generation', 'nlp', 'technical', 'Creating vector representations'),

            # Psychology application skills
            ('Cognitive Bias Recognition', 'cognitive_psychology', 'domain_knowledge', 'Identifying thinking biases'),
            ('Behavioral Design', 'behavioral_psychology', 'domain_knowledge', 'Designing for behavior change'),
            ('Social Influence Principles', 'social_psychology', 'domain_knowledge', 'Understanding persuasion'),
            ('Emotional Intelligence', 'social_psychology', 'interpersonal', 'Understanding and managing emotions'),

            # Business & Strategy
            ('Strategic Thinking', 'business_strategy', 'cognitive', 'Long-term planning and positioning'),
            ('Market Analysis', 'financial_markets', 'domain_knowledge', 'Analyzing market trends'),
            ('Decision Making Under Uncertainty', 'business_strategy', 'cognitive', 'Making decisions with incomplete information'),

            # ML & AI
            ('Model Evaluation', 'machine_learning', 'technical', 'Assessing model performance'),
            ('Feature Engineering', 'machine_learning', 'technical', 'Creating predictive features'),
            ('Hyperparameter Tuning', 'machine_learning', 'technical', 'Optimizing model configuration'),
        ]

        skill_map = {}
        for name, domain_name, skill_type, desc in skills:
            domain_id = domain_map.get(domain_name)
            skill_id = await conn.fetchval('''
                INSERT INTO skills (name, domain_id, skill_type, metadata)
                VALUES ($1, $2, $3, $4::jsonb)
                ON CONFLICT (name) DO UPDATE SET
                    domain_id = EXCLUDED.domain_id,
                    skill_type = EXCLUDED.skill_type
                RETURNING skill_id
            ''', name, domain_id, skill_type, json.dumps({'description': desc}))

            skill_map[name] = skill_id

        print(f"   ✅ Seeded {len(skill_map)} skills")
        print()

        # ====================================================================
        # 3. SKILL CONNECTIONS
        # ====================================================================
        print("3️⃣  Seeding Skill Connections...")

        connections = [
            # Prerequisites
            ('Transformer Architecture', 'Attention Mechanisms', 'prerequisite', 0.9),
            ('Fine-tuning LLMs', 'Transformer Architecture', 'prerequisite', 0.8),
            ('RAG Systems', 'Embedding Generation', 'prerequisite', 0.85),
            ('Prompt Engineering', 'Transformer Architecture', 'prerequisite', 0.7),
            ('Metacognition', 'Critical Thinking', 'prerequisite', 0.75),

            # Complementary
            ('Prompt Engineering', 'Critical Thinking', 'complementary', 0.8),
            ('Cognitive Bias Recognition', 'Critical Thinking', 'complementary', 0.9),
            ('Behavioral Design', 'Social Influence Principles', 'complementary', 0.85),
            ('Strategic Thinking', 'Decision Making Under Uncertainty', 'complementary', 0.9),
            ('Pattern Recognition', 'Feature Engineering', 'complementary', 0.8),

            # Synergistic
            ('Emotional Intelligence', 'Social Influence Principles', 'synergistic', 0.9),
            ('Mental Models', 'Strategic Thinking', 'synergistic', 0.85),
            ('RAG Systems', 'Prompt Engineering', 'synergistic', 0.8),
            ('Metacognition', 'Working Memory Management', 'synergistic', 0.75),
        ]

        for from_skill, to_skill, conn_type, strength in connections:
            from_id = skill_map.get(from_skill)
            to_id = skill_map.get(to_skill)
            if from_id and to_id:
                await conn.execute('''
                    INSERT INTO skill_connections (from_skill_id, to_skill_id, connection_type, strength)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (from_skill_id, to_skill_id, connection_type) DO NOTHING
                ''', from_id, to_id, conn_type, strength)

        print(f"   ✅ Seeded {len(connections)} skill connections")
        print()

        # ====================================================================
        # 4. PSYCHOLOGICAL CONCEPTS
        # ====================================================================
        print("4️⃣  Seeding Psychological Concepts...")

        psych_concepts = [
            ('Working Memory', 'cognitive', 'Baddeley & Hitch', 'Temporary storage and manipulation of information'),
            ('Cognitive Load Theory', 'cognitive', 'John Sweller', 'Limits on working memory capacity during learning'),
            ('Dual Process Theory', 'cognitive', 'Daniel Kahneman', 'System 1 (fast, intuitive) vs System 2 (slow, deliberate)'),
            ('Confirmation Bias', 'cognitive', 'Peter Wason', 'Tendency to seek information confirming existing beliefs'),
            ('Anchoring Effect', 'cognitive', 'Tversky & Kahneman', 'Over-reliance on first piece of information'),

            ('Classical Conditioning', 'behavioral', 'Ivan Pavlov', 'Learning through association'),
            ('Operant Conditioning', 'behavioral', 'B.F. Skinner', 'Learning through consequences'),
            ('Reinforcement Learning', 'behavioral', 'Edward Thorndike', 'Behavior strengthened by rewards'),

            ('Social Proof', 'social', 'Robert Cialdini', 'People follow the actions of others'),
            ('Cognitive Dissonance', 'social', 'Leon Festinger', 'Discomfort from conflicting beliefs'),
            ('Attribution Theory', 'social', 'Fritz Heider', 'How people explain causes of behavior'),
            ('Group Polarization', 'social', 'James Stoner', 'Groups make more extreme decisions'),

            ('Flow State', 'developmental', 'Mihaly Csikszentmihalyi', 'Optimal experience of deep engagement'),
            ('Growth Mindset', 'developmental', 'Carol Dweck', 'Belief that abilities can be developed'),
            ('Deliberate Practice', 'developmental', 'K. Anders Ericsson', 'Focused practice with feedback'),
        ]

        concept_map = {}
        for name, category, researcher, desc in psych_concepts:
            concept_id = await conn.fetchval('''
                INSERT INTO psychological_concepts (
                    name, category, theory_origin, description,
                    key_researchers, evidence_strength
                )
                VALUES ($1, $2, $3, $4, $5::jsonb, 'strong')
                ON CONFLICT (name) DO UPDATE SET
                    category = EXCLUDED.category
                RETURNING concept_id
            ''', name, category, researcher, desc, json.dumps([researcher]))

            concept_map[name] = concept_id

        print(f"   ✅ Seeded {len(concept_map)} psychological concepts")
        print()

        # ====================================================================
        # 5. NLP TECHNIQUES
        # ====================================================================
        print("5️⃣  Seeding NLP Techniques...")

        nlp_techniques = [
            ('Transformer', 'architecture', 'neural', 'Attention-based sequence modeling'),
            ('BERT', 'pre-training', 'neural', 'Bidirectional encoder representations'),
            ('GPT', 'pre-training', 'neural', 'Generative pre-trained transformer'),
            ('T5', 'pre-training', 'neural', 'Text-to-text transfer transformer'),
            ('Self-Attention', 'attention', 'neural', 'Attention over input sequence'),
            ('Cross-Attention', 'attention', 'neural', 'Attention between two sequences'),

            ('Byte-Pair Encoding', 'tokenization', 'statistical', 'Subword tokenization algorithm'),
            ('WordPiece', 'tokenization', 'statistical', 'Google\'s subword tokenization'),
            ('SentencePiece', 'tokenization', 'statistical', 'Unsupervised tokenization'),

            ('Word2Vec', 'embedding', 'neural', 'Word embeddings via shallow networks'),
            ('GloVe', 'embedding', 'statistical', 'Global vectors for word representation'),
            ('Sentence-BERT', 'embedding', 'neural', 'Sentence-level embeddings'),

            ('Beam Search', 'generation', 'symbolic', 'Heuristic search for best sequences'),
            ('Nucleus Sampling', 'generation', 'statistical', 'Top-p sampling for generation'),
            ('Temperature Scaling', 'generation', 'statistical', 'Controlling randomness in generation'),

            ('Named Entity Recognition', 'extraction', 'hybrid', 'Identifying entities in text'),
            ('Relation Extraction', 'extraction', 'hybrid', 'Finding relationships between entities'),
            ('Coreference Resolution', 'extraction', 'hybrid', 'Linking mentions to same entity'),
        ]

        technique_map = {}
        for name, category, approach, desc in nlp_techniques:
            technique_id = await conn.fetchval('''
                INSERT INTO nlp_techniques (name, category, approach, metadata)
                VALUES ($1, $2, $3, $4::jsonb)
                ON CONFLICT (name) DO UPDATE SET
                    category = EXCLUDED.category
                RETURNING technique_id
            ''', name, category, approach, json.dumps({'description': desc}))

            technique_map[name] = technique_id

        print(f"   ✅ Seeded {len(technique_map)} NLP techniques")
        print()

        # ====================================================================
        # 6. PSYCHOLOGY-NLP BRIDGES
        # ====================================================================
        print("6️⃣  Seeding Psychology-NLP Bridges...")

        bridges = [
            ('Working Memory', 'Transformer', 'models', 'Transformers model working memory via attention', 0.8),
            ('Cognitive Load Theory', 'Prompt Engineering', 'applies_to', 'Prompts should manage cognitive load', 0.85),
            ('Confirmation Bias', 'BERT', 'inspired_by', 'BERT masks tokens to avoid confirmation in training', 0.6),
            ('Classical Conditioning', 'Reinforcement Learning', 'implements', 'RL implements conditioning principles', 0.9),
            ('Social Proof', 'Sentiment Analysis', 'applies_to', 'Detecting social influence in text', 0.7),
            ('Flow State', 'Temperature Scaling', 'models', 'Temperature controls "flow" of generation', 0.5),
            ('Deliberate Practice', 'Fine-tuning LLMs', 'applies_to', 'Fine-tuning is deliberate practice for models', 0.75),
            ('Attribution Theory', 'Relation Extraction', 'models', 'Extracting causal relationships', 0.7),
        ]

        for concept_name, technique_name, conn_type, desc, strength in bridges:
            concept_id = concept_map.get(concept_name)
            technique_id = technique_map.get(technique_name)
            if concept_id and technique_id:
                await conn.execute('''
                    INSERT INTO psychology_nlp_bridges (
                        psychological_concept_id, nlp_technique_id,
                        connection_type, description, strength
                    )
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT DO NOTHING
                ''', concept_id, technique_id, conn_type, desc, strength)

        print(f"   ✅ Seeded {len(bridges)} psychology-NLP bridges")
        print()

        # ====================================================================
        # 7. EXCELLENCE PATTERNS
        # ====================================================================
        print("7️⃣  Seeding Excellence Patterns...")

        excellence_patterns = [
            ('First Principles Thinking', 'mental_model', 'business_strategy',
             'Break down problems to fundamental truths and rebuild',
             ['Question assumptions', 'Identify core truths', 'Build from ground up'], 0.95),

            ('Compound Learning', 'framework', 'cognitive_psychology',
             'Build knowledge incrementally with spaced repetition',
             ['Start small', 'Add daily', 'Review regularly', 'Connect concepts'], 0.9),

            ('Deliberate Practice Framework', 'technique', 'cognitive_psychology',
             'Focused, feedback-driven skill development',
             ['Set specific goals', 'Get immediate feedback', 'Focus on weaknesses'], 0.95),

            ('Pre-mortem Analysis', 'technique', 'business_strategy',
             'Imagine failure and work backwards to prevent it',
             ['Assume project failed', 'List reasons', 'Address proactively'], 0.85),

            ('Retrieval Practice', 'technique', 'cognitive_psychology',
             'Test yourself instead of rereading',
             ['Active recall', 'Spaced testing', 'Interleaved practice'], 0.9),

            ('Feynman Technique', 'technique', 'cognitive_psychology',
             'Explain concepts simply to reveal gaps',
             ['Teach concept simply', 'Identify gaps', 'Review and simplify'], 0.88),

            ('Systems Thinking', 'mental_model', 'business_strategy',
             'Understand interconnections and feedback loops',
             ['Map relationships', 'Find leverage points', 'Consider 2nd order effects'], 0.92),

            ('Prompt Chain-of-Thought', 'technique', 'nlp',
             'Guide LLMs through reasoning steps',
             ['Break down problem', 'Request step-by-step', 'Verify each step'], 0.87),

            ('RAG + Prompt Optimization', 'workflow', 'nlp',
             'Combine retrieval with optimized prompts',
             ['Index quality sources', 'Semantic search', 'Context injection', 'Verify facts'], 0.9),
        ]

        pattern_map = {}
        for name, category, domain_name, desc, principles, rating in excellence_patterns:
            domain_id = domain_map.get(domain_name)
            pattern_id = await conn.fetchval('''
                INSERT INTO excellence_patterns (
                    name, category, domain_id, description,
                    key_principles, effectiveness_rating
                )
                VALUES ($1, $2, $3, $4, $5::jsonb, $6)
                ON CONFLICT DO NOTHING
                RETURNING pattern_id
            ''', name, category, domain_id, desc, json.dumps(principles), rating)

            if pattern_id:
                pattern_map[name] = pattern_id

        print(f"   ✅ Seeded {len(pattern_map)} excellence patterns")
        print()

        # ====================================================================
        # 8. UNCONVENTIONAL INSIGHTS
        # ====================================================================
        print("8️⃣  Seeding Unconventional Insights...")

        insights = [
            ('Constraints Boost Creativity', 'counter_intuitive',
             'Limited resources force innovative solutions',
             'More freedom leads to better outcomes',
             'Studies show constraints enhance creative problem-solving', 0.85),

            ('Forgetting Enhances Learning', 'counter_intuitive',
             'Strategic forgetting strengthens long-term memory',
             'Constant review is best for retention',
             'Spacing effect and testing effect research', 0.9),

            ('Slower is Faster', 'counter_intuitive',
             'Deliberate speed beats rushed execution',
             'Working faster produces better results',
             'Quality-first approaches reduce rework', 0.88),

            ('Teach to Learn', 'cross_domain',
             'Teaching others solidifies your own understanding',
             'Learn by consuming information',
             'Protégé effect and Feynman technique', 0.92),

            ('AI Amplifies Human Biases', 'emerging',
             'ML models inherit and amplify training data biases',
             'AI is objective and unbiased',
             'Bias in AI systems research', 0.95),

            ('Attention is All You Need', 'contrarian',
             'Recurrence and convolution not necessary for NLP',
             'RNNs/CNNs required for sequence modeling',
             'Transformer architecture success', 0.98),
        ]

        for title, insight_type, desc, conventional, evidence, impact in insights:
            await conn.execute('''
                INSERT INTO unconventional_insights (
                    title, insight_type, description,
                    conventional_wisdom, supporting_evidence,
                    impact_potential, validation_status
                )
                VALUES ($1, $2, $3, $4, $5::jsonb, $6, 'validated')
                ON CONFLICT DO NOTHING
            ''', title, insight_type, desc, conventional, json.dumps([evidence]), impact)

        print(f"   ✅ Seeded {len(insights)} unconventional insights")
        print()

        # ====================================================================
        # 9. SAMPLE DAILY LEARNINGS
        # ====================================================================
        print("9️⃣  Seeding Sample Daily Learnings...")

        today = date.today()

        # Sample learnings
        sample_learnings = [
            (today, 'insight', 'Prompt Engineering', 'Critical Thinking',
             'Chain-of-Thought dramatically improves reasoning', 'Discovered that explicitly asking for step-by-step reasoning improves accuracy by 40%', 0.9, 0.85),

            (today, 'skill_improvement', 'cognitive_psychology', 'Metacognition',
             'Improved metacognitive monitoring', 'Practiced thinking about my thinking processes during problem-solving', 0.75, 0.8),

            (today, 'connection', 'cognitive_psychology', 'Working Memory Management',
             'Working memory limits affect prompt design', 'Realized that chunking information in prompts respects LLM context window like working memory', 0.85, 0.9),

            (today, 'breakthrough', 'nlp', 'RAG Systems',
             'Semantic chunking beats fixed-size chunks', 'Tested semantic chunking vs fixed 512 tokens - 25% better retrieval', 0.95, 0.9),

            (today, 'pattern', 'business_strategy', 'Strategic Thinking',
             'Compound small wins outperform big bets', 'Consistent daily improvements compound faster than quarterly initiatives', 0.8, 0.85),
        ]

        for learning_date, learning_type, domain_name, skill_name, title, desc, importance, confidence in sample_learnings:
            domain_id = domain_map.get(domain_name)
            skill_id = skill_map.get(skill_name)

            await conn.execute('''
                INSERT INTO daily_learnings (
                    date, learning_type, domain_id, skill_id,
                    title, description, importance_score, confidence_level
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT DO NOTHING
            ''', learning_date, learning_type, domain_id, skill_id, title, desc, importance, confidence)

        print(f"   ✅ Seeded {len(sample_learnings)} daily learnings for {today}")
        print()

        # ====================================================================
        # 10. GENERATE DAILY SUMMARY (Manual - function not supported in CockroachDB)
        # ====================================================================
        print("🔟 Generating Daily Learning Summary...")

        # Manually create summary since function doesn't work in CockroachDB
        v_learnings = await conn.fetchval('''
            SELECT JSONB_AGG(
                JSONB_BUILD_OBJECT(
                    'title', title,
                    'type', learning_type,
                    'importance', importance_score,
                    'description', description
                )
                ORDER BY importance_score DESC
            )
            FROM (
                SELECT * FROM daily_learnings
                WHERE date = $1
                ORDER BY importance_score DESC
                LIMIT 10
            ) top_learnings
        ''', today)

        summary_id = await conn.fetchval('''
            INSERT INTO daily_learning_summary (
                date, total_learnings, top_learnings, overall_progress_score
            )
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (date) DO UPDATE SET
                total_learnings = EXCLUDED.total_learnings,
                top_learnings = EXCLUDED.top_learnings,
                overall_progress_score = EXCLUDED.overall_progress_score,
                updated_at = now()
            RETURNING summary_id
        ''', today,
            await conn.fetchval('SELECT COUNT(*) FROM daily_learnings WHERE date = $1', today),
            v_learnings or '[]',
            await conn.fetchval('SELECT AVG(importance_score) FROM daily_learnings WHERE date = $1', today) or 0.0
        )

        print(f"   ✅ Generated summary: {summary_id}")
        print()

        # ====================================================================
        # 11. SKIP MATERIALIZED VIEW REFRESH (Not supported in CockroachDB functions)
        # ====================================================================
        print("1️⃣1️⃣  Skipping materialized view refresh (will refresh on first query)")
        print()

    await close_pool()

    # ====================================================================
    # FINAL SUMMARY
    # ====================================================================
    print("=" * 80)
    print("✅ KNOWLEDGE ENHANCEMENT SYSTEM SEEDED SUCCESSFULLY!")
    print("=" * 80)
    print()
    print("Seeded:")
    print(f"  • {len(domain_map)} knowledge domains")
    print(f"  • {len(skill_map)} skills")
    print(f"  • {len(connections)} skill connections")
    print(f"  • {len(concept_map)} psychological concepts")
    print(f"  • {len(technique_map)} NLP techniques")
    print(f"  • {len(bridges)} psychology-NLP bridges")
    print(f"  • {len(pattern_map)} excellence patterns")
    print(f"  • {len(insights)} unconventional insights")
    print(f"  • {len(sample_learnings)} daily learnings")
    print()
    print("🚀 System ready for best-in-class knowledge integration!")
    print()

if __name__ == "__main__":
    asyncio.run(seed_knowledge_system())
