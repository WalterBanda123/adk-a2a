# Product Scrapping System with Text File Storage

This system provides comprehensive product scrapping capabilities that extract information from images and text, store them as organized text files with user ID prefixes, and optionally upload them to cloud buckets.

## 🎯 Key Features

### ✅ **Complete Scrapping Workflow**
- **Image Processing**: Extract product info from images using enhanced Google Cloud Vision API
- **Text Processing**: Parse product information from text descriptions
- **Automatic Storage**: Store scraped data as human-readable text files
- **Cloud Upload**: Optional automatic upload to Google Cloud Storage or AWS S3
- **User Organization**: All files prefixed with user IDs for easy bucket management

### ✅ **Smart Storage Organization**
```
data/scraps/
├── user_123/
│   ├── user_123_scrap-id-1_20250610_143022.txt
│   ├── user_123_scrap-id-2_20250610_143045.txt
│   └── scraps_index.json
├── user_456/
│   ├── user_456_scrap-id-3_20250610_143101.txt
│   └── scraps_index.json
```

### ✅ **Bucket-Ready Structure**
Files are automatically organized for cloud storage:
```
bucket/users/{user_id}/scraps/{year}/{month}/{day}/{scrap_id}_{filename}.txt
bucket/users/{user_id}/exports/full_export_{timestamp}.json
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up Environment
```bash
# For Google Cloud Vision API
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"

# For bucket uploads (optional)
export SCRAPS_BUCKET_NAME="your-bucket-name"
```

### 3. Test with Provided Image
```bash
python test_complete_scrapping.py
```

## 🔧 Usage Examples

### Initialize Scrapping Agent
```python
from agents.complete_scrapping_agent import CompleteScrappingAgent

# Create agent for a specific user
agent = CompleteScrappingAgent(
    user_id="user_123",
    auto_upload=True,  # Auto-upload to bucket
    bucket_provider="gcs"  # or "aws"
)
```

### Scrap from Base64 Image
```python
result = await agent.scrap_and_store_product(
    data="base64_encoded_image_data",
    data_type="image_base64",
    source_context="mobile_app_upload",
    tags=["product", "grocery"],
    upload_to_bucket=True
)

print(f"Scrap ID: {result['scrap_id']}")
print(f"Stored locally: {result['stored_locally']}")
print(f"Uploaded to bucket: {result['uploaded_to_bucket']}")
```

### Scrap from Image URL
```python
result = await agent.scrap_and_store_product(
    data="https://example.com/product-image.jpg",
    data_type="image_url",
    source_context="web_scraping",
    tags=["online", "catalog"]
)
```

### Scrap from Text Description
```python
product_text = '''
Mazoe Orange Crush
Brand: Mazoe
Size: 2L
Category: Beverages
Description: Premium orange concentrate from Zimbabwe
'''

result = await agent.scrap_and_store_product(
    data=product_text,
    data_type="text",
    source_context="manual_entry",
    tags=["mazoe", "beverage"]
)
```

### Search Stored Scraps
```python
search_results = await agent.search_scraps(
    query="orange juice",
    tags=["beverage"],
    limit=10
)

for match in search_results["matches"]:
    print(f"Found: {match['title']} (Score: {match['relevance_score']})")
```

### Export All Scraps
```python
# Export as JSON and upload to bucket
export_result = await agent.export_user_scraps(
    export_format="json",
    upload_to_bucket=True
)

print(f"Export created: {export_result['bucket_path']}")
```

### Batch Upload to Bucket
```python
# Upload all stored scraps to bucket
batch_result = await agent.batch_upload_scraps(
    export_format="individual"  # or "consolidated_json"
)

print(f"Uploaded {batch_result['successful_uploads']} files")
```

## 📁 File Structure & Content

### Text File Format
Each scrap is stored as a human-readable text file:

```
================================================================================
PRODUCT SCRAP: 12345678-90ab-cdef-1234-567890abcdef
================================================================================
User ID: user_123
Timestamp: 2025-06-10T14:30:22.123456
Scrap Type: image_base64_processed
Source Context: mobile_app_upload
Tags: product, grocery, vision_processed

EXTRACTED PRODUCT INFORMATION:
----------------------------------------
Title: Mazoe Orange Crush
Brand: Mazoe
Size: 2 L
Category: Beverages
Subcategory: Fruit Drinks
Description: Premium orange-flavored drink concentrate
Confidence: 0.92
Detection Method: enhanced_vision_context

