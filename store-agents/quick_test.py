#!/usr/bin/env python3
"""
Quick product retrieval test with verbose logging
"""

import os
import sys
import asyncio
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

async def quick_test():
    print("⚡ Quick Product Test")
    print("="*30)
    
    try:
        start_time = time.time()
        
        from common.real_product_service import RealProductService
        service = RealProductService()
        
        user_id = "9IbW1ssRI9cneCFC7a1zKOGW1Qa2"
        
        print(f"Calling get_store_products...")
        products = await service.get_store_products(user_id)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️  Query took {duration:.2f} seconds")
        
        if products is None:
            print("❌ Returned None")
        elif len(products) == 0:
            print("⚠️  Returned empty list - no products found for this user")
        else:
            print(f"✅ Found {len(products)} products:")
            for product in products:
                name = product.get('product_name', 'Unknown')
                user = product.get('userId', 'N/A')
                print(f"  - {name} (User: {user})")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(quick_test())
