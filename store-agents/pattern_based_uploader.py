#!/usr/bin/env python3
"""
Enhanced Pattern-Based Training Data Upload System
Upload training images with pattern-based AutoML labels for Zimbabwe retail products
"""
import os
import sys
import json
import csv
import logging
from pathlib import Path
from google.cloud import storage
from google.cloud import automl
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PatternBasedAutoMLUploader:
    """Upload training data with pattern-based labels to AutoML"""
    
    def __init__(self):
        self.project_id = "deve-01"
        self.bucket_name = "deve-01-automl-training" 
        self.dataset_id = None
        self.client = None
        self.dataset_info = self._load_dataset_info()
        
        if self.dataset_info:
            self.dataset_id = self.dataset_info.get('dataset_id')
        
        # Initialize Google Cloud clients
        try:
            self.storage_client = storage.Client(project=self.project_id)
            self.automl_client = automl.AutoMlClient()
            logger.info("✅ Google Cloud clients initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Google Cloud clients: {e}")
            raise
    
    def _load_dataset_info(self):
        """Load AutoML dataset information"""
        dataset_info_file = Path(__file__).parent / "automl_dataset_info.json"
        
        if not dataset_info_file.exists():
            logger.warning("Dataset info file not found. AutoML dataset may not be created yet.")
            return None
            
        with open(dataset_info_file, 'r') as f:
            return json.load(f)
    
    def upload_training_data_from_csv(self, csv_file_path: str) -> bool:
        """Upload training data using our pattern-based CSV labels"""
        
        csv_path = Path(csv_file_path)
        if not csv_path.exists():
            logger.error(f"Training labels CSV not found: {csv_path}")
            return False
        
        # Read training data from CSV
        training_data = []
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('verified', '').lower() == 'yes':  # Only use verified data
                    training_data.append(row)
        
        if not training_data:
            logger.warning("No verified training data found in CSV")
            return False
        
        logger.info(f"📋 Found {len(training_data)} verified training examples")
        
        # Group by category for organized upload
        categories = {}
        for item in training_data:
            category = item['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(item)
        
        # Upload images and create AutoML CSV
        uploaded_count = 0
        automl_csv_rows = []
        
        for category, items in categories.items():
            logger.info(f"📁 Processing category: {category} ({len(items)} items)")
            
            for item in items:
                # Upload image to GCS
                local_image_path = Path("training_data") / item['image_path']
                if not local_image_path.exists():
                    logger.warning(f"⚠️ Image not found: {local_image_path}")
                    continue
                
                # Create GCS path
                gcs_path = f"training_images/{category}/{item['image_filename']}"
                
                # Upload to GCS
                if self._upload_image_to_gcs(local_image_path, gcs_path):
                    # Create AutoML CSV row
                    gcs_uri = f"gs://{self.bucket_name}/{gcs_path}"
                    
                    # Create label using pattern-based information
                    label = self._create_automl_label(item)
                    
                    automl_csv_rows.append([gcs_uri, label])
                    uploaded_count += 1
                    
                    logger.info(f"✅ Uploaded: {item['image_filename']} → {label}")
        
        # Create AutoML import CSV
        if automl_csv_rows:
            self._create_automl_import_csv(automl_csv_rows)
            logger.info(f"🎉 Successfully uploaded {uploaded_count} training images")
            return True
        else:
            logger.error("❌ No images were uploaded successfully")
            return False
    
    def _upload_image_to_gcs(self, local_path: Path, gcs_path: str) -> bool:
        """Upload single image to Google Cloud Storage"""
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(gcs_path)
            
            # Check if already exists
            if blob.exists():
                logger.info(f"⏭️ Already exists: {gcs_path}")
                return True
            
            with open(local_path, 'rb') as f:
                blob.upload_from_file(f)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to upload {local_path}: {e}")
            return False
    
    def _create_automl_label(self, item: Dict[str, str]) -> str:
        """Create AutoML label from pattern-based item data"""
        
        # Create standardized label format
        parts = []
        
        if item['brand']:
            parts.append(item['brand'])
        
        if item['variant']:
            parts.append(item['variant'])
        
        if item['size'] and item['unit']:
            parts.append(f"{item['size']}{item['unit']}")
        
        # Fallback to product_name if parts are empty
        if not parts and item['product_name']:
            return item['product_name'].lower().replace(' ', '_')
        
        return '_'.join(parts).lower()
    
    def _create_automl_import_csv(self, csv_rows: List[List[str]]):
        """Create CSV file for AutoML import"""
        
        import_csv_path = Path("training_data") / "automl_import.csv"
        
        with open(import_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            for row in csv_rows:
                writer.writerow(row)
        
        # Upload to GCS
        gcs_csv_path = "automl_import.csv"
        bucket = self.storage_client.bucket(self.bucket_name)
        blob = bucket.blob(gcs_csv_path)
        
        with open(import_csv_path, 'rb') as f:
            blob.upload_from_file(f)
        
        logger.info(f"📄 Created AutoML import CSV: gs://{self.bucket_name}/{gcs_csv_path}")
        
        # Save local copy with timestamp
        timestamped_path = Path("training_data") / f"automl_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        import_csv_path.rename(timestamped_path)
        
        return f"gs://{self.bucket_name}/{gcs_csv_path}"
    
    def get_upload_status(self) -> Dict[str, Any]:
        """Get status of uploaded training data"""
        
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            blobs = list(bucket.list_blobs(prefix="training_images/"))
            
            categories = {}
            total_images = 0
            
            for blob in blobs:
                if blob.name.endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                    total_images += 1
                    # Extract category from path
                    path_parts = blob.name.split('/')
                    if len(path_parts) >= 2:
                        category = path_parts[1]
                        categories[category] = categories.get(category, 0) + 1
            
            return {
                "success": True,
                "total_images": total_images,
                "categories": categories,
                "bucket_name": self.bucket_name
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get upload status: {e}")
            return {"success": False, "error": str(e)}

def main():
    """Main function"""
    
    print("🚀 Enhanced Pattern-Based Training Data Upload")
    print("=" * 60)
    
    # Check if training data exists
    training_csv = Path("training_data/labels/training_labels.csv")
    if not training_csv.exists():
        print("❌ Training labels CSV not found!")
        print("📋 Please run: python enhanced_training_collector.py")
        return
    
    try:
        # Initialize uploader
        uploader = PatternBasedAutoMLUploader()
        
        # Show current status
        status = uploader.get_upload_status()
        if status['success']:
            print("📊 Current Upload Status:")
            print(f"   Total Images: {status['total_images']}")
            print(f"   Categories: {list(status['categories'].keys())}")
            for cat, count in status['categories'].items():
                print(f"      • {cat}: {count} images")
        
        # Ask for confirmation
        response = input(f"\n🤔 Upload training data from {training_csv}? (y/n): ").lower().strip()
        if response != 'y':
            print("❌ Upload cancelled")
            return
        
        # Upload training data
        print("\n📤 Starting pattern-based training data upload...")
        success = uploader.upload_training_data_from_csv(str(training_csv))
        
        if success:
            print("\n🎉 Training data upload completed successfully!")
            print("\n🎯 Next Steps:")
            print("   1. Review uploaded data in Google Cloud Storage")
            print("   2. Start AutoML training: python automl_training_pipeline.py")
            print("   3. Monitor training progress: python check_training_status.py")
        else:
            print("\n❌ Training data upload failed!")
            print("   Check the logs above for error details")
    
    except Exception as e:
        logger.error(f"❌ Upload failed: {e}")
        print(f"\n💥 Error: {e}")

if __name__ == "__main__":
    main()
