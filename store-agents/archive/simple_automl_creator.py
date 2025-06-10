#!/usr/bin/env python3
"""
Simple AutoML Dataset Creator
"""
import os
import json
from google.cloud import automl
from google.cloud import storage

def create_automl_dataset():
    """Create AutoML Vision dataset for product recognition"""
    
    project_id = "deve-01"
    location = "us-central1"
    dataset_name = "zimbabwe_product_recognition"
    
    print(f"🚀 Creating AutoML dataset: {dataset_name}")
    print(f"📍 Project: {project_id}")
    print(f"📍 Location: {location}")
    
    try:
        # Initialize AutoML client
        client = automl.AutoMlClient()
        
        # Define dataset metadata for object detection
        dataset_metadata = automl.ImageObjectDetectionDatasetMetadata()
        
        dataset = automl.Dataset(
            display_name=dataset_name,
            image_object_detection_dataset_metadata=dataset_metadata,
        )
        
        # Create dataset
        parent = f"projects/{project_id}/locations/{location}"
        print(f"📋 Creating dataset in: {parent}")
        
        operation = client.create_dataset(parent=parent, dataset=dataset)
        print("⏳ Waiting for dataset creation...")
        
        # Wait for operation to complete
        dataset_result = operation.result(timeout=300)  # 5 minutes timeout
        dataset_path = dataset_result.name
        
        print(f"✅ Dataset created successfully!")
        print(f"📊 Dataset path: {dataset_path}")
        
        # Save dataset info
        dataset_info = {
            "dataset_name": dataset_name,
            "dataset_path": dataset_path,
            "project_id": project_id,
            "location": location,
            "bucket_name": f"{project_id}-automl-training",
            "created_date": "2025-06-10",
            "status": "created"
        }
        
        # Save to file for reference
        with open("automl_dataset_info.json", "w") as f:
            json.dump(dataset_info, f, indent=2)
        
        print("💾 Dataset info saved to automl_dataset_info.json")
        return dataset_path
        
    except Exception as e:
        print(f"❌ Failed to create dataset: {e}")
        import traceback
        traceback.print_exc()
        return ""

def main():
    print("🧪 AutoML Dataset Creator")
    print("=" * 50)
    
    dataset_path = create_automl_dataset()
    
    if dataset_path:
        print("\n🎉 Setup Complete!")
        print("=" * 50)
        print("📋 Next Steps:")
        print("1. Collect product images (300-500 images)")
        print("2. Upload images to gs://deve-01-automl-training/images/")
        print("3. Create training CSV with bounding box labels")
        print("4. Import training data to the dataset")
        print("5. Train the model")
        print(f"\n📊 Dataset: {dataset_path}")
    else:
        print("\n❌ Setup failed. Check the error messages above.")

if __name__ == "__main__":
    main()
