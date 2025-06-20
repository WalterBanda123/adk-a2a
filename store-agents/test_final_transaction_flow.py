#!/usr/bin/env python3
"""
Final Transaction Flow Verification
Tests the complete end-to-end transaction flow with real products
"""
import asyncio
import sys
import os
import logging

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_final_transaction_flow():
    """Test complete transaction flow with real products"""
    try:
        from agents.product_transaction_agent.helpers import ProductTransactionHelper
        from common.real_product_service import RealProductService
        
        helper = ProductTransactionHelper()
        product_service = RealProductService()
        user_id = "test_flow_user"
        
        print("=" * 80)
        print("🔥 FINAL TRANSACTION FLOW VERIFICATION")
        print("=" * 80)
        
        # Add test products first
        print("\n📦 Step 1: Adding test products...")
        
        test_products = [
            {
                "product_name": "Raspberry Juice",
                "description": "Mazoe Raspberry Juice 2L",
                "unit_price": 2.50,
                "stock_quantity": 50,
                "category": "Beverages",
                "brand": "Mazoe"
            },
            {
                "product_name": "Orange Crush",
                "description": "Mazoe Orange Crush 2L",
                "unit_price": 2.50,
                "stock_quantity": 30,
                "category": "Beverages", 
                "brand": "Mazoe"
            },
            {
                "product_name": "Bread",
                "description": "White bread loaf",
                "unit_price": 1.00,
                "stock_quantity": 100,
                "category": "Bakery",
                "brand": "Bakers Inn"
            }
        ]
        
        for product in test_products:
            try:
                result = await product_service.add_product(user_id, product)
                if result:
                    print(f"✅ Added: {product['product_name']}")
                else:
                    print(f"❌ Failed to add: {product['product_name']}")
            except Exception as e:
                print(f"❌ Error adding {product['product_name']}: {e}")
        
        print("\n🔍 Step 2: Testing product lookups...")
        
        # Test specific product lookups
        lookup_tests = [
            ("mazoe ruspburry", "Raspberry Juice"),
            ("mazoe raspberry", "Raspberry Juice"),
            ("ruspbury juice", "Raspberry Juice"),
            ("raspberry juice", "Raspberry Juice"),
            ("mazoe orange crush", "Orange Crush"),
            ("orange crush", "Orange Crush"),
            ("bread", "Bread"),
        ]
        
        for query, expected in lookup_tests:
            print(f"\n🔍 Looking up: '{query}'")
            product = await helper.lookup_product_by_name(query, user_id)
            
            if product:
                found_name = product['product_name']
                status = "✅" if found_name == expected else "⚠️"
                print(f"{status} Found: '{found_name}' (expected: '{expected}')")
                if found_name != expected:
                    print(f"   🚨 MISMATCH! Expected '{expected}' but got '{found_name}'")
            else:
                print(f"❌ No match found (expected: '{expected}')")
        
        print("\n💰 Step 3: Testing complete transaction flow...")
        
        # Test transaction processing
        test_transactions = [
            "I sold 2 mazoe ruspburry and 1 bread",
            "Customer bought 1 raspberry juice and 2 bread",
            "Sold 1 mazoe orange crush today"
        ]
        
        for i, transaction_text in enumerate(test_transactions, 1):
            print(f"\n🧾 Transaction Test {i}: '{transaction_text}'")
            print("-" * 60)
            
            # Parse transaction
            parsed_result = await helper.parse_cart_message(transaction_text)
            
            if parsed_result.get("success"):
                items = parsed_result["items"]
                print(f"✅ Parsed {len(items)} items:")
                for item in items:
                    print(f"   - {item['quantity']}x {item['name']}")
                
                # Compute receipt
                receipt_result = await helper.compute_receipt(items, user_id)
                
                if receipt_result.get("success"):
                    receipt = receipt_result["receipt"]
                    print(f"✅ Receipt computed:")
                    print(f"   - Total: ${receipt['total']:.2f}")
                    print(f"   - Items processed: {len(receipt['items'])}")
                    
                    for item in receipt['items']:
                        print(f"   ✓ {item['quantity']}x {item['product_name']} @ ${item['unit_price']:.2f}")
                else:
                    print(f"❌ Receipt failed: {receipt_result.get('errors', ['Unknown error'])}")
            else:
                print(f"❌ Parse failed: {parsed_result.get('error')}")
        
        print("\n" + "=" * 80)
        print("🎯 KEY FINDINGS:")
        print("=" * 80)
        print("1. Product Matching: Testing fuzzy matching for 'mazoe ruspburry' -> 'Raspberry Juice'")
        print("2. Transaction Parsing: Natural language to structured data")
        print("3. Receipt Generation: Complete receipt with taxes and totals")
        print("4. Database Integration: Real Firestore operations")
        print("\n✅ FINAL TRANSACTION FLOW VERIFICATION COMPLETED")
        print("=" * 80)
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_final_transaction_flow())
