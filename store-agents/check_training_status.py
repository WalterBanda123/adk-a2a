#!/usr/bin/env python3
"""
AutoML Training Status Checker
Monitor training progress and model deployment
"""
import json
import time
from google.cloud import automl
from typing import Dict, Any

class AutoMLStatusChecker:
    """Check AutoML training and deployment status"""
    
    def __init__(self):
        # Load dataset and training info
        with open('automl_dataset_info.json', 'r') as f:
            self.dataset_info = json.load(f)
        
        self.project_id = self.dataset_info['project_id']
        self.location = self.dataset_info['location']
        
        # Check for training info
        try:
            with open('automl_training_info.json', 'r') as f:
                self.training_info = json.load(f)
        except FileNotFoundError:
            self.training_info = None
        
        self.automl_client = automl.AutoMlClient()
    
    def check_training_status(self) -> Dict[str, Any]:
        """Check current training status"""
        
        if not self.training_info:
            print("❌ No training info found. Run automl_training_pipeline.py first")
            return {}
        
        try:
            operation_name = self.training_info['operation_path']
            print(f"🔍 Checking training status...")
            print(f"   Operation: {operation_name}")
            
            # Get operation status
            operations_client = automl.AutoMlClient()
            
            # For long-running operations, we need to use the operations client
            from google.longrunning import operations_pb2
            from google.api_core import operations_v1
            
            # Create operations client
            transport = operations_client.transport
            operations_client_v1 = operations_v1.OperationsClient(transport)
            
            # Get operation
            operation = operations_client_v1.get_operation(
                request={"name": operation_name}
            )
            
            status_info = {
                "operation_name": operation_name,
                "done": operation.done,
                "started_at": self.training_info.get('started_at'),
                "model_name": self.training_info.get('model_name')
            }
            
            if operation.done:
                if operation.error.code != 0:
                    status_info["status"] = "failed"
                    status_info["error"] = operation.error.message
                    print("❌ Training failed!")
                    print(f"   Error: {operation.error.message}")
                else:
                    status_info["status"] = "completed"
                    status_info["model_path"] = operation.response.name
                    print("✅ Training completed successfully!")
                    print(f"   Model: {operation.response.name}")
                    
                    # Save model info
                    model_info = {
                        "model_name": self.training_info['model_name'],
                        "model_path": operation.response.name,
                        "completed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "status": "trained",
                        "ready_for_deployment": True
                    }
                    
                    with open("automl_model_info.json", "w") as f:
                        json.dump(model_info, f, indent=2)
                    
                    print("💾 Model info saved to automl_model_info.json")
            else:
                status_info["status"] = "training"
                print("⏳ Training still in progress...")
                print(f"   Started: {self.training_info.get('started_at')}")
                print("   Estimated: 6-24 hours total")
            
            return status_info
            
        except Exception as e:
            print(f"❌ Failed to check status: {e}")
            return {}
    
    def list_trained_models(self) -> List[Dict[str, Any]]:
        """List all trained models"""
        
        try:
            parent = f"projects/{self.project_id}/locations/{self.location}"
            models = self.automl_client.list_models(parent=parent)
            
            model_list = []
            print("📊 Available Models:")
            
            for model in models:
                model_info = {
                    "name": model.display_name,
                    "path": model.name,
                    "create_time": str(model.create_time),
                    "deployment_state": str(model.deployment_state)
                }
                model_list.append(model_info)
                
                print(f"   🤖 {model.display_name}")
                print(f"      Path: {model.name}")
                print(f"      Created: {model_info['create_time']}")
                print(f"      Status: {model_info['deployment_state']}")
                print()
            
            return model_list
            
        except Exception as e:
            print(f"❌ Failed to list models: {e}")
            return []
    
    def deploy_model(self, model_path: str) -> bool:
        """Deploy trained model for prediction"""
        
        try:
            print(f"🚀 Deploying model: {model_path}")
            
            operation = self.automl_client.deploy_model(name=model_path)
            
            print("⏳ Deploying model... This may take a few minutes.")
            result = operation.result(timeout=600)  # 10 minutes timeout
            
            print("✅ Model deployed successfully!")
            print("🎉 Ready for predictions!")
            
            # Update model info
            try:
                with open("automl_model_info.json", "r") as f:
                    model_info = json.load(f)
                
                model_info["deployment_status"] = "deployed"
                model_info["deployed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                model_info["ready_for_production"] = True
                
                with open("automl_model_info.json", "w") as f:
                    json.dump(model_info, f, indent=2)
                
                print("💾 Model info updated")
                
            except FileNotFoundError:
                pass
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to deploy model: {e}")
            return False

def main():
    """Main status checking"""
    
    print("🔍 AutoML Status Checker")
    print("=" * 40)
    
    checker = AutoMLStatusChecker()
    
    # Check training status
    print("\n1️⃣ Checking Training Status...")
    status = checker.check_training_status()
    
    if status.get('status') == 'completed':
        model_path = status.get('model_path')
        if model_path:
            print("\n🚀 Model is ready for deployment!")
            
            deploy = input("\n🤔 Deploy model now? (y/n): ").lower().strip()
            if deploy == 'y':
                print("\n2️⃣ Deploying Model...")
                if checker.deploy_model(model_path):
                    print("\n✅ Deployment complete!")
                    print("🎉 Your custom product recognition model is now live!")
                else:
                    print("\n❌ Deployment failed")
    
    # List all models
    print("\n3️⃣ All Available Models:")
    checker.list_trained_models()
    
    # Next steps
    if status.get('status') == 'training':
        print("\n📋 Next Steps:")
        print("1. ⏳ Wait for training to complete (check back in a few hours)")
        print("2. 🔄 Run this script again to check status")
        print("3. 🚀 Deploy model when ready")
    elif status.get('status') == 'completed':
        print("\n📋 Next Steps:")
        print("1. 🚀 Deploy the model (if not done)")
        print("2. 🔗 Integrate with your vision system")
        print("3. 🧪 Test with real product images")

if __name__ == "__main__":
    main()
