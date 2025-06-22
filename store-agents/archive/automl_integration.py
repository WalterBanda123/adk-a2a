#!/usr/bin/env python3
"""
AutoML Integration with Existing Vision System
Phase 4: Integrate custom model with current infrastructure
"""
import os
import logging
import json
import base64
import re
from typing import Dict, Any, Optional
from google.cloud import automl
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoMLProductProcessor:
    """Enhanced product processor using custom AutoML model with fallback"""
    
    def __init__(self):
        self.project_id = "deve-01"
        self.location = "us-central1"
        self.model_id = None  # Will be loaded from training info
        
        # Initialize clients
        try:
            self.automl_client = automl.PredictionServiceClient()
            self.model_path = self._load_model_path()
            logger.info("✅ AutoML client initialized")
        except Exception as e:
            logger.error(f"❌ AutoML client initialization failed: {e}")
            self.automl_client = None
            self.model_path = None
        
        # Initialize fallback processor
        try:
            from enhanced_add_product_vision_tool_clean import EnhancedProductVisionProcessor
            self.fallback_processor = EnhancedProductVisionProcessor()
            logger.info("✅ Fallback processor available")
        except ImportError:
            self.fallback_processor = None
            logger.warning("⚠️ Fallback processor not available")
    
    def _load_model_path(self) -> Optional[str]:
        """Load trained model path from training info"""
        try:
            with open("model_training_info.json", "r") as f:
                training_info = json.load(f)
            
            model_path = training_info.get("model_path")
            if model_path and training_info.get("deployment_status") == "deployed":
                logger.info(f"📊 Loaded model: {model_path}")
                return model_path
            else:
                logger.warning("⚠️ Model not deployed yet")
                return None
                
        except FileNotFoundError:
            logger.warning("⚠️ No model training info found")
            return None
    
    async def process_image(self, image_data: str, is_url: bool = False, user_id: str = "default") -> Dict[str, Any]:
        """
        Process image with AutoML model first, fallback to enhanced processor
        """
        
        # Try AutoML first if available
        if self.automl_client and self.model_path:
            try:
                result = await self._process_with_automl(image_data, is_url)
                
                # Check confidence threshold
                if result.get("confidence", 0) >= 0.8:
                    logger.info("✅ High confidence AutoML result")
                    return result
                else:
                    logger.info("⚠️ Low confidence, trying fallback")
            
            except Exception as e:
                logger.error(f"❌ AutoML processing failed: {e}")
        
        # Fallback to enhanced processor
        if self.fallback_processor:
            try:
                logger.info("🔄 Using fallback enhanced processor")
                result = self.fallback_processor.process_image(image_data, is_url, user_id)
                result["detection_method"] = "enhanced_dynamic_classifier_fallback"
                return result
            except Exception as e:
                logger.error(f"❌ Fallback processing failed: {e}")
        
        # Final fallback - basic result
        return self._create_basic_result()
    
    async def _process_with_automl(self, image_data: str, is_url: bool) -> Dict[str, Any]:
        """Process image using custom AutoML model"""
        
        try:
            # Prepare image data
            if is_url:
                # Download image from URL
                import requests
                response = requests.get(image_data)
                image_bytes = response.content
            else:
                # Decode base64 image
                image_bytes = base64.b64decode(image_data)
            
            # Create prediction payload
            payload = automl.ExamplePayload(
                image=automl.Image(image_bytes=image_bytes)
            )
            
            # Make prediction
            request = automl.PredictRequest(
                name=self.model_path,
                payload=payload,
                params={"score_threshold": "0.6"}  # Lower threshold for initial detection
            )
            
            response = self.automl_client.predict(request=request)
            
            # Parse response
            return self._parse_automl_response(response)
            
        except Exception as e:
            logger.error(f"AutoML prediction error: {e}")
            raise
    
    def _parse_automl_response(self, response) -> Dict[str, Any]:
        """Parse AutoML response into structured product data"""
        
        result = {
            "success": True,
            "title": "Unknown Product",
            "brand": "",
            "size": "",
            "unit": "",
            "category": "General",
            "subcategory": "",
            "description": "",
            "confidence": 0.0,
            "detection_method": "automl_custom_model",
            "processing_time": 0
        }
        
        detected_objects = {
            "brand": [],
            "product_name": [],
            "size": [],
            "category": []
        }
        
        # Extract detected objects
        for prediction in response.payload:
            if hasattr(prediction, 'object_detection'):
                detection = prediction.object_detection
                label = prediction.display_name
                confidence = detection.score
                
                # Only consider high-confidence detections
                if confidence > 0.6:
                    if label in detected_objects:
                        detected_objects[label].append({
                            "text": self._extract_text_from_detection(detection),
                            "confidence": confidence
                        })
        
        # Process detected objects with highest confidence
        if detected_objects["brand"]:
            best_brand = max(detected_objects["brand"], key=lambda x: x["confidence"])
            result["brand"] = best_brand["text"]
        
        if detected_objects["product_name"]:
            best_product = max(detected_objects["product_name"], key=lambda x: x["confidence"])
            result["title"] = best_product["text"]
        
        if detected_objects["size"]:
            best_size = max(detected_objects["size"], key=lambda x: x["confidence"])
            size_text = best_size["text"]
            
            # Extract size and unit using regex
            size_match = re.search(r'(\d+(?:\.\d+)?)\s*(kg|g|ml|l|oz|lbs)', size_text.lower())
            if size_match:
                result["size"] = size_match.group(1)
                result["unit"] = size_match.group(2)
        
        if detected_objects["category"]:
            best_category = max(detected_objects["category"], key=lambda x: x["confidence"])
            result["category"] = best_category["text"]
        
        # Build comprehensive title if we have brand and product
        if result["brand"] and result["title"] != "Unknown Product":
            if result["brand"].lower() not in result["title"].lower():
                result["title"] = f"{result['brand']} {result['title']}"
        elif result["brand"] and result["title"] == "Unknown Product":
            result["title"] = f"{result['brand']} Product"
        
        # Add size to title if available
        if result["size"] and result["unit"]:
            result["title"] = f"{result['title']} {result['size']}{result['unit']}"
            result["description"] = f"{result['title']}"
        
        # Calculate overall confidence
        all_confidences = []
        for obj_list in detected_objects.values():
            if obj_list:
                all_confidences.extend([obj["confidence"] for obj in obj_list])
        
        if all_confidences:
            result["confidence"] = min(0.98, max(0.7, sum(all_confidences) / len(all_confidences)))
        else:
            result["confidence"] = 0.3  # Low confidence if nothing detected
        
        return result
    
    def _extract_text_from_detection(self, detection) -> str:
        """Extract text from AutoML object detection result"""
        
        # Try different ways to extract text from detection
        if hasattr(detection, 'text_extraction') and detection.text_extraction:
            if hasattr(detection.text_extraction, 'text_segment'):
                return detection.text_extraction.text_segment.content
        
        # If no text extraction, use a placeholder based on bounding box
        # This would need to be enhanced with actual OCR if needed
        return "Detected Object"
    
    def _create_basic_result(self) -> Dict[str, Any]:
        """Create basic fallback result"""
        return {
            "success": True,
            "title": "Unknown Product",
            "brand": "",
            "size": "",
            "unit": "",
            "category": "General",
            "subcategory": "Miscellaneous",
            "description": "Product detection unavailable",
            "confidence": 0.3,
            "detection_method": "basic_fallback",
            "processing_time": 0
        }

