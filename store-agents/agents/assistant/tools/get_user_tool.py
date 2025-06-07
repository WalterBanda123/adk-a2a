import json
from typing import Dict, Any
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from common.user_service import UserService

async def get_user_info_func(user_id: str, include_store: bool = True, user_service: UserService = None) -> Dict[str, Any]:
    """Get user and store information for personalized assistance"""
    try:
        # Get user information
        user_info = await user_service.get_user_info(user_id)
        
        result = {
            "user_info": user_info,
            "store_info": None
        }
        
        # Get store information if requested and user exists
        if include_store and user_info:
            store_info = await user_service.get_store_info(user_id)
            result["store_info"] = store_info
        
        return {
            "success": True,
            "data": result,
            "message": f"Retrieved information for user: {user_info.get('name', 'Unknown') if user_info else 'User not found'}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to retrieve user information: {str(e)}"
        }

def create_get_user_tool(user_service: UserService):
    """Create a function tool for getting user information"""
    
    # Create a closure that includes the user_service
    async def get_user_info(user_id: str, include_store: bool = True) -> Dict[str, Any]:
        """Get user and store information for personalized assistance"""
        return await get_user_info_func(user_id, include_store, user_service)
    
    return FunctionTool(func=get_user_info)
