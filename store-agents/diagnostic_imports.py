#!/usr/bin/env python3
"""
Test product retrieval issue more directly
"""

import os

def check_environment():
    print("🔧 Environment Check")
    print("="*30)
    
    # Check key files
    key_file = 'firebase-service-account-key.json'
    exists = os.path.exists(key_file)
    print(f"Firebase key file exists: {exists}")
    
    if exists:
        size = os.path.getsize(key_file)
        print(f"Key file size: {size} bytes")
    
    # Check environment variables
    firebase_key = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
    firebase_project = os.getenv('FIREBASE_PROJECT_ID')
    
    print(f"FIREBASE_SERVICE_ACCOUNT_KEY: {firebase_key}")
    print(f"FIREBASE_PROJECT_ID: {firebase_project}")

def test_direct_import():
    print(f"\n🔧 Testing Direct Import")
    print("="*30)
    
    try:
        print("Importing firebase_admin...")
        import firebase_admin
        print("✅ firebase_admin imported")
        
        print("Importing credentials...")
        from firebase_admin import credentials
        print("✅ credentials imported")
        
        print("Importing firestore...")
        from firebase_admin import firestore
        print("✅ firestore imported")
        
        # Check if already initialized
        print(f"Apps already initialized: {len(firebase_admin._apps)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_our_service_import():
    print(f"\n🔧 Testing Our Service Import")
    print("="*30)
    
    try:
        print("Adding to sys.path...")
        import sys
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        print("Importing RealProductService...")
        from common.real_product_service import RealProductService
        print("✅ RealProductService imported")
        
        print("Creating service instance...")
        service = RealProductService()
        print("✅ Service instance created")
        
        print(f"Service has db: {service.db is not None}")
        
        return True
        
    except Exception as e:
        print(f"❌ Service import error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 PRODUCT RETRIEVAL DIAGNOSTICS")
    print("="*50)
    
    check_environment()
    
    if test_direct_import():
        test_our_service_import()
    
    print(f"\n✅ Diagnostic complete")
