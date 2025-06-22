#!/usr/bin/env python3
"""
AutoML Model Training Script
Phase 3: Train custom product recognition model
"""
import os
import logging
import json
import time
from google.cloud import automl
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoMLTrainer:
    """Handle AutoML model training and deployment"""
    
    def __init__(self, project_id: str = "deve-01", location: str = "us-central1"):
        self.project_id = project_id
        self.location = location
        self.client = automl.AutoMlClient()
        
    def load_dataset_info(self) -> Dict[str, Any]:
        """Load dataset information from setup"""
        try:
            with open("automl_dataset_info.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("❌ Dataset info not found. Run automl_setup.py first")
            return {}
    
    def upload_training_data(self, dataset_path: str, csv_file_path: str) -> bool:
        """Upload training images and labels to dataset"""
        
        try:
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
            
            # Wait for completion (this can take 10-30 minutes)
            print("⏳ Waiting for data import to complete...")
            result = response.result(timeout=1800)  # 30 minute timeout
            
            logger.info("✅ Training data imported successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to upload training data: {e}")
            return False
    
    def train_model(self, dataset_path: str, model_name: str = "zimbabwe_product_detector_v1") -> str:
        """Train the AutoML object detection model"""
        
        try:
            logger.info(f"🚀 Starting model training: {model_name}")
            
            # Configure model metadata for object detection
            model_metadata = automl.ImageObjectDetectionModelMetadata(
                # Training budget in milli node hours (24000 = 24 hours)
                train_budget_milli_node_hours=24000,
                
                # Model type - high accuracy for production use
                model_type=automl.ImageObjectDetectionModelMetadata.ModelType.CLOUD_HIGH_ACCURACY_1
            )
            
            # Create model configuration
            model = automl.Model(
                display_name=model_name,
                dataset_id=dataset_path.split('/')[-1],
                image_object_detection_model_metadata=model_metadata,
            )
            
            # Start training operation
            parent = f"projects/{self.project_id}/locations/{self.location}"
            response = self.client.create_model(
                parent=parent,
                model=model
            )
            
            operation_name = response.operation.name
            logger.info(f"🎯 Training started!")
            logger.info(f"Operation: {operation_name}")
            logger.info("⏳ Training will take approximately 6-24 hours...")
            
            # Save training info
            training_info = {
                "model_name": model_name,
                "operation_name": operation_name,
                "dataset_path": dataset_path,
                "training_started": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "training",
                "estimated_completion": "6-24 hours"
            }
            
            with open("model_training_info.json", "w") as f:
                json.dump(training_info, f, indent=2)
            
            logger.info("💾 Training info saved to: model_training_info.json")
            
            return operation_name
            
        except Exception as e:
            logger.error(f"❌ Failed to start training: {e}")
            return ""
    
    def check_training_status(self) -> Dict[str, Any]:
        """Check status of ongoing training operation"""
        
        try:
            with open("model_training_info.json", "r") as f:
                training_info = json.load(f)
        except FileNotFoundError:
            return {"error": "No training operation found"}
        
        operation_name = training_info.get("operation_name")
        if not operation_name:
            return {"error": "Invalid training info"}
        
        try:
            # Get operation status
            operation = self.client._transport.operations_client.get_operation(
                name=operation_name
            )
            
            status = {
                "model_name": training_info.get("model_name"),
                "started": training_info.get("training_started"),
                "status": "unknown"
            }
            
            if operation.done:
                if operation.error.code != 0:
                    status["status"] = "failed"
                    status["error"] = operation.error.message
                else:
                    status["status"] = "completed"
                    status["model_path"] = operation.response.name
                    
                    # Update training info with completion
                    training_info.update({
                        "status": "completed",
                        "model_path": operation.response.name,
                        "completed_at": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                    with open("model_training_info.json", "w") as f:
                        json.dump(training_info, f, indent=2)
            else:
                status["status"] = "training"
                # Extract progress if available
                if hasattr(operation, 'metadata'):
                    status["progress"] = "Training in progress..."
            
            return status
            
        except Exception as e:
            return {"error": f"Failed to check status: {e}"}
    
    def deploy_model(self) -> bool:
        """Deploy trained model for predictions"""
        
        try:
            with open("model_training_info.json", "r") as f:
                training_info = json.load(f)
        except FileNotFoundError:
            logger.error("❌ No training info found")
            return False
        
        model_path = training_info.get("model_path")
        if not model_path:
            logger.error("❌ Model not trained yet")
            return False
        
        try:
            # Deploy model for online prediction
            response = self.client.deploy_model(name=model_path)
            
            logger.info("🚀 Model deployment started...")
            logger.info(f"Operation: {response.operation.name}")
            
            # Wait for deployment (usually 5-10 minutes)
            result = response.result(timeout=600)  # 10 minute timeout
            
            logger.info("✅ Model deployed successfully!")
            
            # Update training info
            training_info.update({
                "deployment_status": "deployed",
                "deployed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "prediction_endpoint": model_path
            })
            
            with open("model_training_info.json", "w") as f:
                json.dump(training_info, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Deployment failed: {e}")
            return False

def main():
    """Main training workflow"""
    
    print("🤖 AutoML Model Training Workflow")
    print("=" * 50)
    
    trainer = AutoMLTrainer()
    
    # Load dataset info
    dataset_info = trainer.load_dataset_info()
    if not dataset_info:
        print("❌ Please run automl_setup.py first")
        return
    
    dataset_path = dataset_info.get("dataset_path")
    print(f"📊 Using dataset: {dataset_path}")
    
    # Check if we have training data
    training_csv = "gs://deve-01-automl-training/labels/training_data.csv"
    print(f"📁 Training data: {training_csv}")
    
    print("\n🔄 Choose an option:")
    print("1. Upload training data and start training")
    print("2. Check training status")
    print("3. Deploy completed model")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        print("\n1️⃣ Uploading training data...")
        if trainer.upload_training_data(dataset_path, training_csv):
            print("\n2️⃣ Starting model training...")
            operation = trainer.train_model(dataset_path)
            if operation:
                print("✅ Training started successfully!")
                print("⏰ Check back in 6-24 hours for completion")
            else:
                print("❌ Failed to start training")
        else:
            print("❌ Failed to upload training data")
    
    elif choice == "2":
        print("\n🔍 Checking training status...")
        status = trainer.check_training_status()
        
        if "error" in status:
            print(f"❌ {status['error']}")
        else:
            print(f"📋 Model: {status.get('model_name', 'Unknown')}")
            print(f"📅 Started: {status.get('started', 'Unknown')}")
            print(f"🎯 Status: {status.get('status', 'Unknown')}")
            
            if status.get("status") == "completed":
                print("✅ Training completed!")
                print(f"🎯 Model path: {status.get('model_path', 'Unknown')}")
                print("💡 Run option 3 to deploy the model")
            elif status.get("status") == "training":
                print("⏳ Training still in progress...")
            elif status.get("status") == "failed":
                print(f"❌ Training failed: {status.get('error', 'Unknown')}")
    
    elif choice == "3":
        print("\n🚀 Deploying model...")
        if trainer.deploy_model():
            print("✅ Model deployed successfully!")
            print("🎉 Ready for production use!")
        else:
            print("❌ Deployment failed")
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
