"""
Helper functions for Product Transaction Agent
Handles image processing, AutoML predictions, product lookups, and transaction parsing
"""
import os
import sys
import re
import json
import base64
import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import requests
from io import BytesIO

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

# Import existing services
from common.product_service import ProductService
from common.user_service import UserService

# Import AutoML and vision components
try:
    from google.cloud import automl
    from google.cloud import vision
    from google.cloud import storage
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    automl = None
    vision = None
    storage = None
    GOOGLE_CLOUD_AVAILABLE = False

logger = logging.getLogger(__name__)

class ProductTransactionHelper:
    """Helper class for product transaction operations"""
    
    def __init__(self):
        self.product_service = ProductService()
        self.user_service = UserService()
        self.tax_rate = 0.05  # 5% tax rate
        
        # Initialize Google Cloud clients if available
        if GOOGLE_CLOUD_AVAILABLE and automl and vision and storage:
            try:
                self.automl_client = automl.PredictionServiceClient()
                self.vision_client = vision.ImageAnnotatorClient()
                self.storage_client = storage.Client()
                logger.info("Google Cloud clients initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Google Cloud clients: {e}")
                self.automl_client = None
                self.vision_client = None
                self.storage_client = None
        else:
            logger.warning("Google Cloud libraries not available")
            self.automl_client = None
            self.vision_client = None
            self.storage_client = None

    # =====================
    # Image Processing Functions
    # =====================
    
    async def preprocess_image(self, image_data: str, is_url: bool = False) -> Optional[bytes]:
        """Preprocess image data for AutoML prediction"""
        try:
            if is_url:
                response = requests.get(image_data, timeout=10)
                response.raise_for_status()
                return response.content
            else:
                if image_data.startswith('data:image'):
                    image_data = image_data.split(',')[1]
                return base64.b64decode(image_data)
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return None

    async def call_automl_model(self, image_bytes: bytes, user_id: str) -> Dict[str, Any]:
        """Call AutoML model for product prediction"""
        try:
            if not self.automl_client or not automl:
                return await self._fallback_vision_detection(image_bytes)
            
            project_id = "deve-01"
            location = "us-central1"
            model_id = "IOD1428734374374039552"  
            
            model_path = self.automl_client.model_path(project_id, location, model_id)
            
            payload = automl.ExamplePayload(image=automl.Image(image_bytes=image_bytes))
            
            response = self.automl_client.predict(
                name=model_path,
                payload=payload,
                params={"score_threshold": "0.6"}
            )
            
            # Parse AutoML response
            return self._parse_automl_response(response)
            
        except Exception as e:
            logger.error(f"AutoML prediction failed: {e}")
            return await self._fallback_vision_detection(image_bytes)

    def _parse_automl_response(self, response) -> Dict[str, Any]:
        """Parse AutoML response into structured product data"""
        result = {
            "success": True,
            "title": "Unknown Product",
            "brand": "",
            "size": "",
            "unit": "",
            "category": "General",
            "confidence": 0.0,
            "sku": None,
            "detection_method": "automl"
        }
        
        if not response.payload:
            result["success"] = False
            return result
        
        # Process detected objects
        brand_found = False
        product_found = False
        size_found = False
        max_confidence = 0.0
        
        for prediction in response.payload:
            label = prediction.display_name.lower()
            confidence = prediction.image_object_detection.score
            max_confidence = max(max_confidence, confidence)
            
            if confidence > 0.6:  # High confidence threshold
                if "brand" in label and not brand_found:
                    result["brand"] = prediction.display_name
                    brand_found = True
                elif "product" in label and not product_found:
                    result["title"] = prediction.display_name
                    product_found = True
                elif "size" in label and not size_found:
                    result["size"] = prediction.display_name
                    size_found = True
                elif "category" in label:
                    result["category"] = prediction.display_name
        
        result["confidence"] = min(0.95, max(0.6, max_confidence))
        
        # Generate SKU if we have enough information
        if brand_found and product_found:
            result["sku"] = self._generate_sku(result["brand"], result["title"], result["size"])
        
        return result

    async def _fallback_vision_detection(self, image_bytes: bytes) -> Dict[str, Any]:
        """Fallback to Google Vision API for product detection"""
        try:
            if not self.vision_client or not vision:
                return {
                    "success": False,
                    "error": "No vision services available",
                    "detection_method": "none"
                }
            
            image = vision.Image(content=image_bytes)
            
            # Text detection
            try:
                # Using the correct Google Vision API method
                response = self.vision_client.annotate_image({
                    'image': image,
                    'features': [{'type_': vision.Feature.Type.TEXT_DETECTION}]
                })
                texts = response.text_annotations if hasattr(response, 'text_annotations') and response.text_annotations else []
            except Exception as e:
                logger.warning(f"Text detection failed: {e}")
                texts = []
            
            # Object detection - using a simpler approach
            result = {
                "success": True,
                "title": "Product Detected",
                "brand": "",
                "size": "",
                "unit": "",
                "category": "General",
                "confidence": 0.7,
                "sku": None,
                "detection_method": "vision_api"
            }
            
            # Extract text information
            if texts:
                full_text = texts[0].description.lower()
                result["title"] = self._extract_product_name(full_text)
                result["brand"] = self._extract_brand(full_text)
                result["size"] = self._extract_size(full_text)
            
            return result
            
        except Exception as e:
            logger.error(f"Vision API fallback failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "detection_method": "failed"
            }

    def _generate_sku(self, brand: str, product: str, size: str = "") -> str:
        """Generate a SKU from product information"""
        # Simple SKU generation logic
        brand_code = ''.join(brand.split()[:2])[:4].upper()
        product_code = ''.join(product.split()[:2])[:4].upper()
        size_code = ''.join(size.split()[:1])[:2].upper() if size else "00"
        
        return f"{brand_code}{product_code}{size_code}"

    def _extract_product_name(self, text: str) -> str:
        """Extract product name from detected text"""
        # Basic product name extraction
        words = text.split()
        if len(words) >= 2:
            return ' '.join(words[:3]).title()
        return "Unknown Product"

    def _extract_brand(self, text: str) -> str:
        """Extract brand from detected text"""
        # Common brand patterns for Zimbabwe
        zimbabwe_brands = [
            'hullets', 'mazoe', 'olivine', 'lobels', 'gold leaf', 
            'tanganda', 'coca cola', 'fanta', 'sprite', 'dairibord'
        ]
        
        text_lower = text.lower()
        for brand in zimbabwe_brands:
            if brand in text_lower:
                return brand.title()
        
        return ""

    def _extract_size(self, text: str) -> str:
        """Extract size information from text"""
        # Size pattern matching
        size_patterns = [
            r'(\d+(?:\.\d+)?)\s*(kg|g|l|ml|litre|gram|kilogram)',
            r'(\d+)\s*(pack|piece|bottle|can|bag)'
        ]
        
        for pattern in size_patterns:
            match = re.search(pattern, text.lower())
            if match:
                return f"{match.group(1)}{match.group(2)}"
        
        return ""

    async def lookup_product_by_sku(self, sku: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Look up product metadata by SKU"""
        try:
            # Query products collection for SKU
            if not self.product_service.db:
                return None
            
            products_ref = self.product_service.db.collection('products').where('sku', '==', sku)
            products = products_ref.get()
            
            for product in products:
                product_data = product.to_dict()
                if product_data and product_data.get('store_owner_id') == user_id:
                    product_data['id'] = product.id
                    return product_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error looking up product by SKU {sku}: {e}")
            return None

    async def upload_to_gcs(self, image_bytes: bytes, user_id: str, filename: Optional[str] = None) -> Optional[str]:
        """Upload image to Google Cloud Storage and return public URL"""
        try:
            if not self.storage_client:
                logger.warning("GCS client not available")
                return None
            
            # Generate filename if not provided
            if not filename:
                timestamp = int(datetime.now().timestamp())
                filename = f"products/{user_id}/{timestamp}.jpg"
            
            # Upload to bucket
            bucket_name = "deve-01.appspot.com"  # Firebase storage bucket
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(filename)
            
            blob.upload_from_string(image_bytes, content_type='image/jpeg')
            blob.make_public()
            
            return blob.public_url
            
        except Exception as e:
            logger.error(f"Error uploading to GCS: {e}")
            return None

    # =====================
    # Transaction Processing Functions
    # =====================

    async def parse_cart_message(self, message: str) -> Dict[str, Any]:
        """Parse free-form transaction message into structured items with enhanced NLP"""
        try:
            items = []
            total_items = 0
            estimated_total = 0.0
            
            logger.info(f"Parsing transaction message: '{message}'")
            
            # Clean and normalize the message
            message_cleaned = self._clean_transaction_message(message)
            
            # Try multiple parsing strategies
            parsing_strategies = [
                self._parse_structured_format,    # "2 bread @1.50, 1 milk @0.75"
                self._parse_simple_format,        # "2 bread, 1 milk"
                self._parse_natural_language,     # "sold 2 apples by 3 dollars each"
                self._parse_conversational,       # "I sold some bread and milk today"
            ]
            
            parsed_items = []
            best_confidence = 0.0
            
            for strategy in parsing_strategies:
                try:
                    result = strategy(message_cleaned)
                    if result.get("items") and result.get("confidence", 0) > best_confidence:
                        parsed_items = result["items"]
                        best_confidence = result["confidence"]
                        logger.info(f"Best parsing strategy found {len(parsed_items)} items with confidence {best_confidence}")
                        if best_confidence > 0.8:  # High confidence, use this result
                            break
                except Exception as e:
                    logger.warning(f"Parsing strategy failed: {e}")
                    continue
            
            # If no items found, try fallback parsing
            if not parsed_items:
                logger.warning("All parsing strategies failed, trying fallback")
                parsed_items = self._fallback_parsing(message_cleaned)
            
            # Process the parsed items
            for item in parsed_items:
                if item and item.get("name") and item.get("quantity"):
                    items.append(item)
                    total_items += item["quantity"]
                    if item.get("line_total"):
                        estimated_total += item["line_total"]
            
            success = len(items) > 0
            confidence = best_confidence if success else 0.0
            
            result = {
                "success": success,
                "items": items,
                "total_items": total_items,
                "estimated_total": estimated_total,
                "parsing_confidence": confidence,
                "raw_text": message,
                "needs_price_lookup": any(item.get("unit_price") is None for item in items),
                "parsing_method": "enhanced_nlp"
            }
            
            if not success:
                result["error"] = f"Could not extract any products from message: '{message}'"
                result["suggestions"] = [
                    "Try formats like: '2 bread, 1 milk' or '2 bread @1.50, 1 milk @0.75'",
                    "Include quantity and product name: 'sold 3 apples'",
                    "List items separated by commas: 'bread, milk, eggs'"
                ]
            
            logger.info(f"Final parsing result: {len(items)} items, confidence: {confidence}")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing cart message: {e}")
            return {
                "success": False,
                "error": str(e),
                "items": [],
                "total_items": 0,
                "estimated_total": 0.0,
                "parsing_confidence": 0.0,
                "raw_text": message
            }
    
    def _clean_transaction_message(self, message: str) -> str:
        """Clean and normalize the transaction message"""
        # Remove extra whitespace and newlines
        cleaned = message.strip().replace('\n', ' ')
        
        # Normalize common variations
        replacements = {
            ' by ': ' @ ',  # "apples by 3" -> "apples @ 3"
            ' for ': ' @ ', # "apples for 3" -> "apples @ 3"
            ' at ': ' @ ',  # "apples at 3" -> "apples @ 3"
            ' each': '',    # Remove "each"
            'sold ': '',    # Remove "sold"
            'bought ': '',  # Remove "bought"
            'purchase ': '',# Remove "purchase"
        }
        
        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)
        
        return cleaned
    
    def _parse_structured_format(self, message: str) -> Dict[str, Any]:
        """Parse structured format: '2 bread @1.50, 1 milk @0.75'"""
        import re
        
        items = []
        
        # Enhanced patterns for parsing (in order of preference)
        patterns = [
            r'(\d+)\s*x?\s*([^@,]+?)@\s*(\d+(?:\.\d+)?)',  # "2 bread @1.25" or "2x bread @1.25"
            r'(\d+)\s+([^@,]+?)\s+@\s*(\d+(?:\.\d+)?)',    # "2 bread @ 1.25"
            r'(\d+)\s*([^@,]+?)@(\d+(?:\.\d+)?)',          # "2bread@1.25"
        ]
        
        # Split by commas and process each item
        raw_items = [item.strip() for item in message.split(',') if item.strip()]
        parsed_count = 0
        
        for raw_item in raw_items:
            for pattern in patterns:
                match = re.search(pattern, raw_item, re.IGNORECASE)
                if match:
                    try:
                        quantity = int(match.group(1))
                        name = match.group(2).strip()
                        unit_price = float(match.group(3))
                        line_total = quantity * unit_price
                        
                        items.append({
                            "name": name,
                            "quantity": quantity,
                            "unit_price": unit_price,
                            "line_total": line_total,
                            "raw_text": raw_item,
                            "price_source": "provided"
                        })
                        parsed_count += 1
                        break
                    except (ValueError, IndexError):
                        continue
        
        confidence = parsed_count / len(raw_items) if raw_items else 0.0
        return {"items": items, "confidence": confidence}
    
    def _parse_simple_format(self, message: str) -> Dict[str, Any]:
        """Parse simple format: '2 bread, 1 milk'"""
        import re
        
        items = []
        
        # Patterns for simple format (no prices)
        patterns = [
            r'(\d+)\s*x?\s*([^,@]+)',  # "2 bread" or "2x bread"
            r'(\d+)\s+([^,@]+)',       # "2 bread"
        ]
        
        # Split by commas and process each item
        raw_items = [item.strip() for item in message.split(',') if item.strip()]
        parsed_count = 0
        
        for raw_item in raw_items:
            for pattern in patterns:
                match = re.search(pattern, raw_item, re.IGNORECASE)
                if match:
                    try:
                        quantity = int(match.group(1))
                        name = match.group(2).strip()
                        
                        items.append({
                            "name": name,
                            "quantity": quantity,
                            "unit_price": None,  # To be fetched from database
                            "line_total": None,  # To be calculated after price lookup
                            "raw_text": raw_item,
                            "price_source": "database"
                        })
                        parsed_count += 1
                        break
                    except (ValueError, IndexError):
                        continue
        
        confidence = parsed_count / len(raw_items) if raw_items else 0.0
        return {"items": items, "confidence": confidence}
    
    def _parse_natural_language(self, message: str) -> Dict[str, Any]:
        """Parse natural language: 'sold 2 apples by 3 dollars each'"""
        import re
        
        items = []
        
        # Natural language patterns
        patterns = [
            r'(\d+)\s+(\w+(?:\s+\w+)?)\s+@\s*(\d+(?:\.\d+)?)',  # "2 apples @ 3.50"
            r'(\d+)\s+(\w+(?:\s+\w+)?)\s+(?:by|for|at)\s+(\d+(?:\.\d+)?)',  # "2 apples by 3.50"
            r'(\d+)\s+(\w+(?:\s+\w+)?)',  # "2 apples" (no price)
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                try:
                    quantity = int(match.group(1))
                    name = match.group(2).strip()
                    
                    # Check if price was captured
                    if len(match.groups()) >= 3 and match.group(3):
                        unit_price = float(match.group(3))
                        line_total = quantity * unit_price
                        price_source = "provided"
                    else:
                        unit_price = None
                        line_total = None
                        price_source = "database"
                    
                    items.append({
                        "name": name,
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "line_total": line_total,
                        "raw_text": match.group(0),
                        "price_source": price_source
                    })
                except (ValueError, IndexError):
                    continue
        
        confidence = 0.7 if items else 0.0
        return {"items": items, "confidence": confidence}
    
    def _parse_conversational(self, message: str) -> Dict[str, Any]:
        """Parse conversational format: 'I sold some bread and milk today'"""
        import re
        
        items = []
        
        # Look for product mentions without explicit quantities
        product_keywords = [
            'bread', 'milk', 'eggs', 'rice', 'sugar', 'oil', 'tea', 'coffee',
            'apple', 'apples', 'banana', 'bananas', 'orange', 'oranges',
            'tomato', 'tomatoes', 'onion', 'onions', 'potato', 'potatoes',
            'soap', 'salt', 'flour', 'mealie', 'maize'
        ]
        
        # Extract quantity if present, otherwise assume 1
        quantity_pattern = r'(\d+)\s+(\w+)'
        matches = re.finditer(quantity_pattern, message, re.IGNORECASE)
        
        found_items = []
        for match in matches:
            try:
                quantity = int(match.group(1))
                potential_product = match.group(2).lower();
                
                if potential_product in product_keywords:
                    found_items.append({
                        "name": potential_product,
                        "quantity": quantity,
                        "unit_price": None,
                        "line_total": None,
                        "raw_text": match.group(0),
                        "price_source": "database"
                    })
            except (ValueError, IndexError):
                continue
        
        # If no quantities found, look for product names and assume quantity 1
        if not found_items:
            for keyword in product_keywords:
                if keyword in message.lower():
                    found_items.append({
                        "name": keyword,
                        "quantity": 1,
                        "unit_price": None,
                        "line_total": None,
                        "raw_text": keyword,
                        "price_source": "database"
                    })
        
        confidence = 0.5 if found_items else 0.0
        return {"items": found_items, "confidence": confidence}
    
    def _fallback_parsing(self, message: str) -> List[Dict[str, Any]]:
        """Fallback parsing when all other methods fail"""
        # Extract any numbers and words, make best guesses
        import re
        
        # Look for any number followed by a word
        pattern = r'(\d+)\s*(\w+(?:\s+\w+)?)'
        matches = re.finditer(pattern, message, re.IGNORECASE)
        
        items = []
        for match in matches:
            try:
                quantity = int(match.group(1))
                name = match.group(2).strip()
                
                # Skip if the "name" looks like a price or irrelevant word
                if name.lower() in ['dollars', 'usd', 'cents', 'price', 'total', 'each']:
                    continue
                
                items.append({
                    "name": name,
                    "quantity": quantity,
                    "unit_price": None,
                    "line_total": None,
                    "raw_text": match.group(0),
                    "price_source": "database"
                })
            except (ValueError, IndexError):
                continue
        
        return items

    async def lookup_product_by_name(self, name: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Look up product by name with enhanced fuzzy matching"""
        try:
            if not self.product_service.db:
                return None
            
            # Get all user's products
            products = await self.product_service.get_store_products(user_id)
            if not products:
                return None
            
            # Clean and normalize the input name
            name_cleaned = self._normalize_product_name(name)
            best_match = None
            best_score = 0.0
            
            for product in products:
                product_name_cleaned = self._normalize_product_name(product.get('product_name', ''))
                
                # Multiple matching strategies
                score = self._calculate_product_match_score(name_cleaned, product_name_cleaned, name, product.get('product_name', ''))
                
                if score > best_score and score > 0.4:  # Increased threshold for better matches
                    best_score = score
                    best_match = product
            
            if best_match:
                logger.info(f"Found product match: '{name}' -> '{best_match.get('product_name')}' (score: {best_score:.2f})")
            else:
                logger.warning(f"No product match found for: '{name}' (tried {len(products)} products)")
                
            return best_match
            
        except Exception as e:
            logger.error(f"Error looking up product by name {name}: {e}")
            return None

    def _normalize_product_name(self, name: str) -> str:
        """Normalize product name for better matching"""
        if not name:
            return ""
            
        # Convert to lowercase and strip
        normalized = name.lower().strip()
        
        # Remove common product descriptors that might vary
        descriptors_to_remove = [
            r'\(\d+[a-z]*\)',  # Remove size indicators like (2kg), (500ml)
            r'\d+[a-z]*\s*pack',  # Remove pack indicators
            r'\d+[a-z]*\s*bottle',  # Remove bottle size
            r'\d+[a-z]*\s*can',  # Remove can size
        ]
        
        for pattern in descriptors_to_remove:
            import re
            normalized = re.sub(pattern, '', normalized).strip()
        
        # Handle common plural/singular variations
        singular_to_plural = {
            'apple': 'apples', 'banana': 'bananas', 'orange': 'oranges',
            'tomato': 'tomatoes', 'potato': 'potatoes', 'onion': 'onions',
            'bread': 'breads', 'milk': 'milks', 'egg': 'eggs',
        }
        
        # Check if we can standardize to singular form
        for singular, plural in singular_to_plural.items():
            if normalized.endswith(plural):
                normalized = normalized.replace(plural, singular)
            elif normalized.endswith(singular):
                # Already singular, keep as is
                pass
        
        return normalized
    
    def _calculate_product_match_score(self, name_cleaned: str, product_name_cleaned: str, 
                                     original_name: str, original_product_name: str) -> float:
        """Calculate comprehensive matching score between product names"""
        scores = []
        
        # 1. Exact match (highest priority)
        if name_cleaned == product_name_cleaned:
            return 1.0
        
        # 2. Exact substring match
        if name_cleaned in product_name_cleaned:
            scores.append(len(name_cleaned) / len(product_name_cleaned))
        elif product_name_cleaned in name_cleaned:
            scores.append(len(product_name_cleaned) / len(name_cleaned))
        
        # 3. Word overlap scoring
        name_words = set(name_cleaned.split())
        product_words = set(product_name_cleaned.split())
        if name_words and product_words:
            overlap = len(name_words.intersection(product_words))
            total_words = len(name_words.union(product_words))
            if total_words > 0:
                scores.append(overlap / total_words)
        
        # 4. Fuzzy string similarity (using simple char-based similarity)
        scores.append(self._string_similarity(name_cleaned, product_name_cleaned))
        
        # 5. Check for common variations (apple -> apples, etc.)
        variation_score = self._check_variations(name_cleaned, product_name_cleaned)
        if variation_score > 0:
            scores.append(variation_score)
        
        # 6. Brand name matching
        brand_score = self._check_brand_match(original_name, original_product_name)
        if brand_score > 0:
            scores.append(brand_score * 0.5)  # Weight brand matches lower
        
        # Return the highest score
        return max(scores) if scores else 0.0
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calculate string similarity using character-based approach"""
        if not s1 or not s2:
            return 0.0
        
        # Simple character overlap approach
        s1_chars = set(s1)
        s2_chars = set(s2)
        overlap = len(s1_chars.intersection(s2_chars))
        total = len(s1_chars.union(s2_chars))
        
        return overlap / total if total > 0 else 0.0
    
    def _check_variations(self, name1: str, name2: str) -> float:
        """Check for common product name variations"""
        variations = [
            # Singular/plural pairs
            ('apple', 'apples'), ('banana', 'bananas'), ('orange', 'oranges'),
            ('tomato', 'tomatoes'), ('potato', 'potatoes'), ('onion', 'onions'),
            ('bread', 'breads'), ('milk', 'milks'), ('egg', 'eggs'),
            ('rice', 'rices'), ('sugar', 'sugars'), ('salt', 'salts'),
            ('oil', 'oils'), ('soap', 'soaps'), ('tea', 'teas'),
            
            # Common abbreviations
            ('coke', 'coca cola'), ('pepsi', 'pepsi cola'),
            ('mayo', 'mayonnaise'), ('ketchup', 'tomato sauce'),
        ]
        
        for var1, var2 in variations:
            if (name1 == var1 and var2 in name2) or (name1 == var2 and var1 in name2):
                return 0.9
            if (name2 == var1 and var1 in name1) or (name2 == var2 and var2 in name1):
                return 0.9
        
        return 0.0
    
    def _check_brand_match(self, name1: str, name2: str) -> float:
        """Check if brand names match"""
        common_brands = [
            'coca cola', 'pepsi', 'fanta', 'sprite', 'nestle', 'unilever',
            'lobels', 'bakers inn', 'dairibord', 'olivine', 'mazoe'
        ]
        
        name1_lower = name1.lower()
        name2_lower = name2.lower()
        
        for brand in common_brands:
            if brand in name1_lower and brand in name2_lower:
                return 0.8
        
        return 0.0

    async def compute_receipt(self, parsed_items: List[Dict], user_id: str, store_id: Optional[str] = None, customer_name: Optional[str] = None) -> Dict[str, Any]:
        """Compute final receipt with tax and validate stock"""
        try:
            validated_items = []
            subtotal = 0.0
            errors = []
            warnings = []
            
            # Default store_id if not provided
            if not store_id:
                store_id = f"store_{user_id}"
            
            # Check if we have any items to process
            if not parsed_items:
                return {
                    "success": False,
                    "errors": ["No items were found in your message. Please specify what you want to buy/sell with quantities (e.g., '2 bread, 1 milk' or '2 apples @3.50')"],
                    "warnings": [],
                    "receipt": None
                }
            
            logger.info(f"Processing {len(parsed_items)} items for user {user_id}")
            
            for item in parsed_items:
                item_name = item.get("name", "").strip()
                if not item_name:
                    errors.append("Found an item without a name - please specify the product name")
                    continue
                
                logger.info(f"Looking up product: '{item_name}'")
                
                # Look up product in inventory with enhanced fuzzy matching
                product = await self.lookup_product_by_name(item_name, user_id)
                
                if product:
                    # Product found in database
                    available_stock = product.get('stock_quantity', 0)
                    requested_qty = item["quantity"]
                    database_price = product.get('unit_price', 0)
                    
                    logger.info(f"Found product '{product.get('product_name')}' - stock: {available_stock}, price: ${database_price}")
                    
                    # Use database price if no price was provided, otherwise compare prices
                    if item.get("price_source") == "database" or item["unit_price"] is None:
                        # Use database price
                        final_price = database_price
                        price_source = "database"
                    else:
                        # Price was provided - use it but show comparison
                        provided_price = item["unit_price"]
                        final_price = provided_price
                        price_source = "provided"
                        
                        # Show price difference if significant
                        if abs(database_price - provided_price) > 0.01:
                            warnings.append(f"Price difference for {item['name']}: provided ${provided_price:.2f}, database ${database_price:.2f} - using provided price")
                    
                    # Check stock availability
                    if available_stock >= requested_qty:
                        line_total = requested_qty * final_price
                        
                        validated_item = {
                            "name": product.get('product_name', item["name"]),
                            "quantity": requested_qty,
                            "unit_price": final_price,
                            "line_total": line_total,
                            "sku": product.get('sku'),
                            "category": product.get('category'),
                            "product_id": product.get('id'),
                            "price_source": price_source
                        }
                        
                        validated_items.append(validated_item)
                        subtotal += line_total
                        logger.info(f"Added item: {validated_item['name']} x{requested_qty} @ ${final_price:.2f}")
                        
                    else:
                        errors.append(f"Insufficient stock for {product.get('product_name', item['name'])}: requested {requested_qty}, available {available_stock}")
                        
                else:
                    # Product not found in database - provide helpful suggestions
                    logger.warning(f"Product '{item_name}' not found in inventory")
                    
                    # Get available products to suggest alternatives
                    suggestions = await self._get_product_suggestions(item_name, user_id)
                    
                    if item.get("price_source") == "database" or item["unit_price"] is None:
                        # No price provided and not in database - ask for price or suggest alternatives
                        error_msg = f"Product '{item_name}' not found in inventory."
                        if suggestions:
                            error_msg += f" Did you mean: {', '.join(suggestions[:3])}?"
                        error_msg += f" Or provide price: {item['quantity']} {item_name} @price"
                        errors.append(error_msg)
                    else:
                        # Price was provided - use it
                        warnings.append(f"Product '{item_name}' not found in inventory - using provided price ${item['unit_price']:.2f}")
                        line_total = item["quantity"] * item["unit_price"]
                        
                        validated_item = {
                            "name": item_name,
                            "quantity": item["quantity"],
                            "unit_price": item["unit_price"],
                            "line_total": line_total,
                            "sku": None,
                            "category": "Unknown",
                            "price_source": "provided"
                        }
                        validated_items.append(validated_item)
                        subtotal += line_total
            
            # If no items were successfully processed, return error with suggestions
            if not validated_items:
                error_summary = "No items could be processed from your message."
                if errors:
                    error_summary += " Issues found: " + "; ".join(errors[:3])
                
                return {
                    "success": False,
                    "errors": [error_summary],
                    "warnings": warnings,
                    "receipt": None,
                    "suggestions": [
                        "Check your product names against your inventory",
                        "Use format: 'quantity product' (e.g., '2 bread')",
                        "Include prices if product not in inventory: '2 bread @1.50'",
                        "Available products: " + ", ".join(await self._get_available_products(user_id, limit=5))
                    ]
                }
            
            # Calculate tax and total
            tax_amount = subtotal * self.tax_rate
            total = subtotal + tax_amount
            
            # Generate transaction ID
            transaction_id = f"TXN_{user_id}_{int(datetime.now().timestamp())}"
            
            receipt = {
                "transaction_id": transaction_id,
                "user_id": user_id,
                "store_id": store_id,
                "customer_name": customer_name,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%H:%M:%S"),
                "items": validated_items,
                "subtotal": subtotal,
                "tax_rate": self.tax_rate,
                "tax_amount": tax_amount,
                "total": total,
                "payment_method": "cash",
                "status": "pending",
                "created_at": datetime.now()
            }
            
            return {
                "success": len(errors) == 0,
                "receipt": receipt,
                "errors": errors,
                "warnings": warnings
            }
            
        except Exception as e:
            logger.error(f"Error computing receipt: {e}")
            return {
                "success": False,
                "error": str(e),
                "errors": [str(e)],
                "warnings": []
            }

    async def persist_transaction(self, receipt: Dict[str, Any], collection_name: str = "receipts") -> bool:
        """Persist transaction to Firestore receipts collection and update stock"""
        try:
            if not self.user_service.db:
                logger.error("No database connection available")
                return False
            
            # Store transaction in receipts collection
            receipt_ref = self.user_service.db.collection(collection_name).document(receipt["transaction_id"])
            receipt_ref.set(receipt)
            
            # Update stock levels only if transaction is confirmed
            if receipt.get("status") == "confirmed":
                for item in receipt["items"]:
                    if item.get("product_id"):
                        product_ref = self.user_service.db.collection('products').document(item["product_id"])
                        product_doc = product_ref.get()
                        
                        if product_doc.exists:
                            product_dict = product_doc.to_dict()
                            if product_dict:
                                current_stock = product_dict.get('stock_quantity', 0)
                                new_stock = max(0, current_stock - item["quantity"])
                                product_ref.update({"stock_quantity": new_stock})
            
            logger.info(f"Transaction {receipt['transaction_id']} persisted to {collection_name} successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error persisting transaction: {e}")
            return False

    async def save_pending_transaction(self, receipt: Dict[str, Any]) -> bool:
        """Save pending transaction awaiting confirmation"""
        return await self.persist_transaction(receipt, "pending_transactions")

    async def confirm_transaction(self, transaction_id: str, user_id: str, store_id: str, action: str) -> Dict[str, Any]:
        """Confirm or cancel a pending transaction"""
        try:
            if not self.user_service.db:
                return {"success": False, "error": "No database connection"}
            
            # Get pending transaction
            pending_ref = self.user_service.db.collection('pending_transactions').document(transaction_id)
            pending_doc = pending_ref.get()
            
            if not pending_doc.exists:
                return {"success": False, "error": "Pending transaction not found"}
            
            pending_receipt = pending_doc.to_dict()
            if not pending_receipt:
                return {"success": False, "error": "Invalid transaction data"}
            
            # Verify ownership
            if pending_receipt.get('user_id') != user_id or pending_receipt.get('store_id') != store_id:
                return {"success": False, "error": "Unauthorized access to transaction"}
            
            if action.lower() == "confirm":
                # Move to confirmed receipts collection
                pending_receipt['status'] = 'confirmed'
                
                # Save to receipts collection
                receipt_ref = self.user_service.db.collection('receipts').document(transaction_id)
                receipt_ref.set(pending_receipt)
                
                # Update stock levels
                for item in pending_receipt["items"]:
                    if item.get("product_id"):
                        product_ref = self.user_service.db.collection('products').document(item["product_id"])
                        product_doc = product_ref.get()
                        
                        if product_doc.exists:
                            product_dict = product_doc.to_dict()
                            if product_dict:
                                current_stock = product_dict.get('stock_quantity', 0)
                                new_stock = max(0, current_stock - item["quantity"])
                                product_ref.update({"stock_quantity": new_stock})
                
                # Delete from pending
                pending_ref.delete()
                
                return {
                    "success": True,
                    "message": f"Transaction {transaction_id} confirmed and saved!",
                    "receipt": pending_receipt,
                    "action": "confirmed"
                }
                
            elif action.lower() == "cancel":
                # Update status and delete
                pending_ref.delete()
                
                return {
                    "success": True,
                    "message": f"Transaction {transaction_id} cancelled",
                    "action": "cancelled"
                }
            else:
                return {"success": False, "error": "Invalid action. Use 'confirm' or 'cancel'"}
                
        except Exception as e:
            logger.error(f"Error confirming transaction: {e}")
            return {"success": False, "error": str(e)}

    def format_chat_response(self, receipt: Dict[str, Any], errors: Optional[List[str]] = None, warnings: Optional[List[str]] = None) -> str:
        """Format receipt as chat response"""
        try:
            response = f"🧾 **Transaction Complete!**\n\n"
            response += f"**Receipt ID:** {receipt['transaction_id']}\n"
            response += f"**Date:** {receipt['date']} {receipt['time']}\n"
            
            if receipt.get('customer_name'):
                response += f"**Customer:** {receipt['customer_name']}\n"
            
            response += "\n**Items:**\n"
            for item in receipt['items']:
                response += f"• {item['quantity']}x {item['name']} @ ${item['unit_price']:.2f} = ${item['line_total']:.2f}\n"
            
            response += f"\n**Subtotal:** ${receipt['subtotal']:.2f}\n"
            response += f"**Tax ({receipt['tax_rate']*100:.0f}%):** ${receipt['tax_amount']:.2f}\n"
            response += f"**Total:** ${receipt['total']:.2f}\n"
            
            if warnings:
                response += "\n⚠️ **Warnings:**\n"
                for warning in warnings:
                    response += f"• {warning}\n"
            
            if errors:
                response += "\n❌ **Errors:**\n"
                for error in errors:
                    response += f"• {error}\n"
            
            response += "\nThank you for your business! 🙏"
            return response
            
        except Exception as e:
            logger.error(f"Error formatting chat response: {e}")
            return f"Transaction processed with ID: {receipt.get('transaction_id', 'unknown')}"

    def format_confirmation_request(self, receipt: Dict[str, Any]) -> str:
        """Format confirmation request message for chat"""
        try:
            response = "🧾 **Transaction Ready for Confirmation**\n\n"
            response += f"**Transaction ID:** {receipt['transaction_id']}\n"
            response += f"**Date:** {receipt['date']} {receipt['time']}\n"
            
            if receipt.get('customer_name'):
                response += f"**Customer:** {receipt['customer_name']}\n"
            
            response += "\n**Items:**\n"
            for item in receipt['items']:
                response += f"• {item['quantity']}x {item['name']} @ ${item['unit_price']:.2f} = ${item['line_total']:.2f}\n"
            
            response += f"\n**Subtotal:** ${receipt['subtotal']:.2f}\n"
            response += f"**Tax ({receipt['tax_rate']*100:.0f}%):** ${receipt['tax_amount']:.2f}\n"
            response += f"**Total:** ${receipt['total']:.2f}\n"
            
            response += "\n🔔 **Confirmation Required**\n"
            response += "Please type:\n"
            response += f"• **'confirm {receipt['transaction_id']}'** to save this transaction\n"
            response += f"• **'cancel {receipt['transaction_id']}'** to cancel\n\n"
            response += "⚠️ Transaction will not be saved until confirmed!"
            
            return response
            
        except Exception as e:
            logger.error(f"Error formatting confirmation request: {e}")
            return f"Transaction {receipt.get('transaction_id', 'unknown')} ready for confirmation. Please confirm or cancel."

    def format_confirmation_response(self, confirmation_result: Dict[str, Any]) -> str:
        """Format confirmation result message for chat"""
        try:
            if confirmation_result.get("success"):
                action = confirmation_result.get("action", "")
                if action == "confirmed":
                    response = "✅ **Transaction Confirmed!**\n\n"
                    response += f"Receipt saved successfully! 🎉\n"
                    response += f"Transaction ID: {confirmation_result.get('receipt', {}).get('transaction_id', 'N/A')}\n"
                    response += f"Total: ${confirmation_result.get('receipt', {}).get('total', 0):.2f}\n\n"
                    response += "Stock levels have been updated.\n"
                    response += "Thank you for your business! 🙏"
                elif action == "cancelled":
                    response = "❌ **Transaction Cancelled**\n\n"
                    response += "The transaction has been cancelled and will not be saved.\n"
                    response += "No changes have been made to your inventory."
                else:
                    response = confirmation_result.get("message", "Transaction processed")
            else:
                response = f"❌ **Error:** {confirmation_result.get('error', 'Unknown error occurred')}"
            
            return response
            
        except Exception as e:
            logger.error(f"Error formatting confirmation response: {e}")
            return "Transaction confirmation processed"

    def convert_to_frontend_receipt(self, receipt: Dict[str, Any], user_profile: Optional[Dict] = None) -> Dict[str, Any]:
        """Convert internal receipt format to frontend TransactionReceiptInterface format"""
        try:
            # Convert items to frontend CartItem format
            cart_items = []
            for i, item in enumerate(receipt["items"]):
                cart_item = {
                    "id": f"ITM{i+1:03d}",
                    "name": item["name"],
                    "quantity": item["quantity"],
                    "unitPrice": item["unit_price"],
                    "totalPrice": item["line_total"],
                    "barcode": item.get("sku", ""),
                    "category": item.get("category", "General")
                }
                cart_items.append(cart_item)
            
            # Create customer object if customer name provided
            customer = None
            if receipt.get("customer_name"):
                customer = {
                    "name": receipt["customer_name"],
                    "email": None,
                    "phone": None
                }
            
            # Generate receipt number
            receipt_number = f"RCP-{receipt['transaction_id'].split('_')[-1]}-2025"
            
            # Get merchant name from user profile or default
            merchant_name = "Store"
            if user_profile and user_profile.get("store_name"):
                merchant_name = user_profile["store_name"]
            
            # Generate description
            item_count = len(receipt["items"])
            item_names = [item["name"] for item in receipt["items"][:3]]  # First 3 items
            if item_count > 3:
                description = f"{', '.join(item_names)} and {item_count - 3} more items"
            else:
                description = ', '.join(item_names)
            
            # Format date and time for frontend
            date_formatted = datetime.strptime(receipt["date"], "%Y-%m-%d").strftime("%b %d, %Y")
            time_formatted = datetime.strptime(receipt["time"], "%H:%M:%S").strftime("%I:%M %p")
            
            frontend_receipt = {
                "id": receipt["transaction_id"],
                "amount": receipt["total"],
                "description": description,
                "merchant": merchant_name,
                "date": date_formatted,
                "time": time_formatted,
                "status": "completed",
                "category": self._determine_transaction_category(receipt["items"]),
                "cartItems": cart_items,
                "customer": customer,
                "paymentMethod": receipt.get("payment_method", "cash").title(),
                "cashierName": "System Assistant",
                "receiptNumber": receipt_number,
                "subtotal": receipt["subtotal"],
                "tax": receipt["tax_amount"],
                "discount": None,
                "cartImage": None,  # Could be populated if image processing was used
                "store_id": receipt.get("store_id", f"store_{receipt['user_id']}")
            }
            
            return frontend_receipt
            
        except Exception as e:
            logger.error(f"Error converting to frontend receipt: {e}")
            return {}
    
    def _determine_transaction_category(self, items: List[Dict]) -> str:
        """Determine transaction category based on items"""
        categories = [item.get("category", "General") for item in items]
        
        # Count categories
        category_counts = {}
        for cat in categories:
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        # Return most common category or "Mixed" if diverse
        if not category_counts:
            return "General"
        
        most_common = max(category_counts.keys(), key=lambda x: category_counts[x])
        total_items = len(items)
        
        # If most common category represents less than 60% of items, call it "Mixed"
        if category_counts[most_common] / total_items < 0.6 and len(category_counts) > 1:
            return "Mixed"
        
        return most_common

    async def handle_price_inquiry(self, message: str, user_id: str) -> Dict[str, Any]:
        """Handle price inquiry requests like 'what's the price of bread?'"""
        try:
            # Patterns to detect price inquiries
            price_patterns = [
                r"what'?s?\s+(?:the\s+)?price\s+of\s+(.+?)(?:\?|$)",
                r"price\s+(?:of\s+)?(.+?)(?:\?|$)",
                r"how\s+much\s+(?:is\s+)?(.+?)(?:\?|$)",
                r"cost\s+(?:of\s+)?(.+?)(?:\?|$)"
            ]
            
            message_lower = message.lower().strip()
            product_name = None
            
            for pattern in price_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    product_name = match.group(1).strip()
                    break
            
            if not product_name:
                return {
                    "success": False,
                    "error": "Could not identify product name",
                    "message": "Please specify which product you'd like to know the price of."
                }
            
            # Look up product in database
            product = await self.lookup_product_by_name(product_name, user_id)
            
            if product:
                return {
                    "success": True,
                    "product_name": product.get('product_name', product_name),
                    "price": product.get('unit_price', 0),
                    "stock": product.get('stock_quantity', 0),
                    "sku": product.get('sku'),
                    "category": product.get('category'),
                    "message": f"💰 **{product.get('product_name', product_name)}** costs **${product.get('unit_price', 0):.2f}** per unit\n📦 Stock available: {product.get('stock_quantity', 0)} units"
                }
            else:
                return {
                    "success": False,
                    "error": "Product not found",
                    "message": f"❌ Sorry, I couldn't find '{product_name}' in your inventory.\n\n💡 **Suggestions:**\n- Check the spelling\n- Add the product to your inventory first\n- Try a different product name"
                }
                
        except Exception as e:
            logger.error(f"Error handling price inquiry: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Sorry, I couldn't process your price inquiry."
            }

    def detect_message_type(self, message: str) -> str:
        """Detect the type of message: 'price_inquiry', 'transaction', 'confirmation'"""
        message_lower = message.lower().strip()
        
        # Check for price inquiries
        price_keywords = ["what's the price", "price of", "how much", "cost of", "price for"]
        if any(keyword in message_lower for keyword in price_keywords):
            return "price_inquiry"
        
        # Check for confirmations
        if any(keyword in message_lower for keyword in ["confirm", "cancel"]) and "txn_" in message_lower:
            return "confirmation"
        
        # Check for transactions (items with quantities)
        transaction_patterns = [
            r'\d+\s+\w+',  # "2 bread"
            r'\d+\s*x\s*\w+',  # "2x bread"
            r'\w+\s*@\s*\d+',  # "bread @1.50"
        ]
        
        if any(re.search(pattern, message_lower) for pattern in transaction_patterns):
            return "transaction"
        
        return "unknown"
    
    async def _get_product_suggestions(self, item_name: str, user_id: str, limit: int = 3) -> List[str]:
        """Get product name suggestions for similar items"""
        try:
            products = await self.product_service.get_store_products(user_id)
            if not products:
                return []
            
            suggestions = []
            item_name_lower = item_name.lower()
            
            for product in products:
                product_name = product.get('product_name', '')
                product_name_lower = product_name.lower()
                
                # Check for partial matches or similar words
                if (item_name_lower in product_name_lower or 
                    product_name_lower in item_name_lower or
                    any(word in product_name_lower for word in item_name_lower.split()) or
                    any(word in item_name_lower for word in product_name_lower.split())):
                    suggestions.append(product_name)
                
                if len(suggestions) >= limit:
                    break
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting product suggestions: {e}")
            return []
    
    async def _get_available_products(self, user_id: str, limit: int = 10) -> List[str]:
        """Get list of available product names"""
        try:
            products = await self.product_service.get_store_products(user_id)
            if not products:
                return ["No products found in inventory"]
            
            product_names = [p.get('product_name', 'Unknown') for p in products[:limit]]
            return product_names
            
        except Exception as e:
            logger.error(f"Error getting available products: {e}")
            return ["Error retrieving products"]
