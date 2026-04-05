"""
Script to seed knowledge base with sample data
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Sample product documentation
SAMPLE_DOCS = [
    {
        'feature': 'Slack Integration',
        'content': """Connect TechNova with Slack for real-time notifications.

Steps to integrate:
1. Go to Settings → Integrations
2. Click "Connect Slack"
3. Authorize TechNova in Slack
4. Select channels for notifications
5. Click "Save"

Features:
- Task notifications in Slack channels
- @mentions sync between platforms
- Quick task creation from Slack messages
- Status updates posted automatically

Troubleshooting:
- Make sure you have admin permissions
- Check Slack workspace settings
- Verify webhook URLs are correct""",
        'category': 'integration'
    },
    {
        'feature': 'Task Management',
        'content': """Create and manage tasks efficiently.

Creating tasks:
1. Click + button in project
2. Enter task name
3. Assign team member
4. Set due date
5. Add description and attachments

Features:
- AI-powered task suggestions
- Auto-assign based on workload
- Recurring tasks
- Task templates
- Subtasks and checklists

Tips:
- Use / to quickly create tasks
- Drag and drop to reorder
- Use labels for organization""",
        'category': 'features'
    },
    {
        'feature': 'Team Collaboration',
        'content': """Work together with your team effectively.

Adding team members:
1. Go to Settings → Team
2. Click "Invite Member"
3. Enter email address
4. Select role (Admin, Member, Viewer)
5. Send invitation

Features:
- Real-time editing
- Comments and mentions
- Activity feed
- Team dashboard
- Permission levels

Best practices:
- Use @mentions for important updates
- Set clear roles and permissions
- Regular team check-ins""",
        'category': 'features'
    },
    {
        'feature': 'Billing and Pricing',
        'content': """Manage your subscription and billing.

Plans:
- Basic: Free for up to 5 users
- Pro: $12/user/month - Advanced features
- Enterprise: Custom pricing for 50+ users

Payment methods:
- Credit/Debit cards
- Bank transfer (Enterprise)
- Annual billing (20% discount)

Refund policy:
- 30-day money-back guarantee
- Pro-rated refunds for downgrades
- Contact billing@technova.com for refunds

Common issues:
- Payment failed: Check card details
- Double charge: Usually resolves in 3-5 days
- Invoice download: Settings → Billing → Invoices""",
        'category': 'billing'
    },
    {
        'feature': 'Security and Compliance',
        'content': """Enterprise-grade security features.

Security features:
- SSO/SAML integration
- Two-factor authentication (2FA)
- End-to-end encryption
- Audit logs
- IP allowlisting

Compliance:
- GDPR compliant
- SOC 2 Type II certified
- HIPAA available (Enterprise)
- Data residency options

Data protection:
- Daily automated backups
- 99.9% uptime SLA
- Disaster recovery plan
- Regular security audits

For compliance questions, contact security@technova.com""",
        'category': 'security'
    }
]


def get_embedding(text):
    """Get OpenAI embedding for text"""
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def seed_database():
    """Seed knowledge base with sample data"""
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    
    for doc in SAMPLE_DOCS:
        # Get embedding
        embedding = get_embedding(doc['feature'] + ' ' + doc['content'])
        
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO knowledge_base (feature, content, category, embedding)
                VALUES (%s, %s, %s, %s)
            """, (doc['feature'], doc['content'], doc['category'], embedding))
        
        print(f"✓ Added: {doc['feature']}")
    
    conn.commit()
    conn.close()
    print("\n✅ Knowledge base seeded successfully!")


if __name__ == "__main__":
    seed_database()
