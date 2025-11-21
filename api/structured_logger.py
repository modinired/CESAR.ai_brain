"""
Structured JSON Logging for Production
=======================================

Provides production-grade structured logging with:
- JSON output for log aggregation (ELK, Datadog, Splunk)
- Request tracing with correlation IDs
- Performance tracking
- Security event logging
- Contextual metadata

Benefits:
- Easy to parse and query
- Integrates with monitoring tools
- Tracks requests across services
- Auditable security events
"""

import os
import sys
import json
import logging
import traceback
from datetime import datetime
from typing import Optional, Dict, Any
from contextvars import ContextVar

# Context variables for request tracking
request_id_ctx: ContextVar[str] = ContextVar('request_id', default='')
user_id_ctx: ContextVar[str] = ContextVar('user_id', default='')

# =============================================================================
# CONFIGURATION
# =============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "json")  # json or text
ENABLE_FILE_LOGGING = os.getenv("LOG_FILE_ENABLED", "false").lower() == "true"
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "/var/log/mcp/app.log")
SERVICE_NAME = os.getenv("SERVICE_NAME", "multi-agent-learning-ecosystem")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


# =============================================================================
# CUSTOM JSON FORMATTER
# =============================================================================

class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Output Format:
    {
        "timestamp": "2024-01-15T10:30:45.123Z",
        "level": "INFO",
        "logger": "MainAPI",
        "message": "Request processed successfully",
        "request_id": "abc-123-def",
        "user_id": "user_001",
        "service": "multi-agent-learning-ecosystem",
        "environment": "production",
        "metadata": {...}
    }
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Python logging record

        Returns:
            JSON string
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": SERVICE_NAME,
            "environment": ENVIRONMENT,
        }

        # Add request context if available
        request_id = request_id_ctx.get()
        if request_id:
            log_data["request_id"] = request_id

        user_id = user_id_ctx.get()
        if user_id:
            log_data["user_id"] = user_id

        # Add file location
        log_data["file"] = f"{record.filename}:{record.lineno}"
        log_data["function"] = record.funcName

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Add custom metadata from extra fields
        if hasattr(record, 'metadata'):
            log_data["metadata"] = record.metadata

        # Add specific event types
        if hasattr(record, 'event_type'):
            log_data["event_type"] = record.event_type

        # Performance metrics
        if hasattr(record, 'duration_ms'):
            log_data["duration_ms"] = record.duration_ms

        # Security events
        if hasattr(record, 'security_event'):
            log_data["security"] = record.security_event

        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """
    Human-readable text formatter for development.

    Output Format:
    2024-01-15 10:30:45 INFO [MainAPI] Request processed successfully (request_id=abc-123)
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as human-readable text."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        message = record.getMessage()

        # Add request ID if available
        request_id = request_id_ctx.get()
        context = f" (request_id={request_id})" if request_id else ""

        log_line = f"{timestamp} {record.levelname:7s} [{record.name}] {message}{context}"

        # Add exception if present
        if record.exc_info:
            log_line += "\n" + "".join(traceback.format_exception(*record.exc_info))

        return log_line


# =============================================================================
# LOGGER SETUP
# =============================================================================

def setup_logging() -> logging.Logger:
    """
    Configure root logger with structured logging.

    Returns:
        Configured root logger
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)

    # Remove existing handlers
    root_logger.handlers = []

    # Choose formatter based on configuration
    if LOG_FORMAT == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if ENABLE_FILE_LOGGING:
        try:
            # Create log directory if it doesn't exist
            os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

            file_handler = logging.FileHandler(LOG_FILE_PATH)
            file_handler.setFormatter(JSONFormatter())  # Always use JSON for files
            root_logger.addHandler(file_handler)

            root_logger.info(f"File logging enabled: {LOG_FILE_PATH}")
        except Exception as e:
            root_logger.warning(f"Failed to enable file logging: {e}")

    return root_logger


# =============================================================================
# STRUCTURED LOGGING HELPERS
# =============================================================================

def log_request(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: Optional[str] = None
):
    """
    Log HTTP request with structured metadata.

    Args:
        logger: Logger instance
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
        user_id: Optional user ID
    """
    level = logging.INFO if status_code < 400 else logging.WARNING

    logger.log(
        level,
        f"{method} {path} {status_code}",
        extra={
            "event_type": "http_request",
            "metadata": {
                "http_method": method,
                "http_path": path,
                "http_status": status_code,
                "user_id": user_id
            },
            "duration_ms": duration_ms
        }
    )


