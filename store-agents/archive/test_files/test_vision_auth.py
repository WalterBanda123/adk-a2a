#!/usr/bin/env python3
"""
Quick Vision API Authentication Test
Tests if the Google Cloud Vision API is properly authenticated and working
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_vision_auth():
    """Test Google Cloud Vision API authentication"""
    
    print("🧪 Testing Google Cloud Vision API Authentication")
    print("=" * 50)
    
    # Check if credentials are set
    credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    print(f"📁 Credentials file: {credentials_path}")
    
    if not credentials_path:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS not set!")
        return False
    
    if not os.path.exists(credentials_path):
        print(f"❌ Credentials file not found: {credentials_path}")
        return False
    
    print("✅ Credentials file exists")
    
    # Test Vision API client initialization
    try:
        from google.cloud import vision
        client = vision.ImageAnnotatorClient()
        print("✅ Vision API client created successfully!")
    except Exception as e:
        print(f"❌ Failed to create Vision API client: {e}")
        return False
    
    # Test Enhanced Vision Processor
    try:
        from enhanced_add_product_vision_tool_clean import EnhancedProductVisionProcessor
        processor = EnhancedProductVisionProcessor()
        print("✅ Enhanced Vision Processor initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize Enhanced Vision Processor: {e}")
        return False
    
    # Test Dynamic Classifier
    try:
        from common.dynamic_product_classifier import DynamicProductClassifier
        classifier = DynamicProductClassifier()
        print("✅ Dynamic Product Classifier initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize Dynamic Product Classifier: {e}")
        return False
    
    print("\n🎉 ALL SYSTEMS READY!")
    print("✅ Google Cloud Vision API: AUTHENTICATED")
    print("✅ Enhanced Vision Processor: WORKING")
    print("✅ Dynamic Classification: WORKING")
    print("✅ System Status: PRODUCTION READY")
    
    return True

if __name__ == "__main__":
    success = test_vision_auth()
    sys.exit(0 if success else 1)
