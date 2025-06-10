# User Profile Service for Dynamic Product Recognition
import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class UserBusinessProfile:
    user_id: str
    country: str
    industry: str  # 'grocery', 'pharmacy', 'electronics', 'clothing', etc.
    product_categories: List[str]  # ['beverages', 'snacks', 'dairy', etc.]
    business_size: str  # 'small', 'medium', 'large'
    custom_brands: Optional[List[str]] = None  # User can add their own frequently sold brands

class UserProfileService:
    def __init__(self, data_dir: str = "data/user_profiles"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def save_user_profile(self, profile: UserBusinessProfile) -> bool:
        """Save user business profile"""
        try:
            profile_path = os.path.join(self.data_dir, f"{profile.user_id}_profile.json")
            with open(profile_path, 'w') as f:
                json.dump(profile.__dict__, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving profile: {e}")
            return False
    
    def get_user_profile(self, user_id: str) -> Optional[UserBusinessProfile]:
        """Get user business profile"""
        try:
            profile_path = os.path.join(self.data_dir, f"{user_id}_profile.json")
            if os.path.exists(profile_path):
                with open(profile_path, 'r') as f:
                    data = json.load(f)
                return UserBusinessProfile(**data)
        except Exception as e:
            print(f"Error loading profile: {e}")
        return None
