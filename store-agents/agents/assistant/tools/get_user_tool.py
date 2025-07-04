import logging
import asyncio
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
            # Get user profile information with timeout
            try:
                user_profile = await asyncio.wait_for(
                    user_service.get_user_info(user_id), 
                    timeout=8.0
                )
            except asyncio.TimeoutError:
                logger.warning(f"User info lookup timed out for user_id: {user_id}")
                user_profile = None
            except Exception as e:
                logger.error(f"Error getting user info: {e}")
                user_profile = None
            
            if not user_profile:
                return {
                    "success": False,
                    "message": "User profile not found or database unavailable. This might be a new user who needs to register.",
                    "user_exists": False,
                    "suggestion": "Please ask the user to provide their name and store information for registration.",
                    "fallback_greeting": f"Welcome! I notice this might be your first time here, or I'm having trouble accessing your profile. Could you please tell me your name and a bit about your business?"
                }
            
            # Get store information if available
            try:
                store_info = await asyncio.wait_for(
                    user_service.get_store_info(user_id), 
                    timeout=8.0
                )
            except asyncio.TimeoutError:
                logger.warning(f"Store info lookup timed out for user_id: {user_id}")
                store_info = None
            except Exception as e:
                logger.error(f"Error getting store info: {e}")
                store_info = None
            
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
