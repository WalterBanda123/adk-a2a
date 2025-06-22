#!/usr/bin/env python3
"""
Environment Cleanup and Training Data Enhancement Script
Cleans up test files and prepares for enhanced pattern-based product recognition
"""
import os
import shutil
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def cleanup_environment():
    """Clean up test files and organize the workspace"""
    
    base_dir = Path(__file__).parent
    
    # Create cleanup directories
    cleanup_dirs = {
        'archive': base_dir / 'archive',
        'archive/test_files': base_dir / 'archive' / 'test_files',
        'archive/docs': base_dir / 'archive' / 'docs',
        'training_data': base_dir / 'training_data',
        'training_data/images': base_dir / 'training_data' / 'images',
        'training_data/labels': base_dir / 'training_data' / 'labels'
    }
    
    # Create directories
    for name, path in cleanup_dirs.items():
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Created directory: {name}")
    
    # Test files to archive
    test_files = [
        'test_add_product_curl.sh',
        'test_add_product_vision.py',
        'test_analyze_image_endpoint.sh',
        'test_automl_env.py',
        'test_automl_integration.py',
        'test_before_after.py',
        'test_complete_integration.py',
        'test_complete_scrapping.py',
        'test_direct_api.sh',
        'test_direct_vision.py',
        'test_dynamic_classification.py',
        'test_end_to_end_image.py',
        'test_enhanced_server.py',
        'test_extended_timeout.py',
        'test_full_agent_flow.py',
        'test_full_image.py',
        'test_full_vision_api.py',
        'test_gcs_automl.py',
        'test_minimal_vision.py',
        'test_system_status.py',
        'test_vision_api.py',
        'test_vision_auth.py',
        'test_with_real_image.py',
        'verify_enhancement.py',
        'encoded_image.txt'
    ]
    
    # Documentation files to archive
    doc_files = [
        'ADD_NEW_PRODUCT_README.md',
        'AUTOML_IMPLEMENTATION_COMPLETE.md',
        'AUTOML_IMPLEMENTATION_PLAN.md',
        'AUTOML_INTEGRATION_COMPLETE.md',
        'AUTOML_SETUP_COMPLETE.md',
        'AUTOML_VS_CURRENT_COMPARISON.md',
        'DYNAMIC_CLASSIFICATION_README.md',
        'ENHANCED_VISION_CONTEXT_APPROACH.md',
        'FIREBASE_AUTOML_INTEGRATION.md',
        'IMPLEMENTATION_SUMMARY.md',
        'ISSUE_RESOLVED.md',
        'PHASE_1_COMPLETION_SUMMARY.md',
        'PHASE_2_COMPLETION_REPORT.md',
        'PRODUCTION_DEPLOYMENT_GUIDE.md',
        'SCRAPPING_SYSTEM_README.md',
        'STOCK_INTEGRATION_GUIDE.md'
    ]
    
    # Old AutoML files to archive (keeping only production versions)
    old_automl_files = [
        'automl_quickstart.py',
        'automl_setup.py',
        'automl_setup_firebase.py',
        'automl_setup_simple.py',
        'automl_trainer.py',
        'automl_trainer_firebase.py',
        'automl_integration.py',
        'enhanced_vision_context_example.py',
        'simple_automl_creator.py',
        'NEXT_STEPS_QUICKSTART.py',
        'setup_business_profile.py'
    ]
    
    # Move test files
    moved_count = 0
    for file_name in test_files:
        file_path = base_dir / file_name
        if file_path.exists():
            shutil.move(str(file_path), str(cleanup_dirs['archive/test_files'] / file_name))
            moved_count += 1
            logger.info(f"📁 Moved test file: {file_name}")
    
    # Move documentation files
    for file_name in doc_files:
        file_path = base_dir / file_name
        if file_path.exists():
            shutil.move(str(file_path), str(cleanup_dirs['archive/docs'] / file_name))
            moved_count += 1
            logger.info(f"📚 Moved doc file: {file_name}")
    
    # Move old AutoML files
    for file_name in old_automl_files:
        file_path = base_dir / file_name
        if file_path.exists():
            shutil.move(str(file_path), str(cleanup_dirs['archive'] / file_name))
            moved_count += 1
            logger.info(f"🏗️ Moved old AutoML file: {file_name}")
    
    # Move existing training image to training data folder
    existing_image = base_dir / 'images-mazoe-ruspberry.jpeg'
    if existing_image.exists():
        shutil.move(str(existing_image), str(cleanup_dirs['training_data/images'] / 'mazoe-raspberry.jpeg'))
        logger.info(f"🖼️ Moved training image to training_data/images/")
    
    logger.info(f"✅ Cleanup complete! Moved {moved_count} files to archive folders")
    
    return cleanup_dirs

