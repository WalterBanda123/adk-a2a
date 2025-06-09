import os
import sys
import re
import logging
from typing import Dict, Any, Optional

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from common.misc_transactions_service import MiscTransactionsService

logger = logging.getLogger(__name__)

def create_misc_transactions_tool():
    """Create the miscellaneous transactions tool for the main agent"""
    
    misc_service = MiscTransactionsService()
    
    async def misc_transactions_tool(request: str, user_id: str, amount: Optional[float] = None, purpose: str = "", 
                                   source: str = "", notes: str = "", limit: int = 10, 
                                   transaction_type: str = "", days: int = 30) -> str:
        """
        Handle miscellaneous business transactions including petty cash withdrawals, 
        owner drawings, cash deposits, and transaction reporting.
        
        Args:
            request (str): The user's request describing what they want to do
            user_id (str): The user ID for the business owner
            amount (float, optional): Amount for transactions (must be positive)
            purpose (str, optional): Purpose or reason for withdrawal/drawing
            source (str, optional): Source of cash deposit
            notes (str, optional): Additional notes for the transaction
            limit (int, optional): Number of transactions to retrieve for history (default: 10)
            transaction_type (str, optional): Filter transactions by type
            days (int, optional): Number of days for transaction summary (default: 30)
        
        Returns:
            str: Formatted response with transaction details or error message
        
        Examples:
            - misc_transactions_tool("petty cash withdrawal", user_id, amount=25.0, purpose="office supplies")
            - misc_transactions_tool("owner drawing", user_id, amount=200.0, purpose="personal use")
            - misc_transactions_tool("cash deposit", user_id, amount=500.0, source="bank withdrawal")
            - misc_transactions_tool("check balance", user_id)
            - misc_transactions_tool("transaction history", user_id, limit=5)
            - misc_transactions_tool("monthly summary", user_id, days=30)
        """
        
        try:
            # Parse the request to extract any missing parameters
            request_lower = request.lower()
            
            # Extract amount from request if not provided
            if amount is None:
                amount_match = re.search(r'[\$]?(\d+(?:\.\d{2})?)', request)
                if amount_match:
                    amount = float(amount_match.group(1))
                
                # For product withdrawals, we might not have amount initially
                # The agent should ask for the product value
            
            # Extract purpose from request if not provided and this is a withdrawal
            if not purpose and amount and ("withdrawal" in request_lower or "drawing" in request_lower or "withdraw" in request_lower):
                # Try to extract purpose after "for" or after the amount
                purpose_match = re.search(r'(?:for|purpose|reason)[\s:]*([^,\n]+)', request, re.IGNORECASE)
                if purpose_match:
                    purpose = purpose_match.group(1).strip()
                elif "office supplies" in request_lower or "office" in request_lower:
                    purpose = "Office supplies"
                elif "personal" in request_lower or "home" in request_lower or "family" in request_lower:
                    purpose = "Personal use"
                elif "cleaning" in request_lower:
                    purpose = "Cleaning supplies"
                else:
                    # Extract text after amount as purpose
                    amount_pattern = r'[\$]?\d+(?:\.\d{2})?'
                    remaining_text = re.sub(amount_pattern, '', request, count=1).strip()
                    remaining_text = re.sub(r'^(for|to|withdraw|withdrawal)', '', remaining_text, flags=re.IGNORECASE).strip()
                    if remaining_text:
                        purpose = remaining_text
            
            # Special handling for product withdrawals (owner drawings)
            if not purpose and ("took" in request_lower or "taking" in request_lower or "used" in request_lower):
                # Check for personal use indicators
                personal_indicators = ["home", "personal", "family", "myself", "consumption", "dinner", "house"]
                if any(indicator in request_lower for indicator in personal_indicators):
                    # Extract product information
                    product_match = re.search(r'(took|taking|used)\s+([^,\n]+?)(?:\s+(?:for|from|to))', request, re.IGNORECASE)
                    if product_match:
                        product_info = product_match.group(2).strip()
                        purpose = f"Personal use - {product_info}"
                    else:
                        # Fallback: extract everything after "took" or "taking"
                        took_match = re.search(r'(?:took|taking|used)\s+([^,\n]+)', request, re.IGNORECASE)
                        if took_match:
                            product_info = took_match.group(1).strip()
                            purpose = f"Personal use - {product_info}"
                        else:
                            purpose = "Personal use - product withdrawal"
            
            # Extract source from request if not provided and this is a deposit
            if not source and amount and "deposit" in request_lower:
                source_match = re.search(r'(?:from|source)[\s:]*([^,\n]+)', request, re.IGNORECASE)
                if source_match:
                    source = source_match.group(1).strip()
                elif "bank" in request_lower:
                    source = "Bank withdrawal"
                elif "owner" in request_lower or "capital" in request_lower:
                    source = "Owner capital"
            
            # Prepare kwargs for the misc agent (exclude user_id since it's passed separately)
            kwargs = {
                'amount': amount,
                'purpose': purpose,
                'source': source,
                'notes': notes,
                'limit': limit,
                'transaction_type': transaction_type,
                'days': days
            }
            
            # Remove None values
            kwargs = {k: v for k, v in kwargs.items() if v is not None}
            
            # Process the request through the misc transactions service
            try:
                # Determine the type of transaction based on the request
                request_lower = request.lower()
                
                if "deposit" in request_lower and amount:
                    # Cash deposit
                    result = await misc_service.record_cash_deposit(user_id, amount, source or "Manual deposit", notes)
                elif "withdrawal" in request_lower or "withdraw" in request_lower:
                    if "petty" in request_lower or "office" in request_lower or "business" in request_lower:
                        # Petty cash withdrawal
                        result = await misc_service.record_petty_cash_withdrawal(user_id, amount or 0, purpose or "Business expense", notes)
                    else:
                        # Owner drawing (cash)
                        result = await misc_service.record_owner_drawing(user_id, amount or 0, purpose or "Personal withdrawal", notes)
                elif "took" in request_lower or "taking" in request_lower or "drawing" in request_lower:
                    # Product withdrawal / Owner drawing
                    result = await misc_service.record_owner_drawing(user_id, amount or 0, purpose or "Product withdrawal", notes)
                elif "balance" in request_lower or "check" in request_lower:
                    # Balance inquiry
                    balance = await misc_service.get_current_cash_balance(user_id)
                    return f"💰 Current cash balance: ${balance:.2f}"
                elif "history" in request_lower or "transactions" in request_lower:
                    # Transaction history
                    transactions = await misc_service.get_misc_transactions(user_id, limit, transaction_type)
                    if transactions:
                        history_text = f"📋 Recent {len(transactions)} transactions:\n"
                        for txn in transactions[:5]:  # Show first 5
                            date = txn.get('date', 'N/A')
                            amount = txn.get('amount', 0)
                            desc = txn.get('purpose', txn.get('type', 'Unknown'))
                            history_text += f"• {date}: ${amount:.2f} - {desc}\n"
                        return history_text
                    else:
                        return "📋 No transaction history found."
                else:
                    # Default to general processing - try to determine from parameters
                    if amount and amount > 0:
                        if source:
                            # Has source, likely a deposit
                            result = await misc_service.record_cash_deposit(user_id, amount, source, notes)
                        elif purpose:
                            # Has purpose, likely a withdrawal/drawing
                            result = await misc_service.record_owner_drawing(user_id, amount, purpose, notes)
                        else:
                            return "❓ Please specify the purpose of this transaction or provide more details."
                    else:
                        return "❓ I need more information about this transaction. Please specify the amount and purpose."
                
                if result and result.get('success', False):
                    return result.get('message', 'Transaction processed successfully')
                else:
                    error_msg = result.get('error', 'Unknown error occurred') if result else 'Processing failed'
                    return f"❌ Transaction failed: {error_msg}"
                    
            except Exception as service_error:
                logger.error(f"Service error in misc_transactions_tool: {str(service_error)}")
                return f"❌ Service error: {str(service_error)}"
        
        except Exception as e:
            logger.error(f"Error in misc_transactions_tool: {str(e)}")
            return f"❌ An error occurred while processing your transaction request: {str(e)}"
    
    return misc_transactions_tool
