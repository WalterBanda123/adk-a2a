#!/usr/bin/env python3
"""
Test script for the new direct vision processing approach
"""
import asyncio
import sys
import os

# Add current directory to path
sys.path.append('.')

def test_imports():
    """Test if all imports work"""
    print("🔄 Testing imports...")
    
    try:
        from agents.assistant.tools.add_product_vision_tool import ProductVisionProcessor
        print("✅ ProductVisionProcessor imported successfully")
        
        from agents.assistant.task_manager import TaskManager
        print("✅ TaskManager imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_direct_vision():
    """Test direct vision processing"""
    print("\n🔄 Testing direct vision processing...")
    
    try:
        # Read test image
        with open('encoded_image.txt', 'r') as f:
            image_data = f.read().strip()
        
        print(f"📷 Loaded image data ({len(image_data)} characters)")
        
        # Initialize processor
        from agents.assistant.tools.add_product_vision_tool import ProductVisionProcessor
        processor = ProductVisionProcessor()
        
        # Process image
        result = await processor.process_image(image_data, is_url=False)
        
        print(f"📊 Vision processing result:")
        print(f"   Success: {result.get('success', False)}")
        
        if result.get('success'):
            product = result.get('product', {})
            print(f"   Title: {product.get('title', 'N/A')}")
            print(f"   Brand: {product.get('brand', 'N/A')}")
            print(f"   Size: {product.get('size', 'N/A')}{product.get('unit', '')}")
            print(f"   Category: {product.get('category', 'N/A')}")
            print(f"   Processing time: {product.get('processing_time', 0):.2f}s")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
            
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Direct vision test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_task_manager():
    """Test TaskManager with direct vision"""
    print("\n🔄 Testing TaskManager with direct vision...")
    
    try:
        # Read test image
        with open('encoded_image.txt', 'r') as f:
            image_data = f.read().strip()
        
        # Import agent for TaskManager
        from agents.assistant.agent import agent
        from agents.assistant.task_manager import TaskManager
        
        # Initialize TaskManager
        task_manager = TaskManager(agent)
        
        # Test context with image data
        context = {
            "user_id": "test_user",
            "image_data": image_data,
            "is_url": False
        }
        
        # Process task
        result = await task_manager.process_task(
            message="Analyze this product image and extract details",
            context=context
        )
        
        print(f"📊 TaskManager result:")
        print(f"   Status: {result.get('status', 'N/A')}")
        print(f"   Message: {result.get('message', 'N/A')[:100]}...")
        
        data = result.get('data', {})
        if 'product' in data:
            product = data['product']
            print(f"   Product Title: {product.get('title', 'N/A')}")
            print(f"   Product Brand: {product.get('brand', 'N/A')}")
            print(f"   Processing Method: {data.get('processing_method', 'N/A')}")
        
        return result.get('status') == 'success'
        
    except Exception as e:
        print(f"❌ TaskManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Direct Vision Processing Tests\n")
    
    # Test 1: Imports
    if not test_imports():
        print("\n❌ Import tests failed. Exiting.")
        return
    
    print("\n✅ All imports successful!")
    
    # Test 2: Direct vision processing
    if await test_direct_vision():
        print("\n✅ Direct vision processing works!")
    else:
        print("\n❌ Direct vision processing failed")
    
    # Test 3: TaskManager integration
    if await test_task_manager():
        print("\n✅ TaskManager integration works!")
    else:
        print("\n❌ TaskManager integration failed")
    
    print("\n🎉 Tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
