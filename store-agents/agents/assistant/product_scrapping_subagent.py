"""
Product Scrapping Subagent
Handles extraction and storage of product information from images and other sources
"""

import logging
import json
            # Create scrap from parsed text
            scrap_data = self._create_scrap_from_text(parsed_data, text_data, source_context, tags)
            
            # Store the scrap if service is available
            if self._is_service_available():
                scrap_id = await self.storage_service.store_scrap(scrap_data)
                logger.info(f"✅ Text scrap created with ID: {scrap_id}")
                
                return {
                    "success": True,
                    "scrap_id": scrap_id,
                    "extracted_data": parsed_data,
                    "message": f"Text successfully parsed and stored as scrap {scrap_id}"
                }
            else:
                return {
                    "success": True,
                    "scrap_id": None,
                    "extracted_data": parsed_data,
                    "message": "Text successfully parsed (storage service unavailable)"
                }om datetime import datetime
from typing import Dict, Any, Optional, List
from google.adk.tools import FunctionTool

# Import our enhanced vision processor
import sys
import os
try:
    # Add project root to path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, project_root)
    from enhanced_add_product_vision_tool_clean import EnhancedProductVisionProcessor
    from common.scraps_storage_service import ScrapsStorageService
    ENHANCED_VISION_AVAILABLE = True
except ImportError as e:
    ENHANCED_VISION_AVAILABLE = False
    print(f"Enhanced vision processor not available: {e}")
    # Fallback for storage service
    try:
        from common.scraps_storage_service import ScrapsStorageService
    except ImportError:
        ScrapsStorageService = None

logger = logging.getLogger(__name__)

