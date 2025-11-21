#!/usr/bin/env python3
"""
Agent Reputation Scoring Service
=================================
PhD-Level system for tracking and managing agent performance reputation.

Implements meritocratic knowledge contribution where high-quality mutations
from reliable agents carry more weight than mutations from unreliable agents.

Key Features:
- Dynamic reputation scoring (0-100 scale, 50 = neutral)
- Success/failure tracking for all brain mutations
- Quality-weighted reputation updates
- Periodic decay towards neutral (prevents stagnation)
- Reputation history tracking
- Top agent leaderboard

Author: Enhancement System
Date: 2025-11-21
Quality: PhD-Level, Zero Placeholders
"""

import os
import logging
import psycopg2
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


class AgentReputationService:
    """
    Agent Reputation Scoring System

    Tracks agent performance across all DataBrain mutations and
    maintains reputation scores that weight future contributions.

    Reputation Formula:
    - Success: +2.0 points (weighted by quality score 0-100)
    - Failure: -1.5 points (fixed penalty)
    - Periodic decay: +/- 1% towards 50 (neutral) per week
    """

    def __init__(self, db_url: str = None):
        """
        Initialize agent reputation service

        Args:
            db_url: CockroachDB connection string
        """
        self.db_url = db_url or os.getenv("COCKROACH_DB_URL")
        if not self.db_url or "pending" in self.db_url:
            raise ValueError("COCKROACH_DB_URL not configured")

    def get_connection(self) -> psycopg2.extensions.connection:
        """Get database connection"""
        return psycopg2.connect(self.db_url)

    def record_mutation_quality(
        self,
        agent_name: str,
        mcp_system: str,
        mutation_type: str,
        success: bool,
        quality_score: float = 50.0,
        confidence: float = 50.0,
        impact_score: float = None,
        target_node_id: str = None,
        target_link_id: str = None,
        error_message: str = None,
        mutation_params: Dict = None,
        brain_state_before: Dict = None,
        brain_state_after: Dict = None
    ) -> str:
        """
        Record a mutation quality event and update agent reputation

        Args:
            agent_name: Name of agent performing mutation
            mcp_system: MCP system (finpsy, lex, inno, etc.)
            mutation_type: Type of mutation (CREATE_NODE, UPDATE_MASS, etc.)
            success: Whether mutation succeeded
            quality_score: Quality of mutation (0-100)
            confidence: Agent's confidence in mutation (0-100)
            impact_score: Measured impact on brain performance (0-100)
            target_node_id: Target node if applicable
            target_link_id: Target link if applicable
            error_message: Error message if failed
            mutation_params: Mutation parameters
            brain_state_before: Brain state before mutation
            brain_state_after: Brain state after mutation

        Returns:
            Mutation tracking ID
        """
        conn = self.get_connection()
        cur = conn.cursor()

        try:
            # Insert mutation quality record
            cur.execute("""
                INSERT INTO mutation_quality_tracking (
                    agent_name, mcp_system, mutation_type, target_node_id,
                    target_link_id, quality_score, confidence, impact_score,
                    success, error_message, mutation_params,
                    brain_state_before, brain_state_after, attempted_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                RETURNING id
            """, (
                agent_name, mcp_system, mutation_type, target_node_id,
                target_link_id, quality_score, confidence, impact_score,
                success, error_message,
                psycopg2.extras.Json(mutation_params) if mutation_params else None,
                psycopg2.extras.Json(brain_state_before) if brain_state_before else None,
                psycopg2.extras.Json(brain_state_after) if brain_state_after else None
            ))

            mutation_id = cur.fetchone()[0]

            # Update agent reputation using database function
            cur.execute("""
                SELECT update_agent_reputation(%s, %s, %s, %s, %s)
            """, (
                agent_name, mcp_system, success, quality_score,
                f"{mutation_type} {'succeeded' if success else 'failed'}"
            ))

            new_reputation = cur.fetchone()[0]

            conn.commit()

            logger.info(f"Recorded mutation quality for {agent_name}: "
                       f"{'SUCCESS' if success else 'FAILURE'}, "
                       f"new reputation: {new_reputation:.2f}")

            return str(mutation_id)

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to record mutation quality: {e}")
            raise
        finally:
            cur.close()
            conn.close()

    def get_agent_reputation(self, agent_name: str) -> Optional[Dict]:
        """
        Get current reputation for an agent

        Args:
            agent_name: Agent name

        Returns:
            Dict with reputation details or None if not found
        """
        conn = self.get_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                SELECT
                    reputation_score, total_mutations,
                    successful_mutations, failed_mutations,
                    last_reputation_update
                FROM agents
                WHERE agent_name = %s
            """, (agent_name,))

            row = cur.fetchone()
            if not row:
                return None

            reputation_score, total, success, failed, last_update = row

            success_rate = (float(success) / float(total) * 100.0) if total > 0 else 0.0

            return {
                "agent_name": agent_name,
                "reputation_score": float(reputation_score) if reputation_score else 50.0,
                "total_mutations": int(total) if total else 0,
                "successful_mutations": int(success) if success else 0,
                "failed_mutations": int(failed) if failed else 0,
                "success_rate_percent": success_rate,
                "last_reputation_update": last_update.isoformat() if last_update else None,
                "reputation_tier": self._get_reputation_tier(float(reputation_score) if reputation_score else 50.0)
            }

        except Exception as e:
            logger.error(f"Failed to get agent reputation: {e}")
            return None
        finally:
            cur.close()
            conn.close()

    def _get_reputation_tier(self, score: float) -> str:
        """Get reputation tier based on score"""
        if score >= 75:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Fair"
        else:
            return "Poor"

    def get_top_agents(self, limit: int = 10) -> List[Dict]:
        """
        Get top agents by reputation

        Args:
            limit: Number of agents to return

        Returns:
            List of agent reputation dicts
        """
        conn = self.get_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                SELECT * FROM get_top_agents_by_reputation(%s)
            """, (limit,))

            agents = []
            for row in cur.fetchall():
                agent_name, mcp_system, reputation_score, total_mutations, success_rate, rank = row
                agents.append({
                    "rank": int(rank),
                    "agent_name": agent_name,
                    "mcp_system": mcp_system,
                    "reputation_score": float(reputation_score),
                    "total_mutations": int(total_mutations),
                    "success_rate_percent": float(success_rate),
                    "reputation_tier": self._get_reputation_tier(float(reputation_score))
                })

            return agents

        except Exception as e:
            logger.error(f"Failed to get top agents: {e}")
            return []
        finally:
            cur.close()
            conn.close()

    def get_reputation_history(
        self,
        agent_name: str = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get reputation history events

        Args:
            agent_name: Filter by agent name (optional)
            limit: Maximum number of events to return

        Returns:
            List of reputation history events
        """
        conn = self.get_connection()
        cur = conn.cursor()

        try:
            if agent_name:
                cur.execute("""
                    SELECT
                        agent_name, mcp_system, old_score, new_score,
                        score_delta, event_type, event_details, recorded_at
                    FROM agent_reputation_history
                    WHERE agent_name = %s
                    ORDER BY recorded_at DESC
                    LIMIT %s
                """, (agent_name, limit))
            else:
                cur.execute("""
                    SELECT
                        agent_name, mcp_system, old_score, new_score,
                        score_delta, event_type, event_details, recorded_at
                    FROM agent_reputation_history
                    ORDER BY recorded_at DESC
                    LIMIT %s
                """, (limit,))

            events = []
            for row in cur.fetchall():
                agent, mcp, old, new, delta, event_type, details, recorded = row
                events.append({
                    "agent_name": agent,
                    "mcp_system": mcp,
                    "old_score": float(old),
                    "new_score": float(new),
                    "score_delta": float(delta),
                    "event_type": event_type,
                    "event_details": details,
                    "recorded_at": recorded.isoformat()
                })

            return events

        except Exception as e:
            logger.error(f"Failed to get reputation history: {e}")
            return []
        finally:
            cur.close()
            conn.close()

    def apply_reputation_decay(
        self,
        decay_rate: float = 0.01,
        min_mutations: int = 5
    ) -> int:
        """
        Apply periodic reputation decay towards neutral (50)

        This prevents reputation stagnation and ensures recent performance
        is weighted more heavily than ancient history.

        Args:
            decay_rate: Decay rate (default 1% per cycle)
            min_mutations: Only decay agents with this many mutations

        Returns:
            Number of agents affected
        """
        conn = self.get_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                SELECT apply_reputation_decay(%s, %s)
            """, (decay_rate, min_mutations))

            affected_count = cur.fetchone()[0]
            conn.commit()

            logger.info(f"Applied reputation decay to {affected_count} agents (rate={decay_rate:.2%})")
            return affected_count

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to apply reputation decay: {e}")
            return 0
        finally:
            cur.close()
            conn.close()

    def get_reputation_statistics(self) -> Dict:
        """
        Get overall reputation system statistics

        Returns:
            Dict with system-wide stats
        """
        conn = self.get_connection()
        cur = conn.cursor()

        try:
            # Get overall stats
            cur.execute("""
                SELECT
                    COUNT(*) as total_agents,
                    AVG(reputation_score) as avg_reputation,
                    MIN(reputation_score) as min_reputation,
                    MAX(reputation_score) as max_reputation,
                    SUM(total_mutations) as total_mutations,
                    SUM(successful_mutations) as total_success,
                    SUM(failed_mutations) as total_failures
                FROM agents
                WHERE total_mutations > 0
            """)

            row = cur.fetchone()
            total_agents, avg_rep, min_rep, max_rep, total_mut, total_succ, total_fail = row

            # Get tier distribution
            cur.execute("""
                SELECT
                    COUNT(CASE WHEN reputation_score >= 75 THEN 1 END) as excellent,
                    COUNT(CASE WHEN reputation_score >= 60 AND reputation_score < 75 THEN 1 END) as good,
                    COUNT(CASE WHEN reputation_score >= 40 AND reputation_score < 60 THEN 1 END) as fair,
                    COUNT(CASE WHEN reputation_score < 40 THEN 1 END) as poor
                FROM agents
                WHERE total_mutations > 0
            """)

            tier_row = cur.fetchone()

            overall_success_rate = (
                float(total_succ) / float(total_mut) * 100.0
                if total_mut and total_mut > 0 else 0.0
            )

            return {
                "total_agents": int(total_agents or 0),
                "average_reputation": float(avg_rep or 50.0),
                "min_reputation": float(min_rep or 0.0),
                "max_reputation": float(max_rep or 100.0),
                "total_mutations": int(total_mut or 0),
                "total_successful": int(total_succ or 0),
                "total_failed": int(total_fail or 0),
                "overall_success_rate_percent": overall_success_rate,
                "tier_distribution": {
                    "excellent_75_plus": int(tier_row[0]),
                    "good_60_74": int(tier_row[1]),
                    "fair_40_59": int(tier_row[2]),
                    "poor_0_39": int(tier_row[3])
                }
            }

        except Exception as e:
            logger.error(f"Failed to get reputation statistics: {e}")
            return {}
        finally:
            cur.close()
            conn.close()


