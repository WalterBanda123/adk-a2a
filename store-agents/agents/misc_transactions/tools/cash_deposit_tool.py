import os
import logging
import sys
from typing import Dict, Any

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from common.misc_transactions_service import MiscTransactionsService

logger = logging.getLogger(__name__)

async def cash_deposit_tool(user_id: str, amount: float, source: str, notes: str = "") -> Dict[str, Any]:
    """
    Tool for recording cash deposits into the business (adding money to the cash register).
    This could be from owner capital injection, loan proceeds, or other cash inflows.
    
    Args:
        user_id (str): The user ID of the business owner
        amount (float): The amount to deposit (must be positive)
        source (str): The source of the cash (e.g., "Owner capital", "Loan proceeds", "Bank withdrawal")
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
        result = await service.record_cash_deposit(user_id, amount, source, notes)
        
        if result["success"]:
            return {
                "success": True,
                "message": f"✅ Cash deposit recorded successfully!\n\n"
                          f"💰 Amount: ${amount:.2f}\n"
                          f"📝 Source: {source}\n"
                          f"🏦 New cash balance: ${result['new_balance']:.2f}\n"
                          f"📄 Transaction ID: {result['transaction_id']}\n\n"
                          f"💡 Note: This deposit has been added to your business cash balance.",
                "transaction_id": result["transaction_id"],
                "new_balance": result["new_balance"]
            }
        else:
            return {
                "success": False,
                "error": f"❌ Failed to record cash deposit: {result['error']}"
            }
            
    except Exception as e:
        logger.error(f"Error in cash_deposit_tool: {str(e)}")
        return {
            "success": False,
            "error": f"❌ An error occurred: {str(e)}"
        }
