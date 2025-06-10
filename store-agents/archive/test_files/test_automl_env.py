#!/usr/bin/env python3
"""
Quick AutoML Environment Test
Tests current environment setup for AutoML Vision
"""

import os
from google.cloud import storage
from google.cloud import vision

def test_environment():
    """Test the current AutoML environment setup"""
    print("🔍 Testing AutoML Environment Setup...")
    print()
    
    # Test 1: Check credentials
    print("1. Checking credentials...")
    cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if cred_path and os.path.exists(cred_path):
        print(f"   ✅ Credentials found: {cred_path}")
    else:
        print("   ❌ No credentials found")
        return False
    
    # Test 2: Test Vision API (we know this works)
    print("2. Testing Vision API...")
    try:
        vision_client = vision.ImageAnnotatorClient()
        print("   ✅ Vision API client created successfully")
    except Exception as e:
        print(f"   ❌ Vision API error: {str(e)}")
        return False
    
    # Test 3: Test Storage API
    print("3. Testing Storage API...")
    try:
        storage_client = storage.Client(project='deve-01')
        buckets = list(storage_client.list_buckets())
        print(f"   ✅ Storage API working, found {len(buckets)} buckets")
    except Exception as e:
        print(f"   ❌ Storage API error: {str(e)}")
        return False
    
    # Test 4: Test AutoML import
    print("4. Testing AutoML import...")
    try:
        from google.cloud import automl
        print("   ✅ AutoML library imported successfully")
    except Exception as e:
        print(f"   ❌ AutoML import error: {str(e)}")
        return False
    
    # Test 5: Test AutoML client creation
    print("5. Testing AutoML client...")
    try:
        automl_client = automl.AutoMlClient()
        print("   ✅ AutoML client created successfully")
    except Exception as e:
        print(f"   ⚠️ AutoML client warning: {str(e)}")
        print("   (This might be due to API not being fully enabled yet)")
    
    print()
    print("🎉 Environment test completed!")
    print()
    print("📋 Next Steps for AutoML Implementation:")
    print("1. Create a Cloud Storage bucket for training data")
    print("2. Collect and upload training images (300-500 images)")
    print("3. Create annotations for the images")
    print("4. Train the AutoML model")
    print("5. Deploy and integrate with the vision system")
    
    return True

if __name__ == "__main__":
    test_environment()
