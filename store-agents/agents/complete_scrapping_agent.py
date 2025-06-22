"""
Complete Scrapping Agent
Coordinates product data extraction, text file storage, and bucket upload
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from google.adk.tools import FunctionTool

from ..common.scraps_storage_service import ScrapsStorageService
from ..common.bucket_upload_service import BucketUploadService

# Try to import enhanced vision processor
try:
    from ..enhanced_add_product_vision_tool_clean import EnhancedProductVisionProcessor
    ENHANCED_VISION_AVAILABLE = True
except ImportError:
    ENHANCED_VISION_AVAILABLE = False

logger = logging.getLogger(__name__)

class CompleteScrappingAgent:
    """
    Complete agent for product scrapping with automatic text file storage and bucket upload
    """
    
    def __init__(self, user_id: str, auto_upload: bool = True, bucket_provider: str = "gcs"):
        self.user_id = user_id
        self.auto_upload = auto_upload
        
        # Initialize services
        self.storage_service = ScrapsStorageService(user_id)
        self.bucket_service = BucketUploadService(user_id, bucket_provider) if auto_upload else None
        
        # Initialize vision processor
        self.vision_processor = None
        if ENHANCED_VISION_AVAILABLE:
            try:
                self.vision_processor = EnhancedProductVisionProcessor()
                logger.info("✅ Enhanced Vision Processor initialized")
            except Exception as e:
                logger.error(f"Failed to initialize vision processor: {e}")
        
        logger.info(f"Complete Scrapping Agent initialized for user {user_id}")
        logger.info(f"Auto-upload to bucket: {auto_upload}")
    
    def create_tools(self) -> List[FunctionTool]:
        """Create comprehensive scrapping tools"""
        tools = [
            FunctionTool(func=self.scrap_and_store_product),
            FunctionTool(func=self.batch_upload_scraps),
            FunctionTool(func=self.get_scrapping_stats),
            FunctionTool(func=self.search_scraps),
            FunctionTool(func=self.export_user_scraps),
            FunctionTool(func=self.cleanup_old_scraps)
        ]
        
        return tools
    
    async def scrap_and_store_product(self, data: str, data_type: str, 
                                    source_context: str = "manual_input",
                                    tags: Optional[List[str]] = None, 
                                    upload_to_bucket: bool = True) -> Dict[str, Any]:
        """
        Complete workflow: extract product info, store as text file, optionally upload to bucket
        """
        if tags is None:
            tags = []
            
        try:
            logger.info(f"Starting complete scrapping workflow for {data_type}")
            
            # Step 1: Extract product information
            if data_type in ["image_base64", "image_url"]:
                extraction_result = await self._extract_from_image(data, data_type == "image_url", tags)
            elif data_type == "text":
                extraction_result = await self._extract_from_text(data, tags)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported data type: {data_type}"
                }
            
            if not extraction_result["success"]:
                return extraction_result
            
            # Step 2: Store as text file
            scrap_data = self._create_comprehensive_scrap(
                extraction_result["extracted_data"], 
                data_type, 
                source_context, 
                tags,
                raw_data=data
            )
            
            scrap_id = await self.storage_service.store_scrap(scrap_data)
            
            result = {
                "success": True,
                "scrap_id": scrap_id,
                "extracted_data": extraction_result["extracted_data"],
                "stored_locally": True,
                "local_file": f"{self.user_id}_{scrap_id}_*.txt"
            }
            
            # Step 3: Upload to bucket if requested
            if upload_to_bucket and self.bucket_service:
                upload_result = await self._upload_scrap_to_bucket(scrap_id)
                result["uploaded_to_bucket"] = upload_result["success"]
                if upload_result["success"]:
                    result["bucket_path"] = upload_result.get("bucket_path")
                else:
                    result["upload_error"] = upload_result.get("error")
            else:
                result["uploaded_to_bucket"] = False
                result["upload_reason"] = "Not requested or bucket service unavailable"
            
            logger.info(f"✅ Complete scrapping workflow completed for {scrap_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error in complete scrapping workflow: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def batch_upload_scraps(self, scrap_ids: Optional[List[str]] = None, 
                                export_format: str = "individual") -> Dict[str, Any]:
        """
        Upload multiple scraps to bucket in batch
        """
        try:
            if not self.bucket_service:
                return {
                    "success": False,
                    "error": "Bucket service not available"
                }
            
            # Get scraps to upload
            if not scrap_ids:
                # Upload all scraps
                scraps_list = await self.storage_service.list_scraps(limit=1000)
                scrap_ids = [s["scrap_id"] for s in scraps_list]
            
            if not scrap_ids:
                return {
                    "success": True,
                    "message": "No scraps to upload",
                    "total_uploaded": 0
                }
            
            if export_format == "individual":
                # Upload each scrap individually
                upload_tasks = []
                for scrap_id in scrap_ids:
                    upload_tasks.append(self._upload_scrap_to_bucket(scrap_id))
                
                results = await asyncio.gather(*upload_tasks, return_exceptions=True)
                
                successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
                
                return {
                    "success": True,
                    "total_scraps": len(scrap_ids),
                    "successful_uploads": successful,
                    "failed_uploads": len(scrap_ids) - successful,
                    "upload_format": "individual"
                }
            
            else:
                # Create consolidated export and upload
                export_result = await self.export_user_scraps(
                    export_format=export_format.replace("consolidated_", ""),
                    upload_to_bucket=True
                )
                
                return {
                    "success": export_result["success"],
                    "upload_format": "consolidated",
                    "export_result": export_result
                }
                
        except Exception as e:
            logger.error(f"Error in batch upload: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_scrapping_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about scrapping activity
        """
        try:
            # Get local storage stats
            local_stats = await self.storage_service.get_user_stats()
            
            # Get bucket stats if available
            bucket_stats = {}
            if self.bucket_service:
                bucket_files = await self.bucket_service.list_user_bucket_files()
                if bucket_files["success"]:
                    bucket_stats = {
                        "total_bucket_files": bucket_files["total_files"],
                        "bucket_files": bucket_files["files"][:10]  # Show latest 10
                    }
            
            return {
                "success": True,
                "user_id": self.user_id,
                "timestamp": datetime.now().isoformat(),
                "local_storage": local_stats,
                "bucket_storage": bucket_stats,
                "services_status": {
                    "vision_processor": self.vision_processor is not None,
                    "bucket_service": self.bucket_service is not None,
                    "auto_upload": self.auto_upload
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting scrapping stats: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search_scraps(self, query: str, tags: Optional[List[str]] = None,
                          date_from: Optional[str] = None, date_to: Optional[str] = None,
                          limit: int = 20) -> Dict[str, Any]:
        """
        Search through stored scraps
        """
        try:
            # Get all scraps (could be optimized with proper indexing)
            all_scraps = await self.storage_service.list_scraps(filter_tags=tags or [], limit=1000)
            
            matching_scraps = []
            query_lower = query.lower()
            
            for scrap in all_scraps:
                # Get full content for search
                scrap_content = await self.storage_service.get_scrap(scrap["scrap_id"])
                if not scrap_content:
                    continue
                
                # Search in content
                content_text = scrap_content["content"].lower()
                title = scrap.get("title", "").lower()
                
                if query_lower in content_text or query_lower in title:
                    # Apply date filters if specified
                    scrap_timestamp = scrap.get("timestamp")
                    if date_from and scrap_timestamp and scrap_timestamp < date_from:
                        continue
                    if date_to and scrap_timestamp and scrap_timestamp > date_to:
                        continue
                    
                    matching_scraps.append({
                        "scrap_id": scrap["scrap_id"],
                        "title": scrap.get("title"),
                        "timestamp": scrap.get("timestamp"),
                        "tags": scrap.get("tags", []),
                        "relevance_score": content_text.count(query_lower)  # Simple relevance
                    })
            
            # Sort by relevance and apply limit
            matching_scraps.sort(key=lambda x: x["relevance_score"], reverse=True)
            matching_scraps = matching_scraps[:limit]
            
            return {
                "success": True,
                "query": query,
                "total_matches": len(matching_scraps),
                "matches": matching_scraps
            }
            
        except Exception as e:
            logger.error(f"Error searching scraps: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def export_user_scraps(self, export_format: str = "json",
                               include_content: bool = True,
                               upload_to_bucket: bool = True) -> Dict[str, Any]:
        """
        Create complete export of user's scraps
        """
        try:
            export_path = await self.storage_service.export_scraps_for_bucket(export_format)
            
            result = {
                "success": True,
                "export_path": export_path,
                "export_format": export_format,
                "timestamp": datetime.now().isoformat()
            }
            
            # Upload to bucket if requested
            if upload_to_bucket and self.bucket_service:
                upload_result = await self.bucket_service.upload_export_file(export_path)
                result["uploaded_to_bucket"] = upload_result["success"]
                if upload_result["success"]:
                    result["bucket_path"] = upload_result.get("export_path")
                else:
                    result["upload_error"] = upload_result.get("error")
            
            return result
            
        except Exception as e:
            logger.error(f"Error exporting scraps: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cleanup_old_scraps(self, days_old: int = 90, keep_latest: int = 100,
                               backup_before_delete: bool = True) -> Dict[str, Any]:
        """
        Clean up old scraps with optional backup
        """
        try:
            # Create backup if requested
            backup_result = None
            if backup_before_delete:
                backup_result = await self.export_user_scraps(
                    export_format="json",
                    upload_to_bucket=True
                )
            
            # Get all scraps
            all_scraps = await self.storage_service.list_scraps(limit=10000)
            
            # Sort by timestamp
            all_scraps.sort(key=lambda x: x["timestamp"], reverse=True)
            
            # Determine which scraps to delete
            scraps_to_delete = []
            cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            
            for i, scrap in enumerate(all_scraps):
                # Keep latest N scraps regardless of age
                if i < keep_latest:
                    continue
                
                # Delete old scraps
                scrap_timestamp = datetime.fromisoformat(scrap["timestamp"]).timestamp()
                if scrap_timestamp < cutoff_date:
                    scraps_to_delete.append(scrap["scrap_id"])
            
            # Delete scraps
            deleted_count = 0
            for scrap_id in scraps_to_delete:
                if await self.storage_service.delete_scrap(scrap_id):
                    deleted_count += 1
            
            return {
                "success": True,
                "total_scraps": len(all_scraps),
                "scraps_deleted": deleted_count,
                "scraps_kept": len(all_scraps) - deleted_count,
                "backup_created": backup_result["success"] if backup_result else False,
                "backup_path": backup_result.get("bucket_path") if backup_result else None
            }
            
        except Exception as e:
            logger.error(f"Error in cleanup: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _extract_from_image(self, image_data: str, is_url: bool, tags: List[str]) -> Dict[str, Any]:
        """Extract product info from image"""
        if self.vision_processor:
            try:
                result = self.vision_processor.process_image(image_data, is_url, self.user_id)
                # Check if result is a coroutine and await if needed
                import asyncio
                if asyncio.iscoroutine(result):
                    result = await result
                return result
            except Exception as e:
                logger.error(f"Vision processing error: {e}")
                return {
                    "success": False,
                    "error": f"Vision processing failed: {e}"
                }
        else:
            return {
                "success": True,
                "extracted_data": {
                    "title": "Image Product (Unprocessed)",
                    "brand": "",
                    "size": "",
                    "unit": "",
                    "category": "General",
                    "description": "Image stored without vision processing",
                    "confidence": 0.1,
                    "detection_method": "no_vision_processor"
                }
            }
    
    async def _extract_from_text(self, text_data: str, tags: List[str]) -> Dict[str, Any]:
        """Extract product info from text"""
        # Simple text parsing (could be enhanced with NLP)
        extracted_data = {
            "title": text_data.split('\n')[0][:100] if text_data else "Text Product",
            "brand": "",
            "size": "",
            "unit": "",
            "category": "General",
            "description": text_data[:200] + "..." if len(text_data) > 200 else text_data,
            "confidence": 0.8,
            "detection_method": "text_parsing"
        }
        
        return {
            "success": True,
            "extracted_data": extracted_data
        }
    
    def _create_comprehensive_scrap(self, extracted_data: Dict[str, Any], 
                                  data_type: str, source_context: str,
                                  tags: List[str], raw_data: Optional[str] = None) -> Dict[str, Any]:
        """Create comprehensive scrap data structure"""
        
        import uuid
        
        scrap_data = {
            "scrap_id": str(uuid.uuid4()),
            "user_id": self.user_id,
            "timestamp": datetime.now().isoformat(),
            "scrap_type": f"{data_type}_processed",
            "source_context": source_context,
            "tags": tags + [data_type, "auto_stored"],
            "extracted_data": extracted_data,
            "processing_metadata": {
                "processor_version": "complete_agent_v1",
                "processing_time": datetime.now().isoformat(),
                "data_type": data_type,
                "has_raw_data": raw_data is not None
            }
        }
        
        # Store raw data reference (truncated for storage)
        if raw_data:
            if data_type in ["image_base64", "image_url"]:
                scrap_data["image_reference"] = {
                    "type": data_type,
                    "size_hint": len(raw_data) if data_type == "image_base64" else "url",
                    "preview": raw_data[:100] + "..." if len(raw_data) > 100 else raw_data
                }
            else:
                scrap_data["original_text"] = raw_data
        
        return scrap_data
    
    async def _upload_scrap_to_bucket(self, scrap_id: str) -> Dict[str, Any]:
        """Upload a specific scrap to bucket"""
        try:
            if not self.bucket_service:
                return {
                    "success": False,
                    "error": "Bucket service not available"
                }
                
            # Get scrap content
            scrap_content = await self.storage_service.get_scrap(scrap_id)
            if not scrap_content:
                return {
                    "success": False,
                    "error": f"Scrap {scrap_id} not found"
                }
            
            # Upload to bucket
            upload_result = await self.bucket_service.upload_scrap_file(
                scrap_content["filepath"],
                scrap_id,
                scrap_content["metadata"]
            )
            
            return upload_result
            
        except Exception as e:
            logger.error(f"Error uploading scrap {scrap_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
