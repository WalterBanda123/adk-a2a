#!/usr/bin/env python3
"""
Full test for Google Cloud Vision API with our product image
"""
import os
import sys
import asyncio
import base64

# Add current directory to path
sys.path.append('.')

async def test_full_vision():
    """Test full vision functionality with our product image"""
    print("🔬 Testing Google Cloud Vision API with full product image...")
    
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
            
            # Read the full image data
            with open('encoded_image.txt', 'r') as f:
                image_data = f.read().strip()
            
            print(f"📷 Loaded full image data ({len(image_data)} characters)")
            
            try:
                # Decode image
                if image_data.startswith('data:image'):
                    image_data = image_data.split(',', 1)[1]
                content = base64.b64decode(image_data)
                print(f"✅ Image decoded ({len(content)} bytes)")
                
                # Create vision image
                image = vision.Image(content=content)
                print("✅ Vision Image object created")
                
                # Test label detection
                print("🔍 Testing label detection...")
                response = client.label_detection(image=image)
                print(f"✅ Label detection successful! Found {len(response.label_annotations)} labels")
                
                for label in response.label_annotations[:5]:
                    print(f"   - {label.description}: {label.score:.2f}")
                
                # Test text detection
                print("🔍 Testing text detection...")
                text_response = client.text_detection(image=image)
                print(f"✅ Text detection successful! Found {len(text_response.text_annotations)} text elements")
                
                if text_response.text_annotations:
                    # Print first text element (usually contains all text)
                    full_text = text_response.text_annotations[0].description[:300]
                    print(f"   Text found: {repr(full_text)}")
                
                return True
                    
            except Exception as decode_error:
                print(f"❌ Image processing error: {decode_error}")
                import traceback
                traceback.print_exc()
                return False
                
        else:
            print(f"❌ Credentials file not found: {credentials_path}")
            return False
            
    except Exception as e:
        print(f"❌ Vision API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_full_vision())
    if success:
        print("\n🎉 Vision API test completed successfully!")
    else:
        print("\n❌ Vision API test failed!")
