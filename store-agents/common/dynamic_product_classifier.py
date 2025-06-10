"""
Dynamic Product Classifier
Provides business-specific product classification based on user location and industry
"""

import json
import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from .user_profile_service import UserProfileService, UserBusinessProfile

logger = logging.getLogger(__name__)

@dataclass
class ProductClassificationData:
    """Product classification data for a specific business type and location"""
    country: str
    industry: str
    common_brands: List[str]
    product_categories: Dict[str, List[str]]  # category -> subcategories
    size_patterns: List[str]  # Common size patterns for this industry
    keywords: Dict[str, List[str]]  # category -> keywords to look for
    confidence_boosters: List[str]  # Words that increase confidence

class DynamicProductClassifier:
    """
    Dynamic product classifier that adapts to user's business type and location
    """
    
    def __init__(self, data_dir: str = "data/product_classifications"):
        self.data_dir = data_dir
        self.user_profile_service = UserProfileService()
        self._ensure_classification_files()
        self._classification_cache = {}
        
    def _ensure_classification_files(self):
        """Ensure classification files exist for common business types"""
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Create default classification files if they don't exist
        default_classifications = self._get_default_classifications()
        
        for key, data in default_classifications.items():
            file_path = os.path.join(self.data_dir, f"{key}.json")
            if not os.path.exists(file_path):
                self._save_classification_file(key, data)
    
    def get_classification_for_user(self, user_id: str) -> Optional[ProductClassificationData]:
        """Get product classification data for a specific user"""
        try:
            # Get user profile
            profile = self.user_profile_service.get_user_profile(user_id)
            if not profile:
                logger.warning(f"No profile found for user {user_id}, using default grocery classification")
                return self._get_default_grocery_classification()
            
            # Create classification key
            classification_key = f"{profile.country}_{profile.industry}"
            
            # Check cache first
            if classification_key in self._classification_cache:
                return self._classification_cache[classification_key]
            
            # Load from file
            classification = self._load_classification_file(classification_key)
            if not classification:
                # Fall back to country-generic classification
                classification = self._load_classification_file(f"generic_{profile.industry}")
                if not classification:
                    # Final fallback
                    classification = self._get_default_grocery_classification()
            
            # Add user's custom brands if available
            if profile.custom_brands:
                classification.common_brands.extend(profile.custom_brands)
            
            # Cache the result
            self._classification_cache[classification_key] = classification
            
            logger.info(f"Loaded classification for user {user_id}: {profile.country}_{profile.industry}")
            return classification
            
        except Exception as e:
            logger.error(f"Error getting classification for user {user_id}: {e}")
            return self._get_default_grocery_classification()
    
    def enhance_vision_result(self, vision_result: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Enhance vision processing result with business-specific context"""
        try:
            classification = self.get_classification_for_user(user_id)
            if not classification:
                return vision_result
            
            enhanced_result = vision_result.copy()
            
            # Extract text from vision result for analysis
            detected_text = self._extract_text_from_vision_result(vision_result)
            
            # Enhance title
            enhanced_result['title'] = self._enhance_title(detected_text, classification)
            
            # Enhance brand detection
            enhanced_result['brand'] = self._enhance_brand(detected_text, classification, enhanced_result)
            
            # Enhance size and unit detection
            size_info = self._enhance_size_unit(detected_text, classification)
            enhanced_result['size'] = size_info['size']
            enhanced_result['unit'] = size_info['unit']
            
            # Enhance category classification
            category_info = self._enhance_category(detected_text, enhanced_result['title'], classification)
            enhanced_result['category'] = category_info['category']
            enhanced_result['subcategory'] = category_info['subcategory']
            
            # Enhance confidence based on business context
            enhanced_result['confidence'] = self._calculate_enhanced_confidence(
                enhanced_result, classification, detected_text
            )
            
            # Add detection method info
            enhanced_result['detection_method'] = 'dynamic_business_context'
            enhanced_result['business_context'] = {
                'country': classification.country,
                'industry': classification.industry
            }
            
            logger.info(f"Enhanced vision result for {classification.industry} business in {classification.country}")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Error enhancing vision result: {e}")
            return vision_result
    
    def _extract_text_from_vision_result(self, vision_result: Dict[str, Any]) -> str:
        """Extract all detected text from vision result"""
        text_parts = []
        
        # Add raw text (highest priority - comprehensive OCR result)
        if vision_result.get('raw_text'):
            text_parts.append(vision_result['raw_text'])
        
        # Add title
        if vision_result.get('title'):
            text_parts.append(vision_result['title'])
        
        # Add web entities (brand hints)
        if vision_result.get('web_entities'):
            text_parts.extend(vision_result['web_entities'])
        
        # Add logo descriptions (brand hints)
        if vision_result.get('logo_descriptions'):
            text_parts.extend(vision_result['logo_descriptions'])
        
        # Add detected labels (category hints)
        if vision_result.get('detected_labels'):
            text_parts.extend(vision_result['detected_labels'])
        
        # Add description
        if vision_result.get('description'):
            text_parts.append(vision_result['description'])
        
        return ' '.join(text_parts).lower()
    
    def _enhance_title(self, detected_text: str, classification: ProductClassificationData) -> str:
        """Enhance product title using business context"""
        # Look for brand names in the text
        for brand in classification.common_brands:
            if brand.lower() in detected_text:
                # Try to extract a more complete title around the brand
                words = detected_text.split()
                brand_words = brand.lower().split()
                
                for i, word in enumerate(words):
                    if word in brand_words:
                        # Extract surrounding context
                        start = max(0, i - 2)
                        end = min(len(words), i + len(brand_words) + 3)
                        title_words = words[start:end]
                        return ' '.join(title_words).title()
        
        # Fall back to first meaningful text segment
        words = detected_text.split()
        if len(words) > 0:
            return ' '.join(words[:4]).title()
        
        return "Unknown Product"
    
    def _enhance_brand(self, detected_text: str, classification: ProductClassificationData, vision_result: Optional[Dict[str, Any]] = None) -> str:
        """Enhance brand detection using business context and Vision API data"""
        
        # Priority 1: Logo descriptions from Vision API (highest confidence)
        if vision_result and vision_result.get('logo_descriptions'):
            for logo_desc in vision_result['logo_descriptions']:
                for brand in classification.common_brands:
                    if brand.lower() in logo_desc.lower() or logo_desc.lower() in brand.lower():
                        return brand
        
        # Priority 2: Web entities from Vision API (very reliable)
        if vision_result and vision_result.get('web_entities'):
            for entity in vision_result['web_entities']:
                for brand in classification.common_brands:
                    if brand.lower() in entity.lower() or entity.lower() in brand.lower():
                        return brand
        
        # Priority 3: Text-based detection in raw OCR
        for brand in classification.common_brands:
            if brand.lower() in detected_text:
                return brand
        
        # Priority 4: Fuzzy matching for partial brand names
        for brand in classification.common_brands:
            brand_words = brand.lower().split()
            if len(brand_words) > 1:  # Multi-word brands
                if any(word in detected_text for word in brand_words if len(word) > 3):
                    return brand
        
        return ""
    
    def _enhance_size_unit(self, detected_text: str, classification: ProductClassificationData) -> Dict[str, str]:
        """Enhance size and unit detection using business context"""
        import re
        
        # Look for size patterns specific to this business type
        for pattern in classification.size_patterns:
            match = re.search(pattern, detected_text, re.IGNORECASE)
            if match:
                if len(match.groups()) >= 2:
                    return {"size": match.group(1), "unit": match.group(2)}
                elif len(match.groups()) == 1:
                    # Try to split number and unit
                    size_text = match.group(1)
                    size_match = re.match(r'(\d+(?:\.\d+)?)\s*([a-zA-Z]+)', size_text)
                    if size_match:
                        return {"size": size_match.group(1), "unit": size_match.group(2)}
        
        # Generic size pattern fallback
        size_match = re.search(r'(\d+(?:\.\d+)?)\s*(ml|l|kg|g|oz|lbs|liters?|litres?|grams?|kilograms?)', detected_text, re.IGNORECASE)
        if size_match:
            return {"size": size_match.group(1), "unit": size_match.group(2).lower()}
        
        return {"size": "", "unit": ""}
    
    def _enhance_category(self, detected_text: str, title: str, classification: ProductClassificationData) -> Dict[str, str]:
        """Enhance category classification using business context"""
        
        combined_text = f"{detected_text} {title.lower()}"
        
        # Check keywords for each category
        best_category = "General"
        best_subcategory = "Miscellaneous"
        max_matches = 0
        
        for category, keywords in classification.keywords.items():
            matches = sum(1 for keyword in keywords if keyword.lower() in combined_text)
            if matches > max_matches:
                max_matches = matches
                best_category = category
                
                # Find subcategory
                subcategories = classification.product_categories.get(category, [])
                for subcategory in subcategories:
                    if subcategory.lower() in combined_text:
                        best_subcategory = subcategory
                        break
                else:
                    best_subcategory = subcategories[0] if subcategories else "Miscellaneous"
        
        return {"category": best_category, "subcategory": best_subcategory}
    
    def _calculate_enhanced_confidence(self, enhanced_result: Dict[str, Any], 
                                     classification: ProductClassificationData, 
                                     detected_text: str) -> float:
        """Calculate enhanced confidence based on business context"""
        base_confidence = enhanced_result.get('confidence', 0.5)
        
        # Boost confidence based on context matches
        confidence_boost = 0.0
        
        # Brand match boost
        if enhanced_result.get('brand'):
            confidence_boost += 0.2
        
        # Size detection boost
        if enhanced_result.get('size') and enhanced_result.get('unit'):
            confidence_boost += 0.1
        
        # Category match boost
        if enhanced_result.get('category') != "General":
            confidence_boost += 0.1
        
        # Business-specific confidence boosters
        booster_matches = sum(1 for booster in classification.confidence_boosters 
                            if booster.lower() in detected_text)
        confidence_boost += min(booster_matches * 0.05, 0.15)
        
        # Ensure confidence stays within bounds
        final_confidence = min(1.0, base_confidence + confidence_boost)
        return round(final_confidence, 2)
    
    def _load_classification_file(self, classification_key: str) -> Optional[ProductClassificationData]:
        """Load classification data from file"""
        try:
            file_path = os.path.join(self.data_dir, f"{classification_key}.json")
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                return ProductClassificationData(**data)
        except Exception as e:
            logger.error(f"Error loading classification file {classification_key}: {e}")
        return None
    
    def _save_classification_file(self, classification_key: str, data: ProductClassificationData):
        """Save classification data to file"""
        try:
            file_path = os.path.join(self.data_dir, f"{classification_key}.json")
            with open(file_path, 'w') as f:
                json.dump(data.__dict__, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving classification file {classification_key}: {e}")
    
    def _get_default_classifications(self) -> Dict[str, ProductClassificationData]:
        """Get default classification data for common business types"""
        return {
            "zimbabwe_grocery": ProductClassificationData(
                country="Zimbabwe",
                industry="grocery",
                common_brands=[
                    "Gold Leaf", "Blue Ribbon", "Lobels", "Delta", "Dairibord", "Mazoe", 
                    "Tanganda", "Cairns", "Olivine", "Tongaat Hulett", "Coca Cola", 
                    "Pepsi", "Fanta", "Sprite", "Lake Harvest", "Kapenta"
                ],
                product_categories={
                    "Beverages": ["Soft Drinks", "Juices", "Water", "Alcoholic", "Energy Drinks"],
                    "Dairy": ["Milk", "Cheese", "Yogurt", "Butter", "Cream"],
                    "Staples": ["Mealie Meal", "Rice", "Sugar", "Salt", "Flour"],
                    "Cooking Essentials": ["Oil", "Spices", "Sauces", "Vinegar"],
                    "Snacks": ["Chips", "Biscuits", "Sweets", "Nuts"],
                    "Bakery": ["Bread", "Cakes", "Pastries"],
                    "Protein": ["Meat", "Fish", "Eggs", "Beans"],
                    "Personal Care": ["Soap", "Shampoo", "Toothpaste", "Lotion"],
                    "Household": ["Detergent", "Toilet Paper", "Cleaning Supplies"]
                },
                size_patterns=[
                    r'(\d+(?:\.\d+)?)\s*(ml|l|liters?|litres?)',
                    r'(\d+(?:\.\d+)?)\s*(kg|g|grams?|kilograms?)',
                    r'(\d+(?:\.\d+)?)\s*(oz|lbs|pounds?)',
                    r'(\d+)\s*pack',
                    r'(\d+)\s*pieces?'
                ],
                keywords={
                    "Beverages": ["drink", "juice", "soda", "water", "beer", "wine", "coke", "pepsi", "fanta"],
                    "Dairy": ["milk", "cheese", "yogurt", "butter", "cream", "dairibord"],
                    "Staples": ["mealie", "meal", "rice", "sugar", "salt", "flour", "grain"],
                    "Cooking Essentials": ["oil", "cooking", "olivine", "sauce", "spice"],
                    "Snacks": ["chips", "biscuit", "sweet", "candy", "nuts", "snack"],
                    "Bakery": ["bread", "loaf", "cake", "lobels", "bakery"],
                    "Protein": ["meat", "fish", "matemba", "chicken", "beef", "egg"],
                    "Personal Care": ["soap", "shampoo", "toothpaste", "lotion", "cream"],
                    "Household": ["detergent", "toilet", "paper", "cleaning", "wash"]
                },
                confidence_boosters=["zimbabwe", "harare", "bulawayo", "local", "imported"]
            ),
            
            "generic_grocery": ProductClassificationData(
                country="Generic",
                industry="grocery",
                common_brands=["Coca Cola", "Pepsi", "Nestle", "Unilever", "P&G"],
                product_categories={
                    "Beverages": ["Soft Drinks", "Juices", "Water", "Energy Drinks"],
                    "Dairy": ["Milk", "Cheese", "Yogurt", "Butter"],
                    "Staples": ["Rice", "Sugar", "Salt", "Flour", "Pasta"],
                    "Snacks": ["Chips", "Cookies", "Candy", "Nuts"],
                    "Personal Care": ["Soap", "Shampoo", "Toothpaste"],
                    "Household": ["Detergent", "Paper Products", "Cleaning"]
                },
                size_patterns=[
                    r'(\d+(?:\.\d+)?)\s*(ml|l|oz|fl\.?\s*oz)',
                    r'(\d+(?:\.\d+)?)\s*(kg|g|lbs|oz)'
                ],
                keywords={
                    "Beverages": ["drink", "juice", "soda", "water", "coke", "pepsi"],
                    "Dairy": ["milk", "cheese", "yogurt", "butter"],
                    "Staples": ["rice", "sugar", "salt", "flour", "pasta"],
                    "Snacks": ["chips", "cookie", "candy", "nuts", "snack"],
                    "Personal Care": ["soap", "shampoo", "toothpaste"],
                    "Household": ["detergent", "paper", "cleaning", "wash"]
                },
                confidence_boosters=["organic", "fresh", "premium", "natural"]
            ),
            
            "generic_pharmacy": ProductClassificationData(
                country="Generic",
                industry="pharmacy",
                common_brands=["Johnson & Johnson", "Pfizer", "Bayer", "GSK", "Roche"],
                product_categories={
                    "Medications": ["Pain Relief", "Cold & Flu", "Antibiotics", "Vitamins"],
                    "Personal Care": ["Skincare", "Hair Care", "Oral Care", "Body Care"],
                    "Health Supplements": ["Vitamins", "Minerals", "Protein", "Herbal"],
                    "Medical Supplies": ["Bandages", "Thermometers", "First Aid"],
                    "Baby Care": ["Diapers", "Formula", "Baby Food", "Lotions"]
                },
                size_patterns=[
                    r'(\d+)\s*tablets?',
                    r'(\d+)\s*capsules?',
                    r'(\d+(?:\.\d+)?)\s*(ml|mg|g)',
                    r'(\d+)\s*pieces?'
                ],
                keywords={
                    "Medications": ["tablet", "capsule", "syrup", "medicine", "drug", "pain", "relief"],
                    "Personal Care": ["cream", "lotion", "shampoo", "soap", "toothpaste"],
                    "Health Supplements": ["vitamin", "supplement", "mineral", "protein", "herbal"],
                    "Medical Supplies": ["bandage", "thermometer", "first aid", "gauze"],
                    "Baby Care": ["baby", "diaper", "formula", "infant", "newborn"]
                },
                confidence_boosters=["pharmaceutical", "medical", "health", "clinical", "approved"]
            )
        }
    
    def _get_default_grocery_classification(self) -> ProductClassificationData:
        """Get default grocery classification as fallback"""
        return self._get_default_classifications()["generic_grocery"]
    
    def create_user_classification(self, user_id: str, country: str, industry: str, 
                                 custom_brands: Optional[List[str]] = None) -> bool:
        """Create a custom classification for a user"""
        try:
            # Create user profile
            profile = UserBusinessProfile(
                user_id=user_id,
                country=country,
                industry=industry,
                product_categories=[],  # Will be filled from classification
                business_size="small",  # Default
                custom_brands=custom_brands or []
            )
            
            # Save profile
            return self.user_profile_service.save_user_profile(profile)
            
        except Exception as e:
            logger.error(f"Error creating user classification: {e}")
            return False
