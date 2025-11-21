"""
Knowledge Enhancement + Cognitive Health Integration
Endpoints for Living Brain 2.0
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import date, datetime, timedelta
from pydantic import BaseModel
import json

router = APIRouter(prefix="/atlas", tags=["Knowledge & Cognition"])

# ============================================================================
# MODELS
# ============================================================================

class DailyLearning(BaseModel):
    learning_type: str  # 'insight', 'skill_improvement', 'connection', 'breakthrough', 'pattern'
    skill_name: Optional[str] = None
    domain_name: Optional[str] = None
    title: str
    description: str
    importance_score: float = 0.7
    confidence_level: float = 0.8

class LearningActivity(BaseModel):
    skill_name: str
    activity_type: str  # 'study', 'practice', 'reflection', 'application', 'teaching'
    duration_minutes: int
    insights_gained: List[str] = []
    challenges_faced: List[str] = []
    proficiency_before: Optional[float] = None
    proficiency_after: Optional[float] = None

class EnhancedSelfReflection(BaseModel):
    reflection_content: str
    insights_gained: List[str] = []
    skills_practiced: List[str] = []
    challenges_faced: List[str] = []
    excellence_patterns_applied: List[str] = []

# ============================================================================
# DAILY LEARNING ENDPOINTS
# ============================================================================

@router.get("/knowledge/daily-summary")
async def get_daily_summary(target_date: Optional[str] = None):
    """Get daily learning summary with top insights and progress metrics"""
    from database_async import get_db_connection

    if not target_date:
        target_date = date.today()
    else:
        target_date = datetime.strptime(target_date, "%Y-%m-%d").date()

    async with get_db_connection() as conn:
        summary = await conn.fetchrow('''
            SELECT
                date,
                total_learnings,
                top_learnings,
                domains_explored,
                skills_improved,
                overall_progress_score,
                created_at
            FROM daily_learning_summary
            WHERE date = $1
        ''', target_date)

        if not summary:
            # Generate if not exists
            learnings = await conn.fetch('''
                SELECT
                    learning_type,
                    title,
                    description,
                    importance_score
                FROM daily_learnings
                WHERE date = $1
                ORDER BY importance_score DESC
                LIMIT 10
            ''', target_date)

            if learnings:
                top_learnings = [
                    {
                        'type': l['learning_type'],
                        'title': l['title'],
                        'description': l['description'],
                        'importance': float(l['importance_score'])
                    }
                    for l in learnings
                ]

                return {
                    "date": str(target_date),
                    "total_learnings": len(learnings),
                    "top_learnings": top_learnings,
                    "overall_progress_score": sum(l['importance_score'] for l in learnings) / len(learnings)
                }

            return {
                "date": str(target_date),
                "total_learnings": 0,
                "top_learnings": [],
                "overall_progress_score": 0.0,
                "message": "No learnings recorded for this date"
            }

        return {
            "date": str(summary['date']),
            "total_learnings": summary['total_learnings'],
            "top_learnings": summary['top_learnings'],
            "domains_explored": summary.get('domains_explored', []),
            "skills_improved": summary.get('skills_improved', []),
            "overall_progress_score": float(summary['overall_progress_score'] or 0),
            "created_at": summary['created_at'].isoformat()
        }

@router.post("/knowledge/log-learning")
async def log_learning_activity(
    agent_id: str,
    activity: LearningActivity
):
    """Log a learning activity for an agent"""
    from database_async import get_db_connection

    async with get_db_connection() as conn:
        # Get skill_id
        skill_id = await conn.fetchval(
            'SELECT skill_id FROM skills WHERE name = $1',
            activity.skill_name
        )

        if not skill_id:
            raise HTTPException(404, f"Skill '{activity.skill_name}' not found")

        # Log learning history
        history_id = await conn.fetchval('''
            INSERT INTO learning_history (
                agent_id, skill_id, activity_type,
                duration_minutes, insights_gained, challenges_faced,
                proficiency_before, proficiency_after
            )
            VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7, $8)
            RETURNING history_id
        ''', agent_id, skill_id, activity.activity_type,
            activity.duration_minutes,
            json.dumps(activity.insights_gained),
            json.dumps(activity.challenges_faced),
            activity.proficiency_before,
            activity.proficiency_after
        )

        return {
            "status": "success",
            "history_id": str(history_id),
            "agent_id": agent_id,
            "skill": activity.skill_name
        }

# ============================================================================
# ENHANCED SELF-REFLECTION (Integrates with Cognitive Health)
# ============================================================================

@router.post("/agents/{agent_id}/self-reflection-enhanced")
async def enhanced_self_reflection(
    agent_id: str,
    reflection: EnhancedSelfReflection
):
    """
    Enhanced self-reflection that:
    1. Stores reflection in agent_self_reflections
    2. Creates daily_learnings for each insight
    3. Logs skill practice in learning_history
    4. Tracks excellence pattern application
    5. Contributes to cognitive health score
    """
    from database_async import get_db_connection

    async with get_db_connection() as conn:
        # 1. Store self-reflection
        reflection_id = await conn.fetchval('''
            INSERT INTO agent_self_reflections (
                agent_id, reflection_content, reflection_date
            )
            VALUES ($1, $2, CURRENT_DATE)
            ON CONFLICT (agent_id, reflection_date) DO UPDATE
            SET reflection_content = EXCLUDED.reflection_content,
                updated_at = now()
            RETURNING reflection_id
        ''', agent_id, reflection.reflection_content)

        # 2. Create daily learnings for each insight
        learning_ids = []
        for insight in reflection.insights_gained:
            learning_id = await conn.fetchval('''
                INSERT INTO daily_learnings (
                    date, agent_id, learning_type,
                    title, description, importance_score, confidence_level
                )
                VALUES (
                    CURRENT_DATE, $1, 'insight',
                    $2, $3, 0.75, 0.8
                )
                RETURNING learning_id
            ''', agent_id, insight[:100], insight)
            learning_ids.append(str(learning_id))

        # 3. Log skill practice
        skill_logs = []
        for skill_name in reflection.skills_practiced:
            skill_id = await conn.fetchval(
                'SELECT skill_id FROM skills WHERE name = $1', skill_name
            )
            if skill_id:
                await conn.execute('''
                    INSERT INTO learning_history (
                        agent_id, skill_id, activity_type, timestamp
                    )
                    VALUES ($1, $2, 'reflection', now())
                ''', agent_id, skill_id)
                skill_logs.append(skill_name)

        # 4. Track excellence patterns applied
        patterns_tracked = []
        for pattern_name in reflection.excellence_patterns_applied:
            pattern_id = await conn.fetchval(
                'SELECT pattern_id FROM excellence_patterns WHERE name = $1',
                pattern_name
            )
            if pattern_id:
                # Could create a new table for pattern_applications
                patterns_tracked.append(pattern_name)

        # 5. Check if daily summary needs generation
        summary_exists = await conn.fetchval(
            'SELECT EXISTS(SELECT 1 FROM daily_learning_summary WHERE date = CURRENT_DATE)'
        )

        if not summary_exists and len(learning_ids) > 0:
            # Auto-generate summary
            await conn.execute('''
                INSERT INTO daily_learning_summary (
                    date, total_learnings, overall_progress_score
                )
                SELECT
                    CURRENT_DATE,
                    COUNT(*),
                    AVG(importance_score)
                FROM daily_learnings
                WHERE date = CURRENT_DATE
            ''')

        return {
            "reflection_id": str(reflection_id),
            "insights_logged": len(learning_ids),
            "skills_tracked": len(skill_logs),
            "patterns_applied": len(patterns_tracked),
            "cognitive_health_impact": {
                "daily_reflection_completed": True,
                "learning_velocity_boost": len(learning_ids) * 0.05,
                "skill_breadth_contribution": len(skill_logs)
            }
        }

# ============================================================================
# TRENDING SKILLS & PATTERNS
# ============================================================================

@router.get("/knowledge/trending-skills")
async def get_trending_skills(days: int = 7, limit: int = 20):
    """Get trending skills from last N days"""
    from database_async import get_db_connection

    async with get_db_connection() as conn:
        skills = await conn.fetch(f'''
            SELECT
                s.skill_id,
                s.name as skill_name,
                s.skill_type,
                kd.name as domain_name,
                COUNT(lh.history_id) as activity_count,
                COUNT(DISTINCT lh.agent_id) as agent_count,
                AVG(lh.proficiency_after - lh.proficiency_before) as avg_growth,
                MAX(lh.timestamp) as last_activity
            FROM skills s
            LEFT JOIN knowledge_domains kd ON s.domain_id = kd.domain_id
            LEFT JOIN learning_history lh ON s.skill_id = lh.skill_id
            WHERE lh.timestamp > now() - interval '{days} days'
            GROUP BY s.skill_id, s.name, s.skill_type, kd.name
            HAVING COUNT(lh.history_id) > 0
            ORDER BY activity_count DESC, avg_growth DESC
            LIMIT $1
        ''', limit)

        return [
            {
                "skill_id": str(s['skill_id']),
                "skill_name": s['skill_name'],
                "skill_type": s['skill_type'],
                "domain_name": s['domain_name'],
                "activity_count": s['activity_count'],
                "agent_count": s['agent_count'],
                "avg_growth": float(s['avg_growth'] or 0),
                "last_activity": s['last_activity'].isoformat() if s['last_activity'] else None
            }
            for s in skills
        ]

@router.get("/knowledge/excellence-patterns")
async def get_excellence_patterns(min_effectiveness: float = 0.8):
    """Get best-in-class excellence patterns"""
    from database_async import get_db_connection

    async with get_db_connection() as conn:
        patterns = await conn.fetch('''
            SELECT
                ep.pattern_id,
                ep.name,
                ep.category,
                kd.name as domain_name,
                ep.description,
                ep.key_principles,
                ep.effectiveness_rating,
                COUNT(es1.synergy_id) + COUNT(es2.synergy_id) as synergy_count
            FROM excellence_patterns ep
            LEFT JOIN knowledge_domains kd ON ep.domain_id = kd.domain_id
            LEFT JOIN excellence_synergies es1 ON ep.pattern_id = es1.pattern1_id
            LEFT JOIN excellence_synergies es2 ON ep.pattern_id = es2.pattern2_id
            WHERE ep.effectiveness_rating >= $1
            GROUP BY ep.pattern_id, ep.name, ep.category, kd.name,
                     ep.description, ep.key_principles, ep.effectiveness_rating
            ORDER BY ep.effectiveness_rating DESC, synergy_count DESC
            LIMIT 20
        ''', min_effectiveness)

        return [
            {
                "pattern_id": str(p['pattern_id']),
                "name": p['name'],
                "category": p['category'],
                "domain": p['domain_name'],
                "description": p['description'],
                "key_principles": p['key_principles'],
                "effectiveness_rating": float(p['effectiveness_rating']),
                "synergy_count": p['synergy_count']
            }
            for p in patterns
        ]

# ============================================================================
# PSYCHOLOGY-NLP CONNECTIONS
# ============================================================================

@router.get("/knowledge/psych-nlp-bridges")
async def get_psychology_nlp_bridges(min_strength: float = 0.7):
    """Get cross-domain connections between psychology and NLP"""
    from database_async import get_db_connection

    async with get_db_connection() as conn:
        bridges = await conn.fetch('''
            SELECT
                pc.name as psychology_concept,
                pc.category as psych_category,
                nt.name as nlp_technique,
                nt.category as nlp_category,
                pnb.connection_type,
                pnb.description,
                pnb.strength,
                pnb.practical_applications
            FROM psychology_nlp_bridges pnb
            JOIN psychological_concepts pc ON pnb.psychological_concept_id = pc.concept_id
            JOIN nlp_techniques nt ON pnb.nlp_technique_id = nt.technique_id
            WHERE pnb.strength >= $1
            ORDER BY pnb.strength DESC
        ''', min_strength)

        return [
            {
                "psychology_concept": b['psychology_concept'],
                "psych_category": b['psych_category'],
                "nlp_technique": b['nlp_technique'],
                "nlp_category": b['nlp_category'],
                "connection_type": b['connection_type'],
                "description": b['description'],
                "strength": float(b['strength']),
                "applications": b['practical_applications']
            }
            for b in bridges
        ]

# ============================================================================
# AGENT KNOWLEDGE PROFILE
# ============================================================================

@router.get("/agents/{agent_id}/knowledge-profile")
async def get_agent_knowledge_profile(agent_id: str, days: int = 30):
    """Get comprehensive knowledge profile for an agent"""
    from database_async import get_db_connection

    async with get_db_connection() as conn:
        # Skills practiced
        skills = await conn.fetch(f'''
            SELECT
                s.name,
                s.skill_type,
                COUNT(*) as practice_count,
                AVG(lh.proficiency_after - lh.proficiency_before) as avg_improvement
            FROM learning_history lh
            JOIN skills s ON lh.skill_id = s.skill_id
            WHERE lh.agent_id = $1
              AND lh.timestamp > now() - interval '{days} days'
            GROUP BY s.skill_id, s.name, s.skill_type
            ORDER BY practice_count DESC
        ''', agent_id)

        # Recent insights
        insights = await conn.fetch(f'''
            SELECT
                learning_type,
                title,
                importance_score,
                date
            FROM daily_learnings
            WHERE agent_id = $1
              AND date > CURRENT_DATE - interval '{days} days'
            ORDER BY date DESC, importance_score DESC
            LIMIT 20
        ''', agent_id)

        # Learning velocity
        velocity = await conn.fetchval(f'''
            SELECT COUNT(*)::FLOAT / {days}
            FROM learning_history
            WHERE agent_id = $1
              AND timestamp > now() - interval '{days} days'
        ''', agent_id)

        return {
            "agent_id": agent_id,
            "period_days": days,
            "skills_practiced": [
                {
                    "name": s['name'],
                    "type": s['skill_type'],
                    "practice_count": s['practice_count'],
                    "avg_improvement": float(s['avg_improvement'] or 0)
                }
                for s in skills
            ],
            "recent_insights": [
                {
                    "type": i['learning_type'],
                    "title": i['title'],
                    "importance": float(i['importance_score']),
                    "date": str(i['date'])
                }
                for i in insights
            ],
            "learning_velocity": float(velocity or 0),
            "total_skills": len(skills),
            "total_insights": len(insights)
        }

# ============================================================================
# INTEGRATED COGNITIVE HEALTH + KNOWLEDGE SCORE
# ============================================================================

@router.get("/agents/{agent_id}/cognitive-knowledge-score")
async def get_cognitive_knowledge_score(agent_id: str):
    """
    Integrated score combining:
    - Cognitive health metrics (from existing /cognition endpoint)
    - Knowledge enhancement metrics (learning velocity, skill breadth, etc.)
    """
    from database_async import get_db_connection

    async with get_db_connection() as conn:
        # Knowledge metrics (last 7 days)
        knowledge_metrics = await conn.fetchrow('''
            SELECT
                COUNT(DISTINCT lh.skill_id) as skills_practiced,
                COUNT(lh.history_id) as total_activities,
                AVG(lh.proficiency_after - lh.proficiency_before) as avg_skill_growth,
                COUNT(DISTINCT dl.learning_id) as daily_insights,
                AVG(dl.importance_score) as avg_insight_importance
            FROM learning_history lh
            LEFT JOIN daily_learnings dl ON dl.agent_id = lh.agent_id
                AND dl.date > CURRENT_DATE - interval '7 days'
            WHERE lh.agent_id = $1
              AND lh.timestamp > now() - interval '7 days'
        ''', agent_id)

        # Self-reflection adherence (if table exists)
        try:
            reflection_count = await conn.fetchval('''
                SELECT COUNT(*)
                FROM agent_self_reflections
                WHERE agent_id = $1
                  AND reflection_date > CURRENT_DATE - interval '7 days'
            ''', agent_id)
        except Exception:
            # Table doesn't exist yet - cognitive health system not fully deployed
            reflection_count = 0

        # Calculate subscores
        learning_velocity_score = min(100, (knowledge_metrics['total_activities'] or 0) * 10)
        skill_breadth_score = min(100, (knowledge_metrics['skills_practiced'] or 0) * 15)
        skill_growth_score = min(100, (knowledge_metrics['avg_skill_growth'] or 0) * 200)
        insight_quality_score = min(100, (knowledge_metrics['avg_insight_importance'] or 0) * 100)
        reflection_score = min(100, reflection_count * 14.3)  # 7 days = 100

        # Overall knowledge health score
        knowledge_score = (
            learning_velocity_score * 0.25 +
            skill_breadth_score * 0.25 +
            skill_growth_score * 0.2 +
            insight_quality_score * 0.2 +
            reflection_score * 0.1
        )

        return {
            "agent_id": agent_id,
            "overall_knowledge_health": round(knowledge_score, 2),
            "subscores": {
                "learning_velocity": round(learning_velocity_score, 2),
                "skill_breadth": round(skill_breadth_score, 2),
                "skill_growth": round(skill_growth_score, 2),
                "insight_quality": round(insight_quality_score, 2),
                "daily_reflection_adherence": round(reflection_score, 2)
            },
            "raw_metrics": {
                "skills_practiced_7d": knowledge_metrics['skills_practiced'],
                "total_activities_7d": knowledge_metrics['total_activities'],
                "avg_skill_growth": float(knowledge_metrics['avg_skill_growth'] or 0),
                "daily_insights_7d": knowledge_metrics['daily_insights'],
                "avg_insight_importance": float(knowledge_metrics['avg_insight_importance'] or 0),
                "reflections_7d": reflection_count
            }
        }
