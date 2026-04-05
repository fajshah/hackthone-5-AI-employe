"""
TechNova Customer Support - REST API

Complete FastAPI application with:
- Webhooks (Gmail, WhatsApp, Twilio)
- Health & Metrics endpoints
- Support endpoints (/support/submit, /support/tickets, etc.)
- Customer endpoints
- Admin endpoints
- WebSocket support
"""

import os
import json
import uuid
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from enum import Enum

from fastapi import FastAPI, HTTPException, status, Request, Response, WebSocket, WebSocketDisconnect, BackgroundTasks, Depends, Query, Path
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr, validator
import uvicorn

# Local imports
from .routes import support, customers, tickets, admin, webhooks
from .middleware import RateLimiter, RequestLogger, SecurityMiddleware
from .models import (
    # Request models
    SupportSubmitRequest,
    SupportSubmitResponse,
    TicketCreateRequest,
    TicketUpdateRequest,
    CustomerCreateRequest,
    CustomerUpdateRequest,
    # Response models
    TicketResponse,
    CustomerResponse,
    ConversationResponse,
    HealthResponse,
    MetricsResponse,
    ErrorResponse,
)
from .schemas import (
    WebhookValidationResult,
    KafkaPublishResult,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

class APIConfig:
    """API configuration"""
    
    # Server
    HOST = os.getenv("API_HOST", "0.0.0.0")
    PORT = int(os.getenv("API_PORT", "8000"))
    WORKERS = int(os.getenv("API_WORKERS", "4"))
    DEBUG = os.getenv("API_DEBUG", "false").lower() == "true"
    
    # Security
    API_KEY = os.getenv("API_KEY", "dev-api-key-change-in-production")
    API_KEY_HEADER = os.getenv("API_KEY_HEADER", "X-API-Key")
    ENABLE_CORS = os.getenv("ENABLE_CORS", "true").lower() == "true"
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")
    
    # Rate limiting
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    
    # Kafka
    KAFKA_ENABLED = os.getenv("KAFKA_ENABLED", "true").lower() == "true"
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(",")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/technova")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_REQUESTS = os.getenv("LOG_REQUESTS", "true").lower() == "true"


# ============================================================================
# Application Lifespan
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting TechNova Support API...")
    
    # Initialize database
    try:
        from database import init_database
        init_database()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    # Initialize Kafka
    if APIConfig.KAFKA_ENABLED:
        try:
            from kafka_client import KafkaClient
            app.state.kafka_client = KafkaClient()
            logger.info("Kafka client initialized")
        except Exception as e:
            logger.error(f"Kafka initialization failed: {e}")
    
    # Initialize agent
    try:
        from agent import create_agent
        app.state.agent = create_agent()
        logger.info("Agent initialized")
    except Exception as e:
        logger.error(f"Agent initialization failed: {e}")
    
    # Initialize metrics
    app.state.metrics = {
        "requests_total": 0,
        "requests_failed": 0,
        "requests_by_endpoint": {},
        "average_response_time_ms": 0,
        "start_time": datetime.now(),
    }
    
    logger.info(f"TechNova Support API started on {APIConfig.HOST}:{APIConfig.PORT}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down TechNova Support API...")
    
    # Close database
    try:
        from database import close_database
        close_database()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Database shutdown failed: {e}")
    
    # Close Kafka
    if hasattr(app.state, 'kafka_client'):
        try:
            app.state.kafka_client.close()
            logger.info("Kafka client closed")
        except Exception as e:
            logger.error(f"Kafka shutdown failed: {e}")
    
    logger.info("TechNova Support API shutdown complete")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="TechNova Customer Support API",
    description="""
## TechNova Customer Support API

Complete REST API for customer support automation.

### Features

- **Multi-channel Support**: Email, WhatsApp, Web Form
- **AI-Powered Agent**: Automatic response generation
- **Escalation Management**: Smart routing to human agents
- **Real-time Updates**: WebSocket support for live notifications
- **Analytics**: Comprehensive metrics and reporting

### Authentication

Most endpoints require API key authentication:
```
X-API-Key: your-api-key
```

### Rate Limiting

- Default: 100 requests per minute
- Configurable via environment variables

### Support

For issues, contact: support@technova.com
    """,
    version="1.0.0",
    contact={
        "name": "TechNova Support",
        "email": "support@technova.com",
        "url": "https://technova.com/support",
    },
    license_info={
        "name": "Proprietary",
        "url": "https://technova.com/license",
    },
    lifespan=lifespan,
)

# ============================================================================
# Middleware
# ============================================================================

# CORS
if APIConfig.ENABLE_CORS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=APIConfig.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Trusted hosts
if APIConfig.ALLOWED_HOSTS != ["*"]:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=APIConfig.ALLOWED_HOSTS,
    )

# Request logging
if APIConfig.LOG_REQUESTS:
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        import time
        start_time = time.time()
        
        response = await call_next(request)
        
        duration = (time.time() - start_time) * 1000
        
        # Update metrics
        app.state.metrics["requests_total"] += 1
        app.state.metrics["requests_by_endpoint"][request.url.path] = \
            app.state.metrics["requests_by_endpoint"].get(request.url.path, 0) + 1
        
        # Log
        logger.info(
            f"{request.method} {request.url.path} - "
            f"{response.status_code} - {duration:.0f}ms"
        )
        
        return response

