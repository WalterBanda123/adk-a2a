#!/usr/bin/env python3
"""
Test with longer timeout to see if image processing completes
"""
import base64
import json
import requests
import time

def test_with_longer_timeout():
    """Test with extended timeout"""
    
    # Load a smaller test image first
    try:
        with open("images-mazoe-ruspberry.jpeg", "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
            
        # Make the base64 smaller by truncating (for testing)
        # image_data = image_data[:5000] + "=="  # Truncate for faster processing
        
        payload = {
            "message": "I want to add a new product from this photo. Can you help me extract the product details?",
            "context": {
                "user_id": "zXUaVlBG05bpsCy5QlGkCNbz4Rm2",
                "image_data": image_data,
                "is_url": False
            },
            "session_id": None
        }
        
        print(f"📤 Sending request with image data ({len(image_data)} chars)...")
        start_time = time.time()
        
        # Extended timeout
        response = requests.post(
            "http://127.0.0.1:8003/run",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120  # 2 minutes
        )
        
        end_time = time.time()
        print(f"⏱️ Request completed in {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            print("📋 Response:")
            print(json.dumps(result, indent=2))
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request still timed out after 2 minutes")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing with extended timeout...")
    test_with_longer_timeout()
