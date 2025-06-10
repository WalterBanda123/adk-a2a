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
            query_type: Type of query - "all", "low_stock", "analytics", "out_of_stock", or "stock_overview"
        
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
            
            elif query_type == "stock_overview":
                # Get comprehensive stock overview
                products = await product_service.get_store_products(user_id)
                analytics = await product_service.get_product_analytics(user_id)
                
                if products is None or analytics is None:
                    return {
                        "success": False,
                        "message": "Unable to retrieve stock information from database"
                    }
                
                # Categorize products by stock status
                healthy_stock = []
                low_stock = []
                out_of_stock = []
                
                for product in products:
                    stock_qty = product.get('stock_quantity', 0)
                    reorder_point = product.get('reorder_point', 5)
                    
                    if stock_qty == 0:
                        out_of_stock.append(product)
                    elif stock_qty <= reorder_point:
                        low_stock.append(product)
                    else:
                        healthy_stock.append(product)
                
                # Calculate total inventory value
                total_value = sum(p.get('stock_quantity', 0) * p.get('unit_price', 0) for p in products)
                
                overview = {
                    "total_products": len(products),
                    "healthy_stock": {
                        "count": len(healthy_stock),
                        "products": healthy_stock
                    },
                    "low_stock": {
                        "count": len(low_stock),
                        "products": low_stock
                    },
                    "out_of_stock": {
                        "count": len(out_of_stock),
                        "products": out_of_stock
                    },
                    "total_inventory_value": total_value,
                    "analytics": analytics
                }
                
                # Create summary message
                status_emoji = "✅" if len(out_of_stock) == 0 and len(low_stock) == 0 else "⚠️" if len(out_of_stock) == 0 else "🚨"
                summary = f"{status_emoji} **Stock Overview for Your Store**\n\n"
                summary += f"📦 **Total Products:** {len(products)}\n"
                summary += f"💰 **Total Inventory Value:** ${total_value:.2f}\n\n"
                summary += f"✅ **Healthy Stock:** {len(healthy_stock)} products\n"
                summary += f"⚠️ **Low Stock:** {len(low_stock)} products\n"
                summary += f"🚨 **Out of Stock:** {len(out_of_stock)} products\n\n"
                
                if len(out_of_stock) > 0:
                    summary += f"**Urgent Action Required:**\n"
                    for product in out_of_stock[:3]:  # Show first 3
                        summary += f"• {product.get('product_name', 'Unknown')} - RESTOCK IMMEDIATELY\n"
                    if len(out_of_stock) > 3:
                        summary += f"• ...and {len(out_of_stock) - 3} more\n"
                    summary += "\n"
                
                if len(low_stock) > 0:
                    summary += f"**Reorder Soon:**\n"
                    for product in low_stock[:3]:  # Show first 3
                        qty = product.get('stock_quantity', 0)
                        summary += f"• {product.get('product_name', 'Unknown')} - {qty} left\n"
                    if len(low_stock) > 3:
                        summary += f"• ...and {len(low_stock) - 3} more\n"
                
                return {
                    "success": True,
                    "message": summary,
                    "overview": overview,
                    "requires_attention": len(out_of_stock) > 0 or len(low_stock) > 0
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