import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from firebase_admin import firestore
from .user_service import UserService

logger = logging.getLogger(__name__)

class MiscTransactionsService:
    def __init__(self):
        self.user_service = UserService()
        self.db = self.user_service.db
    
    async def record_petty_cash_withdrawal(self, user_id: str, amount: float, purpose: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """Record a petty cash withdrawal transaction"""
        try:
            if not self.db:
                return {
                    "success": False,
                    "error": "Database connection unavailable"
                }
            
            # Check available cash first
            cash_balance = await self.get_current_cash_balance(user_id)
            if cash_balance < amount:
                return {
                    "success": False,
                    "error": f"Insufficient cash balance. Available: ${cash_balance:.2f}, Requested: ${amount:.2f}"
                }
            
            transaction_id = f"PCW_{user_id}_{int(datetime.now().timestamp())}"
            
            transaction_data = {
                "id": transaction_id,
                "user_id": user_id,
                "type": "petty_cash_withdrawal",
                "amount": amount,
                "purpose": purpose,
                "notes": notes or "",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%H:%M:%S"),
                "timestamp": datetime.now(),
                "status": "completed",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            # Add to misc_transactions collection
            self.db.collection('misc_transactions').document(transaction_id).set(transaction_data)
            
            # Update cash balance
            await self.update_cash_balance(user_id, -amount, f"Petty cash withdrawal: {purpose}")
            
            logger.info(f"Recorded petty cash withdrawal: {transaction_id} for ${amount}")
            
            return {
                "success": True,
                "transaction_id": transaction_id,
                "message": f"Petty cash withdrawal of ${amount:.2f} recorded successfully",
                "remaining_balance": cash_balance - amount
            }
            
        except Exception as e:
            logger.error(f"Error recording petty cash withdrawal: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def record_owner_drawing(self, user_id: str, amount: float, purpose: str = "Owner drawing", notes: Optional[str] = None) -> Dict[str, Any]:
        """Record an owner drawing (withdrawal from business for personal use)"""
        try:
            if not self.db:
                return {
                    "success": False,
                    "error": "Database connection unavailable"
                }
            
            # Check available cash first
            cash_balance = await self.get_current_cash_balance(user_id)
            if cash_balance < amount:
                return {
                    "success": False,
                    "error": f"Insufficient cash balance. Available: ${cash_balance:.2f}, Requested: ${amount:.2f}"
                }
            
            transaction_id = f"DRW_{user_id}_{int(datetime.now().timestamp())}"
            
            transaction_data = {
                "id": transaction_id,
                "user_id": user_id,
                "type": "owner_drawing",
                "amount": amount,
                "purpose": purpose,
                "notes": notes or "",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%H:%M:%S"),
                "timestamp": datetime.now(),
                "status": "completed",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            # Add to misc_transactions collection
            self.db.collection('misc_transactions').document(transaction_id).set(transaction_data)
            
            # Update cash balance
            await self.update_cash_balance(user_id, -amount, f"Owner drawing: {purpose}")
            
            logger.info(f"Recorded owner drawing: {transaction_id} for ${amount}")
            
            return {
                "success": True,
                "transaction_id": transaction_id,
                "message": f"Owner drawing of ${amount:.2f} recorded successfully",
                "remaining_balance": cash_balance - amount
            }
            
        except Exception as e:
            logger.error(f"Error recording owner drawing: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def record_cash_deposit(self, user_id: str, amount: float, source: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """Record a cash deposit (adding money to the business)"""
        try:
            if not self.db:
                return {
                    "success": False,
                    "error": "Database connection unavailable"
                }
            
            transaction_id = f"DEP_{user_id}_{int(datetime.now().timestamp())}"
            
            transaction_data = {
                "id": transaction_id,
                "user_id": user_id,
                "type": "cash_deposit",
                "amount": amount,
                "source": source,
                "notes": notes or "",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%H:%M:%S"),
                "timestamp": datetime.now(),
                "status": "completed",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            # Add to misc_transactions collection
            self.db.collection('misc_transactions').document(transaction_id).set(transaction_data)
            
            # Update cash balance
            current_balance = await self.get_current_cash_balance(user_id)
            await self.update_cash_balance(user_id, amount, f"Cash deposit: {source}")
            
            logger.info(f"Recorded cash deposit: {transaction_id} for ${amount}")
            
            return {
                "success": True,
                "transaction_id": transaction_id,
                "message": f"Cash deposit of ${amount:.2f} recorded successfully",
                "new_balance": current_balance + amount
            }
            
        except Exception as e:
            logger.error(f"Error recording cash deposit: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_current_cash_balance(self, user_id: str) -> float:
        """Get the current cash balance for a user"""
        try:
            if not self.db:
                return 0.0
            
            # Check if cash_balances document exists
            cash_doc = self.db.collection('cash_balances').document(user_id).get()
            
            if cash_doc.exists:
                data = cash_doc.to_dict()
                if data:  # Add null check
                    return data.get('balance', 0.0)
                return 0.0
            else:
                # Initialize cash balance to 0 if not exists
                await self.initialize_cash_balance(user_id)
                return 0.0
                
        except Exception as e:
            logger.error(f"Error getting cash balance: {str(e)}")
            return 0.0
    
    async def initialize_cash_balance(self, user_id: str, initial_balance: float = 0.0) -> Dict[str, Any]:
        """Initialize cash balance for a user"""
        try:
            if not self.db:
                return {
                    "success": False,
                    "error": "Database connection unavailable"
                }
            
            balance_data = {
                "user_id": user_id,
                "balance": initial_balance,
                "last_updated": datetime.now(),
                "created_at": datetime.now()
            }
            
            self.db.collection('cash_balances').document(user_id).set(balance_data)
            
            return {
                "success": True,
                "message": f"Cash balance initialized to ${initial_balance:.2f}"
            }
            
        except Exception as e:
            logger.error(f"Error initializing cash balance: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_cash_balance(self, user_id: str, amount_change: float, description: str) -> Dict[str, Any]:
        """Update the cash balance by adding or subtracting an amount"""
        try:
            if not self.db:
                return {
                    "success": False,
                    "error": "Database connection unavailable"
                }
            
            current_balance = await self.get_current_cash_balance(user_id)
            new_balance = current_balance + amount_change
            
            # Update balance
            self.db.collection('cash_balances').document(user_id).update({
                'balance': new_balance,
                'last_updated': datetime.now()
            })
            
            # Record the balance change
            change_id = f"BAL_{user_id}_{int(datetime.now().timestamp())}"
            change_data = {
                "id": change_id,
                "user_id": user_id,
                "amount_change": amount_change,
                "previous_balance": current_balance,
                "new_balance": new_balance,
                "description": description,
                "timestamp": datetime.now(),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%H:%M:%S")
            }
            
            self.db.collection('balance_changes').document(change_id).set(change_data)
            
            return {
                "success": True,
                "previous_balance": current_balance,
                "new_balance": new_balance,
                "amount_change": amount_change
            }
            
        except Exception as e:
            logger.error(f"Error updating cash balance: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_misc_transactions(self, user_id: str, limit: int = 50, transaction_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get miscellaneous transactions for a user"""
        try:
            if not self.db:
                return []
            
            # Simple query to avoid index issues - using updated Firestore syntax
            query = self.db.collection('misc_transactions').where('user_id', '==', user_id)
            
            if transaction_type:
                query = query.where('type', '==', transaction_type)
            
            # Remove ordering to avoid composite index requirement
            docs = query.get()
            
            transactions = []
            for doc in docs:
                if doc.exists:
                    data = doc.to_dict()
                    if data:  # Add null check
                        data['id'] = doc.id
                        transactions.append(data)
            
            # Sort manually by created_at or timestamp if available
            transactions.sort(key=lambda x: x.get('created_at') or x.get('timestamp') or x.get('date', ''), reverse=True)
            
            # Apply limit after sorting
            return transactions[:limit]
            
        except Exception as e:
            logger.error(f"Error getting misc transactions: {str(e)}")
            # Fallback: get all transactions for user and filter manually
            try:
                if not self.db:
                    return []
                    
                query = self.db.collection('misc_transactions').where('user_id', '==', user_id).limit(limit)
                docs = query.get()
                
                transactions = []
                for doc in docs:
                    if doc.exists:
                        data = doc.to_dict()
                        if data:  # Add null check
                            data['id'] = doc.id
                            if not transaction_type or data.get('type') == transaction_type:
                                transactions.append(data)
                
                # Sort by created_at manually
                transactions.sort(key=lambda x: x.get('created_at', datetime.min), reverse=True)
                return transactions[:limit]
                
            except Exception as fallback_error:
                logger.error(f"Fallback query also failed: {str(fallback_error)}")
                return []
    
    async def get_transaction_summary(self, user_id: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get summary of miscellaneous transactions"""
        try:
            if not self.db:
                return {}
            
            # Simple query without date filtering to avoid index issues - using updated Firestore syntax
            query = self.db.collection('misc_transactions').where('user_id', '==', user_id)
            
            docs = query.get()
            
            summary = {
                "total_withdrawals": 0.0,
                "total_deposits": 0.0,
                "petty_cash_total": 0.0,
                "drawings_total": 0.0,
                "transaction_count": 0,
                "transactions_by_type": {}
            }
            
            for doc in docs:
                if doc.exists:
                    data = doc.to_dict()
                    if not data:  # Add null check
                        continue
                        
                    transaction_date_str = data.get('date', '')
                    
                    # Manual date filtering if dates are provided
                    if start_date or end_date:
                        try:
                            if transaction_date_str:
                                transaction_date = datetime.strptime(transaction_date_str, "%Y-%m-%d")
                                if start_date and transaction_date < start_date:
                                    continue
                                if end_date and transaction_date > end_date:
                                    continue
                        except ValueError:
                            # Skip transactions with invalid dates
                            continue
                    
                    transaction_type = data.get('type', 'unknown')
                    amount = data.get('amount', 0.0)
                    
                    summary["transaction_count"] += 1
                    
                    if transaction_type not in summary["transactions_by_type"]:
                        summary["transactions_by_type"][transaction_type] = {"count": 0, "total": 0.0}
                    
                    summary["transactions_by_type"][transaction_type]["count"] += 1
                    summary["transactions_by_type"][transaction_type]["total"] += amount
                    
                    if transaction_type == "petty_cash_withdrawal":
                        summary["petty_cash_total"] += amount
                        summary["total_withdrawals"] += amount
                    elif transaction_type == "owner_drawing":
                        summary["drawings_total"] += amount
                        summary["total_withdrawals"] += amount
                    elif transaction_type == "cash_deposit":
                        summary["total_deposits"] += amount
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting transaction summary: {str(e)}")
            return {}
