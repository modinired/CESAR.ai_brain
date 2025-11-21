"""
Prometheus Monitoring for MCP Systems
======================================

Exports metrics for all MCP systems, API endpoints, and infrastructure.

Features:
- Request/response metrics
- Task processing metrics
- Agent performance metrics
- System health metrics
- Custom business metrics
"""

import os
import time
import logging
from typing import Optional, Callable
from functools import wraps

try:
    from prometheus_client import (
        Counter, Histogram, Gauge, Info,
        CollectorRegistry, generate_latest,
        CONTENT_TYPE_LATEST, multiprocess, CollectorRegistry as Registry
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logging.warning("prometheus_client not installed. Metrics disabled.")

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PrometheusMetrics")

# Configuration
METRICS_ENABLED = os.getenv("METRICS_ENABLED", "true").lower() == "true"
METRICS_PORT = int(os.getenv("METRICS_PORT", "9090"))


# =============================================================================
# METRIC DEFINITIONS
# =============================================================================

if PROMETHEUS_AVAILABLE and METRICS_ENABLED:
    # Registry
    registry = Registry()

    # =========================================================================
    # HTTP REQUEST METRICS
    # =========================================================================

    http_requests_total = Counter(
        'http_requests_total',
        'Total HTTP requests',
        ['method', 'endpoint', 'status_code'],
        registry=registry
    )

    http_request_duration_seconds = Histogram(
        'http_request_duration_seconds',
        'HTTP request latency',
        ['method', 'endpoint'],
        registry=registry
    )

    http_requests_in_progress = Gauge(
        'http_requests_in_progress',
        'HTTP requests currently in progress',
        ['method', 'endpoint'],
        registry=registry
    )

    # =========================================================================
    # MCP TASK METRICS
    # =========================================================================

    mcp_tasks_total = Counter(
        'mcp_tasks_total',
        'Total MCP tasks processed',
        ['mcp_system', 'task_type', 'status'],
        registry=registry
    )

    mcp_task_duration_seconds = Histogram(
        'mcp_task_duration_seconds',
        'MCP task processing duration',
        ['mcp_system', 'task_type'],
        buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
        registry=registry
    )

    mcp_tasks_in_progress = Gauge(
        'mcp_tasks_in_progress',
        'MCP tasks currently in progress',
        ['mcp_system'],
        registry=registry
    )

    mcp_task_errors_total = Counter(
        'mcp_task_errors_total',
        'Total MCP task errors',
        ['mcp_system', 'task_type', 'error_type'],
        registry=registry
    )

    # =========================================================================
    # AGENT METRICS
    # =========================================================================

    agent_tasks_completed = Counter(
        'agent_tasks_completed_total',
        'Total tasks completed by agent',
        ['agent_id', 'mcp_system'],
        registry=registry
    )

    agent_performance_score = Gauge(
        'agent_performance_score',
        'Agent performance score',
        ['agent_id', 'mcp_system'],
        registry=registry
    )

    agent_skill_level = Gauge(
        'agent_skill_level',
        'Agent skill level',
        ['agent_id', 'skill_name'],
        registry=registry
    )

    # =========================================================================
    # VECTOR MEMORY METRICS
    # =========================================================================

    vector_memory_queries_total = Counter(
        'vector_memory_queries_total',
        'Total vector memory queries',
        ['mcp_system', 'backend'],  # backend: faiss or postgres
        registry=registry
    )

    vector_memory_query_duration_seconds = Histogram(
        'vector_memory_query_duration_seconds',
        'Vector memory query duration',
        ['backend'],
        buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
        registry=registry
    )

    vector_memory_size = Gauge(
        'vector_memory_size',
        'Number of vectors in memory',
        ['backend', 'mcp_system'],
        registry=registry
    )

    # =========================================================================
    # AUTHENTICATION METRICS
    # =========================================================================

    auth_attempts_total = Counter(
        'auth_attempts_total',
        'Total authentication attempts',
        ['method', 'status'],  # method: jwt/api_key, status: success/failure
        registry=registry
    )

    active_sessions = Gauge(
        'active_sessions',
        'Number of active user sessions',
        ['tenant_id'],
        registry=registry
    )

    # =========================================================================
    # RATE LIMITING METRICS
    # =========================================================================

    rate_limit_exceeded_total = Counter(
        'rate_limit_exceeded_total',
        'Total rate limit violations',
        ['endpoint', 'user_type'],  # user_type: user/api_key/ip
        registry=registry
    )

    rate_limit_remaining = Gauge(
        'rate_limit_remaining',
        'Remaining requests in rate limit window',
        ['key'],
        registry=registry
    )

    # =========================================================================
    # PLUGIN METRICS
    # =========================================================================

    plugins_loaded = Gauge(
        'plugins_loaded',
        'Number of loaded plugins',
        registry=registry
    )

    plugin_execution_duration_seconds = Histogram(
        'plugin_execution_duration_seconds',
        'Plugin execution duration',
        ['plugin_name'],
        registry=registry
    )

    # =========================================================================
    # SKILLFORGE METRICS
    # =========================================================================

    skills_discovered_total = Counter(
        'skills_discovered_total',
        'Total skills discovered by SkillForge',
        registry=registry
    )

    skills_deployed_total = Counter(
        'skills_deployed_total',
        'Total skills auto-deployed',
        ['confidence_level'],  # low/medium/high
        registry=registry
    )

    skill_confidence_score = Histogram(
        'skill_confidence_score',
        'Distribution of skill confidence scores',
        buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99],
        registry=registry
    )

    # =========================================================================
    # SYSTEM HEALTH METRICS
    # =========================================================================

    system_health = Gauge(
        'system_health',
        'System health status (1=healthy, 0=unhealthy)',
        ['component'],  # component: api/database/redis/etc
        registry=registry
    )

    database_connections = Gauge(
        'database_connections',
        'Number of database connections',
        ['pool', 'state'],  # state: active/idle
        registry=registry
    )

    redis_connections = Gauge(
        'redis_connections',
        'Number of Redis connections',
        registry=registry
    )

    # =========================================================================
    # BUSINESS METRICS
    # =========================================================================

    learning_materials_processed = Counter(
        'learning_materials_processed_total',
        'Total learning materials processed',
        ['material_type'],
        registry=registry
    )

    reflections_created = Counter(
        'reflections_created_total',
        'Total learning reflections created',
        ['agent_id'],
        registry=registry
    )

    workflows_executed = Counter(
        'workflows_executed_total',
        'Total workflow executions',
        ['workflow_name', 'status'],
        registry=registry
    )

    # =========================================================================
    # SYSTEM INFO
    # =========================================================================

    system_info = Info(
        'mcp_system',
        'MCP System information',
        registry=registry
    )

    system_info.info({
        'version': '2.0.0',
        'environment': os.getenv('ENVIRONMENT', 'development'),
        'mcp_systems': '6',  # FinPsy, PydiniRed, Lex, Inno, Creative, Edu
        'total_agents': '35'
    })


