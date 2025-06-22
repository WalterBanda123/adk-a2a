#!/usr/bin/env python3
"""
Firebase AutoML Integration with Existing Vision System
Connects current enhanced vision processor with AutoML training data collection
"""
import os
import json
import logging
import firebase_admin
from firebase_admin import credentials, storage as firebase_storage
from enhanced_add_product_vision_tool_clean import EnhancedProductVisionProcessor
import base64
import time
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoMLDataCollector:
    """Collect training data from current vision system for AutoML"""
    
    def __init__(self):
        self.project_id = "deve-01"
        self.firebase_bucket_name = f"{self.project_id}.appspot.com"
        self.training_folder = "automl-training"
        
        # Initialize Firebase if not already initialized
        try:
            firebase_admin.get_app()
        except ValueError:
            cred = credentials.Certificate('firebase-service-account-key.json')
            firebase_admin.initialize_app(cred, {
                'storageBucket': self.firebase_bucket_name
            })
        
        self.bucket = firebase_storage.bucket()
        self.vision_processor = EnhancedProductVisionProcessor()
        
    def process_and_collect_training_data(self, image_data: str, user_feedback: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process image with current system and collect data for AutoML training
        
        Args:
            image_data: Base64 encoded image
            user_feedback: User corrections to the detection results
        """
        
        try:
            # Process with current enhanced system
            current_result = self.vision_processor.process_image(image_data)
            
            # Generate filename
            timestamp = int(time.time())
            category = current_result.get('category', 'unknown').lower()
            brand = current_result.get('brand', 'unknown').lower()
            filename = f"{category}_{brand}_{timestamp}.jpg"
            
            # Upload image to Firebase Storage
            image_path = f"{self.training_folder}/images/{category}/{filename}"
            blob = self.bucket.blob(image_path)
            
            # Decode and upload image
            image_bytes = base64.b64decode(image_data)
            blob.upload_from_string(image_bytes, content_type='image/jpeg')
            
            firebase_url = f"gs://{self.firebase_bucket_name}/{image_path}"
            
            # Generate training labels
            training_labels = self._generate_training_labels(
                firebase_url, current_result, user_feedback
            )
            
            # Save to training CSV
            self._append_to_training_csv(training_labels)
            
            logger.info(f"✅ Collected training data: {firebase_url}")
            
            return {
                "status": "success",
                "image_url": firebase_url,
                "current_detection": current_result,
                "training_labels": training_labels,
                "user_feedback": user_feedback
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to collect training data: {e}")
            return {"status": "error", "error": str(e)}
    
    def _generate_training_labels(self, image_url: str, detection_result: Dict[str, Any], user_feedback: Dict[str, Any] = None) -> List[str]:
        """Generate AutoML training labels from detection results"""
        
        labels = []
        
        # Use user feedback if available, otherwise use current detection
        final_result = user_feedback if user_feedback else detection_result
        
        # Generate bounding box coordinates (simplified - in real implementation, you'd need actual coordinates)
        # For now, using mock coordinates that cover different parts of the image
        coords = {
            'brand': '0.1,0.1,0.6,0.4',      # Top-left area
            'product_name': '0.1,0.4,0.8,0.7',  # Middle area  
            'size': '0.6,0.1,0.9,0.3',      # Top-right area
            'category': '0.1,0.7,0.5,0.9'   # Bottom area
        }
        
        # Brand label
        if final_result.get('brand'):
            labels.append(f"{image_url},brand,{coords['brand']}")
        
        # Product name label
        if final_result.get('product_name'):
            labels.append(f"{image_url},product_name,{coords['product_name']}")
        
        # Size label
        if final_result.get('size'):
            labels.append(f"{image_url},size,{coords['size']}")
        
        # Category label
        if final_result.get('category'):
            labels.append(f"{image_url},category,{coords['category']}")
        
        return labels
    
    def _append_to_training_csv(self, labels: List[str]):
        """Append new labels to training CSV file"""
        
        try:
            csv_file = "collected_training_data.csv"
            
            # Create header if file doesn't exist
            if not os.path.exists(csv_file):
                with open(csv_file, 'w') as f:
                    f.write("# AutoML Training Data - Collected from Live System\n")
                    f.write("# IMAGE_URI,LABEL,XMIN,YMIN,XMAX,YMAX\n")
            
            # Append new labels
            with open(csv_file, 'a') as f:
                for label in labels:
                    f.write(label + '\n')
            
            # Also upload to Firebase
            firebase_csv_path = f"{self.training_folder}/labels/collected_training_data.csv"
            blob = self.bucket.blob(firebase_csv_path)
            
            with open(csv_file, 'rb') as f:
                blob.upload_from_file(f)
            
        except Exception as e:
            logger.error(f"❌ Failed to save training data: {e}")
    
    def generate_training_report(self) -> Dict[str, Any]:
        """Generate report on collected training data"""
        
        try:
            csv_file = "collected_training_data.csv"
            
            if not os.path.exists(csv_file):
                return {"status": "no_data", "message": "No training data collected yet"}
            
            with open(csv_file, 'r') as f:
                lines = f.readlines()
            
            # Filter out comments
            data_lines = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
            
            # Analyze data
            images = set()
            labels = {}
            categories = set()
            
            for line in data_lines:
                parts = line.split(',')
                if len(parts) >= 2:
                    image_path = parts[0]
                    label = parts[1]
                    
                    images.add(image_path)
                    labels[label] = labels.get(label, 0) + 1
                    
                    # Extract category from image path
                    if '/images/' in image_path:
                        category = image_path.split('/images/')[1].split('/')[0]
                        categories.add(category)
            
            report = {
                "status": "success",
                "total_images": len(images),
                "total_labels": sum(labels.values()),
                "label_distribution": labels,
                "categories": list(categories),
                "ready_for_automl": len(images) >= 50,  # Minimum for decent AutoML model
                "recommendation": self._get_collection_recommendation(len(images), labels)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Failed to generate report: {e}")
            return {"status": "error", "error": str(e)}
    
    def _get_collection_recommendation(self, image_count: int, labels: Dict[str, int]) -> str:
        """Get recommendation for training data collection"""
        
        if image_count < 50:
            return f"Need {50 - image_count} more images for minimum AutoML training"
        elif image_count < 100:
            return f"Good start! Collect {100 - image_count} more images for better accuracy"
        elif image_count < 300:
            return f"Great progress! {300 - image_count} more images for production-ready model"
        else:
            return "Excellent! You have enough data for high-quality AutoML training"

def main():
    """Demo the data collection integration"""
    
    print("🔥 AutoML Data Collection Integration")
    print("=" * 50)
    
    collector = AutoMLDataCollector()
    
    # Check if we have sample image to test with
    sample_image = "images-mazoe-ruspberry.jpeg"
    
    if os.path.exists(sample_image):
        print(f"\n📸 Processing sample image: {sample_image}")
        
        # Read and encode image
        with open(sample_image, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Process and collect data
        result = collector.process_and_collect_training_data(image_data)
        
        if result["status"] == "success":
            print(f"✅ Image uploaded: {result['image_url']}")
            print(f"🔍 Current detection: {result['current_detection']}")
            print(f"🏷️  Training labels: {len(result['training_labels'])} generated")
        else:
            print(f"❌ Error: {result['error']}")
    
    # Generate training report
    print("\n📊 Training Data Report:")
    report = collector.generate_training_report()
    
    if report["status"] == "success":
        print(f"   📸 Total Images: {report['total_images']}")
        print(f"   🏷️  Total Labels: {report['total_labels']}")
        print(f"   🎯 Categories: {', '.join(report['categories'])}")
        print(f"   ✅ Ready for AutoML: {report['ready_for_automl']}")
        print(f"   💡 Recommendation: {report['recommendation']}")
    else:
        print(f"   ❌ {report.get('message', 'Error generating report')}")
    
    print(f"\n🎯 Next Steps:")
    print("1. Integrate this collector into your product detection workflow")
    print("2. Collect user feedback on incorrect detections")  
    print("3. Use feedback to improve training data")
    print("4. Run automl_trainer_firebase.py when you have 50+ images")

if __name__ == "__main__":
    main()
