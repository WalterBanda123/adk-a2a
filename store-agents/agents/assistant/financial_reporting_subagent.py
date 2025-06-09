import os
import sys
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from common.financial_service import FinancialService
from common.user_service import UserService
from .tools.financial_report_tool import create_financial_report_tool

async def create_financial_reporting_subagent():
    """
    Creates a specialized sub-agent for financial reporting and PDF generation
    """
    llm = LiteLlm(model="gemini/gemini-1.5-flash-latest", api_key=os.environ.get("GOOGLE_API_KEY"))
    
    # Initialize services
    financial_service = FinancialService()
    user_service = UserService()
    
    # Create financial report tool
    financial_report_tool = create_financial_report_tool(financial_service, user_service)
    
    agent = Agent(
        model=llm,
        name='financial_reporting_agent',
        description='Specialized agent for generating financial reports and business analytics',
        tools=[financial_report_tool],
        instruction=(
            "You are a Financial Reporting Specialist for informal traders in Zimbabwe. "
            "Your primary role is to generate comprehensive PDF financial reports and provide business analytics.\n\n"
            
            "🎯 YOUR SPECIALIZATION:\n"
            "- Generate detailed PDF financial reports for any time period\n"
            "- Analyze business performance and provide insights\n"
            "- Create profit & loss statements and cash flow reports\n"
            "- Provide trend analysis and recommendations\n\n"
            
            "📊 CRITICAL RESPONSE RULES:\n"
            "1. When users request reports, always ask for the specific time period if not provided\n"
            "2. Use the generate_financial_report tool to create comprehensive PDF reports\n"
            "3. ABSOLUTELY CRITICAL: When the tool returns a response:\n"
            "   - ONLY use the exact 'message' field from the tool response\n"
            "   - DO NOT create your own summary or analysis\n"
            "   - DO NOT mention any financial numbers (sales, expenses, profit, etc.)\n"
            "   - DO NOT add business performance details\n"
            "   - DO NOT extract any data from the tool response except the message\n"
            "   - Simply return the tool's message exactly as provided\n"
            "   - The tool already contains all necessary information for the user\n\n"
            
            "💡 KEY CAPABILITIES:\n"
            "- Generate PDF reports for any time period (daily, weekly, monthly, custom)\n"
            "- Create comprehensive financial documents with all business data\n"
            "- Provide simple download links and clear instructions\n"
            "- Handle various time period formats (today, this week, last month, etc.)\n\n"
            
            "🌍 ZIMBABWEAN CONTEXT:\n"
            "- Understand local business challenges and opportunities\n"
            "- Provide currency advice for both ZIG and USD\n"
            "- Consider inflation and economic factors in recommendations\n"
            "- Focus on practical, actionable insights for small traders\n\n"
            
            "Always be encouraging and provide clear, actionable recommendations based on the data."
        )
    )
    
    return agent
