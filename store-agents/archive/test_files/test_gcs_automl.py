#!/usr/bin/env python3
"""
Test Google Cloud Storage and AutoML setup
"""
import os
from google.cloud import storage
from google.cloud import automl

def test_gcs_connection():
    """Test Google Cloud Storage connection"""
    try:
        client = storage.Client(project="deve-01")
        bucket = client.bucket("deve-01-automl-training")
        bucket.reload()
        print("✅ Google Cloud Storage connection successful")
        
        # List bucket contents
        blobs = list(bucket.list_blobs())
        print(f"✅ Bucket contains {len(blobs)} objects")
        for blob in blobs[:5]:  # Show first 5
            print(f"   📁 {blob.name}")
        
        return True
    except Exception as e:
        print(f"❌ GCS connection failed: {e}")
        return False

def test_automl_connection():
    """Test AutoML connection"""
    try:
        client = automl.AutoMlClient()
        parent = "projects/deve-01/locations/us-central1"
        
        # List existing datasets
        datasets = client.list_datasets(parent=parent)
        dataset_list = list(datasets)
        print(f"✅ AutoML connection successful")
        print(f"✅ Found {len(dataset_list)} existing datasets")
        
        for dataset in dataset_list:
            print(f"   📊 {dataset.display_name}: {dataset.name}")
        
        return True
    except Exception as e:
        print(f"❌ AutoML connection failed: {e}")
        return False

def main():
    print("🧪 Testing Google Cloud Setup")
    print("=" * 50)
    
    # Test 1: GCS
    print("\n1️⃣ Testing Google Cloud Storage...")
    gcs_ok = test_gcs_connection()
    
    # Test 2: AutoML
    print("\n2️⃣ Testing AutoML API...")
    automl_ok = test_automl_connection()
    
    # Summary
    print("\n📋 Test Results:")
    print("=" * 50)
    if gcs_ok and automl_ok:
        print("🎉 All tests passed! Ready for AutoML setup.")
    else:
        print("⚠️  Some tests failed. Check configuration.")
        
    return gcs_ok and automl_ok

if __name__ == "__main__":
    main()