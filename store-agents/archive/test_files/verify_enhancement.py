#!/usr/bin/env python3
"""
SOLUTION VERIFICATION: Test Your API Endpoint
Run this to verify the enhancement is working
"""
import requests
import base64
import json
import os

def test_your_api_endpoint():
    """Test your actual API endpoint to see the improvement"""
    
    print("🎯 TESTING YOUR API ENDPOINT")
    print("=" * 50)
    
    # Check if image exists
    image_path = 'images-mazoe-ruspberry.jpeg'
    if not os.path.exists(image_path):
        print(f"❌ Test image not found: {image_path}")
        return False
    
    # Read and encode image
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    print(f"✅ Loaded test image: {image_path}")
    
    # Test data with Zimbabwe grocery user
    payload = {
        "message": "Analyze this product image",
        "image_data": image_data,
        "is_url": False,
        "user_id": "grocery_zimb_001"  # This profile has Zimbabwe-specific brands
    }
    
    print("📤 Sending request to your API...")
    print(f"👤 User ID: {payload['user_id']}")
    print(f"📷 Image size: {len(image_data)} characters")
    
    try:
        # Test your endpoint (assuming it's running on port 8000)
        response = requests.post(
            "http://localhost:8000/analyze_image",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n🎉 API RESPONSE RECEIVED!")
            print("=" * 30)
            print(f"Status: {result.get('status', 'unknown')}")
            
            # Extract product data
            product = result.get('data', {}).get('product', {})
            processing_method = result.get('data', {}).get('processing_method', 'unknown')
            
            print(f"\n📦 PRODUCT ANALYSIS:")
            print(f"Title: {product.get('title', 'Unknown')}")
            print(f"Brand: {product.get('brand', 'N/A')}")
            print(f"Size: {product.get('size', 'N/A')} {product.get('unit', '')}")
            print(f"Category: {product.get('category', 'N/A')}")
            print(f"Subcategory: {product.get('subcategory', 'N/A')}")
            print(f"Confidence: {product.get('confidence', 0):.2f}")
            print(f"Processing Method: {processing_method}")
            
            # Check if enhancement is working
            print(f"\n🔍 ENHANCEMENT STATUS:")
            
            if processing_method == "enhanced_dynamic_classifier":
                print("✅ SUCCESS: Using Enhanced Dynamic Classifier!")
                
                if product.get('confidence', 0) > 0.8:
                    print("✅ HIGH CONFIDENCE DETECTION!")
                else:
                    print(f"⚠️ Moderate confidence: {product.get('confidence', 0):.2f}")
                
                if product.get('brand'):
                    print(f"✅ BRAND DETECTED: {product.get('brand')}")
                else:
                    print("⚠️ No brand detected")
                
                if product.get('size'):
                    print(f"✅ SIZE DETECTED: {product.get('size')} {product.get('unit', '')}")
                else:
                    print("⚠️ No size detected")
                
                print("\n🎉 YOUR API IS NOW ENHANCED!")
                print("🚀 Users will get much better product detection!")
                return True
                
            elif processing_method == "direct_vision_api":
                print("❌ STILL USING OLD SYSTEM")
                print("📝 The direct_vision_server.py needs to be restarted")
                print("💡 Solution: Restart your server to load the enhanced code")
                return False
            else:
                print(f"❓ UNKNOWN PROCESSING METHOD: {processing_method}")
                return False
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Is your server running?")
        print("💡 Start your server with: python direct_vision_server.py")
        return False
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

def show_curl_example():
    """Show how to test with curl"""
    print("\n" + "=" * 60)
    print("🛠️  ALTERNATIVE: TEST WITH CURL")
    print("=" * 60)
    
    # Read image for curl example
    image_path = 'images-mazoe-ruspberry.jpeg'
    if os.path.exists(image_path):
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Truncate for display
        image_preview = image_data[:100] + "..." if len(image_data) > 100 else image_data
        
        curl_command = f'''curl -X POST http://localhost:8000/analyze_image \\
  -H "Content-Type: application/json" \\
  -d '{{
    "message": "Analyze this product",
    "image_data": "{image_preview}",
    "is_url": false,
    "user_id": "grocery_zimb_001"
  }}'
'''
        
        print("Copy and run this curl command:")
        print(curl_command)
        print("\n💡 Replace the image_data with the full base64 string")

if __name__ == "__main__":
    print("🔧 ENHANCED PRODUCT DETECTION - VERIFICATION SCRIPT")
    print("=" * 60)
    
    success = test_your_api_endpoint()
    
    if not success:
        show_curl_example()
        
        print("\n📋 TROUBLESHOOTING STEPS:")
        print("1. Make sure your server is running: python direct_vision_server.py")
        print("2. The server should show 'Enhanced Vision Processor' in logs")
        print("3. Test user profile 'grocery_zimb_001' should exist")
        print("4. Google credentials should be set in environment")
        
    print("\n" + "=" * 60)
