"""
Product Setup Helper
Helps users set up their initial product inventory without hardcoded data
"""
import asyncio
import sys
import os
import json
from typing import Dict, Any, List

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from common.real_product_service import RealProductService

async def setup_user_products():
    """Interactive setup for user's initial products"""
    
    service = RealProductService()
    
    print("🏪 PRODUCT INVENTORY SETUP")
    print("=" * 50)
    print("Let's set up your store's initial product inventory.")
    print("You can add products manually, import from CSV, or start with a template.\n")
    
    # Get user ID
    user_id = input("Enter your user ID: ").strip()
    if not user_id:
        print("❌ User ID is required!")
        return
    
    print(f"\n✅ Setting up inventory for user: {user_id}")
    
    while True:
        print("\nChoose an option:")
        print("1. Add a single product manually")
        print("2. Import from CSV file")
        print("3. Use sample template (for testing)")
        print("4. View current products")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            await add_single_product(service, user_id)
        elif choice == "2":
            await import_from_csv(service, user_id)
        elif choice == "3":
            await setup_sample_products(service, user_id)
        elif choice == "4":
            await view_current_products(service, user_id)
        elif choice == "5":
            break
        else:
            print("❌ Invalid choice. Please enter 1-5.")

async def add_single_product(service: RealProductService, user_id: str):
    """Add a single product interactively"""
    print("\n📦 ADD NEW PRODUCT")
    print("-" * 30)
    
    try:
        product_data = {}
        
        # Required fields
        product_data["product_name"] = input("Product name: ").strip()
        product_data["category"] = input("Category (e.g., Beverages, Food, Household): ").strip()
        
        price_input = input("Unit price ($): ").strip()
        product_data["unit_price"] = float(price_input)
        
        stock_input = input("Current stock quantity: ").strip()
        product_data["stock_quantity"] = int(stock_input)
        
        # Optional fields
        brand = input("Brand (optional): ").strip()
        if brand:
            product_data["brand"] = brand
            
        supplier = input("Supplier (optional): ").strip()
        if supplier:
            product_data["supplier"] = supplier
            
        cost_input = input("Cost price (optional): ").strip()
        if cost_input:
            product_data["cost_price"] = float(cost_input)
        
        reorder_input = input("Reorder point (default 5): ").strip()
        product_data["reorder_point"] = int(reorder_input) if reorder_input else 5
        
        unit_measure = input("Unit of measure (default 'units'): ").strip()
        product_data["unit_of_measure"] = unit_measure if unit_measure else "units"
        
        # Add the product
        result = await service.add_product(user_id, product_data)
        
        if result["success"]:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")
            
    except ValueError as e:
        print(f"❌ Invalid input: {e}")
    except Exception as e:
        print(f"❌ Error adding product: {e}")

async def import_from_csv(service: RealProductService, user_id: str):
    """Import products from CSV file"""
    print("\n📄 IMPORT FROM CSV")
    print("-" * 30)
    
    csv_file = input("Enter path to CSV file: ").strip()
    
    if not os.path.exists(csv_file):
        print(f"❌ File not found: {csv_file}")
        return
    
    try:
        import csv
        
        csv_data = []
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Convert numeric fields
                if 'unit_price' in row:
                    row['unit_price'] = float(row['unit_price'])
                if 'stock_quantity' in row:
                    row['stock_quantity'] = int(row['stock_quantity'])
                if 'cost_price' in row and row['cost_price']:
                    row['cost_price'] = float(row['cost_price'])
                if 'reorder_point' in row and row['reorder_point']:
                    row['reorder_point'] = int(row['reorder_point'])
                
                csv_data.append(row)
        
        print(f"Found {len(csv_data)} products in CSV file.")
        confirm = input("Proceed with import? (y/n): ").strip().lower()
        
        if confirm == 'y':
            result = await service.import_products_from_csv(user_id, csv_data)
            print(f"✅ {result['message']}")
            
            if result.get('errors'):
                print("\n⚠️ Errors during import:")
                for error in result['errors']:
                    print(f"  - {error}")
        else:
            print("Import cancelled.")
            
    except Exception as e:
        print(f"❌ Error importing CSV: {e}")

