#!/usr/bin/env python3
"""
Test intent detection and transaction handling
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

async def test_intent_detection():
    """Test intent detection for different message types"""
    
    from unified_chat_agent import UnifiedChatCoordinator
    
    coordinator = UnifiedChatCoordinator()
    
    print("🔍 Testing intent detection...")
    print("=" * 50)
    
    test_messages = [
        ("Show me my inventory", "Should be: inventory_query"),
        ("Sold 2 bottles of Mazoe at $5 each", "Should be: transaction"),
        ("I sold 3 items today", "Should be: transaction"),
        ("Customer bought 1 bottle", "Should be: transaction"),
        ("Check stock levels", "Should be: inventory_query"),
        ("What's my stock", "Should be: inventory_query"),
        ("Selling 5 bottles for $10", "Should be: transaction"),
        ("Transaction for John - 2 items", "Should be: transaction"),
    ]
    
    for message, expected in test_messages:
        intent = coordinator.detect_intent(message)
        print(f"📝 Message: '{message}'")
        print(f"🎯 Intent: {intent} | {expected}")
        print(f"{'✅' if expected.split(': ')[1] == intent else '❌'}")
        print("-" * 30)

async def test_transaction_processing():
    """Test actual transaction processing"""
    
    from unified_chat_agent import UnifiedChatCoordinator, ChatRequest
    
    coordinator = UnifiedChatCoordinator()
    
    print("\n🔍 Testing transaction processing...")
    print("=" * 50)
    
    request = ChatRequest(
        message='Sold 2 bottles of Mazoe at $5 each',
        user_id='9IbW1ssRI9cneCFC7a1zKOGW1Qa2',
        session_id=None,
        context={},
        image_data=None,
        is_url=False
    )
    
    response = await coordinator.process_chat(request)
    print(f"📋 Response: {response.message}")
    print(f"🤖 Agent used: {response.agent_used}")
    print(f"✅ Status: {response.status}")
    
    # Check if it's a transaction response
    if response.agent_used == "transaction_processor":
        print("✅ Correctly identified as transaction!")
        if "receipt" in response.data or "confirmation" in response.message.lower():
            print("✅ Transaction processed successfully!")
        else:
            print("⚠️ Transaction detected but may not have processed correctly")
    else:
        print("❌ Incorrectly routed - should be transaction_processor")

if __name__ == "__main__":
    asyncio.run(test_intent_detection())
    asyncio.run(test_transaction_processing())
