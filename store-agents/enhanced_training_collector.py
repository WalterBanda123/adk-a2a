#!/usr/bin/env python3
"""
Enhanced Training Data Collection System
Focus on pattern-based product recognition for Zimbabwe retail products
"""
import os
import csv
import json
import logging
import base64
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class ZimbabweProductPatternExtractor:
    """Extract product information using Zimbabwe-specific patterns"""
    
    def __init__(self):
        self.zimbabwe_brands = {
            'mazoe': {
                'products': ['orange_crush', 'raspberry', 'lemon', 'ginger'],
                'sizes': ['330ml', '500ml', '2l', '5l'],
                'patterns': [r'mazoe.*orange', r'mazoe.*raspberry', r'mazoe.*lemon'],
                'category': 'beverages',
                'subcategory': 'concentrates'
            },
            'huletts': {
                'products': ['white_sugar', 'brown_sugar', 'castor_sugar'],
                'sizes': ['500g', '1kg', '2kg', '5kg'],
                'patterns': [r'huletts.*sugar', r'huletts.*brown', r'huletts.*white'],
                'category': 'food',
                'subcategory': 'staples'
            },
            'baker_inn': {
                'products': ['white_bread', 'brown_bread', 'whole_grain'],
                'sizes': ['600g', '700g', '800g'],
                'patterns': [r'baker.?inn.*bread', r'baker.?inn.*brown', r'baker.?inn.*white'],
                'category': 'food',
                'subcategory': 'bakery'
            },
            'dairibord': {
                'products': ['milk', 'yogurt', 'cheese', 'butter'],
                'sizes': ['500ml', '1l', '2l'],
                'patterns': [r'dairibord.*milk', r'dairibord.*yogurt'],
                'category': 'food',
                'subcategory': 'dairy'
            },
            'tanganda': {
                'products': ['tea', 'rooibos', 'green_tea'],
                'sizes': ['100g', '250g', '500g'],
                'patterns': [r'tanganda.*tea', r'tanganda.*rooibos'],
                'category': 'beverages',
                'subcategory': 'hot_drinks'
            },
            'coca_cola': {
                'products': ['classic', 'diet', 'zero'],
                'sizes': ['330ml', '500ml', '1l', '2l'],
                'patterns': [r'coca.?cola', r'coke'],
                'category': 'beverages',
                'subcategory': 'soft_drinks'
            },
            'pepsi': {
                'products': ['classic', 'diet', 'max'],
                'sizes': ['330ml', '500ml', '1l', '2l'],
                'patterns': [r'pepsi'],
                'category': 'beverages',
                'subcategory': 'soft_drinks'
            }
        }
        
        self.size_patterns = [
            r'(\d+(?:\.\d+)?)\s*(ml|l|liters?|litres?)',
            r'(\d+(?:\.\d+)?)\s*(g|kg|grams?|kilos?)',
            r'(\d+)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*(ml|l|g|kg)'
        ]
        
    def extract_pattern_based_info(self, text: str) -> Dict[str, Any]:
        """Extract product info using Zimbabwe-specific patterns"""
        text_lower = text.lower().strip()
        
        result = {
            'brand': '',
            'product_name': '',
            'category': 'general',
            'subcategory': 'unknown',
            'size': '',
            'unit': '',
            'variant': '',
            'confidence': 0.0,
            'pattern_matches': []
        }
        
        # Brand and product detection
        for brand, brand_info in self.zimbabwe_brands.items():
            # Check if brand name appears in text
            if brand.replace('_', ' ') in text_lower or brand.replace('_', '') in text_lower:
                result['brand'] = brand
                result['category'] = brand_info['category']
                result['subcategory'] = brand_info['subcategory']
                result['confidence'] += 0.4
                result['pattern_matches'].append(f'brand:{brand}')
                
                # Check for specific product patterns
                for pattern in brand_info['patterns']:
                    if re.search(pattern, text_lower):
                        result['confidence'] += 0.3
                        result['pattern_matches'].append(f'pattern:{pattern}')
                        
                        # Extract product type from pattern
                        for product in brand_info['products']:
                            if product.replace('_', ' ') in text_lower:
                                result['variant'] = product
                                result['confidence'] += 0.2
                                result['pattern_matches'].append(f'product:{product}')
                                break
                break
        
        # Size extraction
        size_info = self._extract_size_pattern(text_lower)
        if size_info:
            result['size'] = size_info['size']
            result['unit'] = size_info['unit']
            result['confidence'] += 0.1
            result['pattern_matches'].append(f'size:{size_info["size"]}{size_info["unit"]}')
        
        # Generate product name using pattern
        result['product_name'] = self._generate_pattern_product_name(result)
        
        return result
    
    def _extract_size_pattern(self, text: str) -> Optional[Dict[str, str]]:
        """Extract size using patterns"""
        for pattern in self.size_patterns:
            matches = re.findall(pattern, text)
            if matches:
                match = matches[0]
                if len(match) == 3:  # Multi-pack format
                    return {'size': f"{match[0]}x{match[1]}", 'unit': match[2]}
                elif len(match) == 2:  # Single size
                    return {'size': str(match[0]), 'unit': match[1]}
        return None
    
    def _generate_pattern_product_name(self, info: Dict[str, Any]) -> str:
        """Generate standardized product name using patterns"""
        parts = []
        
        if info['brand']:
            parts.append(info['brand'].replace('_', ' ').title())
        
        if info['variant']:
            parts.append(info['variant'].replace('_', ' ').title())
        
        if info['size'] and info['unit']:
            parts.append(f"{info['size']}{info['unit']}")
        
        if not parts:
            return "Unknown Product"
        
        return " ".join(parts)

