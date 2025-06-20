"""
Enhanced Product Service for Real-World Usage
Handles dynamic product management without hardcoded demo data
"""
import os
import logging
from typing import Dict, Any, Optional, List
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

logger = logging.getLogger(__name__)

class RealProductService:
    """Production-ready product service without hardcoded data"""
    
    def __init__(self):
        self.db = None
        self._initialize_firebase()
        self.low_stock_threshold = 3
    
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

    async def add_product(self, user_id: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new product to user's inventory"""
        if not self.db:
            return {"success": False, "message": "No database connection"}
        
        try:
            # Ensure required fields
            required_fields = ['product_name', 'category', 'unit_price', 'stock_quantity']
            for field in required_fields:
                if field not in product_data:
                    return {"success": False, "message": f"Missing required field: {field}"}
            
            product_data.update({
                "userId": user_id, 
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "status": "active"
            })
            
            product_data.setdefault("reorder_point", 5)
            product_data.setdefault("unit_of_measure", "units")
            product_data.setdefault("cost_price", 0.0)
            
            doc_ref = self.db.collection('products').add(product_data)
            logger.info(f"Added product '{product_data['product_name']}' for user {user_id}")
            
            return {
                "success": True,
                "message": f"Product '{product_data['product_name']}' added successfully",
                "product_id": doc_ref[1].id,
                "product": product_data
            }
            
        except Exception as e:
            logger.error(f"Error adding product: {str(e)}")
            return {"success": False, "message": f"Failed to add product: {str(e)}"}

    async def update_product(self, user_id: str, product_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        if not self.db:
            return {"success": False, "message": "No database connection"}
        
        try:
            updates["updated_at"] = datetime.now().isoformat()
            
            product_ref = self.db.collection('products').document(product_id)
            product_doc = product_ref.get()
            
            if not product_doc.exists:
                return {"success": False, "message": "Product not found"}
            
            product_data = product_doc.to_dict()
            if not product_data:
                return {"success": False, "message": "Invalid product data"}
            
            # Use only standardized userId field for ownership check
            if product_data.get('userId') != user_id:
                return {"success": False, "message": "Unauthorized: Product belongs to different user"}
            
            product_ref.update(updates)
            logger.info(f"Updated product {product_id} for user {user_id}")
            
            return {
                "success": True,
                "message": "Product updated successfully",
                "product_id": product_id
            }
            
        except Exception as e:
            logger.error(f"Error updating product: {str(e)}")
            return {"success": False, "message": f"Failed to update product: {str(e)}"}

    async def delete_product(self, user_id: str, product_id: str) -> Dict[str, Any]:
        if not self.db:
            return {"success": False, "message": "No database connection"}
        
        try:
            product_ref = self.db.collection('products').document(product_id)
            product_doc = product_ref.get()
            
            if not product_doc.exists:
                return {"success": False, "message": "Product not found"}
            
            product_data = product_doc.to_dict()
            if not product_data:
                return {"success": False, "message": "Invalid product data"}
            
            # Use only standardized userId field for ownership check
            if product_data.get('userId') != user_id:
                return {"success": False, "message": "Unauthorized: Product belongs to different user"}
            
            product_ref.update({
                "status": "inactive",
                "updated_at": datetime.now().isoformat()
            })
            
            logger.info(f"Deleted product {product_id} for user {user_id}")
            
            return {
                "success": True,
                "message": "Product deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error deleting product: {str(e)}")
            return {"success": False, "message": f"Failed to delete product: {str(e)}"}

    async def get_store_products(self, user_id: str, include_inactive: bool = False) -> Optional[List[Dict[str, Any]]]:
        try:
            if not self.db:
                logger.warning("No database connection available")
                return None
            
            products = []
            
            try:
                query = self.db.collection('products').where('userId', '==', user_id)
                if not include_inactive:
                    query = query.where('status', '==', 'active')
                docs = query.get()
                
                for doc in docs:
                    product_data = doc.to_dict()
                    if product_data:
                        product_data['id'] = doc.id
                        products.append(product_data)
                        
                logger.info(f"Found {len(products)} products for user: {user_id}")
                return products
                        
            except Exception as e:
                logger.error(f"Error querying products by userId: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving products for {user_id}: {str(e)}")
            return None

    async def update_stock(self, user_id: str, product_id: str, new_quantity: int, movement_type: str = "adjustment") -> Dict[str, Any]:
        if not self.db:
            return {"success": False, "message": "No database connection"}
        
        try:
            product_ref = self.db.collection('products').document(product_id)
            product_doc = product_ref.get()
            
            if not product_doc.exists:
                return {"success": False, "message": "Product not found"}
            
            product_data = product_doc.to_dict()
            if not product_data:
                return {"success": False, "message": "Invalid product data"}
            
            if product_data.get('userId') != user_id:
                return {"success": False, "message": "Unauthorized: Product belongs to different user"}
            
            old_quantity = product_data.get('stock_quantity', 0)
            
            product_ref.update({
                "stock_quantity": new_quantity,
                "updated_at": datetime.now().isoformat(),
                "last_restocked": datetime.now().isoformat() if movement_type == "restock" else product_data.get("last_restocked")
            })
            
            movement_data = {
                "product_id": product_id,
                "user_id": user_id,
                "movement_type": movement_type,
                "old_quantity": old_quantity,
                "new_quantity": new_quantity,
                "quantity_change": new_quantity - old_quantity,
                "timestamp": datetime.now().isoformat()
            }
            
            self.db.collection('inventory_movements').add(movement_data)
            
            logger.info(f"Updated stock for product {product_id}: {old_quantity} -> {new_quantity}")
            
            return {
                "success": True,
                "message": f"Stock updated: {old_quantity} -> {new_quantity}",
                "old_quantity": old_quantity,
                "new_quantity": new_quantity
            }
            
        except Exception as e:
            logger.error(f"Error updating stock: {str(e)}")
            return {"success": False, "message": f"Failed to update stock: {str(e)}"}

    async def get_low_stock_products(self, user_id: str, threshold: Optional[int] = None) -> Optional[List[Dict[str, Any]]]:
        try:
            if threshold is None:
                threshold = self.low_stock_threshold
            
            products = await self.get_store_products(user_id)
            if products is None:
                return None
            
            low_stock_products = []
            for product in products:
                stock_quantity = product.get('stock_quantity', 0)
                reorder_point = product.get('reorder_point', threshold)
                
                if stock_quantity <= reorder_point:
                    product['is_low_stock'] = True
                    product['threshold'] = reorder_point
                    low_stock_products.append(product)
            
            logger.info(f"Found {len(low_stock_products)} low stock products for user_id: {user_id}")
            return low_stock_products
                
        except Exception as e:
            logger.error(f"Error retrieving low stock products for {user_id}: {str(e)}")
            return None

    async def get_product_analytics(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            products = await self.get_store_products(user_id)
            if products is None:
                return None
            
            analytics = {
                "total_products": len(products),
                "total_value": sum(p.get('stock_quantity', 0) * p.get('unit_price', 0) for p in products),
                "categories": {},
                "brands": {},
                "stock_status": {
                    "healthy": 0,
                    "low": 0,
                    "out": 0
                }
            }
            
            for product in products:
                category = product.get('category', 'Unknown')
                if category not in analytics['categories']:
                    analytics['categories'][category] = {"count": 0, "value": 0}
                analytics['categories'][category]["count"] += 1
                analytics['categories'][category]["value"] += product.get('stock_quantity', 0) * product.get('unit_price', 0)
                
                brand = product.get('brand', 'Unknown')
                if brand not in analytics['brands']:
                    analytics['brands'][brand] = {"count": 0, "value": 0}
                analytics['brands'][brand]["count"] += 1
                analytics['brands'][brand]["value"] += product.get('stock_quantity', 0) * product.get('unit_price', 0)
                
                stock_qty = product.get('stock_quantity', 0)
                reorder_point = product.get('reorder_point', 5)
                
                if stock_qty == 0:
                    analytics['stock_status']['out'] += 1
                elif stock_qty <= reorder_point:
                    analytics['stock_status']['low'] += 1
                else:
                    analytics['stock_status']['healthy'] += 1
            
            return analytics
                
        except Exception as e:
            logger.error(f"Error retrieving analytics for {user_id}: {str(e)}")
            return None

    async def search_products(self, user_id: str, search_term: str) -> Optional[List[Dict[str, Any]]]:
        try:
            products = await self.get_store_products(user_id)
            if products is None:
                return None
            
            search_term_lower = search_term.lower()
            matching_products = []
            
            for product in products:
                searchable_text = " ".join([
                    product.get('product_name', ''),
                    product.get('category', ''),
                    product.get('brand', ''),
                    product.get('description', '')
                ]).lower()
                
                if search_term_lower in searchable_text:
                    matching_products.append(product)
            
            logger.info(f"Found {len(matching_products)} products matching '{search_term}' for user {user_id}")
            return matching_products
                
        except Exception as e:
            logger.error(f"Error searching products for {user_id}: {str(e)}")
            return None

    async def import_products_from_csv(self, user_id: str, csv_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not self.db:
            return {"success": False, "message": "No database connection"}
        
        try:
            added_count = 0
            errors = []
            
            for row_data in csv_data:
                try:
                    if not row_data.get('product_name') or not row_data.get('unit_price'):
                        errors.append(f"Skipping row: missing product_name or unit_price")
                        continue
                    
                    result = await self.add_product(user_id, row_data)
                    if result.get("success"):
                        added_count += 1
                    else:
                        errors.append(f"Failed to add {row_data.get('product_name', 'unknown')}: {result.get('message', 'unknown error')}")
                        
                except Exception as e:
                    errors.append(f"Error processing row: {str(e)}")
            
            return {
                "success": True,
                "message": f"Successfully imported {added_count} products",
                "added_count": added_count,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Error importing products: {str(e)}")
            return {"success": False, "message": f"Failed to import products: {str(e)}"}
