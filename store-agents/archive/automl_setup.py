#!/usr/bin/env python3
"""
AutoML Vision Setup and Management with Google Cloud Storage
Phase 1: Project Setup and Dataset Creation using Google Cloud Storage
"""
import os
import logging
from google.cloud import automl
from google.cloud import storage
import json
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoMLProjectSetup:
    """Handle AutoML Vision project setup and management"""
    
    def __init__(self, project_id: str = "deve-01", location: str = "us-central1"):
        self.project_id = project_id
        self.location = location
        self.bucket_name = f"{project_id}-automl-training"
        
        # Initialize clients
        self.automl_client = automl.AutoMlClient()
        self.storage_client = storage.Client(project=project_id)
        
    def verify_bucket_access(self) -> bool:
        """Verify that we can access the training bucket"""
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            bucket.reload()
            logger.info(f"✅ Bucket {self.bucket_name} accessible")
            return True
        except Exception as e:
            logger.error(f"❌ Cannot access bucket {self.bucket_name}: {e}")
            return False
        
    def setup_storage_bucket(self) -> bool:
        """Create and configure storage bucket for training data"""
        
        try:
            # Check if bucket exists
            try:
                bucket = self.storage_client.bucket(self.bucket_name)
                bucket.reload()
                logger.info(f"✅ Bucket {self.bucket_name} already exists")
                return True
            except:
                pass
            
            # Create bucket
            bucket = self.storage_client.create_bucket(
                self.bucket_name,
                location="US-CENTRAL1"
            )
            
            # Create folder structure
            folders = [
                "images/beverages/",
                "images/staples/", 
                "images/dairy/",
                "images/cooking_oils/",
                "labels/",
                "models/"
            ]
            
            for folder in folders:
                blob = bucket.blob(folder + ".gitkeep")
                blob.upload_from_string("")
            
            logger.info(f"✅ Created bucket: {self.bucket_name}")
            logger.info("✅ Created folder structure for training data")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create bucket: {e}")
            return False
    
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
            operation = self.automl_client.create_dataset(
                parent=parent, 
                dataset=dataset
            )
            
            # Wait for operation to complete
            dataset_result = operation.result(timeout=300)  # 5 minutes timeout
            dataset_path = dataset_result.name
            logger.info(f"✅ Created AutoML dataset: {dataset_path}")
            
            # Save dataset info
            dataset_info = {
                "dataset_name": dataset_name,
                "dataset_path": dataset_path,
                "project_id": self.project_id,
                "location": self.location,
                "created_date": "2024-06-10",
                "status": "created"
            }
            
            # Save to file for reference
            with open("automl_dataset_info.json", "w") as f:
                json.dump(dataset_info, f, indent=2)
            
            return dataset_path
            
        except Exception as e:
            logger.error(f"❌ Failed to create dataset: {e}")
            return ""
    
    def generate_training_csv_template(self) -> str:
        """Generate CSV template for training data"""
        
        csv_template = """# AutoML Vision Training Data CSV Template
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

gs://deve-01-automl-training/images/staples/hullets_brown_sugar_2kg_001.jpg,brand,0.1,0.1,0.4,0.3
gs://deve-01-automl-training/images/staples/hullets_brown_sugar_2kg_001.jpg,product_name,0.1,0.4,0.6,0.6
gs://deve-01-automl-training/images/staples/hullets_brown_sugar_2kg_001.jpg,size,0.7,0.1,0.9,0.2
gs://deve-01-automl-training/images/staples/hullets_brown_sugar_2kg_001.jpg,category,0.1,0.7,0.5,0.9

gs://deve-01-automl-training/images/beverages/mazoe_orange_2l_001.jpg,brand,0.2,0.1,0.5,0.3
gs://deve-01-automl-training/images/beverages/mazoe_orange_2l_001.jpg,product_name,0.2,0.4,0.7,0.6
gs://deve-01-automl-training/images/beverages/mazoe_orange_2l_001.jpg,size,0.7,0.2,0.9,0.3

# Add your training data below:
"""
        
        with open("training_data_template.csv", "w") as f:
            f.write(csv_template)
        
        logger.info("✅ Generated training CSV template: training_data_template.csv")
        return "training_data_template.csv"
    
    def check_api_enablement(self) -> Dict[str, bool]:
        """Check if required APIs are enabled"""
        
        required_apis = {
            "automl.googleapis.com": False,
            "storage-component.googleapis.com": False,
            "vision.googleapis.com": False
        }
        
        # Note: This is a simplified check
        # In practice, you'd use the Service Usage API
        logger.info("📋 Required APIs for AutoML Vision:")
        for api in required_apis.keys():
            logger.info(f"   - {api}")
        
        logger.info("\n💡 To enable APIs, run:")
        logger.info("gcloud services enable automl.googleapis.com")
        logger.info("gcloud services enable storage-component.googleapis.com") 
        logger.info("gcloud services enable vision.googleapis.com")
        
        return required_apis
    
    def generate_data_collection_guide(self) -> str:
        """Generate guide for data collection"""
        
        guide = """
# 📸 AutoML Training Data Collection Guide

## 🎯 Target Products (Start with these)

### High Priority Categories:
1. **Staples** (50 images minimum)
   - Hullets Brown Sugar (various sizes)
   - White Sugar brands
   - Rice (different brands/sizes)
   - Flour products

2. **Beverages** (50 images minimum)
   - Mazoe (Orange, Raspberry, etc.)
   - Coca Cola products
   - Pepsi products
   - Local juice brands

3. **Dairy** (30 images minimum)
   - Dairibord products
   - Milk cartons/bottles
   - Cheese packages

4. **Cooking Oils** (30 images minimum)
   - Olivine products
   - Other cooking oil brands

## 📷 Image Quality Guidelines

### ✅ Good Images:
- Clear product labels visible
- Good lighting (natural or bright indoor)
- Multiple angles of same product
- Different package sizes
- Brand name clearly readable
- Size/weight information visible

### ❌ Avoid:
- Blurry or dark images
- Partially obscured labels
- Extreme angles
- Damaged packaging
- Too far away (brand not readable)

## 🏷️ Labeling Instructions

For each image, create bounding boxes around:

1. **Brand** - Company name (e.g., "Hullets", "Mazoe")
2. **Product Name** - Product type (e.g., "Brown Sugar", "Orange")
3. **Size** - Weight/volume (e.g., "2kg", "500ml")
4. **Category** - Product category (e.g., "Staples", "Beverages")

## 📁 Naming Convention

Format: `{category}_{brand}_{product}_{size}_{sequence}.jpg`

Examples:
- `staples_hullets_brown_sugar_2kg_001.jpg`
- `beverages_mazoe_orange_2l_001.jpg`
- `dairy_dairibord_milk_1l_001.jpg`

## 🚀 Collection Sources

1. **Your Store**: Take photos of actual inventory
2. **Customer Uploads**: Use existing user-submitted images
3. **Supplier Catalogs**: Request images from suppliers
4. **Online Sources**: Product websites (with permission)

## 📊 Target Numbers

- **Total Images**: 300-500 for initial training
- **Per Category**: 50-100 images
- **Per Product**: 10-20 different images
- **Validation Set**: Keep 20% for testing

Start small and expand based on results!
"""
        
        with open("data_collection_guide.md", "w") as f:
            f.write(guide)
        
        logger.info("✅ Generated data collection guide: data_collection_guide.md")
        return "data_collection_guide.md"

