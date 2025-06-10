#!/usr/bin/env python3
"""
Direct Vision API Server - Bypass agent complexity for image processing
"""
import asyncio
import base64
import logging
import os
import sys
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Add current directory to path
sys.path.append('.')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageRequest(BaseModel):
    message: str
    image_data: str
    is_url: bool = False
    user_id: str = "default_user"

class ImageResponse(BaseModel):
    message: str
    status: str
    data: Dict[str, Any]

# Initialize FastAPI app
app = FastAPI(title="Direct Vision API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",    # React default
        "http://127.0.0.1:3000",
        "http://localhost:3001", 
        "http://127.0.0.1:3001",
        "http://localhost:4200",    # Angular default
        "http://127.0.0.1:4200",
        "http://localhost:5173",    # Vite default
        "http://127.0.0.1:5173",
        "http://localhost:8080",    # Vue default
        "http://127.0.0.1:8080",
        "http://localhost:8100",    # Ionic default
        "http://127.0.0.1:8100",
        "https://localhost:8100",
        "https://127.0.0.1:8100",
        "*"  # Allow all origins for development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "direct_vision_api"}

@app.post("/analyze_image", response_model=ImageResponse)
async def analyze_image(request: ImageRequest):
    """
    Directly analyze product image using Enhanced Processor with AutoML support
    Uses AutoML first, falls back to enhanced Vision API
    """
    try:
        logger.info(f"📷 Received image analysis request from user: {request.user_id}")
        
        # Validate image data
        if not request.image_data:
            raise HTTPException(status_code=400, detail="Image data is required")
        
        # Use the integrated enhanced processor with AutoML support
        from enhanced_add_product_vision_tool_clean import EnhancedProductVisionProcessor
        processor = EnhancedProductVisionProcessor()
        logger.info("🤖 Using Enhanced Processor with AutoML integration")
        
        # Process image using the unified processor (handles AutoML + fallback internally)
        vision_result = processor.process_image(request.image_data, request.is_url, request.user_id)
        
        if vision_result.get("success"):
            product_info = vision_result.get("product", {})
            
            # Extract product details
            title = product_info.get("title", "Unknown Product")
            brand = product_info.get("brand", "")
            size = product_info.get("size", "")
            unit = product_info.get("unit", "")
            category = product_info.get("category", "")
            processing_time = product_info.get("processing_time", 0)
            
            # Build summary message
            summary_parts = [f"✅ Product identified: {title}"]
            if brand:
                summary_parts.append(f"Brand: {brand}")
            if size and unit:
                summary_parts.append(f"Size: {size}{unit}")
            if category:
                summary_parts.append(f"Category: {category}")
            summary_parts.append(f"Processing time: {processing_time:.2f}s")
            
            summary_message = " | ".join(summary_parts)
            
            # Structure the product data for response
            product_data = {
                "title": title,
                "brand": brand,
                "size": size,
                "unit": unit,
                "category": category,
                "subcategory": product_info.get("subcategory", ""),
                "description": product_info.get("description", ""),
                "confidence": product_info.get("confidence", 0.0),
                "processing_time": processing_time
            }
            
            logger.info(f"✅ Successfully processed image: {title}")
            
            return ImageResponse(
                message=summary_message,
                status="success",
                data={
                    "product": product_data,
                    "processing_method": "direct_vision_api"
                }
            )
        else:
            error_msg = vision_result.get("error", "Unknown vision processing error")
            logger.error(f"❌ Vision processing failed: {error_msg}")
            
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to analyze image: {error_msg}"
            )
            
    except Exception as e:
        logger.error(f"❌ Error in image analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Image processing error: {str(e)}"
        )

@app.post("/run")
async def legacy_run_endpoint(request: dict):
    """
    Legacy endpoint for compatibility with existing curl tests
    """
    try:
        message = request.get("message", "")
        context = request.get("context", {})
        
        # Check if this is an image processing request
        if "image_data" in context:
            image_request = ImageRequest(
                message=message,
                image_data=context["image_data"],
                is_url=context.get("is_url", False),
                user_id=context.get("user_id", "default_user")
            )
            
            response = await analyze_image(image_request)
            return response.dict()
        else:
            # For non-image requests, return a simple response
            return {
                "message": f"Text-only request received: {message}",
                "status": "success",
                "data": {"processing_method": "direct_simple"}
            }
            
    except Exception as e:
        logger.error(f"❌ Error in legacy endpoint: {str(e)}")
        return {
            "message": f"Error: {str(e)}",
            "status": "error",
            "data": {}
        }

if __name__ == "__main__":
    logger.info("🚀 Starting Direct Vision API Server...")
    logger.info("📷 This server processes images directly without agent complexity")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
