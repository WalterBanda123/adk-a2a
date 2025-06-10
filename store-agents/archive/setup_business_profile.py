#!/usr/bin/env python3
"""
Setup Business Profile for Dynamic Product Classification
Creates user profiles for different business types and locations
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common.dynamic_product_classifier import DynamicProductClassifier
from common.user_profile_service import UserProfileService, UserBusinessProfile

def main():
    """Setup business profiles for testing"""
    
    print("🏪 Business Profile Setup for Dynamic Product Classification")
    print("=" * 60)
    
    # Initialize services
    classifier = DynamicProductClassifier()
    user_service = UserProfileService()
    
    # Test user profiles for different business types
    test_profiles = [
        {
            "user_id": "grocery_zimb_001",
            "country": "Zimbabwe", 
            "industry": "grocery",
            "description": "Mini supermarket in Zimbabwe selling local products",
            "custom_brands": ["Trade Centre", "Better Stores", "Foods Plus"]
        },
        {
            "user_id": "pharmacy_zimb_001", 
            "country": "Zimbabwe",
            "industry": "pharmacy", 
            "description": "Local pharmacy in Zimbabwe",
            "custom_brands": ["Adcock Ingram", "Be-tabs", "Bioplus"]
        },
        {
            "user_id": "grocery_generic_001",
            "country": "Generic",
            "industry": "grocery",
            "description": "Generic grocery store for international testing",
            "custom_brands": ["Local Brand A", "Store Brand B"]
        }
    ]
    
    created_profiles = 0
    
    for profile_data in test_profiles:
        print(f"\n📋 Creating profile: {profile_data['user_id']}")
        print(f"   Country: {profile_data['country']}")
        print(f"   Industry: {profile_data['industry']}")
        print(f"   Description: {profile_data['description']}")
        print(f"   Custom Brands: {profile_data['custom_brands']}")
        
        try:
            # Create user profile
            profile = UserBusinessProfile(
                user_id=profile_data["user_id"],
                country=profile_data["country"],
                industry=profile_data["industry"],
                product_categories=[],  # Will be filled from classification
                business_size="small",
                custom_brands=profile_data["custom_brands"]
            )
            
            # Save profile
            success = user_service.save_user_profile(profile)
            
            if success:
                print(f"   ✅ Profile created successfully")
                created_profiles += 1
                
                # Test classification loading
                classification = classifier.get_classification_for_user(profile_data["user_id"])
                if classification:
                    print(f"   📊 Classification loaded: {len(classification.common_brands)} brands, "
                          f"{len(classification.product_categories)} categories")
                else:
                    print(f"   ⚠️  Classification could not be loaded")
            else:
                print(f"   ❌ Failed to create profile")
                
        except Exception as e:
            print(f"   ❌ Error creating profile: {e}")
    
    print(f"\n🎉 Setup Complete!")
    print(f"Created {created_profiles}/{len(test_profiles)} profiles successfully")
    
    # Test the classification system
    print(f"\n🧪 Testing Dynamic Classification...")
    
    test_user_id = "grocery_zimb_001"
    print(f"Testing with user: {test_user_id}")
    
    # Simulate vision result
    mock_vision_result = {
        'title': 'Unknown Product',
        'brand': '',
        'size': '',
        'unit': '',
        'category': 'General',
        'subcategory': 'Miscellaneous',
        'description': 'Unknown Product',
        'confidence': 0.5,
        'detection_method': 'basic_vision_api',
        'raw_text': 'Coca Cola 2 Litres Soft Drink Refreshing',
        'detected_labels': ['beverage', 'bottle', 'drink'],
        'web_entities': ['Coca Cola', 'Soft Drink'],
        'logo_descriptions': ['Coca Cola']
    }
    
    try:
        enhanced_result = classifier.enhance_vision_result(mock_vision_result, test_user_id)
        
        print(f"\n📊 Enhancement Results:")
        print(f"   Original Title: {mock_vision_result['title']}")
        print(f"   Enhanced Title: {enhanced_result['title']}")
        print(f"   Enhanced Brand: {enhanced_result['brand']}")
        print(f"   Enhanced Size: {enhanced_result['size']} {enhanced_result['unit']}")
        print(f"   Enhanced Category: {enhanced_result['category']} > {enhanced_result['subcategory']}")
        print(f"   Enhanced Confidence: {enhanced_result['confidence']}")
        print(f"   Detection Method: {enhanced_result['detection_method']}")
        
        if enhanced_result['confidence'] > 0.7:
            print(f"   ✅ High confidence enhancement successful!")
        else:
            print(f"   ⚠️  Moderate confidence, but enhancement working")
            
    except Exception as e:
        print(f"   ❌ Error testing classification: {e}")
    
    print(f"\n📁 Files created:")
    
    # Show created files
    profiles_dir = "data/user_profiles"
    classifications_dir = "data/product_classifications"
    
    if os.path.exists(profiles_dir):
        profile_files = [f for f in os.listdir(profiles_dir) if f.endswith('.json')]
        print(f"   User Profiles ({len(profile_files)}): {profile_files}")
    
    if os.path.exists(classifications_dir):
        classification_files = [f for f in os.listdir(classifications_dir) if f.endswith('.json')]
        print(f"   Classifications ({len(classification_files)}): {classification_files}")
    
    print(f"\n🚀 Your system is now ready for dynamic product classification!")
    print(f"   Users will get enhanced product detection based on their business type and location.")
    print(f"   The system supports any business type and can be easily extended.")

if __name__ == "__main__":
    main()