# =============================================================================
# MIDDLEWARE FOR AUTOMATIC METRICS
# =============================================================================

class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically collect HTTP metrics
    """

    def __init__(self, app):
        super().__init__(app)
        self.metrics_enabled = PROMETHEUS_AVAILABLE and METRICS_ENABLED

    async def dispatch(self, request: Request, call_next):
        """Process request and collect metrics"""

        if not self.metrics_enabled:
            return await call_next(request)

        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        endpoint = request.url.path

        # Track in-progress requests
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

        # Time the request
        start_time = time.time()

        try:
            response = await call_next(request)
            status_code = response.status_code

            # Record metrics
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()

            duration = time.time() - start_time
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)

            return response

        except Exception as e:
            # Record error
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=500
            ).inc()

            raise

        finally:
            # Decrement in-progress
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()


# =============================================================================
# DECORATORS FOR FUNCTION METRICS
# =============================================================================

def track_mcp_task(mcp_system: str, task_type: str):
    """
    Decorator to track MCP task execution

    Usage:
        @track_mcp_task("finpsy", "market_analysis")
        def process_market_analysis(data):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not (PROMETHEUS_AVAILABLE and METRICS_ENABLED):
                return func(*args, **kwargs)

            # Track in-progress
            mcp_tasks_in_progress.labels(mcp_system=mcp_system).inc()

            start_time = time.time()
            status = "success"

            try:
                result = func(*args, **kwargs)
                return result

            except Exception as e:
                status = "error"
                error_type = type(e).__name__

                mcp_task_errors_total.labels(
                    mcp_system=mcp_system,
                    task_type=task_type,
                    error_type=error_type
                ).inc()

                raise

            finally:
                # Record completion
                duration = time.time() - start_time

                mcp_tasks_total.labels(
                    mcp_system=mcp_system,
                    task_type=task_type,
                    status=status
                ).inc()

                mcp_task_duration_seconds.labels(
                    mcp_system=mcp_system,
                    task_type=task_type
                ).observe(duration)

                mcp_tasks_in_progress.labels(mcp_system=mcp_system).dec()

        return wrapper

    return decorator


