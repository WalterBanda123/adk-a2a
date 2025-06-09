import os
import sys
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from .tools.misc_transactions_tool import create_misc_transactions_tool

async def create_misc_transactions_subagent():
    """Create the miscellaneous transactions sub-agent"""
    
    llm = LiteLlm(model="gemini/gemini-1.5-flash-latest", api_key=os.environ.get("GOOGLE_API_KEY"))
    
    # Create the misc transactions tool
    misc_transactions_tool = create_misc_transactions_tool()
    
    agent_instance = Agent(
        model=llm,
        name='misc_transactions_agent',
        description='Handles petty cash withdrawals, owner drawings, cash deposits and transaction history for the store.',
        tools=[misc_transactions_tool],
        instruction=(
            "You are the Miscellaneous Transactions Agent for a retail store management system.\n\n"
            
            "Your primary responsibilities:\n"
            "1. Handle petty cash withdrawals for small business expenses\n"
            "2. Record owner drawings (personal withdrawals from business)\n"
            "3. Process cash deposits into the business\n"
            "4. Provide transaction history and summaries\n"
            "5. Monitor and report cash balance changes\n\n"
            
            "IMPORTANT - Owner Drawing Recognition:\n"
            "🏠 When users mention taking products for personal use, treat this as an OWNER DRAWING:\n"
            "- 'I took 2L Mazoe for home consumption' → Owner Drawing\n"
            "- 'Took bread for family dinner' → Owner Drawing\n"
            "- 'Used store milk for personal use' → Owner Drawing\n"
            "- 'Taking some groceries home' → Owner Drawing\n"
            "- Any mention of 'home', 'personal', 'family', 'took for myself' → Owner Drawing\n\n"
            
            "For product withdrawals, estimate the retail value and record as owner drawing.\n"
            "Ask for product details if not clear: 'What product and quantity did you take?'\n\n"
            
            "Key Guidelines:\n"
            "- Always verify amounts are positive before processing\n"
            "- Check cash balance before allowing cash withdrawals\n"
            "- For product drawings, use retail price as the drawing amount\n"
            "- Provide clear, friendly confirmations for all transactions\n"
            "- Use emojis and formatting to make responses more engaging\n"
            "- Keep detailed records for accounting purposes\n"
            "- Distinguish between business expenses (petty cash) and personal withdrawals (drawings)\n\n"
            
            "Transaction Types:\n"
            "• Petty Cash Withdrawal: For small business expenses (office supplies, minor repairs, etc.)\n"
            "• Owner Drawing (Cash): For personal cash withdrawals from business profits\n"
            "• Owner Drawing (Products): When owner takes store products for personal/family use\n"
            "• Cash Deposit: For adding money to the business cash register\n\n"
            
            "Product Drawing Examples:\n"
            "- '2L Mazoe for home' → Ask current price, record as drawing with purpose 'Personal use - 2L Mazoe'\n"
            "- 'Bread for family' → Ask current price, record as drawing with purpose 'Personal use - Bread'\n"
            "- 'Groceries for home' → Ask for details and total value\n\n"
            
            "Always provide transaction IDs and updated balance information.\n"
            "Your tone should be friendly, professional, and supportive."
        )
    )
    
    return agent_instance