def create_training_structure():
    """Create organized training data structure"""
    
    base_dir = Path(__file__).parent
    training_dir = base_dir / 'training_data'
    
    # Create training subdirectories for different product categories
    categories = [
        'beverages/mazoe',
        'beverages/coca_cola',
        'beverages/pepsi', 
        'food/bread',
        'food/sugar',
        'food/rice',
        'household/cleaning',
        'personal_care',
        'snacks'
    ]
    
    for category in categories:
        category_path = training_dir / 'images' / category
        category_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Created category: {category}")
    
    # Create template files for organized labeling
    templates = {
        'image_collection_guide.md': create_collection_guide(),
        'labeling_standards.md': create_labeling_standards(),
        'product_patterns.md': create_product_patterns()
    }
    
    for filename, content in templates.items():
        file_path = training_dir / filename
        with open(file_path, 'w') as f:
            f.write(content)
        logger.info(f"📝 Created guide: {filename}")

def create_collection_guide():
    """Create image collection guide"""
    return """# Training Image Collection Guide

## Zimbabwe Retail Product Recognition Training

### Image Collection Strategy

#### 1. **Product Categories to Focus On:**
- **Beverages:** Mazoe, Coca-Cola, Pepsi, Fanta, Sprite, etc.
- **Food Staples:** Bread (Baker Inn, Proton), Rice, Sugar (Huletts)
- **Household Items:** Cleaning products, soap
- **Snacks:** Chips, biscuits, sweets

#### 2. **Image Quality Requirements:**
- **Resolution:** Minimum 640x480, preferably 1024x768 or higher
- **Focus:** Product label/packaging should be clearly visible
- **Lighting:** Good natural or artificial lighting
- **Angles:** Multiple angles per product (front, side, slight angle)
- **Backgrounds:** Various backgrounds (shelf, counter, hand-held)

#### 3. **Naming Convention:**
```
brand_product_variant_size_angle.jpg
Examples:
- mazoe_orange_crush_2l_front.jpg
- coca_cola_classic_330ml_side.jpg
- huletts_white_sugar_1kg_angle.jpg
- baker_inn_white_bread_800g_front.jpg
```

#### 4. **Collection Goals:**
- **Minimum per product:** 10-15 images
- **Target total:** 500-1000 images
- **Brand coverage:** Top 20 Zimbabwe retail brands
- **Variety:** Different lighting, angles, conditions

#### 5. **Pattern Recognition Focus:**
Focus on products that follow common Zimbabwe naming patterns:
- Brand + Product Type + Variant + Size
- Local brands: Mazoe, Huletts, Baker Inn, Dairibord
- International brands with local variants
"""

def create_labeling_standards():
    """Create labeling standards guide"""
    return """# Product Labeling Standards

## Standardized Product Information Extraction

### 1. **Brand Identification Patterns**
```yaml
Primary Brands:
  - mazoe, huletts, baker_inn, dairibord, tanganda
  - coca_cola, pepsi, fanta, sprite
  - proton, blue_ribbon, cairns

Brand Variations:
  - "Coca Cola" → "coca_cola"
  - "Baker Inn" → "baker_inn" 
  - "Huletts" → "huletts"
```

### 2. **Product Naming Patterns**
```yaml
Structure: [Brand] [Product Type] [Variant] [Size][Unit]

Examples:
  - "Mazoe Orange Crush 2L" → brand: mazoe, product: orange_crush, size: 2, unit: l
  - "Huletts White Sugar 1kg" → brand: huletts, product: white_sugar, size: 1, unit: kg
  - "Baker Inn Brown Bread 800g" → brand: baker_inn, product: brown_bread, size: 800, unit: g
```

### 3. **Size Pattern Recognition**
```yaml
Volume Units: ml, l, liters, litres
Weight Units: g, kg, grams, kilos
Count Units: pack, pieces, units

Common Sizes:
  Beverages: 330ml, 500ml, 750ml, 1l, 2l, 5l
  Food: 250g, 500g, 750g, 1kg, 2kg, 5kg, 10kg
  Bread: 600g, 700g, 800g, 1kg
```

### 4. **Category Classification**
```yaml
Categories:
  beverages:
    - soft_drinks: cola, orange, lemon
    - juices: fruit_concentrates, pure_juice
    - water: still, sparkling
  
  food:
    - staples: rice, sugar, flour, oil
    - bread: white, brown, whole_grain
    - dairy: milk, yogurt, cheese
  
  household:
    - cleaning: detergent, soap, disinfectant
    - personal_care: shampoo, toothpaste
```

### 5. **Training Data Format**
```csv
image_path,brand,product_name,category,subcategory,size,unit,variant,confidence
images/beverages/mazoe/mazoe_orange_front.jpg,mazoe,orange_crush,beverages,soft_drinks,2,l,orange,1.0
images/food/huletts/huletts_sugar_front.jpg,huletts,white_sugar,food,staples,1,kg,white,1.0
```
"""

