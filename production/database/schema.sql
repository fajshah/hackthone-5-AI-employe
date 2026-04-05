-- ============================================================================
-- TechNova Customer Support Agent - Database Schema
-- Hackathon 5 Production Database
-- ============================================================================
-- PostgreSQL 14+ with pgvector extension
-- This schema supports:
-- - Multi-channel customer support (Email, WhatsApp, Web Form)
-- - Customer profile management
-- - Conversation history tracking
-- - Ticket management with escalation
-- - Knowledge base with semantic search (pgvector)
-- - Sentiment analysis tracking
-- ============================================================================

-- Enable pgvector extension for semantic search
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- ENUMS
-- ============================================================================

-- Communication channels
CREATE TYPE channel_type AS ENUM ('email', 'whatsapp', 'web_form');

-- Ticket categories (from discovery phase analysis)
CREATE TYPE ticket_category AS ENUM (
    'how_to',
    'technical_issue',
    'feature_inquiry',
    'billing',
    'bug_report',
    'compliance',
    'cancellation',
    'sales',
    'account',
    'performance'
);

-- Priority levels (SLA-based)
CREATE TYPE priority_level AS ENUM ('P0', 'P1', 'P2', 'P3');

-- Ticket status
CREATE TYPE ticket_status AS ENUM (
    'open',
    'in_progress',
    'waiting_customer',
    'resolved',
    'escalated',
    'closed'
);

-- Sentiment types
CREATE TYPE sentiment_type AS ENUM (
    'positive',
    'neutral',
    'negative',
    'urgent',
    'angry',
    'frustrated'
);

-- Resolution status
CREATE TYPE resolution_status AS ENUM (
    'open',
    'in_progress',
    'waiting_customer',
    'resolved',
    'escalated'
);

-- Escalation reasons
CREATE TYPE escalation_reason AS ENUM (
    'enterprise_sales',
    'refund_billing',
    'legal_compliance',
    'angry_customer',
    'system_outage',
    'data_loss_security',
    'vip_customer',
    'api_integration',
    'cancellation',
    'feature_request'
);

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Customers table (unified profile across channels)
CREATE TABLE customers (
    customer_id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50) UNIQUE,
    name VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    
    -- Account details
    account_tier VARCHAR(50) DEFAULT 'basic',
    is_vip BOOLEAN DEFAULT FALSE,
    arr DECIMAL(12, 2) DEFAULT 0,  -- Annual Recurring Revenue
    
    -- Preferences
    preferred_channel channel_type DEFAULT 'email',
    communication_style VARCHAR(50) DEFAULT 'neutral',
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',
    
    -- Statistics
    total_tickets INTEGER DEFAULT 0,
    escalated_tickets INTEGER DEFAULT 0,
    avg_sentiment_score DECIMAL(3, 2) DEFAULT 0.0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_contact_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Conversations table (unified thread across channels)
