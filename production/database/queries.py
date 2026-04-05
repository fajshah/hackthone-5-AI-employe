"""
TechNova Customer Support Agent - Database Queries

Helper functions for database operations.
Uses psycopg2 with connection pooling.
"""

import os
import json
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor, Json

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

class DatabaseConfig:
    """Database configuration"""
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/technova")
    PGVECTOR_DIMENSION = int(os.getenv("PGVECTOR_DIMENSION", "1536"))
    MIN_CONNECTIONS = int(os.getenv("DB_MIN_CONNECTIONS", "2"))
    MAX_CONNECTIONS = int(os.getenv("DB_MAX_CONNECTIONS", "10"))


# ============================================================================
# Connection Pool
# ============================================================================

class DatabasePool:
    """PostgreSQL connection pool manager"""
    
    _pool: Optional[pool.SimpleConnectionPool] = None
    
    @classmethod
    def initialize(cls):
        """Initialize connection pool"""
        if cls._pool is None:
            try:
                cls._pool = pool.SimpleConnectionPool(
                    minconn=DatabaseConfig.MIN_CONNECTIONS,
                    maxconn=DatabaseConfig.MAX_CONNECTIONS,
                    dsn=DatabaseConfig.DATABASE_URL
                )
                logger.info("Database connection pool initialized")
            except Exception as e:
                logger.error(f"Failed to initialize database pool: {e}")
                raise
    
    @classmethod
    @contextmanager
    def get_connection(cls):
        """Get connection from pool"""
        if cls._pool is None:
            cls.initialize()
        
        conn = None
        try:
            conn = cls._pool.getconn()
            yield conn
        finally:
            if conn:
                cls._pool.putconn(conn)
    
    @classmethod
    def close_all(cls):
        """Close all connections"""
        if cls._pool:
            cls._pool.closeall()
            cls._pool = None


# ============================================================================
# Customer Queries
# ============================================================================

class CustomerQueries:
    """Customer-related database queries"""
    
    @staticmethod
    def create_or_update_customer(
        customer_id: str,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        account_tier: str = 'basic',
        is_vip: bool = False
    ) -> Dict:
        """Create or update customer profile"""
        query = """
            INSERT INTO customers (
                customer_id, email, phone, name, company,
                account_tier, is_vip, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (customer_id) DO UPDATE SET
                email = COALESCE(EXCLUDED.email, customers.email),
                phone = COALESCE(EXCLUDED.phone, customers.phone),
                name = COALESCE(EXCLUDED.name, customers.name),
                company = COALESCE(EXCLUDED.company, customers.company),
                updated_at = NOW()
            RETURNING *
        """
        
        with DatabasePool.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (
                    customer_id, email, phone, name, company,
                    account_tier, is_vip
                ))
                result = cur.fetchone()
                conn.commit()
                return dict(result) if result else None
    
    @staticmethod
    def get_customer(customer_id: str) -> Optional[Dict]:
        """Get customer by ID"""
        query = "SELECT * FROM customers WHERE customer_id = %s"
        
        with DatabasePool.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (customer_id,))
                result = cur.fetchone()
                return dict(result) if result else None
    
    @staticmethod
    def get_customer_by_email(email: str) -> Optional[Dict]:
        """Get customer by email"""
        query = "SELECT * FROM customers WHERE email = %s"
        
        with DatabasePool.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (email,))
                result = cur.fetchone()
                return dict(result) if result else None
    
    @staticmethod
    def get_customer_stats(customer_id: str) -> Dict:
        """Get customer statistics"""
        query = """
            SELECT 
                total_tickets,
                escalated_tickets,
                avg_sentiment_score,
                preferred_channel,
                last_contact_at
            FROM customers
            WHERE customer_id = %s
        """
        
        with DatabasePool.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (customer_id,))
                result = cur.fetchone()
                return dict(result) if result else {}
    
    @staticmethod
    def update_customer_sentiment(customer_id: str, sentiment_score: float) -> bool:
        """Update customer average sentiment"""
        query = """
            UPDATE customers
            SET avg_sentiment_score = (
                SELECT AVG(sentiment_score)
                FROM messages
                WHERE customer_id = %s AND sentiment_score IS NOT NULL
            )
            WHERE customer_id = %s
            RETURNING avg_sentiment_score
        """
        
        with DatabasePool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (customer_id, customer_id))
                conn.commit()
                return True


# ============================================================================
# Conversation Queries
# ============================================================================

