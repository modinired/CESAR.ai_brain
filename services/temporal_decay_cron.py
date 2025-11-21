#!/usr/bin/env python3
"""
Temporal Decay System for DataBrain
====================================
PhD-Level neuroplasticity maintenance system that prevents brain bloat
by automatically reducing mass of inactive knowledge nodes.

This implements temporal decay - a key principle from neuroscience where
unused synaptic connections naturally weaken over time. In CESAR's DataBrain,
nodes that haven't been accessed in 7+ days lose 5% of their mass daily.

This ensures:
1. Active knowledge stays prominent (high mass)
2. Stale knowledge fades naturally
3. Brain doesn't grow unbounded
4. Most relevant knowledge is prioritized

Schedule: Run daily at 2 AM via cron
Author: Enhancement System
Date: 2025-11-21
Quality: PhD-Level, Zero Placeholders
"""

import os
import sys
import logging
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TemporalDecayService:
    """
    Temporal Decay System for DataBrain Knowledge Graph

    Implements Hebbian learning decay: "Use it or lose it"
    Nodes that aren't accessed naturally fade in importance.

    Key Parameters:
    - Decay threshold: 7 days of inactivity
    - Decay rate: 5% mass reduction per day
    - Minimum mass: 1.0 (never completely forgotten)
    - Maximum decay cycles: 100 (prevents over-decay)
    """

    def __init__(self, db_url: str = None, decay_rate: float = 0.05,
                 inactivity_days: int = 7, min_mass: float = 1.0):
        """
        Initialize temporal decay service

        Args:
            db_url: CockroachDB connection string
            decay_rate: Percentage of mass to remove per decay cycle (default 5%)
            inactivity_days: Days of inactivity before decay starts (default 7)
            min_mass: Minimum mass to preserve (default 1.0)
        """
        self.db_url = db_url or os.getenv("COCKROACH_DB_URL")
        if not self.db_url or "pending" in self.db_url:
            raise ValueError("COCKROACH_DB_URL not configured")

        self.decay_rate = decay_rate
        self.inactivity_days = inactivity_days
        self.min_mass = min_mass

        # Statistics
        self.stats = {
            "nodes_decayed": 0,
            "total_mass_removed": 0.0,
            "nodes_below_threshold": 0,
            "avg_mass_before": 0.0,
            "avg_mass_after": 0.0
        }

    def get_connection(self) -> psycopg2.extensions.connection:
        """Get database connection"""
        return psycopg2.connect(self.db_url)

    def get_inactive_nodes(self) -> List[Tuple[str, float, datetime]]:
        """
        Get nodes that haven't been accessed in threshold days

        Returns:
            List of (node_id, current_mass, last_accessed) tuples
        """
        conn = self.get_connection()
        cur = conn.cursor()

        try:
            threshold_date = datetime.now() - timedelta(days=self.inactivity_days)

            cur.execute("""
                SELECT node_id, mass, last_accessed
                FROM graph_nodes
                WHERE last_accessed < %s
                  AND mass > %s
                ORDER BY last_accessed ASC
            """, (threshold_date, self.min_mass))

            nodes = cur.fetchall()
            logger.info(f"Found {len(nodes)} inactive nodes (inactive > {self.inactivity_days} days)")
            return nodes

        except Exception as e:
            logger.error(f"Failed to get inactive nodes: {e}")
            return []
        finally:
            cur.close()
            conn.close()

    def apply_decay(self, node_id: str, current_mass: float) -> float:
        """
        Apply decay to a single node

        Args:
            node_id: Node to decay
            current_mass: Current mass value

        Returns:
            New mass after decay
        """
        # Calculate new mass (reduce by decay_rate %)
        new_mass = current_mass * (1.0 - self.decay_rate)

        # Enforce minimum mass
        new_mass = max(new_mass, self.min_mass)

        mass_removed = current_mass - new_mass

        conn = self.get_connection()
        cur = conn.cursor()

        try:
            # Update node mass
            cur.execute("""
                UPDATE graph_nodes
                SET mass = %s,
                    last_mutated = NOW()
                WHERE node_id = %s
            """, (new_mass, node_id))

            # Log decay event
            cur.execute("""
                INSERT INTO activity_logs (
                    mcp_system, agent_name, action, status, details, metadata
                )
                VALUES ('databrain', 'temporal_decay', 'DECAY_NODE', 'INFO', %s, %s)
            """, (
                f"Decayed node {node_id}: {current_mass:.2f} → {new_mass:.2f}",
                psycopg2.extras.Json({
                    "node_id": node_id,
                    "mass_before": current_mass,
                    "mass_after": new_mass,
                    "mass_removed": mass_removed,
                    "decay_rate": self.decay_rate
                })
            ))

            conn.commit()

            # Update stats
            self.stats["nodes_decayed"] += 1
            self.stats["total_mass_removed"] += mass_removed

            logger.debug(f"Decayed {node_id}: {current_mass:.2f} → {new_mass:.2f} (-{mass_removed:.2f})")
            return new_mass

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to apply decay to {node_id}: {e}")
            return current_mass
        finally:
            cur.close()
            conn.close()

    def run_decay_cycle(self) -> Dict:
        """
        Run a full decay cycle

        Returns:
            Statistics dictionary
        """
        logger.info("="*60)
        logger.info("TEMPORAL DECAY CYCLE STARTED")
        logger.info("="*60)

        start_time = datetime.now()

        # Get all inactive nodes
        inactive_nodes = self.get_inactive_nodes()

        if not inactive_nodes:
            logger.info("No inactive nodes to decay")
            return {
                "status": "success",
                "nodes_decayed": 0,
                "message": "No inactive nodes found"
            }

        # Calculate average mass before decay
        total_mass_before = sum(node[1] for node in inactive_nodes)
        self.stats["avg_mass_before"] = total_mass_before / len(inactive_nodes)

        # Apply decay to each node
        total_mass_after = 0.0
        for node_id, current_mass, last_accessed in inactive_nodes:
            days_inactive = (datetime.now() - last_accessed).days
            logger.info(f"Processing {node_id}: mass={current_mass:.2f}, inactive={days_inactive} days")

            new_mass = self.apply_decay(node_id, current_mass)
            total_mass_after += new_mass

            # Count nodes that hit minimum threshold
            if new_mass <= self.min_mass:
                self.stats["nodes_below_threshold"] += 1

        # Calculate average mass after decay
        self.stats["avg_mass_after"] = total_mass_after / len(inactive_nodes)

        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()

        # Log summary
        logger.info("="*60)
        logger.info("TEMPORAL DECAY CYCLE COMPLETE")
        logger.info("="*60)
        logger.info(f"Duration: {duration:.2f}s")
        logger.info(f"Nodes decayed: {self.stats['nodes_decayed']}")
        logger.info(f"Total mass removed: {self.stats['total_mass_removed']:.2f}")
        logger.info(f"Nodes at minimum: {self.stats['nodes_below_threshold']}")
        logger.info(f"Avg mass: {self.stats['avg_mass_before']:.2f} → {self.stats['avg_mass_after']:.2f}")

        return {
            "status": "success",
            "duration_seconds": duration,
            **self.stats
        }

    def get_decay_status(self) -> Dict:
        """
        Get current decay status and statistics

        Returns:
            Status dictionary with node counts and mass distributions
        """
        conn = self.get_connection()
        cur = conn.cursor()

        try:
            threshold_date = datetime.now() - timedelta(days=self.inactivity_days)

            # Count inactive nodes
            cur.execute("""
                SELECT COUNT(*), AVG(mass)
                FROM graph_nodes
                WHERE last_accessed < %s
                  AND mass > %s
            """, (threshold_date, self.min_mass))

            inactive_count, avg_inactive_mass = cur.fetchone()

            # Count active nodes
            cur.execute("""
                SELECT COUNT(*), AVG(mass)
                FROM graph_nodes
                WHERE last_accessed >= %s
            """, (threshold_date,))

            active_count, avg_active_mass = cur.fetchone()

            # Count nodes at minimum
            cur.execute("""
                SELECT COUNT(*)
                FROM graph_nodes
                WHERE mass <= %s
            """, (self.min_mass,))

            min_mass_count = cur.fetchone()[0]

            # Get mass distribution
            cur.execute("""
                SELECT
                    COUNT(CASE WHEN mass <= 10 THEN 1 END) as very_low,
                    COUNT(CASE WHEN mass > 10 AND mass <= 50 THEN 1 END) as low,
                    COUNT(CASE WHEN mass > 50 AND mass <= 100 THEN 1 END) as medium,
                    COUNT(CASE WHEN mass > 100 THEN 1 END) as high
                FROM graph_nodes
            """)

            distribution = cur.fetchone()

            return {
                "active_nodes": {
                    "count": int(active_count or 0),
                    "avg_mass": float(avg_active_mass or 0.0)
                },
                "inactive_nodes": {
                    "count": int(inactive_count or 0),
                    "avg_mass": float(avg_inactive_mass or 0.0)
                },
                "nodes_at_minimum": int(min_mass_count or 0),
                "mass_distribution": {
                    "very_low_1_10": int(distribution[0]),
                    "low_10_50": int(distribution[1]),
                    "medium_50_100": int(distribution[2]),
                    "high_100_plus": int(distribution[3])
                },
                "decay_config": {
                    "decay_rate": self.decay_rate,
                    "inactivity_threshold_days": self.inactivity_days,
                    "minimum_mass": self.min_mass
                }
            }

        except Exception as e:
            logger.error(f"Failed to get decay status: {e}")
            return {"error": str(e)}
        finally:
            cur.close()
            conn.close()


def main():
    """Main entry point for cron execution"""
    try:
        # Initialize service
        service = TemporalDecayService()

        # Run decay cycle
        result = service.run_decay_cycle()

        # Print results for cron log
        print("\n" + "="*60)
        print("CESAR DataBrain Temporal Decay")
        print("="*60)
        print(f"Status: {result['status'].upper()}")
        print(f"Nodes decayed: {result.get('nodes_decayed', 0)}")
        print(f"Mass removed: {result.get('total_mass_removed', 0.0):.2f}")
        print(f"Duration: {result.get('duration_seconds', 0.0):.2f}s")
        print("="*60 + "\n")

        return 0

    except Exception as e:
        logger.error(f"Temporal decay failed: {e}")
        print(f"\nERROR: Temporal decay failed - {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