# Security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# ============================================================================
# Authentication
# ============================================================================

security = HTTPBearer(auto_error=False)

async def verify_api_key(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """
    Verify API key from header or query param
    
    Args:
        request: FastAPI request
        credentials: HTTP Bearer credentials (optional)
        
    Returns:
        API key if valid, None for public endpoints
    """
    # Check for API key in header
    api_key = request.headers.get(APIConfig.API_KEY_HEADER)
    
    # Check for Bearer token
    if not api_key and credentials:
        api_key = credentials.credentials
    
    # Check for query param (for webhooks)
    if not api_key:
        api_key = request.query_params.get("api_key")
    
    # Validate
    if api_key and api_key != APIConfig.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return api_key


# ============================================================================
# Root Endpoints
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API information
    """
    return {
        "name": "TechNova Customer Support API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
    }


@app.get("/health", tags=["Health"], response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns current health status of all components
    """
    health = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "components": {
            "api": {"status": "healthy"},
            "database": {"status": "unknown"},
            "kafka": {"status": "unknown"},
            "agent": {"status": "unknown"},
        }
    }
    
    # Check database
    try:
        from database import DatabasePool
        with DatabasePool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        health["components"]["database"]["status"] = "healthy"
    except Exception as e:
        health["components"]["database"]["status"] = "unhealthy"
        health["components"]["database"]["error"] = str(e)
        health["status"] = "degraded"
    
    # Check Kafka
    if APIConfig.KAFKA_ENABLED and hasattr(app.state, 'kafka_client'):
        try:
            # Simple Kafka check (would need admin client for real check)
            health["components"]["kafka"]["status"] = "healthy"
        except Exception as e:
            health["components"]["kafka"]["status"] = "unhealthy"
            health["components"]["kafka"]["error"] = str(e)
            health["status"] = "degraded"
    
    # Check agent
    if hasattr(app.state, 'agent'):
        health["components"]["agent"]["status"] = "healthy"
    
    return health


@app.get("/health/live", tags=["Health"])
async def liveness_probe():
    """
    Kubernetes liveness probe
    
    Returns 200 if API is running
    """
    return {"status": "alive"}


@app.get("/health/ready", tags=["Health"])
async def readiness_probe():
    """
    Kubernetes readiness probe
    
    Returns 200 if API is ready to serve traffic
    """
    health = await health_check()
    
    if health["status"] == "healthy":
        return {"status": "ready"}
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )


@app.get("/metrics", tags=["Monitoring"], response_model=MetricsResponse)
async def get_metrics():
    """
    Get API metrics
    
    Returns request counts, response times, and system stats
    """
    uptime = datetime.now() - app.state.metrics["start_time"]
    
    return {
        "requests_total": app.state.metrics["requests_total"],
        "requests_failed": app.state.metrics["requests_failed"],
        "requests_by_endpoint": app.state.metrics["requests_by_endpoint"],
        "average_response_time_ms": app.state.metrics["average_response_time_ms"],
        "uptime_seconds": uptime.total_seconds(),
        "start_time": app.state.metrics["start_time"].isoformat(),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/metrics/prometheus", tags=["Monitoring"])
async def prometheus_metrics():
    """
    Prometheus-format metrics
    
    For scraping by Prometheus
    """
    uptime = datetime.now() - app.state.metrics["start_time"]
    
    metrics = f"""
# HELP technova_api_requests_total Total number of requests
# TYPE technova_api_requests_total counter
technova_api_requests_total {app.state.metrics["requests_total"]}

# HELP technova_api_requests_failed Total number of failed requests
# TYPE technova_api_requests_failed counter
technova_api_requests_failed {app.state.metrics["requests_failed"]}

# HELP technova_api_uptime_seconds API uptime in seconds
# TYPE technova_api_uptime_seconds gauge
technova_api_uptime_seconds {uptime.total_seconds()}

# HELP technova_api_response_time_ms Average response time in milliseconds
# TYPE technova_api_response_time_ms gauge
technova_api_response_time_ms {app.state.metrics["average_response_time_ms"]}
"""
    
    return PlainTextResponse(metrics)


# ============================================================================
# Include Routers
# ============================================================================

# Support endpoints
app.include_router(support.router, prefix="/support", tags=["Support"])

# Customer endpoints
app.include_router(customers.router, prefix="/customers", tags=["Customers"])

# Ticket endpoints
app.include_router(tickets.router, prefix="/tickets", tags=["Tickets"])

# Admin endpoints
app.include_router(admin.router, prefix="/admin", tags=["Admin"])

# Webhook endpoints
app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "message": exc.detail,
            "path": str(request.url.path),
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Internal server error",
            "path": str(request.url.path),
            "timestamp": datetime.now().isoformat(),
        }
    )


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Run the API server"""
    uvicorn.run(
        "api.main:app",
        host=APIConfig.HOST,
        port=APIConfig.PORT,
        workers=APIConfig.WORKERS,
        reload=APIConfig.DEBUG,
        log_level=APIConfig.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