CREATE TABLE conversations (
    conversation_id VARCHAR(255) PRIMARY KEY,
    customer_id VARCHAR(255) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    
    -- Channel info
    channel channel_type NOT NULL,
    thread_id VARCHAR(255),  -- External thread ID (e.g., WhatsApp conversation ID)
    
    -- Status
    status VARCHAR(50) DEFAULT 'active',
    topic VARCHAR(500),
    
    -- Statistics
    message_count INTEGER DEFAULT 0,
    avg_response_time_seconds INTEGER,
    
    -- Sentiment tracking
    overall_sentiment sentiment_type DEFAULT 'neutral',
    sentiment_score DECIMAL(3, 2) DEFAULT 0.0,
    
    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_message_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Messages table (individual messages within conversations)
CREATE TABLE messages (
    message_id VARCHAR(255) PRIMARY KEY,
    conversation_id VARCHAR(255) NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    customer_id VARCHAR(255) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    
    -- Message content
    role VARCHAR(20) NOT NULL CHECK (role IN ('customer', 'agent', 'system')),
    content TEXT NOT NULL,
    
    -- Channel-specific data
    channel channel_type NOT NULL,
    subject VARCHAR(500),
    attachments JSONB DEFAULT '[]'::jsonb,
    
    -- Analysis results
    category ticket_category,
    sentiment sentiment_type,
    sentiment_score DECIMAL(3, 2),
    priority priority_level DEFAULT 'P3',
    
    -- Entities extracted
    entities JSONB DEFAULT '{}'::jsonb,  -- {transaction_ids, dates, amounts, etc.}
    
    -- Response tracking
    is_followup BOOLEAN DEFAULT FALSE,
    requires_escalation BOOLEAN DEFAULT FALSE,
    escalation_reason escalation_reason,
    
    -- Response info (for agent messages)
    response_template VARCHAR(100),
    kb_articles_referenced TEXT[],
    response_time_seconds INTEGER,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Tickets table (formal support tickets)
CREATE TABLE tickets (
    ticket_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(255) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    conversation_id VARCHAR(255) REFERENCES conversations(conversation_id) ON DELETE SET NULL,
    
    -- Ticket details
    subject VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    channel channel_type NOT NULL,
    
    -- Classification
    category ticket_category NOT NULL,
    priority priority_level DEFAULT 'P3',
    status ticket_status DEFAULT 'open',
    
    -- Sentiment tracking
    sentiment sentiment_type DEFAULT 'neutral',
    sentiment_score DECIMAL(3, 2) DEFAULT 0.0,
    
    -- Assignment
    assigned_to VARCHAR(255),
    assigned_team VARCHAR(255),
    
    -- Escalation
    requires_escalation BOOLEAN DEFAULT FALSE,
    escalation_reason escalation_reason,
    escalated_at TIMESTAMP WITH TIME ZONE,
    escalation_notes TEXT,
    
    -- Resolution
    resolution TEXT,
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    -- SLA tracking
    sla_deadline TIMESTAMP WITH TIME ZONE,
    sla_breached BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================================================
-- KNOWLEDGE BASE (with pgvector for semantic search)
-- ============================================================================

-- Knowledge base articles
CREATE TABLE knowledge_base (
    id SERIAL PRIMARY KEY,
    feature VARCHAR(255) NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100),
    
    -- Search keywords
    keywords TEXT[],
    
    -- Embedding for semantic search (OpenAI text-embedding-3-small = 1536 dimensions)
    embedding vector(1536),
    
    -- Metadata
    url VARCHAR(500),
    version VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    view_count INTEGER DEFAULT 0,
    helpful_count INTEGER DEFAULT 0,
    not_helpful_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================================================
-- ESCALATION TRACKING
-- ============================================================================

-- Escalation log
CREATE TABLE escalations (
    escalation_id VARCHAR(255) PRIMARY KEY,
    ticket_id VARCHAR(50) NOT NULL REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    customer_id VARCHAR(255) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    
    -- Escalation details
    reason escalation_reason NOT NULL,
    priority priority_level NOT NULL,
    target_team VARCHAR(255) NOT NULL,
    
    -- Handoff info
    handoff_summary TEXT NOT NULL,
    context_summary TEXT,
    recommended_actions TEXT[],
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending',
    resolved_by VARCHAR(255),
    resolution_notes TEXT,
    
    -- SLA
    sla_response_time VARCHAR(50),
    sla_deadline TIMESTAMP WITH TIME ZONE,
    responded_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================================================
-- ANALYTICS & LOGGING
-- ============================================================================

-- Agent performance tracking
CREATE TABLE agent_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    customer_id VARCHAR(255) REFERENCES customers(customer_id) ON DELETE SET NULL,
    conversation_id VARCHAR(255) REFERENCES conversations(conversation_id) ON DELETE SET NULL,
    
    -- Session info
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    
    -- Performance metrics
    messages_exchanged INTEGER DEFAULT 0,
    avg_response_time_seconds INTEGER,
    intent_accuracy DECIMAL(3, 2),
    sentiment_accuracy DECIMAL(3, 2),
    
    -- Outcome
    resolved BOOLEAN,
    escalated BOOLEAN,
    customer_satisfaction INTEGER CHECK (customer_satisfaction BETWEEN 1 AND 5),
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- System logs
CREATE TABLE system_logs (
    log_id VARCHAR(255) PRIMARY KEY,
    log_level VARCHAR(20) NOT NULL,
    component VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    
    -- Context
    customer_id VARCHAR(255) REFERENCES customers(customer_id) ON DELETE SET NULL,
    ticket_id VARCHAR(50) REFERENCES tickets(ticket_id) ON DELETE SET NULL,
    conversation_id VARCHAR(255) REFERENCES conversations(conversation_id) ON DELETE SET NULL,
    
    -- Error details
    error_code VARCHAR(50),
    stack_trace TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Customers indexes
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_phone ON customers(phone);
CREATE INDEX idx_customers_tier ON customers(account_tier);
CREATE INDEX idx_customers_vip ON customers(is_vip);
CREATE INDEX idx_customers_created ON customers(created_at DESC);

-- Conversations indexes
CREATE INDEX idx_conversations_customer ON conversations(customer_id);
CREATE INDEX idx_conversations_channel ON conversations(channel);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_started ON conversations(started_at DESC);
CREATE INDEX idx_conversations_sentiment ON conversations(overall_sentiment);

-- Messages indexes
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_customer ON messages(customer_id);
CREATE INDEX idx_messages_role ON messages(role);
CREATE INDEX idx_messages_channel ON messages(channel);
CREATE INDEX idx_messages_category ON messages(category);
CREATE INDEX idx_messages_sentiment ON messages(sentiment);
CREATE INDEX idx_messages_priority ON messages(priority);
CREATE INDEX idx_messages_created ON messages(created_at DESC);
CREATE INDEX idx_messages_escalation ON messages(requires_escalation) WHERE requires_escalation = TRUE;

-- Tickets indexes
CREATE INDEX idx_tickets_customer ON tickets(customer_id);
CREATE INDEX idx_tickets_conversation ON tickets(conversation_id);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_priority ON tickets(priority);
CREATE INDEX idx_tickets_category ON tickets(category);
CREATE INDEX idx_tickets_assigned ON tickets(assigned_to);
CREATE INDEX idx_tickets_created ON tickets(created_at DESC);
CREATE INDEX idx_tickets_sla_deadline ON tickets(sla_deadline) WHERE status NOT IN ('resolved', 'closed');
CREATE INDEX idx_tickets_escalated ON tickets(requires_escalation) WHERE requires_escalation = TRUE;

-- Knowledge base indexes (CRITICAL for semantic search)
CREATE INDEX idx_kb_feature ON knowledge_base(feature);
CREATE INDEX idx_kb_category ON knowledge_base(category);
CREATE INDEX idx_kb_active ON knowledge_base(is_active) WHERE is_active = TRUE;

-- pgvector index for semantic search (IVFFlat for fast approximate nearest neighbor)
CREATE INDEX idx_kb_embedding ON knowledge_base 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Alternative: HNSW index (more accurate but slower to build)
-- CREATE INDEX idx_kb_embedding_hnsw ON knowledge_base 
--     USING hnsw (embedding vector_cosine_ops);

-- Escalations indexes
CREATE INDEX idx_escalations_ticket ON escalations(ticket_id);
CREATE INDEX idx_escalations_customer ON escalations(customer_id);
CREATE INDEX idx_escalations_reason ON escalations(reason);
CREATE INDEX idx_escalations_priority ON escalations(priority);
CREATE INDEX idx_escalations_status ON escalations(status);
CREATE INDEX idx_escalations_team ON escalations(target_team);
CREATE INDEX idx_escalations_created ON escalations(created_at DESC);
CREATE INDEX idx_escalations_pending ON escalations(status) WHERE status = 'pending';

-- Agent sessions indexes
CREATE INDEX idx_agent_sessions_customer ON agent_sessions(customer_id);
CREATE INDEX idx_agent_sessions_conversation ON agent_sessions(conversation_id);
CREATE INDEX idx_agent_sessions_started ON agent_sessions(started_at DESC);
CREATE INDEX idx_agent_sessions_resolved ON agent_sessions(resolved);

-- System logs indexes
CREATE INDEX idx_system_logs_level ON system_logs(log_level);
CREATE INDEX idx_system_logs_component ON system_logs(component);
CREATE INDEX idx_system_logs_created ON system_logs(created_at DESC);
CREATE INDEX idx_system_logs_customer ON system_logs(customer_id);
CREATE INDEX idx_system_logs_error ON system_logs(error_code) WHERE error_code IS NOT NULL;

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tickets_updated_at
    BEFORE UPDATE ON tickets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_base_updated_at
    BEFORE UPDATE ON knowledge_base
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate sentiment trend for a customer
CREATE OR REPLACE FUNCTION get_customer_sentiment_trend(p_customer_id VARCHAR(255))
RETURNS TABLE (
    sentiment sentiment_type,
    avg_score DECIMAL(3, 2),
    message_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.sentiment,
        AVG(m.sentiment_score)::DECIMAL(3, 2) as avg_score,
        COUNT(*)::BIGINT as message_count
    FROM messages m
    WHERE m.customer_id = p_customer_id
        AND m.sentiment IS NOT NULL
    GROUP BY m.sentiment
    ORDER BY message_count DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get open tickets count by priority
CREATE OR REPLACE FUNCTION get_open_tickets_by_priority()
RETURNS TABLE (
    priority priority_level,
    count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.priority,
        COUNT(*)::BIGINT
    FROM tickets t
    WHERE t.status NOT IN ('resolved', 'closed')
    GROUP BY t.priority
    ORDER BY t.priority;
END;
$$ LANGUAGE plpgsql;

-- Function to search knowledge base with semantic similarity
CREATE OR REPLACE FUNCTION search_knowledge_base(
    p_query_embedding vector(1536),
    p_limit INTEGER DEFAULT 5,
    p_min_confidence DECIMAL(3, 2) DEFAULT 0.3
)
RETURNS TABLE (
    id INTEGER,
    feature VARCHAR(255),
    title VARCHAR(500),
    content TEXT,
    category VARCHAR(100),
    confidence DECIMAL(3, 2),
    url VARCHAR(500)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        kb.id,
        kb.feature,
        kb.title,
        kb.content,
        kb.category,
        (1 - (kb.embedding <=> p_query_embedding))::DECIMAL(3, 2) as confidence,
        kb.url
    FROM knowledge_base kb
    WHERE kb.is_active = TRUE
        AND (1 - (kb.embedding <=> p_query_embedding)) >= p_min_confidence
    ORDER BY kb.embedding <=> p_query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Customer summary view
CREATE VIEW customer_summary AS
SELECT 
    c.customer_id,
    c.name,
    c.email,
    c.phone,
    c.company,
    c.account_tier,
    c.is_vip,
    c.total_tickets,
    c.escalated_tickets,
    c.avg_sentiment_score,
    c.preferred_channel,
    c.last_contact_at,
    COUNT(DISTINCT CASE WHEN t.status NOT IN ('resolved', 'closed') THEN t.ticket_id END) as open_tickets,
    COUNT(DISTINCT t.ticket_id) as total_tickets_history
FROM customers c
LEFT JOIN tickets t ON c.customer_id = t.customer_id
GROUP BY c.customer_id;

-- Ticket dashboard view
CREATE VIEW ticket_dashboard AS
SELECT 
    DATE(t.created_at) as date,
    t.channel,
    t.category,
    t.priority,
    t.status,
    COUNT(*) as ticket_count,
    AVG(EXTRACT(EPOCH FROM (t.updated_at - t.created_at)))::INTEGER as avg_resolution_seconds
FROM tickets t
GROUP BY DATE(t.created_at), t.channel, t.category, t.priority, t.status;

-- Escalation summary view
CREATE VIEW escalation_summary AS
SELECT 
    e.reason,
    e.priority,
    e.target_team,
    e.status,
    COUNT(*) as escalation_count,
    AVG(EXTRACT(EPOCH FROM (e.responded_at - e.created_at)))::INTEGER as avg_response_seconds
FROM escalations e
GROUP BY e.reason, e.priority, e.target_team, e.status;

-- ============================================================================
-- INITIAL DATA (Optional)
-- ============================================================================

-- Insert sample knowledge base categories
INSERT INTO knowledge_base (feature, title, content, category, keywords) VALUES
('Slack Integration', 'How to Connect Slack', 'Connect TechNova with Slack for real-time notifications...', 'integration', ARRAY['slack', 'integration', 'notifications']),
('Task Management', 'Creating Tasks', 'Create and manage tasks efficiently in TechNova...', 'features', ARRAY['task', 'create', 'manage']),
('Team Collaboration', 'Adding Team Members', 'Invite team members to collaborate on projects...', 'features', ARRAY['team', 'collaboration', 'invite']),
('Billing', 'Subscription Plans', 'TechNova offers Basic, Pro, and Enterprise plans...', 'billing', ARRAY['billing', 'pricing', 'subscription']),
('Security', 'GDPR Compliance', 'TechNova is fully GDPR compliant...', 'security', ARRAY['gdpr', 'compliance', 'security'])
ON CONFLICT DO NOTHING;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
