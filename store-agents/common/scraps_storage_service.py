"""
Scraps Storage Service
Handles storage and retrieval of scraped product data in organized text files
with user ID prefixes for cloud bucket storage
"""

import os
import json
import logging
import aiofiles
from datetime import datetime
from typing import Dict, Any, List, Optional
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)

class ScrapsStorageService:
    """
    Service for storing and managing product scraps in text files
    Organized with user ID prefixes for easy bucket storage
    """
    
    def __init__(self, user_id: str, storage_path: Optional[str] = None):
        self.user_id = user_id
        
        # Set up storage path
        if storage_path is None:
            # Default to a scraps directory in the project
            self.storage_path = Path(__file__).parent.parent.parent / "data" / "scraps"
        else:
            self.storage_path = Path(storage_path)
        
        # Create user-specific directory
        self.user_storage_path = self.storage_path / f"user_{user_id}"
        self.user_storage_path.mkdir(parents=True, exist_ok=True)
        
        # Create index file path
        self.index_file = self.user_storage_path / "scraps_index.json"
        
        logger.info(f"Scraps storage initialized for user {user_id} at {self.user_storage_path}")
    
    async def store_scrap(self, scrap_data: Dict[str, Any]) -> str:
        """
        Store a scrap as a text file with structured format
        Returns the scrap_id for reference
        """
        try:
            scrap_id = scrap_data["scrap_id"]
            timestamp = scrap_data["timestamp"]
            
            # Create filename with user prefix and timestamp
            filename = f"{self.user_id}_{scrap_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = self.user_storage_path / filename
            
            # Create human-readable text content
            text_content = self._format_scrap_as_text(scrap_data)
            
            # Write scrap to text file
            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(text_content)
            
            # Update index
            await self._update_index(scrap_id, filename, scrap_data)
            
            logger.info(f"✅ Scrap {scrap_id} stored as {filename}")
            
            return scrap_id
            
        except Exception as e:
            logger.error(f"Error storing scrap: {e}")
            raise
    
    async def get_scrap(self, scrap_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a scrap by ID"""
        try:
            index = await self._load_index()
            
            if scrap_id not in index:
                logger.warning(f"Scrap {scrap_id} not found in index")
                return None
            
            scrap_info = index[scrap_id]
            filepath = self.user_storage_path / scrap_info["filename"]
            
            if not filepath.exists():
                logger.error(f"Scrap file {filepath} does not exist")
                return None
            
            # Read the text file
            async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            # Return both metadata and content
            return {
                "metadata": scrap_info,
                "content": content,
                "filepath": str(filepath)
            }
            
        except Exception as e:
            logger.error(f"Error retrieving scrap {scrap_id}: {e}")
            return None
    
    async def list_scraps(self, filter_tags: Optional[List[str]] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List scraps with optional tag filtering"""
        try:
            if filter_tags is None:
                filter_tags = []
            
            index = await self._load_index()
            
            scraps = []
            for scrap_id, scrap_info in index.items():
                # Apply tag filtering if specified
                if filter_tags:
                    scrap_tags = set(scrap_info.get("tags", []))
                    filter_tag_set = set(filter_tags)
                    if not filter_tag_set.intersection(scrap_tags):
                        continue
                
                scraps.append({
                    "scrap_id": scrap_id,
                    "timestamp": scrap_info.get("timestamp"),
                    "scrap_type": scrap_info.get("scrap_type"),
                    "tags": scrap_info.get("tags", []),
                    "title": scrap_info.get("title", "Unknown"),
                    "filename": scrap_info.get("filename"),
                    "source_context": scrap_info.get("source_context")
                })
            
            # Sort by timestamp (newest first) and apply limit
            scraps.sort(key=lambda x: x["timestamp"], reverse=True)
            return scraps[:limit]
            
        except Exception as e:
            logger.error(f"Error listing scraps: {e}")
            return []
    
    async def delete_scrap(self, scrap_id: str) -> bool:
        """Delete a scrap and remove from index"""
        try:
            index = await self._load_index()
            
            if scrap_id not in index:
                logger.warning(f"Scrap {scrap_id} not found for deletion")
                return False
            
            scrap_info = index[scrap_id]
            filepath = self.user_storage_path / scrap_info["filename"]
            
            # Delete file if it exists
            if filepath.exists():
                filepath.unlink()
                logger.info(f"Deleted scrap file: {filepath}")
            
            # Remove from index
            del index[scrap_id]
            await self._save_index(index)
            
            logger.info(f"✅ Scrap {scrap_id} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting scrap {scrap_id}: {e}")
            return False
    
    async def get_user_stats(self) -> Dict[str, Any]:
        """Get statistics about user's scraps"""
        try:
            index = await self._load_index()
            
            stats = {
                "total_scraps": len(index),
                "scrap_types": {},
                "tags": {},
                "storage_path": str(self.user_storage_path),
                "oldest_scrap": None,
                "newest_scrap": None
            }
            
            timestamps = []
            for scrap_info in index.values():
                # Count scrap types
                scrap_type = scrap_info.get("scrap_type", "unknown")
                stats["scrap_types"][scrap_type] = stats["scrap_types"].get(scrap_type, 0) + 1
                
                # Count tags
                for tag in scrap_info.get("tags", []):
                    stats["tags"][tag] = stats["tags"].get(tag, 0) + 1
                
                # Collect timestamps
                if scrap_info.get("timestamp"):
                    timestamps.append(scrap_info["timestamp"])
            
            if timestamps:
                timestamps.sort()
                stats["oldest_scrap"] = timestamps[0]
                stats["newest_scrap"] = timestamps[-1]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {"error": str(e)}
    
    async def export_scraps_for_bucket(self, export_format: str = "json") -> str:
        """
        Export all scraps in a format suitable for bucket storage
        Returns the path to the export file
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            export_filename = f"{self.user_id}_scraps_export_{timestamp}.{export_format}"
            export_path = self.user_storage_path / export_filename
            
            index = await self._load_index()
            
            if export_format == "json":
                # Export as JSON
                export_data = {
                    "user_id": self.user_id,
                    "export_timestamp": datetime.now().isoformat(),
                    "total_scraps": len(index),
                    "scraps": {}
                }
                
                for scrap_id, scrap_info in index.items():
                    # Get full scrap content
                    scrap_content = await self.get_scrap(scrap_id)
                    if scrap_content:
                        export_data["scraps"][scrap_id] = {
                            "metadata": scrap_content["metadata"],
                            "content": scrap_content["content"]
                        }
                
                async with aiofiles.open(export_path, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(export_data, indent=2, ensure_ascii=False))
            
            elif export_format == "txt":
                # Export as consolidated text file
                async with aiofiles.open(export_path, 'w', encoding='utf-8') as f:
                    await f.write(f"SCRAPS EXPORT FOR USER: {self.user_id}\n")
                    await f.write(f"Export Date: {datetime.now().isoformat()}\n")
                    await f.write(f"Total Scraps: {len(index)}\n")
                    await f.write("=" * 80 + "\n\n")
                    
                    for scrap_id, scrap_info in index.items():
                        scrap_content = await self.get_scrap(scrap_id)
                        if scrap_content:
                            await f.write(f"SCRAP ID: {scrap_id}\n")
                            await f.write("-" * 40 + "\n")
                            await f.write(scrap_content["content"])
                            await f.write("\n" + "=" * 80 + "\n\n")
            
            logger.info(f"✅ Exported scraps to {export_path}")
            return str(export_path)
            
        except Exception as e:
            logger.error(f"Error exporting scraps: {e}")
            raise
    
    def _format_scrap_as_text(self, scrap_data: Dict[str, Any]) -> str:
        """Format scrap data as human-readable text"""
        
        lines = []
        lines.append("=" * 80)
        lines.append(f"PRODUCT SCRAP: {scrap_data['scrap_id']}")
        lines.append("=" * 80)
        lines.append(f"User ID: {scrap_data['user_id']}")
        lines.append(f"Timestamp: {scrap_data['timestamp']}")
        lines.append(f"Scrap Type: {scrap_data['scrap_type']}")
        lines.append(f"Source Context: {scrap_data['source_context']}")
        lines.append(f"Tags: {', '.join(scrap_data.get('tags', []))}")
        lines.append("")
        
        # Extracted product data
        lines.append("EXTRACTED PRODUCT INFORMATION:")
        lines.append("-" * 40)
        extracted = scrap_data.get('extracted_data', {})
        
        lines.append(f"Title: {extracted.get('title', 'N/A')}")
        lines.append(f"Brand: {extracted.get('brand', 'N/A')}")
        lines.append(f"Size: {extracted.get('size', 'N/A')} {extracted.get('unit', '')}")
        lines.append(f"Category: {extracted.get('category', 'N/A')}")
        lines.append(f"Subcategory: {extracted.get('subcategory', 'N/A')}")
        lines.append(f"Description: {extracted.get('description', 'N/A')}")
        lines.append(f"Confidence: {extracted.get('confidence', 'N/A')}")
        lines.append(f"Detection Method: {extracted.get('detection_method', 'N/A')}")
        lines.append("")
        
        # Raw data section
        if 'raw_vision_data' in scrap_data:
            lines.append("RAW VISION DATA:")
            lines.append("-" * 40)
            lines.append(json.dumps(scrap_data['raw_vision_data'], indent=2))
            lines.append("")
        
        if 'original_text' in scrap_data:
            lines.append("ORIGINAL TEXT:")
            lines.append("-" * 40)
            lines.append(scrap_data['original_text'])
            lines.append("")
        
        # Processing metadata
        lines.append("PROCESSING METADATA:")
        lines.append("-" * 40)
        metadata = scrap_data.get('processing_metadata', {})
        for key, value in metadata.items():
            lines.append(f"{key}: {value}")
        
        lines.append("")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    async def _load_index(self) -> Dict[str, Any]:
        """Load the scraps index file"""
        try:
            if not self.index_file.exists():
                return {}
            
            async with aiofiles.open(self.index_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                return json.loads(content) if content.strip() else {}
                
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            return {}
    
    async def _save_index(self, index: Dict[str, Any]):
        """Save the scraps index file"""
        try:
            async with aiofiles.open(self.index_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(index, indent=2, ensure_ascii=False))
                
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            raise
    
    async def _update_index(self, scrap_id: str, filename: str, scrap_data: Dict[str, Any]):
        """Update the index with new scrap information"""
        try:
            index = await self._load_index()
            
            index[scrap_id] = {
                "filename": filename,
                "timestamp": scrap_data["timestamp"],
                "scrap_type": scrap_data["scrap_type"],
                "source_context": scrap_data["source_context"],
                "tags": scrap_data.get("tags", []),
                "title": scrap_data.get("extracted_data", {}).get("title", "Unknown"),
                "created_at": datetime.now().isoformat()
            }
            
            await self._save_index(index)
            
        except Exception as e:
            logger.error(f"Error updating index: {e}")
            raise
