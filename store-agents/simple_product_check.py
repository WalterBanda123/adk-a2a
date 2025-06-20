#!/usr/bin/env python3
"""
Simple product collection check
"""

import firebase_admin
from firebase_admin import credentials, firestore

def simple_check():
    try:
        # Initialize Firebase
        cred = credentials.Certificate('firebase-service-account-key.json')
        firebase_admin.initialize_app(cred)
        print("✓ Firebase initialized")
        
        # Get Firestore client
        db = firestore.client()
        print("✓ Firestore client created")
        
        # Check products collection
        print("\n🔍 Checking products collection...")
        products_ref = db.collection('products')
        
        # Get all documents
        docs = products_ref.get()
        print(f"Total documents: {len(docs)}")
        
        # Show each product
        for i, doc in enumerate(docs, 1):
            data = doc.to_dict()
            if data:
                print(f"\nProduct {i} (ID: {doc.id}):")
                print(f"  Name: {data.get('product_name', 'N/A')}")
                print(f"  Price: ${data.get('unit_price', 'N/A')}")
                print(f"  UserId: {data.get('userId', 'N/A')}")
                print(f"  Status: {data.get('status', 'N/A')}")
        
        # Test specific user query
        user_id = "9IbW1ssRI9cneCFC7a1zKOGW1Qa2"
        print(f"\n🔍 Querying for user: {user_id}")
        
        user_docs = products_ref.where('userId', '==', user_id).get()
        print(f"Found {len(user_docs)} products for user")
        
        for doc in user_docs:
            data = doc.to_dict()
            if data:
                print(f"  - {data.get('product_name', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_check()
