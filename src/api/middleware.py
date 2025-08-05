"""Middleware for API security, logging, and rate limiting."""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from typing import Dict, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        """Add security headers to response."""
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'"
        )

        # Remove server header
        if "Server" in response.headers:
            del response.headers["Server"]

        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests and responses."""

    async def dispatch(self, request: Request, call_next):
        """Log request and response information."""
        start_time = time.time()

        # Generate correlation ID
        correlation_id = f"req_{int(start_time * 1000000)}"

        # Log request
        logger.info(
            "Request started",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
            }
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Process-Time"] = str(round(process_time, 4))

            # Log response
            logger.info(
                "Request completed",
                extra={
                    "correlation_id": correlation_id,
                    "status_code": response.status_code,
                    "process_time_seconds": process_time,
                }
            )

            return response

        except Exception as e:
            process_time = time.time() - start_time

            logger.exception(
                "Request failed",
                extra={
                    "correlation_id": correlation_id,
                    "error": str(e),
                    "process_time_seconds": process_time,
                }
            )

            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": 500,
                        "message": "Internal server error",
                        "correlation_id": correlation_id
                    }
                },
                headers={"X-Correlation-ID": correlation_id}
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using sliding window algorithm."""

    def __init__(self, app, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        """
        Initialize rate limiter.
        
        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests per minute per IP
            requests_per_hour: Maximum requests per hour per IP
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour

        # In-memory storage for request counts
        # In production, this should use Redis or similar
        self.minute_requests: Dict[str, deque] = defaultdict(deque)
        self.hour_requests: Dict[str, deque] = defaultdict(deque)

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded IP (behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"

    def _cleanup_old_requests(self, request_queue: deque, window_seconds: int) -> None:
        """Remove requests older than the window."""
        now = time.time()
        cutoff = now - window_seconds

        while request_queue and request_queue[0] < cutoff:
            request_queue.popleft()

    def _is_rate_limited(self, client_ip: str) -> tuple[bool, Dict[str, any]]:
        """
        Check if client is rate limited.
        
        Returns:
            Tuple of (is_limited, limit_info)
        """
        now = time.time()

        # Get request queues for this IP
        minute_queue = self.minute_requests[client_ip]
        hour_queue = self.hour_requests[client_ip]

        # Clean up old requests
        self._cleanup_old_requests(minute_queue, 60)  # 1 minute
        self._cleanup_old_requests(hour_queue, 3600)  # 1 hour

        # Check minute limit
        if len(minute_queue) >= self.requests_per_minute:
            return True, {
                "limit_type": "minute",
                "limit": self.requests_per_minute,
                "requests": len(minute_queue),
                "reset_at": int(minute_queue[0] + 60)
            }

        # Check hour limit
        if len(hour_queue) >= self.requests_per_hour:
            return True, {
                "limit_type": "hour",
                "limit": self.requests_per_hour,
                "requests": len(hour_queue),
                "reset_at": int(hour_queue[0] + 3600)
            }

        # Add current request to queues
        minute_queue.append(now)
        hour_queue.append(now)

        return False, {
            "minute_requests": len(minute_queue),
            "minute_limit": self.requests_per_minute,
            "hour_requests": len(hour_queue),
            "hour_limit": self.requests_per_hour
        }

    async def dispatch(self, request: Request, call_next):
        """Check rate limits for the request."""
        client_ip = self._get_client_ip(request)

        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)

        # Check rate limits
        is_limited, limit_info = self._is_rate_limited(client_ip)

        if is_limited:
            logger.warning(
                f"Rate limit exceeded for {client_ip}",
                extra={
                    "client_ip": client_ip,
                    "limit_info": limit_info,
                    "path": request.url.path
                }
            )

            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": 429,
                        "message": f"Rate limit exceeded: {limit_info['limit']} requests per {limit_info['limit_type']}",
                        "type": "rate_limit_exceeded",
                        "limit_info": limit_info
                    }
                },
                headers={
                    "Retry-After": str(limit_info.get("reset_at", 60)),
                    "X-RateLimit-Limit": str(limit_info["limit"]),
                    "X-RateLimit-Remaining": str(max(0, limit_info["limit"] - limit_info["requests"])),
                    "X-RateLimit-Reset": str(limit_info.get("reset_at", int(time.time()) + 60))
                }
            )

        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Minute-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Minute-Remaining"] = str(
            max(0, self.requests_per_minute - limit_info.get("minute_requests", 0))
        )
        response.headers["X-RateLimit-Hour-Limit"] = str(self.requests_per_hour)
        response.headers["X-RateLimit-Hour-Remaining"] = str(
            max(0, self.requests_per_hour - limit_info.get("hour_requests", 0))
        )

        return response


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Simple API key authentication middleware."""

    def __init__(self, app):
        """Initialize authentication middleware."""
        super().__init__(app)

        # In production, these would come from environment variables or database
        self.api_keys = {
            "demo-api-key": {"name": "Demo User", "permissions": ["read", "write"]},
            "readonly-key": {"name": "Readonly User", "permissions": ["read"]},
        }

        # Paths that don't require authentication
        self.public_paths = {
            "/", "/health", "/metrics", "/docs", "/redoc", "/openapi.json"
        }

    def _extract_api_key(self, request: Request) -> Optional[str]:
        """Extract API key from request."""
        # Check Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer " prefix

        # Check X-API-Key header
        api_key_header = request.headers.get("X-API-Key")
        if api_key_header:
            return api_key_header

        # Check query parameter
        api_key_param = request.query_params.get("api_key")
        if api_key_param:
            return api_key_param

        return None

    def _validate_api_key(self, api_key: str) -> Optional[Dict[str, any]]:
        """Validate API key and return user info."""
        return self.api_keys.get(api_key)

    async def dispatch(self, request: Request, call_next):
        """Authenticate the request."""
        # Skip authentication for public paths
        if request.url.path in self.public_paths:
            return await call_next(request)

        # Extract API key
        api_key = self._extract_api_key(request)

        if not api_key:
            logger.warning(
                f"Missing API key for {request.url.path}",
                extra={"client_ip": request.client.host if request.client else "unknown"}
            )
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "code": 401,
                        "message": "API key required",
                        "type": "authentication_required"
                    }
                }
            )

        # Validate API key
        user_info = self._validate_api_key(api_key)

        if not user_info:
            logger.warning(
                f"Invalid API key for {request.url.path}",
                extra={"client_ip": request.client.host if request.client else "unknown"}
            )
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "code": 401,
                        "message": "Invalid API key",
                        "type": "authentication_failed"
                    }
                }
            )

        # Add user info to request state
        request.state.user = user_info
        request.state.api_key = api_key

        logger.debug(
            f"Authenticated user {user_info['name']} for {request.url.path}",
            extra={"user": user_info["name"], "permissions": user_info["permissions"]}
        )

        return await call_next(request)


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Add cache control headers based on content type and path."""

    def __init__(self, app):
        """Initialize cache control middleware."""
        super().__init__(app)

        # Cache policies for different paths
        self.cache_policies = {
            "/health": "no-cache",
            "/metrics": "no-cache",
            "/api/v1/contracts": "private, max-age=300",  # 5 minutes
            "/api/v1/status": "no-cache",
            "/docs": "public, max-age=3600",  # 1 hour
            "/openapi.json": "public, max-age=3600",
        }

    async def dispatch(self, request: Request, call_next):
        """Add cache control headers."""
        response = await call_next(request)

        # Determine cache policy
        cache_control = "no-cache"  # Default

        for path_pattern, policy in self.cache_policies.items():
            if request.url.path.startswith(path_pattern):
                cache_control = policy
                break

        response.headers["Cache-Control"] = cache_control

        # Add ETag for GET requests (simple implementation)
        if request.method == "GET" and hasattr(response, 'body'):
            import hashlib
            etag = hashlib.md5(response.body).hexdigest()[:16]
            response.headers["ETag"] = f'"{etag}"'

        return response
