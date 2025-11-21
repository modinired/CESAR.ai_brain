"""
Monitoring Module for MCP Systems
==================================

Exports Prometheus metrics for monitoring and observability.
"""

from .prometheus import (
    # Middleware
    PrometheusMiddleware,

    # Decorators
    track_mcp_task,
    track_agent_task,

    # Helper functions
    record_vector_query,
    update_agent_performance,
    update_agent_skill,
    record_auth_attempt,
    record_rate_limit_exceeded,
    record_skill_discovery,
    update_system_health,
    metrics_endpoint,
    initialize_metrics,

    # Configuration
    PROMETHEUS_AVAILABLE,
    METRICS_ENABLED,
    METRICS_PORT
)

__all__ = [
    "PrometheusMiddleware",
    "track_mcp_task",
    "track_agent_task",
    "record_vector_query",
    "update_agent_performance",
    "update_agent_skill",
    "record_auth_attempt",
    "record_rate_limit_exceeded",
    "record_skill_discovery",
    "update_system_health",
    "metrics_endpoint",
    "initialize_metrics",
    "PROMETHEUS_AVAILABLE",
    "METRICS_ENABLED",
    "METRICS_PORT"
]
