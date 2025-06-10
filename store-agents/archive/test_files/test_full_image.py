#!/usr/bin/env python3
"""
Test the direct vision API with full image data
"""
import requests
import json

def test_direct_vision_api():
    """Test direct vision API with full image data"""
    print("🧪 Testing Direct Vision API with full image data...")
    
    # Load the full image data
    try:
        with open('encoded_image.txt', 'r') as f:
            image_data = f.read().strip()
        print(f"📷 Loaded image data ({len(image_data)} characters)")
    except Exception as e:
        print(f"❌ Failed to load image data: {e}")
        return
    
    # Prepare the request
    payload = {
        "message": "Analyze this product image and extract details",
        "context": {
            "user_id": "test_user",
            "image_data": image_data,
            "is_url": False
        }
    }
    
    try:
        print("🔄 Sending request to direct vision API...")
        response = requests.post(
            "http://localhost:8000/run",
            json=payload,
            timeout=30  # 30 second timeout
        )
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success! Response:")
            print(json.dumps(result, indent=2))
            
            # Extract and display key product info
            if "data" in result and "product" in result["data"]:
                product = result["data"]["product"]
                print("\n🎯 Extracted Product Information:")
                print(f"   Title: {product.get('title', 'N/A')}")
                print(f"   Brand: {product.get('brand', 'N/A')}")
                print(f"   Size: {product.get('size', 'N/A')}{product.get('unit', '')}")
                print(f"   Category: {product.get('category', 'N/A')}")
                print(f"   Confidence: {product.get('confidence', 0):.2f}")
                print(f"   Processing time: {product.get('processing_time', 0):.2f}s")
        else:
            print(f"❌ Error response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out after 30 seconds")
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_direct_vision_api()
