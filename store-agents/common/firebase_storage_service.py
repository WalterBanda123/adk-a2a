"""
Firebase Storage Service
Handles uploading reports to Firebase Storage and generates public URLs for preview and download
"""
import os
import json
import logging
import shutil
from datetime import datetime
from typing import Dict, Any, Optional
import firebase_admin
from firebase_admin import credentials, storage as firebase_storage
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

logger = logging.getLogger(__name__)

class FirebaseStorageService:
    """
    Service for uploading reports to Firebase Storage with local fallback
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.bucket = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK and Storage"""
        try:
            # Check if Firebase is already initialized
            app = None
            try:
                app = firebase_admin.get_app()
                logger.info("Firebase already initialized, using existing app")
            except ValueError:
                # Initialize Firebase without specifying storage bucket
                cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY") or "firebase-service-account-key.json"
                
                if os.path.exists(cred_path):
                    logger.info(f"Initializing Firebase with service account key: {cred_path}")
                    cred = credentials.Certificate(cred_path)
                    # Initialize without specific storage bucket - let Firebase use default
                    app = firebase_admin.initialize_app(cred)
                else:
                    logger.warning("No valid Firebase service account key found, attempting default initialization")
                    app = firebase_admin.initialize_app()
                
                logger.info("Firebase Admin SDK initialized successfully")
            
            # Get the Firebase storage bucket with explicit bucket name
            try:
                # Read project_id from service account key
                cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY") or "firebase-service-account-key.json"
                project_id = None
                
                if os.path.exists(cred_path):
                    try:
                        with open(cred_path, 'r') as f:
                            cred_json = json.load(f)
                            project_id = cred_json.get('project_id')
                    except Exception as e:
                        logger.warning(f"Could not read project_id from credentials: {e}")
                
                if project_id:
                    bucket_name = f"{project_id}.appspot.com"
                    logger.info(f"Connecting to bucket: {bucket_name}")
                    self.bucket = firebase_storage.bucket(bucket_name, app=app)
                    logger.info(f"✅ Firebase Storage connected to bucket: {self.bucket.name}")
                else:
                    logger.error("Could not determine project_id for bucket name")
                    self.bucket = None
                    
            except Exception as e:
                logger.error(f"Failed to connect to Firebase Storage bucket: {e}")
                self.bucket = None
                
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Storage: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            self.bucket = None
    
    async def upload_report(self, file_path: str, report_type: str = "daily_sales") -> Dict[str, Any]:
        """
        Upload a report file to Firebase Storage and return a public URL
        Falls back to local storage if Firebase Storage is not available
        """
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"File {file_path} does not exist"
                }
            
            # If Firebase Storage is not available, use local storage fallback
            if not self.bucket:
                logger.warning("Firebase Storage not available, using local storage fallback")
                return await self._local_storage_fallback(file_path, report_type)
            
            # Create storage path with user ID prefix
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.basename(file_path)
            storage_path = f"users/{self.user_id}/reports/{report_type}/{timestamp}_{filename}"
            
            # Upload file to Firebase Storage
            blob = self.bucket.blob(storage_path)
            
            # Set content type
            if filename.endswith('.pdf'):
                content_type = 'application/pdf'
            elif filename.endswith('.json'):
                content_type = 'application/json'
            else:
                content_type = 'application/octet-stream'
            
            # Upload with metadata
            blob.metadata = {
                'user_id': self.user_id,
                'report_type': report_type,
                'upload_timestamp': timestamp,
                'original_filename': filename
            }
            
            logger.info(f"Uploading {filename} to Firebase Storage at {storage_path}")
            blob.upload_from_filename(file_path, content_type=content_type)
            
            # Make the file publicly accessible
            blob.make_public()
            
            # Get the public URL
            public_url = blob.public_url
            
            logger.info(f"✅ Successfully uploaded {filename} to Firebase Storage")
            logger.info(f"   Public URL: {public_url}")
            
            return {
                "success": True,
                "public_url": public_url,
                "storage_path": storage_path,
                "bucket_name": self.bucket.name,
                "file_size": os.path.getsize(file_path),
                "content_type": content_type
            }
            
        except Exception as e:
            logger.error(f"Error uploading report to Firebase Storage: {str(e)}")
            
            # If Firebase upload fails, try local storage fallback
            logger.warning("Firebase upload failed, attempting local storage fallback")
            return await self._local_storage_fallback(file_path, report_type)
    
    async def _local_storage_fallback(self, file_path: str, report_type: str) -> Dict[str, Any]:
        """
        Fallback method to store files locally when Firebase Storage is not available
        """
        try:
            # Create local reports directory
            reports_dir = os.path.join(os.getcwd(), "reports", self.user_id, report_type)
            os.makedirs(reports_dir, exist_ok=True)
            
            # Create destination filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)
            dest_filename = f"{name}_{timestamp}{ext}"
            dest_path = os.path.join(reports_dir, dest_filename)
            
            # Copy file to local reports directory
            shutil.copy2(file_path, dest_path)
            
            # Create a local URL (relative path for serving)
            relative_path = os.path.relpath(dest_path, os.getcwd())
            local_url = f"/{relative_path.replace(os.sep, '/')}"
            
            logger.info(f"✅ Stored file locally at: {dest_path}")
            logger.warning(f"⚠️ Using local storage fallback. File available at: {local_url}")
            
            return {
                "success": True,
                "public_url": local_url,
                "storage_path": dest_path,
                "bucket_name": "local_storage",
                "file_size": os.path.getsize(dest_path),
                "content_type": "application/pdf" if filename.endswith('.pdf') else "application/json",
                "storage_type": "local_fallback",
                "warning": "Firebase Storage not available, using local storage"
            }
            
        except Exception as e:
            logger.error(f"Local storage fallback also failed: {str(e)}")
            return {
                "success": False,
                "error": f"Both Firebase Storage and local fallback failed: {str(e)}"
            }
    
    async def list_user_reports(self, report_type: Optional[str] = None) -> Dict[str, Any]:
        """
        List reports for the user from Firebase Storage or local storage
        """
        try:
            if not self.bucket:
                # List from local storage
                return await self._list_local_reports(report_type)
            
            prefix = f"users/{self.user_id}/reports"
            if report_type:
                prefix += f"/{report_type}"
            
            blobs = self.bucket.list_blobs(prefix=prefix)
            
            reports = []
            for blob in blobs:
                reports.append({
                    "name": blob.name,
                    "public_url": blob.public_url,
                    "created": blob.time_created.isoformat() if blob.time_created else None,
                    "size": blob.size,
                    "content_type": blob.content_type
                })
            
            return {
                "success": True,
                "reports": reports,
                "count": len(reports)
            }
            
        except Exception as e:
            logger.error(f"Error listing reports: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _list_local_reports(self, report_type: Optional[str] = None) -> Dict[str, Any]:
        """
        List reports from local storage
        """
        try:
            reports_dir = os.path.join(os.getcwd(), "reports", self.user_id)
            if report_type:
                reports_dir = os.path.join(reports_dir, report_type)
            
            if not os.path.exists(reports_dir):
                return {
                    "success": True,
                    "reports": [],
                    "count": 0,
                    "storage_type": "local"
                }
            
            reports = []
            for root, dirs, files in os.walk(reports_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, os.getcwd())
                    local_url = f"/{relative_path.replace(os.sep, '/')}"
                    
                    stat = os.stat(file_path)
                    reports.append({
                        "name": file,
                        "public_url": local_url,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "size": stat.st_size,
                        "content_type": "application/pdf" if file.endswith('.pdf') else "application/json"
                    })
            
            return {
                "success": True,
                "reports": reports,
                "count": len(reports),
                "storage_type": "local"
            }
            
        except Exception as e:
            logger.error(f"Error listing local reports: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "storage_type": "local"
            }
