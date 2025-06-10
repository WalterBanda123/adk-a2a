#!/usr/bin/env python3
"""
Test the complete end-to-end image processing flow through the agent server
"""
import base64
import json
import requests
import time

def test_agent_server_with_image():
    """Test the agent server with a real image"""
    
    # Load the image and convert to base64
    image_path = "images-mazoe-ruspberry.jpeg"
    
    try:
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
        print(f"✅ Image loaded and encoded: {len(image_data)} characters")
        
        # Prepare the request payload (exactly like your frontend would send)
        payload = {
            "message": "I want to add a new product from this photo. Can you help me extract the product details?",
            "context": {
                "user_id": "zXUaVlBG05bpsCy5QlGkCNbz4Rm2",
                "image_data": image_data,
                "is_url": False
            },
            "session_id": None
        }
        
        print("🔄 Sending request to agent server...")
        start_time = time.time()
        
        # Send the request to the agent server
        response = requests.post(
            "http://127.0.0.1:8003/run",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ Agent server response received!")
            print(f"⏱️ Total processing time: {end_time - start_time:.2f} seconds")
            print("📋 Response:")
            print(json.dumps(result, indent=2))
            
            # Check if we got a proper response
            if result.get("status") == "success" and result.get("message") != "(No response generated)":
                print("\n🎉 SUCCESS! Agent processed the image and generated a response!")
                return True
            else:
                print(f"\n❌ Agent did not generate a proper response: {result.get('message')}")
                return False
        else:
            print(f"❌ Server error: {response.status_code}")
            print(response.text)
            return False
            
    except FileNotFoundError:
        print(f"❌ Image file not found: {image_path}")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to agent server. Make sure it's running on port 8003.")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing complete end-to-end image processing...")
    print("=" * 60)
    
    success = test_agent_server_with_image()
    
    if success:
        print("\n🎉 End-to-end test completed successfully!")
        print("The agent can now process product images and extract information.")
    else:
        print("\n💥 End-to-end test failed!")
        print("Check the server logs for more details.")
