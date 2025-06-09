import os
import logging
import sys
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from common.misc_transactions_service import MiscTransactionsService

logger = logging.getLogger(__name__)

async def get_transaction_history_tool(user_id: str, limit: int = 10, transaction_type: str = "") -> Dict[str, Any]:
    """
    Tool for retrieving recent miscellaneous transaction history.
    
    Args:
        user_id (str): The user ID of the business owner
        limit (int): Maximum number of transactions to retrieve (default: 10)
        transaction_type (str): Filter by transaction type ("petty_cash_withdrawal", "owner_drawing", "cash_deposit")
        
    Returns:
        Dict containing transaction history and summary
    """
    try:
        service = MiscTransactionsService()
        
        # Get transactions
        filter_type = transaction_type if transaction_type else None
        transactions = await service.get_misc_transactions(user_id, limit, filter_type)
        
        if not transactions:
            return {
                "success": True,
                "message": "📄 No miscellaneous transactions found.",
                "transactions": [],
                "count": 0
            }
        
        # Format transactions for display
        formatted_transactions = []
        for txn in transactions:
            formatted_txn = {
                "date": txn.get('date', ''),
                "time": txn.get('time', ''),
                "type": txn.get('type', ''),
                "amount": txn.get('amount', 0),
                "description": txn.get('purpose', txn.get('source', '')),
                "notes": txn.get('notes', ''),
                "id": txn.get('id', '')
            }
            formatted_transactions.append(formatted_txn)
        
        # Create display message
        message = f"📄 Recent Miscellaneous Transactions ({len(transactions)} found):\n\n"
        
        for txn in formatted_transactions[:5]:  # Show only first 5 in message
            type_emoji = {
                "petty_cash_withdrawal": "💸",
                "owner_drawing": "👤",
                "cash_deposit": "💰"
            }.get(txn["type"], "📝")
            
            message += f"{type_emoji} {txn['date']} {txn['time']}\n"
            message += f"   Type: {txn['type'].replace('_', ' ').title()}\n"
            message += f"   Amount: ${txn['amount']:.2f}\n"
            message += f"   Description: {txn['description']}\n"
            if txn['notes']:
                message += f"   Notes: {txn['notes']}\n"
            message += "\n"
        
        if len(transactions) > 5:
            message += f"... and {len(transactions) - 5} more transactions\n"
        
        return {
            "success": True,
            "message": message,
            "transactions": formatted_transactions,
            "count": len(transactions)
        }
        
    except Exception as e:
        logger.error(f"Error in get_transaction_history_tool: {str(e)}")
        return {
            "success": False,
            "error": f"❌ An error occurred while retrieving transaction history: {str(e)}"
        }

async def get_transaction_summary_tool(user_id: str, days: int = 30) -> Dict[str, Any]:
    """
    Tool for getting a summary of miscellaneous transactions over a period.
    
    Args:
        user_id (str): The user ID of the business owner
        days (int): Number of days to look back (default: 30)
        
    Returns:
        Dict containing transaction summary and statistics
    """
    try:
        service = MiscTransactionsService()
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        summary = await service.get_transaction_summary(user_id, start_date, end_date)
        
        if not summary or summary.get("transaction_count", 0) == 0:
            return {
                "success": True,
                "message": f"📊 No miscellaneous transactions found in the last {days} days.",
                "summary": {}
            }
        
        # Format summary message
        message = f"📊 Miscellaneous Transactions Summary (Last {days} days):\n\n"
        message += f"🔢 Total Transactions: {summary['transaction_count']}\n"
        message += f"💸 Total Withdrawals: ${summary['total_withdrawals']:.2f}\n"
        message += f"💰 Total Deposits: ${summary['total_deposits']:.2f}\n"
        message += f"📈 Net Cash Flow: ${summary['total_deposits'] - summary['total_withdrawals']:.2f}\n\n"
        
        message += "📋 Breakdown by Type:\n"
        for txn_type, data in summary.get("transactions_by_type", {}).items():
            type_display = txn_type.replace('_', ' ').title()
            message += f"  • {type_display}: {data['count']} transactions, ${data['total']:.2f}\n"
        
        # Get current balance
        current_balance = await service.get_current_cash_balance(user_id)
        message += f"\n🏦 Current Cash Balance: ${current_balance:.2f}"
        
        return {
            "success": True,
            "message": message,
            "summary": summary,
            "current_balance": current_balance
        }
        
    except Exception as e:
        logger.error(f"Error in get_transaction_summary_tool: {str(e)}")
        return {
            "success": False,
            "error": f"❌ An error occurred while generating transaction summary: {str(e)}"
        }
