#!/usr/bin/env python3
"""
Firebase AutoML Model Training Script
Phase 3: Train custom product recognition model using Firebase Storage
"""
import os
import logging
import json
import time
import firebase_admin
from firebase_admin import credentials, storage as firebase_storage
from google.cloud import automl
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FirebaseAutoMLTrainer:
    """Handle AutoML model training using Firebase Storage"""
    
    def __init__(self, project_id: str = "deve-01", location: str = "us-central1"):
        self.project_id = project_id
        self.location = location
        self.firebase_bucket_name = f"{project_id}.appspot.com"
        self.training_folder = "automl-training"
        
        # Initialize Firebase if not already initialized
        try:
            firebase_admin.get_app()
            logger.info("✅ Firebase already initialized")
        except ValueError:
            # Initialize Firebase
            cred = credentials.Certificate('firebase-service-account-key.json')
            firebase_admin.initialize_app(cred, {
                'storageBucket': self.firebase_bucket_name
            })
            logger.info("✅ Firebase initialized")
        
        # Initialize AutoML client
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'firebase-service-account-key.json'
        self.client = automl.AutoMlClient()
        
        # Get Firebase storage bucket
        self.bucket = firebase_storage.bucket()
        
    def load_dataset_info(self) -> Dict[str, Any]:
        """Load dataset information from Firebase or local file"""
        try:
            # Try to load from Firebase first
            blob = self.bucket.blob(f"{self.training_folder}/datasets/dataset_info.json")
            if blob.exists():
                dataset_info = json.loads(blob.download_as_text())
                logger.info("✅ Loaded dataset info from Firebase Storage")
                return dataset_info
        except Exception as e:
            logger.warning(f"⚠️  Could not load from Firebase: {e}")
        
        # Fallback to local file
        try:
            with open("automl_dataset_info.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("❌ Dataset info not found. Run automl_setup_firebase.py first")
            return {}
    
    def upload_training_csv_to_firebase(self, local_csv_path: str) -> str:
        """Upload training CSV to Firebase Storage"""
        
        try:
            if not os.path.exists(local_csv_path):
                logger.error(f"❌ CSV file not found: {local_csv_path}")
                return ""
            
            # Upload CSV to Firebase Storage
            csv_blob_path = f"{self.training_folder}/labels/training_data.csv"
            blob = self.bucket.blob(csv_blob_path)
            
            with open(local_csv_path, 'rb') as csv_file:
                blob.upload_from_file(csv_file)
            
            firebase_csv_url = f"gs://{self.firebase_bucket_name}/{csv_blob_path}"
            logger.info(f"✅ Uploaded training CSV: {firebase_csv_url}")
            
            return firebase_csv_url
            
        except Exception as e:
            logger.error(f"❌ Failed to upload CSV: {e}")
            return ""
    
    def upload_training_data(self, dataset_path: str, csv_file_path: str) -> bool:
        """Upload training images and labels to AutoML dataset"""
        
        try:
            # First upload CSV to Firebase if it's a local file
            if not csv_file_path.startswith("gs://"):
                csv_file_path = self.upload_training_csv_to_firebase(csv_file_path)
                if not csv_file_path:
                    return False
            
            logger.info(f"📤 Uploading training data from: {csv_file_path}")
            
            # Prepare input configuration
            gcs_source = automl.GcsSource(input_uris=[csv_file_path])
            input_config = automl.InputConfig(gcs_source=gcs_source)
            
            # Start import operation
            response = self.client.import_data(
                name=dataset_path,
                input_config=input_config
            )
            
            logger.info("⏳ Import operation started...")
            logger.info(f"Operation name: {response.operation.name}")
            
            # Wait for import to complete
            logger.info("⏳ Waiting for data import to complete (this may take several minutes)...")
            result = response.result(timeout=1800)  # 30 minutes timeout
            
            logger.info("✅ Training data uploaded successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to upload training data: {e}")
            return False
    
    def create_model(self, dataset_path: str, model_name: str = "zimbabwe_product_model") -> str:
        """Create and train AutoML model"""
        
        try:
            logger.info(f"🧠 Creating AutoML model: {model_name}")
            
            # Define model metadata for object detection
            model_metadata = automl.ImageObjectDetectionModelMetadata(
                # Set training budget (node hours)
                # 1 node hour = minimum, 20 node hours = recommended for production
                node_count=1,  # Start with minimum for testing
                # You can increase this to 8-20 for better accuracy
            )
            
            model = automl.Model(
                display_name=model_name,
                dataset_id=dataset_path.split("/")[-1],
                image_object_detection_model_metadata=model_metadata,
            )
            
            # Start training
            parent = f"projects/{self.project_id}/locations/{self.location}"
            response = self.client.create_model(parent=parent, model=model)
            
            logger.info("🚀 Model training started!")
            logger.info(f"Operation name: {response.operation.name}")
            logger.info("⏳ Training will take 6-24 hours depending on data size...")
            
            # Don't wait for completion as it takes hours
            # Instead, save operation info for later checking
            operation_info = {
                "operation_name": response.operation.name,
                "model_name": model_name,
                "dataset_path": dataset_path,
                "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "training_started"
            }
            
            # Save operation info locally
            with open("automl_training_operation.json", "w") as f:
                json.dump(operation_info, f, indent=2)
            
            # Also save to Firebase
            operation_blob = self.bucket.blob(f"{self.training_folder}/models/training_operation.json")
            operation_blob.upload_from_string(json.dumps(operation_info, indent=2))
            
            logger.info("💾 Training operation info saved")
            logger.info("💡 Use check_training_status.py to monitor progress")
            
            return response.operation.name
            
        except Exception as e:
            logger.error(f"❌ Failed to create model: {e}")
            return ""
    
    def check_training_status(self) -> Dict[str, Any]:
        """Check status of ongoing training operation"""
        
        try:
            # Load operation info
            with open("automl_training_operation.json", "r") as f:
                operation_info = json.load(f)
            
            operation_name = operation_info["operation_name"]
            logger.info(f"🔍 Checking training status for: {operation_name}")
            
            # Get operation status
            operation = self.client.get_operation(name=operation_name)
            
            if operation.done:
                if operation.error:
                    logger.error(f"❌ Training failed: {operation.error}")
                    return {"status": "failed", "error": str(operation.error)}
                else:
                    model = operation.result
                    logger.info(f"✅ Training completed! Model: {model.name}")
                    
                    # Update operation info
                    operation_info["status"] = "completed"
                    operation_info["model_path"] = model.name
                    operation_info["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Save updated info
                    with open("automl_training_operation.json", "w") as f:
                        json.dump(operation_info, f, indent=2)
                    
                    return {"status": "completed", "model_path": model.name}
            else:
                logger.info("⏳ Training still in progress...")
                return {"status": "training", "operation": operation_name}
                
        except FileNotFoundError:
            logger.error("❌ No training operation found. Start training first.")
            return {"status": "not_found"}
        except Exception as e:
            logger.error(f"❌ Failed to check status: {e}")
            return {"status": "error", "error": str(e)}
    
    def generate_training_summary(self, csv_file_path: str) -> Dict[str, Any]:
        """Generate summary of training data"""
        
        try:
            if csv_file_path.startswith("gs://"):
                # Download from Firebase to analyze
                blob_path = csv_file_path.replace(f"gs://{self.firebase_bucket_name}/", "")
                blob = self.bucket.blob(blob_path)
                csv_content = blob.download_as_text()
                lines = csv_content.strip().split('\n')
            else:
                # Local file
                with open(csv_file_path, 'r') as f:
                    lines = f.readlines()
            
            # Filter out comments and empty lines
            data_lines = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
            
            if not data_lines:
                return {"error": "No training data found in CSV"}
            
            # Analyze data
            labels = {}
            images = set()
            
            for line in data_lines:
                parts = line.split(',')
                if len(parts) >= 2:
                    image_path = parts[0]
                    label = parts[1]
                    
                    images.add(image_path)
                    labels[label] = labels.get(label, 0) + 1
            
            summary = {
                "total_images": len(images),
                "total_labels": sum(labels.values()),
                "unique_labels": len(labels),
                "label_distribution": labels,
                "ready_for_training": len(images) >= 10  # Minimum recommendation
            }
            
            logger.info("📊 Training Data Summary:")
            logger.info(f"   📸 Total Images: {summary['total_images']}")
            logger.info(f"   🏷️  Total Labels: {summary['total_labels']}")
            logger.info(f"   🎯 Unique Labels: {summary['unique_labels']}")
            logger.info(f"   ✅ Ready for Training: {summary['ready_for_training']}")
            
            if summary['ready_for_training']:
                logger.info("🚀 You have enough data to start training!")
            else:
                logger.warning(f"⚠️  Need at least 10 images (current: {summary['total_images']})")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze training data: {e}")
            return {"error": str(e)}

def main():
    """Run training process"""
    
    print("🔥 Firebase AutoML Model Training")
    print("=" * 50)
    
    trainer = FirebaseAutoMLTrainer()
    
    # Step 1: Load dataset info
    print("\n1️⃣ Loading Dataset Information...")
    dataset_info = trainer.load_dataset_info()
    
    if not dataset_info:
        print("❌ No dataset found. Run automl_setup_firebase.py first")
        return
    
    dataset_path = dataset_info.get("dataset_path", "")
    if not dataset_path:
        print("❌ Invalid dataset information")
        return
    
    print(f"✅ Dataset: {dataset_path}")
    
    # Step 2: Check for training data
    print("\n2️⃣ Checking Training Data...")
    csv_files = [
        "firebase_training_data_template.csv",
        "training_data.csv",
        f"gs://{trainer.firebase_bucket_name}/{trainer.training_folder}/labels/training_data.csv"
    ]
    
    training_csv = None
    for csv_file in csv_files:
        if csv_file.startswith("gs://") or os.path.exists(csv_file):
            training_csv = csv_file
            break
    
    if not training_csv:
        print("❌ No training data CSV found")
        print("💡 Create training_data.csv with your labeled images")
        return
    
    # Step 3: Analyze training data
    print("\n3️⃣ Analyzing Training Data...")
    summary = trainer.generate_training_summary(training_csv)
    
    if "error" in summary:
        print(f"❌ Error analyzing data: {summary['error']}")
        return
    
    if not summary.get("ready_for_training", False):
        print("⚠️  Not enough training data. Need at least 10 images.")
        print("📋 Add more images and labels to your CSV file")
        return
    
    # Step 4: Check if already training
    print("\n4️⃣ Checking Training Status...")
    status = trainer.check_training_status()
    
    if status["status"] == "training":
        print("⏳ Training already in progress")
        print(f"Operation: {status['operation']}")
        print("💡 Use this script again later to check completion status")
        return
    elif status["status"] == "completed":
        print("✅ Training already completed!")
        print(f"Model: {status['model_path']}")
        print("🚀 Ready to deploy!")
        return
    
    # Step 5: Upload training data
    print("\n5️⃣ Uploading Training Data...")
    if trainer.upload_training_data(dataset_path, training_csv):
        print("✅ Training data uploaded successfully")
    else:
        print("❌ Failed to upload training data")
        return
    
    # Step 6: Start training
    print("\n6️⃣ Starting Model Training...")
    operation_name = trainer.create_model(dataset_path)
    
    if operation_name:
        print("🚀 Training started successfully!")
        print("⏰ Training will take 6-24 hours")
        print("💡 Run this script again later to check progress")
    else:
        print("❌ Failed to start training")

if __name__ == "__main__":
    main()
