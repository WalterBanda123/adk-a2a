# filepath: /Users/walterbanda/Desktop/AI/adk-a2a/store-agents/common/user_service.py
import os
import logging
import asyncio
from typing import Dict, Any, Optional
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self):
        self.db = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if Firebase is already initialized
            if not firebase_admin._apps:
                cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
                project_id = os.getenv("FIREBASE_PROJECT_ID")
                
                if cred_path and os.path.exists(cred_path):
                    logger.info(f"Initializing Firebase with service account key: {cred_path}")
                    cred = credentials.Certificate(cred_path)
                    
                    if project_id:
                        firebase_admin.initialize_app(cred, {'projectId': project_id})
                    else:
                        firebase_admin.initialize_app(cred)
                        
                    logger.info("Firebase Admin SDK initialized successfully with service account")
                else:
                    logger.warning("No valid Firebase service account key found, attempting default initialization")
                    firebase_admin.initialize_app()
                    logger.info("Firebase Admin SDK initialized with default credentials")
            
            self.db = firestore.client()
            logger.info("Firestore client connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")
            logger.warning("Database connection unavailable")
            self.db = None
    
    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information from Firebase"""
        try:
            if not self.db:
                logger.warning("No database connection available")
                return None

            async def _fetch_user_data():
                if not self.db:
                    logger.error("Database connection not available for user data fetch")
                    return None
                    
                # Strategy 1: Try users collection first
                user_ref = self.db.collection('users').document(user_id)
                user_doc = await asyncio.get_event_loop().run_in_executor(None, user_ref.get)
                
                if user_doc.exists:
                    user_data = user_doc.to_dict()
                    logger.info(f"Retrieved user data from users collection for user_id: {user_id}")
                    return user_data
                
                # Strategy 2: Try profiles collection by user_id field
                profiles_ref = self.db.collection('profiles').where('user_id', '==', user_id).limit(1)
                profiles = await asyncio.get_event_loop().run_in_executor(None, profiles_ref.get)
                
                if profiles:
                    profile_data = profiles[0].to_dict()
                    if not profile_data:
                        logger.warning(f"Profile document has no data for user_id: {user_id}")
                        return None
                        
                    logger.info(f"Retrieved user data from profiles collection for user_id: {user_id}")
                    user_data = {
                        "name": profile_data.get("name", f"User {user_id}"),
                        "email": profile_data.get("email", f"{user_id}@example.com"),
                        "phone": profile_data.get("phone", "+263000000000"),
                        "language_preference": profile_data.get("language_preference", "English"),
                        "location": profile_data.get("location", "Zimbabwe"),
                        "user_id": profile_data.get("user_id", user_id),
                        "created_at": profile_data.get("createdAt"),
                        "business_owner": profile_data.get("business_owner", False),
                        "preferred_currency": profile_data.get("preferred_currency", "USD")
                    }
                    return user_data
                
                # Strategy 3: Try profiles collection with user_id as document ID
                if not self.db:
                    logger.error("Database connection lost during user lookup")
                    return None
                    
                profile_ref = self.db.collection('profiles').document(user_id)
                profile_doc = await asyncio.get_event_loop().run_in_executor(None, profile_ref.get)
                
                if profile_doc.exists:
                    profile_data = profile_doc.to_dict()
                    if not profile_data:
                        logger.warning(f"Profile document has no data for user_id: {user_id}")
                        return None
                        
                    logger.info(f"Retrieved user data from profiles document for user_id: {user_id}")
                    
                    user_data = {
                        "name": profile_data.get("name", f"User {user_id}"),
                        "email": profile_data.get("email", f"{user_id}@example.com"),
                        "phone": profile_data.get("phone", "+263000000000"),
                        "language_preference": profile_data.get("language_preference", "English"),
                        "location": profile_data.get("location", "Zimbabwe"),
                        "user_id": profile_data.get("user_id", user_id),
                        "created_at": profile_data.get("createdAt"),
                        "business_owner": profile_data.get("business_owner", False),
                        "preferred_currency": profile_data.get("preferred_currency", "USD")
                    }
                    return user_data
                
                logger.warning(f"User not found in any collection: {user_id}")
                return None

            # Add timeout to prevent hanging
            try:
                return await asyncio.wait_for(_fetch_user_data(), timeout=8.0)
            except asyncio.TimeoutError:
                logger.error(f"Timeout retrieving user info for {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving user info for {user_id}: {str(e)}")
            return None
    
    async def get_store_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get store information for a user from Firebase"""
        try:
            if not self.db:
                logger.warning("No database connection available")
                return None
            
            # Strategy 1: Query stores collection by owner_id
            stores_ref = self.db.collection('stores').where('owner_id', '==', user_id).limit(1)
            stores = stores_ref.get()
            
            if stores:
                store_data = stores[0].to_dict()
                logger.info(f"Retrieved store data for user_id: {user_id}")
                return store_data
            
            # Strategy 2: Query stores collection by user_id field
            stores_ref = self.db.collection('stores').where('user_id', '==', user_id).limit(1)
            stores = stores_ref.get()
            
            if stores:
                store_data = stores[0].to_dict()
                logger.info(f"Retrieved store data by user_id field for: {user_id}")
                return store_data
            
            # Strategy 3: Query stores collection by userId field (camelCase)
            stores_ref = self.db.collection('stores').where('userId', '==', user_id).limit(1)
            stores = stores_ref.get()
            
            if stores:
                store_data = stores[0].to_dict()
                logger.info(f"Retrieved store data by userId field for: {user_id}")
                return store_data
            
            # Strategy 4: Try store document with user_id as document ID
            store_ref = self.db.collection('stores').document(user_id)
            store_doc = store_ref.get()
            
            if store_doc.exists:
                store_data = store_doc.to_dict()
                logger.info(f"Retrieved store data from document for user_id: {user_id}")
                return store_data
            
            logger.warning(f"Store not found for user: {user_id}")
            return None
                
        except Exception as e:
            logger.error(f"Error retrieving store info for {user_id}: {str(e)}")
            return None
    
    async def test_firebase_connection(self) -> Dict[str, Any]:
        """Test Firebase connection and return status"""
        if not self.db:
            return {
                "connected": False,
                "message": "Firebase not initialized",
                "collections": []
            }
        
        try:
            # Test connection by listing collections
            collections = []
            for collection in self.db.collections():
                collections.append(collection.id)
            
            return {
                "connected": True,
                "message": "Firebase connected successfully",
                "collections": collections
            }
        except Exception as e:
            return {
                "connected": False,
                "message": f"Firebase connection error: {str(e)}",
                "collections": []
            }
