#!/usr/bin/env python3
"""
Check products in database and test retrieval with specific user ID
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import firebase_admin
from firebase_admin import credentials, firestore
from common.real_product_service import RealProductService

def initialize_firebase():
    """Initialize Firebase if not already done"""
    try:
        firebase_admin.get_app()
        print("✓ Firebase already initialized")
    except ValueError:
        try:
            cred = credentials.Certificate('firebase-service-account-key.json')
            firebase_admin.initialize_app(cred)
            print("✓ Firebase initialized successfully")
        except Exception as e:
            print(f"✗ Failed to initialize Firebase: {e}")
            return False
    return True

def check_products_collection():
    """Check what's actually in the products collection"""
    
    if not initialize_firebase():
        return
    
    print("\n" + "="*70)
    print("🔍 CHECKING PRODUCTS COLLECTION DIRECTLY")
    print("="*70)
    
    db = firestore.client()
    
    try:
        # Get all products
        products_ref = db.collection('products')
        all_products = products_ref.get()
        
        print(f"\nTotal products in collection: {len(all_products)}")
        
        if len(all_products) == 0:
            print("❌ No products found in collection!")
            return
        
        print(f"\n📋 ALL PRODUCTS:")
        for i, doc in enumerate(all_products, 1):
            product_data = doc.to_dict()
            if product_data:  # Check if data is not None
                print(f"\n  Product {i} (ID: {doc.id}):")
                print(f"    Name: {product_data.get('product_name', 'N/A')}")
                print(f"    Price: ${product_data.get('unit_price', 'N/A')}")
                print(f"    Stock: {product_data.get('stock_quantity', 'N/A')}")
                print(f"    User ID: {product_data.get('userId', 'N/A')}")
                print(f"    Status: {product_data.get('status', 'N/A')}")
                print(f"    All fields: {list(product_data.keys())}")
            else:
                print(f"\n  Product {i} (ID: {doc.id}): No data found")
        
        # Check for specific user ID
        target_user_id = "9IbW1ssRI9cneCFC7a1zKOGW1Qa2"
        print(f"\n🔍 CHECKING FOR USER: {target_user_id}")
        
        user_products = products_ref.where('userId', '==', target_user_id).get()
        print(f"Found {len(user_products)} products for user {target_user_id}")
        
        for doc in user_products:
            product_data = doc.to_dict()
            if product_data:  # Check if data is not None
                print(f"  - {product_data.get('product_name', 'Unknown')} (${product_data.get('unit_price', 'N/A')})")
        
    except Exception as e:
        print(f"✗ Error checking products: {e}")
        import traceback
        traceback.print_exc()

async def test_real_product_service():
    """Test the RealProductService with the specific user ID"""
    
    print(f"\n" + "="*70)
    print("🧪 TESTING REALPRODUCTSERVICE")
    print("="*70)
    
    target_user_id = "9IbW1ssRI9cneCFC7a1zKOGW1Qa2"
    
    try:
        service = RealProductService()
        print(f"✓ RealProductService initialized")
        
        # Test getting products by user
        print(f"\n📦 Getting products for user: {target_user_id}")
        products = await service.get_store_products(target_user_id)
        
        if products is None:
            print(f"❌ Service returned None!")
            return
        
        print(f"Found {len(products)} products")
        
        if products:
            for i, product in enumerate(products, 1):
                print(f"  {i}. {product.get('product_name', 'Unknown')} - ${product.get('unit_price', 'N/A')} (Stock: {product.get('stock_quantity', 'N/A')})")
        else:
            print("  ❌ No products found!")
            
            # Debug: Check what the service method is actually doing
            print(f"\n🔧 DEBUG: Checking service internals...")
            print(f"  Service has db connection: {service.db is not None}")
            
            if service.db:
                # Try direct query
                print(f"  Trying direct query...")
                try:
                    direct_query = service.db.collection('products').where('userId', '==', target_user_id).get()
                    print(f"  Direct query found: {len(direct_query)} products")
                    
                    for doc in direct_query:
                        data = doc.to_dict()
                        if data:  # Check if data is not None
                            print(f"    - {data.get('product_name')} (User: {data.get('userId')})")
                        
                except Exception as e:
                    print(f"  Direct query failed: {e}")
        
    except Exception as e:
        print(f"✗ Error testing service: {e}")
        import traceback
        traceback.print_exc()

async def test_product_lookup():
    """Test specific product lookup"""
    
    print(f"\n" + "="*70)
    print("🔍 TESTING PRODUCT LOOKUP")
    print("="*70)
    
    target_user_id = "9IbW1ssRI9cneCFC7a1zKOGW1Qa2"
    
    try:
        service = RealProductService()
        
        # Test searching for specific products
        test_searches = ["mazoe", "raspberry", "bread", "orange"]
        
        for search_term in test_searches:
            print(f"\n🔍 Searching for '{search_term}':")
            
            # Get all products first
            all_products = await service.get_store_products(target_user_id)
            
            if all_products:
                matches = []
                for product in all_products:
                    name = product.get('product_name', '').lower()
                    if search_term.lower() in name:
                        matches.append(product)
                
                if matches:
                    for match in matches:
                        print(f"  ✓ Found: {match.get('product_name')} - ${match.get('unit_price')}")
                else:
                    print(f"  ❌ No matches for '{search_term}'")
            else:
                print(f"  ❌ No products available to search")
        
    except Exception as e:
        print(f"✗ Error in product lookup test: {e}")
        import traceback
        traceback.print_exc()

import asyncio

async def run_all_tests():
    """Run all diagnostic tests"""
    check_products_collection()
    await test_real_product_service()
    await test_product_lookup()

if __name__ == "__main__":
    print("🔍 PRODUCT RETRIEVAL DIAGNOSTIC")
    print("="*70)
    
    asyncio.run(run_all_tests())
    
    print(f"\n" + "="*70)
    print("✅ DIAGNOSTIC COMPLETE")
    print("="*70)
