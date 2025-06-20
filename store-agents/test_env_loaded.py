#!/usr/bin/env python3
"""
Test product retrieval with explicit env loading
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables explicitly
from dotenv import load_dotenv
load_dotenv()

import asyncio

async def test_product_service():
    print("🔧 Testing Product Service with Loaded Environment")
    print("="*60)
    
    # Check environment after loading
    firebase_key = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
    firebase_project = os.getenv('FIREBASE_PROJECT_ID')
    
    print(f"After load_dotenv():")
    print(f"  FIREBASE_SERVICE_ACCOUNT_KEY: {firebase_key}")
    print(f"  FIREBASE_PROJECT_ID: {firebase_project}")
    
    try:
        from common.real_product_service import RealProductService
        
        print(f"\nCreating RealProductService...")
        service = RealProductService()
        print(f"✅ Service created")
        print(f"Service has db: {service.db is not None}")
        
        # Test with the specific user ID
        user_id = "9IbW1ssRI9cneCFC7a1zKOGW1Qa2"
        print(f"\n🔍 Testing get_store_products for user: {user_id}")
        
        # Set a timeout for this operation
        try:
            products = await asyncio.wait_for(
                service.get_store_products(user_id), 
                timeout=15.0
            )
            
            if products is None:
                print("❌ Service returned None")
            elif len(products) == 0:
                print("⚠️  Service returned empty list")
            else:
                print(f"✅ Service returned {len(products)} products:")
                for i, product in enumerate(products[:3], 1):
                    name = product.get('product_name', 'Unknown')
                    price = product.get('unit_price', 'N/A')
                    user = product.get('userId', 'N/A')
                    print(f"  {i}. {name} - ${price} (User: {user})")
                    
        except asyncio.TimeoutError:
            print("⏰ get_store_products timed out after 15 seconds")
            
        except Exception as e:
            print(f"❌ Error calling get_store_products: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Error creating service: {e}")
        import traceback
        traceback.print_exc()

async def test_helpers():
    print(f"\n🔧 Testing ProductTransactionHelper")
    print("="*60)
    
    try:
        from agents.product_transaction_agent.helpers import ProductTransactionHelper
        
        print("Creating ProductTransactionHelper...")
        helper = ProductTransactionHelper()
        print("✅ Helper created")
        
        user_id = "9IbW1ssRI9cneCFC7a1zKOGW1Qa2"
        print(f"\n🔍 Testing lookup_product_by_name...")
        
        try:
            result = await asyncio.wait_for(
                helper.lookup_product_by_name("mazoe", user_id),
                timeout=15.0
            )
            
            if result:
                print(f"✅ Found product: {result.get('product_name')} - ${result.get('unit_price')}")
            else:
                print("❌ No product found")
                
        except asyncio.TimeoutError:
            print("⏰ lookup_product_by_name timed out")
            
        except Exception as e:
            print(f"❌ Error in lookup: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Error creating helper: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    async def main():
        await test_product_service()
        await test_helpers()
        
    asyncio.run(main())
