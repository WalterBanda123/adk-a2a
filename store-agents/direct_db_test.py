#!/usr/bin/env python3
"""
Direct database test to bypass the service
"""

import os
import sys
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()

def direct_test():
    print("🔧 Direct Database Test")
    print("="*30)
    
    try:
        # Initialize Firebase directly
        if not firebase_admin._apps:
            cred = credentials.Certificate('firebase-service-account-key.json')
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        user_id = "9IbW1ssRI9cneCFC7a1zKOGW1Qa2"
        
        print(f"Testing direct query for user: {user_id}")
        
        # Direct query with limit to avoid hanging
        products_ref = db.collection('products')
        
        # Try with a limit first
        print("Trying limited query...")
        limited_docs = products_ref.limit(5).get()
        print(f"Limited query returned {len(limited_docs)} docs")
        
        for doc in limited_docs:
            data = doc.to_dict()
            if data:
                print(f"  - {data.get('product_name', 'Unknown')} (User: {data.get('userId', 'N/A')})")
        
        # Now try user-specific query
        print(f"\nTrying user-specific query...")
        user_docs = products_ref.where('userId', '==', user_id).limit(5).get()
        print(f"User query returned {len(user_docs)} docs")
        
        for doc in user_docs:
            data = doc.to_dict()
            if data:
                print(f"  ✅ {data.get('product_name', 'Unknown')} - ${data.get('unit_price', 'N/A')}")
        
        if len(user_docs) == 0:
            print("❌ No products found for this user!")
            print("Let's check what user IDs exist...")
            
            # Check what user IDs exist
            all_docs = products_ref.limit(10).get()
            user_ids = set()
            for doc in all_docs:
                data = doc.to_dict()
                if data and 'userId' in data:
                    user_ids.add(data['userId'])
            
            print(f"Found user IDs: {list(user_ids)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    direct_test()
