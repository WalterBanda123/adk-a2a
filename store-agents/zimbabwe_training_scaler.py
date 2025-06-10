#!/usr/bin/env python3
"""
Zimbabwe Product Recognition Training Data Scaling Guide
Help collect and organize training data for 90-95% accuracy AutoML model
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class ZimbabweTrainingScaler:
    """Scale training data collection for Zimbabwe retail products"""
    
    def __init__(self):
        self.target_products = {
            # Priority 1: Most Common Zimbabwe Brands (20+ images each)
            'mazoe': {
                'variants': ['orange_crush', 'raspberry', 'lemon', 'ginger'],
                'sizes': ['330ml', '500ml', '2l', '5l'],
                'priority': 1,
                'target_images': 25,
                'current_images': 1
            },
            'huletts': {
                'variants': ['white_sugar', 'brown_sugar', 'castor_sugar'],
                'sizes': ['500g', '1kg', '2kg', '5kg'],
                'priority': 1,
                'target_images': 20,
                'current_images': 0
            },
            'baker_inn': {
                'variants': ['white_bread', 'brown_bread', 'whole_grain'],
                'sizes': ['600g', '700g', '800g'],
                'priority': 1,
                'target_images': 20,
                'current_images': 0
            },
            'coca_cola': {
                'variants': ['classic', 'diet', 'zero'],
                'sizes': ['330ml', '500ml', '1l', '2l'],
                'priority': 1,
                'target_images': 20,
                'current_images': 0
            },
            'dairibord': {
                'variants': ['milk', 'yogurt', 'cheese'],
                'sizes': ['500ml', '1l', '2l'],
                'priority': 1,
                'target_images': 15,
                'current_images': 0
            },
            
            # Priority 2: Secondary Zimbabwe Brands (10+ images each)
            'tanganda': {
                'variants': ['tea', 'rooibos'],
                'sizes': ['100g', '250g', '500g'],
                'priority': 2,
                'target_images': 12,
                'current_images': 0
            },
            'proton': {
                'variants': ['white_bread', 'brown_bread'],
                'sizes': ['600g', '800g'],
                'priority': 2,
                'target_images': 10,
                'current_images': 0
            },
            'blue_ribbon': {
                'variants': ['cooking_oil', 'sunflower_oil'],
                'sizes': ['750ml', '1l', '2l'],
                'priority': 2,
                'target_images': 10,
                'current_images': 0
            },
            'cairns': {
                'variants': ['food_products'],
                'sizes': ['various'],
                'priority': 2,
                'target_images': 10,
                'current_images': 0
            },
            
            # Priority 3: International Brands (5+ images each)
            'pepsi': {
                'variants': ['classic', 'diet'],
                'sizes': ['330ml', '500ml', '1l', '2l'],
                'priority': 3,
                'target_images': 8,
                'current_images': 0
            },
            'fanta': {
                'variants': ['orange', 'grape'],
                'sizes': ['330ml', '500ml', '1l', '2l'],
                'priority': 3,
                'target_images': 8,
                'current_images': 0
            },
            'sprite': {
                'variants': ['original'],
                'sizes': ['330ml', '500ml', '1l', '2l'],
                'priority': 3,
                'target_images': 8,
                'current_images': 0
            }
        }
        
        self.collection_strategies = {
            'retail_stores': {
                'description': 'Visit local grocery stores, supermarkets',
                'locations': ['OK Zimbabwe', 'TM Pick n Pay', 'Spar', 'Choppies'],
                'advantages': 'Real retail environment, good lighting, multiple brands',
                'tips': 'Ask permission, take photos of shelf displays'
            },
            'home_products': {
                'description': 'Products you already have at home',
                'locations': ['Kitchen', 'Pantry', 'Storage'],
                'advantages': 'Easy access, controlled environment',
                'tips': 'Use different backgrounds, lighting conditions'
            },
            'wholesale_markets': {
                'description': 'Wholesale markets, distributors',
                'locations': ['Mbare Musika', 'Wholesale shops'],
                'advantages': 'Bulk products, variety of brands',
                'tips': 'Focus on packaging variety, different angles'
            }
        }
    
    def generate_collection_plan(self) -> Dict[str, Any]:
        """Generate a strategic collection plan"""
        
        # Calculate current vs target
        total_current = sum(brand['current_images'] for brand in self.target_products.values())
        total_target = sum(brand['target_images'] for brand in self.target_products.values())
        
        # Prioritize brands by gap and priority
        collection_priority = []
        for brand, info in self.target_products.items():
            gap = info['target_images'] - info['current_images']
            if gap > 0:
                collection_priority.append({
                    'brand': brand,
                    'gap': gap,
                    'priority': info['priority'],
                    'variants': info['variants'],
                    'sizes': info['sizes']
                })
        
        # Sort by priority then by gap
        collection_priority.sort(key=lambda x: (x['priority'], -x['gap']))
        
        return {
            'current_status': {
                'total_images': total_current,
                'target_images': total_target,
                'completion_rate': total_current / total_target if total_target > 0 else 0
            },
            'collection_priority': collection_priority[:10],  # Top 10 priorities
            'strategies': self.collection_strategies
        }
    
    def create_collection_checklist(self) -> str:
        """Create a practical collection checklist"""
        
        plan = self.generate_collection_plan()
        
        checklist = """# Zimbabwe Product Recognition Training Data Collection Plan

## 🎯 Collection Goals
- **Target Total:** {total_target} images
- **Current:** {total_current} images  
- **Completion:** {completion_rate:.1%}
- **Remaining:** {remaining} images needed

