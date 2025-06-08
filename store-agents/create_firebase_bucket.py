#!/usr/bin/env python3
"""
Script to create Firebase Storage bucket programmatically
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

def create_firebase_storage_bucket():
    """Create Firebase Storage bucket programmatically"""
    
    try:
        # Set credentials
        cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
        project_id = os.getenv("FIREBASE_PROJECT_ID")
        
        if not cred_path or not os.path.exists(cred_path):
            logger.error(f"Service account key not found at: {cred_path}")
            return False
            
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = cred_path
        
        # Initialize GCS client
        client = storage.Client(project=project_id)
        bucket_name = f'{project_id}.appspot.com'
        
        logger.info(f"Creating bucket: {bucket_name}")
        
        # Create bucket
        bucket = client.bucket(bucket_name)
        
        # Try creating in different locations
        locations = ['us-central1', 'us-east1', 'us-west1', 'europe-west1']
        
        for location in locations:
            try:
                logger.info(f"Attempting to create bucket in location: {location}")
                new_bucket = client.create_bucket(bucket, location=location)
                logger.info(f"✅ Successfully created bucket: {bucket_name} in {location}")
                
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
                
                return True
                
            except Exception as location_error:
                logger.warning(f"Failed to create bucket in {location}: {str(location_error)}")
                if "already exists" in str(location_error).lower():
                    logger.info(f"✅ Bucket {bucket_name} already exists!")
                    return True
                continue
        
        logger.error("❌ Failed to create bucket in any location")
        return False
        
    except Exception as e:
        logger.error(f"❌ Failed to create bucket: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("🏗️  Creating Firebase Storage bucket...")
    
    success = create_firebase_storage_bucket()
    
    if success:
        logger.info("\n🎉 Firebase Storage bucket created successfully!")
        logger.info("Running storage test...")
        
        # Run the storage test
        os.system("python test_firebase_storage.py")
    else:
        logger.error("\n❌ Failed to create Firebase Storage bucket.")
        logger.info("\n📝 Manual setup required:")
        logger.info("1. Go to https://console.firebase.google.com/")
        logger.info("2. Select your project: deve-01")
        logger.info("3. Go to Storage > Get Started")
        logger.info("4. Choose your storage location")
        logger.info("5. Create the bucket")
