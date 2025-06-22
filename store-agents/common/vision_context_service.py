"""
Vision Context Service - Provides product context directly to Google Vision API
"""
import os
import logging
from typing import Dict, Any, List, Optional
from google.cloud import vision
from google.protobuf import field_mask_pb2

logger = logging.getLogger(__name__)

class VisionContextService:
    """Service to provide product context directly to Vision API"""
    
    def __init__(self):
        self.client = None
        
    def _initialize_client(self):
        """Initialize Vision API client"""
        if not self.client:
            try:
                self.client = vision.ImageAnnotatorClient()
                logger.info("Vision Context Service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Vision client: {e}")
    
    async def detect_products_with_context(self, image, product_hints: List[str]) -> Dict[str, Any]:
        """
        Use Vision API's web detection with product hints for better brand recognition
        """
        self._initialize_client()
        
        try:
            # Method 1: Web Detection with Geographic Hints
            web_request = vision.WebDetectionParams(
                include_geo_results=True  # Include geographic context
            )
            
            # Method 2: Enhanced Text Detection with Language Hints
            text_request = vision.TextDetectionParams(
                enable_text_detection_confidence_score=True
                # Note: Advanced OCR options may not be available in all API versions
            )
            
            # Combine all detection methods
            image_context = vision.ImageContext(
                web_detection_params=web_request,
                text_detection_params=text_request,
                # Add geographic context if available
                lat_long_rect=self._get_geographic_context()
            )
            
            # Run enhanced detection
            features = [
                vision.Feature(type_=vision.Feature.Type.WEB_DETECTION, max_results=50),
                vision.Feature(type_=vision.Feature.Type.TEXT_DETECTION, max_results=50),
                vision.Feature(type_=vision.Feature.Type.LABEL_DETECTION, max_results=50),
                vision.Feature(type_=vision.Feature.Type.OBJECT_LOCALIZATION, max_results=20),
                vision.Feature(type_=vision.Feature.Type.LOGO_DETECTION, max_results=20),
            ]
            
            request = vision.AnnotateImageRequest(
                image=image,
                features=features,
                image_context=image_context
            )
            
            response = self.client.annotate_image(request=request) if self.client else None
            
            if not response:
                logger.error("Vision client not available for enhanced detection")
                return {}
            
            return self._process_enhanced_response(response, product_hints)
            
        except Exception as e:
            logger.error(f"Enhanced detection failed: {e}")
            return {}
    
    def _get_geographic_context(self):
        """Get geographic context for better local product recognition"""
        try:
            # Try to use LatLng if available in the vision module
            LatLng = getattr(vision, 'LatLng', None)
            LatLongRect = getattr(vision, 'LatLongRect', None)
            
            if LatLng and LatLongRect:
                # For Zimbabwe, approximate coordinates
                return LatLongRect(
                    min_lat_lng=LatLng(latitude=-22.4, longitude=29.8),
                    max_lat_lng=LatLng(latitude=-15.6, longitude=33.1)
                )
        except Exception as e:
            logger.debug(f"Geographic context not available: {e}")
        
        return None
    
    def _process_enhanced_response(self, response, product_hints: List[str]) -> Dict[str, Any]:
        """Process the enhanced Vision API response with product context"""
        results = {
            'brands': [],
            'products': [],
            'text_elements': [],
            'confidence_scores': {}
        }
        
        # Process web entities (often contains brand information)
        if response.web_detection and response.web_detection.web_entities:
            for entity in response.web_detection.web_entities:
                if entity.description and entity.score > 0.3:
                    # Check if entity matches our product hints
                    for hint in product_hints:
                        if self._fuzzy_match(entity.description.lower(), hint.lower(), threshold=0.8):
                            results['brands'].append({
                                'name': entity.description,
                                'confidence': entity.score,
                                'source': 'web_entity',
                                'matched_hint': hint
                            })
        
        # Process logos (brand detection)
        if response.logo_annotations:
            for logo in response.logo_annotations:
                results['brands'].append({
                    'name': logo.description,
                    'confidence': logo.score,
                    'source': 'logo_detection',
                    'bounding_box': self._extract_bounding_box(logo.bounding_poly)
                })
        
        # Process text with product context
        if response.text_annotations:
            full_text = response.text_annotations[0].description if response.text_annotations else ""
            
            # Extract product-relevant text using hints
            for hint in product_hints:
                if hint.lower() in full_text.lower():
                    results['products'].append({
                        'detected_text': hint,
                        'confidence': 0.9,  # High confidence for exact matches
                        'source': 'text_detection'
                    })
        
        # Process labels with product context
        if response.label_annotations:
            for label in response.label_annotations:
                # Check if label relates to our product categories
                if self._is_product_relevant(label.description, product_hints):
                    results['products'].append({
                        'category': label.description,
                        'confidence': label.score,
                        'source': 'label_detection'
                    })
        
        return results
    
    def _fuzzy_match(self, text1: str, text2: str, threshold: float = 0.8) -> bool:
        """Simple fuzzy matching"""
        from difflib import SequenceMatcher
        return SequenceMatcher(None, text1, text2).ratio() >= threshold
    
    def _extract_bounding_box(self, bounding_poly) -> Dict:
        """Extract bounding box coordinates"""
        if not bounding_poly or not bounding_poly.vertices:
            return {}
        
        vertices = [(v.x, v.y) for v in bounding_poly.vertices]
        return {
            'vertices': vertices,
            'center': self._calculate_center(vertices)
        }
    
    def _calculate_center(self, vertices: List[tuple]) -> tuple:
        """Calculate center point of bounding box"""
        if not vertices:
            return (0, 0)
        
        x_coords = [v[0] for v in vertices]
        y_coords = [v[1] for v in vertices]
        
        return (
            sum(x_coords) / len(x_coords),
            sum(y_coords) / len(y_coords)
        )
    
    def _is_product_relevant(self, label: str, product_hints: List[str]) -> bool:
        """Check if a label is relevant to our product categories"""
        product_categories = [
            'beverage', 'drink', 'bottle', 'can', 'food', 'snack',
            'package', 'container', 'product', 'brand', 'grocery'
        ]
        
        label_lower = label.lower()
        
        # Check against known categories
        if any(cat in label_lower for cat in product_categories):
            return True
        
        # Check against product hints
        return any(hint.lower() in label_lower for hint in product_hints)