def track_agent_task(agent_id: str, mcp_system: str):
    """
    Decorator to track agent task execution

    Usage:
        @track_agent_task("agent_001", "finpsy")
        def execute_task(task):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not (PROMETHEUS_AVAILABLE and METRICS_ENABLED):
                return func(*args, **kwargs)

            try:
                result = func(*args, **kwargs)

                # Increment completed tasks
                agent_tasks_completed.labels(
                    agent_id=agent_id,
                    mcp_system=mcp_system
                ).inc()

                return result

            except Exception:
                raise

        return wrapper

    return decorator


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def record_vector_query(backend: str, mcp_system: str, duration: float):
    """Record vector memory query metrics"""
    if not (PROMETHEUS_AVAILABLE and METRICS_ENABLED):
        return

    vector_memory_queries_total.labels(
        mcp_system=mcp_system,
        backend=backend
    ).inc()

    vector_memory_query_duration_seconds.labels(backend=backend).observe(duration)


def update_agent_performance(agent_id: str, mcp_system: str, score: float):
    """Update agent performance score"""
    if not (PROMETHEUS_AVAILABLE and METRICS_ENABLED):
        return

    agent_performance_score.labels(
        agent_id=agent_id,
        mcp_system=mcp_system
    ).set(score)


def update_agent_skill(agent_id: str, skill_name: str, level: float):
    """Update agent skill level"""
    if not (PROMETHEUS_AVAILABLE and METRICS_ENABLED):
        return

    agent_skill_level.labels(
        agent_id=agent_id,
        skill_name=skill_name
    ).set(level)


def record_auth_attempt(method: str, success: bool):
    """Record authentication attempt"""
    if not (PROMETHEUS_AVAILABLE and METRICS_ENABLED):
        return

    status = "success" if success else "failure"
    auth_attempts_total.labels(method=method, status=status).inc()


def record_rate_limit_exceeded(endpoint: str, user_type: str):
    """Record rate limit violation"""
    if not (PROMETHEUS_AVAILABLE and METRICS_ENABLED):
        return

    rate_limit_exceeded_total.labels(
        endpoint=endpoint,
        user_type=user_type
    ).inc()


def record_skill_discovery(confidence: float, deployed: bool = False):
    """Record SkillForge skill discovery"""
    if not (PROMETHEUS_AVAILABLE and METRICS_ENABLED):
        return

    skills_discovered_total.inc()
    skill_confidence_score.observe(confidence)

    if deployed:
        if confidence >= 0.9:
            level = "high"
        elif confidence >= 0.7:
            level = "medium"
        else:
            level = "low"

        skills_deployed_total.labels(confidence_level=level).inc()


def update_system_health(component: str, healthy: bool):
    """Update system health status"""
    if not (PROMETHEUS_AVAILABLE and METRICS_ENABLED):
        return

    system_health.labels(component=component).set(1 if healthy else 0)


def metrics_endpoint() -> Response:
    """
    Generate Prometheus metrics endpoint response

    Returns:
        Response with metrics in Prometheus format
    """
    if not (PROMETHEUS_AVAILABLE and METRICS_ENABLED):
        return Response(
            content="Metrics disabled",
            media_type="text/plain"
        )

    metrics_data = generate_latest(registry)

    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST
    )


# =============================================================================
# INITIALIZATION
# =============================================================================

def initialize_metrics():
    """Initialize metrics with default values"""
    if not (PROMETHEUS_AVAILABLE and METRICS_ENABLED):
        logger.warning("Metrics disabled")
        return

    # Set initial health status
    components = ["api", "database", "redis", "faiss", "postgres"]
    for component in components:
        update_system_health(component, True)

    logger.info("Prometheus metrics initialized")


# Initialize on module load
if PROMETHEUS_AVAILABLE and METRICS_ENABLED:
    initialize_metrics()
