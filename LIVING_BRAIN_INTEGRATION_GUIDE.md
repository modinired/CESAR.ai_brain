# 🧠 Living Brain Integration Guide - CESAR Ecosystem

**Date:** November 21, 2025
**Purpose:** Finalize living brain update with knowledge enhancement system
**Atlas Prime Port:** 8011

---

## 🎯 Current Living Brain Status

### ✅ Already Implemented:
1. **Optic Nerve Dedupe** - Vision processing checks tenant+label before creating nodes
2. **Agent Self-Reflection** - POST `/atlas/agents/{agent_id}/self_reflection` (one per day)
3. **Weekly 1:1 Scheduling** - POST `/atlas/agents/{agent_id}/one_on_one` (upserts per agent/user/week)
4. **New Tables**:
   - `agent_self_reflections`
   - `agent_one_on_one`

### 🆕 Knowledge Enhancement Addition:
- **13 new tables** for comprehensive knowledge tracking
- **15+ psychology concepts**
- **18+ NLP techniques**
- **20+ skills with connections**
- **Daily learning summaries**
- **Excellence patterns & unconventional insights**

---

## 🔗 Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LIVING BRAIN                              │
│  (Atlas Prime - Port 8011)                                   │
└──────────────────┬──────────────────────────────────────────┘
                   │
    ┌──────────────┼──────────────┬────────────────────┐
    │              │              │                    │
    ▼              ▼              ▼                    ▼
┌──────────┐  ┌──────────┐  ┌──────────┐      ┌──────────────┐
│  Optic   │  │  Self    │  │ Weekly   │      │  Knowledge   │
│  Nerve   │  │ Reflect  │  │  1:1s    │      │ Enhancement  │
└──────────┘  └──────────┘  └──────────┘      └──────────────┘
     │              │              │                    │
     │         Feeds into     Feeds into           Feeds into
     │              │              │                    │
     └──────────────┴──────────────┴────────────────────┘
                            │
                            ▼
                   ┌──────────────┐
                   │    DAILY     │
                   │  LEARNINGS   │
                   └──────────────┘
```

---

## 🔄 Data Flow Integration

### 1. Self-Reflection → Daily Learnings

```python
# When agent creates self-reflection
POST /atlas/agents/{agent_id}/self_reflection
{
  "reflection_content": "Today I improved contract analysis by..."
  "insights_gained": ["RAG improved accuracy 30%"]
}

# Automatically create daily_learning entry
INSERT INTO daily_learnings (
    date, agent_id, learning_type,
    title, description, importance_score
)
VALUES (
    CURRENT_DATE,
    '{agent_id}',
    'insight',
    'Contract analysis RAG improvement',
    'Adding legal precedent retrieval boosted accuracy 30%',
    0.85
);
```

### 2. Weekly 1:1 → Skills & Excellence Patterns

```python
# During 1:1, track skills discussed
POST /atlas/agents/{agent_id}/one_on_one
{
  "agenda": ["Review prompt engineering progress", "Discuss metacognition"],
  "user_id": "modini"
}

# Link to skills
SELECT skill_id FROM skills
WHERE name IN ('Prompt Engineering', 'Metacognition');

# Suggest excellence patterns
SELECT name, description, effectiveness_rating
FROM excellence_patterns
WHERE domain_id IN (SELECT domain_id FROM skills WHERE name IN (...))
ORDER BY effectiveness_rating DESC;
```

### 3. Optic Nerve → Knowledge Domains

```python
# When processing vision input
POST /atlas/optic-nerve
{
  "tenant": "modini",
  "label": "financial_chart",
  "description": "Stock market trends"
}

# Tag with domain
domain_id = await conn.fetchval(
    "SELECT domain_id FROM knowledge_domains WHERE name = 'financial_markets'"
);

# Track as learning activity
INSERT INTO learning_history (
    agent_id, domain_id, activity_type, content_type
)
VALUES ('portfolio_optimizer', domain_id, 'study', 'vision');
```

---

## 📝 New Atlas Prime Endpoints to Add

### 1. Knowledge Enhancement Endpoints

```python
# In atlas_prime.py