class ConversationQueries:
    """Conversation-related database queries"""
    
    @staticmethod
    def create_conversation(
        conversation_id: str,
        customer_id: str,
        channel: str,
        thread_id: Optional[str] = None
    ) -> Dict:
        """Create new conversation"""
        query = """
            INSERT INTO conversations (
                conversation_id, customer_id, channel, thread_id
            )
            VALUES (%s, %s, %s, %s)
            RETURNING *
        """
        
        with DatabasePool.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (conversation_id, customer_id, channel, thread_id))
                result = cur.fetchone()
                conn.commit()
                return dict(result) if result else None
    
    @staticmethod
    def get_conversation(conversation_id: str) -> Optional[Dict]:
        """Get conversation by ID"""
        query = "SELECT * FROM conversations WHERE conversation_id = %s"
        
        with DatabasePool.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (conversation_id,))
                result = cur.fetchone()
                return dict(result) if result else None
    
    @staticmethod
    def get_customer_conversations(customer_id: str, limit: int = 20) -> List[Dict]:
        """Get customer's conversation history"""
        query = """
            SELECT * FROM conversations
            WHERE customer_id = %s
            ORDER BY started_at DESC
            LIMIT %s
        """
        
        with DatabasePool.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (customer_id, limit))
                results = cur.fetchall()
                return [dict(r) for r in results]
    
    @staticmethod
    def update_conversation_sentiment(
        conversation_id: str,
        sentiment: str,
        sentiment_score: float
    ) -> bool:
        """Update conversation sentiment"""
        query = """
            UPDATE conversations
            SET 
                overall_sentiment = %s,
                sentiment_score = %s,
                last_message_at = NOW()
            WHERE conversation_id = %s
        """
        
        with DatabasePool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (sentiment, sentiment_score, conversation_id))
                conn.commit()
                return True


# ============================================================================
# Message Queries
# ============================================================================

class MessageQueries:
    """Message-related database queries"""
    
    @staticmethod
    def create_message(
        message_id: str,
        conversation_id: str,
        customer_id: str,
        role: str,
        content: str,
        channel: str,
        category: Optional[str] = None,
        sentiment: Optional[str] = None,
        sentiment_score: Optional[float] = None,
        priority: str = 'P3',
        entities: Optional[Dict] = None,
        requires_escalation: bool = False,
        escalation_reason: Optional[str] = None
    ) -> Dict:
        """Create new message"""
        query = """
            INSERT INTO messages (
                message_id, conversation_id, customer_id, role, content,
                channel, category, sentiment, sentiment_score, priority,
                entities, requires_escalation, escalation_reason
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        
        with DatabasePool.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (
                    message_id, conversation_id, customer_id, role, content,
                    channel, category, sentiment, sentiment_score, priority,
                    Json(entities) if entities else None,
                    requires_escalation, escalation_reason
                ))
                result = cur.fetchone()
                conn.commit()
                return dict(result) if result else None
    
    @staticmethod
    def get_conversation_messages(conversation_id: str, limit: int = 50) -> List[Dict]:
        """Get messages for a conversation"""
        query = """
            SELECT * FROM messages
            WHERE conversation_id = %s
            ORDER BY created_at ASC
            LIMIT %s
        """
        
        with DatabasePool.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (conversation_id, limit))
                results = cur.fetchall()
                return [dict(r) for r in results]


# ============================================================================
# Ticket Queries
# ============================================================================

class TicketQueries:
    """Ticket-related database queries"""
    
    @staticmethod
    def create_ticket(
        ticket_id: str,
        customer_id: str,
        subject: str,
        description: str,
        channel: str,
        category: str,
        priority: str = 'P3',
        conversation_id: Optional[str] = None,
        sentiment: Optional[str] = None,
        sentiment_score: Optional[float] = None,
        requires_escalation: bool = False,
        escalation_reason: Optional[str] = None,
        sla_deadline: Optional[datetime] = None
    ) -> Dict:
        """Create new ticket"""
        query = """
            INSERT INTO tickets (
                ticket_id, customer_id, conversation_id, subject, description,
                channel, category, priority, sentiment, sentiment_score,
                requires_escalation, escalation_reason, sla_deadline
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        
        with DatabasePool.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (
                    ticket_id, customer_id, conversation_id, subject, description,
                    channel, category, priority, sentiment, sentiment_score,
                    requires_escalation, escalation_reason, sla_deadline
                ))
                result = cur.fetchone()
                conn.commit()
                return dict(result) if result else None
    
    @staticmethod
    def get_ticket(ticket_id: str) -> Optional[Dict]:
        """Get ticket by ID"""
        query = "SELECT * FROM tickets WHERE ticket_id = %s"
        
        with DatabasePool.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (ticket_id,))
                result = cur.fetchone()
                return dict(result) if result else None
    
    @staticmethod
    def update_ticket_status(ticket_id: str, status: str) -> bool:
        """Update ticket status"""
        query = """
            UPDATE tickets
            SET status = %s, updated_at = NOW()
            WHERE ticket_id = %s
        """
        
        with DatabasePool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (status, ticket_id))
                conn.commit()
                return True
    
    @staticmethod
    def escalate_ticket(
        ticket_id: str,
        escalation_reason: str,
        priority: str,
        assigned_team: str,
        notes: Optional[str] = None
    ) -> bool:
        """Escalate a ticket"""
        query = """
            UPDATE tickets
            SET 
                requires_escalation = TRUE,
                escalation_reason = %s,
                priority = %s,
                assigned_team = %s,
                status = 'escalated',
                escalated_at = NOW(),
                escalation_notes = %s,
                updated_at = NOW()
            WHERE ticket_id = %s
        """
        
        with DatabasePool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (escalation_reason, priority, assigned_team, notes, ticket_id))
                conn.commit()
                return True
    
    @staticmethod
    def get_open_tickets(customer_id: str) -> List[Dict]:
        """Get customer's open tickets"""
        query = """
            SELECT * FROM tickets
            WHERE customer_id = %s AND status NOT IN ('resolved', 'closed')
            ORDER BY priority, created_at DESC
        """
        
        with DatabasePool.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (customer_id,))
                results = cur.fetchall()
                return [dict(r) for r in results]


