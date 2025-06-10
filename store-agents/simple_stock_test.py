#!/usr/bin/env python3
"""
Simple test to validate stock levels functionality
"""
import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from common.product_service import ProductService

async def simple_test():
    """Simple test to check if products are accessible"""
    print("🧪 Simple Stock Test")
    print("=" * 30)
    
    service = ProductService()
    test_user_id = "zXUaVlBG05bpsCy5QlGkCNbz4Rm2"
    
    # Test basic product retrieval
    print("Testing basic product retrieval...")
    products = await service.get_store_products(test_user_id)
    
    if products is not None:
        print(f"✅ Found {len(products)} products")
        
        # Show sample product info
        if products:
            sample = products[0]
            print(f"Sample product: {sample.get('product_name', 'Unknown')}")
            print(f"Stock quantity: {sample.get('stock_quantity', 0)}")
            print(f"Unit price: ${sample.get('unit_price', 0):.2f}")
        
        # Test analytics
        print("\nTesting analytics...")
        analytics = await service.get_product_analytics(test_user_id)
        if analytics:
            print(f"✅ Analytics generated")
            print(f"Total products: {analytics.get('total_products', 0)}")
            print(f"Low stock count: {analytics.get('low_stock_count', 0)}")
            print(f"Out of stock count: {analytics.get('out_of_stock_count', 0)}")
            print(f"Total stock value: ${analytics.get('total_stock_value', 0):.2f}")
        else:
            print("❌ Analytics failed")
            
    else:
        print("❌ No products found or database error")
    
    print("\n🎯 Test Complete!")

if __name__ == "__main__":
    asyncio.run(simple_test())
