# Zimbabwe Product Pattern Recognition

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