class SmartProductDetector:
    """Enhanced product detector using Vision API context features"""
    
    def __init__(self, vision_context_service: VisionContextService):
        self.vision_service = vision_context_service
        
    async def detect_products_smart(self, image, user_store_context: Dict) -> Dict[str, Any]:
        """
        Smart product detection using store context
        """
        # Extract product hints from store context
        product_hints = self._build_product_hints(user_store_context)
        
        # Use Vision API with context
        vision_results = await self.vision_service.detect_products_with_context(
            image, product_hints
        )
        
        # Post-process with store-specific logic
        return self._post_process_with_store_context(vision_results, user_store_context)
    
    def _build_product_hints(self, store_context: Dict) -> List[str]:
        """Build product hints from store context"""
        hints = []
        
        # Add brands from store's country/industry
        if 'brands' in store_context:
            hints.extend(store_context['brands'])
        
        # Add common product types for the industry
        if 'product_types' in store_context:
            hints.extend(store_context['product_types'])
        
        # Add location-specific terms
        if 'location_keywords' in store_context:
            hints.extend(store_context['location_keywords'])
        
        return hints
    
    def _post_process_with_store_context(self, vision_results: Dict, store_context: Dict) -> Dict:
        """Post-process Vision results with store context"""
        processed = {
            'title': 'Unknown Product',
            'brand': '',
            'confidence': 0.0,
            'detection_method': 'unknown'
        }
        
        # Prioritize brand detection
        if vision_results.get('brands'):
            best_brand = max(vision_results['brands'], key=lambda x: x['confidence'])
            processed['brand'] = best_brand['name']
            processed['confidence'] = best_brand['confidence']
            processed['detection_method'] = best_brand['source']
            
            # Try to build title from brand + product type
            if vision_results.get('products'):
                best_product = max(vision_results['products'], key=lambda x: x['confidence'])
                if 'category' in best_product:
                    processed['title'] = f"{best_brand['name']} {best_product['category']}"
                else:
                    processed['title'] = best_brand['name']
        
        return processed
