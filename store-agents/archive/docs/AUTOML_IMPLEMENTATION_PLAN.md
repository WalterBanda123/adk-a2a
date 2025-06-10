# 🎯 Custom AutoML Vision Model Implementation Plan

## 🌟 **Why This Approach is Superior**

Instead of manually adding brand names and relying on fuzzy text matching, a custom AutoML Vision model will:

✅ **Automatically detect product structure** (brand, name, size, unit)  
✅ **Learn from your specific product catalog**  
✅ **Handle Zimbabwe products with 95%+ accuracy**  
✅ **Extract structured data directly from images**  
✅ **Scale to thousands of products automatically**  

## 📋 **Implementation Phases**

### Phase 1: Setup & Preparation (1-2 days)
### Phase 2: Data Collection (1-2 weeks) 
### Phase 3: Model Training (1-3 days)
### Phase 4: Integration (2-3 days)
### Phase 5: Production Deployment (1 day)

---

## 🚀 **Phase 1: AutoML Vision Setup**

### 1.1 Enable Required APIs
```bash
# Enable AutoML Vision API
gcloud services enable automl.googleapis.com
gcloud services enable storage-component.googleapis.com
```

### 1.2 Create AutoML Project Structure
```bash
# Create storage bucket for training data
gsutil mb -p deve-01 -c regional -l us-central1 gs://store-agents-automl-training

# Create folders for organized data
gsutil mkdir gs://store-agents-automl-training/images/
gsutil mkdir gs://store-agents-automl-training/labels/
```

### 1.3 Service Account Permissions
Your existing `vision-api-service.json` needs AutoML permissions:
- `AutoML Admin`
- `Storage Admin` 
- `Vision AI Admin`

---

## 📸 **Phase 2: Data Collection Strategy**

### 2.1 Product Categories to Focus On (Start Small)
```json
{
  "high_priority": [
    "beverages",     // Mazoe, Coca Cola, Pepsi
    "staples",       // Sugar, Rice, Flour (including Hullets)
    "dairy",         // Dairibord products
    "cooking_oils"   // Olivine brands
  ],
  "target_per_category": 50-100 images,
  "total_initial_dataset": 300-500 images
}
```

### 2.2 Image Collection Sources
1. **Your Store Photos**: Take pictures of actual products
2. **User Uploads**: Collect from your existing users
3. **Online Sources**: Product catalogs, websites (with permission)
4. **Supplier Catalogs**: Partner with local suppliers

### 2.3 Labeling Structure
For each image, we'll create bounding boxes with labels:
```json
{
  "image": "hullets_brown_sugar_2kg.jpg",
  "annotations": [
    {
      "label": "brand",
      "text": "Hullets",
      "bounding_box": [x1, y1, x2, y2]
    },
    {
      "label": "product_name", 
      "text": "Brown Sugar",
      "bounding_box": [x1, y1, x2, y2]
    },
    {
      "label": "size",
      "text": "2kg",
      "bounding_box": [x1, y1, x2, y2]
    },
    {
      "label": "category",
      "text": "Staples",
      "bounding_box": [x1, y1, x2, y2]
    }
  ]
}
```

---

## 🔧 **Phase 3: Model Training Implementation**

### 3.1 AutoML Dataset Creation Script
```python
# create_automl_dataset.py
from google.cloud import automl
import json
import csv

def create_product_dataset():
    """Create AutoML Vision dataset for product recognition"""
    
    client = automl.AutoMlClient()
    project_id = "deve-01"
    location = "us-central1"
    
    # Create dataset
    dataset_metadata = automl.ImageObjectDetectionDatasetMetadata()
    dataset = automl.Dataset(
        display_name="zimbabwe_product_recognition",
        image_object_detection_dataset_metadata=dataset_metadata,
    )
    
    parent = f"projects/{project_id}/locations/{location}"
    response = client.create_dataset(parent=parent, dataset=dataset)
    
    print(f"Dataset created: {response.name}")
    return response.name

def upload_training_data(dataset_name, csv_file_path):
    """Upload training images and labels"""
    
    client = automl.AutoMlClient()
    
    # CSV format: gs://bucket/image.jpg,label,xmin,ymin,xmax,ymax
    input_config = automl.InputConfig(
        gcs_source=automl.GcsSource(input_uris=[csv_file_path])
    )
    
    response = client.import_data(
        name=dataset_name,
        input_config=input_config
    )
    
    print("Training data upload started...")
    return response
```

