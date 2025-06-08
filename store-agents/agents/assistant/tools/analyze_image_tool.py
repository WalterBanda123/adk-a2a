import logging
import base64
import sys
import os
from typing import Dict, Any
from google.adk.tools import FunctionTool

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

logger = logging.getLogger(__name__)

def create_analyze_product_image_tool(image_analysis_service):
    """Create a tool for analyzing product images and extracting information"""
    
    async def analyze_product_image(
        image_base64: str,
        user_id: str = "default_user", 
        filename: str = "product_image.jpg"
    ) -> Dict[str, Any]:
        """
        Analyze a product image and extract structured product information
        
        Args:
            image_base64: Base64 encoded image data
            user_id: The user ID of the store owner
            filename: Original filename
        
        Returns:
            Clean JSON with product name, category, subcategory, size, image_url, description
        """
        try:
            logger.info(f"Starting product image analysis for user: {user_id}")
            
            # Decode base64 to bytes
            try:
                # Remove data URL prefix if present (e.g., "data:image/jpeg;base64,")
                if ',' in image_base64:
                    image_base64 = image_base64.split(',')[1]
                
                image_bytes = base64.b64decode(image_base64)
                logger.info(f"Successfully decoded image: {len(image_bytes)} bytes")
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to decode image: {str(e)}"
                }
            
            # Call the image analysis service
            result = await image_analysis_service.analyze_product_image(
                image_data=image_bytes,
                user_id=user_id,
                filename=filename
            )
            
            if result.get("success"):
                # Extract and clean the product info
                product_info = result.get("product_info", {})
                
                # Return exactly what was requested: clean JSON structure
                clean_response = {
                    "name": product_info.get("name", "Unknown Product"),
                    "category": product_info.get("category", "General"),
                    "subcategory": product_info.get("subcategory", "Other"),
                    "size": product_info.get("size", ""),
                    "brand": product_info.get("brand", ""),
                    "description": product_info.get("description", ""),
                    "image_url": product_info.get("image", ""),
                    "success": True
                }
                
                logger.info(f"Image analysis completed successfully: {clean_response['name']}")
                return clean_response
            else:
                return {
                    "success": False,
                    "error": result.get("message", "Image analysis failed")
                }
                
        except Exception as e:
            logger.error(f"Error in analyze_product_image tool: {str(e)}")
            return {
                "success": False,
                "error": f"Tool execution error: {str(e)}"
            }

    return FunctionTool(func=analyze_product_image)
