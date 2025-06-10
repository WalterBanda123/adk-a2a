#!/usr/bin/env python3
"""
Test Enhanced Direct Vision Server
"""
import asyncio
import base64
import os
import sys

# Set up environment
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/walterbanda/Desktop/AI/adk-a2a/store-agents/vision-api-service.json'

async def test_direct_server():
    """Test the enhanced direct vision server"""
    print("🧪 Testing Enhanced Direct Vision Server")
    print("=" * 50)
    
    try:
        # Import after setting environment
        from direct_vision_server import analyze_image, ImageRequest
        
        # Read the test image
        image_path = 'images-mazoe-ruspberry.jpeg'
        if os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            print(f"✅ Loaded image: {image_path}")
        else:
            print(f"❌ Image not found: {image_path}")
            return False
        
        # Create test request
        request = ImageRequest(
            message="Analyze this product image",
            image_data=image_data,
            is_url=False,
            user_id="test_user_zimbabwe_grocery"
        )
        
        print(f"📤 Sending request for user: {request.user_id}")
        
        # Test the endpoint
        result = await analyze_image(request)
        
        print("\n🎉 RESPONSE RECEIVED:")
        print(f"Status: {result.status}")
        print(f"Message: {result.message}")
        
        # Extract product data
        product = result.data.get('product', {})
        processing_method = result.data.get('processing_method', 'unknown')
        
        print(f"\n📦 PRODUCT ANALYSIS:")
        print(f"Title: {product.get('title', 'Unknown')}")
        print(f"Brand: {product.get('brand', 'N/A')}")
        print(f"Size: {product.get('size', 'N/A')} {product.get('unit', '')}")
        print(f"Category: {product.get('category', 'N/A')}")
        print(f"Subcategory: {product.get('subcategory', 'N/A')}")
        print(f"Confidence: {product.get('confidence', 0):.2f}")
        print(f"Processing Method: {processing_method}")
        
        # Check if we're using the enhanced system
        if processing_method == "enhanced_dynamic_classifier":
            print("\n✅ SUCCESS: Using Enhanced Dynamic Classifier!")
            
            if product.get('confidence', 0) > 0.8:
                print("✅ HIGH CONFIDENCE DETECTION!")
            else:
                print("⚠️ Moderate confidence - may need profile adjustment")
                
            return True
        else:
            print(f"\n❌ ISSUE: Still using old processor: {processing_method}")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_direct_server())
    sys.exit(0 if success else 1)
