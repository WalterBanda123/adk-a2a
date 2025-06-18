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

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import sub-agents
from agents.product_transaction_agent.agent import ProductTransactionAgent
from agents.misc_transactions.agent import MiscTransactionsAgent

# Import common services
from common.user_service import UserService
from common.real_product_service import RealProductService

logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str = Field(..., description="User's chat message")
    user_id: str = Field(..., description="User identifier")
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
        
        # Initialize services
        self.user_service = UserService()
        self.product_service = RealProductService()
        
        # Intent patterns for routing
        self.intent_patterns = {
            'product_registration': [
                r'register.*product', r'add.*product.*image', r'scan.*product',
                r'new.*product.*photo', r'upload.*product', r'analyze.*image'
            ],
            'transaction': [
                r'sold.*', r'sale.*', r'customer.*bought', r'purchase.*',
                r'transaction.*', r'receipt.*', r'checkout.*', r'buy.*'
            ],
            'petty_cash': [
                r'petty.*cash', r'small.*expense', r'office.*supplies',
                r'withdraw.*cash', r'cash.*expense', r'minor.*expense'
            ],
            'owner_drawing': [
                r'owner.*drawing', r'personal.*withdrawal', r'take.*money',
                r'withdraw.*personal', r'drawing.*'
            ],
            'cash_deposit': [
                r'deposit.*cash', r'add.*money', r'put.*money', r'cash.*in'
            ],
            'inventory_query': [
                r'stock.*level', r'inventory.*', r'how.*many.*', r'product.*quantity',
                r'low.*stock', r'out.*of.*stock', r'check.*stock'
            ],
            'store_query': [
                r'store.*info', r'business.*details', r'sales.*summary',
                r'financial.*report', r'analytics.*'
            ],
            'general_help': [
                r'help.*', r'what.*can.*you.*do', r'commands.*', r'features.*'
            ]
        }
    
    def detect_intent(self, message: str, has_image: bool = False) -> str:
        """
        Detect user intent from message
        """
        message_lower = message.lower()
        
        # Image takes priority for product registration
        if has_image:
            return 'product_registration'
        
        # Check patterns
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent
        
        # Default to general help
        return 'general_help'
    
    async def route_to_agent(self, intent: str, message: str, user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route request to appropriate sub-agent
        """
        try:
            if intent == 'product_registration':
                return await self.handle_product_registration(message, user_id, context)
            
            elif intent == 'transaction':
                return await self.handle_transaction(message, user_id, context)
            
            elif intent in ['petty_cash', 'owner_drawing', 'cash_deposit']:
                return await self.handle_misc_transaction(intent, message, user_id, context)
            
            elif intent == 'inventory_query':
                return await self.handle_inventory_query(message, user_id, context)
            
            elif intent == 'store_query':
                return await self.handle_store_query(message, user_id, context)
            
            else:
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
            # Use product transaction agent for chat-based transactions
            from agents.product_transaction_agent.models import TransactionRequest
            
            request = TransactionRequest(
                message=message,
                user_id=user_id,
                store_id=context.get('store_id')
            )
            
            result = await self.product_agent.process_chat_transaction(request)
            
            return {
                "message": result.message,
                "agent_used": "transaction_processor",
                "status": "success" if result.success else "error",
                "data": {
                    "receipt": result.receipt.dict() if result.receipt else None,
                    "frontend_receipt": result.frontend_receipt.dict() if result.frontend_receipt else None,
                    "pending_transaction_id": result.pending_transaction_id,
                    "confirmation_required": result.confirmation_required
                }
            }
            
        except Exception as e:
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
                # General inventory query
                products = await self.product_service.get_store_products(user_id)
                if products:
                    count = len(products)
                    message = f"📦 You have {count} products in inventory. Use 'low stock' to see items that need restocking, or 'analytics' for detailed insights."
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
    
    async def handle_general_help(self, message: str, user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general help and unknown requests"""
        help_message = """
🤖 **Store Assistant - How I Can Help:**

📸 **Product Management:**
• Upload product images → I'll register them automatically
• "Add product with photo" → Product registration
• "Scan this item" → Image analysis

💰 **Transactions:**
• "Sold 2 apples at $1 each" → Process sales
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
    
    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """
        Main chat processing function
        """
        try:
            # Detect intent
            has_image = bool(request.image_data)
            intent = self.detect_intent(request.message, has_image)
            
            # Prepare context
            context = dict(request.context)
            if request.image_data:
                context['image_data'] = request.image_data
                context['is_url'] = request.is_url
            
            # Route to appropriate agent
            result = await self.route_to_agent(intent, request.message, request.user_id, context)
            
            return ChatResponse(
                message=result["message"],
                agent_used=result["agent_used"],
                status=result["status"],
                data=result.get("data", {}),
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
    return await coordinator.process_chat(request)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Store Assistant"}

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
    uvicorn.run(app, host="0.0.0.0", port=8000)
