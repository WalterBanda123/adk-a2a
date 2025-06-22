"""
Unified Chat Agent Coordinator
Handles all chat interactions through specialized sub-agents
"""
import os
import sys
import logging
import json
import asyncio
from typing import Dict, Any, Optional, List
import re

# Configure logging for debugging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# Import sub-agents
from agents.product_transaction_agent.agent import ProductTransactionAgent
from agents.misc_transactions.agent import MiscTransactionsAgent
from agents.assistant.financial_reporting_subagent import create_financial_reporting_subagent

# Import common services
from common.user_service import UserService
from common.real_product_service import RealProductService

logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str = Field(..., description="User's chat message")
    user_id: Optional[str] = Field(None, description="User identifier (can be in context instead)")
    session_id: Optional[str] = Field(None, description="Session identifier")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    image_data: Optional[str] = Field(None, description="Base64 image data for vision tasks")
    is_url: Optional[bool] = Field(False, description="Whether image_data is a URL")

class ChatResponse(BaseModel):
    message: str = Field(..., description="Agent response")
    agent_used: str = Field(..., description="Which sub-agent handled the request")
    status: str = Field(default="success", description="Response status")
    data: Dict[str, Any] = Field(default_factory=dict, description="Additional response data")
    session_id: Optional[str] = Field(None, description="Session identifier")

