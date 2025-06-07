import logging
from typing import Dict, Any
from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)

def create_get_products_tool(product_service):
    """Create a tool for retrieving product information and stock levels"""
    
    async def get_products_info(user_id: str, query_type: str = "all") -> Dict[str, Any]:
        """
        Get product information for a store
        
        Args:
            user_id: The user ID of the store owner
            query_type: Type of query - "all", "low_stock", "analytics", or "out_of_stock"
        
        Returns:
            Dict containing product information based on query type
        """
        try:
            if query_type == "low_stock":
                products = await product_service.get_low_stock_products(user_id)
                if products is None:
                    return {
                        "success": False,
                        "message": "Unable to retrieve product information from database"
                    }
                
                if not products:
                    return {
                        "success": True,
                        "message": "Good news! All products are well stocked.",
                        "low_stock_products": [],
                        "count": 0
                    }
                
                return {
                    "success": True,
                    "message": f"Found {len(products)} products that need restocking",
                    "low_stock_products": products,
                    "count": len(products),
                    "threshold": 3,
                    "advice": "Consider restocking these items soon to avoid running out of stock. Products with 0 stock should be prioritized."
                }
            
            elif query_type == "analytics":
                analytics = await product_service.get_product_analytics(user_id)
                if analytics is None:
                    return {
                        "success": False,
                        "message": "Unable to retrieve product analytics from database"
                    }
                
                return {
                    "success": True,
                    "message": "Product analytics retrieved successfully",
                    "analytics": analytics
                }
            
            elif query_type == "out_of_stock":
                products = await product_service.get_store_products(user_id)
                if products is None:
                    return {
                        "success": False,
                        "message": "Unable to retrieve product information from database"
                    }
                
                out_of_stock = [p for p in products if p.get('stock_quantity', 0) == 0]
                return {
                    "success": True,
                    "message": f"Found {len(out_of_stock)} products that are out of stock",
                    "out_of_stock_products": out_of_stock,
                    "count": len(out_of_stock)
                }
            
            else:  # query_type == "all"
                products = await product_service.get_store_products(user_id)
                if products is None:
                    return {
                        "success": False,
                        "message": "Unable to retrieve product information from database"
                    }
                
                return {
                    "success": True,
                    "message": f"Retrieved {len(products)} products from your store",
                    "products": products,
                    "count": len(products)
                }
                
        except Exception as e:
            logger.error(f"Error in get_products_info: {str(e)}")
            return {
                "success": False,
                "message": f"Error retrieving product information: {str(e)}"
            }
    
    return FunctionTool(func=get_products_info)