#!/usr/bin/env python3
"""
Test the add_product_vision_tool with the actual image in the project
"""
import os
import sys
import asyncio
import base64
import json
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.assistant.tools.add_product_vision_tool import create_add_product_vision_tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_with_real_image():
    """Test the vision tool with the real product image"""
    
    # Path to the image file
    image_path = os.path.join(os.path.dirname(__file__), 'images-mazoe-ruspberry.jpeg')
    
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return False
    
    print(f"✅ Found image: {image_path}")
    
    try:
        # Read and encode the image
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        print(f"✅ Image encoded to base64 ({len(image_data)} characters)")
        
        # Create the vision tool
        vision_tool = create_add_product_vision_tool()
        
        print("🔄 Calling add_product_vision_tool...")
        
        # Call the tool
        result = await vision_tool.func(
            image_data=image_data,
            is_url=False,
            user_id="test_user_vision"
        )
        
        print("📋 Raw result:")
        print(result)
        print("\n" + "="*60 + "\n")
        
        # Parse and display the result nicely
        try:
            parsed_result = json.loads(result)
            
            if parsed_result.get("success"):
                print("🎉 SUCCESS! Product analysis complete:")
                print(f"📦 Title: {parsed_result.get('title', 'N/A')}")
                print(f"📏 Size: {parsed_result.get('size', 'N/A')} {parsed_result.get('unit', '')}")
                print(f"🏷️ Category: {parsed_result.get('category', 'N/A')}")
                print(f"🔖 Subcategory: {parsed_result.get('subcategory', 'N/A')}")
                print(f"📝 Description: {parsed_result.get('description', 'N/A')}")
                print(f"🎯 Confidence: {parsed_result.get('confidence', 0):.2f}")
                print(f"⏱️ Processing Time: {parsed_result.get('processing_time', 0):.2f}s")
                return True
            else:
                print(f"❌ Vision tool failed: {parsed_result.get('error', 'Unknown error')}")
                return False
                
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse result as JSON: {e}")
            print(f"Raw result: {result}")
            return False
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing add_product_vision_tool with real image...")
    print("="*60)
    
    success = asyncio.run(test_with_real_image())
    
    if success:
        print("\n🎉 Vision API test completed successfully!")
        print("The image processing is working correctly.")
    else:
        print("\n💥 Vision API test failed!")
        print("Check the logs above for error details.")
    
    print("="*60)
