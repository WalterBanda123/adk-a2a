import os
import logging
import sys
from typing import Dict, Any

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from common.misc_transactions_service import MiscTransactionsService

logger = logging.getLogger(__name__)

async def owner_drawing_tool(user_id: str, amount: float, purpose: str = "Personal withdrawal", notes: str = "") -> Dict[str, Any]:
    """
    Tool for recording owner drawings (money taken from business for personal use).
    This affects the business cash balance and should be recorded for accounting purposes.
    
    Args:
        user_id (str): The user ID of the business owner
        amount (float): The amount to withdraw (must be positive)
        purpose (str): The purpose/reason for the drawing
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
        result = await service.record_owner_drawing(user_id, amount, purpose, notes)
        
        if result["success"]:
            return {
                "success": True,
                "message": f"✅ Owner drawing recorded successfully!\n\n"
                          f"💰 Amount: ${amount:.2f}\n"
                          f"📝 Purpose: {purpose}\n"
                          f"🏦 Remaining cash balance: ${result['remaining_balance']:.2f}\n"
                          f"📄 Transaction ID: {result['transaction_id']}\n\n"
                          f"💡 Note: This withdrawal has been recorded as an owner drawing for accounting purposes.",
                "transaction_id": result["transaction_id"],
                "remaining_balance": result["remaining_balance"]
            }
        else:
            return {
                "success": False,
                "error": f"❌ Failed to record owner drawing: {result['error']}"
            }
            
    except Exception as e:
        logger.error(f"Error in owner_drawing_tool: {str(e)}")
        return {
            "success": False,
            "error": f"❌ An error occurred: {str(e)}"
        }