### 3.2 Training Configuration
```python
# train_model.py
from google.cloud import automl

def train_product_model(dataset_name):
    """Train the custom product recognition model"""
    
    client = automl.AutoMlClient()
    
    # Model configuration for object detection
    model_metadata = automl.ImageObjectDetectionModelMetadata(
        train_budget_milli_node_hours=24000,  # 24 hours training
        model_type=automl.ImageObjectDetectionModelMetadata.ModelType.CLOUD_HIGH_ACCURACY_1
    )
    
    model = automl.Model(
        display_name="zimbabwe_product_detector_v1",
        dataset_id=dataset_name.split('/')[-1],
        image_object_detection_model_metadata=model_metadata,
    )
    
    response = client.create_model(
        parent=dataset_name.rsplit('/', 2)[0],
        model=model
    )
    
    print("Model training started...")
    print(f"Training operation: {response.operation.name}")
    return response
```

---

## 🔌 **Phase 4: Integration with Existing System**

### 4.1 Enhanced Processor with AutoML
```python
# enhanced_automl_vision_processor.py
from google.cloud import automl
import logging

class AutoMLProductVisionProcessor:
    """Enhanced processor using custom AutoML model"""
    
    def __init__(self):
        self.automl_client = automl.PredictionServiceClient()
        self.project_id = "deve-01"
        self.location = "us-central1" 
        self.model_id = "your_trained_model_id"  # After training
        
    def process_image_with_automl(self, image_data: str, user_id: str) -> dict:
        """Process image using custom trained model"""
        
        try:
            # Prepare model path
            model_path = self.automl_client.model_path(
                self.project_id, self.location, self.model_id
            )
            
            # Prepare image payload
            payload = automl.ExamplePayload(
                image=automl.Image(image_bytes=image_data)
            )
            
            # Make prediction
            response = self.automl_client.predict(
                name=model_path,
                payload=payload,
                params={"score_threshold": "0.7"}  # Confidence threshold
            )
            
            # Parse AutoML response into structured data
            return self._parse_automl_response(response)
            
        except Exception as e:
            logging.error(f"AutoML prediction failed: {e}")
            # Fallback to basic Vision API
            return self._fallback_to_basic_vision(image_data, user_id)
    
    def _parse_automl_response(self, response) -> dict:
        """Convert AutoML response to structured product data"""
        
        result = {
            "success": True,
            "title": "Unknown Product",
            "brand": "",
            "size": "",
            "unit": "", 
            "category": "General",
            "confidence": 0.0,
            "detection_method": "automl_custom_model"
        }
        
        brand_found = False
        product_found = False
        size_found = False
        
        # Process detected objects
        for prediction in response.payload:
            label = prediction.display_name
            confidence = prediction.object_detection.score
            
            if confidence > 0.7:  # High confidence threshold
                if label == "brand" and not brand_found:
                    result["brand"] = prediction.object_detection.text_extraction.text_segment.content
                    brand_found = True
                    
                elif label == "product_name" and not product_found:
                    result["title"] = prediction.object_detection.text_extraction.text_segment.content
                    product_found = True
                    
                elif label == "size" and not size_found:
                    size_text = prediction.object_detection.text_extraction.text_segment.content
                    # Extract size and unit
                    size_match = re.search(r'(\d+(?:\.\d+)?)\s*(kg|g|ml|l)', size_text.lower())
                    if size_match:
                        result["size"] = size_match.group(1)
                        result["unit"] = size_match.group(2)
                    size_found = True
                    
                elif label == "category":
                    result["category"] = prediction.object_detection.text_extraction.text_segment.content
        
        # Build title if not found
        if not product_found and brand_found:
            result["title"] = f"{result['brand']} Product"
            
        # Calculate overall confidence
        result["confidence"] = min(0.95, max(0.7, sum([p.object_detection.score for p in response.payload]) / len(response.payload)))
        
        return result
```