@router.get("/knowledge/daily-summary")
async def get_daily_summary(date: str = None, db=Depends(get_db)):
    """Get daily learning summary with top insights"""
    if not date:
        date = datetime.now().date()

    summary = await db.fetchrow('''
        SELECT * FROM daily_learning_summary
        WHERE date = $1
    ''', date)

    if not summary:
        # Generate on-demand
        await db.execute('SELECT generate_daily_learning_summary($1)', date)
        summary = await db.fetchrow(
            'SELECT * FROM daily_learning_summary WHERE date = $1', date
        )

    return summary

@router.get("/knowledge/trending-skills")
async def get_trending_skills(days: int = 7, db=Depends(get_db)):
    """Get trending skills from last N days"""
    # Refresh view if stale
    await db.execute('REFRESH MATERIALIZED VIEW mv_trending_skills')

    skills = await db.fetch('''
        SELECT * FROM mv_trending_skills
        LIMIT 20
    ''')
    return skills

@router.get("/knowledge/excellence-patterns")
async def get_excellence_patterns(min_effectiveness: float = 0.8, db=Depends(get_db)):
    """Get top excellence patterns"""
    patterns = await db.fetch('''
        SELECT * FROM mv_top_excellence_patterns
        WHERE effectiveness_rating >= $1
        LIMIT 10
    ''', min_effectiveness)
    return patterns

@router.get("/knowledge/psych-nlp-bridges")
async def get_psychology_nlp_bridges(min_strength: float = 0.7, db=Depends(get_db)):
    """Get psychology-NLP connections"""
    bridges = await db.fetch('''
        SELECT
            pc.name as psychology_concept,
            nt.name as nlp_technique,
            pnb.connection_type,
            pnb.description,
            pnb.strength
        FROM psychology_nlp_bridges pnb
        JOIN psychological_concepts pc ON pnb.psychological_concept_id = pc.concept_id
        JOIN nlp_techniques nt ON pnb.nlp_technique_id = nt.technique_id
        WHERE pnb.strength >= $1
        ORDER BY pnb.strength DESC
    ''', min_strength)
    return bridges

@router.post("/knowledge/log-learning")
async def log_learning_activity(
    agent_id: str,
    skill_name: str,
    activity_type: str,
    duration_minutes: int,
    insights: List[str],
    db=Depends(get_db)
):
    """Log learning activity for an agent"""
    skill_id = await db.fetchval(
        'SELECT skill_id FROM skills WHERE name = $1', skill_name
    )

    if not skill_id:
        raise HTTPException(404, f"Skill '{skill_name}' not found")

    await db.execute('''
        INSERT INTO learning_history (
            agent_id, skill_id, activity_type,
            duration_minutes, insights_gained
        )
        VALUES ($1, $2, $3, $4, $5::jsonb)
    ''', agent_id, skill_id, activity_type, duration_minutes, json.dumps(insights))

    return {"status": "success", "agent_id": agent_id, "skill": skill_name}
```

### 2. Enhanced Self-Reflection Endpoint

```python
@router.post("/atlas/agents/{agent_id}/self_reflection")
async def agent_self_reflection_enhanced(
    agent_id: str,
    reflection_content: str,
    insights_gained: List[str] = [],
    skills_practiced: List[str] = [],
    db=Depends(get_db)
):
    """Enhanced self-reflection that auto-creates daily learnings"""

    # 1. Store self-reflection (existing)
    reflection_id = await db.fetchval('''
        INSERT INTO agent_self_reflections (agent_id, reflection_content, reflection_date)
        VALUES ($1, $2, CURRENT_DATE)
        ON CONFLICT (agent_id, reflection_date) DO UPDATE
        SET reflection_content = EXCLUDED.reflection_content,
            updated_at = now()
        RETURNING reflection_id
    ''', agent_id, reflection_content)

    # 2. NEW: Create daily learnings for each insight
    for insight in insights_gained:
        await db.execute('''
            INSERT INTO daily_learnings (
                date, agent_id, learning_type,
                title, description, importance_score
            )
            VALUES (
                CURRENT_DATE, $1, 'insight',
                $2, $3, 0.7
            )
        ''', agent_id, insight[:100], insight)

    # 3. NEW: Log skill practice
    for skill_name in skills_practiced:
        skill_id = await db.fetchval(
            'SELECT skill_id FROM skills WHERE name = $1', skill_name
        )
        if skill_id:
            await db.execute('''
                INSERT INTO learning_history (
                    agent_id, skill_id, activity_type, timestamp
                )
                VALUES ($1, $2, 'reflection', now())
            ''', agent_id, skill_id)

    # 4. Generate daily summary if not exists
    summary_exists = await db.fetchval(
        'SELECT EXISTS(SELECT 1 FROM daily_learning_summary WHERE date = CURRENT_DATE)'
    )
    if not summary_exists:
        await db.execute('SELECT generate_daily_learning_summary(CURRENT_DATE)')

    return {
        "reflection_id": reflection_id,
        "insights_logged": len(insights_gained),
        "skills_tracked": len(skills_practiced)
    }
