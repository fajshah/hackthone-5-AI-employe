"""
TechNova Support API - Routes

All API route definitions organized by domain:
- support: Support form submission, status
- customers: Customer CRUD, history
- tickets: Ticket CRUD, management
- admin: Admin endpoints, analytics
- webhooks: External webhook handlers
"""

from .support import router as support_router
from .customers import router as customers_router
from .tickets import router as tickets_router
from .admin import router as admin_router
from .webhooks import router as webhooks_router

__all__ = [
    'support_router',
    'customers_router',
    'tickets_router',
    'admin_router',
    'webhooks_router',
]
