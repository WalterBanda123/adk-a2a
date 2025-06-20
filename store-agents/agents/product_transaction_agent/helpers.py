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
from common.real_product_service import RealProductService
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
        self.product_service = RealProductService()
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
        
        # Enhanced natural language patterns with better product name capture
        patterns = [
            r'(\d+)\s+((?:\w+\s*){1,5})\s+@\s*(\d+(?:\.\d+)?)',  # "2 mazoe orange crush @ 3.50"
            r'(\d+)\s+((?:\w+\s*){1,5})\s+(?:by|for|at)\s+(\d+(?:\.\d+)?)',  # "2 mazoe orange crush by 3.50"
            r'(\d+)\s+((?:\w+\s*){1,5})(?:\s*,|$)',  # "2 mazoe orange crush," or end of string
        ]
        
        # First, split by common delimiters
        segments = re.split(r'[,;]', message)
        
        for segment in segments:
            segment = segment.strip()
            if not segment:
                continue
                
            for pattern in patterns:
                matches = re.finditer(pattern, segment, re.IGNORECASE)
                for match in matches:
                    try:
                        quantity = int(match.group(1))
                        raw_name = match.group(2).strip()
                        
                        # Clean up the product name - remove units/descriptors
                        name = self._clean_product_name_from_parse(raw_name)
                        
                        # Check if price was captured
                        if len(match.groups()) >= 3 and match.group(3):
                            unit_price = float(match.group(3))
                            line_total = quantity * unit_price
                            price_source = "provided"
                        else:
                            unit_price = None
                            line_total = None
                            price_source = "database"
                        
                        if name:  # Only add if we have a valid product name
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
    
    def _clean_product_name_from_parse(self, raw_name: str) -> str:
        """Clean product name extracted from parsing"""
        if not raw_name:
            return ""
        
        # Remove common units/descriptors that shouldn't be part of product name
        units_to_remove = [
            r'\b(?:liters?|litres?|ml|milliliters?)\b',
            r'\b(?:kg|kilograms?|grams?|g)\b', 
            r'\b(?:bottles?|cans?|packs?|pieces?)\b',
            r'\b(?:units?|items?|pcs)\b'
        ]
        
        cleaned = raw_name
        for unit_pattern in units_to_remove:
            import re
            cleaned = re.sub(unit_pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remove extra whitespace and normalize
        cleaned = ' '.join(cleaned.split())
        
        # Fix common typos with more comprehensive patterns
        typo_fixes = {
            # Raspberry variations
            'raspbuspburry': 'raspberry',
            'ruspburry': 'raspberry',
            'raspburry': 'raspberry',
            'rassberry': 'raspberry', 
            'rasberry': 'raspberry',
            'rasperry': 'raspberry',
            'raspberrry': 'raspberry',
            'razzberry': 'raspberry',
            
            # Mazoe variations
            'mazue': 'mazoe',
            'mazo': 'mazoe',
            'masoe': 'mazoe',
            
            # Orange variations
            'ornage': 'orange',
            'orang': 'orange',
            'ornge': 'orange',
            
            # Bread variations
            'bred': 'bread',
            'brd': 'bread',
            
            # Juice variations
            'juce': 'juice',
            'juic': 'juice',
            'juise': 'juice',
        }
        
        cleaned_lower = cleaned.lower()
        
        # Apply exact typo fixes first
        for typo, correction in typo_fixes.items():
            if typo in cleaned_lower:
                cleaned = re.sub(re.escape(typo), correction, cleaned, flags=re.IGNORECASE)
                cleaned_lower = cleaned.lower()  # Update the lowercase version
                break  # Apply only the first match to avoid multiple corrections
        
        # Apply fuzzy typo correction using edit distance for remaining words
        cleaned = self._apply_fuzzy_typo_correction(cleaned)
        
        return cleaned.strip()
    
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
                logger.warning("No database connection available for product lookup")
                return None
            
            # Get all user's products with timeout
            try:
                products = await asyncio.wait_for(
                    self.product_service.get_store_products(user_id),
                    timeout=10.0  # 10 second timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"Timeout getting products for user {user_id}")
                return None
            except Exception as e:
                logger.error(f"Error getting products for user {user_id}: {e}")
                return None
                
            if not products:
                logger.warning(f"No products found for user {user_id}")
                return None
            
            logger.info(f"Looking up '{name}' among {len(products)} products for user {user_id}")
            
            # Clean and normalize the input name
            name_cleaned = self._normalize_product_name(name)
            best_match = None
            best_score = 0.0
            
            for product in products:
                product_name = product.get('product_name', '')
                product_name_cleaned = self._normalize_product_name(product_name)
                
                # Multiple matching strategies
                score = self._calculate_product_match_score(name_cleaned, product_name_cleaned, name, product_name)
                
                logger.debug(f"Matching '{name}' vs '{product_name}': score = {score:.3f}")
                
                # Lowered threshold from 0.4 to 0.3 for better fuzzy matching
                if score > best_score and score > 0.3:
                    best_score = score
                    best_match = product
                    logger.info(f"New best match: '{product_name}' with score {score:.3f}")
            
            if best_match:
                logger.info(f"✅ Found product match: '{name}' -> '{best_match.get('product_name')}' (score: {best_score:.2f})")
            else:
                logger.warning(f"❌ No product match found for: '{name}' (tried {len(products)} products, best score: {best_score:.3f})")
                
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
        
        # 3. Primary keyword identification and matching
        name_words = name_cleaned.split()
        product_words = product_name_cleaned.split()
        
        if name_words and product_words:
            # Identify the primary/key word (usually the main product name)
            # Priority order: last word (often the main product), longest word, first word
            key_word = max(name_words, key=len)  # Get the longest word as primary
            
            # Check if the key word has a strong match in product name
            key_matches = [word for word in product_words if key_word in word or word in key_word]
            
            if key_matches:
                # Strong key word match found
                key_match_score = max(
                    min(len(key_word), len(match)) / max(len(key_word), len(match))
                    for match in key_matches
                )
                scores.append(key_match_score * 1.2)  # Boost key word matches
        
        # 4. Word overlap scoring with improved logic  
        name_words_set = set(name_words)
        product_words_set = set(product_words)
        if name_words_set and product_words_set:
            overlap = len(name_words_set.intersection(product_words_set))
            total_input_words = len(name_words_set)
            
            # Priority scoring: if majority of input words match, give high score
            if total_input_words > 0:
                input_match_ratio = overlap / total_input_words
                scores.append(input_match_ratio)
                
                # Bonus for high input word match ratio
                if input_match_ratio >= 0.7:  # 70% or more of input words match
                    scores.append(0.9)
        
        # 5. Fuzzy string similarity (using simple char-based similarity)
        char_similarity = self._string_similarity(name_cleaned, product_name_cleaned)
        scores.append(char_similarity * 0.8)  # Reduce weight of character similarity
        
        # 6. Check for common variations (apple -> apples, etc.)
        variation_score = self._check_variations(name_cleaned, product_name_cleaned)
        if variation_score > 0:
            scores.append(variation_score)
        
        # 7. Brand name matching (but only if key product word also matches)
        brand_score = self._check_brand_match(original_name, original_product_name)
        if brand_score > 0:
            # Only apply brand score if there's also a product word match
            if len(name_words) > 1:  # Multi-word input, check for product match
                non_brand_words = [w for w in name_words if w not in ['mazoe', 'coca', 'pepsi', 'nestle']]
                if non_brand_words:
                    product_match = any(
                        any(nb_word in pw or pw in nb_word for pw in product_words)
                        for nb_word in non_brand_words
                    )
                    if product_match:
                        scores.append(brand_score)
            else:
                scores.append(brand_score)  # Single word, apply brand score
        
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
            
            # Common abbreviations and brand shortcuts
            ('coke', 'coca cola'), ('pepsi', 'pepsi cola'),
            ('mayo', 'mayonnaise'), ('ketchup', 'tomato sauce'),
            ('mazoe', 'mazoe orange'), ('mazoe', 'orange crush'),
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
            'lobels', 'bakers inn', 'dairibord', 'olivine', 'mazoe',
            'colgate', 'surf', 'omo', 'vaseline', 'blue band'
        ]
        
        name1_lower = name1.lower()
        name2_lower = name2.lower()
        
        for brand in common_brands:
            if brand in name1_lower and brand in name2_lower:
                # Give higher score for brand matches
                return 0.9
        
        # Also check if the entire input is just a brand name
        if name1_lower in common_brands and name1_lower in name2_lower:
            return 0.95
        
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
                    
                    # Price validation and correction logic
                    if item.get("price_source") == "database" or item["unit_price"] is None:
                        # No price provided - use database price
                        final_price = database_price
                        price_source = "database"
                    else:
                        # Price was provided by user - validate against database
                        provided_price = item["unit_price"]
                        price_difference = abs(database_price - provided_price)
                        
                        if price_difference > 0.01:  # Significant difference (more than 1 cent)
                            # Use database price but warn user about discrepancy
                            final_price = database_price
                            price_source = "database_corrected"
                            
                            percentage_diff = (price_difference / database_price) * 100
                            warnings.append(
                                f"Price correction for '{product.get('product_name', item_name)}': "
                                f"You entered ${provided_price:.2f}, but the saved price is ${database_price:.2f} "
                                f"({percentage_diff:.1f}% difference). Using saved price ${database_price:.2f}. "
                                f"If you want to update the product price, please let me know after confirming this transaction."
                            )
                        else:
                            # Prices match (within 1 cent) - use provided price
                            final_price = provided_price
                            price_source = "provided"
                    
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
            current_datetime = datetime.now()
            
            # Create receipt following standardized model structure
            receipt = {
                "transaction_id": transaction_id,
                "userId": user_id,  # Primary user ID field (standardized)
                "user_id": user_id,  # Legacy field for compatibility
                "store_id": store_id,
                "customer_name": customer_name or "Walk-in Customer",
                "date": current_datetime.strftime("%Y-%m-%d"),
                "time": current_datetime.strftime("%H:%M:%S"),
                "created_at": current_datetime.isoformat(),
                "items": [
                    {
                        "name": item["name"],
                        "quantity": item["quantity"],
                        "unit_price": item["unit_price"],
                        "line_total": item["line_total"],
                        "product_id": item.get("product_id"),
                        "sku": item.get("sku"),
                        "category": item.get("category")
                    } for item in validated_items
                ],
                "subtotal": round(subtotal, 2),
                "tax_rate": self.tax_rate,
                "tax_amount": round(tax_amount, 2),
                "total": round(total, 2),
                "payment_method": "cash",
                "change_due": 0.0,  # Default, can be updated if payment amount provided
                "status": "pending"
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
    async def persist_transaction(self, receipt: Dict[str, Any], collection_name: str = "transactions") -> bool:
        """Persist transaction to Firestore and update stock (following standardized model)"""
        try:
            if not self.user_service.db:
                logger.error("No database connection available")
                return False
            
            # Ensure standardized field structure
            if 'userId' not in receipt and 'user_id' in receipt:
                receipt['userId'] = receipt['user_id']
            
            # Store transaction in specified collection (default: transactions)
            transaction_ref = self.user_service.db.collection(collection_name).document(receipt["transaction_id"])
            transaction_ref.set(receipt)
            
            # Update stock levels only if transaction is completed/confirmed
            if receipt.get("status") in ["completed", "confirmed"]:
                for item in receipt["items"]:
                    product_id = item.get("product_id")
                    if product_id:
                        try:
                            product_ref = self.user_service.db.collection('products').document(product_id)
                            product_doc = product_ref.get()
                            
                            if product_doc.exists:
                                product_dict = product_doc.to_dict()
                                if product_dict:
                                    current_stock = product_dict.get('stock_quantity', 0)
                                    new_stock = max(0, current_stock - item["quantity"])
                                    
                                    # Update using standardized field names
                                    product_ref.update({
                                        "stock_quantity": new_stock,
                                        "last_updated": datetime.now().isoformat()
                                    })
                                    
                                    logger.info(f"Updated stock for {item.get('name', 'Unknown')}: {current_stock} -> {new_stock}")
                        except Exception as e:
                            logger.error(f"Error updating stock for product {product_id}: {e}")
                            # Continue with other items even if one fails
            
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
                
            # Verify ownership - check standardized userId field first, then legacy fields
            receipt_user_id = pending_receipt.get('userId') or pending_receipt.get('user_id')
            receipt_store_id = pending_receipt.get('store_id')
            
            if receipt_user_id != user_id or receipt_store_id != store_id:
                return {"success": False, "error": "Unauthorized access to transaction"}
            
            if action.lower() == "confirm":
                # Update status and timestamps for confirmation
                pending_receipt['status'] = 'completed'  # Use 'completed' as per standardized model
                pending_receipt['confirmed_at'] = datetime.now().isoformat()
                
                # Ensure standardized field structure
                if 'userId' not in pending_receipt:
                    pending_receipt['userId'] = user_id
                # Update stock levels for confirmed transaction
                for item in pending_receipt["items"]:
                    product_id = item.get("product_id")
                    if product_id:
                        try:
                            product_ref = self.user_service.db.collection('products').document(product_id)
                            product_doc = product_ref.get()
                            
                            if product_doc.exists:
                                product_dict = product_doc.to_dict()
                                if product_dict:
                                    current_stock = product_dict.get('stock_quantity', 0)
                                    new_stock = max(0, current_stock - item["quantity"])
                                    
                                    # Update using standardized field name
                                    product_ref.update({
                                        "stock_quantity": new_stock,
                                        "last_updated": datetime.now().isoformat()
                                    })
                                    
                                    logger.info(f"Updated stock for {item.get('name', 'Unknown')}: {current_stock} -> {new_stock}")
                        except Exception as e:
                            logger.error(f"Error updating stock for product {product_id}: {e}")
                            # Continue with other items even if one fails
                
                # Save confirmed transaction to main transactions collection
                confirmed_success = await self.persist_transaction(pending_receipt, "transactions")
                if not confirmed_success:
                    logger.error(f"Failed to save confirmed transaction {transaction_id}")
                
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
    
    def is_stock_inquiry(self, message: str) -> bool:
        """Detect if the message is asking about stock levels rather than making a sale"""
        import re
        
        # Patterns that indicate stock inquiry
        stock_patterns = [
            r'\b(?:how much|how many|what(?:\'s| is)|check|show)\b.*\b(?:stock|inventory|have|left|remaining)\b',
            r'\b(?:stock|inventory)\b.*\b(?:of|for|level|levels)\b',
            r'\b(?:do i have|have i got|what do i have|show me)\b',
            r'\b(?:current|available)\b.*\b(?:stock|inventory)\b',
            r'\b(?:stock|inventory)\b.*\b(?:check|status|report|levels)\b',
            r'\b(?:list|show|display)\b.*\b(?:all|my|current)\b.*\b(?:products|items|stock|inventory)\b'
        ]
        
        message_lower = message.lower()
        
        # Check for stock inquiry patterns
        for pattern in stock_patterns:
            if re.search(pattern, message_lower):
                return True
        
        # Additional simple keyword checks
        stock_keywords = ['inventory', 'stock level', 'stock check', 'how much', 'how many']
        for keyword in stock_keywords:
            if keyword in message_lower:
                return True
        
        return False
    
    def extract_product_from_stock_query(self, message: str) -> Optional[str]:
        """Extract specific product name from stock inquiry"""
        import re
        
        # Clean the message
        message_lower = message.lower()
        
        # If asking for general inventory, return None for overview
        general_patterns = [
            r'\b(?:inventory|stock|products|items)\b\s*$',
            r'(?:show|list|check)\s+(?:all|my|current|total)\s*(?:inventory|stock|products|items)',
            r'(?:what|how many|how much)\s+(?:products|items|stock|inventory)\s+(?:do\s+)?(?:i\s+)?(?:have|got)',
        ]
        
        for pattern in general_patterns:
            if re.search(pattern, message_lower):
                return None  # Return None for general overview
        
        # Remove stock inquiry words and common stop words
        remove_patterns = [
            r'\b(?:what|how|do|i|have|of|for|the|my|me|is|are|in|on|at|to|from|with)\b',
            r'\b(?:much|many|any|some|all|current|available|remaining|left)\b',
            r'\b(?:stock|inventory|level|levels|check|show|list|display)\b',
            r'\b(?:what\'s|how\'s|there|here|got|get)\b'
        ]
        
        cleaned = message_lower
        for pattern in remove_patterns:
            cleaned = re.sub(pattern, ' ', cleaned)
        
        # Extract meaningful words (potential product names)
        words = re.findall(r'\b[a-zA-Z]{2,}\b', cleaned)
        words = [w for w in words if len(w) > 2]  # Filter out very short words
        
        if words:
            # Join words to form potential product name, but limit to reasonable length
            if len(words) <= 4:  # Max 4 words for product name
                potential_product = ' '.join(words).strip()
                if potential_product and len(potential_product) > 2:
                    return potential_product
        
        return None
    
    async def handle_stock_inquiry(self, message: str, user_id: str) -> Dict[str, Any]:
        """Handle stock level inquiries and return formatted response"""
        try:
            # Import the real product service for actual stock data
            from common.real_product_service import RealProductService
            real_product_service = RealProductService()
            
            # Get user's products
            products = await real_product_service.get_store_products(user_id)
            
            if not products:
                return {
                    "success": True,
                    "message": "📦 **Inventory Check**\n\nNo products found in your inventory. Start by adding some products to track your stock levels!",
                    "is_stock_query": True
                }
            
            # Check if asking about a specific product
            specific_product = self.extract_product_from_stock_query(message)
            
            if specific_product:
                # Find matching products
                matches = []
                specific_lower = specific_product.lower()
                
                for product in products:
                    name = product.get('product_name', product.get('name', '')).lower()
                    if specific_lower in name or name in specific_lower:
                        matches.append(product)
                
                if matches:
                    response = f"📦 **Stock Check: {specific_product.title()}**\n\n"
                    for product in matches:
                        name = product.get('product_name', product.get('name', 'Unknown'))
                        stock = product.get('stock_quantity', product.get('quantity', 0))
                        unit = product.get('unit_of_measure', product.get('unit', 'units'))
                        price = product.get('unit_price', product.get('unitPrice', 0))
                        
                        stock_status = "🟢 In Stock" if stock > 5 else "🟡 Low Stock" if stock > 0 else "🔴 Out of Stock"
                        response += f"• **{name}**: {stock} {unit} {stock_status}\n"
                        response += f"  Price: ${price:.2f} per {unit}\n\n"
                else:
                    response = f"📦 **Stock Check**\n\nNo products found matching '{specific_product}'. Here are your available products:\n\n"
                    for product in products[:5]:  # Show first 5
                        name = product.get('product_name', product.get('name', 'Unknown'))
                        response += f"• {name}\n"
                    
                    if len(products) > 5:
                        response += f"\n...and {len(products) - 5} more products."
            else:
                # General inventory overview
                response = "📦 **Complete Inventory Overview**\n\n"
                
                # Group by stock status
                in_stock = []
                low_stock = []
                out_of_stock = []
                
                for product in products:
                    stock = product.get('stock_quantity', product.get('quantity', 0))
                    if stock > 5:
                        in_stock.append(product)
                    elif stock > 0:
                        low_stock.append(product)
                    else:
                        out_of_stock.append(product)
                
                # Display summary
                response += f"**Total Products**: {len(products)}\n"
                response += f"🟢 **In Stock**: {len(in_stock)} items\n"
                response += f"🟡 **Low Stock**: {len(low_stock)} items\n"
                response += f"🔴 **Out of Stock**: {len(out_of_stock)} items\n\n"
                
                # Show details for each category
                if low_stock:
                    response += "⚠️ **Low Stock Alert**:\n"
                    for product in low_stock[:3]:  # Show top 3
                        name = product.get('product_name', product.get('name', 'Unknown'))
                        stock = product.get('stock_quantity', product.get('quantity', 0))
                        unit = product.get('unit_of_measure', product.get('unit', 'units'))
                        response += f"• {name}: {stock} {unit}\n"
                    response += "\n"
                
                if out_of_stock:
                    response += "🚨 **Out of Stock**:\n"
                    for product in out_of_stock[:3]:  # Show top 3
                        name = product.get('product_name', product.get('name', 'Unknown'))
                        response += f"• {name}\n"
                    response += "\n"
                
                # Show some in-stock items
                if in_stock:
                    response += "✅ **Well Stocked** (sample):\n"
                    for product in in_stock[:5]:  # Show top 5
                        name = product.get('product_name', product.get('name', 'Unknown'))
                        stock = product.get('stock_quantity', product.get('quantity', 0))
                        unit = product.get('unit_of_measure', product.get('unit', 'units'))
                        response += f"• {name}: {stock} {unit}\n"
                    
                    if len(in_stock) > 5:
                        response += f"...and {len(in_stock) - 5} more well-stocked items.\n"
            
            return {
                "success": True,
                "message": response,
                "is_stock_query": True,
                "products_count": len(products)
            }
            
        except Exception as e:
            logger.error(f"Error handling stock inquiry: {str(e)}")
            return {
                "success": False,
                "message": f"📦 **Stock Check Error**\n\nSorry, I couldn't retrieve your inventory at the moment. Please try again later.\n\nError: {str(e)}",
                "is_stock_query": True
            }
    
    def _apply_fuzzy_typo_correction(self, text: str) -> str:
        """Apply fuzzy typo correction using edit distance for unmatched words"""
        if not text:
            return ""
        
        # Common product words for reference
        common_product_words = {
            'bread', 'milk', 'eggs', 'rice', 'sugar', 'oil', 'tea', 'coffee',
            'apple', 'banana', 'orange', 'tomato', 'onion', 'potato',
            'soap', 'salt', 'flour', 'juice', 'crush', 'raspberry',
            'mazoe', 'coca', 'cola', 'pepsi', 'fanta', 'sprite'
        }
        
        words = text.lower().split()
        corrected_words = []
        
        for word in words:
            if len(word) <= 2:  # Skip very short words
                corrected_words.append(word)
                continue
                
            # Check if word is already correct
            if word in common_product_words:
                corrected_words.append(word)
                continue
            
            # Find closest match using simple edit distance
            best_match = word
            best_distance = float('inf')
            
            for reference_word in common_product_words:
                distance = self._edit_distance(word, reference_word)
                # Only consider it a typo if it's close enough (within 2-3 character changes)
                max_allowed_distance = min(3, len(word) // 2)
                
                if distance < best_distance and distance <= max_allowed_distance:
                    best_distance = distance
                    best_match = reference_word
            
            corrected_words.append(best_match)
        
        return ' '.join(corrected_words)
    
    def _edit_distance(self, s1: str, s2: str) -> int:
        """Calculate edit distance between two strings"""
        if len(s1) < len(s2):
            return self._edit_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
