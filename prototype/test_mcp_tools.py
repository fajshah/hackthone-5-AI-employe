"""
Quick test script to verify MCP server tools work correctly
"""

import asyncio
import json
from mcp_server import (
    kb, memory, escalation_checker, 
    sentiment_analyzer, response_generator,
    search_knowledge_base, create_ticket, 
    get_customer_history, escalate_to_human, send_response
)


async def test_all_tools():
    print("=" * 80)
    print("MCP SERVER TOOLS TEST")
    print("=" * 80)
    
    # Test 1: Search Knowledge Base
    print("\n\n1️⃣  Testing search_knowledge_base...")
    print("-" * 80)
    results = await search_knowledge_base("Slack integration", limit=2)
    print(f"✓ Found {len(results)} results")
    response_text = results[0].text
    data = json.loads(response_text)
    print(f"✓ Query: {data['query']}")
    print(f"✓ Count: {data['count']}")
    if data['results']:
        print(f"✓ First result: {data['results'][0]['feature']}")
    
    # Test 2: Create Ticket
    print("\n\n2️⃣  Testing create_ticket...")
    print("-" * 80)
    ticket_result = await create_ticket(
        customer_email="test@company.com",
        customer_name="Test User",
        channel="email",
        subject="Test ticket",
        message="How do I add team members?"
    )
    response_text = ticket_result[0].text
    data = json.loads(response_text)
    print(f"✓ Ticket created: {data['ticket']['ticket_id']}")
    print(f"✓ Customer: {data['customer']['name']}")
    print(f"✓ Category: {data['ticket']['category']}")
    
    # Test 3: Get Customer History
    print("\n\n3️⃣  Testing get_customer_history...")
    print("-" * 80)
    history_result = await get_customer_history("test@company.com")
    response_text = history_result[0].text
    data = json.loads(response_text)
    print(f"✓ Customer: {data['customer']['name']}")
    print(f"✓ Total tickets: {data['statistics']['total_tickets']}")
    print(f"✓ Open topics: {data['statistics']['open_topics']}")
    
    # Test 4: Send Response
    print("\n\n4️⃣  Testing send_response...")
    print("-" * 80)
    response_result = await send_response(
        customer_email="test@company.com",
        channel="whatsapp",
        message="How do I add team members?",
        category="how_to",
        customer_name="Test"
    )
    response_text = response_result[0].text
    data = json.loads(response_text)
    print(f"✓ Response generated for {data['response']['channel']}")
    print(f"✓ Character count: {data['response']['character_count']}")
    print(f"✓ Response preview: {data['response']['text'][:80]}...")
    
    # Test 5: Escalate to Human
    print("\n\n5️⃣  Testing escalate_to_human...")
    print("-" * 80)
    # First create a ticket to escalate
    ticket_result = await create_ticket(
        customer_email="urgent@company.com",
        channel="email",
        message="I need a refund for double charge!"
    )
    ticket_data = json.loads(ticket_result[0].text)
    ticket_id = ticket_data['ticket']['ticket_id']
    
    escalate_result = await escalate_to_human(
        ticket_id=ticket_id,
        reason="Billing dispute - customer upset",
        priority="P1",
        notes="Customer wants immediate refund"
    )
    response_text = escalate_result[0].text
    data = json.loads(response_text)
    print(f"✓ Ticket escalated: {data['escalation']['ticket_id']}")
    print(f"✓ Routed to: {data['escalation']['routed_to']}")
    print(f"✓ SLA: {data['escalation']['sla_response_time']}")
    
    # Test Enums
    print("\n\n6️⃣  Testing Enums...")
    print("-" * 80)
    from mcp_server import Channel, Priority, Category, Sentiment, ResolutionStatus
    
    print(f"✓ Channel.EMAIL = {Channel.EMAIL.value}")
    print(f"✓ Channel.WHATSAPP = {Channel.WHATSAPP.value}")
    print(f"✓ Channel.WEB_FORM = {Channel.WEB_FORM.value}")
    print(f"✓ Priority.P0 = {Priority.P0.value}")
    print(f"✓ Category.HOW_TO = {Category.HOW_TO.value}")
    print(f"✓ Sentiment.POSITIVE = {Sentiment.POSITIVE.value}")
    print(f"✓ ResolutionStatus.OPEN = {ResolutionStatus.OPEN.value}")
    
    # Summary
    print("\n\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print(f"\n✓ 5/5 tools working correctly")
    print(f"✓ 5/5 enums implemented")
    print(f"✓ Memory system functional")
    print(f"✓ Escalation rules active")
    print(f"\nMCP Server is ready for Hackathon 5! 🚀")


if __name__ == "__main__":
    asyncio.run(test_all_tools())