```

---

## ⚙️ Job Queue Integration

### Add to job queue worker:

```python
# In services/job_queue_worker.py

async def process_job(conn, job):
    job_type = job['job_type']

    if job_type == 'daily_learning_summary':
        # Generate daily summary
        await conn.execute('SELECT generate_daily_learning_summary(CURRENT_DATE)')

    elif job_type == 'refresh_knowledge_views':
        # Refresh materialized views
        await conn.execute('SELECT refresh_knowledge_enhancement_views()')

    elif job_type == 'weekly_learning_trends':
        # Aggregate weekly trends
        await conn.execute('''
            INSERT INTO learning_trends (
                aggregation_period, period_start, period_end,
                agent_id, skill_id, total_activities, avg_proficiency_gain
            )
            SELECT
                'weekly',
                date_trunc('week', timestamp)::date,
                (date_trunc('week', timestamp) + interval '6 days')::date,
                agent_id,
                skill_id,
                COUNT(*),
                AVG(proficiency_after - proficiency_before)
            FROM learning_history
            WHERE timestamp >= CURRENT_DATE - interval '7 days'
            GROUP BY agent_id, skill_id, date_trunc('week', timestamp)
            ON CONFLICT (aggregation_period, period_start, agent_id, skill_id)
            DO UPDATE SET
                total_activities = EXCLUDED.total_activities,
                avg_proficiency_gain = EXCLUDED.avg_proficiency_gain
        ''')

    # ... existing job types ...
```

### Schedule jobs:

```sql
-- Daily summary at 2 AM
INSERT INTO job_queue (job_type, payload, next_run_at, status)
VALUES ('daily_learning_summary', '{}', '2025-11-22 02:00:00', 'pending');

-- Refresh views every 6 hours
INSERT INTO job_queue (job_type, payload, next_run_at, status)
VALUES ('refresh_knowledge_views', '{}', '2025-11-21 18:00:00', 'pending');

-- Weekly trends on Sunday at 3 AM
INSERT INTO job_queue (job_type, payload, next_run_at, status)
VALUES ('weekly_learning_trends', '{}', '2025-11-24 03:00:00', 'pending');
```

---

## 🎨 Dashboard Widgets

### Widget 1: Daily Learning Highlights

```javascript
// curator-ui/src/components/DailyLearningHighlights.js

const DailyLearningHighlights = () => {
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    fetch('http://localhost:8011/knowledge/daily-summary')
      .then(res => res.json())
      .then(data => setSummary(data));
  }, []);

  if (!summary) return <Loading />;

  return (
    <Card title="Today's Key Learnings">
      <ProgressScore score={summary.overall_progress_score} />
      <h3>Top Insights:</h3>
      {summary.top_learnings.slice(0, 5).map(learning => (
        <InsightCard
          key={learning.title}
          title={learning.title}
          description={learning.description}
          importance={learning.importance}
        />
      ))}
      <Stats>
        <Stat label="Domains Explored" value={summary.domains_explored.length} />
        <Stat label="Skills Improved" value={summary.skills_improved.length} />
        <Stat label="Total Learnings" value={summary.total_learnings} />
      </Stats>
    </Card>
  );
};
```

### Widget 2: Trending Skills

```javascript
// curator-ui/src/components/TrendingSkills.js

const TrendingSkills = () => {
  const [skills, setSkills] = useState([]);

  useEffect(() => {
    fetch('http://localhost:8011/knowledge/trending-skills')
      .then(res => res.json())
      .then(data => setSkills(data));
  }, []);

  return (
    <Card title="Trending Skills (Last 7 Days)">
      {skills.map(skill => (
        <SkillRow key={skill.skill_id}>
          <SkillName>{skill.skill_name}</SkillName>
          <Domain>{skill.domain_name}</Domain>
          <Metrics>
            <Badge>{skill.activity_count} activities</Badge>
            <GrowthBadge growth={skill.avg_growth}>
              +{(skill.avg_growth * 100).toFixed(0)}% growth
            </GrowthBadge>
            <AgentBadge>{skill.agent_count} agents</AgentBadge>
          </Metrics>
        </SkillRow>
      ))}
    </Card>
  );
};
```

### Widget 3: Excellence Patterns

```javascript
// curator-ui/src/components/ExcellencePatterns.js

