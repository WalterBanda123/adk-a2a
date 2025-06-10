#!/usr/bin/env python3
"""
Simplified AutoML Setup Script
Creates necessary Google Cloud resources for AutoML Vision
"""

import os
import sys
from google.cloud import storage
from google.cloud import automl
import subprocess
import time

def run_gcloud_command(cmd):
    """Run a gcloud command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running command: {cmd}")
            print(f"Error: {result.stderr}")
            return False, result.stderr
        return True, result.stdout
    except Exception as e:
        print(f"Exception running command: {cmd}")
        print(f"Exception: {str(e)}")
        return False, str(e)

def main():
    project_id = "deve-01"
    location = "us-central1"  # AutoML supported region
    
    print("🚀 Starting AutoML Vision Setup...")
    print(f"Project ID: {project_id}")
    print(f"Location: {location}")
    print()
    
    # Step 1: Enable required APIs
    print("📋 Step 1: Enabling required APIs...")
    apis = [
        "automl.googleapis.com",
        "vision.googleapis.com", 
        "storage.googleapis.com"
    ]
    
    for api in apis:
        print(f"  Enabling {api}...")
        success, output = run_gcloud_command(f"gcloud services enable {api}")
        if success:
            print(f"  ✅ {api} enabled")
        else:
            print(f"  ⚠️ {api} may already be enabled or encountered an issue")
    
    print("\n⏳ Waiting 30 seconds for APIs to propagate...")
    time.sleep(30)
    
    # Step 2: Create storage bucket
    print("🪣 Step 2: Creating storage bucket...")
    bucket_name = f"{project_id}-automl-vision"
    
    try:
        storage_client = storage.Client(project=project_id)
        
        # Check if bucket exists
        try:
            bucket = storage_client.bucket(bucket_name)
            bucket.reload()
            print(f"  ✅ Bucket {bucket_name} already exists")
        except Exception:
            # Create bucket
            bucket = storage_client.create_bucket(bucket_name, location=location)
            print(f"  ✅ Created bucket: {bucket_name}")
            
    except Exception as e:
        print(f"  ❌ Error with storage bucket: {str(e)}")
        return False
    
    # Step 3: Test AutoML client
    print("🤖 Step 3: Testing AutoML client...")
    try:
        automl_client = automl.AutoMlClient()
        parent = f"projects/{project_id}/locations/{location}"
        
        # List datasets (this will work if AutoML is properly set up)
        datasets = automl_client.list_datasets(parent=parent)
        dataset_list = list(datasets)
        print(f"  ✅ AutoML client working! Found {len(dataset_list)} existing datasets")
        
    except Exception as e:
        print(f"  ⚠️ AutoML client issue: {str(e)}")
        print("     This might resolve after APIs are fully propagated")
    
    # Step 4: Create project structure
    print("📁 Step 4: Creating project structure...")
    directories = [
        "automl_data",
        "automl_data/images",
        "automl_data/annotations"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"  ✅ Created directory: {directory}")
    
    # Step 5: Generate configuration file
    print("⚙️ Step 5: Creating configuration file...")
    config_content = f"""# AutoML Vision Configuration
PROJECT_ID = "{project_id}"
LOCATION = "{location}"
BUCKET_NAME = "{bucket_name}"
DATASET_NAME = "product_classifier"

# Training parameters
TRAIN_BUDGET = 8  # Node hours for training (adjust based on needs)
CONFIDENCE_THRESHOLD = 0.7

# Paths
TRAINING_DATA_PATH = "automl_data/images"
ANNOTATIONS_PATH = "automl_data/annotations"
"""
    
    with open("automl_config.py", "w") as f:
        f.write(config_content)
    
    print("  ✅ Created automl_config.py")
    
    print("\n🎉 AutoML Setup Complete!")
    print("\nNext Steps:")
    print("1. Collect 300-500 product images")
    print("2. Create annotations (labels) for each image")
    print("3. Run automl_trainer.py to create and train the model")
    print("4. Integrate trained model with the vision system")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
