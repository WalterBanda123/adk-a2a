#!/usr/bin/env python3
"""
Minimal test for Google Cloud Vision API
"""
import os
import sys
import asyncio
import base64

# Add current directory to path
sys.path.append('.')

async def test_minimal_vision():
    """Test minimal vision functionality"""
    print("🔬 Testing minimal Google Cloud Vision API...")
    
    try:
        # Import and test vision components
        from google.cloud import vision
        from google.oauth2 import service_account
        print("✅ Google Cloud imports successful")
        
        # Check credentials file
        credentials_path = 'vision-api-service.json'
        if os.path.exists(credentials_path):
            print(f"✅ Credentials file found: {credentials_path}")
            
            # Try to initialize client
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            client = vision.ImageAnnotatorClient(credentials=credentials)
            print("✅ Vision API client initialized")
            
            # Test with a small image
            print("📷 Testing with small image...")
            
            # Read a small portion of the image
            with open('encoded_image.txt', 'r') as f:
                image_data = f.read(1000)  # Just first 1000 chars
            
            try:
                # Decode image
                if image_data.startswith('data:image'):
                    image_data = image_data.split(',', 1)[1]
                content = base64.b64decode(image_data)
                print(f"✅ Image decoded ({len(content)} bytes)")
                
                # Create vision image
                image = vision.Image(content=content)
                print("✅ Vision Image object created")
                
                # Test a simple API call
                print("🔍 Testing label detection...")
                response = client.label_detection(image=image)
                print(f"✅ Label detection successful! Found {len(response.label_annotations)} labels")
                
                for label in response.label_annotations[:3]:
                    print(f"   - {label.description}: {label.score:.2f}")
                    
            except Exception as decode_error:
                print(f"❌ Image processing error: {decode_error}")
                
        else:
            print(f"❌ Credentials file not found: {credentials_path}")
            
    except Exception as e:
        print(f"❌ Vision API test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_minimal_vision())
