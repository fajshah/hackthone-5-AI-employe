"""
Shared Ticket Storage
In-memory storage that persists across module reloads during development.
"""

from typing import Dict, Any, List
from datetime import datetime
import json
from pathlib import Path

# File-based storage for persistence across reloads
TICKETS_FILE = Path(__file__).parent.parent / "data" / "tickets.json"

# Ensure data directory exists
TICKETS_FILE.parent.mkdir(parents=True, exist_ok=True)

# In-memory cache
_ticket_store: Dict[str, Dict[str, Any]] = {}


def _load_tickets():
    """Load tickets from file."""
    global _ticket_store
    if TICKETS_FILE.exists():
        try:
            with open(TICKETS_FILE, 'r', encoding='utf-8') as f:
                _ticket_store = json.load(f)
        except:
            _ticket_store = {}


def _save_tickets():
    """Save tickets to file."""
    with open(TICKETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(_ticket_store, f, indent=2, ensure_ascii=False)


# Load tickets on module import
_load_tickets()


def create_ticket(ticket_data: Dict[str, Any]) -> str:
    """
    Create a new ticket and store it.
    
    Args:
        ticket_data: Dictionary with ticket information
        
    Returns:
        ticket_id: The generated ticket ID
    """
    ticket_id = ticket_data["ticket_id"]
    _ticket_store[ticket_id] = ticket_data
    _save_tickets()
    return ticket_id


def get_ticket(ticket_id: str) -> Dict[str, Any]:
    """
    Get ticket by ID.
    
    Args:
        ticket_id: The ticket ID
        
    Returns:
        Ticket data or None if not found
    """
    return _ticket_store.get(ticket_id)


def get_all_tickets() -> List[Dict[str, Any]]:
    """Get all tickets sorted by creation date (newest first)."""
    tickets = list(_ticket_store.values())
    tickets.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return tickets


def get_tickets_by_email(email: str) -> List[Dict[str, Any]]:
    """Get all tickets for a specific email."""
    tickets = [
        ticket for ticket in _ticket_store.values()
        if ticket.get("email") == email
    ]
    tickets.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return tickets


def update_ticket(ticket_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update ticket fields.
    
    Args:
        ticket_id: The ticket ID
        updates: Dictionary of fields to update
        
    Returns:
        True if ticket was updated, False if not found
    """
    if ticket_id not in _ticket_store:
        return False
    
    _ticket_store[ticket_id].update(updates)
    _save_tickets()
    return True


def add_message(ticket_id: str, message: Dict[str, Any]) -> bool:
    """
    Add a message to a ticket's conversation.
    
    Args:
        ticket_id: The ticket ID
        message: Message data with role, content, etc.
        
    Returns:
        True if message was added, False if ticket not found
    """
    if ticket_id not in _ticket_store:
        return False
    
    if "messages" not in _ticket_store[ticket_id]:
        _ticket_store[ticket_id]["messages"] = []
    
    _ticket_store[ticket_id]["messages"].append(message)
    _save_tickets()
    return True


def get_stats() -> Dict[str, Any]:
    """Get ticket statistics."""
    all_tickets = get_all_tickets()
    
    return {
        "total": len(all_tickets),
        "by_status": {},
        "by_category": {},
        "recent": all_tickets[:10]
    }