def create_product_patterns():
    """Create product pattern recognition guide"""
    return """# Zimbabwe Product Pattern Recognition

## Pattern-Based Product Detection System

### 1. **Brand Recognition Patterns**

#### Local Zimbabwe Brands:
```python
zimbabwe_brands = {
    'mazoe': {
        'products': ['orange_crush', 'raspberry', 'lemon', 'ginger'],
        'sizes': ['330ml', '500ml', '2l', '5l'],
        'patterns': ['mazoe.*orange', 'mazoe.*raspberry']
    },
    'huletts': {
        'products': ['white_sugar', 'brown_sugar', 'castor_sugar'],
        'sizes': ['500g', '1kg', '2kg'],
        'patterns': ['huletts.*sugar', 'huletts.*brown', 'huletts.*white']
    },
    'baker_inn': {
        'products': ['white_bread', 'brown_bread', 'whole_grain'],
        'sizes': ['600g', '700g', '800g'],
        'patterns': ['baker.?inn.*bread', 'baker.?inn.*brown']
    }
}
```

### 2. **Product Name Generation Patterns**

#### Pattern Rules:
1. **Brand First:** Always start with brand name
2. **Product Type:** Main product category 
3. **Variant:** Flavor, color, or type
4. **Size:** Numerical size with unit

#### Examples:
```python
# Pattern: brand_product_variant_size
"Mazoe Orange Crush 2L" → "mazoe_orange_crush_2l"
"Huletts Brown Sugar 1kg" → "huletts_brown_sugar_1kg"
"Baker Inn White Bread 800g" → "baker_inn_white_bread_800g"

# Confidence scoring based on pattern match
full_pattern_match = 1.0      # All elements detected
partial_pattern_match = 0.8   # Missing one element
brand_only_match = 0.6        # Only brand detected
```

### 3. **Regional Variations**

#### Zimbabwe-Specific Terms:
```python
local_terms = {
    'flavors': ['mazoe', 'tanganda', 'maheu'],
    'sizes': ['dumpy', 'schooner'],  # Local bottle sizes
    'variants': ['original', 'traditional', 'homestyle']
}
```

### 4. **Training Strategy**

#### Phase 1: Core Brands (Current)
- Focus on top 5 Zimbabwe brands
- 50-100 images per brand
- Basic pattern recognition

#### Phase 2: Expanded Recognition  
- 15-20 brands
- 500+ training images
- Advanced pattern matching
- Regional variant detection

#### Phase 3: Full Market Coverage
- Complete product catalog
- 1000+ training images
- Real-time learning
- Customer-specific patterns

### 5. **Pattern Confidence Scoring**

```python
def calculate_pattern_confidence(detected_elements):
    confidence = 0.0
    
    if 'brand' in detected_elements:
        confidence += 0.4
    if 'product_type' in detected_elements:
        confidence += 0.3
    if 'size' in detected_elements:
        confidence += 0.2
    if 'variant' in detected_elements:
        confidence += 0.1
    
    # Bonus for Zimbabwe-specific patterns
    if is_zimbabwe_brand(detected_elements['brand']):
        confidence += 0.1
    
    return min(confidence, 1.0)
```
"""

if __name__ == "__main__":
    print("🧹 Starting environment cleanup and training data organization...")
    print("=" * 70)
    
    # Cleanup environment
    cleanup_dirs = cleanup_environment()
    
    # Create training structure  
    create_training_structure()
    
    print("\n" + "=" * 70)
    print("✅ Environment cleanup and organization complete!")
    print("\n📁 New Directory Structure:")
    print("   archive/")
    print("   ├── test_files/     (all test files)")
    print("   ├── docs/           (documentation)")
    print("   └── old_automl/     (archived AutoML versions)")
    print("   training_data/")
    print("   ├── images/         (organized by category)")
    print("   ├── labels/         (CSV labeling files)")
    print("   └── guides/         (collection and labeling guides)")
    
    print("\n🎯 Next Steps:")
    print("   1. Review training_data/image_collection_guide.md")
    print("   2. Collect images following the category structure")
    print("   3. Use training_data/labeling_standards.md for consistency")
    print("   4. Run training pipeline when 100+ images are ready")
    
    print("\n📋 Training Goals:")
    print("   • Pattern-based product recognition")
    print("   • Zimbabwe-specific brand detection")
    print("   • 90-95% accuracy target")
    print("   • Real-world retail environment testing")