const ExcellencePatterns = () => {
  const [patterns, setPatterns] = useState([]);

  useEffect(() => {
    fetch('http://localhost:8011/knowledge/excellence-patterns')
      .then(res => res.json())
      .then(data => setPatterns(data));
  }, []);

  return (
    <Card title="Best-in-Class Patterns">
      {patterns.map(pattern => (
        <PatternCard key={pattern.pattern_id}>
          <Header>
            <Title>{pattern.name}</Title>
            <Rating>{(pattern.effectiveness_rating * 100).toFixed(0)}% effective</Rating>
          </Header>
          <Category>{pattern.category}</Category>
          <Domain>{pattern.domain_name}</Domain>
          <SynergyCount>{pattern.synergy_count} synergies</SynergyCount>
        </PatternCard>
      ))}
    </Card>
  );
};
```

---

## 🚀 Deployment Checklist

### Phase 1: Database (30 mins)
- [ ] Apply migration 012 to CockroachDB
- [ ] Run seed script to populate knowledge
- [ ] Verify all tables created
- [ ] Test materialized views
- [ ] Confirm functions work

### Phase 2: Atlas Prime (1 hour)
- [ ] Add knowledge endpoints to atlas_prime.py
- [ ] Update self-reflection endpoint
- [ ] Add learning activity logging
- [ ] Test all new endpoints
- [ ] Restart Atlas Prime (port 8011)

### Phase 3: Job Queue (30 mins)
- [ ] Add daily_learning_summary job
- [ ] Add refresh_knowledge_views job
- [ ] Add weekly_learning_trends job
- [ ] Test job execution
- [ ] Schedule recurring jobs

### Phase 4: Dashboard (1 hour)
- [ ] Create DailyLearningHighlights widget
- [ ] Create TrendingSkills widget
- [ ] Create ExcellencePatterns widget
- [ ] Add to main dashboard layout
- [ ] Test real-time updates

### Phase 5: Agent Integration (1 hour)
- [ ] Update agent self-reflection to log learnings
- [ ] Add skill tracking to agent activities
- [ ] Wire optic nerve to domains
- [ ] Test end-to-end flow
- [ ] Verify daily summary generation

---

## 📊 Success Validation

### Day 1:
```bash
# Check daily summary was generated
psql "$COCKROACH_DB_URL" -c "SELECT * FROM daily_learning_summary WHERE date = CURRENT_DATE"

# Verify learning entries
psql "$COCKROACH_DB_URL" -c "SELECT COUNT(*) FROM daily_learnings WHERE date = CURRENT_DATE"

# Test endpoints
curl http://localhost:8011/knowledge/daily-summary
curl http://localhost:8011/knowledge/trending-skills
curl http://localhost:8011/knowledge/excellence-patterns
```

### Week 1:
- [ ] 100+ learning_history entries
- [ ] 20+ daily_learnings per day
- [ ] All 48 agents have learning activities
- [ ] Weekly trends showing growth
- [ ] Dashboard widgets displaying real data

---

## 🎯 Final Integration Steps (Ready to Execute)

1. **Apply Migration:**
   ```bash
   psql "$COCKROACH_DB_URL" -f migrations/012_knowledge_enhancement_system.sql
   ```

2. **Seed Data:**
   ```bash
   python3 seed_knowledge_enhancement.py
   ```

3. **Add Endpoints to Atlas Prime:**
   - Copy endpoint code above into `atlas_prime.py`
   - Restart Atlas Prime service

4. **Schedule Jobs:**
   - Run SQL to insert job_queue entries

5. **Deploy Dashboard Widgets:**
   - Add widget components to curator-ui
   - Update main dashboard layout

6. **Test End-to-End:**
   - Create self-reflection → verify daily_learning created
   - Check daily summary generated automatically
   - Confirm dashboard shows real data

---

## ✅ Ready for Living Brain Finalization!

All components designed, coded, and documented.
**Next Action:** Execute deployment checklist above.

---

**Built with 🧠 + ❤️ for CESAR.ai**
**November 21, 2025 - Living Brain 2.0**