def main():
    """Run AutoML setup process"""
    
    print("🚀 AutoML Vision Setup for Product Recognition")
    print("=" * 60)
    
    # Initialize setup
    setup = AutoMLProjectSetup()
    
    # Step 1: Check API requirements
    print("\n1️⃣ Checking API Requirements...")
    setup.check_api_enablement()
    
    # Step 2: Setup storage
    print("\n2️⃣ Setting up Storage Bucket...")
    if setup.setup_storage_bucket():
        print("✅ Storage setup complete")
    else:
        print("❌ Storage setup failed")
        return
    
    # Step 3: Create dataset
    print("\n3️⃣ Creating AutoML Dataset...")
    dataset_path = setup.create_automl_dataset()
    if dataset_path:
        print(f"✅ Dataset created: {dataset_path}")
    else:
        print("❌ Dataset creation failed")
        return
    
    # Step 4: Generate templates and guides
    print("\n4️⃣ Generating Templates and Guides...")
    setup.generate_training_csv_template()
    setup.generate_data_collection_guide()
    
    print("\n🎉 AutoML Setup Complete!")
    print("=" * 60)
    print("📋 Next Steps:")
    print("1. Review data_collection_guide.md")
    print("2. Start collecting product images")
    print("3. Use training_data_template.csv for labeling")
    print("4. Upload images to the created bucket")
    print("5. Run the training script when ready")
    
    print(f"\n📁 Storage Bucket: gs://{setup.bucket_name}")
    print(f"📊 Dataset Path: {dataset_path}")

if __name__ == "__main__":
    main()
