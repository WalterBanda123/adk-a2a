import os
import sys
from contextlib import AsyncExitStack
from google.adk.agents import Agent
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from common.user_service import UserService
from common.product_service import ProductService
from common.image_analysis_service import ImageAnalysisService
from .tools.get_user_tool import create_get_user_tool
from .tools.get_products_tool import create_get_products_tool
from .tools.analyze_image_tool import create_analyze_product_image_tool

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

async def create_main_agent():
    
    print("--- Attempting to start and connect to elevenlabs-mcp via uvx ---")
    llm = LiteLlm(model="gemini/gemini-1.5-flash-latest", api_key=os.environ.get("GOOGLE_API_KEY"))
    
    # Initialize services
    user_service = UserService()
    product_service = ProductService()
    image_analysis_service = ImageAnalysisService()
    
    # Create tools
    get_user_tool = create_get_user_tool(user_service)
    get_products_tool = create_get_products_tool(product_service)
    analyze_image_tool = create_analyze_product_image_tool(image_analysis_service)
    
    agent_instance = Agent(
        model=llm,
        name='store_assistant',
        description='A knowledgeable and friendly grocery store assistant for customers and store managers in Zimbabwe.',
        tools=[get_user_tool, get_products_tool, analyze_image_tool],
        instruction=(
            "You are a Smart Business Assistant agent for informal traders in Zimbabwe. "
            "You help small business owners, shopkeepers, and vendors manage their daily operations.\n\n"
            
            "CRITICAL IMAGE ANALYSIS INSTRUCTION:\n"
            "When you receive instructions that say 'EXECUTE TOOL CALL: Please call the analyze_product_image tool', "
            "you MUST immediately call the analyze_product_image tool with the exact parameters provided. "
            "Do not ask questions, do not hesitate - just execute the tool call immediately.\n\n"
            
            "MAIN FUNCTIONS:\n"
            "1. PRODUCT IMAGE ANALYSIS:\n"
            "   - Use the analyze_product_image tool when instructed to analyze images\n"
            "   - Return clean JSON with: name, category, subcategory, size, brand, description, image_url\n"
            "   - Present results in a clear, structured format\n\n"
            
            "2. USER & PRODUCT MANAGEMENT:\n"
            "   - Use get_user_info and get_products tools as needed\n"
            "   - Provide business advice and support\n\n"
            
            "3. MULTILINGUAL SUPPORT:\n"
            "   - Support English, Shona, and Ndebele\n"
            "   - Use user's preferred language\n\n"
            
            "Always be friendly, professional, and supportive in your responses."
        )
    )
    
    exit_stack = AsyncExitStack()
    return agent_instance, exit_stack

root_agent = create_main_agent

