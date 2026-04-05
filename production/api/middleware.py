"""
TechNova Support API - Middleware

Custom middleware for:
- Rate limiting
- Request logging
- Security
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Callable, Dict
import time
from collections import defaultdict
from datetime import datetime, timedelta


# ============================================================================
# Rate Limiter
# ============================================================================

class RateLimiter:
    """
    Simple in-memory rate limiter
    
    For production, use Redis-based rate limiting
    """
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_rate_limited(self, identifier: str, max_requests: int, window_seconds: int) -> bool:
        """
        Check if identifier is rate limited
        
        Args:
            identifier: Client identifier (IP, API key, etc.)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            True if rate limited, False otherwise
        """
        now = time.time()
        window_start = now - window_seconds
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]
        
        # Check limit
        if len(self.requests[identifier]) >= max_requests:
            return True
        
        # Record this request
        self.requests[identifier].append(now)
        return False


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(requests: int = 100, window_seconds: int = 60):
    """
    Rate limiting decorator for routes
    
    Args:
        requests: Max requests per window
        window_seconds: Time window in seconds
    """
    async def middleware(request: Request, call_next: Callable):
        # Get client identifier (IP address)
        identifier = request.client.host
        
        # Check rate limit
        if rate_limiter.is_rate_limited(identifier, requests, window_seconds):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": True,
                    "message": "Rate limit exceeded",
                    "retry_after": window_seconds,
                }
            )
        
        # Process request
        return await call_next(request)
    
    return middleware


# ============================================================================
# Request Logger
# ============================================================================

class RequestLogger:
    """Request logging middleware"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, request: Request, call_next: Callable):
        import logging
        logger = logging.getLogger(__name__)
        
        # Log request
        logger.info(f"{request.method} {request.url.path}")
        
        # Process
        start_time = time.time()
        response = await call_next(request)
        duration = (time.time() - start_time) * 1000
        
        # Log response
        logger.info(f"Response: {response.status_code} in {duration:.0f}ms")
        
        return response


# ============================================================================
# Security Middleware
# ============================================================================

class SecurityMiddleware:
    """Security headers middleware"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, request: Request, call_next: Callable):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response
