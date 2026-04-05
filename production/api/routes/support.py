"""
TechNova Support API - Support Routes

Endpoints:
- POST /support/submit - Submit support request
- GET /support/status/{ticket_id} - Get ticket status
- GET /support/ticket/{ticket_id} - Get ticket details (for frontend)
- GET /support/tickets - List user tickets
"""

from fastapi import APIRouter, HTTPException, status, Request, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from ..models import SupportSubmitRequest, SupportSubmitResponse, TicketResponse
from ..storage import create_ticket, get_ticket, get_all_tickets, get_tickets_by_email, add_message

router = APIRouter()


@router.post(
    "/submit",
    response_model=SupportSubmitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Support Request",
    description="Submit a new support request via web form",
    responses={
        201: {"description": "Request submitted successfully"},
        400: {"description": "Validation error"},
        429: {"description": "Rate limit exceeded"},
    }
)
async def submit_support_request(
    request: SupportSubmitRequest,
    http_request: Request
):
    """
    Submit a new support request

    **Fields:**
    - **email**: Customer email (required)
    - **name**: Customer name (optional)
    - **company**: Company name (optional)
    - **subject**: Request subject (required, 5-200 chars)
    - **message**: Request message (required, 10-5000 chars)
    - **attachments**: File attachments (optional, max 5 files)

    **Returns:**
    - ticket_id: Generated ticket ID
    - status: Initial status
    - message: Confirmation message
    """
    try:
        # Generate ticket ID
        ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        
        # Create ticket data
        ticket_data = {
            "ticket_id": ticket_id,
            "name": request.name,
            "email": request.email,
            "subject": request.subject,
            "category": "general",  # Default category
            "priority": "medium",  # Default priority
            "status": "open",
            "created_at": datetime.now().isoformat(),
            "messages": [
                {
                    "id": f"MSG-{uuid.uuid4().hex[:6].upper()}",
                    "role": "customer",
                    "content": request.message,
                    "created_at": datetime.now().isoformat()
                }
            ]
        }
        
        # Store ticket using storage module
        create_ticket(ticket_data)

        return SupportSubmitResponse(
            ticket_id=ticket_id,
            status="received",
            message="Your support request has been submitted successfully. We'll respond within 24 hours.",
            email=request.email,
            submitted_at=datetime.now().isoformat()
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit request: {str(e)}"
        )


@router.get(
    "/ticket/{ticket_id}",
    summary="Get Ticket Details",
    description="Get full ticket details including conversation history",
    responses={
        200: {"description": "Ticket details retrieved successfully"},
        404: {"description": "Ticket not found"},
    }
)
async def get_ticket_details(ticket_id: str):
    """
    Get ticket details by ID (for frontend display)

    **Path Parameters:**
    - **ticket_id**: Ticket ID (e.g., TKT-ABC123)

    **Returns:**
    - ticket_id: Ticket ID
    - subject: Ticket subject
    - status: Current status
    - category: Ticket category
    - messages: Conversation history
    - created_at: Creation timestamp
    """
    # Look up ticket using storage module
    ticket = get_ticket(ticket_id)
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found"
        )
    
    return ticket


@router.get(
    "/status/{ticket_id}",
    response_model=Dict,
    summary="Get Ticket Status",
    description="Get the current status of a support ticket",
    responses={
        200: {"description": "Status retrieved successfully"},
        404: {"description": "Ticket not found"},
    }
)
async def get_ticket_status(ticket_id: str):
    """
    Get ticket status by ID

    **Path Parameters:**
    - **ticket_id**: Ticket ID (e.g., TKT-ABC123)

    **Returns:**
    - ticket_id: Ticket ID
    - status: Current status
    - message: Status message
    - updates: Status update history
    """
    # Look up ticket using storage module
    ticket = get_ticket(ticket_id)
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found"
        )
    
    return {
        "ticket_id": ticket["ticket_id"],
        "status": ticket["status"],
        "message": f"Ticket status: {ticket['status']}",
        "created_at": ticket["created_at"],
        "updated_at": datetime.now().isoformat(),
        "updates": [
            {
                "timestamp": ticket["created_at"],
                "status": "received",
                "message": "Ticket received"
            }
        ]
    }


@router.get(
    "/tickets",
    summary="List User Tickets",
    description="Get all tickets for a customer",
    responses={
        200: {"description": "Tickets retrieved successfully"},
    }
)
async def list_user_tickets(
    email: str,
    limit: int = 20,
    offset: int = 0
):
    """
    List tickets by customer email

    **Query Parameters:**
    - **email**: Customer email (required)
    - **limit**: Max results (default: 20)
    - **offset**: Pagination offset (default: 0)

    **Returns:**
    - List of tickets
    """
    # Get tickets by email using storage module
    user_tickets = get_tickets_by_email(email)
    
    # Apply pagination
    paginated = user_tickets[offset:offset + limit]
    
    return paginated
