# Product Labeling Standards

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
