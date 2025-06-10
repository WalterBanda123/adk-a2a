"""
Bucket Upload Service
Handles uploading scraped text files to cloud storage buckets with user ID prefixes
"""

import os
import logging
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
from datetime import datetime

# Import cloud storage libraries (add based on your cloud provider)
try:
    from google.cloud import storage as gcs
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False

try:
    import boto3  # type: ignore
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
    boto3 = None  # type: ignore

logger = logging.getLogger(__name__)

class BucketUploadService:
    """
    Service for uploading scraped text files to cloud storage buckets
    Supports Google Cloud Storage and AWS S3
    """
    
    def __init__(self, user_id: str, provider: str = "gcs", bucket_name: Optional[str] = None):
        self.user_id = user_id
        self.provider = provider.lower()
        self.bucket_name = bucket_name or os.getenv('SCRAPS_BUCKET_NAME', 'product-scraps-bucket')
        
        # Initialize cloud client
        self.client = None
        self.bucket = None
        
        if self.provider == "gcs" and GCS_AVAILABLE:
            self._init_gcs()
        elif self.provider == "aws" and AWS_AVAILABLE:
            self._init_aws()
        else:
            logger.warning(f"Cloud provider {provider} not available or not supported")
        
        logger.info(f"Bucket upload service initialized for user {user_id} using {provider}")
    
    def _init_gcs(self):
        """Initialize Google Cloud Storage client"""
        try:
            # Initialize with service account key if available
            credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if credentials_path and Path(credentials_path).exists():
                self.client = gcs.Client.from_service_account_json(credentials_path)
            else:
                self.client = gcs.Client()
            
            self.bucket = self.client.bucket(self.bucket_name)
            logger.info(f"✅ GCS client initialized for bucket: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}")
            self.client = None
    
    def _init_aws(self):
        """Initialize AWS S3 client"""
        try:
            if boto3 is not None:
                self.client = boto3.client('s3')  # type: ignore
                logger.info(f"✅ AWS S3 client initialized for bucket: {self.bucket_name}")
            else:
                logger.error("boto3 not available")
                self.client = None
            
        except Exception as e:
            logger.error(f"Failed to initialize AWS S3 client: {e}")
            self.client = None
    
    async def upload_scrap_file(self, local_file_path: str, scrap_id: str, 
                              metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Upload a single scrap text file to the bucket
        """
        try:
            if metadata is None:
                metadata = {}
            
            if not self.client:
                return {
                    "success": False,
                    "error": "Cloud storage client not initialized"
                }
            
            file_path = Path(local_file_path)
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"File {local_file_path} does not exist"
                }
            
            # Create bucket path with user ID prefix
            timestamp = datetime.now().strftime('%Y/%m/%d')
            bucket_path = f"users/{self.user_id}/scraps/{timestamp}/{scrap_id}_{file_path.name}"
            
            # Upload based on provider
            if self.provider == "gcs":
                result = await self._upload_to_gcs(file_path, bucket_path, metadata)
            elif self.provider == "aws":
                result = await self._upload_to_s3(file_path, bucket_path, metadata)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported provider: {self.provider}"
                }
            
            if result["success"]:
                logger.info(f"✅ Uploaded scrap {scrap_id} to {bucket_path}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error uploading scrap file: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def upload_scraps_batch(self, scraps_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Upload multiple scrap files in batch
        """
        try:
            results = []
            successful_uploads = 0
            failed_uploads = 0
            
            for scrap_info in scraps_data:
                result = await self.upload_scrap_file(
                    scrap_info["local_path"],
                    scrap_info["scrap_id"],
                    scrap_info.get("metadata") or {}
                )
                
                results.append({
                    "scrap_id": scrap_info["scrap_id"],
                    "result": result
                })
                
                if result["success"]:
                    successful_uploads += 1
                else:
                    failed_uploads += 1
            
            return {
                "success": True,
                "total_files": len(scraps_data),
                "successful_uploads": successful_uploads,
                "failed_uploads": failed_uploads,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error in batch upload: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def upload_export_file(self, export_file_path: str, export_type: str = "full") -> Dict[str, Any]:
        """
        Upload a complete export file of user's scraps
        """
        try:
            if not self.client:
                return {
                    "success": False,
                    "error": "Cloud storage client not initialized"
                }
            
            file_path = Path(export_file_path)
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"Export file {export_file_path} does not exist"
                }
            
            # Create bucket path for export
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            bucket_path = f"users/{self.user_id}/exports/{export_type}_export_{timestamp}_{file_path.name}"
            
            metadata = {
                "export_type": export_type,
                "user_id": self.user_id,
                "export_timestamp": datetime.now().isoformat(),
                "file_size": str(file_path.stat().st_size)
            }
            
            # Upload based on provider
            if self.provider == "gcs":
                result = await self._upload_to_gcs(file_path, bucket_path, metadata)
            elif self.provider == "aws":
                result = await self._upload_to_s3(file_path, bucket_path, metadata)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported provider: {self.provider}"
                }
            
            if result["success"]:
                result["export_path"] = bucket_path
                logger.info(f"✅ Uploaded export file to {bucket_path}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error uploading export file: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_user_bucket_files(self, prefix_filter: str = "scraps") -> Dict[str, Any]:
        """
        List all files in the bucket for this user
        """
        try:
            if not self.client:
                return {
                    "success": False,
                    "error": "Cloud storage client not initialized"
                }
            
            prefix = f"users/{self.user_id}/{prefix_filter}/"
            
            if self.provider == "gcs":
                files = await self._list_gcs_files(prefix)
            elif self.provider == "aws":
                files = await self._list_s3_files(prefix)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported provider: {self.provider}"
                }
            
            return {
                "success": True,
                "user_id": self.user_id,
                "prefix": prefix,
                "total_files": len(files),
                "files": files
            }
            
        except Exception as e:
            logger.error(f"Error listing bucket files: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_bucket_file(self, bucket_path: str) -> Dict[str, Any]:
        """
        Delete a file from the bucket
        """
        try:
            if not self.client:
                return {
                    "success": False,
                    "error": "Cloud storage client not initialized"
                }
            
            if self.provider == "gcs":
                result = await self._delete_from_gcs(bucket_path)
            elif self.provider == "aws":
                result = await self._delete_from_s3(bucket_path)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported provider: {self.provider}"
                }
            
            if result["success"]:
                logger.info(f"✅ Deleted {bucket_path} from bucket")
            
            return result
            
        except Exception as e:
            logger.error(f"Error deleting bucket file: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _upload_to_gcs(self, file_path: Path, bucket_path: str, 
                           metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Upload file to Google Cloud Storage"""
        try:
            if not self.bucket:
                return {"success": False, "error": "Bucket not initialized"}
            
            blob = self.bucket.blob(bucket_path)
            
            # Set metadata
            if metadata:
                blob.metadata = metadata
            
            # Set content type based on file extension
            if file_path.suffix == '.json':
                blob.content_type = 'application/json'
            else:
                blob.content_type = 'text/plain'
            
            # Upload file
            blob.upload_from_filename(str(file_path))
            
            return {
                "success": True,
                "bucket_path": bucket_path,
                "public_url": blob.public_url,
                "size": blob.size
            }
            
        except Exception as e:
            logger.error(f"GCS upload error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _upload_to_s3(self, file_path: Path, bucket_path: str, 
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Upload file to AWS S3"""
        try:
            extra_args = {}
            
            # Set metadata
            if metadata:
                extra_args['Metadata'] = metadata
            
            # Set content type
            if file_path.suffix == '.json':
                extra_args['ContentType'] = 'application/json'
            else:
                extra_args['ContentType'] = 'text/plain'
            
            # Upload file
            if self.client:
                self.client.upload_file(  # type: ignore
                    str(file_path),
                    self.bucket_name,
                    bucket_path,
                    ExtraArgs=extra_args
                )
            else:
                raise ValueError("Client not initialized")
            
            return {
                "success": True,
                "bucket_path": bucket_path,
                "bucket": self.bucket_name
            }
            
        except Exception as e:
            logger.error(f"S3 upload error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _list_gcs_files(self, prefix: str) -> List[Dict[str, Any]]:
        """List files in GCS bucket with prefix"""
        files = []
        
        if not self.bucket:
            return files
        
        for blob in self.bucket.list_blobs(prefix=prefix):
            files.append({
                "name": blob.name,
                "size": blob.size,
                "created": blob.time_created.isoformat() if blob.time_created else None,
                "updated": blob.updated.isoformat() if blob.updated else None,
                "metadata": blob.metadata or {}
            })
        
        return files
    
    async def _list_s3_files(self, prefix: str) -> List[Dict[str, Any]]:
        """List files in S3 bucket with prefix"""
        files = []
        
        if not self.client:
            return files
        
        response = self.client.list_objects_v2(  # type: ignore
            Bucket=self.bucket_name,
            Prefix=prefix
        )
        
        for obj in response.get('Contents', []):
            last_modified = obj.get('LastModified')
            created_str = ""
            if last_modified and hasattr(last_modified, 'isoformat'):
                created_str = last_modified.isoformat()
            elif last_modified:
                created_str = str(last_modified)
            
            files.append({
                "name": obj.get('Key', ''),
                "size": obj.get('Size', 0),
                "created": created_str,
                "metadata": {}
            })
        
        return files
    
    async def _delete_from_gcs(self, bucket_path: str) -> Dict[str, Any]:
        """Delete file from GCS"""
        try:
            if not self.bucket:
                return {"success": False, "error": "Bucket not initialized"}
            
            blob = self.bucket.blob(bucket_path)
            blob.delete()
            
            return {"success": True}
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _delete_from_s3(self, bucket_path: str) -> Dict[str, Any]:
        """Delete file from S3"""
        try:
            if not self.client:
                return {"success": False, "error": "Client not initialized"}
            
            self.client.delete_object(  # type: ignore
                Bucket=self.bucket_name,
                Key=bucket_path
            )
            
            return {"success": True}
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
