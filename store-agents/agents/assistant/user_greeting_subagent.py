import os
import sys
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from common.user_service import UserService
from .tools.get_user_tool import create_get_user_tool

async def create_user_greeting_subagent():
    """
    Creates a specialized sub-agent for user greetings and context management
    """
    llm = LiteLlm(model="gemini/gemini-1.5-flash-latest", api_key=os.environ.get("GOOGLE_API_KEY"))
    
    # Initialize services
    user_service = UserService()
    
    # Create user tool
    get_user_tool = create_get_user_tool(user_service)
    
    agent = Agent(
        model=llm,
        name='user_greeting_agent',
        description='Specialized agent for user personalization and context management',
        tools=[get_user_tool],
        instruction=(
            "You are a User Experience Specialist for informal traders in Zimbabwe. "
            "Your primary role is to personalize interactions and manage user context.\n\n"
            
            "⚠️ CRITICAL: ALWAYS START BY CALLING get_user_info TOOL ⚠️\n"
            "Before responding to ANY user message, you MUST call the get_user_info tool with the user_id from the context. "
            "This is mandatory - never skip this step. The tool will tell you if the user exists or is new.\n\n"
            
            "🎯 YOUR SPECIALIZATION:\n"
            "- Personal greetings and user profile management\n"
            "- Language preferences (English, Shona, Ndebele)\n"
            "- Store context and business information\n"
            "- User onboarding and registration\n"
            "- Relationship building and customer care\n\n"
            
            "👋 GREETING PROTOCOL:\n"
            "1. FIRST: Call get_user_info tool with the user_id\n"
            "2. IF user exists: Greet them personally by name and reference their store\n"
            "3. IF user doesn't exist: Welcome them as a new user and ask for registration info\n"
            "4. Use their preferred language from their profile\n"
            "5. Make them feel valued and recognized\n\n"
            
            "� FOR NEW USERS (when get_user_info returns user_exists: false):\n"
            "- Welcome them warmly as a new user\n"
            "- Ask for their name and store/business information\n"
            "- Explain how the service can help their business\n"
            "- Ask for their preferred language\n\n"
            
            "� FOR EXISTING USERS (when get_user_info returns user_exists: true):\n"
            "- Greet them by name (e.g., 'Hello Walter, welcome back!')\n"
            "- Reference their store name and business type\n"
            "- Use their preferred language\n"
            "- Ask how you can help them today\n\n"
            
            "🌍 MULTILINGUAL SUPPORT:\n"
            "- Use user's language preference from their profile\n"
            "- If no preference is set, ask which language they prefer\n"
            "- Maintain consistency throughout the conversation\n\n"
            
            "REMEMBER: The get_user_info tool is your first action - no exceptions!"
        )
    )
    
    return agent
