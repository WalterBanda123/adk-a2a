import os
import sys
import json
import base64
import asyncio
import logging
import re
from typing import Dict, Any, List, Tuple, Union
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
    """High-performance product image processor using Google Cloud Vision API"""
    
    def __init__(self):
        self.client = None
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
        
        # Zimbabwe-specific product mappings for better accuracy
        self.zimbabwe_brands = {
            'delta', 'lobels', 'blue ribbon', 'mazoe', 'tanganda', 'cairns',
            'dairibord', 'tregers', 'bakers inn', 'proton', 'willowton',
            'colgate', 'surf', 'rama', 'gloria', 'cremora', 'jungle oats',
            'cascade', 'charhons', 'lyons' # Added more specific brands
        }
        
        self.category_keywords = {
            'beverages': {
                'soft drinks': ['coca', 'pepsi', 'fanta', 'sprite', 'sparletta', 'mirinda', 'soda', 'cola'], # Added sparletta, mirinda
                'water': ['water', 'aqua', 'spring', 'still', 'sparkling'],
                'beer': ['beer', 'lager', 'castle', 'lion', 'zambezi', 'bohlers'],
                'juices': ['juice', 'mazoe', 'fresh', 'fruit', 'orange', 'apple', 'crush', 'minute maid'] # Added crush, minute maid
            },
            'food': {
                'groceries': ['maize', 'meal', 'flour', 'rice', 'beans', 'sugar', 'salt'],
                'snacks': ['chips', 'biscuits', 'cookies', 'nuts', 'chocolates'],
                'dairy': ['milk', 'cheese', 'butter', 'yogurt', 'cream'],
                'cooking': ['oil', 'cooking', 'margarine', 'spices']
            },
            'household': {
                'cleaning': ['detergent', 'soap', 'bleach', 'polish', 'cleaner'],
                'personal care': ['shampoo', 'toothpaste', 'lotion', 'deodorant']
            }
        }
        
        self.size_patterns = [
            r'(\d+(?:\.\d+)?)\s*(ml|l|litre|liter)',
            r'(\d+(?:\.\d+)?)\s*(kg|g|gram|kilogram)',
            r'(\d+(?:\.\d+)?)\s*(oz|ounce)',
            r'(\d+)\s*x\s*(\d+(?:\.\d+)?)\s*(ml|g|kg)',
            r'(\d+(?:\.\d+)?)\s*(pack|piece|pc)',
            r'(\d+)\s*(litres?|liters?)',
            r'(\d+)\s*ml',
            r'(\d+)\s*L',
            r'(\d+(?:\.\d+)?)\s*(?:litres?|liters?)',
            r'(\d+(?:\.\d+)?)\s*(?:grams?|grammes?)',
            r'(\d+(?:\.\d+)?)\s*(?:kilos?|kilograms?)'
        ]
    
    async def process_image(self, image_data: str, is_url: bool) -> Dict[str, Any]:
        """Process product image and extract structured information"""
        if not self.client:
            return {
                "success": False,
                "error": "Google Cloud Vision API not available"
            }
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            # Prepare image for Vision API
            image = await self._prepare_image(image_data, is_url)
            if not image:
                return {
                    "success": False,
                    "error": "Failed to process image data"
                }
            
            # Run Vision API operations concurrently for speed
            tasks = [
                self._detect_labels(image),
                self._detect_text(image),
            ]
            
            # Execute all detection tasks concurrently with proper error handling
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Safely extract results
            labels_result: List[Dict] = []
            text_result: List[Dict] = []
            
            if len(results) > 0:
                if isinstance(results[0], list):
                    labels_result = results[0]
                elif not isinstance(results[0], Exception):
                    labels_result = []
                    
            if len(results) > 1:
                if isinstance(results[1], list):
                    text_result = results[1]
                elif not isinstance(results[1], Exception):
                    text_result = []
            
            # If primary methods don't yield good results, try web detection as fallback
            web_result: List[Dict] = []
            if not labels_result and not text_result:
                try:
                    web_result = await self._detect_web_entities(image)
                except Exception as e:
                    logger.warning(f"Web detection failed: {e}")
            
            # Parse and normalize the extracted data
            product_info = self._parse_vision_results(labels_result, text_result, web_result)
            
            processing_time = asyncio.get_event_loop().time() - start_time
            product_info["processing_time"] = round(processing_time, 2)
            
            logger.info(f"Image processed in {processing_time:.2f} seconds")
            
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
    
    async def _prepare_image(self, image_data: str, is_url: bool):
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
    
    async def _detect_labels(self, image) -> List[Dict]:
        """Detect labels/objects in the image"""
        if not self.client:
            return []
            
        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            
            # Use the correct API method signature
            def detect_labels_sync():
                # Use getattr to avoid type checker issues
                if hasattr(self.client, 'label_detection'):
                    return getattr(self.client, 'label_detection')(image=image)
                else:
                    return None
            
            response = await loop.run_in_executor(None, detect_labels_sync)
            
            labels = []
            if response and hasattr(response, 'label_annotations'):
                for label in response.label_annotations:
                    labels.append({
                        'description': label.description.lower(),
                        'score': label.score
                    })
            
            return labels
            
        except Exception as e:
            logger.error(f"Label detection failed: {e}")
            return []
    
    async def _detect_text(self, image) -> List[Dict]:
        """Detect and extract text from the image"""
        if not self.client:
            return []
            
        try:
            loop = asyncio.get_event_loop()
            
            def detect_text_sync():
                # Use getattr to avoid type checker issues
                if hasattr(self.client, 'text_detection'):
                    return getattr(self.client, 'text_detection')(image=image)
                else:
                    return None
            
            response = await loop.run_in_executor(None, detect_text_sync)
            
            texts = []
            if response and hasattr(response, 'text_annotations'):
                for text in response.text_annotations:
                    texts.append({
                        'description': text.description,
                        'confidence': getattr(text, 'confidence', 0.9)
                    })
            
            return texts
            
        except Exception as e:
            logger.error(f"Text detection failed: {e}")
            return []
    
    async def _detect_web_entities(self, image) -> List[Dict]:
        """Fallback: detect web entities for product identification"""
        if not self.client:
            return []
            
        try:
            loop = asyncio.get_event_loop()
            
            def detect_web_sync():
                # Use getattr to avoid type checker issues
                if hasattr(self.client, 'web_detection'):
                    return getattr(self.client, 'web_detection')(image=image)
                else:
                    return None
            
            response = await loop.run_in_executor(None, detect_web_sync)
            
            entities = []
            if response and hasattr(response, 'web_detection') and response.web_detection.web_entities:
                for entity in response.web_detection.web_entities:
                    if entity.description and entity.score > 0.3:
                        entities.append({
                            'description': entity.description.lower(),
                            'score': entity.score
                        })
            
            return entities
            
        except Exception as e:
            logger.error(f"Web detection failed: {e}")
            return []
    
    def _parse_vision_results(self, labels: List[Dict], texts: List[Dict], web_entities: List[Dict]) -> Dict[str, Any]:
        """Parse and normalize Vision API results into product information"""
        
        # Extract all text content
        all_text = ""
        if texts:
            all_text = " ".join([t.get('description', '') for t in texts]).lower()
        
        # Debug logging to see what we detected
        logger.info(f"🔍 DEBUG - Detected text: {all_text[:200]}...")
        logger.info(f"🔍 DEBUG - Labels: {[l.get('description', '') for l in labels[:5]]}")
        
        # Combine all detection sources
        all_labels = [l.get('description', '') for l in labels]
        all_web = [w.get('description', '') for w in web_entities]
        all_descriptions = all_labels + all_web
        
        # Extract product information
        title = self._extract_title(all_descriptions, all_text)
        size, unit = self._extract_size_and_unit(all_text)
        category, subcategory = self._extract_category(all_descriptions, all_text)
        description = self._generate_description(title, size, unit, category)
        
        logger.info(f"🎯 DEBUG - Extracted title: {title}")
        
        return {
            "title": title,
            "size": size,
            "unit": unit,
            "category": category,
            "subcategory": subcategory,
            "description": description,
            "confidence": self._calculate_confidence(labels, texts, web_entities)
        }
    
    def _extract_title(self, descriptions: List[str], text: str) -> str:
        """Extract the main product title/name"""
        
        lower_text = text.lower()
        text_lines = [line.strip() for line in lower_text.split('\n') if line.strip()]

        # Priority 1: Look for specific brand + product name combinations
        # Example: "Mazoe Orange Crush"
        for brand in self.zimbabwe_brands:
            if brand in lower_text:
                # Search for [Brand] [Flavor/Type] [Variant/Name]
                # e.g. Mazoe Orange Crush, Delta Blue, Lobels Lemon Creams
                # More sophisticated pattern matching could be added here if needed
                # For now, we check if brand and other keywords appear close by
                
                # Check for Mazoe specific patterns
                if brand == 'mazoe':
                    if 'orange' in lower_text and 'crush' in lower_text:
                        return "Mazoe Orange Crush"
                    if 'raspberry' in lower_text and 'crush' in lower_text: # Example for other flavors
                        return "Mazoe Raspberry Crush"
                    if 'orange' in lower_text:
                        return "Mazoe Orange"
                
                # General approach: find the line containing the brand and return it if it seems descriptive
                for line in text_lines:
                    if brand in line:
                        # Attempt to find a more complete name on this line
                        # This is a simple heuristic, could be improved
                        potential_title = line
                        # Remove very common words that might dilute the title
                        common_fillers = ['product of', 'manufactured by', 'ingredients']
                        for filler in common_fillers:
                            potential_title = potential_title.replace(filler, '')
                        
                        # If the line is reasonably long and contains the brand, it might be the title
                        if len(potential_title.split()) > 1 and len(potential_title.split()) < 7: # Avoid very short/long lines
                            return potential_title.strip().title()

        # Fallback to existing brand detection
        text_words = lower_text.split()
        detected_brands = []
        
        for brand in self.zimbabwe_brands:
            if brand in text.lower():
                detected_brands.append(brand)
        
        # If we found brands in text, try to construct a proper product name
        if detected_brands:
            # Look for flavor/variant keywords in text
            flavor_keywords = ['raspberry', 'orange', 'apple', 'chocolate', 'vanilla', 'strawberry', 'mango', 'pineapple']
            detected_flavors = [flavor for flavor in flavor_keywords if flavor in text.lower()]
            
            if detected_flavors:
                # Combine brand and flavor
                primary_brand = detected_brands[0].title()
                primary_flavor = detected_flavors[0].title()
                return f"{primary_brand} {primary_flavor}"
            else:
                # Just return the brand
                return detected_brands[0].title()
        
        # Look for complete product names in OCR text
        # Split text into lines and look for meaningful product names
        text_lines = text.split('\n')
        for line in text_lines:
            line = line.strip()
            if len(line) > 3 and not line.isdigit():
                # Check if this line contains a brand name
                for brand in self.zimbabwe_brands:
                    if brand in line.lower():
                        return line.title()
        
        # Look for product names in longer text segments
        for line in text_lines:
            line = line.strip()
            # Look for lines that might be product names (contain letters, not just numbers/symbols)
            if len(line) > 5 and any(c.isalpha() for c in line):
                # Skip obvious non-product text
                skip_words = ['ingredients', 'nutrition', 'www', 'http', 'ltd', 'company']
                if not any(skip in line.lower() for skip in skip_words):
                    return line.title()
        
        # Look for known Zimbabwe brands in descriptions
        for desc in descriptions:
            for brand in self.zimbabwe_brands:
                if brand in desc.lower():
                    # Try to get more specific product name
                    brand_products = [d for d in descriptions if brand in d.lower()]
                    if brand_products:
                        # Return the most specific one
                        return max(brand_products, key=len).title()
        
        # Look for beverage/food product indicators, but avoid generic terms
        food_indicators = ['drink', 'beverage', 'food', 'snack', 'juice']  # Removed 'bottle', 'can', 'packet'
        food_products = [d for d in descriptions if any(indicator in d.lower() for indicator in food_indicators)]
        
        if food_products:
            # Return the most descriptive food product
            return max(food_products, key=len).title()
        
        # Fallback: return the most descriptive label that's not too generic
        generic_terms = ['bottle', 'plastic', 'container', 'package', 'product', 'item']
        specific_descriptions = [d for d in descriptions if not any(generic in d.lower() for generic in generic_terms)]
        
        if specific_descriptions:
            return max(specific_descriptions, key=len).title()
        
        # Last resort: extract meaningful words from text
        words = text.split()
        meaningful_words = []
        for word in words:
            word = word.strip('.,!?()[]{}')
            if (len(word) > 3 and 
                word.isalpha() and 
                not word.lower() in ['the', 'and', 'for', 'with', 'from', 'this', 'that']):
                meaningful_words.append(word)
        
        if meaningful_words:
            # Return the first meaningful word, capitalized
            return meaningful_words[0].title()
        
        return "Unknown Product"
    
    def _extract_size_and_unit(self, text: str) -> Tuple[str, str]:
        """Extract size and unit from text"""
        
        # Improved regex to better capture variations like 2L, 2LITRES etc.
        # Added case for 'x' packs e.g. 6x300ml
        # Prioritize patterns that are more specific or common for Zim products
        priority_patterns = [
            r'(\d+(?:\.\d+)?)\s*(LITRES?|LITERS?|L)\b', # 2L, 2LITRES, 2 LITERS
            r'(\d+(?:\.\d+)?)\s*(ML)\b', # 500ML
            r'(\d+(?:\.\d+)?)\s*(KG|KILOGRAMS?)\b', # 2KG, 2 KILOGRAMS
            r'(\d+(?:\.\d+)?)\s*(G|GRAMS?|GRAMMES?)\b', # 500G, 500 GRAMS
            r'(\d+)\s*x\s*(\d+(?:\.\d+)?)\s*(ML|G|KG)\b' # 6x300ML, 4x100G
        ]
        
        # Combine with existing patterns, giving priority to the new ones
        # Ensure self.size_patterns is defined in __init__ if this is the first modification point for it
        # For this edit, assuming self.size_patterns exists and we are prepending to it.
        # If self.size_patterns was not previously defined, it should be initialized in __init__.
        # For now, let's assume it exists and we are adding to it.
        # To be safe, we can define it here if it might not exist, or ensure it's in __init__
        # For this specific request, we will just use the priority_patterns and then the existing ones.

        all_patterns = priority_patterns + getattr(self, 'size_patterns', [])

        for pattern in all_patterns:
            # Using re.IGNORECASE for flexibility
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                match = matches[0]
                if isinstance(match, tuple) and len(match) >= 2:
                    if 'x' in pattern: # Handle pack like "6x300ML"
                        size = f"{match[0]}x{match[1]}" # e.g. "6x300"
                        unit = match[2].lower()
                    else:
                        size = match[0]
                        unit = match[1].lower()
                    
                    # Normalize units
                    unit_mappings = {
                        'l': 'L', 'litre': 'L', 'liters': 'L', 'litres': 'L',
                        'ml': 'ml',
                        'kg': 'kg', 'kilogram': 'kg', 'kilograms': 'kg',
                        'g': 'g', 'gram': 'g', 'grams': 'g', 'grammes': 'g',
                        'oz': 'oz', 'ounce': 'oz',
                        'pack': 'pack', 'piece': 'piece', 'pc': 'piece'
                    }
                    
                    normalized_unit = unit_mappings.get(unit, unit)
                    return str(size), str(normalized_unit)
        
        return "", ""
    
    def _extract_category(self, descriptions: List[str], text: str) -> Tuple[str, str]:
        """Extract category and subcategory"""
        
        all_content = " ".join(descriptions + [text]).lower()
        
        for category, subcats in self.category_keywords.items():
            for subcat, keywords in subcats.items():
                if any(keyword in all_content for keyword in keywords):
                    return category.title(), subcat.title().replace('_', ' ')
        
        # Fallback categorization based on common labels
        if any(term in all_content for term in ['drink', 'beverage', 'bottle', 'can']):
            return "Beverages", "Soft Drinks"
        elif any(term in all_content for term in ['food', 'snack', 'packet']):
            return "Food", "Groceries"
        elif any(term in all_content for term in ['soap', 'detergent', 'cleaner']):
            return "Household", "Cleaning"
        
        return "General", "Miscellaneous"
    
    def _generate_description(self, title: str, size: str, unit: str, category: str) -> str:
        """Generate a descriptive product description"""
        
        desc_parts = [title]
        
        if size and unit:
            desc_parts.append(f"{size}{unit}")
        
        # Add category context if it adds value
        if category.lower() not in title.lower():
            if category in ["Beverages", "Food"]:
                desc_parts.append(category.lower().rstrip('s'))
        
        return " ".join(desc_parts)
    
    def _calculate_confidence(self, labels: List[Dict], texts: List[Dict], web_entities: List[Dict]) -> float:
        """Calculate overall confidence score"""
        
        total_score = 0.0
        count = 0
        
        # Label confidence
        for label in labels:
            total_score += label.get('score', 0.0)
            count += 1
        
        # Text confidence
        for text in texts:
            total_score += text.get('confidence', 0.8)
            count += 1
        
        # Web entity confidence
        for entity in web_entities:
            total_score += entity.get('score', 0.0)
            count += 1
        
        return round(total_score / max(count, 1), 2)


