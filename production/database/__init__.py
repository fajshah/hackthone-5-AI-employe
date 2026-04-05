"""
TechNova Customer Support Agent - Database Module

PostgreSQL database with pgvector for semantic search.
"""

from .queries import (
    # Connection management
    init_database,
    close_database,
    database_transaction,
    
    # Query classes
    CustomerQueries,
    ConversationQueries,
    MessageQueries,
    TicketQueries,
    KnowledgeBaseQueries,
    EscalationQueries,
    AnalyticsQueries,
    
    # Database pool
    DatabasePool,
    DatabaseConfig,
)

__version__ = "1.0.0"
__all__ = [
    # Connection management
    "init_database",
    "close_database",
    "database_transaction",
    
    # Query classes
    "CustomerQueries",
    "ConversationQueries",
    "MessageQueries",
    "TicketQueries",
    "KnowledgeBaseQueries",
    "EscalationQueries",
    "AnalyticsQueries",
    
    # Database pool
    "DatabasePool",
    "DatabaseConfig",
]
