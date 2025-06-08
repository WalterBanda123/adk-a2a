#!/usr/bin/env python3
"""
Script to create a regular GCS bucket for Firebase Storage
"""

import os
import logging
from dotenv import load_dotenv
from google.cloud import storage

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_storage_bucket():
    """Create a Google Cloud Storage bucket that can be used with Firebase"""
    
    try:
        # Set credentials
        cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
        project_id = os.getenv("FIREBASE_PROJECT_ID")
        
        if not cred_path or not os.path.exists(cred_path):
            logger.error(f"Service account key not found at: {cred_path}")
            return False, None
            
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = cred_path
        
        # Initialize GCS client
        client = storage.Client(project=project_id)
        
        # Try different bucket naming patterns
        bucket_names = [
            f'{project_id}-firebase-storage',
            f'{project_id}-store-images',
            f'store-assistant-{project_id}',
            f'{project_id}-product-images'
        ]
        
        for bucket_name in bucket_names:
            try:
                logger.info(f"Attempting to create bucket: {bucket_name}")
                
                # Check if bucket already exists
                try:
                    existing_bucket = client.bucket(bucket_name)
                    existing_bucket.reload()
                    logger.info(f"✅ Bucket {bucket_name} already exists!")
                    return True, bucket_name
                except:
                    pass  # Bucket doesn't exist, proceed to create
                
                # Create bucket
                bucket = client.bucket(bucket_name)
                new_bucket = client.create_bucket(bucket, location='us-central1')
                
                logger.info(f"✅ Successfully created bucket: {bucket_name}")
                
                # Set up CORS for web access
                cors_configuration = [
                    {
                        "origin": ["*"],
                        "method": ["GET", "POST", "PUT", "DELETE"],
                        "responseHeader": ["Content-Type"],
                        "maxAgeSeconds": 3600
                    }
                ]
                new_bucket.cors = cors_configuration
                new_bucket.patch()
                logger.info("✅ CORS configuration applied")
                
                # Make bucket publicly readable for uploaded images
                new_bucket.make_public(recursive=False, future=True)
                logger.info("✅ Public access configured")
                
                return True, bucket_name
                
            except Exception as bucket_error:
                logger.warning(f"Failed to create {bucket_name}: {str(bucket_error)}")
                continue
        
        logger.error("❌ Failed to create any bucket")
        return False, None
        
    except Exception as e:
        logger.error(f"❌ Failed to create bucket: {str(e)}")
        return False, None

def test_bucket_upload(bucket_name):
    """Test uploading to the created bucket"""
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        
        # Create a simple test image (1x1 pixel PNG)
        import base64
        from datetime import datetime
        
        test_image_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        )
        
        # Upload test image
        test_filename = f"test_images/test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        blob = bucket.blob(test_filename)
        
        blob.upload_from_string(
            test_image_data,
            content_type='image/png'
        )
        
        # Make it publicly accessible
        blob.make_public()
        public_url = blob.public_url
        
        logger.info(f"✅ Test image uploaded successfully!")
        logger.info(f"📎 Public URL: {public_url}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Upload test failed: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("🏗️  Creating Google Cloud Storage bucket...")
    
    success, bucket_name = create_storage_bucket()
    
    if success and bucket_name:
        logger.info(f"\n🎉 Storage bucket created: {bucket_name}")
        logger.info("Testing upload functionality...")
        
        upload_success = test_bucket_upload(bucket_name)
        
        if upload_success:
            logger.info(f"\n✅ All tests passed! Use bucket name: {bucket_name}")
            logger.info("\n📝 Update your image analysis service to use this bucket:")
            logger.info(f"   FIREBASE_STORAGE_BUCKET={bucket_name}")
        else:
            logger.error("\n❌ Upload test failed")
    else:
        logger.error("\n❌ Failed to create storage bucket")
        logger.info("\n📝 You may need to manually create a bucket in the Google Cloud Console:")
        logger.info("1. Go to https://console.cloud.google.com/storage")
        logger.info("2. Select your project: deve-01")
        logger.info("3. Click 'Create Bucket'")
        logger.info("4. Choose a unique name and location")
        logger.info("5. Create the bucket")