## 📋 Priority Collection List

""".format(
            total_target=plan['current_status']['target_images'],
            total_current=plan['current_status']['total_images'],
            completion_rate=plan['current_status']['completion_rate'],
            remaining=plan['current_status']['target_images'] - plan['current_status']['total_images']
        )
        
        for i, item in enumerate(plan['collection_priority'], 1):
            checklist += f"""### {i}. {item['brand'].title()} ({item['gap']} images needed)
- **Priority:** {item['priority']} (1=highest)
- **Variants:** {', '.join(item['variants'])}
- **Common Sizes:** {', '.join(item['sizes'])}
- **Collection Tips:**
  - Take photos from multiple angles (front, side, angled)
  - Include size labels clearly visible
  - Good lighting (natural light preferred)
  - Different backgrounds (shelf, hand, counter)

"""
        
        checklist += """## 📸 Image Collection Guidelines

### Quality Requirements:
- **Resolution:** Minimum 640x480, prefer 1024x768+
- **Focus:** Sharp, clear product labels
- **Lighting:** Bright, even lighting
- **Background:** Varied but not distracting

### Naming Convention:
```
brand_variant_size_angle.jpg
Examples:
- mazoe_orange_crush_2l_front.jpg
- huletts_white_sugar_1kg_side.jpg
- baker_inn_brown_bread_800g_angled.jpg
```

### Collection Strategies:

"""
        
        for strategy, info in plan['strategies'].items():
            checklist += f"""#### {strategy.replace('_', ' ').title()}
- **Description:** {info['description']}
- **Locations:** {', '.join(info['locations'])}
- **Advantages:** {info['advantages']}
- **Tips:** {info['tips']}

"""
        
        checklist += """## 🎮 Collection Workflow

1. **Prepare Equipment:**
   - Smartphone/camera with good camera
   - Good lighting or portable light
   - Notebook for tracking

2. **Visit Collection Location:**
   - Ask permission if in store
   - Look for priority brands first
   - Take multiple angles per product

3. **Organize Images:**
   - Download to computer immediately
   - Rename following naming convention
   - Sort into category folders

4. **Process Training Data:**
   ```bash
   # Add images to training folder
   cp your_images/* training_data/images/beverages/mazoe/
   
   # Run pattern recognition
   python enhanced_training_collector.py
   
   # Verify and correct labels
   python training_data_manager.py
   ```

## 📊 Progress Tracking

Keep track of your collection progress:

```
Brand                Current  Target  Progress
=====================================
Mazoe                1        25      ████░░░░░░ 4%
Huletts              0        20      ░░░░░░░░░░ 0%
Baker Inn            0        20      ░░░░░░░░░░ 0%
Coca Cola            0        20      ░░░░░░░░░░ 0%
Dairibord            0        15      ░░░░░░░░░░ 0%
```

## 🏆 Milestones

- **25 images:** Basic pattern recognition ready
- **50 images:** Minimum training threshold
- **100 images:** Good training quality
- **150+ images:** Excellent accuracy potential

## 🚀 Ready to Train When:
- ✅ 100+ verified images
- ✅ 5+ different brands
- ✅ 70%+ high confidence labels
- ✅ Multiple product categories
"""
        
        return checklist
    
    def save_collection_plan(self):
        """Save the collection plan to files"""
        
        training_dir = Path("training_data")
        
        # Create collection plan
        checklist = self.create_collection_checklist()
        
        with open(training_dir / "collection_plan.md", 'w') as f:
            f.write(checklist)
        
        # Create tracking JSON
        plan = self.generate_collection_plan()
        with open(training_dir / "collection_tracking.json", 'w') as f:
            json.dump(plan, f, indent=2)
        
        logger.info("✅ Collection plan saved to training_data/collection_plan.md")
        logger.info("✅ Tracking data saved to training_data/collection_tracking.json")

def main():
    """Main function"""
    
    print("🎯 Zimbabwe Product Recognition Training Data Scaling")
    print("=" * 60)
    
    scaler = ZimbabweTrainingScaler()
    
    # Generate and save collection plan
    scaler.save_collection_plan()
    
    # Show current status
    plan = scaler.generate_collection_plan()
    status = plan['current_status']
    
    print(f"📊 Current Status:")
    print(f"   • Total Images: {status['total_images']}")
    print(f"   • Target Images: {status['target_images']}")
    print(f"   • Completion: {status['completion_rate']:.1%}")
    print(f"   • Remaining: {status['target_images'] - status['total_images']} images needed")
    
    print(f"\n🎯 Top Priority Brands to Collect:")
    for i, item in enumerate(plan['collection_priority'][:5], 1):
        print(f"   {i}. {item['brand'].title()}: {item['gap']} images needed (Priority {item['priority']})")
    
    print(f"\n📋 Next Steps:")
    print(f"   1. Review: training_data/collection_plan.md")
    print(f"   2. Start collecting priority brands: {', '.join([item['brand'] for item in plan['collection_priority'][:3]])}")
    print(f"   3. Use naming convention: brand_variant_size_angle.jpg")
    print(f"   4. Process with: python enhanced_training_collector.py")
    
    print(f"\n🎉 When you reach 100+ images:")
    print(f"   • Run: python training_data_manager.py")
    print(f"   • Verify and export data")
    print(f"   • Upload with: python pattern_based_uploader.py")
    print(f"   • Start training: python automl_training_pipeline.py")

if __name__ == "__main__":
    main()
