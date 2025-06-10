#!/usr/bin/env python3
"""
AutoML Data Import and Training Pipeline
Import training data and train the custom model
"""
import os
import json
import time
from google.cloud import automl
from google.cloud import storage
from typing import List, Dict, Any

class AutoMLTrainingPipeline:
    """Handle data import and model training"""
    
    def __init__(self):
        # Load dataset info
        with open('automl_dataset_info.json', 'r') as f:
            self.dataset_info = json.load(f)
        
        self.project_id = self.dataset_info['project_id']
        self.location = self.dataset_info['location']
        self.dataset_path = self.dataset_info['dataset_path']
        self.bucket_name = self.dataset_info['bucket_name']
        
        # Initialize clients
        self.automl_client = automl.AutoMlClient()
        self.storage_client = storage.Client(project=self.project_id)
        
    def upload_training_csv(self, csv_file: str) -> str:
        """Upload training CSV to GCS bucket"""
        
        if not os.path.exists(csv_file):
            raise FileNotFoundError(f"Training CSV not found: {csv_file}")
        
        bucket = self.storage_client.bucket(self.bucket_name)
        blob_name = f"labels/{os.path.basename(csv_file)}"
        blob = bucket.blob(blob_name)
        
        print(f"📤 Uploading training data: {csv_file}")
        blob.upload_from_filename(csv_file)
        
        gcs_path = f"gs://{self.bucket_name}/{blob_name}"
        print(f"✅ Training data uploaded to: {gcs_path}")
        
        return gcs_path
    
    def import_training_data(self, csv_gcs_path: str) -> bool:
        """Import training data into AutoML dataset"""
        
        print(f"📥 Importing training data to dataset...")
        print(f"   Dataset: {self.dataset_path}")
        print(f"   CSV: {csv_gcs_path}")
        
        try:
            # Create import config
            input_config = automl.InputConfig(
                gcs_source=automl.GcsSource(input_uris=[csv_gcs_path])
            )
            
            # Import data
            operation = self.automl_client.import_data(
                name=self.dataset_path,
                input_config=input_config
            )
            
            print("⏳ Importing data... This may take a few minutes.")
            result = operation.result(timeout=1800)  # 30 minutes timeout
            
            print("✅ Training data imported successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to import training data: {e}")
            return False
    
    def train_model(self, model_name: str = "zimbabwe_product_model") -> str:
        """Train AutoML model"""
        
        print(f"🤖 Starting model training: {model_name}")
        print("⏳ This will take 6-24 hours depending on data size...")
        
        try:
            # Define model metadata
            model_metadata = automl.ImageObjectDetectionModelMetadata(
                train_budget_milli_node_hours=20000,  # 20 node hours
                stop_reason=None,
            )
            
            model = automl.Model(
                display_name=model_name,
                dataset_id=self.dataset_path.split('/')[-1],
                image_object_detection_model_metadata=model_metadata,
            )
            
            # Start training
            parent = f"projects/{self.project_id}/locations/{self.location}"
            operation = self.automl_client.create_model(
                parent=parent,
                model=model
            )
            
            model_path = operation.name
            print(f"🚀 Training started!")
            print(f"📊 Model operation: {model_path}")
            
            # Save training info
            training_info = {
                "model_name": model_name,
                "operation_path": model_path,
                "dataset_path": self.dataset_path,
                "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "training",
                "estimated_completion": "6-24 hours"
            }
            
            with open("automl_training_info.json", "w") as f:
                json.dump(training_info, f, indent=2)
            
            print("💾 Training info saved to automl_training_info.json")
            print("\n📋 Next Steps:")
            print("1. Monitor training progress in Google Cloud Console")
            print("2. Training will complete in 6-24 hours")
            print("3. Use check_training_status.py to monitor progress")
            print("4. Deploy model when training completes")
            
            return model_path
            
        except Exception as e:
            print(f"❌ Failed to start training: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def get_dataset_stats(self) -> Dict[str, Any]:
        """Get dataset statistics"""
        
        try:
            dataset = self.automl_client.get_dataset(name=self.dataset_path)
            
            stats = {
                "name": dataset.display_name,
                "create_time": str(dataset.create_time),
                "example_count": dataset.example_count,
                "etag": dataset.etag
            }
            
            print("📊 Dataset Statistics:")
            print(f"   Name: {stats['name']}")
            print(f"   Created: {stats['create_time']}")
            print(f"   Examples: {stats['example_count']}")
            
            return stats
            
        except Exception as e:
            print(f"❌ Failed to get dataset stats: {e}")
            return {}

def main():
    """Main training pipeline"""
    
    print("🚀 AutoML Training Pipeline")
    print("=" * 50)
    
    pipeline = AutoMLTrainingPipeline()
    
    # Step 1: Check dataset
    print("\n1️⃣ Checking Dataset...")
    stats = pipeline.get_dataset_stats()
    
    if stats.get('example_count', 0) == 0:
        print("\n📤 No training data found. Starting data import...")
        
        # Check for training CSV
        csv_files = ['training_data.csv', 'training_data_template.csv']
        training_csv = None
        
        for csv_file in csv_files:
            if os.path.exists(csv_file):
                training_csv = csv_file
                break
        
        if not training_csv:
            print("❌ No training CSV found. Please create training_data.csv")
            print("💡 Use training_data_template.csv as a starting point")
            return
        
        # Upload and import data
        print(f"\n2️⃣ Using training file: {training_csv}")
        gcs_path = pipeline.upload_training_csv(training_csv)
        
        print("\n3️⃣ Importing training data...")
        if not pipeline.import_training_data(gcs_path):
            print("❌ Data import failed")
            return
        
        # Check stats again
        print("\n📊 Updated dataset statistics:")
        pipeline.get_dataset_stats()
    
    # Step 2: Start training
    print("\n4️⃣ Starting Model Training...")
    model_path = pipeline.train_model()
    
    if model_path:
        print("\n🎉 Training Pipeline Started Successfully!")
        print("=" * 50)
        print("📋 What's Happening:")
        print("1. ⏳ Model is training (6-24 hours)")
        print("2. 📊 Monitor progress in Google Cloud Console")
        print("3. 🔔 Check status with: python check_training_status.py")
        print("4. 🚀 Deploy when training completes")
        
        print(f"\n📁 Files Created:")
        print("   • automl_training_info.json - Training details")
        print("   • Check Google Cloud Console for progress")
        
    else:
        print("\n❌ Training failed to start")

if __name__ == "__main__":
    main()
