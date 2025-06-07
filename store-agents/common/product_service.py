import os
import logging
from typing import Dict, Any, Optional, List
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

logger = logging.getLogger(__name__)

class ProductService:
    def __init__(self):
        self.db = None
        self._initialize_firebase()
        self.low_stock_threshold = 3  # Default threshold for low stock
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if Firebase is already initialized
            if not firebase_admin._apps:
                cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
                project_id = os.getenv("FIREBASE_PROJECT_ID")
                
                if cred_path and os.path.exists(cred_path):
                    logger.info(f"Initializing Firebase with service account key: {cred_path}")
                    cred = credentials.Certificate(cred_path)
                    
                    if project_id:
                        firebase_admin.initialize_app(cred, {'projectId': project_id})
                    else:
                        firebase_admin.initialize_app(cred)
                        
                    logger.info("Firebase Admin SDK initialized successfully with service account")
                else:
                    logger.warning("No valid Firebase service account key found, attempting default initialization")
                    firebase_admin.initialize_app()
                    logger.info("Firebase Admin SDK initialized with default credentials")
            
            self.db = firestore.client()
            logger.info("Firestore client connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")
            logger.warning("Database connection unavailable")
            self.db = None
    
    async def get_store_products(self, user_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get all products for a user's store"""
        try:
            if not self.db:
                logger.warning("No database connection available")
                return None
            
            # Query products collection by store_owner_id
            products_ref = self.db.collection('products').where('store_owner_id', '==', user_id)
            products = products_ref.get()
            
            if products:
                product_list = []
                for product in products:
                    product_data = product.to_dict()
                    product_data['id'] = product.id
                    product_list.append(product_data)
                
                logger.info(f"Retrieved {len(product_list)} products for user_id: {user_id}")
                return product_list
            
            logger.warning(f"No products found for user: {user_id}")
            return []
                
        except Exception as e:
            logger.error(f"Error retrieving products for {user_id}: {str(e)}")
            return None
    
    async def get_low_stock_products(self, user_id: str, threshold: Optional[int] = None) -> Optional[List[Dict[str, Any]]]:
        """Get products with stock levels below the threshold"""
        try:
            if threshold is None:
                threshold = self.low_stock_threshold
            
            products = await self.get_store_products(user_id)
            if products is None:
                return None
            
            low_stock_products = []
            for product in products:
                stock_quantity = product.get('stock_quantity', 0)
                if stock_quantity <= threshold:
                    product['is_low_stock'] = True
                    product['threshold'] = threshold
                    low_stock_products.append(product)
            
            logger.info(f"Found {len(low_stock_products)} low stock products for user_id: {user_id}")
            return low_stock_products
                
        except Exception as e:
            logger.error(f"Error retrieving low stock products for {user_id}: {str(e)}")
            return None
    
    async def get_product_analytics(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get product analytics and insights"""
        try:
            products = await self.get_store_products(user_id)
            if products is None:
                return None
            
            total_products = len(products)
            low_stock_products = await self.get_low_stock_products(user_id)
            low_stock_count = len(low_stock_products) if low_stock_products else 0
            
            out_of_stock = [p for p in products if p.get('stock_quantity', 0) == 0]
            out_of_stock_count = len(out_of_stock)
            
            total_stock_value = sum(
                p.get('stock_quantity', 0) * p.get('unit_price', 0) 
                for p in products
            )
            
            analytics = {
                "total_products": total_products,
                "low_stock_count": low_stock_count,
                "out_of_stock_count": out_of_stock_count,
                "total_stock_value": total_stock_value,
                "low_stock_products": low_stock_products,
                "out_of_stock_products": out_of_stock,
                "stock_status": {
                    "healthy": total_products - low_stock_count - out_of_stock_count,
                    "low_stock": low_stock_count,
                    "out_of_stock": out_of_stock_count
                }
            }
            
            logger.info(f"Generated product analytics for user_id: {user_id}")
            return analytics
                
        except Exception as e:
            logger.error(f"Error generating product analytics for {user_id}: {str(e)}")
            return None
    
    async def populate_demo_products(self, user_id: str = "zXUaVlBG05bpsCy5QlGkCNbz4Rm2") -> Dict[str, Any]:
        """Populate Firebase with demo product data including some low stock items"""
        if not self.db:
            return {"success": False, "message": "No database connection"}
        
        try:
            # Demo products for Walter's store with some low stock items
            demo_products = [
                {
                    "store_owner_id": user_id,
                    "product_name": "Mealie Meal (10kg)",
                    "category": "Staples",
                    "brand": "Gold Leaf",
                    "unit_price": 8.50,
                    "stock_quantity": 15,
                    "reorder_point": 5,
                    "supplier": "OK Zimbabwe",
                    "cost_price": 7.20,
                    "last_restocked": "2025-06-05T10:00:00Z",
                    "expiry_date": "2025-12-01",
                    "unit_of_measure": "10kg bags",
                    "barcode": "123456789001"
                },
                {
                    "store_owner_id": user_id,
                    "product_name": "Cooking Oil (2L)",
                    "category": "Cooking Essentials",
                    "brand": "Olivine",
                    "unit_price": 4.75,
                    "stock_quantity": 2,  # LOW STOCK
                    "reorder_point": 8,
                    "supplier": "TM Supermarkets",
                    "cost_price": 4.10,
                    "last_restocked": "2025-06-01T14:30:00Z",
                    "expiry_date": "2026-01-15",
                    "unit_of_measure": "2L bottles",
                    "barcode": "123456789002"
                },
                {
                    "store_owner_id": user_id,
                    "product_name": "Bread (Loaf)",
                    "category": "Bakery",
                    "brand": "Lobels",
                    "unit_price": 1.25,
                    "stock_quantity": 8,
                    "reorder_point": 10,
                    "supplier": "Lobels Bakery",
                    "cost_price": 1.00,
                    "last_restocked": "2025-06-08T06:00:00Z",
                    "expiry_date": "2025-06-10",
                    "unit_of_measure": "loaves",
                    "barcode": "123456789003"
                },
                {
                    "store_owner_id": user_id,
                    "product_name": "Sugar (2kg)",
                    "category": "Staples",
                    "brand": "Tongaat Hulett",
                    "unit_price": 3.20,
                    "stock_quantity": 1,  # LOW STOCK
                    "reorder_point": 6,
                    "supplier": "OK Zimbabwe",
                    "cost_price": 2.80,
                    "last_restocked": "2025-05-28T11:00:00Z",
                    "expiry_date": "2026-05-30",
                    "unit_of_measure": "2kg packets",
                    "barcode": "123456789004"
                },
                {
                    "store_owner_id": user_id,
                    "product_name": "Rice (2kg)",
                    "category": "Staples",
                    "brand": "Kapenta",
                    "unit_price": 3.80,
                    "stock_quantity": 12,
                    "reorder_point": 5,
                    "supplier": "Local Distributor",
                    "cost_price": 3.20,
                    "last_restocked": "2025-06-03T09:15:00Z",
                    "expiry_date": "2026-03-15",
                    "unit_of_measure": "2kg packets",
                    "barcode": "123456789005"
                },
                {
                    "store_owner_id": user_id,
                    "product_name": "Matemba (Dried Fish)",
                    "category": "Protein",
                    "brand": "Lake Harvest",
                    "unit_price": 2.50,
                    "stock_quantity": 0,  # OUT OF STOCK
                    "reorder_point": 4,
                    "supplier": "Lake Harvest",
                    "cost_price": 2.00,
                    "last_restocked": "2025-05-20T16:00:00Z",
                    "expiry_date": "2025-08-20",
                    "unit_of_measure": "500g packets",
                    "barcode": "123456789006"
                },
                {
                    "store_owner_id": user_id,
                    "product_name": "Coca Cola (500ml)",
                    "category": "Beverages",
                    "brand": "Coca Cola",
                    "unit_price": 1.00,
                    "stock_quantity": 24,
                    "reorder_point": 12,
                    "supplier": "Delta Beverages",
                    "cost_price": 0.75,
                    "last_restocked": "2025-06-07T13:00:00Z",
                    "expiry_date": "2025-09-07",
                    "unit_of_measure": "500ml bottles",
                    "barcode": "123456789007"
                },
                {
                    "store_owner_id": user_id,
                    "product_name": "Maheu (1L)",
                    "category": "Beverages",
                    "brand": "Dairibord",
                    "unit_price": 1.80,
                    "stock_quantity": 3,  # LOW STOCK
                    "reorder_point": 8,
                    "supplier": "Dairibord",
                    "cost_price": 1.45,
                    "last_restocked": "2025-06-04T08:30:00Z",
                    "expiry_date": "2025-06-12",
                    "unit_of_measure": "1L cartons",
                    "barcode": "123456789008"
                }
            ]
            
            # Add all products to the products collection
            products_ref = self.db.collection('products')
            added_count = 0
            
            for product_data in demo_products:
                # Check if product already exists
                existing_products = products_ref.where('store_owner_id', '==', user_id).where('product_name', '==', product_data['product_name']).get()
                
                if existing_products:
                    # Update existing product
                    existing_products[0].reference.update(product_data)
                    logger.info(f"Updated existing product: {product_data['product_name']}")
                else:
                    # Create new product
                    products_ref.add(product_data)
                    logger.info(f"Added new product: {product_data['product_name']}")
                
                added_count += 1
            
            return {
                "success": True,
                "message": f"Successfully processed {added_count} products",
                "products_count": added_count,
                "low_stock_items": [p['product_name'] for p in demo_products if p['stock_quantity'] <= 3]
            }
            
        except Exception as e:
            logger.error(f"Error populating demo products: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to populate demo products: {str(e)}"
            }