async def setup_sample_products(service: RealProductService, user_id: str):
    """Set up sample products for testing"""
    print("\n🧪 SAMPLE PRODUCT SETUP")
    print("-" * 30)
    print("This will add a few sample products to test the system.")
    
    confirm = input("Add sample products? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Sample setup cancelled.")
        return
    
    sample_products = [
        {
            "product_name": "Bread (Loaf)",
            "category": "Bakery",
            "brand": "Local Bakery",
            "unit_price": 1.25,
            "stock_quantity": 10,
            "cost_price": 1.00,
            "reorder_point": 5,
            "unit_of_measure": "loaves"
        },
        {
            "product_name": "Milk (1L)",
            "category": "Dairy",
            "brand": "Dairibord",
            "unit_price": 1.80,
            "stock_quantity": 8,
            "cost_price": 1.45,
            "reorder_point": 6,
            "unit_of_measure": "1L cartons"
        },
        {
            "product_name": "Cooking Oil (2L)",
            "category": "Cooking Essentials",
            "brand": "Olivine",
            "unit_price": 4.75,
            "stock_quantity": 5,
            "cost_price": 4.10,
            "reorder_point": 3,
            "unit_of_measure": "2L bottles"
        }
    ]
    
    added_count = 0
    for product_data in sample_products:
        result = await service.add_product(user_id, product_data)
        if result["success"]:
            added_count += 1
            print(f"✅ Added: {product_data['product_name']}")
        else:
            print(f"❌ Failed to add {product_data['product_name']}: {result['message']}")
    
    print(f"\n✅ Added {added_count} sample products successfully!")

async def view_current_products(service: RealProductService, user_id: str):
    """View user's current products"""
    print("\n📋 CURRENT PRODUCTS")
    print("-" * 30)
    
    products = await service.get_store_products(user_id)
    
    if not products:
        print("No products found. Add some products first!")
        return
    
    print(f"Found {len(products)} products:\n")
    
    for i, product in enumerate(products, 1):
        stock_status = "🟢" if product.get('stock_quantity', 0) > product.get('reorder_point', 5) else "🟡" if product.get('stock_quantity', 0) > 0 else "🔴"
        
        print(f"{i}. {stock_status} {product.get('product_name', 'Unknown')}")
        print(f"   Category: {product.get('category', 'Unknown')}")
        print(f"   Price: ${product.get('unit_price', 0):.2f}")
        print(f"   Stock: {product.get('stock_quantity', 0)} {product.get('unit_of_measure', 'units')}")
        print(f"   Reorder Point: {product.get('reorder_point', 5)}")
        print()

def create_csv_template():
    """Create a CSV template file"""
    template_data = [
        {
            "product_name": "Example Product 1",
            "category": "Food",
            "brand": "Example Brand",
            "unit_price": "2.50",
            "stock_quantity": "15",
            "cost_price": "2.00",
            "reorder_point": "5",
            "unit_of_measure": "units",
            "supplier": "Example Supplier",
            "barcode": "1234567890",
            "description": "Example product description"
        },
        {
            "product_name": "Example Product 2", 
            "category": "Beverages",
            "brand": "Another Brand",
            "unit_price": "1.75",
            "stock_quantity": "20",
            "cost_price": "1.25",
            "reorder_point": "8",
            "unit_of_measure": "bottles",
            "supplier": "Beverage Supplier",
            "barcode": "0987654321",
            "description": "Example beverage"
        }
    ]
    
    filename = "product_template.csv"
    
    import csv
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        if template_data:
            fieldnames = template_data[0].keys()
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(template_data)
    
    print(f"✅ Created CSV template: {filename}")
    print("Edit this file with your products and use the import option.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Product Setup Helper")
    parser.add_argument("--create-template", action="store_true", help="Create CSV template file")
    
    args = parser.parse_args()
    
    if args.create_template:
        create_csv_template()
    else:
        asyncio.run(setup_user_products())