class UnifiedChatCoordinator:
    """
    Main coordinator that routes chat requests to appropriate sub-agents
    """
    
    def __init__(self):
        self.name = "Store Assistant"
        self.description = "Unified chat interface for store management"
        
        # Initialize sub-agents
        self.product_agent = ProductTransactionAgent()
        self.misc_agent = MiscTransactionsAgent()
        self.financial_agent = None  # Will be initialized async
        
        # Initialize services
        self.user_service = UserService()
        self.product_service = RealProductService()
        
        # Agent capabilities - let agents decide what they can handle
        self.agent_capabilities = {
            'product_transaction': {
                'agent': self.product_agent,
                'description': 'Handles product sales, transactions, receipts, and product registration',
                'keywords': ['sell', 'sold', 'buy', 'bought', 'transaction', 'receipt', 'customer', 'purchase', 'register product', 'scan', 'photo', 'image']
            },
            'misc_transactions': {
                'agent': self.misc_agent, 
                'description': 'Handles petty cash, owner drawings, deposits, and other financial transactions',
                'keywords': ['petty cash', 'drawing', 'deposit', 'withdraw', 'expense', 'cash']
            }
        }
        
    async def _ensure_financial_agent(self):
        """Lazy initialization of financial reporting agent"""
        if self.financial_agent is None:
            self.financial_agent = await create_financial_reporting_subagent()
    
    def should_route_to_agent(self, message: str, agent_type: str, has_image: bool = False) -> bool:
        """
        Simple heuristic to determine if message should go to specific agent
        """
        message_lower = message.lower()
        
        if agent_type == 'product_transaction':
            # Check if it's about products, sales, transactions, or has an image
            if has_image:
                logger.info(f"Routing to product_transaction (has_image=True): {message}")
                return True
            keywords = self.agent_capabilities['product_transaction']['keywords']
            # Use word boundaries to avoid partial matches (e.g., "sale" shouldn't match "sales")
            import re
            matches = []
            for keyword in keywords:
                # Use word boundaries to match whole words only
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, message_lower):
                    matches.append(keyword)
            
            if matches:
                logger.info(f"Routing to product_transaction (matches: {matches}): {message}")
                return True
            return False
        
        elif agent_type == 'misc_transactions':
            keywords = self.agent_capabilities['misc_transactions']['keywords']
            # Use word boundaries for misc transactions too
            import re
            matches = []
            for keyword in keywords:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, message_lower):
                    matches.append(keyword)
            
            if matches:
                logger.info(f"Routing to misc_transactions (matches: {matches}): {message}")
                return True
            return False
        
        return False
    
    async def route_to_agent(self, message: str, user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intelligent agent routing - let agents decide if they can handle the request
        """
        try:
            has_image = bool(context.get('image_data'))
            message_lower = message.lower()
            
            logger.info(f"Routing message: '{message}' (has_image: {has_image})")
            
            # Handle simple confirmations first
            if re.match(r'^(confirm|cancel)\s+txn_', message_lower):
                logger.info("Routing to transaction confirmation handler")
                return await self.handle_transaction_confirmation(message, user_id, context)
            
            # Handle greetings
            if any(greeting in message_lower for greeting in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
                logger.info("Routing to general help (greeting)")
                return await self.handle_general_help(message, user_id, context)
            
            # Handle reports FIRST and EXPLICITLY (highest priority to avoid conflicts)
            # Check for any report-related keywords
            report_keywords = ['report', 'financial', 'analytics', 'generate report', 'sales report', 'yesterday', 'last week', 'last month', 'generate a report']
            if any(keyword in message_lower for keyword in report_keywords):
                logger.info(f"Routing to financial report (matched report keywords)")
                return await self.handle_financial_report(message, user_id, context)
            
            # Handle inventory/stock queries (before product transaction to avoid confusion)
            if any(keyword in message_lower for keyword in ['inventory', 'stock', 'how many products', 'low stock', 'out of stock']):
                logger.info("Routing to inventory query")
                return await self.handle_inventory_query(message, user_id, context)
            
            # Handle store queries
            if any(keyword in message_lower for keyword in ['store info', 'business details', 'store analytics']):
                logger.info("Routing to store query")
                return await self.handle_store_query(message, user_id, context)
            
            # Try misc transactions agent (before product transactions to avoid confusion)
            if self.should_route_to_agent(message, 'misc_transactions'):
                logger.info("Routing to misc transactions")
                return await self.handle_misc_transaction('auto', message, user_id, context)
            
            # Try product/transaction agent (handles direct sales transactions, not reports)
            if self.should_route_to_agent(message, 'product_transaction', has_image):
                if has_image:
                    logger.info("Routing to product registration (image)")
                    return await self.handle_product_registration(message, user_id, context)
                else:
                    logger.info("Routing to transaction handler")
                    return await self.handle_transaction(message, user_id, context)
            
            # Default to general help
            logger.info("Routing to general help (default)")
            return await self.handle_general_help(message, user_id, context)
                
        except Exception as e:
            logger.error(f"Error routing to agent: {e}")
            return {
                "message": f"Sorry, I encountered an error: {str(e)}",
                "agent_used": "error_handler",
                "status": "error"
            }
    
    async def handle_product_registration(self, message: str, user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle product registration via image"""
        try:
            if not context.get('image_data'):
                return {
                    "message": "🖼️ Please provide an image to register a product. You can upload a photo of the product and I'll extract the details automatically!",
                    "agent_used": "product_registration",
                    "status": "info"
                }
            
            # Use product transaction agent for image registration
            from agents.product_transaction_agent.models import ProductRegistrationRequest
            
            request = ProductRegistrationRequest(
                image_data=context['image_data'],
                user_id=user_id,
                is_url=context.get('is_url', False),
                enhance_image=True
            )
            
            result = await self.product_agent.register_product_image(request)
            
            return {
                "message": result.message,
                "agent_used": "product_registration",
                "status": "success" if result.success else "error",
                "data": {
                    "product": result.product,
                    "confidence": result.confidence,
                    "sku": result.sku
                }
            }
            
        except Exception as e:
            return {
                "message": f"❌ Error registering product: {str(e)}",
                "agent_used": "product_registration",
                "status": "error"
            }
    
    async def handle_transaction(self, message: str, user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle sales transactions"""
        try:
            logger.info(f"Processing transaction: {message} for user {user_id}")
            
            # Use product transaction agent for chat-based transactions
            from agents.product_transaction_agent.models import TransactionRequest
            
            request = TransactionRequest(
                message=message,
                user_id=user_id,
                customer_name=context.get('customer_name'),
                payment_method=context.get('payment_method', 'cash')
            )
            
            result = await self.product_agent.process_chat_transaction(request)
            
            # Use chat_response if available (contains formatted confirmation), otherwise use message
            response_message = result.chat_response if result.chat_response else result.message
            
            # Clean up data - remove technical fields
            clean_data = {}
            if result.receipt:
                clean_data["receipt"] = result.receipt.dict()
            if result.frontend_receipt:
                clean_data["frontend_receipt"] = result.frontend_receipt.dict()
            if result.pending_transaction_id:
                clean_data["pending_transaction_id"] = result.pending_transaction_id
            if result.confirmation_required:
                clean_data["confirmation_required"] = result.confirmation_required
            
            return {
                "message": response_message,
                "agent_used": "transaction_processor",
                "status": "success" if result.success else "error",
                "data": clean_data
            }
            
        except Exception as e:
            logger.error(f"Error processing transaction: {e}")
            return {
                "message": f"❌ Error processing transaction: {str(e)}",
                "agent_used": "transaction_processor", 
                "status": "error"
            }
    
    async def handle_misc_transaction(self, intent: str, message: str, user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle miscellaneous transactions (petty cash, drawings, deposits)"""
        try:
            result = await self.misc_agent.process_request(user_id, message, intent=intent)
            
            return {
                "message": result.get("message", "Transaction processed"),
                "agent_used": "misc_transactions",
                "status": result.get("status", "success"),
                "data": result.get("data", {})
            }
            
        except Exception as e:
            return {
                "message": f"❌ Error processing transaction: {str(e)}",
                "agent_used": "misc_transactions",
                "status": "error"
            }
    
    async def handle_inventory_query(self, message: str, user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle inventory and stock queries"""
        try:
            message_lower = message.lower()
            
            if 'low stock' in message_lower or 'low inventory' in message_lower:
                products = await self.product_service.get_low_stock_products(user_id)
                if products:
                    product_list = "\\n".join([f"• {p.get('product_name', p.get('name', 'Unknown'))} - {p.get('stock_quantity', p.get('quantity', 0))} units" for p in products[:10]])
                    message = f"⚠️ **Low Stock Items:**\\n{product_list}"
                else:
                    message = "✅ All products are well stocked!"
                    
            elif 'analytics' in message_lower or 'summary' in message_lower:
                analytics = await self.product_service.get_product_analytics(user_id)
                if analytics:
                    message = f"""📊 **Store Analytics:**
• Total Products: {analytics.get('total_products', 0)}
• Total Value: ${analytics.get('total_inventory_value', 0):.2f}
• Low Stock Items: {analytics.get('low_stock_count', 0)}
• Out of Stock: {analytics.get('out_of_stock_count', 0)}"""
                else:
                    message = "📊 No analytics data available yet."
            
            else:
                # General inventory query - get basic product list
                products = await self.product_service.get_store_products(user_id)
                if products:
                    # Create a better formatted response showing actual products
                    if len(products) <= 5:
                        # Show all products if there are 5 or fewer
                        product_list = "\\n".join([
                            f"• {p.get('product_name', p.get('name', 'Unknown'))} - {p.get('stock_quantity', p.get('quantity', 0))} units"
                            for p in products
                        ])
                        message = f"📦 **Your Current Inventory:**\\n{product_list}\\n\\nAll quantities shown in units/items."
                    else:
                        # Show summary if more than 5 products
                        total_count = len(products)
                        total_units = sum(p.get('stock_quantity', p.get('quantity', 0)) for p in products)
                        message = f"📦 **Inventory Summary:**\\n• {total_count} different products\\n• {total_units} total units in stock\\n\\nUse 'low stock' or 'analytics' for detailed views."
                else:
                    message = "📦 Your inventory is empty. Start by adding products with images!"
            
            return {
                "message": message,
                "agent_used": "inventory_manager",
                "status": "success",
                "data": {"user_id": user_id}
            }
            
        except Exception as e:
            return {
                "message": f"❌ Error checking inventory: {str(e)}",
                "agent_used": "inventory_manager",
                "status": "error"
            }
    
    async def handle_store_query(self, message: str, user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle store and business queries"""
        try:
            user_info = await self.user_service.get_user_info(user_id)
            store_info = await self.user_service.get_store_info(user_id)
            
            if not user_info:
                return {
                    "message": "❌ User profile not found. Please check your user ID.",
                    "agent_used": "store_manager",
                    "status": "error"
                }
            
            message_parts = []
            
            # User info
            if user_info:
                message_parts.append(f"👤 **User:** {user_info.get('name', 'Unknown')}")
                if user_info.get('business_owner'):
                    message_parts.append(f"🏪 **Business Owner** in {user_info.get('city', 'Unknown')}, {user_info.get('country', 'Unknown')}")
            
            # Store info  
            if store_info:
                message_parts.append(f"🏬 **Store:** {store_info.get('store_name', 'Unknown')}")
                message_parts.append(f"💼 **Type:** {store_info.get('business_type', 'General')}")
                if store_info.get('currency'):
                    message_parts.append(f"💰 **Currency:** {store_info.get('currency')}")
            
            if not message_parts:
                message_parts.append("ℹ️ Store information not available. Please set up your store profile.")
            
            return {
                "message": "\\n".join(message_parts),
                "agent_used": "store_manager", 
                "status": "success",
                "data": {
                    "user_info": user_info,
                    "store_info": store_info
                }
            }
            
        except Exception as e:
            return {
                "message": f"❌ Error retrieving store information: {str(e)}",
                "agent_used": "store_manager",
                "status": "error"
            }
    
    async def handle_financial_report(self, message: str, user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle financial report generation requests"""
        try:
            from agents.assistant.tools.financial_report_tool import generate_financial_report_func
            from common.financial_service import FinancialService
            from common.pdf_report_generator import PDFReportGenerator
            
            # Initialize services
            financial_service = FinancialService()
            pdf_generator = PDFReportGenerator()
            
            # Extract period from message (default to today)
            period = "today"
            if "month" in message.lower() or "monthly" in message.lower():
                period = "this month"
            elif "week" in message.lower() or "weekly" in message.lower():
                period = "this week"
            elif "year" in message.lower() or "yearly" in message.lower() or "annual" in message.lower():
                period = "this year"
            elif "yesterday" in message.lower():
                period = "yesterday"
            elif "last week" in message.lower():
                period = "last week"
            elif "last month" in message.lower():
                period = "last month"
            elif "last year" in message.lower():
                period = "last year"
            elif "last two days" in message.lower() or "past two days" in message.lower():
                period = "last two days"
            
            # Generate the report
            result = await generate_financial_report_func(
                user_id=user_id,
                period=period,
                include_insights=True,
                financial_service=financial_service,
                pdf_generator=pdf_generator,
                user_service=self.user_service
            )
            
            if result.get('success'):
                filename = result.get('filename', '')
                firebase_url = result.get('firebase_url')
                download_url = result.get('download_url')
                
                # Check if we're using local storage fallback (URL starts with /)
                is_local_storage = firebase_url and firebase_url.startswith('/')
                
                # Create proper download URLs for frontend
                if is_local_storage:
                    # Convert local path to server URL
                    server_url = f"http://localhost:8003{firebase_url}"
                    actual_filename = firebase_url.split('/')[-1] if firebase_url else ""
                else:
                    # Use Firebase URL as-is
                    server_url = firebase_url
                    actual_filename = filename or ""
                
                # Ensure we have a proper download URL
                final_download_url = download_url or server_url or f"/download/{actual_filename}"
                
                # Create user-friendly message without URLs
                message_text = f"� **Financial Report Generated Successfully!**\n\n"
                
                # Add period info
                message_text += f"� **Period:** {period.title()}\n"
                
                # Add summary if available
                if result.get('summary'):
                    summary = result['summary']
                    message_text += f"💰 **Revenue:** ${summary.get('total_revenue', 0):.2f}\n"
                    message_text += f"💸 **Expenses:** ${summary.get('total_expenses', 0):.2f}\n"
                    message_text += f"💵 **Net Profit:** ${summary.get('net_profit', 0):.2f}\n"
                    message_text += f"📦 **Transactions:** {summary.get('transaction_count', 0)}\n\n"
                
                if actual_filename:
                    message_text += f"📄 **Report:** {actual_filename}\n"
                
                message_text += "✅ Your PDF report has been generated and is ready for download!"
                
                return {
                    "message": message_text,
                    "agent_used": "financial_reporting",
                    "status": "success",
                    "data": {
                        "filename": actual_filename,
                        "download_url": final_download_url,
                        "firebase_url": firebase_url,
                        "server_url": server_url,  # Direct server URL for frontend
                        "storage_type": "local" if is_local_storage else "firebase",
                        "summary": result.get('summary', {}),
                        "period": period
                    }
                }
            else:
                return {
                    "message": f"❌ Error generating report: {result.get('error', 'Unknown error')}",
                    "agent_used": "financial_reporting",
                    "status": "error",
                    "data": {"error": result.get('error', 'Unknown error')}
                }
                
        except Exception as e:
            logger.error(f"Error in financial report handler: {e}")
            return {
                "message": f"❌ Error generating financial report: {str(e)}",
                "agent_used": "financial_reporting",
                "status": "error"
            }
    
    async def handle_general_help(self, message: str, user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general help and greetings with personalized user recognition"""
        try:
            message_lower = message.lower()
            
            # Check if this is a greeting
            greeting_patterns = [r'hello', r'hi', r'hey', r'good morning', r'good afternoon', r'good evening', r'greetings']
            is_greeting = any(re.search(pattern, message_lower) for pattern in greeting_patterns)
            
            if is_greeting:
                # Load user profile for personalized greeting
                user_info = await self.user_service.get_user_info(user_id)
                store_info = await self.user_service.get_store_info(user_id)
                
                if user_info and store_info:
                    # Personalized greeting for existing user
                    user_name = user_info.get('name', 'there')
                    store_name = store_info.get('store_name', 'your store')
                    business_type = store_info.get('business_type', 'business')
                    
                    # Get recent activity context
                    products = await self.product_service.get_store_products(user_id)
                    product_count = len(products) if products else 0
                    
                    greeting_message = f"""👋 Hello {user_name}! Welcome back to your {business_type}.

🏪 **{store_name}** Dashboard:
📦 Products in inventory: {product_count}
🆔 Session ID: {context.get('session_id', 'N/A')}

What would you like to do today?
• 📸 Register new products (upload images)
• 💰 Process sales transactions  
• 📊 Check inventory or analytics
• 💵 Manage cash (petty cash, deposits, drawings)

Just tell me what you need! 😊"""
                    
                    return {
                        "message": greeting_message,
                        "agent_used": "personalized_greeting",
                        "status": "success",
                        "data": {
                            "user_info": user_info,
                            "store_info": store_info,
                            "product_count": product_count,
                            "recognized_user": True
                        }
                    }
                
                elif user_info:
                    # User exists but no store info
                    user_name = user_info.get('name', 'there')
                    return {
                        "message": f"👋 Hello {user_name}! I see you have a profile but no store setup yet. Let me help you set up your store information first. What type of business are you running?",
                        "agent_used": "user_setup_assistant",
                        "status": "success",
                        "data": {"user_info": user_info, "needs_store_setup": True}
                    }
                
                else:
                    # New user - need full setup
                    return {
                        "message": f"👋 Hello there! Welcome! I see you're a new user (ID: {user_id[:8]}...). To get started, could you please tell me your name and a little about your store? What type of business do you run, and what is its name?",
                        "agent_used": "new_user_onboarding",
                        "status": "success", 
                        "data": {"new_user": True, "user_id": user_id}
                    }
            
            # Not a greeting - show general help
            help_message = """
🤖 **Store Assistant - How I Can Help:**

📸 **Product Management:**
• Upload product images → I'll register them automatically
• "Add product with photo" → Product registration
• "Scan this item" → Image analysis

💰 **Transactions:**
• "Sold 2 apples at $1.50 each" → Process sales
• "Customer bought bread and milk" → Create receipts
• "Transaction for John" → Named customer sales

💵 **Cash Management:**
• "Petty cash $20 for office supplies" → Record expenses
• "Owner drawing $100" → Personal withdrawals  
• "Deposit $500 cash" → Add money to register

📊 **Inventory & Reports:**
• "Check low stock" → See items to reorder
• "Store analytics" → Business insights
• "How many products do I have?" → Inventory overview
• "Store information" → Business details

Just type naturally - I'll understand what you need! 😊
"""
            
            return {
                "message": help_message,
                "agent_used": "help_assistant",
                "status": "success",
                "data": {"available_features": ["product_registration", "transactions", "cash_management", "inventory", "reports"]}
            }
            
        except Exception as e:
            logger.error(f"Error in handle_general_help: {str(e)}")
            return {
                "message": f"👋 Hello! I encountered an issue loading your profile: {str(e)}. How can I help you today?",
                "agent_used": "error_fallback",
                "status": "error"
            }
    
    async def handle_transaction_confirmation(self, message: str, user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle transaction confirmation or cancellation"""
        try:
            # Parse the confirmation command
            message_lower = message.lower().strip()
            
            # Extract transaction ID and action
            import re
            
            # Look for patterns like "confirm TXN_..." or "cancel TXN_..."
            confirm_match = re.match(r'^confirm\s+(txn_[a-zA-Z0-9_]+)', message_lower)
            cancel_match = re.match(r'^cancel\s+(txn_[a-zA-Z0-9_]+)', message_lower)
            
            if confirm_match:
                transaction_id = confirm_match.group(1)  # Keep original case
                action = "confirm"
            elif cancel_match:
                transaction_id = cancel_match.group(1)  # Keep original case
                action = "cancel"
            else:
                return {
                    "message": "❌ Invalid confirmation format. Please use 'confirm TXN_...' or 'cancel TXN_...'",
                    "agent_used": "transaction_confirmation",
                    "status": "error"
                }
            
            logger.info(f"Processing {action} for transaction {transaction_id} by user {user_id}")
            
            # Use the product transaction helper to confirm/cancel
            from agents.product_transaction_agent.helpers import ProductTransactionHelper
            helper = ProductTransactionHelper()
            
            # For store_id, use user_id as default (common pattern in the system)
            store_id = user_id
            
            result = await helper.confirm_transaction(
                transaction_id=transaction_id,
                user_id=user_id,
                store_id=store_id,
                action=action
            )
            
            if result.get("success"):
                # Format the response using the helper's formatter
                response_message = helper.format_confirmation_response(result)
                
                return {
                    "message": response_message,
                    "agent_used": "transaction_confirmation",
                    "status": "success",
                    "data": {
                        "transaction_id": transaction_id,
                        "action": action,
                        "receipt": result.get("receipt")
                    }
                }
            else:
                error_msg = result.get("error", "Unknown error during confirmation")
                logger.error(f"Confirmation failed for {transaction_id}: {error_msg}")
                
                return {
                    "message": f"❌ Failed to {action} transaction: {error_msg}",
                    "agent_used": "transaction_confirmation",
                    "status": "error",
                    "data": {
                        "transaction_id": transaction_id,
                        "action": action,
                        "error": error_msg
                    }
                }
                
        except Exception as e:
            logger.error(f"Error in transaction confirmation: {e}")
            return {
                "message": "I apologize, but I'm still encountering an error when trying to confirm the transaction. There may be a problem with the system. Please try again later, or contact support for assistance.",
                "agent_used": "transaction_confirmation",
                "status": "error"
            }

    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """
        Main chat processing function
        """
        try:
            # Ensure user_id is available - check direct field first, then context
            user_id = request.user_id or request.context.get('user_id')
            if not user_id:
                return ChatResponse(
                    message="❌ User ID is required for processing.",
                    agent_used="error_handler",
                    status="error",
                    session_id=request.session_id
                )
            
            logger.info(f"Processing message: '{request.message}' | User: {user_id}")
            
            # Prepare context
            context = dict(request.context)
            if request.image_data:
                context['image_data'] = request.image_data
                context['is_url'] = request.is_url
            # Pass session_id in context
            if request.session_id:
                context['session_id'] = request.session_id
            
            # Route to appropriate agent using simplified routing
            result = await self.route_to_agent(request.message, user_id, context)
            
            # Check if result contains raw agent data and clean it
            if isinstance(result, dict) and 'raw_events' in result.get('data', {}):
                logger.warning(f"🔧 DETECTED RAW AGENT RESPONSE - CLEANING IT")
                # This is a raw agent response - extract and clean it
                raw_data = result.get('data', {})
                message_content = ""
                firebase_url = ""
                
                # Extract message from raw_events
                if 'raw_events' in raw_data and 'content' in raw_data['raw_events']:
                    content = raw_data['raw_events']['content']
                    if 'parts' in content and content['parts']:
                        message_content = content['parts'][0].get('text', '')
                        logger.info(f"📝 Extracted message content: {message_content[:100]}...")
                        
                        # Extract Firebase URL from message
                        import re
                        url_pattern = r'https://storage\.googleapis\.com/[^\s]+'
                        url_match = re.search(url_pattern, message_content)
                        if url_match:
                            firebase_url = url_match.group(0)
                            logger.info(f"🔗 Extracted Firebase URL: {firebase_url}")
                            # Remove URL from message
                            message_content = re.sub(url_pattern, '', message_content).strip()
                
                # Clean the message and create proper response
                if firebase_url:
                    filename = firebase_url.split('/')[-1] if firebase_url else ""
                    
                    # Create clean user message
                    clean_message = "📊 **Financial Report Generated Successfully!**\n\n"
                    clean_message += "📅 **Period:** Report Generated\n"
                    
                    if "broke even" in message_content.lower():
                        clean_message += "💵 **Status:** Break-even period\n"
                        clean_message += "💡 **Insight:** Your business balanced expenses and revenue.\n\n"
                    elif "profit" in message_content.lower():
                        clean_message += "💰 **Status:** Profitable period\n"
                        clean_message += "💡 **Insight:** Great job! Your business generated profit.\n\n"
                    
                    if filename:
                        clean_message += f"📄 **Report File:** {filename}\n"
                    
                    clean_message += "✅ Your PDF report has been generated and is ready for download!"
                    
                    logger.info(f"✅ CLEANED RESPONSE CREATED - URL moved to data field")
                    
                    # Return clean response with URL in data field
                    result = {
                        "message": clean_message,
                        "agent_used": "financial_reporting",
                        "status": "success",
                        "data": {
                            "filename": filename,
                            "firebase_url": firebase_url,
                            "download_url": firebase_url,
                            "storage_type": "firebase",
                            "report_type": "financial"
                        }
                    }
            
            # Clean up response data - remove any technical fields recursively
            clean_data = result.get("data", {})
            
            # Function to recursively clean technical fields
            def clean_technical_fields(data):
                if isinstance(data, dict):
                    # Remove technical fields at this level
                    technical_fields = ['raw_events', 'usage_metadata', 'invocation_id', 'author', 'actions', 'partial', 'content', 'processing_method']
                    for field in technical_fields:
                        data.pop(field, None)
                    
                    # Recursively clean nested dictionaries
                    for key, value in data.items():
                        if isinstance(value, dict):
                            clean_technical_fields(value)
                        elif isinstance(value, list):
                            for item in value:
                                if isinstance(item, dict):
                                    clean_technical_fields(item)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            clean_technical_fields(item)
            
            # Apply recursive cleaning
            clean_technical_fields(clean_data)
            
            # Log the agent used and cleaned data for debugging
            logger.info(f"Agent used: {result.get('agent_used', 'unknown')}")
            logger.info(f"Cleaned data keys: {list(clean_data.keys()) if clean_data else 'empty'}")
            
            return ChatResponse(
                message=result["message"],
                agent_used=result["agent_used"],
                status=result["status"],
                data=clean_data,
                session_id=request.session_id
            )
            
        except Exception as e:
            logger.error(f"Error in chat processing: {e}")
            return ChatResponse(
                message=f"😔 Sorry, I encountered an error: {str(e)}",
                agent_used="error_handler",
                status="error",
                session_id=request.session_id
            )

# Create FastAPI app
app = FastAPI(title="Store Assistant", description="Unified chat interface for store management")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize coordinator
coordinator = UnifiedChatCoordinator()

@app.post("/run", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest = Body(...)):
    """
    Unified chat endpoint that handles all store management interactions
    """
    # Extract user_id from request or context
    user_id = request.user_id or request.context.get("user_id")
    
    if not user_id:
        return ChatResponse(
            message="❌ User ID is required. Please provide user_id in the request or context.",
            agent_used="error_handler",
            status="error",
            session_id=request.session_id
        )
    
    # Create a new request with the extracted user_id
    updated_request = ChatRequest(
        message=request.message,
        user_id=user_id,
        session_id=request.session_id,
        context=request.context,
        image_data=request.image_data,
        is_url=request.is_url
    )
    
    return await coordinator.process_chat(updated_request)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Store Assistant"}

@app.get("/download/{filename}")
async def download_file(filename: str):
    """Redirect to Firebase Storage for downloads (legacy endpoint for backward compatibility)"""
    try:
        from fastapi.responses import JSONResponse, RedirectResponse
        
        # Extract components from filename to help identify the report
        import re
        
        # Check if this is a financial report 
        is_financial = bool(re.search(r'(Business|Financial|Sales)', filename, re.IGNORECASE))
        report_type = "financial" if is_financial else "unknown"
        
        # Return a clear message about using Firebase URLs instead
        return JSONResponse({
            "error": "Local file access deprecated",
            "message": "Reports are now stored in Firebase Storage for secure access.",
            "help": "Please use the firebase_url from the report generation response.",
            "action_required": "Update your frontend to use the firebase_url for accessing reports.",
            "report_type": report_type,
            "storage_location": "firebase"
        }, status_code=410)  # 410 Gone - resource no longer available
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/{user_id}/{report_type}/{filename}")
async def serve_report_file(user_id: str, report_type: str, filename: str):
    """Serve report files from local storage when Firebase Storage is unavailable"""
    try:
        import os
        from fastapi.responses import FileResponse
        
        # Construct the local file path
        reports_dir = os.path.join(os.getcwd(), "reports", user_id, report_type)
        file_path = os.path.join(reports_dir, filename)
        
        # Security check: ensure the file path is within the reports directory
        abs_reports_dir = os.path.abspath(reports_dir)
        abs_file_path = os.path.abspath(file_path)
        
        if not abs_file_path.startswith(abs_reports_dir):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Report file not found")
        
        # Determine content type
        content_type = "application/pdf" if filename.endswith('.pdf') else "application/octet-stream"
        
        # Return the file
        return FileResponse(
            path=file_path,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET",
                "Access-Control-Allow-Headers": "*"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving report file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents")
async def list_agents():
    """List available sub-agents and their capabilities"""
    return {
        "agents": {
            "product_registration": "Register products via image upload",
            "transaction_processor": "Process sales and create receipts", 
            "misc_transactions": "Handle petty cash, drawings, deposits",
            "inventory_manager": "Check stock levels and analytics",
            "store_manager": "Store information and business details",
            "help_assistant": "General help and feature overview"
        },
        "example_requests": [
            "Register this product [with image]",
            "Sold 2 apples at $1.50 each",
            "Petty cash $25 for office supplies", 
            "Check low stock items",
            "Store analytics",
            "Help - what can you do?"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