def create_add_product_vision_tool():
    """Create the product vision analysis tool"""
    
    processor = ProductVisionProcessor()
    
    async def add_product_vision_tool(
        image_data: str,
        is_url: bool,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Analyze a product image and extract structured product information
        
        Args:
            image_data (str): Base64 encoded image data or image URL
            is_url (bool): Whether image_data is a URL (True) or base64 string (False)
            user_id (str): User ID for logging purposes
            
        Returns:
            Dict[str, Any]: Dictionary containing extracted product information
        """
        
        try:
            logger.info(f"Processing product image for user: {user_id}")
            
            # Validate input
            if not image_data:
                return {
                    "success": False,
                    "error": "No image data provided"
                }
            
            # Process the image
            result = await processor.process_image(image_data, is_url)
            
            if result.get("success"):
                product = result.get("product", {})
                
                # Format response for easy consumption
                response = {
                    "success": True,
                    "title": product.get("title", ""),
                    "brand": product.get("brand", ""),
                    "size": product.get("size", ""),
                    "unit": product.get("unit", ""),
                    "category": product.get("category", ""),
                    "subcategory": product.get("subcategory", ""),
                    "description": product.get("description", ""),
                    "confidence": product.get("confidence", 0.0),
                    "processing_time": product.get("processing_time", 0.0)
                }
                
                logger.info(f"Successfully extracted product: {product.get('title')} "
                           f"in {product.get('processing_time', 0):.2f}s")
                
                return response
            else:
                error_msg = result.get("error", "Unknown error")
                logger.error(f"Image processing failed: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }
                
        except Exception as e:
            logger.error(f"Error in add_product_vision_tool: {str(e)}")
            return {
                "success": False,
                "error": f"Tool error: {str(e)}"
            }
    
    # Create the FunctionTool
    return FunctionTool(func=add_product_vision_tool)
