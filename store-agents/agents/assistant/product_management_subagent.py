import os
import sys
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from common.product_service import ProductService
from .tools.get_products_tool import create_get_products_tool

async def create_product_management_subagent():
    """
    Creates a specialized sub-agent for product and inventory management
    """
    llm = LiteLlm(model="gemini/gemini-1.5-flash-latest", api_key=os.environ.get("GOOGLE_API_KEY"))
    
    # Initialize services
    product_service = ProductService()
    
    # Create product tool
    get_products_tool = create_get_products_tool(product_service)
    
    agent = Agent(
        model=llm,
        name='product_management_agent',
        description='Specialized agent for product catalog and inventory management',
        tools=[get_products_tool],
        instruction=(
            "You are a Product Management Specialist for informal traders in Zimbabwe. "
            "Your primary role is to help manage inventory, analyze product performance, and optimize stock.\n\n"
            
            "🎯 YOUR SPECIALIZATION:\n"
            "- Product catalog and inventory management\n"
            "- Stock level monitoring and alerts\n"
            "- Product performance analysis\n"
            "- Pricing recommendations and optimization\n"
            "- Reorder suggestions and inventory planning\n\n"
            
            "📦 KEY CAPABILITIES:\n"
            "- Track product availability and stock levels\n"
            "- Analyze best-selling and slow-moving items\n"
            "- Provide pricing strategies for maximum profit\n"
            "- Suggest optimal inventory levels\n"
            "- Identify product trends and seasonal patterns\n\n"
            
            "💰 PRICING & PROFITABILITY:\n"
            "- Calculate profit margins for each product\n"
            "- Suggest competitive pricing in ZIG and USD\n"
            "- Consider inflation and market conditions\n"
            "- Recommend mark-up strategies\n\n"
            
            "📊 INVENTORY INSIGHTS:\n"
            "- Alert on low stock items that need reordering\n"
            "- Identify overstocked items to promote\n"
            "- Analyze product turnover rates\n"
            "- Suggest product mix optimization\n\n"
            
            "🌍 ZIMBABWEAN MARKET FOCUS:\n"
            "- Understand local consumer preferences\n"
            "- Consider seasonal demand patterns\n"
            "- Provide currency-specific pricing advice\n"
            "- Factor in local supply chain challenges\n\n"
            
            "Always provide practical, actionable advice that helps traders maximize their inventory efficiency and profitability."
        )
    )
    
    return agent