def log_security_event(
    logger: logging.Logger,
    event_type: str,
    details: Dict[str, Any],
    severity: str = "INFO"
):
    """
    Log security event with structured metadata.

    Args:
        logger: Logger instance
        event_type: Type of security event (auth_failure, rate_limit, etc.)
        details: Event details
        severity: Log severity (INFO, WARNING, ERROR)
    """
    level = getattr(logging, severity.upper())

    logger.log(
        level,
        f"Security event: {event_type}",
        extra={
            "event_type": "security",
            "security_event": {
                "type": event_type,
                **details
            }
        }
    )


def log_mcp_task(
    logger: logging.Logger,
    mcp_system: str,
    task_type: str,
    status: str,
    duration_ms: float,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Log MCP task execution with structured metadata.

    Args:
        logger: Logger instance
        mcp_system: MCP system name (FinPsy, Pydini, etc.)
        task_type: Task type
        status: Task status (success, failure)
        duration_ms: Task duration in milliseconds
        metadata: Optional task metadata
    """
    level = logging.INFO if status == "success" else logging.ERROR

    logger.log(
        level,
        f"MCP task {status}: {mcp_system}/{task_type}",
        extra={
            "event_type": "mcp_task",
            "metadata": {
                "mcp_system": mcp_system,
                "task_type": task_type,
                "status": status,
                **(metadata or {})
            },
            "duration_ms": duration_ms
        }
    )


def log_database_query(
    logger: logging.Logger,
    query_type: str,
    table: str,
    duration_ms: float,
    rows_affected: Optional[int] = None
):
    """
    Log database query with performance metrics.

    Args:
        logger: Logger instance
        query_type: Type of query (SELECT, INSERT, UPDATE, DELETE)
        table: Database table
        duration_ms: Query duration in milliseconds
        rows_affected: Number of rows affected
    """
    logger.debug(
        f"Database query: {query_type} {table}",
        extra={
            "event_type": "database_query",
            "metadata": {
                "query_type": query_type,
                "table": table,
                "rows_affected": rows_affected
            },
            "duration_ms": duration_ms
        }
    )


def log_performance_metric(
    logger: logging.Logger,
    metric_name: str,
    value: float,
    unit: str = "ms",
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Log performance metric.

    Args:
        logger: Logger instance
        metric_name: Name of the metric
        value: Metric value
        unit: Unit of measurement (ms, bytes, count)
        metadata: Optional metadata
    """
    logger.info(
        f"Performance metric: {metric_name} = {value}{unit}",
        extra={
            "event_type": "performance_metric",
            "metadata": {
                "metric_name": metric_name,
                "value": value,
                "unit": unit,
                **(metadata or {})
            }
        }
    )


# =============================================================================
# REQUEST TRACING MIDDLEWARE
# =============================================================================

import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured request logging with tracing.

    Automatically:
    - Generates request IDs
    - Logs all HTTP requests
    - Tracks request duration
    - Adds request context to logs
    """

    async def dispatch(self, request: Request, call_next):
        """Process request and log with structured metadata."""
        # Generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_ctx.set(request_id)

        # Extract user ID from auth (if available)
        # This would be populated by auth middleware
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            user_id_ctx.set(user_id)

        # Track request timing
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Log request
        logger = logging.getLogger("RequestLogger")
        log_request(
            logger,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            user_id=user_id
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response


# =============================================================================
# USAGE EXAMPLES
# =============================================================================

LOGGING_EXAMPLES = """
# Basic Usage
logger = logging.getLogger(__name__)
logger.info("Application started")
logger.error("Error occurred", extra={"metadata": {"error_code": "E001"}})

# Request Logging
log_request(logger, "GET", "/api/users", 200, 45.2, user_id="user_123")

# Security Logging
log_security_event(
    logger,
    event_type="auth_failure",
    details={"username": "admin", "ip": "1.2.3.4"},
    severity="WARNING"
)

# MCP Task Logging
log_mcp_task(
    logger,
    mcp_system="FinPsy",
    task_type="sentiment_analysis",
    status="success",
    duration_ms=150.5,
    metadata={"ticker": "AAPL"}
)

# Database Query Logging
log_database_query(
    logger,
    query_type="SELECT",
    table="users",
    duration_ms=5.2,
    rows_affected=10
)

# Performance Metrics
log_performance_metric(
    logger,
    metric_name="vector_search_latency",
    value=23.5,
    unit="ms",
    metadata={"backend": "faiss"}
)
"""

# Initialize logging on module import
setup_logging()