RAW VISION DATA:
----------------------------------------
{
  "text_annotations": [...],
  "web_entities": [...],
  "logos": [...]
}

PROCESSING METADATA:
----------------------------------------
processor_version: complete_agent_v1
processing_time: 2025-06-10T14:30:22.123456
data_type: image_base64
================================================================================
```

### Index File
Each user has an index file (`scraps_index.json`) for quick lookups:

```json
{
  "scrap-id-1": {
    "filename": "user_123_scrap-id-1_20250610_143022.txt",
    "timestamp": "2025-06-10T14:30:22.123456",
    "scrap_type": "image_base64_processed",
    "tags": ["product", "grocery"],
    "title": "Mazoe Orange Crush"
  }
}
```

## 🌍 Cloud Storage Integration

### Google Cloud Storage
```python
# Auto-upload to GCS bucket
agent = CompleteScrappingAgent(
    user_id="user_123",
    bucket_provider="gcs"
)

# Files uploaded to:
# gs://your-bucket/users/user_123/scraps/2025/06/10/scrap-id_filename.txt
```

### AWS S3
```python
# Auto-upload to S3 bucket
agent = CompleteScrappingAgent(
    user_id="user_123",
    bucket_provider="aws"
)

# Files uploaded to:
# s3://your-bucket/users/user_123/scraps/2025/06/10/scrap-id_filename.txt
```

## 🔍 Advanced Features

### Smart Search
- Full-text search across all scrap content
- Tag-based filtering
- Date range filtering
- Relevance scoring

### Automatic Cleanup
```python
# Clean up old scraps (keep latest 100, delete older than 90 days)
cleanup_result = await agent.cleanup_old_scraps(
    days_old=90,
    keep_latest=100,
    backup_before_delete=True
)
```

### Statistics & Analytics
```python
stats = await agent.get_scrapping_stats()
print(f"Total scraps: {stats['local_storage']['total_scraps']}")
print(f"Most common tags: {stats['local_storage']['tags']}")
```

## 🔧 Available Tools

The scrapping agent provides these tools for integration:

1. **`scrap_and_store_product`** - Complete workflow for any input type
2. **`batch_upload_scraps`** - Upload multiple scraps to bucket
3. **`get_scrapping_stats`** - Get comprehensive statistics
4. **`search_scraps`** - Search through stored scraps
5. **`export_user_scraps`** - Create complete exports
6. **`cleanup_old_scraps`** - Automated cleanup with backup

## 🎯 Integration with Existing System

### Add to Existing Subagent
```python
from agents.complete_scrapping_agent import CompleteScrappingAgent

class YourSubagent:
    def __init__(self, user_id: str):
        self.scrapping_agent = CompleteScrappingAgent(user_id)
    
    def create_tools(self):
        # Add scrapping tools to your existing tools
        tools = []
        tools.extend(self.scrapping_agent.create_tools())
        # ... your other tools
        return tools
```

### Use in Product Management
```python
# When user uploads product image
scrap_result = await scrapping_agent.scrap_and_store_product(
    data=uploaded_image,
    data_type="image_base64",
    source_context="product_catalog_upload",
    tags=["inventory", "new_product"]
)

# Use extracted data for product creation
if scrap_result["success"]:
    product_data = scrap_result["extracted_data"]
    # Create product in your system using extracted data
```

## 🚨 Error Handling

The system includes comprehensive error handling:
- Vision API failures (falls back to basic storage)
- Bucket upload failures (data still stored locally)
- File system errors (with proper logging)
- Network issues (with retry logic)

## 📊 Performance & Scalability

- **Async Operations**: All file I/O operations are async
- **Batch Processing**: Efficient batch uploads to reduce API calls
- **Smart Indexing**: Quick lookups without scanning all files
- **Compression**: Export files can be compressed for large datasets
- **User Isolation**: Each user's data is completely separate

## 🔒 Security & Privacy

- **User Isolation**: Files are completely separated by user ID
- **No Cross-User Access**: Agents can only access their user's data
- **Secure Uploads**: Uses authenticated cloud storage APIs
- **Local Encryption**: Can be extended to encrypt local files
- **Access Logging**: All operations are logged for audit trails

This system provides a complete solution for scrapping product information and storing it in an organized, scalable, and bucket-ready format with full user isolation.
