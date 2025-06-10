"""
Test script for the add_new_product sub-agent
This demonstrates how to use the image-based product addition functionality
"""

import asyncio
import os
import sys
import base64
import json
from dotenv import load_dotenv

# Add the project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

async def test_add_product_subagent():
    """Test the add new product sub-agent with sample data"""
    
    try:
        # Import the sub-agent
        from agents.assistant.add_new_product_subagent import create_add_new_product_subagent
        
        print("🚀 Testing Add New Product Sub-Agent")
        print("=" * 50)
        
        # Create the sub-agent
        agent = await create_add_new_product_subagent()
        print(f"✅ Sub-agent created: {agent.name}")
        
        # Test with a sample base64 image (1x1 pixel PNG for demonstration)
        # In real usage, this would be a proper product image
        sample_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        print("\n📸 Testing image processing...")
        print("Processing sample image...")
        
        # Test the vision tool directly
        from agents.assistant.tools.add_product_vision_tool import create_add_product_vision_tool
        
        vision_tool = create_add_product_vision_tool()
        
        # Call the tool function
        result = await vision_tool.function(
            image_data=sample_image_b64,
            is_url=False,
            user_id="test_user"
        )
        
        print("\n📊 Vision Tool Result:")
        print("-" * 30)
        
        # Parse and display the result
        try:
            result_data = json.loads(result)
            if result_data.get("success"):
                print("✅ Image processing successful!")
                print(f"📝 Title: {result_data.get('title', 'N/A')}")
                print(f"📏 Size: {result_data.get('size', 'N/A')} {result_data.get('unit', '')}")
                print(f"🏷️ Category: {result_data.get('category', 'N/A')} / {result_data.get('subcategory', 'N/A')}")
                print(f"📄 Description: {result_data.get('description', 'N/A')}")
                print(f"🎯 Confidence: {result_data.get('confidence', 0):.2f}")
                print(f"⚡ Processing Time: {result_data.get('processing_time', 0):.2f}s")
            else:
                print(f"❌ Processing failed: {result_data.get('error', 'Unknown error')}")
        except json.JSONDecodeError:
            print(f"📋 Raw result: {result}")
        
        print("\n" + "=" * 50)
        print("🎉 Test completed!")
        
        # Usage example
        print("\n💡 Usage Example:")
        print("-" * 20)
        print("# To use this sub-agent in your application:")
        print("# 1. Send a product image (base64 or URL) to the agent")
        print("# 2. The agent will return structured JSON with product data")
        print("# 3. Use the extracted data to populate your product form")
        print()
        print("# Sample API call:")
        print("# POST /agent/add_new_product")
        print("# {")
        print("#   'image_data': 'base64_encoded_image_string',")
        print("#   'is_url': false,")
        print("#   'user_id': 'your_user_id'")
        print("# }")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure to install dependencies: pip install google-cloud-vision")
    except Exception as e:
        print(f"❌ Test error: {e}")

async def test_url_image():
    """Test with a URL image (if you have one)"""
    
    # Example with a URL (commented out - replace with actual product image URL)
    # image_url = "https://example.com/product-image.jpg"
    
    print("\n🌐 URL Image Test")
    print("-" * 20)
    print("To test with a URL image, uncomment the code in test_url_image()")
    print("and provide a real product image URL")

if __name__ == "__main__":
    print("🔧 Add New Product Sub-Agent Test")
    print("This test requires Google Cloud Vision API credentials")
    print("Set GOOGLE_APPLICATION_CREDENTIALS environment variable")
    print()
    
    # Check for Google Cloud credentials
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("⚠️  Warning: GOOGLE_APPLICATION_CREDENTIALS not set")
        print("   The Vision API may not work without proper credentials")
        print()
    
    # Run the test
    asyncio.run(test_add_product_subagent())
    asyncio.run(test_url_image())
