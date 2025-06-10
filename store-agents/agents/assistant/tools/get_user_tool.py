import logging
from typing import Dict, Any
from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)

def create_get_user_tool(user_service):
    """Create a tool for retrieving user information and context"""
    
    async def get_user_info(user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive user information including profile, store details, and preferences
        
        Args:
            user_id: The unique identifier for the user
        
        Returns:
            Dict containing user information, store context, and preferences
        """
        try:
            # Get user profile information
            user_profile = await user_service.get_user_profile(user_id)
            
            if not user_profile:
                return {
                    "success": False,
                    "message": "User profile not found. This might be a new user who needs to register.",
                    "user_exists": False,
                    "suggestion": "Please ask the user to provide their name and store information for registration."
                }
            
            # Get store information if available
            store_info = await user_service.get_store_info(user_id)
            
            # Format user information for greeting
            user_name = user_profile.get('name', 'Friend')
            store_name = store_info.get('store_name', '') if store_info else ''
            business_type = store_info.get('business_type', 'business') if store_info else 'business'
            location = store_info.get('location', '') if store_info else ''
            language_preference = user_profile.get('language_preference', 'English')
            
            # Create personalized greeting context
            greeting_context = {
                "user_name": user_name,
                "store_name": store_name,
                "business_type": business_type,
                "location": location,
                "language_preference": language_preference,
                "has_store_info": bool(store_info),
                "user_exists": True
            }
            
            # Generate personalized message
            if store_name:
                personal_message = f"Welcome back, {user_name}! How can I help you with {store_name} today?"
            else:
                personal_message = f"Hello {user_name}! How can I assist you with your {business_type} today?"
            
            return {
                "success": True,
                "message": personal_message,
                "user_profile": user_profile,
                "store_info": store_info,
                "greeting_context": greeting_context,
                "user_exists": True,
                "language_preference": language_preference
            }
            
        except Exception as e:
            logger.error(f"Error in get_user_info: {str(e)}")
            return {
                "success": False,
                "message": f"Error retrieving user information: {str(e)}",
                "user_exists": False,
                "error": str(e)
            }
    
    return FunctionTool(func=get_user_info)
