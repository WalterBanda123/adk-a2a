import os
import logging
import sys
from typing import Dict, Any

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from common.misc_transactions_service import MiscTransactionsService

logger = logging.getLogger(__name__)

async def petty_cash_withdrawal_tool(user_id: str, amount: float, purpose: str, notes: str = "") -> Dict[str, Any]:
    """
    Tool for recording petty cash withdrawals from the business cash register.
    Used for small business expenses like office supplies, minor repairs, etc.
    
    Args:
        user_id (str): The user ID of the business owner
        amount (float): The amount to withdraw (must be positive)
        purpose (str): The purpose/reason for the withdrawal
        notes (str): Optional additional notes
        
    Returns:
        Dict containing success status, transaction details, and updated balance
    """
    try:
        if amount <= 0:
            return {
                "success": False,
                "error": "Amount must be greater than 0"
            }
        
        service = MiscTransactionsService()
        result = await service.record_petty_cash_withdrawal(user_id, amount, purpose, notes)
        
        if result["success"]:
            return {
                "success": True,
                "message": f"✅ Petty cash withdrawal recorded successfully!\n\n"
                          f"💰 Amount: ${amount:.2f}\n"
                          f"📝 Purpose: {purpose}\n"
                          f"🏦 Remaining cash balance: ${result['remaining_balance']:.2f}\n"
                          f"📄 Transaction ID: {result['transaction_id']}",
                "transaction_id": result["transaction_id"],
                "remaining_balance": result["remaining_balance"]
            }
        else:
            return {
                "success": False,
                "error": f"❌ Failed to record petty cash withdrawal: {result['error']}"
            }
            
    except Exception as e:
        logger.error(f"Error in petty_cash_withdrawal_tool: {str(e)}")
        return {
            "success": False,
            "error": f"❌ An error occurred: {str(e)}"
        }

async def get_cash_balance_tool(user_id: str) -> Dict[str, Any]:
    """
    Tool for checking the current cash balance in the business register.
    
    Args:
        user_id (str): The user ID of the business owner
        
    Returns:
        Dict containing the current cash balance
    """
    try:
        service = MiscTransactionsService()
        balance = await service.get_current_cash_balance(user_id)
        
        return {
            "success": True,
            "balance": balance,
            "message": f"💰 Current cash balance: ${balance:.2f}"
        }
        
    except Exception as e:
        logger.error(f"Error in get_cash_balance_tool: {str(e)}")
        return {
            "success": False,
            "error": f"❌ An error occurred while checking balance: {str(e)}"
        }
