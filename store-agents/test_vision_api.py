#!/usr/bin/env python3
"""
Quick test to verify Google Cloud Vision API is working
"""
import os
import sys
import asyncio
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.assistant.tools.add_product_vision_tool import ProductVisionProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple base64 test image (1x1 transparent PNG)
TEST_IMAGE_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

async def test_vision_api():
    """Test the Vision API functionality"""
    
    processor = ProductVisionProcessor()
    
    if not processor.client:
        print("❌ Vision API client not initialized")
        print("Make sure vision-api-service.json exists and contains valid credentials")
        return False
    
    print("✅ Vision API client initialized successfully")
    
    try:
        print("🔄 Testing image processing...")
        result = await processor.process_image(TEST_IMAGE_BASE64, is_url=False)
        
        if result.get("success"):
            print("✅ Image processing successful!")
            product = result.get("product", {})
            print(f"Processing time: {product.get('processing_time', 0):.2f}s")
            return True
        else:
            error = result.get("error", "Unknown error")
            print(f"❌ Image processing failed: {error}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during testing: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_vision_api())
    if success:
        print("\n🎉 Vision API is working correctly!")
        sys.exit(0)
    else:
        print("\n💥 Vision API test failed!")
        sys.exit(1)
