"""
Rate Limiting for MCP API
==========================

Implements token bucket rate limiting with Redis backend
Protects API from abuse and ensures fair usage
"""

import os
import time
import hashlib
from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as aioredis

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds


class RateLimiter:
    """
    Token bucket rate limiter with Redis backend
    """

    def __init__(self, redis_url: str = REDIS_URL):
        self.redis_url = redis_url
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self):
        """Connect to Redis"""
        if self._redis is None:
            self._redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )

    async def close(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()

    async def is_allowed(
        self,
        key: str,
        max_requests: int = RATE_LIMIT_REQUESTS,
        window: int = RATE_LIMIT_WINDOW
    ) -> tuple[bool, dict]:
        """
        Check if request is allowed under rate limit

        Args:
            key: Unique identifier (e.g., user_id, IP address)
            max_requests: Maximum requests allowed in window
            window: Time window in seconds

        Returns:
            Tuple of (is_allowed, metadata)
        """
        await self.connect()

        current_time = int(time.time())
        window_start = current_time - window

        # Redis key for this rate limit
        redis_key = f"rate_limit:{key}"

        # Use Redis sorted set to track requests in time window
        pipeline = self._redis.pipeline()

        # Remove old entries outside window
        pipeline.zremrangebyscore(redis_key, 0, window_start)

        # Count requests in current window
        pipeline.zcard(redis_key)

        # Add current request
        pipeline.zadd(redis_key, {str(current_time): current_time})

        # Set expiration
        pipeline.expire(redis_key, window)

        results = await pipeline.execute()

        # Get request count (before adding current request)
        request_count = results[1]

        # Calculate remaining requests
        remaining = max(0, max_requests - request_count - 1)

        # Check if allowed
        is_allowed = request_count < max_requests

        metadata = {
            "limit": max_requests,
            "remaining": remaining,
            "reset": current_time + window,
            "retry_after": window if not is_allowed else None
        }

        return is_allowed, metadata

    async def get_rate_limit_key(self, request: Request) -> str:
        """
        Generate rate limit key from request

        Prioritizes:
        1. Authenticated user ID
        2. API key
        3. IP address
        """
        # Check for authenticated user
        if hasattr(request.state, "user"):
            user = request.state.user
            return f"user:{user.user_id}"

        # Check for API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            # Hash API key for privacy
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
            return f"api_key:{key_hash}"

        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        return f"ip:{ip}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting all requests
    """

    def __init__(self, app, rate_limiter: RateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter

        # Endpoints that bypass rate limiting
        self.whitelist = [
            "/health",
            "/docs",
            "/openapi.json",
            "/api/auth/demo-credentials"
        ]

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""

        # Skip rate limiting for whitelisted endpoints
        if request.url.path in self.whitelist:
            return await call_next(request)

        # Get rate limit key
        key = await self.rate_limiter.get_rate_limit_key(request)

        # Determine rate limit based on endpoint
        max_requests, window = self._get_limits_for_endpoint(request.url.path)

        # Check rate limit
        is_allowed, metadata = await self.rate_limiter.is_allowed(
            key,
            max_requests=max_requests,
            window=window
        )

        # Set rate limit headers
        response = None

        if is_allowed:
            response = await call_next(request)
        else:
            # Rate limit exceeded
            response = HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded. Try again in {metadata['retry_after']} seconds.",
                    "limit": metadata["limit"],
                    "retry_after": metadata["retry_after"]
                }
            )
            # Convert to response
            from fastapi.responses import JSONResponse
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=response.detail,
                headers={"Retry-After": str(metadata["retry_after"])}
            )

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(metadata["limit"])
        response.headers["X-RateLimit-Remaining"] = str(metadata["remaining"])
        response.headers["X-RateLimit-Reset"] = str(metadata["reset"])

        return response

    def _get_limits_for_endpoint(self, path: str) -> tuple[int, int]:
        """
        Get rate limits for specific endpoint

        Returns:
            Tuple of (max_requests, window_seconds)
        """
        # Higher limits for expensive MCP operations
        if "/api/mcp/" in path:
            # MCP endpoints: 30 requests per minute
            return 30, 60

        # Authentication endpoints: 5 requests per minute
        if "/api/auth/" in path:
            return 5, 60

        # Default: 60 requests per minute
        return 60, 60


# =============================================================================
# DECORATOR FOR MANUAL RATE LIMITING
# =============================================================================

from functools import wraps


def rate_limit(max_requests: int = 10, window: int = 60):
    """
    Decorator for manual rate limiting on specific endpoints

    Usage:
        @app.get("/expensive-operation")
        @rate_limit(max_requests=5, window=60)
        async def expensive_op(request: Request):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                request = kwargs.get("request")

            if request:
                limiter = RateLimiter()
                key = await limiter.get_rate_limit_key(request)
                is_allowed, metadata = await limiter.is_allowed(
                    key,
                    max_requests=max_requests,
                    window=window
                )

                if not is_allowed:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded. Try again in {metadata['retry_after']} seconds."
                    )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def get_rate_limit_status(key: str) -> dict:
    """
    Get current rate limit status for a key

    Args:
        key: Rate limit key

    Returns:
        Dict with current rate limit status
    """
    limiter = RateLimiter()
    await limiter.connect()

    redis_key = f"rate_limit:{key}"
    current_time = int(time.time())
    window_start = current_time - RATE_LIMIT_WINDOW

    # Count requests in window
    count = await limiter._redis.zcount(redis_key, window_start, current_time)

    remaining = max(0, RATE_LIMIT_REQUESTS - count)

    return {
        "key": key,
        "requests_used": count,
        "requests_remaining": remaining,
        "limit": RATE_LIMIT_REQUESTS,
        "window_seconds": RATE_LIMIT_WINDOW,
        "reset_at": current_time + RATE_LIMIT_WINDOW
    }