class EnhancedAutoMLVisionServer:
    """Integration class for updating the direct vision server"""
    
    def __init__(self):
        self.automl_processor = AutoMLProductProcessor()
    
    async def analyze_image_enhanced(self, image_data: str, is_url: bool, user_id: str) -> Dict[str, Any]:
        """Enhanced image analysis with AutoML integration"""
        
        try:
            # Process with AutoML-enhanced system
            result = await self.automl_processor.process_image(image_data, is_url, user_id)
            
            # Format response for API
            if result.get("success"):
                product_data = {
                    "title": result.get("title", "Unknown Product"),
                    "brand": result.get("brand", ""),
                    "size": result.get("size", ""),
                    "unit": result.get("unit", ""),
                    "category": result.get("category", "General"),
                    "subcategory": result.get("subcategory", ""),
                    "description": result.get("description", ""),
                    "confidence": result.get("confidence", 0.0),
                    "processing_time": result.get("processing_time", 0)
                }
                
                # Build summary message
                title = product_data["title"]
                brand = product_data["brand"]
                size = product_data["size"]
                unit = product_data["unit"]
                category = product_data["category"]
                confidence = product_data["confidence"]
                
                summary_parts = [f"✅ Product identified: {title}"]
                if brand and brand.lower() not in title.lower():
                    summary_parts.append(f"Brand: {brand}")
                if size and unit:
                    summary_parts.append(f"Size: {size}{unit}")
                if category and category != "General":
                    summary_parts.append(f"Category: {category}")
                summary_parts.append(f"Confidence: {confidence:.1%}")
                
                return {
                    "message": " | ".join(summary_parts),
                    "status": "success",
                    "data": {
                        "product": product_data,
                        "processing_method": result.get("detection_method", "automl_enhanced")
                    }
                }
            else:
                return {
                    "message": f"Failed to analyze image: {result.get('error', 'Unknown error')}",
                    "status": "error",
                    "data": {"error": result.get("error", "Unknown error")}
                }
                
        except Exception as e:
            logger.error(f"Enhanced analysis failed: {e}")
            return {
                "message": f"Image processing error: {str(e)}",
                "status": "error", 
                "data": {"error": str(e)}
            }

# Test function
async def test_automl_integration():
    """Test the AutoML integration"""
    
    print("🧪 Testing AutoML Integration")
    print("=" * 40)
    
    processor = AutoMLProductProcessor()
    
    # Test with sample image (if available)
    image_path = "images-mazoe-ruspberry.jpeg"
    if os.path.exists(image_path):
        print(f"📸 Testing with image: {image_path}")
        
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        result = await processor.process_image(image_data, is_url=False, user_id="test_user")
        
        print("\n📋 Result:")
        print(f"Title: {result.get('title', 'N/A')}")
        print(f"Brand: {result.get('brand', 'N/A')}")
        print(f"Size: {result.get('size', 'N/A')} {result.get('unit', '')}")
        print(f"Category: {result.get('category', 'N/A')}")
        print(f"Confidence: {result.get('confidence', 0):.2f}")
        print(f"Method: {result.get('detection_method', 'unknown')}")
        
    else:
        print(f"❌ Test image not found: {image_path}")

if __name__ == "__main__":
    asyncio.run(test_automl_integration())