# ============================================================================
# Knowledge Base Queries (with pgvector)
# ============================================================================

class KnowledgeBaseQueries:
    """Knowledge base queries with semantic search"""
    
    @staticmethod
    def search_semantic(
        query_embedding: List[float],
        limit: int = 5,
        min_confidence: float = 0.3
    ) -> List[Dict]:
        """Semantic search using pgvector"""
        query = """
            SELECT 
                id, feature, title, content, category, url,
                1 - (embedding <=> %s::vector) as confidence
            FROM knowledge_base
            WHERE is_active = TRUE
                AND 1 - (embedding <=> %s::vector) >= %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        with DatabasePool.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (embedding_str, embedding_str, min_confidence, embedding_str, limit))
                results = cur.fetchall()
                return [dict(r) for r in results]
    
    @staticmethod
    def search_keyword(query: str, limit: int = 5) -> List[Dict]:
        """Keyword-based search fallback"""
        query_sql = """
            SELECT 
                id, feature, title, content, category, url,
                ts_rank(to_tsvector('english', feature || ' ' || content), 
                       plainto_tsquery('english', %s)) as confidence
            FROM knowledge_base
            WHERE is_active = TRUE
                AND to_tsvector('english', feature || ' ' || content) 
                    @@ plainto_tsquery('english', %s)
            ORDER BY confidence DESC
            LIMIT %s
        """
        
        with DatabasePool.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query_sql, (query, query, limit))
                results = cur.fetchall()
                return [dict(r) for r in results]
    
    @staticmethod
    def add_article(
        feature: str,
        title: str,
        content: str,
        category: str,
        keywords: List[str],
        embedding: List[float],
        url: Optional[str] = None
    ) -> int:
        """Add knowledge base article"""
        query = """
            INSERT INTO knowledge_base (
                feature, title, content, category, keywords, embedding, url
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
        
        with DatabasePool.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (feature, title, content, category, keywords, embedding_str, url))
                result = cur.fetchone()
                conn.commit()
                return result['id'] if result else None
    
    @staticmethod
    def increment_view_count(article_id: int) -> bool:
        """Increment article view count"""
        query = """
            UPDATE knowledge_base
            SET view_count = view_count + 1
            WHERE id = %s
        """
        
        with DatabasePool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (article_id,))
                conn.commit()
                return True


# ============================================================================
# Escalation Queries
# ============================================================================

