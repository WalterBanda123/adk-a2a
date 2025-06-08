import os
import logging
import base64
import uuid
import re
from typing import Dict, Any, Optional
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore, storage
from google.cloud import vision
from PIL import Image, ImageEnhance, ImageFilter
import io
import requests
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

logger = logging.getLogger(__name__)

class ImageAnalysisService:
    def __init__(self):
        self.db = None
        self.storage_bucket = None
        self.vision_client = None
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize Firebase and Google Vision services"""
        try:
            # Initialize Firebase if not already done
            if not firebase_admin._apps:
                cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
                project_id = os.getenv("FIREBASE_PROJECT_ID")
                
                if cred_path and os.path.exists(cred_path):
                    logger.info(f"Initializing Firebase with service account key: {cred_path}")
                    cred = credentials.Certificate(cred_path)
                    
                    if project_id:
                        firebase_admin.initialize_app(cred, {
                            'projectId': project_id,
                            'storageBucket': f'{project_id}.appspot.com'
                        })
                    else:
                        firebase_admin.initialize_app(cred)
                        
                    logger.info("Firebase Admin SDK initialized successfully")
                else:
                    logger.warning("No valid Firebase service account key found")
            
            # Initialize services
            self.db = firestore.client()
            
            # Get Firebase project ID for storage bucket
            project_id = os.getenv("FIREBASE_PROJECT_ID")
            if project_id:
                self.storage_bucket = storage.bucket(f'{project_id}.appspot.com')
            else:
                # Try to get default bucket
                try:
                    self.storage_bucket = storage.bucket()
                except Exception:
                    # If default bucket fails, try using project_id from service account
                    try:
                        cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
                        if cred_path and os.path.exists(cred_path):
                            import json
                            with open(cred_path, 'r') as f:
                                cred_data = json.load(f)
                                project_id = cred_data.get('project_id')
                                if project_id:
                                    self.storage_bucket = storage.bucket(f'{project_id}.appspot.com')
                    except Exception:
                        pass
            
            # For Vision API, we need to set the credentials explicitly BEFORE creating the client
            cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
            if cred_path and os.path.exists(cred_path):
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = cred_path
                try:
                    self.vision_client = vision.ImageAnnotatorClient()
                    logger.info("Google Vision API client initialized successfully")
                except Exception as vision_error:
                    logger.error(f"Failed to initialize Vision API client: {str(vision_error)}")
                    if "SERVICE_DISABLED" in str(vision_error):
                        logger.error("Google Cloud Vision API is not enabled. Please enable it in Google Cloud Console.")
                    self.vision_client = None
            else:
                logger.warning("No service account key found for Vision API")
                self.vision_client = None
            
            logger.info("Image Analysis Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Image Analysis Service: {str(e)}")
            self.db = None
            self.storage_bucket = None
            self.vision_client = None
    
    async def analyze_product_image(self, image_data: bytes, user_id: str, filename: str = None) -> Dict[str, Any]:
        """
        Analyze a product image and extract structured product information
        
        Args:
            image_data: Raw image bytes
            user_id: The user ID of the store owner
            filename: Optional original filename
        
        Returns:
            Dict containing structured product information
        """
        try:
            if not self.storage_bucket:
                logger.warning("Firebase Storage not available, analysis will continue without image storage")
            
            # Generate unique ID for this product analysis
            product_id = f"PRD_{user_id[:8]}_{uuid.uuid4().hex[:8]}"
            
            # Step 1: Process and enhance the image
            processed_image_data = self._enhance_image(image_data)
            
            # Step 2: Analyze image with Google Vision API (if available)
            if self.vision_client:
                vision_results = await self._analyze_with_vision(processed_image_data)
            else:
                # Fallback mode without Vision API
                logger.warning("Vision API not available, using fallback mode")
                vision_results = {
                    "text": "Vision API not available",
                    "objects": [],
                    "labels": [],
                    "confidence": 0
                }
            
            # Step 3: Extract structured product information
            product_info = self._extract_product_info(vision_results, product_id, user_id)
            
            # Step 4: Upload processed image to Firebase Storage
            image_url = await self._upload_image_to_storage(
                processed_image_data, 
                f"products/{user_id}/{product_id}.jpg"
            )
            
            # Step 5: Add image URL to product info
            product_info["image"] = image_url
            product_info["original_filename"] = filename
            
            return {
                "success": True,
                "product_info": product_info,
                "message": "Product image processed successfully" + (" (Vision AI not available)" if not self.vision_client else ""),
                "analysis_details": {
                    "vision_confidence": vision_results.get("confidence", 0),
                    "detected_text": vision_results.get("text", ""),
                    "detected_objects": vision_results.get("objects", []),
                    "vision_api_available": self.vision_client is not None
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing product image: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to analyze product image: {str(e)}"
            }
    
    def _enhance_image(self, image_data: bytes) -> bytes:
        """Enhance image quality for better analysis and display"""
        try:
            # Open image with PIL
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large (max 1024x1024)
            max_size = 1024
            if image.width > max_size or image.height > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Enhance image quality
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)  # Increase contrast slightly
            
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.1)  # Sharpen slightly
            
            # Save enhanced image to bytes
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            logger.warning(f"Image enhancement failed: {str(e)}, using original")
            return image_data
    
    async def _analyze_with_vision(self, image_data: bytes) -> Dict[str, Any]:
        """Analyze image using Google Vision API"""
        try:
            image = vision.Image(content=image_data)
            
            # Perform text detection
            text_response = self.vision_client.text_detection(image=image)
            texts = text_response.text_annotations
            
            # Perform object detection
            object_response = self.vision_client.object_localization(image=image)
            objects = object_response.localized_object_annotations
            
            # Perform label detection
            label_response = self.vision_client.label_detection(image=image)
            labels = label_response.label_annotations
            
            # Extract and structure results
            detected_text = texts[0].description if texts else ""
            detected_objects = [obj.name for obj in objects]
            detected_labels = [label.description for label in labels]
            
            return {
                "text": detected_text,
                "objects": detected_objects,
                "labels": detected_labels,
                "confidence": texts[0].score if texts else 0
            }
            
        except Exception as e:
            logger.error(f"Vision API analysis failed: {str(e)}")
            return {"text": "", "objects": [], "labels": [], "confidence": 0}
    
    def _extract_product_info(self, vision_results: Dict[str, Any], product_id: str, user_id: str) -> Dict[str, Any]:
        """Extract structured product information from vision analysis results"""
        detected_text = vision_results.get("text", "").upper()
        detected_labels = vision_results.get("labels", [])
        detected_objects = vision_results.get("objects", [])
        
        # If Vision API is not available, provide fallback values
        if not detected_text or detected_text == "VISION API NOT AVAILABLE":
            name = "Product from Image"
            brand = "Unknown Brand"
            size = ""
            unit = "pieces"
            category = "General"
            subcategory = "Miscellaneous"
            barcode = ""
            description = "Product imported from image - please update details"
        else:
            # Extract product name and brand
            name, brand = self._extract_name_and_brand(detected_text)
            
            # Extract size information
            size, unit = self._extract_size_info(detected_text)
            
            # Determine category
            category, subcategory = self._categorize_product(detected_labels, detected_objects, detected_text)
            
            # Extract barcode if visible
            barcode = self._extract_barcode(detected_text)
            
            # Generate description
            description = self._generate_description(name, brand, size, unit)
        
        # Structure the product information
        product_info = {
            "id": product_id,
            "name": name,
            "description": description,
            "category": category,
            "subcategory": subcategory,
            "unitPrice": 0.0,  # To be filled by user
            "quantity": 0,  # To be filled by user
            "unit": unit or "pieces",
            "brand": brand,
            "size": size,
            "status": "pending",  # Will be set to 'in-stock' when user saves
            "lastRestocked": datetime.now().strftime("%b %d, %Y"),
            "supplier": "",  # To be filled by user
            "barcode": barcode,
            "store_owner_id": user_id,
            "created_at": datetime.now().isoformat(),
            "analysis_source": "image_ai" if detected_text != "VISION API NOT AVAILABLE" else "image_upload"
        }
        
        return product_info
    
    def _extract_name_and_brand(self, text: str) -> tuple[str, str]:
        """Extract product name and brand from detected text"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Common brand patterns for Zimbabwe market
        zimbabwe_brands = [
            'COCA-COLA', 'PEPSI', 'SPRITE', 'FANTA', 'MAZOE', 'DAIRIBORD',
            'LOBELS', 'PROTON', 'OLIVINE', 'GOLDLEAF', 'BLUE RIBBON',
            'CAIRNS', 'TANGANDA', 'FLAME LILY', 'LAKE HARVEST', 'KAPENTA'
        ]
        
        brand = ""
        name = ""
        
        # Look for known brands
        for line in lines:
            for zim_brand in zimbabwe_brands:
                if zim_brand in line:
                    brand = zim_brand.title()
                    # If we found the brand, see if there's a product name on the same line or other lines
                    remaining_text = line.replace(zim_brand, "").strip()
                    if remaining_text and len(remaining_text) > 2:
                        name = remaining_text
                    break
            if brand:
                break
        
        # If no brand found, try to extract from first line
        if not brand and lines:
            first_line = lines[0]
            # Check if it contains common product indicators
            if any(word in first_line.upper() for word in ['COLA', 'DRINK', 'JUICE', 'WATER', 'BEER']):
                brand = first_line
        
        # Extract product name from remaining lines if not found yet
        if not name and lines:
            for line in lines:
                if line.upper() != brand.upper() and len(line) > 2:
                    # Look for product descriptors
                    if any(word in line.upper() for word in ['COLA', 'CLASSIC', 'ORIGINAL', 'LIGHT', 'ZERO']):
                        name = line
                        break
        
        # If brand is found but no separate name, use brand as name
        if brand and not name:
            name = brand
            
        # Clean up name to remove brand duplication
        if name and brand and brand.upper() in name.upper():
            name = name.replace(brand, "").strip()
            if not name:
                name = brand
        
        # Clean up name
        if name:
            name = re.sub(r'[^\w\s\(\)\-\.]', '', name).strip()
        
        return name or "Product", brand or "Unknown Brand"
    
    def _extract_size_info(self, text: str) -> tuple[str, str]:
        """Extract size and unit information from text"""
        # Common size patterns
        size_patterns = [
            r'(\d+(?:\.\d+)?)\s*(ML|L|LITERS?|LITRES?)',
            r'(\d+(?:\.\d+)?)\s*(KG|G|GRAMS?)',
            r'(\d+(?:\.\d+)?)\s*(OZ|OUNCES?)',
            r'(\d+)\s*(PACK|PCS?|PIECES?)',
            r'(\d+)\s*X\s*(\d+(?:\.\d+)?)\s*(ML|L|G|KG)'
        ]
        
        for pattern in size_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    size, unit = match.groups()
                    return size, unit.lower()
                elif len(match.groups()) == 3:  # For patterns like "6 X 500 ML"
                    count, size, unit = match.groups()
                    return f"{count}x{size}", unit.lower()
        
        return "", "pieces"
    
    def _categorize_product(self, labels: list, objects: list, text: str) -> tuple[str, str]:
        """Categorize product based on detected labels and text"""
        category_mapping = {
            'Beverages': {
                'keywords': ['drink', 'beverage', 'juice', 'soda', 'water', 'cola', 'beer', 'wine'],
                'subcategories': ['Soft Drinks', 'Juices', 'Water', 'Alcoholic']
            },
            'Food': {
                'keywords': ['food', 'snack', 'bread', 'biscuit', 'cookie', 'cake', 'meal'],
                'subcategories': ['Snacks', 'Bakery', 'Prepared Foods', 'Confectionery']
            },
            'Dairy': {
                'keywords': ['milk', 'cheese', 'yogurt', 'dairy', 'cream'],
                'subcategories': ['Milk', 'Cheese', 'Yogurt', 'Other Dairy']
            },
            'Household': {
                'keywords': ['soap', 'detergent', 'cleaning', 'tissue', 'paper'],
                'subcategories': ['Cleaning', 'Personal Care', 'Paper Products']
            },
            'Personal Care': {
                'keywords': ['shampoo', 'lotion', 'cream', 'toothpaste', 'deodorant'],
                'subcategories': ['Hair Care', 'Skin Care', 'Oral Care', 'Body Care']
            }
        }
        
        # Combine all text for analysis
        all_text = ' '.join(labels + objects + [text]).lower()
        
        for category, data in category_mapping.items():
            for keyword in data['keywords']:
                if keyword in all_text:
                    # Try to determine subcategory
                    subcategory = data['subcategories'][0]  # Default to first
                    for sub in data['subcategories']:
                        if sub.lower() in all_text:
                            subcategory = sub
                            break
                    return category, subcategory
        
        return 'General', 'Miscellaneous'
    
    def _extract_barcode(self, text: str) -> str:
        """Extract barcode from detected text"""
        # Look for number sequences that could be barcodes
        barcode_patterns = [
            r'\b(\d{8,14})\b',  # Common barcode lengths
            r'(\d{3}-\d{3,4}-\d{3,6})',  # Formatted barcodes
        ]
        
        for pattern in barcode_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return ""
    
    def _generate_description(self, name: str, brand: str, size: str, unit: str) -> str:
        """Generate a product description in the format: 'size unit of product' (e.g., '2kg sachet of sugar', '500ml PET Coke')"""
        
        # Clean up inputs
        name = name.strip() if name and name != "Unknown Product" else ""
        brand = brand.strip() if brand and brand != "Unknown Brand" else ""
        size = size.strip() if size else ""
        unit = unit.strip() if unit and unit != "pieces" else ""
        
        # Build description parts
        description_parts = []
        
        # Add size and unit if available
        if size and unit:
            if unit.lower() in ['ml', 'l', 'liters', 'litres']:
                size_part = f"{size}{unit.lower()}"
            elif unit.lower() in ['kg', 'g', 'grams']:
                size_part = f"{size}{unit.lower()}"
            else:
                size_part = f"{size} {unit}"
            description_parts.append(size_part)
        elif size:
            description_parts.append(size)
        
        # Add container type based on common patterns
        container_type = ""
        if unit and unit.lower() in ['ml', 'l']:
            if 'bottle' in name.lower() or 'pet' in name.lower():
                container_type = "bottle"
            elif 'can' in name.lower():
                container_type = "can"
            elif 'carton' in name.lower():
                container_type = "carton"
        elif unit and unit.lower() in ['kg', 'g']:
            if 'packet' in name.lower() or 'pack' in name.lower():
                container_type = "packet"
            elif 'bag' in name.lower():
                container_type = "bag"
            elif 'sachet' in name.lower():
                container_type = "sachet"
        
        if container_type:
            description_parts.append(container_type)
        
        # Add "of" connector
        if description_parts:
            description_parts.append("of")
        
        # Add product name or brand (avoid duplication)
        product_part = ""
        if brand and name and name.lower() != brand.lower():
            product_part = f"{brand} {name}".strip()
        elif brand:
            product_part = brand
        elif name:
            product_part = name
        else:
            product_part = "product"
        
        description_parts.append(product_part.lower())
        
        # Join and clean up
        description = " ".join(description_parts)
        
        # Clean up common issues
        description = description.replace("  ", " ").strip()
        
        # Capitalize first letter
        if description:
            description = description[0].upper() + description[1:]
        
        # Fallback if no meaningful description could be generated
        if not description or description in ["Product", "Of product"]:
            if brand and name:
                description = f"{brand} {name}"
            elif name:
                description = name
            elif brand:
                description = brand
            else:
                description = "Product from image"
        
        return description
    
    async def _upload_image_to_storage(self, image_data: bytes, storage_path: str) -> str:
        """Upload processed image to Firebase Storage and return public URL"""
        try:
            if not self.storage_bucket:
                # Return a placeholder URL when storage is not available
                logger.warning("Firebase Storage not available, returning placeholder URL")
                return f"https://placeholder.example.com/images/{storage_path.split('/')[-1]}"
            
            blob = self.storage_bucket.blob(storage_path)
            blob.upload_from_string(image_data, content_type='image/jpeg')
            
            # Make the blob publicly accessible
            blob.make_public()
            
            return blob.public_url
            
        except Exception as e:
            logger.error(f"Failed to upload image to storage: {str(e)}")
            # Return a placeholder URL on error
            return f"https://placeholder.example.com/images/{storage_path.split('/')[-1]}"
