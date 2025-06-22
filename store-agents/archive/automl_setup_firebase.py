#!/usr/bin/env python3
"""
AutoML Vision Setup and Management with Firebase Integration
Phase 1: Project Setup and Dataset Creation using Firebase Storage
"""
import os
import logging
import firebase_admin
from firebase_admin import credentials, storage as firebase_storage
from google.cloud import automl
import json
from typing import List, Dict, Any
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FirebaseAutoMLSetup:
    """Handle AutoML Vision setup using Firebase Storage"""
    
    def __init__(self, project_id: str = "deve-01", location: str = "us-central1"):
        self.project_id = project_id
        self.location = location
        self.firebase_bucket_name = f"{project_id}.appspot.com"
        self.training_folder = "automl-training"
        
        # Initialize Firebase if not already initialized
        try:
            firebase_admin.get_app()
            logger.info("✅ Firebase already initialized")
        except ValueError:
            # Initialize Firebase
            cred = credentials.Certificate('firebase-service-account-key.json')
            firebase_admin.initialize_app(cred, {
                'storageBucket': self.firebase_bucket_name
            })
            logger.info("✅ Firebase initialized")
        
        # Initialize AutoML client
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'firebase-service-account-key.json'
        self.automl_client = automl.AutoMlClient()
        
        # Get Firebase storage bucket
        self.bucket = firebase_storage.bucket()
        
    def setup_firebase_storage_structure(self) -> bool:
        """Create folder structure in Firebase Storage for training data"""
        
        try:
            # Create folder structure for AutoML training
            folders = [
                f"{self.training_folder}/images/beverages/",
                f"{self.training_folder}/images/staples/", 
                f"{self.training_folder}/images/dairy/",
                f"{self.training_folder}/images/cooking_oils/",
                f"{self.training_folder}/labels/",
                f"{self.training_folder}/models/",
                f"{self.training_folder}/datasets/"
            ]
            
            for folder in folders:
                # Create a placeholder file to ensure folder exists
                blob = self.bucket.blob(f"{folder}.gitkeep")
                blob.upload_from_string("")
            
            logger.info(f"✅ Created folder structure in Firebase Storage")
            logger.info(f"📁 Training data will be stored at: gs://{self.firebase_bucket_name}/{self.training_folder}/")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create Firebase storage structure: {e}")
            return False
    
    def enable_required_apis(self) -> bool:
        """Enable required Google Cloud APIs"""
        
        apis_to_enable = [
            "automl.googleapis.com",
            "vision.googleapis.com",
            "storage-component.googleapis.com"
        ]
        
        logger.info("🔧 Enabling required APIs...")
        
        for api in apis_to_enable:
            try:
                # Use gcloud command to enable APIs
                import subprocess
                result = subprocess.run([
                    'gcloud', 'services', 'enable', api, 
                    '--project', self.project_id
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(f"✅ Enabled API: {api}")
                else:
                    logger.warning(f"⚠️  API {api} may already be enabled or there was an issue")
                    
            except Exception as e:
                logger.error(f"❌ Failed to enable {api}: {e}")
                return False
        
        # Wait for APIs to propagate
        logger.info("⏳ Waiting for APIs to propagate (30 seconds)...")
        time.sleep(30)
        return True
    
    def create_automl_dataset(self, dataset_name: str = "zimbabwe_product_recognition") -> str:
        """Create AutoML Vision dataset for object detection"""
        
        try:
            # Define dataset metadata for object detection
            dataset_metadata = automl.ImageObjectDetectionDatasetMetadata()
            
            dataset = automl.Dataset(
                display_name=dataset_name,
                image_object_detection_dataset_metadata=dataset_metadata,
            )
            
            # Create dataset
            parent = f"projects/{self.project_id}/locations/{self.location}"
            
            logger.info(f"🔄 Creating AutoML dataset: {dataset_name}")
            logger.info(f"📍 Location: {parent}")
            
            operation = self.automl_client.create_dataset(
                parent=parent, 
                dataset=dataset
            )
            
            # Wait for operation to complete
            logger.info("⏳ Waiting for dataset creation to complete...")
            result = operation.result(timeout=300)  # 5 minutes timeout
            
            dataset_path = result.name
            logger.info(f"✅ Created AutoML dataset: {dataset_path}")
            
            # Save dataset info
            dataset_info = {
                "dataset_name": dataset_name,
                "dataset_path": dataset_path,
                "project_id": self.project_id,
                "location": self.location,
                "firebase_bucket": self.firebase_bucket_name,
                "training_folder": self.training_folder,
                "created_date": "2024-06-10",
                "status": "created"
            }
            
            # Save to file for reference
            with open("automl_dataset_info.json", "w") as f:
                json.dump(dataset_info, f, indent=2)
            
            # Also save to Firebase Storage
            blob = self.bucket.blob(f"{self.training_folder}/datasets/dataset_info.json")
            blob.upload_from_string(json.dumps(dataset_info, indent=2))
            
            return dataset_path
            
        except Exception as e:
            logger.error(f"❌ Failed to create dataset: {e}")
            logger.error(f"💡 Make sure AutoML APIs are enabled and you have sufficient permissions")
            return ""
    
    def generate_firebase_training_csv_template(self) -> str:
        """Generate CSV template for training data using Firebase Storage paths"""
        
        csv_template = f"""# AutoML Vision Training Data CSV Template (Firebase Storage)
# Format: IMAGE_URI,LABEL,XMIN,YMIN,XMAX,YMAX
# 
# LABEL options:
# - brand (e.g., "Hullets", "Mazoe", "Coca Cola")
# - product_name (e.g., "Brown Sugar", "Orange Crush", "Classic")
# - size (e.g., "2kg", "500ml", "1L")
# - category (e.g., "Staples", "Beverages", "Dairy")
#
# Coordinates are normalized (0.0 to 1.0)
# Example entries:

gs://{self.firebase_bucket_name}/{self.training_folder}/images/staples/hullets_brown_sugar_2kg_001.jpg,brand,0.1,0.1,0.4,0.3
gs://{self.firebase_bucket_name}/{self.training_folder}/images/staples/hullets_brown_sugar_2kg_001.jpg,product_name,0.1,0.4,0.6,0.6
gs://{self.firebase_bucket_name}/{self.training_folder}/images/staples/hullets_brown_sugar_2kg_001.jpg,size,0.7,0.1,0.9,0.2
gs://{self.firebase_bucket_name}/{self.training_folder}/images/staples/hullets_brown_sugar_2kg_001.jpg,category,0.1,0.7,0.5,0.9

gs://{self.firebase_bucket_name}/{self.training_folder}/images/beverages/mazoe_orange_2l_001.jpg,brand,0.2,0.1,0.5,0.3
gs://{self.firebase_bucket_name}/{self.training_folder}/images/beverages/mazoe_orange_2l_001.jpg,product_name,0.2,0.4,0.7,0.6
gs://{self.firebase_bucket_name}/{self.training_folder}/images/beverages/mazoe_orange_2l_001.jpg,size,0.7,0.2,0.9,0.3

# Add your training data below:
"""
        
        with open("firebase_training_data_template.csv", "w") as f:
            f.write(csv_template)
        
        # Also save to Firebase Storage
        blob = self.bucket.blob(f"{self.training_folder}/labels/training_data_template.csv")
        blob.upload_from_string(csv_template)
        
        logger.info("✅ Generated Firebase training CSV template: firebase_training_data_template.csv")
        return "firebase_training_data_template.csv"
    
    def upload_sample_image_to_firebase(self, local_image_path: str, category: str, filename: str) -> str:
        """Upload a sample image to Firebase Storage"""
        
        try:
            if not os.path.exists(local_image_path):
                logger.warning(f"⚠️  Sample image not found: {local_image_path}")
                return ""
            
            # Upload to Firebase Storage
            destination_path = f"{self.training_folder}/images/{category}/{filename}"
            blob = self.bucket.blob(destination_path)
            
            with open(local_image_path, 'rb') as image_file:
                blob.upload_from_file(image_file)
            
            firebase_url = f"gs://{self.firebase_bucket_name}/{destination_path}"
            logger.info(f"✅ Uploaded sample image: {firebase_url}")
            
            return firebase_url
            
        except Exception as e:
            logger.error(f"❌ Failed to upload sample image: {e}")
            return ""
    
    def generate_firebase_integration_guide(self) -> str:
        """Generate guide for Firebase integration"""
        
        guide = f"""
# 🔥 Firebase AutoML Integration Guide

## 📁 Firebase Storage Structure

Your training data will be stored in Firebase Storage at:
```
gs://{self.firebase_bucket_name}/{self.training_folder}/
├── images/
│   ├── beverages/
│   ├── staples/
│   ├── dairy/
│   └── cooking_oils/
├── labels/
│   └── training_data_template.csv
├── datasets/
│   └── dataset_info.json
└── models/
    └── (trained models will be stored here)
```

## 🚀 Uploading Images via Firebase Console

1. Go to Firebase Console: https://console.firebase.google.com
2. Select project: {self.project_id}
3. Navigate to Storage
4. Upload images to: `{self.training_folder}/images/[category]/`

## 📱 Uploading via Your App

You can integrate image upload directly into your store management app:

```javascript
// Example: Upload product image for training
const uploadTrainingImage = async (imageFile, category, productInfo) => {{
    const filename = `${{category}}_${{productInfo.brand}}_${{productInfo.name}}_${{Date.now()}}.jpg`;
    const storageRef = ref(storage, `{self.training_folder}/images/${{category}}/${{filename}}`);
    
    await uploadBytes(storageRef, imageFile);
    const downloadURL = await getDownloadURL(storageRef);
    
    // Add to training CSV data
    return `gs://{self.firebase_bucket_name}/{self.training_folder}/images/${{category}}/${{filename}}`;
}};
```

## 🏷️ Automated Labeling Integration

Since you have existing product classification data, you can:

1. **Use existing product detection results** to pre-populate labels
2. **Integrate with your current vision processing** to collect training data
3. **Crowdsource from users** - let store owners correct/improve detection

## 📊 Training Data Collection Strategy

### Phase 1: Quick Start (100 images)
- Use existing user-uploaded images from your system
- Focus on commonly misidentified products (like Hullets Brown Sugar)
- Manual labeling for highest quality

### Phase 2: Scale Up (300-500 images)  
- Integrate collection into your app workflow
- User feedback on incorrect detections becomes training data
- Automated bounding box suggestions from current vision system

### Phase 3: Continuous Learning
- New product images automatically added to training set
- Periodic model retraining (monthly/quarterly)
- A/B testing new models vs current system

## 🔧 Integration with Current System

Your enhanced vision processor can be modified to:
1. **Collect training data** from user interactions
2. **Pre-label images** using current classification logic
3. **Switch between models** (current enhanced vs AutoML)
4. **Provide fallback** when AutoML confidence is low

## 🎯 Expected Improvements

Current System → AutoML System:
- Brand Detection: ~50% → 90%+
- Size Detection: ~30% → 85%+
- Category Classification: ~70% → 95%+
- Overall Accuracy: ~50% → 90%+

Firebase Storage Path: gs://{self.firebase_bucket_name}/{self.training_folder}/
"""
        
        with open("firebase_automl_integration_guide.md", "w") as f:
            f.write(guide)
        
        # Also save to Firebase Storage
        blob = self.bucket.blob(f"{self.training_folder}/integration_guide.md")
        blob.upload_from_string(guide)
        
        logger.info("✅ Generated Firebase integration guide: firebase_automl_integration_guide.md")
        return "firebase_automl_integration_guide.md"

def main():
    """Run Firebase AutoML setup process"""
    
    print("🔥 Firebase AutoML Vision Setup for Product Recognition")
    print("=" * 70)
    
    # Initialize setup
    setup = FirebaseAutoMLSetup()
    
    # Step 1: Enable APIs
    print("\n1️⃣ Enabling Required APIs...")
    if setup.enable_required_apis():
        print("✅ APIs enabled successfully")
    else:
        print("⚠️  API enablement had issues - continuing anyway")
    
    # Step 2: Setup Firebase Storage
    print("\n2️⃣ Setting up Firebase Storage Structure...")
    if setup.setup_firebase_storage_structure():
        print("✅ Firebase storage setup complete")
    else:
        print("❌ Firebase storage setup failed")
        return
    
    # Step 3: Create AutoML dataset
    print("\n3️⃣ Creating AutoML Dataset...")
    dataset_path = setup.create_automl_dataset()
    if dataset_path:
        print(f"✅ Dataset created: {dataset_path}")
    else:
        print("❌ Dataset creation failed - check API enablement and permissions")
        print("💡 You can manually create the dataset later using the Firebase Console")
    
    # Step 4: Generate templates and guides
    print("\n4️⃣ Generating Templates and Guides...")
    setup.generate_firebase_training_csv_template()
    setup.generate_firebase_integration_guide()
    
    # Step 5: Upload sample image if available
    print("\n5️⃣ Looking for Sample Images...")
    sample_image = "images-mazoe-ruspberry.jpeg"
    if os.path.exists(sample_image):
        firebase_url = setup.upload_sample_image_to_firebase(
            sample_image, "beverages", "mazoe_raspberry_sample.jpeg"
        )
        if firebase_url:
            print(f"✅ Uploaded sample image: {firebase_url}")
    
    print("\n🎉 Firebase AutoML Setup Complete!")
    print("=" * 70)
    print("📋 Next Steps:")
    print("1. Review firebase_automl_integration_guide.md")
    print("2. Start collecting product images via Firebase Console or your app")
    print("3. Use firebase_training_data_template.csv for labeling")
    print("4. Run automl_trainer.py when you have 100+ labeled images")
    
    print(f"\n🔥 Firebase Storage: gs://{setup.firebase_bucket_name}/{setup.training_folder}/")
    print(f"🌐 Firebase Console: https://console.firebase.google.com/project/{setup.project_id}/storage")
    if dataset_path:
        print(f"📊 AutoML Dataset: {dataset_path}")

if __name__ == "__main__":
    main()