class EscalationQueries:
    """Escalation-related queries"""
    
    @staticmethod
    def create_escalation(
        escalation_id: str,
        ticket_id: str,
        customer_id: str,
        reason: str,
        priority: str,
        target_team: str,
        handoff_summary: str,
        sla_response_time: str,
        sla_deadline: datetime,
        context_summary: Optional[str] = None,
        recommended_actions: Optional[List[str]] = None
    ) -> Dict:
        """Create escalation record"""
        query = """
            INSERT INTO escalations (
                escalation_id, ticket_id, customer_id, reason, priority,
                target_team, handoff_summary, context_summary,
                recommended_actions, sla_response_time, sla_deadline
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        
        with DatabasePool.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (
                    escalation_id, ticket_id, customer_id, reason, priority,
                    target_team, handoff_summary, context_summary,
                    recommended_actions, sla_response_time, sla_deadline
                ))
                result = cur.fetchone()
                conn.commit()
                return dict(result) if result else None
    
    @staticmethod
    def get_pending_escalations() -> List[Dict]:
        """Get all pending escalations"""
        query = """
            SELECT e.*, t.subject, t.priority as ticket_priority
            FROM escalations e
            JOIN tickets t ON e.ticket_id = t.ticket_id
            WHERE e.status = 'pending'
            ORDER BY e.priority, e.sla_deadline
        """
        
        with DatabasePool.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                results = cur.fetchall()
                return [dict(r) for r in results]
    
    @staticmethod
    def resolve_escalation(
        escalation_id: str,
        resolved_by: str,
        resolution_notes: str
    ) -> bool:
        """Resolve an escalation"""
        query = """
            UPDATE escalations
            SET 
                status = 'resolved',
                resolved_by = %s,
                resolution_notes = %s,
                resolved_at = NOW()
            WHERE escalation_id = %s
        """
        
        with DatabasePool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (resolved_by, resolution_notes, escalation_id))
                conn.commit()
                return True


# ============================================================================
# Analytics Queries
# ============================================================================

class AnalyticsQueries:
    """Analytics and reporting queries"""
    
    @staticmethod
    def get_ticket_stats(days: int = 30) -> Dict:
        """Get ticket statistics for last N days"""
        query = """
            SELECT 
                COUNT(*) as total_tickets,
                COUNT(*) FILTER (WHERE status = 'resolved') as resolved_tickets,
                COUNT(*) FILTER (WHERE requires_escalation = TRUE) as escalated_tickets,
                AVG(sentiment_score) as avg_sentiment,
                COUNT(DISTINCT customer_id) as unique_customers
            FROM tickets
            WHERE created_at >= NOW() - INTERVAL '%s days'
        """
        
        with DatabasePool.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (days,))
                result = cur.fetchone()
                return dict(result) if result else {}
    
    @staticmethod
    def get_channel_distribution(days: int = 30) -> List[Dict]:
        """Get ticket distribution by channel"""
        query = """
            SELECT 
                channel,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
            FROM tickets
            WHERE created_at >= NOW() - INTERVAL '%s days'
            GROUP BY channel
            ORDER BY count DESC
        """
        
        with DatabasePool.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (days,))
                results = cur.fetchall()
                return [dict(r) for r in results]
    
    @staticmethod
    def get_response_time_stats() -> Dict:
        """Get response time statistics"""
        query = """
            SELECT 
                AVG(response_time_seconds) as avg_response_time,
                MIN(response_time_seconds) as min_response_time,
                MAX(response_time_seconds) as max_response_time,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_seconds) as p95_response_time
            FROM messages
            WHERE response_time_seconds IS NOT NULL
        """
        
        with DatabasePool.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                result = cur.fetchone()
                return dict(result) if result else {}


# ============================================================================
# Helper Functions
# ============================================================================

def init_database():
    """Initialize database connection pool"""
    DatabasePool.initialize()


def close_database():
    """Close all database connections"""
    DatabasePool.close_all()


@contextmanager
def database_transaction():
    """Context manager for database transactions"""
    conn = None
    try:
        with DatabasePool.get_connection() as conn:
            yield conn
            conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database transaction failed: {e}")
        raise


# ============================================================================
# Usage Example
# ============================================================================

"""
# Initialize database
init_database()

# Create customer
customer = CustomerQueries.create_or_update_customer(
    customer_id="CUST-001",
    name="John Doe",
    email="john@example.com",
    account_tier="pro"
)

# Create conversation
conversation = ConversationQueries.create_conversation(
    conversation_id="CONV-001",
    customer_id="CUST-001",
    channel="email"
)

# Create message
message = MessageQueries.create_message(
    message_id="MSG-001",
    conversation_id="CONV-001",
    customer_id="CUST-001",
    role="customer",
    content="How do I integrate with Slack?",
    channel="email",
    category="how_to",
    sentiment="neutral"
)

# Search knowledge base
from openai import OpenAI
client = OpenAI()
embedding = client.embeddings.create(
    model="text-embedding-3-small",
    input="Slack integration"
).data[0].embedding

results = KnowledgeBaseQueries.search_semantic(embedding, limit=5)

# Close connections
close_database()
"""
