#!/usr/bin/env python3
"""
Simple Image Uploader for AutoML Training Data
Upload images to the correct bucket folder based on category
"""
import os
import subprocess
import sys
from pathlib import Path

BUCKET_NAME = "deve-01-automl-training"
CATEGORIES = {
    "staples": "images/staples/",
    "beverages": "images/beverages/", 
    "dairy": "images/dairy/",
    "cooking_oils": "images/cooking_oils/"
}

def upload_images(image_folder: str, category: str):
    """Upload images to GCS bucket"""
    
    if category not in CATEGORIES:
        print(f"❌ Invalid category. Choose from: {list(CATEGORIES.keys())}")
        return False
    
    image_folder_path = Path(image_folder)
    if not image_folder_path.exists():
        print(f"❌ Folder not found: {image_folder}")
        return False
    
    # Find image files
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(image_folder_path.glob(f"*{ext}"))
        image_files.extend(image_folder_path.glob(f"*{ext.upper()}"))
    
    if not image_files:
        print(f"❌ No image files found in {image_folder}")
        return False
    
    print(f"📸 Found {len(image_files)} images to upload")
    print(f"📁 Category: {category}")
    print(f"🎯 Destination: gs://{BUCKET_NAME}/{CATEGORIES[category]}")
    
    # Confirm upload
    response = input("\n🤔 Proceed with upload? (y/n): ").lower().strip()
    if response != 'y':
        print("❌ Upload cancelled")
        return False
    
    # Upload files
    success_count = 0
    for image_file in image_files:
        try:
            dest_path = f"gs://{BUCKET_NAME}/{CATEGORIES[category]}{image_file.name}"
            cmd = ["gsutil", "cp", str(image_file), dest_path]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Uploaded: {image_file.name}")
                success_count += 1
            else:
                print(f"❌ Failed: {image_file.name} - {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error uploading {image_file.name}: {e}")
    
    print(f"\n🎉 Upload complete: {success_count}/{len(image_files)} files uploaded")
    return success_count > 0

def list_bucket_contents(category: str = None):
    """List contents of the bucket"""
    
    if category and category in CATEGORIES:
        path = f"gs://{BUCKET_NAME}/{CATEGORIES[category]}"
    else:
        path = f"gs://{BUCKET_NAME}"
    
    try:
        cmd = ["gsutil", "ls", path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"📁 Contents of {path}:")
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    print(f"   📄 {line}")
            else:
                print("   (empty)")
        else:
            print(f"❌ Error listing bucket: {result.stderr}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function"""
    
    print("📸 AutoML Image Uploader")
    print("=" * 40)
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python upload_images.py <image_folder> <category>")
        print("  python upload_images.py --list [category]")
        print()
        print("Categories:", list(CATEGORIES.keys()))
        print()
        print("Examples:")
        print("  python upload_images.py ./my_photos staples")
        print("  python upload_images.py ./beverages beverages")
        print("  python upload_images.py --list staples")
        return
    
    if sys.argv[1] == "--list":
        category = sys.argv[2] if len(sys.argv) > 2 else None
        list_bucket_contents(category)
        return
    
    if len(sys.argv) < 3:
        print("❌ Please provide both image folder and category")
        return
    
    image_folder = sys.argv[1]
    category = sys.argv[2]
    
    upload_images(image_folder, category)

if __name__ == "__main__":
    main()
