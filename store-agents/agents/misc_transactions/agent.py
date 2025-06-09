import os
import sys
import logging
import asyncio
from typing import Dict, Any, List, Callable

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from .tools.petty_cash_tool import petty_cash_withdrawal_tool, get_cash_balance_tool
from .tools.owner_drawing_tool import owner_drawing_tool
from .tools.cash_deposit_tool import cash_deposit_tool
from .tools.transaction_history_tool import get_transaction_history_tool, get_transaction_summary_tool

logger = logging.getLogger(__name__)

class MiscTransactionsAgent:
    """
    Agent for handling miscellaneous business transactions including:
    - Petty cash withdrawals
    - Owner drawings (personal withdrawals)
    - Cash deposits
    - Transaction history and summaries
    """
    
    def __init__(self):
        self.name = "Miscellaneous Transactions Agent"
        self.description = "Handles petty cash, owner drawings, deposits, and miscellaneous business transactions"
        
        # Available tools
        self.tools = {
            "petty_cash_withdrawal": {
                "function": petty_cash_withdrawal_tool,
                "description": "Record a petty cash withdrawal for business expenses",
                "parameters": ["user_id", "amount", "purpose", "notes"]
            },
            "owner_drawing": {
                "function": owner_drawing_tool,
                "description": "Record an owner drawing (personal withdrawal from business)",
                "parameters": ["user_id", "amount", "purpose", "notes"]
            },
            "cash_deposit": {
                "function": cash_deposit_tool,
                "description": "Record a cash deposit into the business",
                "parameters": ["user_id", "amount", "source", "notes"]
            },
            "get_cash_balance": {
                "function": get_cash_balance_tool,
                "description": "Check the current cash balance",
                "parameters": ["user_id"]
            },
            "transaction_history": {
                "function": get_transaction_history_tool,
                "description": "Get recent miscellaneous transaction history",
                "parameters": ["user_id", "limit", "transaction_type"]
            },
            "transaction_summary": {
                "function": get_transaction_summary_tool,
                "description": "Get a summary of miscellaneous transactions over a period",
                "parameters": ["user_id", "days"]
            }
        }
        
        # Agent instructions
        self.instructions = """
        You are the Miscellaneous Transactions Agent for a retail store management system.
        
        Your primary responsibilities:
        1. Handle petty cash withdrawals for small business expenses
        2. Record owner drawings (personal withdrawals from business)
        3. Process cash deposits into the business
        4. Provide transaction history and summaries
        5. Monitor and report cash balance changes
        
        Key Guidelines:
        - Always verify amounts are positive before processing
        - Check cash balance before allowing withdrawals
        - Provide clear, friendly confirmations for all transactions
        - Use emojis and formatting to make responses more engaging
        - Keep detailed records for accounting purposes
        - Distinguish between business expenses (petty cash) and personal withdrawals (drawings)
        
        Transaction Types:
        • Petty Cash Withdrawal: For small business expenses (office supplies, minor repairs, etc.)
        • Owner Drawing: For personal withdrawals from business profits
        • Cash Deposit: For adding money to the business cash register
        
        Always provide transaction IDs and updated balance information.
        """
    
    async def process_request(self, user_id: str, request: str, **kwargs) -> Dict[str, Any]:
        """
        Process a user request related to miscellaneous transactions
        
        Args:
            user_id (str): The user ID
            request (str): The user's request
            **kwargs: Additional parameters
            
        Returns:
            Dict containing the response and status
        """
        try:
            request_lower = request.lower()
            
            # Determine the intent and extract parameters
            if ("petty cash" in request_lower or "small expense" in request_lower or 
                ("withdraw" in request_lower and "personal" not in request_lower and "drawing" not in request_lower)):
                return await self._handle_petty_cash_request(user_id, request, **kwargs)
            elif "drawing" in request_lower or "personal withdrawal" in request_lower or "take money" in request_lower:
                return await self._handle_owner_drawing_request(user_id, request, **kwargs)
            elif "deposit" in request_lower or "add money" in request_lower or "put money" in request_lower:
                return await self._handle_cash_deposit_request(user_id, request, **kwargs)
            elif "balance" in request_lower:
                return await self._handle_balance_request(user_id)
            elif "history" in request_lower or "transactions" in request_lower:
                return await self._handle_history_request(user_id, **kwargs)
            elif "summary" in request_lower or "report" in request_lower:
                return await self._handle_summary_request(user_id, **kwargs)
            else:
                return {
                    "success": True,
                    "message": self._get_help_message(),
                    "agent": self.name
                }
        
        except Exception as e:
            logger.error(f"Error processing misc transaction request: {str(e)}")
            return {
                "success": False,
                "error": f"❌ An error occurred while processing your request: {str(e)}",
                "agent": self.name
            }
    
    async def _handle_petty_cash_request(self, user_id: str, request: str, **kwargs) -> Dict[str, Any]:
        """Handle petty cash withdrawal requests"""
        amount = kwargs.get('amount')
        purpose = kwargs.get('purpose', '')
        notes = kwargs.get('notes', '')
        
        if not amount or not purpose:
            return {
                "success": False,
                "error": "❌ Please provide both amount and purpose for petty cash withdrawal.\n"
                        "Example: 'Petty cash withdrawal of $25 for office supplies'",
                "agent": self.name
            }
        
        result = await petty_cash_withdrawal_tool(user_id, amount, purpose, notes)
        result["agent"] = self.name
        return result
    
    async def _handle_owner_drawing_request(self, user_id: str, request: str, **kwargs) -> Dict[str, Any]:
        """Handle owner drawing requests"""
        amount = kwargs.get('amount')
        purpose = kwargs.get('purpose', 'Personal withdrawal')
        notes = kwargs.get('notes', '')
        
        if not amount:
            return {
                "success": False,
                "error": "❌ Please provide the amount for owner drawing.\n"
                        "Example: 'Owner drawing of $200'",
                "agent": self.name
            }
        
        result = await owner_drawing_tool(user_id, amount, purpose, notes)
        result["agent"] = self.name
        return result
    
    async def _handle_cash_deposit_request(self, user_id: str, request: str, **kwargs) -> Dict[str, Any]:
        """Handle cash deposit requests"""
        amount = kwargs.get('amount')
        source = kwargs.get('source', '')
        notes = kwargs.get('notes', '')
        
        if not amount or not source:
            return {
                "success": False,
                "error": "❌ Please provide both amount and source for cash deposit.\n"
                        "Example: 'Cash deposit of $500 from bank withdrawal'",
                "agent": self.name
            }
        
        result = await cash_deposit_tool(user_id, amount, source, notes)
        result["agent"] = self.name
        return result
    
    async def _handle_balance_request(self, user_id: str) -> Dict[str, Any]:
        """Handle cash balance requests"""
        result = await get_cash_balance_tool(user_id)
        result["agent"] = self.name
        return result
    
    async def _handle_history_request(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """Handle transaction history requests"""
        limit = kwargs.get('limit', 10)
        transaction_type = kwargs.get('transaction_type', '')
        
        result = await get_transaction_history_tool(user_id, limit, transaction_type)
        result["agent"] = self.name
        return result
    
    async def _handle_summary_request(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """Handle transaction summary requests"""
        days = kwargs.get('days', 30)
        
        result = await get_transaction_summary_tool(user_id, days)
        result["agent"] = self.name
        return result
    
    def _get_help_message(self) -> str:
        """Get help message explaining available functions"""
        return """
🏪 **Miscellaneous Transactions Agent**

I can help you with various cash transactions for your business:

💸 **Petty Cash Withdrawals**
- Record small business expenses
- Example: "Petty cash withdrawal of $25 for office supplies"

👤 **Owner Drawings**
- Record personal withdrawals from business
- Example: "Owner drawing of $200 for personal use"

💰 **Cash Deposits**
- Add money to your business cash register
- Example: "Cash deposit of $500 from bank withdrawal"

📊 **Balance & Reports**
- Check current cash balance
- View transaction history
- Get transaction summaries

**Available Commands:**
- "What's my cash balance?"
- "Show recent transactions"
- "Transaction summary for last 30 days"
- "Petty cash withdrawal of $X for [purpose]"
- "Owner drawing of $X"
- "Cash deposit of $X from [source]"

How can I assist you with your cash transactions today? 💼
        """
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return list(self.tools.keys())
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a specific tool by name"""
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
                "agent": self.name
            }
        
        try:
            tool_info = self.tools[tool_name]
            result = await tool_info["function"](**kwargs)
            result["agent"] = self.name
            return result
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            return {
                "success": False,
                "error": f"Error executing {tool_name}: {str(e)}",
                "agent": self.name
            }

# Example usage
async def main():
    agent = MiscTransactionsAgent()
    
    # Test with example user
    user_id = "test_user_1749461758"
    
    # Test cash balance
    result = await agent.process_request(user_id, "What's my cash balance?")
    print(result["message"])
    
    # Test petty cash withdrawal
    result = await agent.process_request(
        user_id, 
        "petty cash withdrawal", 
        amount=25.0, 
        purpose="Office supplies"
    )
    print(result["message"])

if __name__ == "__main__":
    asyncio.run(main())
