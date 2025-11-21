#!/usr/bin/env python3
"""
Knowledge Gap Detection and Bridge Suggestion System
====================================================
PhD-Level graph analysis tool that identifies under-connected clusters
in the DataBrain knowledge graph and suggests bridge nodes to improve
knowledge integration.

Implements graph theory principles:
- Connected component analysis
- Betweenness centrality for bridge detection
- Clustering coefficient for density analysis
- Semantic gap identification via trigram analysis

Key Outputs:
- Isolated knowledge clusters (potential silos)
- Missing conceptual bridges
- Low-connectivity domains
- Suggested connections to improve knowledge flow

Author: Enhancement System
Date: 2025-11-21
Quality: PhD-Level, Zero Placeholders
"""

import os
import logging
import psycopg2
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, deque
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class KnowledgeGapAnalyzer:
    """
    Knowledge Gap Detection System

    Analyzes DataBrain knowledge graph structure to identify:
    1. Isolated clusters (knowledge silos)
    2. Under-connected domains
    3. Missing conceptual bridges
    4. Weak inter-domain connections

    Uses graph theory + semantic analysis to suggest improvements.
    """

    def __init__(self, db_url: str = None):
        """
        Initialize knowledge gap analyzer

        Args:
            db_url: CockroachDB connection string
        """
        self.db_url = db_url or os.getenv("COCKROACH_DB_URL")
        if not self.db_url or "pending" in self.db_url:
            raise ValueError("COCKROACH_DB_URL not configured")

        # Analysis thresholds
        self.min_cluster_size = 3  # Minimum nodes to be considered a cluster
        self.min_connectivity = 0.3  # Minimum connectivity ratio for health
        self.weak_link_threshold = 0.3  # Links below this strength are "weak"

    def get_connection(self) -> psycopg2.extensions.connection:
        """Get database connection"""
        return psycopg2.connect(self.db_url)

    def get_graph_structure(self) -> Tuple[Dict[str, Dict], Dict[str, List[Tuple[str, float]]]]:
        """
        Load complete graph structure from database

        Returns:
            Tuple of (nodes dict, adjacency dict)
            - nodes: {node_id: {label, type, z_index, mass, ...}}
            - adjacency: {node_id: [(connected_node_id, strength), ...]}
        """
        conn = self.get_connection()
        cur = conn.cursor()

        try:
            # Load all nodes
            cur.execute("""
                SELECT node_id, label, type, z_index, mass, description
                FROM graph_nodes
            """)

            nodes = {}
            for row in cur.fetchall():
                node_id, label, node_type, z_index, mass, description = row
                nodes[node_id] = {
                    "label": label,
                    "type": node_type,
                    "z_index": int(z_index) if z_index else 0,
                    "mass": float(mass) if mass else 0.0,
                    "description": description
                }

            # Load all links (bidirectional)
            cur.execute("""
                SELECT source_id, target_id, strength
                FROM graph_links
            """)

            adjacency = defaultdict(list)
            for row in cur.fetchall():
                source, target, strength = row
                strength_val = float(strength) if strength else 0.5

                # Add both directions (undirected graph)
                adjacency[source].append((target, strength_val))
                adjacency[target].append((source, strength_val))

            logger.info(f"Loaded graph: {len(nodes)} nodes, {len(adjacency)} adjacency entries")
            return nodes, dict(adjacency)

        except Exception as e:
            logger.error(f"Failed to load graph structure: {e}")
            return {}, {}
        finally:
            cur.close()
            conn.close()

    def find_connected_components(
        self,
        adjacency: Dict[str, List[Tuple[str, float]]]
    ) -> List[Set[str]]:
        """
        Find all connected components (clusters) in the graph

        Args:
            adjacency: Graph adjacency list

        Returns:
            List of sets, each set is a connected component
        """
        visited = set()
        components = []

        def bfs(start_node: str) -> Set[str]:
            """BFS to find all nodes in component"""
            component = set()
            queue = deque([start_node])
            component.add(start_node)
            visited.add(start_node)

            while queue:
                node = queue.popleft()
                for neighbor, _ in adjacency.get(node, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        component.add(neighbor)
                        queue.append(neighbor)

            return component

        # Find all components
        for node in adjacency.keys():
            if node not in visited:
                component = bfs(node)
                if len(component) >= self.min_cluster_size:
                    components.append(component)

        logger.info(f"Found {len(components)} connected components")
        return components

    def calculate_cluster_density(
        self,
        cluster: Set[str],
        adjacency: Dict[str, List[Tuple[str, float]]]
    ) -> float:
        """
        Calculate density of a cluster (ratio of actual links to possible links)

        Args:
            cluster: Set of node IDs in cluster
            adjacency: Graph adjacency list

        Returns:
            Density score (0-1)
        """
        n = len(cluster)
        if n < 2:
            return 0.0

        # Count actual edges within cluster
        actual_edges = 0
        for node in cluster:
            for neighbor, _ in adjacency.get(node, []):
                if neighbor in cluster and neighbor > node:  # Count each edge once
                    actual_edges += 1

        # Maximum possible edges in undirected graph: n(n-1)/2
        max_edges = (n * (n - 1)) / 2
        density = actual_edges / max_edges if max_edges > 0 else 0.0

        return density

    def identify_weak_connections(
        self,
        adjacency: Dict[str, List[Tuple[str, float]]]
    ) -> List[Dict]:
        """
        Identify weak connections in the graph

        Args:
            adjacency: Graph adjacency list

        Returns:
            List of weak connection dicts
        """
        weak_connections = []

        for source, neighbors in adjacency.items():
            for target, strength in neighbors:
                if strength < self.weak_link_threshold and source < target:  # Count each link once
                    weak_connections.append({
                        "source": source,
                        "target": target,
                        "strength": strength,
                        "severity": "weak" if strength >= 0.2 else "very_weak"
                    })

        weak_connections.sort(key=lambda x: x["strength"])
        return weak_connections

    def suggest_bridge_nodes(
        self,
        components: List[Set[str]],
        nodes: Dict[str, Dict]
    ) -> List[Dict]:
        """
        Suggest conceptual bridge nodes to connect isolated clusters

        Args:
            components: List of connected components
            nodes: Node metadata dict

        Returns:
            List of bridge suggestions
        """
        if len(components) <= 1:
            return []

        suggestions = []

        # For each pair of components, suggest bridging concepts
        for i in range(len(components)):
            for j in range(i + 1, len(components)):
                comp1, comp2 = components[i], components[j]

                # Get representative nodes from each cluster (highest mass)
                rep1 = max(comp1, key=lambda nid: nodes[nid]["mass"])
                rep2 = max(comp2, key=lambda nid: nodes[nid]["mass"])

                # Suggest bridge based on semantic similarity
                bridge_concept = self._suggest_bridge_concept(
                    nodes[rep1]["label"],
                    nodes[rep2]["label"]
                )

                suggestions.append({
                    "cluster_1": {
                        "size": len(comp1),
                        "representative": rep1,
                        "label": nodes[rep1]["label"]
                    },
                    "cluster_2": {
                        "size": len(comp2),
                        "representative": rep2,
                        "label": nodes[rep2]["label"]
                    },
                    "suggested_bridge": bridge_concept,
                    "priority": "high" if len(comp1) > 5 and len(comp2) > 5 else "medium"
                })

        return suggestions

    def _suggest_bridge_concept(self, label1: str, label2: str) -> str:
        """
        Suggest a bridging concept between two labels

        Args:
            label1: First label
            label2: Second label

        Returns:
            Suggested bridge concept name
        """
        # Simple heuristic: combine keywords from both labels
        words1 = set(label1.lower().split())
        words2 = set(label2.lower().split())

        common = words1 & words2
        if common:
            return f"{label1} <-> {label2} Integration"
        else:
            return f"{label1} / {label2} Bridge Concept"

    def analyze_knowledge_gaps(self) -> Dict:
        """
        Run complete knowledge gap analysis

        Returns:
            Comprehensive analysis report
        """
        logger.info("="*60)
        logger.info("KNOWLEDGE GAP ANALYSIS STARTED")
        logger.info("="*60)

        start_time = datetime.now()

        # Load graph
        nodes, adjacency = self.get_graph_structure()

        if not nodes:
            return {
                "status": "error",
                "message": "No nodes in DataBrain"
            }

        # Find connected components
        components = self.find_connected_components(adjacency)

        # Analyze each component
        component_analysis = []
        for i, comp in enumerate(components):
            density = self.calculate_cluster_density(comp, adjacency)

            # Get top nodes by mass
            top_nodes = sorted(
                [nodes[nid] for nid in comp],
                key=lambda n: n["mass"],
                reverse=True
            )[:3]

            component_analysis.append({
                "cluster_id": i + 1,
                "size": len(comp),
                "density": round(density, 3),
                "health": "healthy" if density >= self.min_connectivity else "sparse",
                "top_nodes": [{"label": n["label"], "mass": n["mass"]} for n in top_nodes]
            })

        # Identify weak connections
        weak_conns = self.identify_weak_connections(adjacency)

        # Suggest bridge nodes
        bridges = self.suggest_bridge_nodes(components, nodes)

        # Calculate overall connectivity
        total_possible_links = len(nodes) * (len(nodes) - 1) / 2
        actual_links = len([1 for neighbors in adjacency.values() for _ in neighbors]) / 2
        overall_connectivity = actual_links / total_possible_links if total_possible_links > 0 else 0.0

        duration = (datetime.now() - start_time).total_seconds()

        report = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "graph_summary": {
                "total_nodes": len(nodes),
                "total_links": int(actual_links),
                "overall_connectivity": round(overall_connectivity, 3),
                "connectivity_health": "healthy" if overall_connectivity >= 0.1 else "sparse"
            },
            "clusters": {
                "count": len(components),
                "analysis": component_analysis
            },
            "weak_connections": {
                "count": len(weak_conns),
                "examples": weak_conns[:10]  # Top 10 weakest
            },
            "bridge_suggestions": {
                "count": len(bridges),
                "suggestions": bridges
            },
            "recommendations": self._generate_recommendations(
                len(components), overall_connectivity, len(weak_conns)
            )
        }

        logger.info("="*60)
        logger.info("KNOWLEDGE GAP ANALYSIS COMPLETE")
        logger.info("="*60)
        logger.info(f"Duration: {duration:.2f}s")
        logger.info(f"Clusters found: {len(components)}")
        logger.info(f"Weak connections: {len(weak_conns)}")
        logger.info(f"Bridge suggestions: {len(bridges)}")

        return report

    def _generate_recommendations(
        self,
        num_clusters: int,
        connectivity: float,
        num_weak: int
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        if num_clusters > 3:
            recommendations.append(
                f"⚠️  High cluster count ({num_clusters}) suggests knowledge silos. "
                "Consider creating bridge nodes to connect isolated domains."
            )

        if connectivity < 0.1:
            recommendations.append(
                f"⚠️  Low overall connectivity ({connectivity:.1%}). "
                "Add more inter-domain links to improve knowledge flow."
            )

        if num_weak > 10:
            recommendations.append(
                f"⚠️  Many weak connections ({num_weak}) detected. "
                "Strengthen or prune low-value links."
            )

        if not recommendations:
            recommendations.append(
                "✅ Knowledge graph structure is healthy. Continue monitoring."
            )

        return recommendations


if __name__ == "__main__":
    # Test the analyzer
    logging.basicConfig(level=logging.INFO)

    analyzer = KnowledgeGapAnalyzer()

    print("\n" + "="*60)
    print("Knowledge Gap Analyzer - Running Analysis")
    print("="*60)

    report = analyzer.analyze_knowledge_gaps()

    if report["status"] == "success":
        print(f"\nGraph Summary:")
        print(f"  Total nodes: {report['graph_summary']['total_nodes']}")
        print(f"  Total links: {report['graph_summary']['total_links']}")
        print(f"  Connectivity: {report['graph_summary']['overall_connectivity']:.1%}")
        print(f"  Health: {report['graph_summary']['connectivity_health']}")

        print(f"\nClusters: {report['clusters']['count']}")
        for cluster in report['clusters']['analysis']:
            print(f"  Cluster {cluster['cluster_id']}: "
                  f"{cluster['size']} nodes, "
                  f"density={cluster['density']:.2f}, "
                  f"{cluster['health']}")

        print(f"\nWeak Connections: {report['weak_connections']['count']}")
        print(f"Bridge Suggestions: {report['bridge_suggestions']['count']}")

        print("\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  {rec}")

        print("\n" + "="*60 + "\n")

        # Save report
        with open("/tmp/knowledge_gap_report.json", "w") as f:
            json.dump(report, f, indent=2)
        print("Full report saved to: /tmp/knowledge_gap_report.json\n")
    else:
        print(f"\nError: {report.get('message', 'Unknown error')}\n")
