#!/usr/bin/env python3
"""
AutoML Production Integration
Connect trained AutoML model to existing vision system
"""
import json
import base64
import os
from google.cloud import automl
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class AutoMLProductionProcessor:
    """Production-ready AutoML processor for product recognition"""
    
    def __init__(self):
        # Load model info
        try:
            with open('automl_model_info.json', 'r') as f:
                self.model_info = json.load(f)
            self.model_path = self.model_info['model_path']
            self.model_available = True
        except FileNotFoundError:
            logger.warning("AutoML model not found, will use fallback")
            self.model_available = False
            self.model_path = None
        
        # Initialize AutoML client
        if self.model_available:
            self.prediction_client = automl.PredictionServiceClient()
        
        # Load fallback processor
        try:
            from enhanced_add_product_vision_tool_clean import EnhancedProductVisionProcessor
            self.fallback_processor = EnhancedProductVisionProcessor()
        except ImportError:
            logger.error("Fallback processor not available")
            self.fallback_processor = None
    
    def predict_with_automl(self, image_data: bytes, confidence_threshold: float = 0.5) -> Dict[str, Any]:
        """Make prediction using trained AutoML model"""
        
        if not self.model_available:
            raise Exception("AutoML model not available")
        
        try:
            # Prepare the image for prediction
            image = automl.Image(image_bytes=image_data)
            payload = automl.ExamplePayload(image=image)
            
            # Make prediction request
            request = automl.PredictRequest(
                name=self.model_path,
                payload=payload,
                params={"score_threshold": str(confidence_threshold)}
            )
            
            response = self.prediction_client.predict(request=request)
            
            # Process results
            results = {
                "brand": None,
                "product_name": None, 
                "size": None,
                "category": None,
                "confidence_scores": {},
                "processing_method": "automl_custom_model"
            }
            
            # Extract predictions by label type
            for prediction in response.payload:
                label = prediction.display_name
                confidence = prediction.classification.score
                
                # Determine label type and update results
                if confidence >= confidence_threshold:
                    if self._is_brand_label(label):
                        if not results["brand"] or confidence > results["confidence_scores"].get("brand", 0):
                            results["brand"] = label
                            results["confidence_scores"]["brand"] = confidence
                    
                    elif self._is_size_label(label):
                        if not results["size"] or confidence > results["confidence_scores"].get("size", 0):
                            results["size"] = label
                            results["confidence_scores"]["size"] = confidence
                    
                    elif self._is_category_label(label):
                        if not results["category"] or confidence > results["confidence_scores"].get("category", 0):
                            results["category"] = label
                            results["confidence_scores"]["category"] = confidence
                    
                    else:
                        # Assume it's a product name
                        if not results["product_name"] or confidence > results["confidence_scores"].get("product_name", 0):
                            results["product_name"] = label
                            results["confidence_scores"]["product_name"] = confidence
            
            # Calculate overall confidence
            avg_confidence = sum(results["confidence_scores"].values()) / max(len(results["confidence_scores"]), 1)
            results["overall_confidence"] = avg_confidence
            
            logger.info(f"AutoML prediction completed with confidence: {avg_confidence:.2f}")
            return results
            
        except Exception as e:
            logger.error(f"AutoML prediction failed: {e}")
            raise
    
    def _is_brand_label(self, label: str) -> bool:
        """Check if label is a brand name"""
        known_brands = [
            "hullets", "mazoe", "coca cola", "pepsi", "dairibord", 
            "olivine", "tanganda", "cairns", "gloria", "lobels"
        ]
        return label.lower() in known_brands
    
    def _is_size_label(self, label: str) -> bool:
        """Check if label is a size/weight"""
        import re
        size_pattern = r'\d+(\.\d+)?(kg|g|ml|l|litre|liter)\b'
        return bool(re.search(size_pattern, label.lower()))
    
    def _is_category_label(self, label: str) -> bool:
        """Check if label is a category"""
        categories = [
            "staples", "beverages", "dairy", "cooking_oils", 
            "snacks", "household", "personal_care"
        ]
        return label.lower() in categories
    
    def process_product_image(self, image_data: bytes, use_fallback_on_low_confidence: bool = True) -> Dict[str, Any]:
        """Main processing method with fallback support"""
        
        try:
            # Try AutoML first
            if self.model_available:
                result = self.predict_with_automl(image_data, confidence_threshold=0.6)
                
                # Check if we have good results
                overall_confidence = result.get("overall_confidence", 0)
                
                if overall_confidence >= 0.6:
                    logger.info(f"AutoML processing successful (confidence: {overall_confidence:.2f})")
                    return result
                
                elif use_fallback_on_low_confidence and self.fallback_processor:
                    logger.info(f"AutoML confidence low ({overall_confidence:.2f}), using fallback")
                    fallback_result = self.fallback_processor.process_image_for_product_detection(image_data)
                    
                    # Combine results, preferring AutoML where confident
                    combined_result = self._combine_results(result, fallback_result)
                    return combined_result
                
                else:
                    return result
            
            # Fallback only
            elif self.fallback_processor:
                logger.info("Using fallback processor (AutoML not available)")
                return self.fallback_processor.process_image_for_product_detection(image_data)
            
            else:
                raise Exception("No processing method available")
        
        except Exception as e:
            logger.error(f"Product processing failed: {e}")
            
            # Final fallback
            if self.fallback_processor:
                logger.info("Using fallback due to error")
                return self.fallback_processor.process_image_for_product_detection(image_data)
            else:
                raise
    
    def _combine_results(self, automl_result: Dict[str, Any], fallback_result: Dict[str, Any]) -> Dict[str, Any]:
        """Intelligently combine AutoML and fallback results"""
        
        combined = {
            "brand": None,
            "product_name": None,
            "size": None, 
            "category": None,
            "confidence_scores": {},
            "processing_method": "automl_with_fallback"
        }
        
        # Use AutoML results where confidence is good (>0.5)
        automl_confidence = automl_result.get("confidence_scores", {})
        
        for field in ["brand", "product_name", "size", "category"]:
            automl_conf = automl_confidence.get(field, 0)
            
            if automl_conf > 0.5 and automl_result.get(field):
                combined[field] = automl_result[field]
                combined["confidence_scores"][field] = automl_conf
            elif fallback_result.get(field):
                combined[field] = fallback_result[field]
                combined["confidence_scores"][field] = fallback_result.get("confidence", 0.4)
        
        # Calculate overall confidence
        if combined["confidence_scores"]:
            combined["overall_confidence"] = sum(combined["confidence_scores"].values()) / len(combined["confidence_scores"])
        else:
            combined["overall_confidence"] = 0.3
        
        return combined
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get current model status and statistics"""
        
        status = {
            "automl_available": self.model_available,
            "fallback_available": self.fallback_processor is not None,
            "model_path": self.model_path,
            "ready_for_production": self.model_available
        }
        
        if self.model_available:
            try:
                status.update(self.model_info)
            except:
                pass
        
        return status

# Integration with existing server
def create_enhanced_processor():
    """Factory function to create the production processor"""
    return AutoMLProductionProcessor()

# Test function
def test_automl_integration():
    """Test the AutoML integration"""
    
    processor = AutoMLProductionProcessor()
    status = processor.get_model_status()
    
    print("🧪 AutoML Integration Test")
    print("=" * 40)
    print(f"✅ AutoML Available: {status['automl_available']}")
    print(f"✅ Fallback Available: {status['fallback_available']}")
    print(f"✅ Production Ready: {status['ready_for_production']}")
    
    if status['automl_available']:
        print(f"🤖 Model: {status.get('model_name', 'Unknown')}")
        print(f"📊 Path: {status.get('model_path', 'Unknown')}")
    
    # Test with sample image if available
    test_images = ['images-mazoe-ruspberry.jpeg', 'encoded_image.txt']
    
    for test_image in test_images:
        if os.path.exists(test_image):
            print(f"\n🧪 Testing with: {test_image}")
            
            try:
                if test_image.endswith('.txt'):
                    # Encoded image
                    with open(test_image, 'r') as f:
                        encoded_data = f.read().strip()
                    image_data = base64.b64decode(encoded_data)
                else:
                    # Regular image file
                    with open(test_image, 'rb') as f:
                        image_data = f.read()
                
                result = processor.process_product_image(image_data)
                
                print("📋 Results:")
                print(f"   Brand: {result.get('brand', 'Not detected')}")
                print(f"   Product: {result.get('product_name', 'Not detected')}")
                print(f"   Size: {result.get('size', 'Not detected')}")
                print(f"   Category: {result.get('category', 'Not detected')}")
                print(f"   Confidence: {result.get('overall_confidence', 0):.2f}")
                print(f"   Method: {result.get('processing_method', 'Unknown')}")
                
            except Exception as e:
                print(f"❌ Test failed: {e}")
            
            break
    
    print("\n🎉 Integration test complete!")

if __name__ == "__main__":
    test_automl_integration()