class TrainingDataCollector:
    """Collect and organize training data with pattern-based labeling"""
    
    def __init__(self, training_dir: str = "training_data"):
        self.training_dir = Path(training_dir)
        self.pattern_extractor = ZimbabweProductPatternExtractor()
        self.labels_file = self.training_dir / "labels" / "training_labels.csv"
        
        # Ensure directories exist
        (self.training_dir / "labels").mkdir(parents=True, exist_ok=True)
        
        # Initialize CSV file if it doesn't exist
        if not self.labels_file.exists():
            self._initialize_csv()
    
    def _initialize_csv(self):
        """Initialize the training labels CSV file"""
        headers = [
            'image_path', 'image_filename', 'brand', 'product_name', 
            'category', 'subcategory', 'size', 'unit', 'variant',
            'confidence', 'pattern_matches', 'created_date', 'verified'
        ]
        
        with open(self.labels_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
        
        logger.info(f"✅ Initialized training labels CSV: {self.labels_file}")
    
    def add_training_image(self, image_path: str, detected_text: str = "", 
                          manual_override: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Add a new training image with pattern-based labeling"""
        
        image_path_obj = Path(image_path)
        if not image_path_obj.exists():
            return {"success": False, "error": f"Image not found: {image_path}"}
        
        # Extract information using patterns
        if detected_text:
            extracted_info = self.pattern_extractor.extract_pattern_based_info(detected_text)
        else:
            # If no text provided, try to extract from filename
            filename_text = image_path_obj.stem.replace('_', ' ').replace('-', ' ')
            extracted_info = self.pattern_extractor.extract_pattern_based_info(filename_text)
        
        # Apply manual overrides
        if manual_override:
            extracted_info.update(manual_override)
        
        # Determine relative path for CSV
        try:
            relative_path = image_path_obj.relative_to(self.training_dir)
        except ValueError:
            relative_path = image_path_obj
        
        # Add to CSV
        row_data = [
            str(relative_path),
            image_path_obj.name,
            extracted_info['brand'],
            extracted_info['product_name'],
            extracted_info['category'],
            extracted_info['subcategory'],
            extracted_info['size'],
            extracted_info['unit'],
            extracted_info['variant'],
            extracted_info['confidence'],
            ';'.join(extracted_info['pattern_matches']),
            str(datetime.now().date()),
            'no'  # needs verification
        ]
        
        with open(self.labels_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row_data)
        
        logger.info(f"✅ Added training data: {extracted_info['product_name']} (confidence: {extracted_info['confidence']:.2f})")
        
        return {
            "success": True,
            "extracted_info": extracted_info,
            "image_path": str(relative_path)
        }
    
    def scan_training_directory(self) -> Dict[str, Any]:
        """Scan training directory and auto-label images"""
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
        images_dir = self.training_dir / "images"
        
        if not images_dir.exists():
            return {"success": False, "error": "Images directory not found"}
        
        processed = 0
        skipped = 0
        errors = []
        
        # Get existing entries to avoid duplicates
        existing_images = set()
        if self.labels_file.exists():
            with open(self.labels_file, 'r') as f:
                reader = csv.DictReader(f)
                existing_images = {row['image_filename'] for row in reader}
        
        # Scan all image files
        for image_file in images_dir.rglob('*'):
            if image_file.suffix.lower() in image_extensions:
                if image_file.name in existing_images:
                    skipped += 1
                    continue
                
                try:
                    # Extract text from filename for pattern matching
                    filename_text = image_file.stem.replace('_', ' ').replace('-', ' ')
                    result = self.add_training_image(str(image_file), filename_text)
                    
                    if result['success']:
                        processed += 1
                    else:
                        errors.append(f"{image_file.name}: {result['error']}")
                        
                except Exception as e:
                    errors.append(f"{image_file.name}: {str(e)}")
        
        return {
            "success": True,
            "processed": processed,
            "skipped": skipped,
            "errors": errors,
            "total_images": processed + skipped
        }
    
    def get_training_statistics(self) -> Dict[str, Any]:
        """Get statistics about the training data"""
        
        if not self.labels_file.exists():
            return {"success": False, "error": "No training data found"}
        
        stats = {
            "total_images": 0,
            "brands": {},
            "categories": {},
            "confidence_distribution": {"high": 0, "medium": 0, "low": 0},
            "verified": 0,
            "needs_verification": 0
        }
        
        with open(self.labels_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                stats["total_images"] += 1
                
                # Brand distribution
                brand = row['brand']
                stats["brands"][brand] = stats["brands"].get(brand, 0) + 1
                
                # Category distribution
                category = row['category']
                stats["categories"][category] = stats["categories"].get(category, 0) + 1
                
                # Confidence distribution
                try:
                    confidence = float(row['confidence'])
                    if confidence >= 0.8:
                        stats["confidence_distribution"]["high"] += 1
                    elif confidence >= 0.6:
                        stats["confidence_distribution"]["medium"] += 1
                    else:
                        stats["confidence_distribution"]["low"] += 1
                except:
                    stats["confidence_distribution"]["low"] += 1
                
                # Verification status
                if row['verified'].lower() == 'yes':
                    stats["verified"] += 1
                else:
                    stats["needs_verification"] += 1
        
        return {"success": True, "statistics": stats}

def main():
    """Main function to demonstrate the training data collection system"""
    
    print("🏷️ Enhanced Training Data Collection System")
    print("=" * 60)
    
    # Initialize collector
    collector = TrainingDataCollector()
    
    # Scan existing images in training directory
    print("📁 Scanning training directory for images...")
    scan_result = collector.scan_training_directory()
    
    if scan_result['success']:
        print(f"✅ Processed: {scan_result['processed']} images")
        print(f"⏭️ Skipped: {scan_result['skipped']} images (already labeled)")
        print(f"📊 Total images: {scan_result['total_images']}")
        
        if scan_result['errors']:
            print(f"⚠️ Errors: {len(scan_result['errors'])}")
            for error in scan_result['errors'][:5]:  # Show first 5 errors
                print(f"   • {error}")
    else:
        print(f"❌ Scan failed: {scan_result['error']}")
    
    # Get training statistics
    print("\n📊 Training Data Statistics:")
    stats_result = collector.get_training_statistics()
    
    if stats_result['success']:
        stats = stats_result['statistics']
        print(f"   Total Images: {stats['total_images']}")
        print(f"   Verified: {stats['verified']}")
        print(f"   Needs Verification: {stats['needs_verification']}")
        
        print("\n🏷️ Brand Distribution:")
        for brand, count in sorted(stats['brands'].items()):
            print(f"   • {brand}: {count} images")
        
        print("\n📂 Category Distribution:")
        for category, count in sorted(stats['categories'].items()):
            print(f"   • {category}: {count} images")
        
        print("\n🎯 Confidence Distribution:")
        conf_dist = stats['confidence_distribution']
        print(f"   • High (≥0.8): {conf_dist['high']} images")
        print(f"   • Medium (0.6-0.8): {conf_dist['medium']} images")
        print(f"   • Low (<0.6): {conf_dist['low']} images")
    
    print("\n" + "=" * 60)
    print("🎯 Next Steps:")
    print("   1. Add more product images to training_data/images/")
    print("   2. Review and verify labels in training_data/labels/training_labels.csv")
    print("   3. Focus on low-confidence entries for manual review")
    print("   4. Aim for 100+ verified images before training")

if __name__ == "__main__":
    main()