class ProductScrappingSubagent:
    """
    Subagent responsible for scrapping product information from various sources
    and storing them as organized text files with user ID prefixes
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.vision_processor = None
        self.storage_service = ScrapsStorageService(user_id) if ScrapsStorageService else None
        
        # Initialize vision processor if available
        if ENHANCED_VISION_AVAILABLE:
            try:
                self.vision_processor = EnhancedProductVisionProcessor()
                logger.info("✅ Enhanced Vision Processor initialized for scrapping")
            except Exception as e:
                logger.error(f"Failed to initialize vision processor: {e}")
                self.vision_processor = None
        
        logger.info(f"Product Scrapping Subagent initialized for user: {user_id}")
    
    def create_tools(self) -> List[FunctionTool]:
        """Create tools for product scrapping operations"""
        return [
            FunctionTool(func=self.scrap_product_from_image),
            FunctionTool(func=self.scrap_product_from_text),
            FunctionTool(func=self.list_user_scraps),
            FunctionTool(func=self.get_scrap_content),
            FunctionTool(func=self.delete_scrap)
        ]
    
    async def scrap_product_from_image(self, image_data: str, is_url: bool = False, 
                                     source_context: str = "manual_upload", 
                                     tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Extract product information from image and store as scrap
        """
        if tags is None:
            tags = []
            
        try:
            logger.info(f"Starting product scrapping from image for user: {self.user_id}")
            
            # Use enhanced vision processor if available
            if self.vision_processor:
                result = self.vision_processor.process_image(image_data, is_url, self.user_id)
                
                if result.get('success'):
                    # Create scrap from vision result
                    scrap_data = self._create_scrap_from_vision_result(result, source_context, tags)
                    
                    # Store the scrap if service is available
                    if self._is_service_available():
                        scrap_id = await self.storage_service.store_scrap(scrap_data)
                        logger.info(f"✅ Product scrap created with ID: {scrap_id}")
                        
                        return {
                            "success": True,
                            "scrap_id": scrap_id,
                            "extracted_data": result,
                            "message": f"Product information successfully scraped and stored as {scrap_id}"
                        }
                    else:
                        return {
                            "success": True,
                            "scrap_id": None,
                            "extracted_data": result,
                            "message": "Product information successfully scraped (storage service unavailable)"
                        }
                else:
                    logger.error(f"Vision processing failed: {result.get('error')}")
                    return {
                        "success": False,
                        "error": f"Failed to process image: {result.get('error')}"
                    }
            else:
                # Fallback: store basic image scrap without processing
                if self._is_service_available():
                    scrap_data = self._create_basic_image_scrap(image_data, is_url, source_context, tags)
                    scrap_id = await self.storage_service.store_scrap(scrap_data)
                    
                    return {
                        "success": True,
                        "scrap_id": scrap_id,
                        "message": f"Image stored as basic scrap {scrap_id} (vision processing unavailable)"
                    }
                else:
                    return {
                        "success": False,
                        "error": "Both vision processing and storage services are unavailable"
                    }
                
        except Exception as e:
            logger.error(f"Error in scrap_product_from_image: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def scrap_product_from_text(self, text_data: str, source_context: str = "manual_entry", 
                                    tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Extract and structure product information from text
        """
        if tags is None:
            tags = []
            
        try:
            logger.info(f"Starting product scrapping from text for user: {self.user_id}")
            
            # Parse text for product information
            parsed_data = self._parse_text_for_product_info(text_data)
            
            # Create scrap from parsed text
            scrap_data = self._create_scrap_from_text(parsed_data, text_data, source_context, tags)
            
            # Store the scrap
            scrap_id = await self.storage_service.store_scrap(scrap_data)
            
            logger.info(f"✅ Text scrap created with ID: {scrap_id}")
            
            return {
                "success": True,
                "scrap_id": scrap_id,
                "extracted_data": parsed_data,
                "message": f"Text information successfully scraped and stored as {scrap_id}"
            }
            
        except Exception as e:
            logger.error(f"Error in scrap_product_from_text: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_user_scraps(self, filter_tags: Optional[List[str]] = None, limit: int = 50) -> Dict[str, Any]:
        """List all scraps for the user"""
        try:
            if filter_tags is None:
                filter_tags = []
            scraps = await self.storage_service.list_scraps(filter_tags, limit)
            
            return {
                "success": True,
                "scraps": scraps,
                "total_count": len(scraps),
                "user_id": self.user_id
            }
            
        except Exception as e:
            logger.error(f"Error listing user scraps: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_scrap_content(self, scrap_id: str) -> Dict[str, Any]:
        """Get full content of a specific scrap"""
        try:
            content = await self.storage_service.get_scrap(scrap_id)
            
            if content:
                return {
                    "success": True,
                    "scrap_id": scrap_id,
                    "content": content
                }
            else:
                return {
                    "success": False,
                    "error": f"Scrap with ID {scrap_id} not found"
                }
                
        except Exception as e:
            logger.error(f"Error getting scrap content: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_scrap(self, scrap_id: str) -> Dict[str, Any]:
        """Delete a specific scrap"""
        try:
            success = await self.storage_service.delete_scrap(scrap_id)
            
            if success:
                return {
                    "success": True,
                    "message": f"Scrap {scrap_id} deleted successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to delete scrap {scrap_id}"
                }
                
        except Exception as e:
            logger.error(f"Error deleting scrap: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_scrap_from_vision_result(self, vision_result: Dict[str, Any], 
                                       source_context: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a structured scrap from vision processing result"""
        
        if tags is None:
            tags = []
        
        scrap_data = {
            "scrap_id": str(uuid.uuid4()),
            "user_id": self.user_id,
            "timestamp": datetime.now().isoformat(),
            "scrap_type": "image_vision",
            "source_context": source_context,
            "tags": tags + ["vision_processed", "product_image"],
            "extracted_data": {
                "title": vision_result.get('title', 'Unknown Product'),
                "brand": vision_result.get('brand', ''),
                "size": vision_result.get('size', ''),
                "unit": vision_result.get('unit', ''),
                "category": vision_result.get('category', 'General'),
                "subcategory": vision_result.get('subcategory', ''),
                "description": vision_result.get('description', ''),
                "confidence": vision_result.get('confidence', 0.0),
                "detection_method": vision_result.get('detection_method', 'unknown')
            },
            "raw_vision_data": vision_result,
            "processing_metadata": {
                "processor_version": "enhanced_v1",
                "processing_time": datetime.now().isoformat()
            }
        }
        
        return scrap_data
    
    def _create_basic_image_scrap(self, image_data: str, is_url: bool, 
                                source_context: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a basic scrap for images when vision processing is unavailable"""
        
        if tags is None:
            tags = []
        
        scrap_data = {
            "scrap_id": str(uuid.uuid4()),
            "user_id": self.user_id,
            "timestamp": datetime.now().isoformat(),
            "scrap_type": "image_basic",
            "source_context": source_context,
            "tags": tags + ["unprocessed_image"],
            "image_data": {
                "data": image_data[:100] + "..." if len(image_data) > 100 else image_data,  # Truncate for storage
                "is_url": is_url,
                "size_bytes": len(image_data) if not is_url else None
            },
            "extracted_data": {
                "title": "Unprocessed Image",
                "needs_processing": True
            },
            "processing_metadata": {
                "processor_version": "basic_v1",
                "processing_time": datetime.now().isoformat(),
                "note": "Vision processing was unavailable"
            }
        }
        
        return scrap_data
    
    def _create_scrap_from_text(self, parsed_data: Dict[str, Any], original_text: str,
                              source_context: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a scrap from parsed text data"""
        
        if tags is None:
            tags = []
        
        scrap_data = {
            "scrap_id": str(uuid.uuid4()),
            "user_id": self.user_id,
            "timestamp": datetime.now().isoformat(),
            "scrap_type": "text_parsed",
            "source_context": source_context,
            "tags": tags + ["text_processed"],
            "original_text": original_text,
            "extracted_data": parsed_data,
            "processing_metadata": {
                "processor_version": "text_parser_v1",
                "processing_time": datetime.now().isoformat()
            }
        }
        
        return scrap_data
    
    def _parse_text_for_product_info(self, text: str) -> Dict[str, Any]:
        """Parse text to extract product information"""
        
        # Basic text parsing logic - can be enhanced with NLP
        lines = text.strip().split('\n')
        parsed_data = {
            "title": "Unknown Product",
            "brand": "",
            "size": "",
            "unit": "",
            "category": "General",
            "description": text[:200] + "..." if len(text) > 200 else text,
            "confidence": 0.7,
            "detection_method": "text_parsing"
        }
        
        # Simple parsing logic
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            lower_line = line.lower()
            
            # Try to identify product title (usually first meaningful line)
            if parsed_data["title"] == "Unknown Product" and len(line) > 3:
                parsed_data["title"] = line
            
            # Look for brand indicators
            if any(brand_word in lower_line for brand_word in ['brand:', 'manufacturer:', 'made by']):
                parsed_data["brand"] = line.split(':', 1)[-1].strip()
            
            # Look for size indicators
            if any(size_word in lower_line for size_word in ['size:', 'weight:', 'volume:', 'ml', 'kg', 'g', 'oz']):
                # Extract size information
                import re
                size_match = re.search(r'(\d+(?:\.\d+)?)\s*(ml|kg|g|oz|l|liter|litre)', lower_line)
                if size_match:
                    parsed_data["size"] = size_match.group(1)
                    parsed_data["unit"] = size_match.group(2)
        
        return parsed_data
    
    def _is_service_available(self) -> bool:
        """Check if scraps storage service is available"""
        return self.storage_service is not None
    
    def _is_vision_available(self) -> bool:
        """Check if vision processor is available"""
        return self.vision_processor is not None
