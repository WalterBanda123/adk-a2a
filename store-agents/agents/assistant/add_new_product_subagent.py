import os
import sys
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from .tools.add_product_vision_tool import create_add_product_vision_tool

async def create_add_new_product_subagent():
    """
    Creates a specialized sub-agent for adding new products via image analysis
    """
    llm = LiteLlm(model="gemini/gemini-1.5-flash-latest", api_key=os.environ.get("GOOGLE_API_KEY"))
    
    # Create the vision-based product addition tool
    add_product_vision_tool = create_add_product_vision_tool()
    
    agent = Agent(
        model=llm,
        name='add_new_product_agent',
        description='Specialized agent for adding new products via image analysis using Google Cloud Vision API',
        tools=[add_product_vision_tool],
        instruction=(
            "You are a Product Addition Specialist. Your primary role is to help users add new products to their inventory by analyzing product images using the 'add_product_vision_tool'.\n\n"
            
            "CRITICAL WORKFLOW FOR IMAGES:\n"
            "1. When a user message contains 'IMAGE DATA AVAILABLE', you MUST use the 'add_product_vision_tool'.\n"
            "2. The user message will contain the necessary parameters for the tool: 'image_data', 'is_url', and 'user_id'. Extract these exact values from the user's message.\n"
            "3. Invoke 'add_product_vision_tool' with these extracted parameters.\n"
            "4. After the tool executes, it will return structured product information. Your response to the user should be a concise summary of the findings (e.g., 'The image shows a [Product Title], size [Size][Unit]. Confidence: [Confidence]%. Would you like to add it?').\n"
            "5. If the tool fails or returns no useful information, inform the user clearly (e.g., 'I couldn\'t analyze the product from the image. Please provide details manually.').\n\n"
            
            "IMPORTANT: Do NOT output the literal tool call syntax (like 'add_product_vision_tool(...)') as your response. Your role is to USE the tool and then COMMUNICATE the results naturally to the user.\n\n"
            
            "Focus on products relevant to the Zimbabwean market if applicable. Aim for speed and accuracy.\n"
        )
    )
    
    return agent