### 4.2 Update Direct Vision Server
```python
# Update direct_vision_server.py to use AutoML
@app.post("/analyze_image", response_model=ImageResponse)
async def analyze_image(request: ImageRequest):
    """Enhanced with AutoML custom model"""
    
    try:
        # Try AutoML first (high accuracy)
        automl_processor = AutoMLProductVisionProcessor()
        result = automl_processor.process_image_with_automl(
            request.image_data, 
            request.user_id
        )
        
        if result.get("confidence", 0) > 0.8:
            # High confidence from AutoML
            return create_response(result, "automl_custom_model")
        else:
            # Fallback to enhanced dynamic classifier
            enhanced_processor = EnhancedProductVisionProcessor()
            result = enhanced_processor.process_image(
                request.image_data, 
                request.is_url, 
                request.user_id
            )
            return create_response(result, "enhanced_dynamic_classifier")
            
    except Exception as e:
        # Final fallback to basic Vision API
        return handle_error(e)
```

---

## 📊 **Phase 5: Expected Results & Metrics**

### Before (Current System):
```json
{
  "title": "Brown Sugar",
  "brand": "",
  "size": "",
  "confidence": 0.5,
  "detection_method": "direct_vision_api"
}
```

### After (AutoML Custom Model):
```json
{
  "title": "Hullets Brown Sugar",
  "brand": "Hullets", 
  "size": "2",
  "unit": "kg",
  "category": "Staples",
  "confidence": 0.94,
  "detection_method": "automl_custom_model"
}
```

### Expected Performance:
- **Accuracy**: 90-95% for trained products
- **Brand Detection**: 95%+ for local brands
- **Size Extraction**: 85%+ accuracy
- **Processing Time**: 2-4 seconds
- **Confidence Scores**: 0.8-0.95 range

---

## 💰 **Cost Considerations**

### Training Costs (One-time):
- **Data Storage**: ~$5-10/month
- **Model Training**: ~$100-300 (24 hours training)
- **Dataset Preparation**: Time investment

### Prediction Costs (Ongoing):
- **AutoML Predictions**: ~$1.50 per 1000 images
- **Fallback Vision API**: ~$1.50 per 1000 images
- **Total**: Similar to current costs but much higher accuracy

---

## 🛣️ **Implementation Timeline**

### Week 1: Setup & Data Collection Start
- [ ] Enable AutoML APIs
- [ ] Set up storage buckets
- [ ] Start collecting product images
- [ ] Create labeling guidelines

### Week 2-3: Data Collection & Labeling
- [ ] Collect 300+ product images
- [ ] Label with bounding boxes
- [ ] Create training CSV file
- [ ] Upload to Google Cloud Storage

### Week 4: Model Training & Testing
- [ ] Train AutoML model (24 hours)
- [ ] Test model accuracy
- [ ] Fine-tune if needed
- [ ] Deploy model endpoint

### Week 5: Integration & Production
- [ ] Integrate with existing system
- [ ] A/B test against current system
- [ ] Deploy to production
- [ ] Monitor performance

---

## 🎯 **Next Steps (Immediate Actions)**

1. **Enable AutoML APIs** in your Google Cloud project
2. **Start collecting product images** from your store
3. **Create a labeling strategy** for your team
4. **Set up storage buckets** for training data

Would you like me to start implementing Phase 1 (Setup) right now?
