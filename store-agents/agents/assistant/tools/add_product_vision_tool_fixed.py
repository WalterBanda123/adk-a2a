# Enhanced Product Vision Tool - Fixed Version
import os
import sys
import json
import base64
import logging
import re
from typing import Dict, Any, List, Tuple, Optional
import requests

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

try:
    from google.cloud import vision
    from google.oauth2 import service_account
    VISION_AVAILABLE = True
except ImportError:
    vision = None
    service_account = None
    VISION_AVAILABLE = False

from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)

class ProductVisionProcessor:
    """Enhanced product image processor using Google Cloud Vision API with store context"""
    
    def __init__(self):
        # Lazy initialization - don't create client until needed
        self.client = None
        self._client_initialized = False
        
        # Store context will be loaded per user
        self.current_store_info: Optional[Dict] = None
    
    def _initialize_client(self):
        """Initialize the Vision API client when first needed"""
        if self._client_initialized:
            return
            
        self._client_initialized = True
        
        if VISION_AVAILABLE and vision and service_account:
            try:
                # Try to load service account credentials from the project root
                credentials_path = os.path.join(project_root, 'vision-api-service.json')
                
                if os.path.exists(credentials_path):
                    # Load credentials from service account file
                    credentials = service_account.Credentials.from_service_account_file(credentials_path)
                    self.client = vision.ImageAnnotatorClient(credentials=credentials)
                    logger.info("Google Cloud Vision API client initialized with service account")
                else:
                    # Fall back to default credentials (environment variable or gcloud auth)
                    self.client = vision.ImageAnnotatorClient()
                    logger.info("Google Cloud Vision API client initialized with default credentials")
                    
            except Exception as e:
                logger.error(f"Failed to initialize Vision API client: {e}")
                logger.error("Make sure 'vision-api-service.json' exists in the project root or set GOOGLE_APPLICATION_CREDENTIALS")
        else:
            logger.warning("Google Cloud Vision API not available - install google-cloud-vision")

    def process_image(self, image_data: str, is_url: bool, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Process product image and extract structured information using enhanced Vision API"""
        # Initialize client when first needed
        self._initialize_client()
        
        if not self.client:
            return {
                "success": False,
                "error": "Google Cloud Vision API not available"
            }
        
        try:
            logger.info("🔄 Starting enhanced image processing with store context...")
            
            # Load user-specific store context
            if user_id:
                self._load_user_store_context(user_id)
            
            # Prepare image for Vision API
            logger.info("📷 Preparing image for Vision API...")
            image = self._prepare_image(image_data, is_url)
            if not image:
                return {
                    "success": False,
                    "error": "Failed to process image data"
                }
            
            logger.info("🔍 Running enhanced Vision API detection with store context...")
            
            # Use enhanced detection with store context
            if self.current_store_info:
                product_info = self._detect_with_store_context(image, self.current_store_info)
            else:
                logger.warning("No store context available, using basic detection")
                product_info = self._basic_detection(image)
            
            logger.info(f"✅ Image processed successfully")
            
            return {
                "success": True,
                "product": product_info
            }
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _load_user_store_context(self, user_id: str):
        """Load user-specific store context for enhanced detection"""
        
        try:
            # TODO: Get actual store info from user service
            # For now, use sample data based on common store types
            store_info = {
                'country': 'zimbabwe',
                'industry': 'retail',
                'business_type': 'grocery',
                'brands': ['delta', 'lobels', 'mazoe', 'coca cola', 'pepsi', 'fanta', 'sprite', 
                          'castle', 'lion', 'zambezi', 'schweppes', 'cairns', 'dairibord'],
                'product_types': ['juice', 'soda', 'water', 'beer', 'milk', 'bread', 'chips', 'snacks'],
                'common_sizes': ['330ml', '500ml', '750ml', '1L', '2L', '500g', '1kg', '2kg'],
                'location_keywords': ['zimbabwe', 'harare', 'bulawayo', 'gweru']
            }
            
            self.current_store_info = store_info
            logger.info(f"✅ Loaded store context: {store_info['country']}-{store_info['industry']} with {len(store_info['brands'])} brands")
            
        except Exception as e:
            logger.error(f"Failed to load store context: {e}")
            self.current_store_info = None
    
    def _prepare_image(self, image_data: str, is_url: bool):
        """Prepare image for Vision API processing"""
        if not VISION_AVAILABLE or not vision:
            return None
            
        try:
            if is_url:
                # Download image from URL
                response = requests.get(image_data, timeout=5)
                response.raise_for_status()
                content = response.content
            else:
                # Decode base64 image
                # Remove data URL prefix if present
                if image_data.startswith('data:image'):
                    image_data = image_data.split(',', 1)[1]
                content = base64.b64decode(image_data)
            
            return vision.Image(content=content)
            
        except Exception as e:
            logger.error(f"Failed to prepare image: {e}")
            return None
    
    def _detect_with_store_context(self, image, store_context: Dict) -> Dict[str, Any]:
        """
        Enhanced detection using Google Cloud Vision API with direct context provision
        """
        try:
            # Create comprehensive image context with all store information
            image_context = self._create_enhanced_image_context(store_context)
            
            # Set up comprehensive feature detection prioritizing our needs
            if VISION_AVAILABLE and vision:
                features = [
                    # Text detection with enhanced context for brand/product names
                    vision.Feature(type_=vision.Feature.Type.TEXT_DETECTION, max_results=50),
                    
                    # Web detection for brand recognition (very powerful for known brands)
                    vision.Feature(type_=vision.Feature.Type.WEB_DETECTION, max_results=30),
                    
                    # Logo detection for brand logos
                    vision.Feature(type_=vision.Feature.Type.LOGO_DETECTION, max_results=20),
                    
                    # Label detection for product categories
                    vision.Feature(type_=vision.Feature.Type.LABEL_DETECTION, max_results=30),
                    
                    # Object localization for product positioning
                    vision.Feature(type_=vision.Feature.Type.OBJECT_LOCALIZATION, max_results=20),
                ]
                
                # Create request with enhanced context
                request = vision.AnnotateImageRequest(
                    image=image,
                    features=features,
                    image_context=image_context
                )
                
                # Execute Vision API call
                if self.client:
                    response = self.client.annotate_image(request=request)
                    
                    # Process results with store context
                    return self._process_enhanced_response(response, store_context)
                else:
                    return self._basic_detection_fallback()
            else:
                # Fallback when Vision API not available
                return self._basic_detection_fallback()
                
        except Exception as e:
            logger.error(f"Enhanced detection failed: {e}")
            return self._basic_detection_fallback()
    
    def _create_enhanced_image_context(self, store_context: Dict):
        """
        Create comprehensive image context with store-specific information for Vision API
        """
        if not VISION_AVAILABLE or not vision:
            return None
            
        image_context = vision.ImageContext()
        
        # 1. Geographic context for better regional recognition
        if store_context.get('country') == 'zimbabwe':
            # Set geographic bounds for Zimbabwe to improve regional product recognition
            try:
                LatLongRect = getattr(vision, 'LatLongRect', None)
                LatLng = getattr(vision, 'LatLng', None)
                
                if LatLongRect and LatLng:
                    image_context.lat_long_rect = LatLongRect(
                        min_lat_lng=LatLng(latitude=-22.4, longitude=29.8),
                        max_lat_lng=LatLng(latitude=-15.6, longitude=33.1)
                    )
                    logger.info("🌍 Added Zimbabwe geographic context to Vision API")
                else:
                    logger.warning("Geographic context not available in this Vision API version")
            except Exception as e:
                logger.warning(f"Could not set geographic context: {e}")
        
        # 2. Language hints for better OCR accuracy
        image_context.language_hints = ['en']  # English for Zimbabwe
        
        # 3. Build product vocabulary to guide text detection
        vocabulary = self._build_product_vocabulary(store_context)
        logger.info(f"🎯 Providing {len(vocabulary)} vocabulary terms to Vision API")
        
        # Note: Vision API doesn't directly support vocabulary in all versions,
        # but geographic and language context significantly improve detection
        
        return image_context
    
    def _build_product_vocabulary(self, store_context: Dict) -> List[str]:
        """
        Build vocabulary from store context to guide Vision API text detection
        """
        vocabulary = []
        
        # Add store-specific brands
        if store_context.get('brands'):
            vocabulary.extend(store_context['brands'])
        
        # Add product types
        if store_context.get('product_types'):
            vocabulary.extend(store_context['product_types'])
        
        # Add common sizes/units
        if store_context.get('common_sizes'):
            vocabulary.extend(store_context['common_sizes'])
        
        # Add regional keywords
        if store_context.get('location_keywords'):
            vocabulary.extend(store_context['location_keywords'])
        
        # Add common product descriptors
        vocabulary.extend([
            'ml', 'kg', 'g', 'litre', 'liter', 'pack', 'bottle', 'can',
            'original', 'classic', 'diet', 'zero', 'light', 'fresh'
        ])
        
        return vocabulary
    
    def _process_enhanced_response(self, response, store_context: Dict) -> Dict[str, Any]:
        """Process enhanced Vision API response with store context"""
        
        product_info = {
            'title': 'Unknown Product',
            'brand': '',
            'size': '',
            'unit': '',
            'category': 'General',
            'subcategory': 'Miscellaneous',
            'description': '',
            'confidence': 0.0,
            'detection_method': 'enhanced_context'
        }
        
        # Extract all detected text for analysis
        full_text = ""
        if response.text_annotations:
            full_text = response.text_annotations[0].description.lower()
            logger.info(f"🔍 Detected text preview: {full_text[:100]}...")
        
        # 1. Enhanced brand detection using multiple sources
        detected_brand = self._detect_brand_enhanced(response, store_context, full_text)
        if detected_brand:
            product_info['brand'] = detected_brand['name']
            product_info['confidence'] = max(product_info['confidence'], detected_brand['confidence'])
            logger.info(f"🏷️  Detected brand: {detected_brand['name']} (confidence: {detected_brand['confidence']:.2f})")
        
        # 2. Enhanced size and unit extraction
        size, unit = self._extract_size_unit_enhanced(full_text, store_context)
        product_info['size'] = size
        product_info['unit'] = unit
        if size and unit:
            logger.info(f"📏 Detected size: {size}{unit}")
        
        # 3. Category determination from multiple sources
        category, subcategory = self._determine_category_enhanced(response, store_context, full_text)
        product_info['category'] = category
        product_info['subcategory'] = subcategory
        
        # 4. Build intelligent product title
        product_info['title'] = self._build_product_title_enhanced(
            detected_brand, full_text, category, response, store_context
        )
        
        # 5. Generate rich description
        product_info['description'] = self._generate_description_enhanced(
            product_info['title'], size, unit, category, detected_brand
        )
        
        logger.info(f"🎯 Final result: {product_info['title']} | {product_info['brand']} | {size}{unit}")
        
        return product_info
    
    def _detect_brand_enhanced(self, response, store_context: Dict, full_text: str) -> Optional[Dict]:
        """Enhanced brand detection using multiple Vision API sources"""
        
        candidates = []
        store_brands = store_context.get('brands', [])
        
        # 1. Logo detection (highest confidence)
        if response.logo_annotations:
            for logo in response.logo_annotations:
                candidates.append({
                    'name': logo.description,
                    'confidence': logo.score,
                    'source': 'logo_detection'
                })
        
        # 2. Web entities (very reliable for known brands)
        if response.web_detection and response.web_detection.web_entities:
            for entity in response.web_detection.web_entities:
                if entity.score > 0.4:  # High threshold for web entities
                    # Check if it matches our store brands
                    for brand in store_brands:
                        if self._fuzzy_match(entity.description.lower(), brand.lower(), 0.85):
                            candidates.append({
                                'name': brand,  # Use store brand name for consistency
                                'confidence': entity.score * 0.95,  # Slightly lower than logo
                                'source': 'web_entity_matched'
                            })
                            break
                    else:
                        # Add as candidate even if not in store list
                        candidates.append({
                            'name': entity.description,
                            'confidence': entity.score * 0.8,
                            'source': 'web_entity_generic'
                        })
        
        # 3. Text-based brand detection (good for clear text)
        for brand in store_brands:
            if brand.lower() in full_text:
                # Calculate confidence based on text clarity and position
                confidence = self._calculate_text_brand_confidence(brand, full_text)
                candidates.append({
                    'name': brand,
                    'confidence': confidence,
                    'source': 'text_exact_match'
                })
        
        # Return best candidate
        if candidates:
            best = max(candidates, key=lambda x: x['confidence'])
            logger.info(f"Brand detection: {len(candidates)} candidates, best: {best['name']} ({best['source']})")
            return best
        
        return None
    
    def _extract_size_unit_enhanced(self, text: str, store_context: Dict) -> Tuple[str, str]:
        """Enhanced size and unit extraction with store context"""
        
        if not text:
            return "", ""
        
        # Get common sizes from store context
        common_sizes = store_context.get('common_sizes', [])
        
        # 1. Check for exact matches from store's common sizes
        for size in common_sizes:
            if size.lower() in text.lower():
                # Split size and unit
                size_match = re.match(r'(\d+(?:\.\d+)?)\s*([a-zA-Z]+)', size)
                if size_match:
                    return size_match.group(1), size_match.group(2).lower()
        
        # 2. Enhanced pattern matching with OCR error handling
        patterns = [
            # Standard size patterns
            r'(\d+(?:\.\d+)?)\s*(ml|l|g|kg|liters?|litres?|grams?|kilos?)\b',
            
            # Multi-pack patterns
            r'(\d+)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*(ml|l|g|kg)\b',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                match = matches[0]
                if isinstance(match, tuple):
                    if len(match) == 3:  # Multi-pack
                        return f"{match[0]}x{match[1]}", match[2].lower()
                    elif len(match) == 2:  # Single size
                        return str(match[0]), match[1].lower()
        
        return "", ""
    
    def _determine_category_enhanced(self, response, store_context: Dict, full_text: str) -> Tuple[str, str]:
        """Enhanced category determination"""
        
        # Check labels with confidence thresholds
        if response.label_annotations:
            for label in response.label_annotations:
                if label.score > 0.7:  # High confidence labels only
                    label_desc = label.description.lower()
                    
                    if any(term in label_desc for term in ['drink', 'beverage', 'bottle', 'can', 'liquid']):
                        return "Beverages", "Soft Drinks"
                    elif any(term in label_desc for term in ['food', 'snack', 'grocery', 'package']):
                        return "Food", "Groceries"
                    elif any(term in label_desc for term in ['beer', 'alcohol']):
                        return "Beverages", "Alcoholic"
        
        # Check text content for category hints
        text_lower = full_text.lower()
        if any(term in text_lower for term in ['juice', 'soda', 'drink', 'water']):
            return "Beverages", "Soft Drinks"
        elif any(term in text_lower for term in ['beer', 'lager']):
            return "Beverages", "Alcoholic"
        elif any(term in text_lower for term in ['milk', 'yogurt']):
            return "Food", "Dairy"
        elif any(term in text_lower for term in ['bread', 'chips', 'biscuit']):
            return "Food", "Snacks"
        
        # Fallback based on business type
        business_type = store_context.get('business_type', 'general')
        if business_type == 'grocery':
            return "Food & Beverages", "General"
        
        return "General", "Miscellaneous"
    
    def _build_product_title_enhanced(self, detected_brand: Optional[Dict], text: str, 
                                     category: str, response, store_context: Dict) -> str:
        """Build enhanced product title using all available information"""
        
        if detected_brand:
            brand_name = detected_brand['name']
            
            # Look for product type/flavor in text
            product_descriptors = self._extract_product_descriptors(text, brand_name)
            
            if product_descriptors:
                return f"{brand_name} {product_descriptors}"
            
            # Fallback to brand + category
            if category and category != 'General':
                return f"{brand_name} {category}"
            
            return brand_name
        
        # No brand detected - use best text line
        return self._extract_best_title_from_text(text)
    
    def _extract_product_descriptors(self, text: str, brand: str) -> str:
        """Extract product descriptors like flavors, types, variants"""
        
        # Common product descriptors
        flavors = ['orange', 'apple', 'grape', 'lemon', 'strawberry', 'vanilla', 'chocolate', 'berry']
        types = ['juice', 'soda', 'water', 'beer', 'lager', 'drink', 'cola']
        variants = ['diet', 'zero', 'light', 'max', 'original', 'classic', 'fresh']
        
        found_descriptors = []
        text_lower = text.lower()
        
        # Find flavors
        for flavor in flavors:
            if flavor in text_lower:
                found_descriptors.append(flavor.title())
                break  # Only take first flavor found
        
        # Find types
        for ptype in types:
            if ptype in text_lower and ptype not in brand.lower():
                found_descriptors.append(ptype.title())
                break
        
        # Find variants
        for variant in variants:
            if variant in text_lower:
                found_descriptors.append(variant.title())
                break
        
        return " ".join(found_descriptors)
    
    def _extract_best_title_from_text(self, text: str) -> str:
        """Extract best title when no brand is detected"""
        
        if not text:
            return "Unknown Product"
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        if not lines:
            return "Unknown Product"
        
        best_line = ""
        best_score = 0
        
        for line in lines:
            words = line.split()
            score = 0
            
            # Prefer 2-6 word lines
            if 2 <= len(words) <= 6:
                score += 3
            elif len(words) == 1:
                score += 1
            
            # Avoid number-heavy lines
            digit_ratio = sum(c.isdigit() for c in line) / len(line) if line else 0
            score -= digit_ratio * 2
            
            # Prefer product-related words
            product_words = ['juice', 'drink', 'soda', 'water', 'milk', 'beer', 'cola']
            if any(word in line.lower() for word in product_words):
                score += 2
            
            # Avoid technical/legal text
            avoid_words = ['manufactured', 'distributed', 'ingredients', 'nutrition', 'warning']
            if any(word in line.lower() for word in avoid_words):
                score -= 3
            
            if score > best_score:
                best_score = score
                best_line = line
        
        return best_line.title() if best_line else "Unknown Product"
    
    def _basic_detection(self, image) -> Dict[str, Any]:
        """Fallback basic detection"""
        
        try:
            if VISION_AVAILABLE and vision:
                features = [
                    vision.Feature(type_=vision.Feature.Type.TEXT_DETECTION, max_results=10),
                    vision.Feature(type_=vision.Feature.Type.LABEL_DETECTION, max_results=10),
                ]
                
                request = vision.AnnotateImageRequest(image=image, features=features)
                if self.client:
                    response = self.client.annotate_image(request=request)
                    
                    title = "Unknown Product"
                    if response.text_annotations:
                        title = self._extract_best_title_from_text(response.text_annotations[0].description)
                else:
                    return self._basic_detection_fallback()
                
                return {
                    'title': title,
                    'brand': '',
                    'size': '',
                    'unit': '',
                    'category': 'General',
                    'subcategory': 'Miscellaneous',
                    'description': title,
                    'confidence': 0.5,
                    'detection_method': 'basic_fallback'
                }
            else:
                return self._basic_detection_fallback()
                
        except Exception as e:
            logger.error(f"Basic detection failed: {e}")
            return self._basic_detection_fallback()
    
    def _basic_detection_fallback(self) -> Dict[str, Any]:
        """Fallback detection when Vision API is not available"""
        return {
            'title': 'Unknown Product',
            'brand': '',
            'size': '',
            'unit': '',
            'category': 'General',
            'subcategory': 'Miscellaneous',
            'description': 'Unknown Product',
            'confidence': 0.0,
            'detection_method': 'fallback_no_vision_api'
        }
    
    def _calculate_text_brand_confidence(self, brand: str, text: str) -> float:
        """Calculate confidence for text-based brand detection"""
        
        confidence = 0.6  # Base confidence for exact text match
        
        # Bonus for brand appearing near start of text
        brand_pos = text.find(brand.lower())
        if brand_pos >= 0 and brand_pos < len(text) * 0.3:
            confidence += 0.2
        
        # Bonus for brand appearing multiple times
        brand_count = text.lower().count(brand.lower())
        if brand_count > 1:
            confidence += min(brand_count * 0.1, 0.2)
        
        return min(confidence, 0.95)  # Cap at 0.95
    
    def _fuzzy_match(self, text1: str, text2: str, threshold: float = 0.8) -> bool:
        """Simple fuzzy matching between two strings"""
        
        if not text1 or not text2:
            return False
        
        # Normalize
        t1 = text1.lower().strip()
        t2 = text2.lower().strip()
        
        if t1 == t2:
            return True
        
        # Character-based similarity
        shorter = min(len(t1), len(t2))
        longer = max(len(t1), len(t2))
        
        if shorter == 0:
            return longer == 0
        
        matches = sum(c1 == c2 for c1, c2 in zip(t1, t2))
        similarity = matches / longer
        
        return similarity >= threshold
    
    def _generate_description_enhanced(self, title: str, size: str, unit: str, 
                                     category: str, detected_brand: Optional[Dict]) -> str:
        """Generate enhanced product description"""
        
        desc_parts = [title]
        
        # Add size information
        if size and unit:
            desc_parts.append(f"{size}{unit}")
        
        # Add category if not already in title
        if category and category.lower() not in title.lower():
            if category in ["Beverages", "Food"]:
                desc_parts.append(category.lower().rstrip('s'))
        
        # Add detection confidence info for debugging
        if detected_brand:
            confidence = detected_brand.get('confidence', 0)
            if confidence > 0.8:
                desc_parts.append("(high confidence)")
        
        return " ".join(desc_parts)


def create_add_product_vision_tool():
    """Create the enhanced product vision analysis tool"""
    
    processor = ProductVisionProcessor()
    
    def add_product_vision_tool(
        image_data: str,
        is_url: bool,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Analyze a product image using enhanced Vision API with store context
        
        Args:
            image_data (str): Base64 encoded image data or image URL
            is_url (bool): Whether image_data is a URL (True) or base64 string (False)
            user_id (str): User ID for store context
            
        Returns:
            Dict[str, Any]: Dictionary containing extracted product information
        """
        
        try:
            logger.info(f"🔍 Processing product image for user: {user_id}")
            
            # Validate input
            if not image_data:
                return {
                    "success": False,
                    "error": "No image data provided"
                }
            
            # Process the image with enhanced detection
            result = processor.process_image(image_data, is_url, user_id)
            
            if result.get("success"):
                product = result.get("product", {})
                
                # Format response structure to match expected format
                response = {
                    "success": True,
                    "data": {
                        "product": {
                            "title": product.get("title", ""),
                            "brand": product.get("brand", ""),
                            "size": product.get("size", ""),
                            "unit": product.get("unit", ""),
                            "category": product.get("category", ""),
                            "subcategory": product.get("subcategory", ""),
                            "description": product.get("description", ""),
                            "confidence": product.get("confidence", 0.0),
                            "detection_method": product.get("detection_method", "unknown")
                        }
                    }
                }
                
                logger.info(f"✅ Successfully extracted: {product.get('title')} | Brand: {product.get('brand')} | Size: {product.get('size')}{product.get('unit')}")
                
                return response
            else:
                error_msg = result.get("error", "Unknown error")
                logger.error(f"❌ Image processing failed: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }
                
        except Exception as e:
            logger.error(f"❌ Error in add_product_vision_tool: {str(e)}")
            return {
                "success": False,
                "error": f"Tool error: {str(e)}"
            }
    
    # Create the FunctionTool
    return FunctionTool(func=add_product_vision_tool)
