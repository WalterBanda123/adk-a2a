#!/usr/bin/env python3
"""
Test the specific product lookup issue with timeout
"""

import sys
import os
import asyncio
import signal
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.product_transaction_agent.helpers import ProductTransactionHelper

async def test_with_timeout():
    """Test product lookup with timeout"""
    
    print("🔍 Testing Product Lookup with Timeout")
    print("="*50)
    
    helper = ProductTransactionHelper()
    user_id = "9IbW1ssRI9cneCFC7a1zKOGW1Qa2"
    
    try:
        print(f"Testing lookup for user: {user_id}")
        
        # Test with timeout
        result = await asyncio.wait_for(
            helper.lookup_product_by_name("mazoe", user_id),
            timeout=10.0  # 10 second timeout
        )
        
        if result:
            print(f"✅ Found product: {result.get('product_name')} - ${result.get('unit_price')}")
        else:
            print("❌ No product found")
            
    except asyncio.TimeoutError:
        print("⏰ Request timed out after 10 seconds")
        print("This suggests the database query is hanging")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

async def test_service_directly():
    """Test the service directly"""
    
    print(f"\n🔧 Testing RealProductService Directly")
    print("="*50)
    
    try:
        from common.real_product_service import RealProductService
        
        service = RealProductService()
        user_id = "9IbW1ssRI9cneCFC7a1zKOGW1Qa2"
        
        print(f"Service initialized: {service is not None}")
        print(f"Database connection: {service.db is not None}")
        
        # Test with timeout
        result = await asyncio.wait_for(
            service.get_store_products(user_id),
            timeout=10.0
        )
        
        if result is not None:
            print(f"✅ Service returned {len(result)} products")
            for product in result[:3]:  # Show first 3
                print(f"  - {product.get('product_name', 'Unknown')}")
        else:
            print("❌ Service returned None")
            
    except asyncio.TimeoutError:
        print("⏰ Service call timed out")
        
    except Exception as e:
        print(f"❌ Service error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main test function"""
    await test_service_directly()
    await test_with_timeout()

if __name__ == "__main__":
    # Handle Ctrl+C gracefully
    def signal_handler(signum, frame):
        print(f"\n⚠️  Interrupted by user")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n⚠️  Test interrupted")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
