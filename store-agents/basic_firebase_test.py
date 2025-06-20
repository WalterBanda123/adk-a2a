#!/usr/bin/env python3
"""
Basic Firebase connection test
"""

import os
import firebase_admin
from firebase_admin import credentials, firestore

def test_basic_connection():
    print("🔧 Basic Firebase Connection Test")
    print("="*40)
    
    try:
        # Check if service account key exists
        key_path = 'firebase-service-account-key.json'
        if os.path.exists(key_path):
            print(f"✅ Service account key found: {key_path}")
        else:
            print(f"❌ Service account key NOT found: {key_path}")
            return
        
        # Initialize Firebase
        print("Initializing Firebase...")
        cred = credentials.Certificate(key_path)
        app = firebase_admin.initialize_app(cred)
        print(f"✅ Firebase app initialized: {app.name}")
        
        # Get Firestore client
        print("Getting Firestore client...")
        db = firestore.client()
        print(f"✅ Firestore client created")
        
        # Try a simple operation - list collections
        print("Testing basic database access...")
        collections = db.collections()
        collection_names = [col.id for col in collections]
        print(f"✅ Found collections: {collection_names}")
        
        # Try to access products collection specifically
        print("Accessing products collection...")
        products_ref = db.collection('products')
        print(f"✅ Products collection reference created")
        
        # Try to count documents (this should be fast)
        print("Counting products...")
        try:
            # Use limit to avoid fetching all data
            sample_docs = products_ref.limit(1).get()
            print(f"✅ Products collection accessible (sample: {len(sample_docs)} docs)")
            
            if sample_docs:
                sample_data = sample_docs[0].to_dict()
                if sample_data:
                    print(f"Sample product fields: {list(sample_data.keys())}")
                    print(f"Sample userId: {sample_data.get('userId', 'NOT FOUND')}")
                
        except Exception as e:
            print(f"❌ Error accessing products: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_basic_connection()
