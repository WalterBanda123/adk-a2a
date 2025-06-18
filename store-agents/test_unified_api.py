#!/usr/bin/env python3
"""
Test script for the Unified Chat Agent API
Tests all major functionality through the /run endpoint
"""
import requests
import json
import base64
import sys

API_BASE = "http://localhost:8000"
TEST_USER_ID = "9IbW1ssRI9cneCFC7a1zKOGW1Qa2"

def test_api_endpoint(message, image_data=None):
    """Test the /run endpoint with a message"""
    payload = {
        "message": message,
        "user_id": TEST_USER_ID,
        "session_id": "test_session"
    }
    
    if image_data:
        payload["image_data"] = image_data
        payload["is_url"] = False
    
    try:
        response = requests.post(f"{API_BASE}/run", json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e), "status": "error"}

def main():
    print("🧪 Testing Unified Chat Agent API")
    print("=" * 50)
    
    # Test 1: Health check
    print("\\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
        print("   Make sure the server is running: ./start_unified_agent.sh")
        return
    
    # Test 2: List agents
    print("\\n2. Testing agents list...")
    try:
        response = requests.get(f"{API_BASE}/agents")
        agents_data = response.json()
        print(f"   Available agents: {len(agents_data.get('agents', {}))}")
        for agent, desc in agents_data.get('agents', {}).items():
            print(f"   • {agent}: {desc}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Help request
    print("\\n3. Testing help request...")
    result = test_api_endpoint("Help - what can you do?")
    print(f"   Agent: {result.get('agent_used')}")
    print(f"   Status: {result.get('status')}")
    print(f"   Response: {result.get('message', '')[:100]}...")
    
    # Test 4: Inventory query
    print("\\n4. Testing inventory query...")
    result = test_api_endpoint("Check low stock items")
    print(f"   Agent: {result.get('agent_used')}")
    print(f"   Status: {result.get('status')}")
    print(f"   Response: {result.get('message', '')[:100]}...")
    
    # Test 5: Transaction attempt
    print("\\n5. Testing transaction processing...")
    result = test_api_endpoint("Sold 2 apples at $1.50 each")
    print(f"   Agent: {result.get('agent_used')}")
    print(f"   Status: {result.get('status')}")
    print(f"   Response: {result.get('message', '')[:100]}...")
    
    # Test 6: Petty cash
    print("\\n6. Testing petty cash transaction...")
    result = test_api_endpoint("Petty cash $20 for office supplies")
    print(f"   Agent: {result.get('agent_used')}")
    print(f"   Status: {result.get('status')}")
    print(f"   Response: {result.get('message', '')[:100]}...")
    
    # Test 7: Store information
    print("\\n7. Testing store information...")
    result = test_api_endpoint("Store information")
    print(f"   Agent: {result.get('agent_used')}")
    print(f"   Status: {result.get('status')}")
    print(f"   Response: {result.get('message', '')[:100]}...")
    
    # Test 8: Image upload (without actual image)
    print("\\n8. Testing product registration request...")
    result = test_api_endpoint("Register this product")
    print(f"   Agent: {result.get('agent_used')}")
    print(f"   Status: {result.get('status')}")
    print(f"   Response: {result.get('message', '')[:100]}...")
    
    print("\\n" + "=" * 50)
    print("✅ API testing complete!")
    print("\\n💡 To test with a real image:")
    print("   1. Start the server: ./start_unified_agent.sh")
    print("   2. Use your frontend to send image data")
    print("   3. Or modify this script to include base64 image data")

if __name__ == "__main__":
    main()
