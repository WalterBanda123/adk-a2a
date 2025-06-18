"""
Product Management API Endpoints
Provides REST API for frontend to manage products without hardcoded data
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from common.real_product_service import RealProductService

app = FastAPI(title="Product Management API", version="1.0.0")

# Models
class ProductCreate(BaseModel):
    product_name: str
    category: str
    unit_price: float
    stock_quantity: int
    brand: Optional[str] = None
    supplier: Optional[str] = None
    cost_price: Optional[float] = None
    reorder_point: Optional[int] = 5
    unit_of_measure: Optional[str] = "units"
    barcode: Optional[str] = None
    description: Optional[str] = None
    size: Optional[str] = None
    expiry_date: Optional[str] = None

class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    category: Optional[str] = None
    unit_price: Optional[float] = None
    stock_quantity: Optional[int] = None
    brand: Optional[str] = None
    supplier: Optional[str] = None
    cost_price: Optional[float] = None
    reorder_point: Optional[int] = None
    unit_of_measure: Optional[str] = None
    barcode: Optional[str] = None
    description: Optional[str] = None
    size: Optional[str] = None
    expiry_date: Optional[str] = None

class StockUpdate(BaseModel):
    new_quantity: int
    movement_type: str = "adjustment"  # "restock", "sale", "adjustment", "waste"

# Initialize service
product_service = RealProductService()

@app.post("/products/{user_id}")
async def add_product(user_id: str, product: ProductCreate):
    """Add a new product to user's inventory"""
    result = await product_service.add_product(user_id, product.dict())
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.get("/products/{user_id}")
async def get_products(user_id: str, include_inactive: bool = False):
    """Get all products for a user"""
    products = await product_service.get_store_products(user_id, include_inactive)
    if products is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve products")
    return {"success": True, "products": products, "count": len(products)}

@app.get("/products/{user_id}/low-stock")
async def get_low_stock_products(user_id: str, threshold: Optional[int] = None):
    """Get products with low stock"""
    products = await product_service.get_low_stock_products(user_id, threshold)
    if products is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve low stock products")
    return {"success": True, "low_stock_products": products, "count": len(products)}

@app.get("/products/{user_id}/analytics")
async def get_product_analytics(user_id: str):
    """Get product analytics"""
    analytics = await product_service.get_product_analytics(user_id)
    if analytics is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")
    return {"success": True, "analytics": analytics}

@app.get("/products/{user_id}/search")
async def search_products(user_id: str, q: str):
    """Search products"""
    products = await product_service.search_products(user_id, q)
    if products is None:
        raise HTTPException(status_code=500, detail="Failed to search products")
    return {"success": True, "products": products, "count": len(products)}

@app.put("/products/{user_id}/{product_id}")
async def update_product(user_id: str, product_id: str, updates: ProductUpdate):
    """Update an existing product"""
    # Filter out None values
    update_data = {k: v for k, v in updates.dict().items() if v is not None}
    
    result = await product_service.update_product(user_id, product_id, update_data)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.delete("/products/{user_id}/{product_id}")
async def delete_product(user_id: str, product_id: str):
    """Delete a product (soft delete)"""
    result = await product_service.delete_product(user_id, product_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.put("/products/{user_id}/{product_id}/stock")
async def update_stock(user_id: str, product_id: str, stock_update: StockUpdate):
    """Update product stock quantity"""
    result = await product_service.update_stock(
        user_id, 
        product_id, 
        stock_update.new_quantity, 
        stock_update.movement_type
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.post("/products/{user_id}/import-csv")
async def import_products_csv(user_id: str, csv_data: List[Dict[str, Any]]):
    """Import products from CSV data"""
    result = await product_service.import_products_from_csv(user_id, csv_data)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Product Management API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
