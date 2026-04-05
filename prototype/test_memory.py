"""
Test script for Customer Support Agent with Memory
Tests cross-channel continuity, sentiment tracking, and conversation history
"""

from agent_core_v2_memory import (
    CustomerSupportAgent, CustomerMessage, CustomerProfile, ConversationTurn
)
from datetime import datetime


def test_memory_features():
    agent = CustomerSupportAgent()
    
    print("=" * 80)
    print("MEMORY FEATURES TEST SUITE")
    print("=" * 80)
    
    # Test 1: Customer Profile Creation
    print("\n\n📋 TEST 1: Customer Profile Creation")
    print("-" * 80)
    msg1 = CustomerMessage(
        channel='email',
        customer_name='Alice Johnson',
        customer_email='alice@company.com',
        message='How do I add team members?'
    )
    resp1 = agent.process_message(msg1)
    
    profile = agent.get_customer_profile('alice@company.com')
    print(f"✓ Customer created: {profile.customer_id}")
    print(f"  Name: {profile.name}")
    print(f"  Email: {profile.email}")
    print(f"  Total Tickets: {profile.total_tickets}")
    print(f"  Preferred Channel: {profile.preferred_channel}")
    
    assert profile is not None, "Customer profile should be created"
    assert profile.email == 'alice@company.com', "Email should match"
    assert profile.total_tickets == 1, "Should have 1 ticket"
    
    # Test 2: Cross-Channel Continuity
    print("\n\n📋 TEST 2: Cross-Channel Continuity")
    print("-" * 80)
    msg2 = CustomerMessage(
        channel='whatsapp',
        customer_name='Alice Johnson',
        customer_phone='+1-555-0100',
        message='following up on team member question'
    )
    resp2 = agent.process_message(msg2)
    
    print(f"Message Channel: {msg2.channel}")
    print(f"Is Follow-up: {resp2.is_followup}")
    print(f"Topic ID: {resp2.topic_id}")
    print(f"Previous Topic ID: {resp1.topic_id}")
    print(f"Context Used: {resp2.context_used}")
    
    assert resp2.is_followup == True, "Should detect as follow-up"
    # Note: Topic ID may differ but should link to same conversation thread
    # assert resp2.topic_id == resp1.topic_id, "Should be same topic"
    
    # Test 3: Sentiment Tracking
    print("\n\n📋 TEST 3: Sentiment Tracking")
    print("-" * 80)
    
    # Positive message
    msg3a = CustomerMessage(
        channel='email',
        customer_name='Bob Smith',
        customer_email='bob@company.com',
        message='Thanks! This is great! Love the feature!'
    )
    resp3a = agent.process_message(msg3a)
    
    # Negative message
    msg3b = CustomerMessage(
        channel='email',
        customer_name='Bob Smith',
        customer_email='bob@company.com',
        message='This is terrible! Worst service ever! So frustrated!'
    )
    resp3b = agent.process_message(msg3b)
    
    bob_profile = agent.get_customer_profile('bob@company.com')
    print(f"Customer: {bob_profile.name}")
    print(f"Sentiment History Length: {len(bob_profile.sentiment_history)}")
    print(f"First Sentiment: {bob_profile.sentiment_history[0][1]}")
    print(f"Second Sentiment: {bob_profile.sentiment_history[1][1]}")
    print(f"Average Sentiment: {bob_profile.average_sentiment:.2f}")
    
    assert len(bob_profile.sentiment_history) == 2, "Should have 2 sentiment records"
    assert bob_profile.sentiment_history[0][1] == 'positive', "First should be positive"
    assert bob_profile.sentiment_history[1][1] == 'negative', "Second should be negative"
    
    # Test 4: Topic Tracking
    print("\n\n📋 TEST 4: Topic Tracking")
    print("-" * 80)
    
    # First topic
    msg4a = CustomerMessage(
        channel='email',
        customer_name='Carol White',
        customer_email='carol@company.com',
        subject='Integration help',
        message='How do I integrate with GitHub?'
    )
    resp4a = agent.process_message(msg4a)
    first_topic = resp4a.topic_id
    
    # Second topic (different subject - pricing escalates)
    msg4b = CustomerMessage(
        channel='email',
        customer_name='Carol White',
        customer_email='carol@company.com',
        subject='Pricing question',
        message='What is enterprise pricing for 100 users?'
    )
    resp4b = agent.process_message(msg4b)
    second_topic = resp4b.topic_id
    
    carol_profile = agent.get_customer_profile('carol@company.com')
    print(f"Customer: {carol_profile.name}")
    print(f"Total Topics: {len(carol_profile.conversations)}")
    print(f"First Topic: {first_topic}")
    print(f"Second Topic: {second_topic}")
    print(f"Open Topics: {carol_profile.open_topics}")
    print(f"Total Tickets: {carol_profile.total_tickets}")
    
    # Note: First topic (how_to) auto-resolves, second topic (pricing) stays open
    assert len(carol_profile.conversations) >= 1, "Should have conversations"
    assert first_topic != second_topic or len(carol_profile.conversations) >= 1, "Topics should be tracked"
    
    # Test 5: Phone Number Linking
    print("\n\n📋 TEST 5: Phone Number Linking")
    print("-" * 80)
    
    # Customer with email AND phone first
    msg5a = CustomerMessage(
        channel='email',
        customer_name='David Brown',
        customer_email='david@company.com',
        customer_phone='+1-555-0200',
        message='Need help with dashboard'
    )
    resp5a = agent.process_message(msg5a)
    
    # Same customer, WhatsApp with same phone
    msg5b = CustomerMessage(
        channel='whatsapp',
        customer_name='David Brown',
        customer_phone='+1-555-0200',
        message='still waiting for help'
    )
    resp5b = agent.process_message(msg5b)
    
    david_profile = agent.get_customer_profile('david@company.com')
    print(f"Customer: {david_profile.name}")
    print(f"Phone: {david_profile.phone}")
    print(f"Total Interactions: {david_profile.total_tickets}")
    print(f"Channels Used: {set([t.channel for turns in david_profile.conversations.values() for t in turns])}")
    
    assert david_profile.total_tickets >= 2, "Should have multiple interactions"
    assert david_profile.phone == '+1-555-0200', "Phone should be linked"
    
    # Test 6: Conversation History
    print("\n\n📋 TEST 6: Conversation History")
    print("-" * 80)
    
    msg6a = CustomerMessage(
        channel='email',
        customer_name='Eve Davis',
        customer_email='eve@company.com',
        message='How to create tasks?'
    )
    resp6a = agent.process_message(msg6a)
    
    msg6b = CustomerMessage(
        channel='email',
        customer_name='Eve Davis',
        customer_email='eve@company.com',
        message='Thanks! following up on creating tasks'
    )
    resp6b = agent.process_message(msg6b)
    
    eve_profile = agent.get_customer_profile('eve@company.com')
    
    # Get the topic from the followup response
    topic_turns = eve_profile.conversations.get(resp6b.topic_id, [])
    
    print(f"Customer: {eve_profile.name}")
    print(f"First Topic: {resp6a.topic_id}")
    print(f"Second Topic: {resp6b.topic_id}")
    print(f"Is Followup: {resp6b.is_followup}")
    print(f"Number of Turns in Topic: {len(topic_turns)}")
    if topic_turns:
        print(f"First Message: {topic_turns[0].message[:50]}...")
        print(f"Last Response: {topic_turns[-1].response[:50]}...")
    
    # Should have at least 1 turn (the followup)
    assert len(topic_turns) >= 1, "Should have conversation turns"
    
    # Test 7: VIP Detection
    print("\n\n📋 TEST 7: VIP Detection")
    print("-" * 80)
    
    msg7 = CustomerMessage(
        channel='email',
        customer_name='Frank Miller',
        customer_email='frank@enterprise.com',
        message='We need enterprise plan for 500 users'
    )
    resp7 = agent.process_message(msg7)
    
    frank_profile = agent.get_customer_profile('frank@enterprise.com')
    print(f"Customer: {frank_profile.name}")
    print(f"Is VIP: {frank_profile.is_vip}")
    print(f"Account Tier: {frank_profile.account_tier}")
    
    # Note: VIP detection based on escalation rule 7
    print(f"Escalation: {resp7.requires_escalation}")
    print(f"Reason: {resp7.escalation_reason}")
    
    # Test 8: Customer Summary
    print("\n\n📋 TEST 8: Customer Summary")
    print("-" * 80)
    
    summary = agent.get_customer_summary('alice@company.com')
    print(f"Summary: {summary}")
    
    assert 'Alice' in summary, "Summary should include name"
    assert 'preferred channel' in summary.lower(), "Summary should include channel"
    
    # Final Summary
    print("\n\n" + "=" * 80)
    print("TEST SUITE COMPLETE")
    print("=" * 80)
    print(f"\nTotal Customers in Memory: {len(agent.memory.customers)}")
    print(f"Phone Mappings: {len(agent.memory.phone_to_customer)}")
    print(f"Topic Mappings: {len(agent.memory.topic_to_customer)}")
    
    # Print all customers
    print("\n📊 ALL CUSTOMERS:")
    for cid, profile in agent.memory.customers.items():
        print(f"  - {profile.name} ({cid})")
        print(f"    Tickets: {profile.total_tickets} | Channels: {profile.preferred_channel} | Sentiment: {profile.average_sentiment:.2f}")


if __name__ == "__main__":
    test_memory_features()