# Global singleton
_global_reputation_service: Optional[AgentReputationService] = None


def get_reputation_service() -> AgentReputationService:
    """Get global reputation service instance (singleton)"""
    global _global_reputation_service
    if _global_reputation_service is None:
        _global_reputation_service = AgentReputationService()
    return _global_reputation_service


if __name__ == "__main__":
    # Test the reputation service
    logging.basicConfig(level=logging.INFO)

    service = AgentReputationService()

    print("\n" + "="*60)
    print("Agent Reputation Service - Test Mode")
    print("="*60)

    # Get statistics
    stats = service.get_reputation_statistics()
    print(f"\nTotal agents with mutations: {stats.get('total_agents', 0)}")
    print(f"Average reputation: {stats.get('average_reputation', 0.0):.2f}")
    print(f"Overall success rate: {stats.get('overall_success_rate_percent', 0.0):.2f}%")

    # Get top agents
    print("\nTop 10 Agents by Reputation:")
    print("-" * 60)
    top_agents = service.get_top_agents(10)
    for agent in top_agents:
        print(f"{agent['rank']}. {agent['agent_name']:30s} "
              f"Score: {agent['reputation_score']:5.2f} "
              f"({agent['reputation_tier']:9s}) "
              f"Success: {agent['success_rate_percent']:5.1f}%")

    print("\n" + "="*60 + "\n")
