import os
import sys
import logging
from typing import Dict, Any, Optional, List
import re

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from agents.misc_transactions.agent import MiscTransactionsAgent
from common.user_service import UserService

logger = logging.getLogger(__name__)

class AgentCoordinator:
    """
    Coordinator agent that routes requests to specialized sub-agents
    """
    
    def __init__(self):
        self.name = "Store Assistant Coordinator"
        self.description = "Coordinates requests between specialized agents for store management"
        
        # Initialize sub-agents
        self.misc_transactions_agent = MiscTransactionsAgent()
        self.user_service = UserService()
        
        # Keywords for routing to misc transactions agent
        self.misc_transaction_keywords = [
            'petty cash', 'withdraw', 'withdrawal', 'drawing', 'deposit', 
            'cash balance', 'balance', 'transaction history', 'transactions',
            'owner drawing', 'personal withdrawal', 'cash deposit', 'add money',
            'put money', 'take money', 'small expense'
        ]
    
    def _extract_amount_from_text(self, text: str) -> Optional[float]:
        """Extract amount from text using regex"""
        # Look for patterns like $25, 25, $25.50, etc.
        amount_patterns = [
            r'\$(\d+(?:\.\d{2})?)',  # $25 or $25.50
            r'(\d+(?:\.\d{2})?)\s*(?:dollars?|usd|\$)',  # 25 dollars, 25 USD, 25$
            r'(\d+(?:\.\d{2})?)'  # Just numbers
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except (ValueError, IndexError):
                    continue
        return None
    
    def _extract_purpose_from_text(self, text: str) -> str:
        """Extract purpose/reason from transaction text"""
        # Common purpose indicators
        purpose_patterns = [
            r'from\s+(.+?)(?:\.|$)',  # "from bank withdrawal"
            r'for\s+(.+?)(?:\.|$)',   # "for office supplies"
            r'purpose\s*:\s*(.+?)(?:\.|$)',
            r'reason\s*:\s*(.+?)(?:\.|$)',
            r'to\s+(?:buy|purchase|get)\s+(.+?)(?:\.|$)'
        ]
        
        for pattern in purpose_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                purpose = match.group(1).strip()
                if purpose:
                    return purpose
        
        # If no specific pattern found, try to extract from the end of the sentence
        if 'for' in text.lower():
            parts = text.lower().split('for')
            if len(parts) > 1:
                return parts[-1].strip(' .,')
        
        return ""
    
    def _should_route_to_misc_transactions(self, message: str) -> bool:
        """Determine if message should be routed to misc transactions agent"""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.misc_transaction_keywords)
    
    async def route_request(self, user_id: str, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Route the user request to the appropriate agent
        
        Args:
            user_id (str): The user ID
            message (str): The user's message
            context (Dict): Additional context
            
        Returns:
            Dict containing the response
        """
        try:
            if context is None:
                context = {}  # Ensure context is initialized as an empty dictionary
            
            # Check if this should go to misc transactions agent
            if self._should_route_to_misc_transactions(message):
                return await self._handle_misc_transaction_request(user_id, message, context)
            
            # For other requests, provide a helpful response
            return await self._handle_general_request(user_id, message, context)
            
        except Exception as e:
            logger.error(f"Error in coordinator routing: {str(e)}")
            return {
                "success": False,
                "message": f"❌ Sorry, I encountered an error processing your request: {str(e)}",
                "agent": self.name
            }
    
    async def _handle_misc_transaction_request(self, user_id: str, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle requests that should go to the misc transactions agent"""
        try:
            # Extract parameters from the message
            amount = self._extract_amount_from_text(message)
            purpose = self._extract_purpose_from_text(message)
            
            # Prepare kwargs for the misc transactions agent
            kwargs = {}
            if amount:
                kwargs['amount'] = amount
            if purpose:
                # For deposits, we need both source and purpose - they're often the same
                if "deposit" in message.lower():
                    kwargs['source'] = purpose
                else:
                    kwargs['purpose'] = purpose
                
            # Debug logging
            logger.info(f"Extracted amount: {amount}, purpose: '{purpose}', kwargs: {kwargs}")
            
            # Route to misc transactions agent
            result = await self.misc_transactions_agent.process_request(user_id, message, **kwargs)
            
            # Add coordinator info
            if 'agent' not in result:
                result['agent'] = f"{self.name} -> {self.misc_transactions_agent.name}"
            else:
                result['agent'] = f"{self.name} -> {result['agent']}"
            
            return result
            
        except Exception as e:
            logger.error(f"Error handling misc transaction request: {str(e)}")
            return {
                "success": False,
                "message": f"❌ Error processing transaction request: {str(e)}",
                "agent": f"{self.name} -> MiscTransactionsAgent"
            }
    
    async def _handle_general_request(self, user_id: str, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general requests not specific to any sub-agent"""
        try:
            # Get user info for personalized response (fix the method call)
            user_info = await self.user_service.get_user_info(user_id)
            user_name = user_info.get('name', 'there') if user_info else 'there'
            
            return {
                "success": True,
                "message": f"Hello {user_name}! 👋\n\n"
                          f"I can help you with various aspects of your business:\n\n"
                          f"💰 **Cash Transactions:**\n"
                          f"- Petty cash withdrawals\n"
                          f"- Owner drawings\n"
                          f"- Cash deposits\n"
                          f"- Check cash balance\n"
                          f"- Transaction history\n\n"
                          f"📊 **Coming Soon:**\n"
                          f"- Financial reports\n"
                          f"- Product management\n"
                          f"- Business advice\n\n"
                          f"Try saying: \"I need to withdraw $25 for office supplies\" or \"What's my cash balance?\"",
                "agent": self.name
            }
            
        except Exception as e:
            logger.error(f"Error handling general request: {str(e)}")
            return {
                "success": False,
                "message": f"❌ Error processing your request: {str(e)}",
                "agent": self.name
            }
    
    def get_available_agents(self) -> List[str]:
        """Get list of available sub-agents"""
        return [
            self.misc_transactions_agent.name
        ]
    
    def get_agent_capabilities(self) -> Dict[str, Any]:
        """Get capabilities of all agents"""
        return {
            "coordinator": {
                "name": self.name,
                "description": self.description,
                "capabilities": ["Request routing", "Agent coordination"]
            },
            "misc_transactions": {
                "name": self.misc_transactions_agent.name,
                "description": self.misc_transactions_agent.description,
                "capabilities": ["Petty cash", "Owner drawings", "Cash deposits", "Transaction history", "Balance checking"]
            }
        }

# Example usage
async def main():
    """Test the coordinator"""
    coordinator = AgentCoordinator()
    
    # Test user
    user_id = "test_user_1749461758"
    
    # Test different types of requests
    test_requests = [
        "What's my cash balance?",
        "I need to withdraw $25 for office supplies",
        "Owner drawing of $200",
        "Deposit $500 from bank withdrawal",
        "Show me recent transactions",
        "Hello, how can you help me?"
    ]
    
    for request in test_requests:
        print(f"\n🔄 Request: {request}")
        result = await coordinator.route_request(user_id, request)
        print(f"✅ Response: {result.get('message', 'No message')}")
        print(f"🤖 Agent: {result.get('agent', 'Unknown')}")
        print("-" * 80)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
