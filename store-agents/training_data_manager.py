#!/usr/bin/env python3
"""
Training Data Management System
Manage, verify, and enhance training data for Zimbabwe retail product recognition
"""
import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class TrainingDataManager:
    """Manage training data with verification and enhancement features"""
    
    def __init__(self, training_dir: str = "training_data"):
        self.training_dir = Path(training_dir)
        self.labels_file = self.training_dir / "labels" / "training_labels.csv"
        self.verified_file = self.training_dir / "labels" / "verified_labels.csv"
        
        # Zimbabwe product knowledge base
        self.zimbabwe_products = {
            'mazoe': {
                'variants': ['orange_crush', 'raspberry', 'lemon', 'ginger'],
                'common_sizes': ['330ml', '500ml', '2l', '5l'],
                'category': 'beverages',
                'subcategory': 'concentrates'
            },
            'huletts': {
                'variants': ['white_sugar', 'brown_sugar', 'castor_sugar', 'icing_sugar'],
                'common_sizes': ['500g', '1kg', '2kg', '5kg'],
                'category': 'food',
                'subcategory': 'staples'
            },
            'baker_inn': {
                'variants': ['white_bread', 'brown_bread', 'whole_grain', 'sandwich'],
                'common_sizes': ['600g', '700g', '800g'],
                'category': 'food',
                'subcategory': 'bakery'
            },
            'coca_cola': {
                'variants': ['classic', 'diet', 'zero', 'cherry'],
                'common_sizes': ['330ml', '500ml', '1l', '2l'],
                'category': 'beverages',
                'subcategory': 'soft_drinks'
            },
            'dairibord': {
                'variants': ['full_cream_milk', 'low_fat_milk', 'yogurt', 'cheese'],
                'common_sizes': ['500ml', '1l', '2l'],
                'category': 'food',
                'subcategory': 'dairy'
            }
        }
    
    def review_and_verify_data(self, interactive: bool = True) -> Dict[str, Any]:
        """Review training data and mark as verified"""
        
        if not self.labels_file.exists():
            return {"success": False, "error": "No training data found"}
        
        # Read unverified data
        unverified_data = []
        with open(self.labels_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['verified'].lower() != 'yes':
                    unverified_data.append(row)
        
        if not unverified_data:
            return {"success": True, "message": "All data is already verified"}
        
        print(f"📋 Found {len(unverified_data)} unverified entries")
        
        verified_count = 0
        corrected_count = 0
        
        for i, item in enumerate(unverified_data):
            print(f"\n--- Entry {i+1}/{len(unverified_data)} ---")
            print(f"📷 Image: {item['image_filename']}")
            print(f"🏷️ Brand: {item['brand']}")
            print(f"📦 Product: {item['product_name']}")
            print(f"📂 Category: {item['category']} → {item['subcategory']}")
            print(f"📏 Size: {item['size']} {item['unit']}")
            print(f"🎯 Confidence: {float(item['confidence']):.2f}")
            print(f"🔍 Patterns: {item['pattern_matches']}")
            
            if interactive:
                action = input("\nAction: (y)es verify, (c)orrect, (s)kip, (q)uit: ").lower().strip()
                
                if action == 'q':
                    break
                elif action == 's':
                    continue
                elif action == 'c':
                    # Allow corrections
                    corrected_item = self._correct_item(item)
                    if corrected_item:
                        self._update_item_in_csv(item['image_filename'], corrected_item)
                        corrected_count += 1
                        verified_count += 1
                elif action == 'y':
                    # Mark as verified
                    item['verified'] = 'yes'
                    self._update_item_in_csv(item['image_filename'], item)
                    verified_count += 1
            else:
                # Auto-verify high confidence items
                if float(item['confidence']) >= 0.8 and self._validate_against_knowledge_base(item):
                    item['verified'] = 'yes'
                    self._update_item_in_csv(item['image_filename'], item)
                    verified_count += 1
        
        return {
            "success": True,
            "verified": verified_count,
            "corrected": corrected_count,
            "total_reviewed": len(unverified_data)
        }
    
    def _correct_item(self, item: Dict[str, str]) -> Dict[str, str]:
        """Allow user to correct an item"""
        
        print("\n🔧 Correction Mode:")
        corrected = item.copy()
        
        # Suggest corrections based on knowledge base
        if item['brand'] in self.zimbabwe_products:
            product_info = self.zimbabwe_products[item['brand']]
            print(f"💡 Suggestions for {item['brand']}:")
            print(f"   Variants: {', '.join(product_info['variants'])}")
            print(f"   Sizes: {', '.join(product_info['common_sizes'])}")
        
        fields_to_correct = ['brand', 'product_name', 'category', 'subcategory', 'size', 'unit', 'variant']
        
        for field in fields_to_correct:
            current_value = item.get(field, '')
            new_value = input(f"{field} [{current_value}]: ").strip()
            if new_value:
                corrected[field] = new_value
        
        # Regenerate product name if needed
        if corrected['brand'] and corrected['variant']:
            if corrected['size'] and corrected['unit']:
                corrected['product_name'] = f"{corrected['brand'].title()} {corrected['variant'].replace('_', ' ').title()} {corrected['size']}{corrected['unit']}"
            else:
                corrected['product_name'] = f"{corrected['brand'].title()} {corrected['variant'].replace('_', ' ').title()}"
        
        corrected['verified'] = 'yes'
        return corrected
    
    def _validate_against_knowledge_base(self, item: Dict[str, str]) -> bool:
        """Validate item against Zimbabwe product knowledge base"""
        
        brand = item['brand']
        if brand not in self.zimbabwe_products:
            return False
        
        product_info = self.zimbabwe_products[brand]
        
        # Check category
        if item['category'] != product_info['category']:
            return False
        
        # Check variant if provided
        if item['variant'] and item['variant'] not in product_info['variants']:
            return False
        
        # Check size if provided
        if item['size'] and item['unit']:
            size_str = f"{item['size']}{item['unit']}"
            if size_str not in product_info['common_sizes']:
                return False
        
        return True
    
    def _update_item_in_csv(self, image_filename: str, updated_item: Dict[str, str]):
        """Update a specific item in the CSV"""
        
        # Read all data
        all_data = []
        fieldnames = None
        with open(self.labels_file, 'r') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                if row['image_filename'] == image_filename:
                    all_data.append(updated_item)
                else:
                    all_data.append(row)
        
        # Write back
        if fieldnames:
            with open(self.labels_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_data)
    
    def export_verified_data(self) -> Dict[str, Any]:
        """Export only verified data for training"""
        
        if not self.labels_file.exists():
            return {"success": False, "error": "No training data found"}
        
        verified_data = []
        with open(self.labels_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['verified'].lower() == 'yes':
                    verified_data.append(row)
        
        if not verified_data:
            return {"success": False, "error": "No verified data found"}
        
        # Write verified data to separate file
        with open(self.verified_file, 'w', newline='') as f:
            if verified_data:
                writer = csv.DictWriter(f, fieldnames=verified_data[0].keys())
                writer.writeheader()
                writer.writerows(verified_data)
        
        return {
            "success": True,
            "verified_count": len(verified_data),
            "export_file": str(self.verified_file)
        }
    
    def generate_training_report(self) -> Dict[str, Any]:
        """Generate comprehensive training data report"""
        
        if not self.labels_file.exists():
            return {"success": False, "error": "No training data found"}
        
        all_data = []
        with open(self.labels_file, 'r') as f:
            reader = csv.DictReader(f)
            all_data = list(reader)
        
        # Statistics
        total_images = len(all_data)
        verified_images = sum(1 for item in all_data if item['verified'].lower() == 'yes')
        
        # Brand distribution
        brands = {}
        categories = {}
        confidence_ranges = {"high": 0, "medium": 0, "low": 0}
        
        for item in all_data:
            # Brand distribution
            brand = item['brand']
            brands[brand] = brands.get(brand, 0) + 1
            
            # Category distribution
            category = item['category']
            categories[category] = categories.get(category, 0) + 1
            
            # Confidence distribution
            try:
                confidence = float(item['confidence'])
                if confidence >= 0.8:
                    confidence_ranges["high"] += 1
                elif confidence >= 0.6:
                    confidence_ranges["medium"] += 1
                else:
                    confidence_ranges["low"] += 1
            except:
                confidence_ranges["low"] += 1
        
        # Readiness assessment
        readiness_score = 0
        readiness_notes = []
        
        if verified_images >= 100:
            readiness_score += 40
            readiness_notes.append("✅ Sufficient verified images (100+)")
        elif verified_images >= 50:
            readiness_score += 25
            readiness_notes.append("⚠️ Moderate verified images (50+), aim for 100+")
        else:
            readiness_notes.append("❌ Insufficient verified images (<50)")
        
        if len(brands) >= 5:
            readiness_score += 30
            readiness_notes.append("✅ Good brand diversity (5+ brands)")
        else:
            readiness_notes.append(f"⚠️ Limited brand diversity ({len(brands)} brands)")
        
        if confidence_ranges["high"] / total_images >= 0.7:
            readiness_score += 30
            readiness_notes.append("✅ High quality data (70%+ high confidence)")
        else:
            readiness_notes.append("⚠️ Consider improving data quality")
        
        return {
            "success": True,
            "statistics": {
                "total_images": total_images,
                "verified_images": verified_images,
                "verification_rate": verified_images / total_images if total_images > 0 else 0,
                "brands": brands,
                "categories": categories,
                "confidence_distribution": confidence_ranges
            },
            "readiness": {
                "score": readiness_score,
                "max_score": 100,
                "ready_for_training": readiness_score >= 70,
                "notes": readiness_notes
            }
        }

def main():
    """Main function"""
    
    print("📊 Training Data Management System")
    print("=" * 50)
    
    manager = TrainingDataManager()
    
    # Generate report
    report = manager.generate_training_report()
    
    if report['success']:
        stats = report['statistics']
        readiness = report['readiness']
        
        print("📈 Training Data Statistics:")
        print(f"   Total Images: {stats['total_images']}")
        print(f"   Verified Images: {stats['verified_images']}")
        print(f"   Verification Rate: {stats['verification_rate']:.1%}")
        
        print("\n🏷️ Brand Distribution:")
        for brand, count in sorted(stats['brands'].items()):
            print(f"   • {brand}: {count} images")
        
        print("\n📂 Category Distribution:")
        for category, count in sorted(stats['categories'].items()):
            print(f"   • {category}: {count} images")
        
        print(f"\n🎯 Readiness Score: {readiness['score']}/100")
        for note in readiness['notes']:
            print(f"   {note}")
        
        if readiness['ready_for_training']:
            print("\n🎉 Ready for AutoML training!")
        else:
            print("\n⚠️ More data preparation needed before training")
        
        # Offer actions
        print("\n🔧 Available Actions:")
        print("   1. Review and verify unverified data")
        print("   2. Export verified data for training")
        print("   3. Auto-verify high-confidence data")
        
        action = input("\nChoose action (1-3, or Enter to skip): ").strip()
        
        if action == '1':
            result = manager.review_and_verify_data(interactive=True)
            if result['success']:
                print(f"✅ Verified {result['verified']} entries, corrected {result.get('corrected', 0)}")
        
        elif action == '2':
            result = manager.export_verified_data()
            if result['success']:
                print(f"✅ Exported {result['verified_count']} verified entries to {result['export_file']}")
        
        elif action == '3':
            result = manager.review_and_verify_data(interactive=False)
            if result['success']:
                print(f"✅ Auto-verified {result['verified']} high-confidence entries")
    
    else:
        print(f"❌ Error: {report['error']}")

if __name__ == "__main__":
    main()
