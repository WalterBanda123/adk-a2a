# filepath: /Users/walterbanda/Desktop/AI/adk-a2a/store-agents/common/financial_service.py
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from firebase_admin import firestore
from .user_service import UserService

logger = logging.getLogger(__name__)

class FinancialService:
    def __init__(self):
        self.user_service = UserService()
        self.db = self.user_service.db
    
    async def get_financial_data(self, user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get comprehensive financial data for a user within a date range"""
        try:
            if not self.db:
                logger.warning("No database connection available")
                return {
                    "success": False,
                    "error": "Database connection unavailable",
                    "data": {}
                }
            
            # Get transactions data
            transactions = await self._get_transactions(user_id, start_date, end_date)
            
            # Get sales data
            sales = await self._get_sales(user_id, start_date, end_date)
            
            # Get expenses data
            expenses = await self._get_expenses(user_id, start_date, end_date)
            
            # Get inventory data
            inventory = await self._get_inventory(user_id, start_date, end_date)
            
            # Calculate financial metrics
            metrics = self._calculate_financial_metrics(transactions, sales, expenses)
            
            return {
                "success": True,
                "data": {
                    "transactions": transactions,
                    "sales": sales,
                    "expenses": expenses,
                    "inventory": inventory,
                    "metrics": metrics,
                    "period": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    }
                }
            }
        except Exception as e:
            logger.error(f"Error getting financial data for {user_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": {}
            }
    
    async def _get_transactions(self, user_id: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        try:
            if not self.db:
                return []
                
            transactions = []
            
            # Prioritize the transactions collection first, then try others
            collection_names = ['transactions', 'sales', 'records', 'business_transactions']
            
            # Convert datetime objects to date strings for comparison
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            
            for collection_name in collection_names:
                try:
                    # Strategy 1: Query by user_id field
                    query = self.db.collection(collection_name).where('user_id', '==', user_id)
                    query = query.where('date', '>=', start_date_str).where('date', '<=', end_date_str)
                    docs = query.get()
                    
                    for doc in docs:
                        if doc.exists:
                            data = doc.to_dict()
                            if data:  # Add null check
                                data['id'] = doc.id
                                data['collection'] = collection_name
                                transactions.append(data)
                    
                    # Strategy 2: Query by userId field (camelCase) - try this regardless of previous results
                    # This ensures we find all transactions regardless of which field is used
                    query = self.db.collection(collection_name).where('userId', '==', user_id)
                    query = query.where('date', '>=', start_date_str).where('date', '<=', end_date_str)
                    docs = query.get()
                    
                    for doc in docs:
                        if doc.exists:
                            data = doc.to_dict()
                            if data:  # Add null check
                                data['id'] = doc.id
                                data['collection'] = collection_name
                                transactions.append(data)
                        
                except Exception as e:
                    logger.debug(f"Collection {collection_name} not found or no date field: {str(e)}")
                    continue
            
            return transactions
            
        except Exception as e:
            logger.error(f"Error getting transactions: {str(e)}")
            return []
    
    async def _get_sales(self, user_id: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        try:
            if not self.db:
                return []
                
            sales = []
            
            # Convert datetime objects to date strings for comparison
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            
            try:
                # Strategy 1: Query by user_id field
                query = self.db.collection('transactions').where('userId', '==', user_id)
                query = query.where('date', '>=', start_date_str).where('date', '<=', end_date_str)
                docs = query.get()
                
                for doc in docs:
                    if doc.exists:
                        data = doc.to_dict()
                        if data:  # Add null check
                            data['id'] = doc.id
                            sales.append(data)
                
                # Strategy 2: Query by userId field (camelCase) - try regardless of previous results
                # This ensures we find all sales regardless of which field is used
                query = self.db.collection('sales').where('userId', '==', user_id)
                query = query.where('date', '>=', start_date_str).where('date', '<=', end_date_str)
                docs = query.get()
                
                for doc in docs:
                    if doc.exists:
                        data = doc.to_dict()
                        if data:  # Add null check
                            data['id'] = doc.id
                            sales.append(data)
                    
            except Exception as e:
                logger.debug(f"Sales collection query failed: {str(e)}")
            
            return sales
            
        except Exception as e:
            logger.error(f"Error getting sales: {str(e)}")
            return []
    
    async def _get_expenses(self, user_id: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        try:
            if not self.db:
                return []
                
            expenses = []
            
            # Convert datetime objects to date strings for comparison
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            
            try:
                # Strategy 1: Query by user_id field
                query = self.db.collection('expenses').where('userId', '==', user_id)
                query = query.where('date', '>=', start_date_str).where('date', '<=', end_date_str)
                docs = query.get()
                
                for doc in docs:
                    if doc.exists:
                        data = doc.to_dict()
                        if data:  # Add null check
                            data['id'] = doc.id
                            expenses.append(data)
                
                # Strategy 2: Query by userId field (camelCase) - try regardless of previous results
                # This ensures we find all expenses regardless of which field is used
                query = self.db.collection('expenses').where('userId', '==', user_id)
                query = query.where('date', '>=', start_date_str).where('date', '<=', end_date_str)
                docs = query.get()
                
                for doc in docs:
                    if doc.exists:
                        data = doc.to_dict()
                        if data:  # Add null check
                            data['id'] = doc.id
                            expenses.append(data)
                    
            except Exception as e:
                logger.debug(f"Expenses collection query failed: {str(e)}")
            
            return expenses
            
        except Exception as e:
            logger.error(f"Error getting expenses: {str(e)}")
            return []
    
    async def _get_inventory(self, user_id: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        try:
            if not self.db:
                return []
                
            inventory = []
            
            # Convert datetime objects to date strings for comparison
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            
            try:
                # Strategy 1: Query by user_id field
                query = self.db.collection('products').where('userId', '==', user_id)
                query = query.where('createdAt', '>=', start_date_str).where('createdAt', '<=', end_date_str)
                docs = query.get()
                
                for doc in docs:
                    if doc.exists:
                        data = doc.to_dict()
                        if data:  # Add null check
                            data['id'] = doc.id
                            inventory.append(data)
                
                # Strategy 2: Query by userId field (camelCase) - try regardless of previous results
                # This ensures we find all inventory records regardless of which field is used
                query = self.db.collection('products').where('userId', '==', user_id)
                query = query.where('date', '>=', start_date_str).where('date', '<=', end_date_str)
                docs = query.get()
                
                for doc in docs:
                    if doc.exists:
                        data = doc.to_dict()
                        if data:  # Add null check
                            data['id'] = doc.id
                            inventory.append(data)
                    
            except Exception as e:
                logger.debug(f"Inventory collection query failed: {str(e)}")
            
            return inventory
            
        except Exception as e:
            logger.error(f"Error getting inventory: {str(e)}")
            return []
    
    def _calculate_financial_metrics(self, transactions: List[Dict[str, Any]], 
                                   sales: List[Dict[str, Any]], 
                                   expenses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate financial metrics from the data with improved field detection"""
        
        # Define possible field names for different values
        amount_fields = ['amount', 'price', 'total', 'value', 'sale_amount', 'transaction_amount', 'payment']
        status_fields = ['status', 'state', 'transaction_status']
        completed_values = ['completed', 'complete', 'success', 'successful', 'paid', 'confirmed']
        
        # Helper function to get amount from different possible field names
        def get_amount(item):
            if not item:
                return 0
                
            for field in amount_fields:
                if field in item:
                    try:
                        value = item[field]
                        # Convert to float if it's a string with possible commas
                        if isinstance(value, str):
                            value = float(value.replace(',', '').strip())
                        return float(value)
                    except (ValueError, TypeError):
                        # If conversion fails, try next field
                        continue
            return 0
            
        # Helper function to check if transaction is completed
        def is_completed(item):
            if not item:
                return False
                
            for field in status_fields:
                if field in item and item[field] and str(item[field]).lower() in completed_values:
                    return True
                    
            # If no status field or no completed status, assume it's valid
            # This helps when the data doesn't follow the expected format
            return True
            
        # Calculate revenue from transactions
        total_revenue_transactions = 0
        completed_transactions = []
        
        for transaction in transactions:
            if is_completed(transaction):
                amount = get_amount(transaction)
                total_revenue_transactions += amount
                completed_transactions.append(transaction)
        
        # Calculate revenue from sales (some systems store sales separately)
        total_revenue_sales = 0
        for sale in sales:
            if is_completed(sale):
                amount = get_amount(sale)
                total_revenue_sales += amount
                
        # Use the higher of the two revenue calculations
        # This handles cases where data might be in either collection
        total_revenue = max(total_revenue_transactions, total_revenue_sales)
        
        # If both are zero but we have transaction or sales records, try to find any numeric values
        if total_revenue == 0 and (transactions or sales):
            logger.info("No standard amount fields found, checking for any numeric fields")
            
            # Try all possible fields that might contain monetary values
            for item in transactions + sales:
                if not item:
                    continue
                    
                for key, value in item.items():
                    # Skip obvious non-monetary fields
                    if key.lower() in ['user_id', 'userid', 'id', 'date', 'timestamp', 'collection']:
                        continue
                        
                    try:
                        # Try to convert to number if it's a non-zero value
                        if isinstance(value, str) and value:
                            value = value.replace(',', '').strip()
                        val = float(value)
                        if val > 0:
                            total_revenue += val
                            logger.info(f"Adding value {val} from field {key}")
                    except:
                        continue
        
        # Calculate total expenses
        total_expenses = 0
        for expense in expenses:
            amount = get_amount(expense)
            total_expenses += amount
        
        # Calculate profit/loss
        profit_loss = total_revenue - total_expenses
        
        # Calculate profit margin
        profit_margin = (profit_loss / total_revenue * 100) if total_revenue > 0 else 0
        
        # Count transactions - use either completed transactions or all transactions if empty
        transaction_count = len(completed_transactions) if completed_transactions else len(transactions)
        if transaction_count == 0 and sales:
            transaction_count = len(sales)  # Use sales count as fallback
        
        return {
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "profit_loss": profit_loss,
            "profit_margin": profit_margin,
            "transaction_count": transaction_count,
            "avg_transaction_value": total_revenue / transaction_count if transaction_count > 0 else 0
        }
    
    def parse_date_period(self, period: str) -> tuple[datetime, datetime]:
        """Parse natural language date periods into start and end dates"""
        now = datetime.now()
        period = period.lower().strip()
        
        if period in ['today', 'today\'s']:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        elif period in ['yesterday', 'yesterday\'s']:
            yesterday = now - timedelta(days=1)
            start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        elif period in ['this week', 'week', 'weekly']:
            # Start from Monday of current week
            days_since_monday = now.weekday()
            start = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        
        elif period in ['last week', 'previous week']:
            # Last week Monday to Sunday
            days_since_monday = now.weekday()
            this_monday = now - timedelta(days=days_since_monday)
            last_monday = this_monday - timedelta(days=7)
            start = last_monday.replace(hour=0, minute=0, second=0, microsecond=0)
            end = (last_monday + timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=999999)
        
        elif period in ['this month', 'month', 'monthly']:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now
        
        elif period in ['last month', 'previous month']:
            # First day of last month
            first_this_month = now.replace(day=1)
            start = (first_this_month - timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = (first_this_month - timedelta(seconds=1))
        
        elif period.endswith(' days'):
            # Extract number of days
            try:
                days = int(period.split()[0])
                start = now - timedelta(days=days)
                end = now
            except ValueError:
                # Default to 7 days if parsing fails
                start = now - timedelta(days=7)
                end = now
        
        elif period.endswith(' day'):
            # Handle "1 day" case
            try:
                days = int(period.split()[0])
                start = now - timedelta(days=days)
                end = now
            except ValueError:
                # Default to 1 day if parsing fails
                start = now - timedelta(days=1)
                end = now
        
        else:
            # Default to last 7 days for unrecognized periods
            start = now - timedelta(days=7)
            end = now
        
        return start, end
