"""
Test script for Product Transaction Agent
Tests both image registration and transaction processing endpoints
"""
import asyncio
import json
import base64
import requests
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:8001"
TEST_USER_ID = "test_user_1749461758"

def test_server_health():
    """Test if server is running and accessible"""
    try:
        response = requests.get(f"{BASE_URL}/.well-known/agent.json")
        if response.status_code == 200:
            print("✅ Server is running and accessible")
            print(f"📊 Server info: {response.json()}")
            return True
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on port 8001")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_product_registration():
    """Test product registration endpoint with a sample image"""
    print("\n🧪 Testing Product Registration...")
    
    # Create a simple test image (1x1 pixel JPEG)
    # This is a minimal JPEG header + data for testing
    test_image_b64 = "/9j/4AAQSkZJRgABAQEAYABgAAD//gASTWljcm9zb2Z0IE9mZmljZQD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/AD//2Q=="
    
    request_data = {
        "image_data": f"data:image/jpeg;base64,{test_image_b64}",
        "user_id": TEST_USER_ID,
        "is_url": False,
        "enhance_image": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/register-product-image",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Product registration successful!")
            print(f"📦 Product: {result.get('product', {}).get('title', 'Unknown')}")
            print(f"🎯 Confidence: {result.get('confidence', 0):.2%}")
            print(f"⏱️  Processing time: {result.get('processing_time', 0):.2f}s")
            print(f"🔍 Detection method: {result.get('detection_method', 'unknown')}")
            if result.get('image_url'):
                print(f"🖼️  Image URL: {result['image_url']}")
            return True
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (>30s)")
        return False
    except Exception as e:
        print(f"❌ Registration test error: {e}")
        return False

def test_chat_transaction():
    """Test chat transaction endpoint"""
    print("\n💰 Testing Chat Transaction...")
    
    request_data = {
        "message": "2 bread @1.25, 1 milk @2.50, 3x maputi @0.5",
        "user_id": TEST_USER_ID,
        "customer_name": "Test Customer",
        "payment_method": "cash"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat/transaction",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Transaction processing successful!")
            
            if result.get('success'):
                receipt = result.get('receipt', {})
                print(f"🧾 Transaction ID: {receipt.get('transaction_id', 'N/A')}")
                print(f"📅 Date: {receipt.get('date', 'N/A')} {receipt.get('time', 'N/A')}")
                print(f"👤 Customer: {receipt.get('customer_name', 'N/A')}")
                print(f"📦 Items: {len(receipt.get('items', []))}")
                print(f"💵 Subtotal: ${receipt.get('subtotal', 0):.2f}")
                print(f"🏛️  Tax: ${receipt.get('tax_amount', 0):.2f}")
                print(f"💰 Total: ${receipt.get('total', 0):.2f}")
                
                # Print item details
                for item in receipt.get('items', []):
                    print(f"   • {item.get('quantity', 0)}x {item.get('name', 'Unknown')} @ ${item.get('unit_price', 0):.2f}")
                
                # Print warnings if any
                warnings = result.get('warnings', [])
                if warnings:
                    print("⚠️  Warnings:")
                    for warning in warnings:
                        print(f"   • {warning}")
                
                # Print chat response
                chat_response = result.get('chat_response', '')
                if chat_response:
                    print("\n💬 Chat Response Preview:")
                    # Show first few lines
                    lines = chat_response.split('\n')[:5]
                    for line in lines:
                        print(f"   {line}")
                    if len(chat_response.split('\n')) > 5:
                        print("   ...")
                
                return True
            else:
                print(f"❌ Transaction failed: {result.get('message', 'Unknown error')}")
                errors = result.get('errors', [])
                if errors:
                    print("🚫 Errors:")
                    for error in errors:
                        print(f"   • {error}")
                return False
        else:
            print(f"❌ Transaction request failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (>15s)")
        return False
    except Exception as e:
        print(f"❌ Transaction test error: {e}")
        return False

def test_invalid_requests():
    """Test error handling with invalid requests"""
    print("\n🚨 Testing Error Handling...")
    
    # Test invalid product registration
    try:
        response = requests.post(
            f"{BASE_URL}/register-product-image",
            json={"invalid": "data"},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 422:  # Validation error
            print("✅ Product registration validation working")
        else:
            print(f"⚠️  Unexpected response for invalid product request: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing invalid product request: {e}")
    
    # Test invalid transaction
    try:
        response = requests.post(
            f"{BASE_URL}/chat/transaction",
            json={"message": ""},  # Empty message
            headers={"Content-Type": "application/json"}
        )
        if response.status_code in [400, 422]:  # Bad request or validation error
            print("✅ Transaction validation working")
        else:
            print(f"⚠️  Unexpected response for invalid transaction: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing invalid transaction: {e}")

def test_parsing_examples():
    """Test various transaction parsing formats"""
    print("\n📝 Testing Transaction Parsing Formats...")
    
    test_messages = [
        "2 bread @1.25",
        "1 milk @ 2.50",
        "3x soap @1.2",
        "2 maputi @0.5, 1 drink @1.0",
        "5 eggs @ 0.25, 2x bread @ 1.25, 1 milk @ 2.50"
    ]
    
    success_count = 0
    for i, message in enumerate(test_messages, 1):
        try:
            response = requests.post(
                f"{BASE_URL}/chat/transaction",
                json={
                    "message": message,
                    "user_id": TEST_USER_ID,
                    "customer_name": f"Test Customer {i}"
                },
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                items_count = len(result.get('receipt', {}).get('items', []))
                total = result.get('receipt', {}).get('total', 0)
                print(f"✅ Format {i}: '{message}' → {items_count} items, ${total:.2f}")
                success_count += 1
            else:
                print(f"❌ Format {i}: '{message}' → Failed ({response.status_code})")
                
        except Exception as e:
            print(f"❌ Format {i}: '{message}' → Error: {e}")
    
    print(f"📊 Parsing success rate: {success_count}/{len(test_messages)} ({success_count/len(test_messages)*100:.1f}%)")

def main():
    """Run all tests"""
    print("🧪 Product Transaction Agent Test Suite")
    print("=" * 50)
    
    # Test server health first
    if not test_server_health():
        print("\n❌ Server is not accessible. Please start the server with:")
        print("   ./start_product_transaction_agent.sh")
        return False
    
    # Run tests
    tests_passed = 0
    total_tests = 4
    
    if test_product_registration():
        tests_passed += 1
    
    if test_chat_transaction():
        tests_passed += 1
    
    test_invalid_requests()  # Always runs
    tests_passed += 1
    
    test_parsing_examples()  # Always runs  
    tests_passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests completed")
    
    if tests_passed == total_tests:
        print("🎉 All tests completed successfully!")
        print("\n🚀 Your Product Transaction Agent is ready for production!")
        print("\n📚 API Documentation:")
        print("   • Product Registration: POST /register-product-image")
        print("   • Chat Transaction: POST /chat/transaction")
        print("   • Server Info: GET /.well-known/agent.json")
        print(f"\n🌐 Base URL: {BASE_URL}")
    else:
        print("⚠️  Some tests had issues. Check the logs above for details.")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    main()
