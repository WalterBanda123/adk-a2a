# Zimbabwe Product Recognition Training Data Collection Plan

## 🎯 Collection Goals
- **Target Total:** 166 images
- **Current:** 1 images  
- **Completion:** 0.6%
- **Remaining:** 165 images needed

## 📋 Priority Collection List

### 1. Mazoe (24 images needed)
- **Priority:** 1 (1=highest)
- **Variants:** orange_crush, raspberry, lemon, ginger
- **Common Sizes:** 330ml, 500ml, 2l, 5l
- **Collection Tips:**
  - Take photos from multiple angles (front, side, angled)
  - Include size labels clearly visible
  - Good lighting (natural light preferred)
  - Different backgrounds (shelf, hand, counter)

### 2. Huletts (20 images needed)
- **Priority:** 1 (1=highest)
- **Variants:** white_sugar, brown_sugar, castor_sugar
- **Common Sizes:** 500g, 1kg, 2kg, 5kg
- **Collection Tips:**
  - Take photos from multiple angles (front, side, angled)
  - Include size labels clearly visible
  - Good lighting (natural light preferred)
  - Different backgrounds (shelf, hand, counter)

### 3. Baker_Inn (20 images needed)
- **Priority:** 1 (1=highest)
- **Variants:** white_bread, brown_bread, whole_grain
- **Common Sizes:** 600g, 700g, 800g
- **Collection Tips:**
  - Take photos from multiple angles (front, side, angled)
  - Include size labels clearly visible
  - Good lighting (natural light preferred)
  - Different backgrounds (shelf, hand, counter)

### 4. Coca_Cola (20 images needed)
- **Priority:** 1 (1=highest)
- **Variants:** classic, diet, zero
- **Common Sizes:** 330ml, 500ml, 1l, 2l
- **Collection Tips:**
  - Take photos from multiple angles (front, side, angled)
  - Include size labels clearly visible
  - Good lighting (natural light preferred)
  - Different backgrounds (shelf, hand, counter)

### 5. Dairibord (15 images needed)
- **Priority:** 1 (1=highest)
- **Variants:** milk, yogurt, cheese
- **Common Sizes:** 500ml, 1l, 2l
- **Collection Tips:**
  - Take photos from multiple angles (front, side, angled)
  - Include size labels clearly visible
  - Good lighting (natural light preferred)
  - Different backgrounds (shelf, hand, counter)

### 6. Tanganda (12 images needed)
- **Priority:** 2 (1=highest)
- **Variants:** tea, rooibos
- **Common Sizes:** 100g, 250g, 500g
- **Collection Tips:**
  - Take photos from multiple angles (front, side, angled)
  - Include size labels clearly visible
  - Good lighting (natural light preferred)
  - Different backgrounds (shelf, hand, counter)

### 7. Proton (10 images needed)
- **Priority:** 2 (1=highest)
- **Variants:** white_bread, brown_bread
- **Common Sizes:** 600g, 800g
- **Collection Tips:**
  - Take photos from multiple angles (front, side, angled)
  - Include size labels clearly visible
  - Good lighting (natural light preferred)
  - Different backgrounds (shelf, hand, counter)

### 8. Blue_Ribbon (10 images needed)
- **Priority:** 2 (1=highest)
- **Variants:** cooking_oil, sunflower_oil
- **Common Sizes:** 750ml, 1l, 2l
- **Collection Tips:**
  - Take photos from multiple angles (front, side, angled)
  - Include size labels clearly visible
  - Good lighting (natural light preferred)
  - Different backgrounds (shelf, hand, counter)

### 9. Cairns (10 images needed)
- **Priority:** 2 (1=highest)
- **Variants:** food_products
- **Common Sizes:** various
- **Collection Tips:**
  - Take photos from multiple angles (front, side, angled)
  - Include size labels clearly visible
  - Good lighting (natural light preferred)
  - Different backgrounds (shelf, hand, counter)

### 10. Pepsi (8 images needed)
- **Priority:** 3 (1=highest)
- **Variants:** classic, diet
- **Common Sizes:** 330ml, 500ml, 1l, 2l
- **Collection Tips:**
  - Take photos from multiple angles (front, side, angled)
  - Include size labels clearly visible
  - Good lighting (natural light preferred)
  - Different backgrounds (shelf, hand, counter)

## 📸 Image Collection Guidelines

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

#### Retail Stores
- **Description:** Visit local grocery stores, supermarkets
- **Locations:** OK Zimbabwe, TM Pick n Pay, Spar, Choppies
- **Advantages:** Real retail environment, good lighting, multiple brands
- **Tips:** Ask permission, take photos of shelf displays

#### Home Products
- **Description:** Products you already have at home
- **Locations:** Kitchen, Pantry, Storage
- **Advantages:** Easy access, controlled environment
- **Tips:** Use different backgrounds, lighting conditions

#### Wholesale Markets
- **Description:** Wholesale markets, distributors
- **Locations:** Mbare Musika, Wholesale shops
- **Advantages:** Bulk products, variety of brands
- **Tips:** Focus on packaging variety, different angles

## 🎮 Collection Workflow

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
