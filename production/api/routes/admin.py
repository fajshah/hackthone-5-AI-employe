"""
TechNova Support API - Admin Routes

Endpoints:
- GET /admin/stats - System statistics
- GET /admin/metrics - Detailed metrics
- POST /admin/broadcast - Send broadcast message
- GET /admin/escalations - List escalations
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/stats")
async def get_stats():
    """Get system statistics"""
    return {
        "total_tickets": 0,
        "open_tickets": 0,
        "resolved_tickets": 0,
        "escalations": 0,
    }


@router.get("/metrics")
async def get_metrics():
    """Get detailed system metrics"""
    return {
        "requests_total": 0,
        "avg_response_time_ms": 0,
        "error_rate": 0.0,
    }


@router.post("/broadcast")
async def send_broadcast(broadcast_data: dict):
    """Send broadcast message to customers"""
    return {"status": "sent", "recipients": 0}


@router.get("/escalations")
async def list_escalations():
    """List all escalations"""
    return {"escalations": []}
