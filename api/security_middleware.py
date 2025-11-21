"""
Security Headers Middleware for MCP API
========================================

Implements production-grade security headers to protect against common web
vulnerabilities (OWASP Top 10).

Security Headers Implemented:
- HSTS (HTTP Strict Transport Security)
- CSP (Content Security Policy)
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Referrer-Policy
- Permissions-Policy
"""

import os
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all HTTP responses.

    Protects against:
    - Clickjacking (X-Frame-Options)
    - XSS attacks (CSP, X-XSS-Protection)
    - MIME sniffing (X-Content-Type-Options)
    - Man-in-the-middle attacks (HSTS)
    - Information leakage (Referrer-Policy)
    """

    def __init__(self, app, enable_hsts: bool = True, enable_csp: bool = True):
        """
        Initialize security headers middleware.

        Args:
            app: FastAPI application instance
            enable_hsts: Enable HSTS header (requires HTTPS)
            enable_csp: Enable Content Security Policy
        """
        super().__init__(app)
        self.enable_hsts = enable_hsts and os.getenv("FORCE_HTTPS", "false").lower() == "true"
        self.enable_csp = enable_csp and os.getenv("CSP_ENABLED", "true").lower() == "true"

        # Load CSP policy from environment
        self.csp_policy = os.getenv(
            "CSP_POLICY",
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none';"
        )

        # HSTS configuration
        self.hsts_max_age = int(os.getenv("HSTS_MAX_AGE", "31536000"))  # 1 year

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add security headers to response.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain

        Returns:
            Response with security headers added
        """
        response = await call_next(request)

        # X-Frame-Options: Prevent clickjacking
        # DENY = Page cannot be displayed in a frame
        response.headers["X-Frame-Options"] = "DENY"

        # X-Content-Type-Options: Prevent MIME sniffing
        # nosniff = Browser must respect Content-Type header
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection: Enable browser XSS filter
        # 1; mode=block = Enable XSS filter, block page if attack detected
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy: Control referrer information
        # strict-origin-when-cross-origin = Send origin for same-origin, only origin for HTTPS->HTTP
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy: Disable dangerous browser features
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )

        # HSTS: Force HTTPS (only in production with HTTPS)
        if self.enable_hsts:
            response.headers["Strict-Transport-Security"] = (
                f"max-age={self.hsts_max_age}; includeSubDomains; preload"
            )

        # Content Security Policy: Prevent XSS and injection attacks
        if self.enable_csp:
            response.headers["Content-Security-Policy"] = self.csp_policy

        # X-Powered-By: Remove server fingerprinting
        # (Some frameworks add this by default)
        for header in ("X-Powered-By", "Server"):
            if header in response.headers:
                del response.headers[header]

        return response


def configure_security_headers(app, enable_hsts: bool = None, enable_csp: bool = None):
    """
    Configure and add security headers middleware to FastAPI app.

    Usage:
        from api.security_middleware import configure_security_headers

        app = FastAPI()
        configure_security_headers(app)

    Args:
        app: FastAPI application instance
        enable_hsts: Override HSTS setting (default: from env FORCE_HTTPS)
        enable_csp: Override CSP setting (default: from env CSP_ENABLED)
    """
    # Determine HSTS setting
    if enable_hsts is None:
        enable_hsts = os.getenv("HSTS_ENABLED", "false").lower() == "true"

    # Determine CSP setting
    if enable_csp is None:
        enable_csp = os.getenv("CSP_ENABLED", "true").lower() == "true"

    # Add middleware
    app.add_middleware(SecurityHeadersMiddleware, enable_hsts=enable_hsts, enable_csp=enable_csp)

    return app


# =============================================================================
# SECURITY HEADER EXAMPLES & DOCUMENTATION
# =============================================================================

SECURITY_HEADERS_INFO = {
    "headers": {
        "Strict-Transport-Security": {
            "purpose": "Force HTTPS connections",
            "protection": "Man-in-the-middle attacks, protocol downgrade attacks",
            "value": "max-age=31536000; includeSubDomains; preload",
            "notes": "Only enabled when FORCE_HTTPS=true"
        },
        "Content-Security-Policy": {
            "purpose": "Control resource loading to prevent XSS",
            "protection": "XSS, code injection, data injection",
            "value": "Configurable via CSP_POLICY env variable",
            "notes": "Default allows self + inline scripts (adjust for production)"
        },
        "X-Frame-Options": {
            "purpose": "Prevent page from being framed",
            "protection": "Clickjacking attacks",
            "value": "DENY",
            "notes": "Prevents all framing (use SAMEORIGIN if needed)"
        },
        "X-Content-Type-Options": {
            "purpose": "Prevent MIME type sniffing",
            "protection": "MIME confusion attacks",
            "value": "nosniff",
            "notes": "Browser must respect Content-Type header"
        },
        "X-XSS-Protection": {
            "purpose": "Enable browser XSS filter",
            "protection": "Reflected XSS attacks",
            "value": "1; mode=block",
            "notes": "Legacy header, CSP is preferred"
        },
        "Referrer-Policy": {
            "purpose": "Control referrer information leakage",
            "protection": "Information disclosure",
            "value": "strict-origin-when-cross-origin",
            "notes": "Balances privacy and functionality"
        },
        "Permissions-Policy": {
            "purpose": "Disable dangerous browser features",
            "protection": "Unauthorized access to device features",
            "value": "geolocation=(), microphone=(), camera=(), ...",
            "notes": "Denies all sensitive features by default"
        }
    },
    "environment_variables": {
        "FORCE_HTTPS": "Enable HTTPS enforcement (default: false)",
        "HSTS_ENABLED": "Enable HSTS header (default: false)",
        "HSTS_MAX_AGE": "HSTS max age in seconds (default: 31536000 = 1 year)",
        "CSP_ENABLED": "Enable Content Security Policy (default: true)",
        "CSP_POLICY": "Custom CSP policy string"
    },
    "owasp_coverage": [
        "A01:2021 - Broken Access Control (X-Frame-Options)",
        "A03:2021 - Injection (CSP)",
        "A05:2021 - Security Misconfiguration (All headers)",
        "A06:2021 - Vulnerable Components (X-Content-Type-Options)"
    ]
}


def get_security_info() -> dict:
    """
    Get information about configured security headers.

    Returns:
        Dictionary with security header documentation
    """
    return SECURITY_HEADERS_INFO
