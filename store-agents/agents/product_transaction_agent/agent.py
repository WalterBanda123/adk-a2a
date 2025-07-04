"""
Product Transaction Agent
FastAPI subagent for image-based product registration and chat-based transactions
"""
import os
import sys
import logging
import time
from typing import Dict, Any, Optional

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import JSONResponse

# Import models and helpers
try:
    from .models import (
        ProductRegistrationRequest, ProductRegistrationResponse,
        TransactionRequest, TransactionResponse, Receipt, LineItem
    )
    from .helpers import ProductTransactionHelper
except ImportError:
    # Running directly - use absolute imports
    from models import (
        ProductRegistrationRequest, ProductRegistrationResponse,
        TransactionRequest, TransactionResponse, Receipt, LineItem
    )
    from helpers import ProductTransactionHelper

# Import common server utilities
from common.server import create_agent_server

logger = logging.getLogger(__name__)

class ProductTransactionAgent:
    """Agent for handling product registration and transactions"""
    
    def __init__(self):
        self.name = "Product Transaction Agent"
        self.description = "Handles image-based product registration and chat-based transactions"
        self.helper = ProductTransactionHelper()
    
    async def register_product_image(self, request: ProductRegistrationRequest) -> ProductRegistrationResponse:
        """
        Register a product via image using AutoML Vision
        
        Process:
        1. Preprocess image
        2. Call AutoML model for prediction
        3. Look up product metadata by predicted SKU
        4. Upload image to GCS
        5. Return structured response
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing product registration for user: {request.user_id}")
            
            # Step 1: Preprocess image
            image_bytes = await self.helper.preprocess_image(request.image_data, request.is_url)
            if not image_bytes:
                raise HTTPException(status_code=400, detail="Invalid image data")
            
            # Step 2: Call AutoML model
            prediction_result = await self.helper.call_automl_model(image_bytes, request.user_id)
            
            if not prediction_result.get("success"):
                raise HTTPException(status_code=500, detail="Failed to analyze image")
            
            # Step 3: Look up product metadata
            product_metadata = None
            if prediction_result.get("sku"):
                product_metadata = await self.helper.lookup_product_by_sku(
                    prediction_result["sku"], 
                    request.user_id
                )
            
            # Step 4: Upload image to GCS (if requested)
            image_url = None
            if request.enhance_image:
                image_url = await self.helper.upload_to_gcs(
                    image_bytes, 
                    request.user_id
                )
            
            # Step 5: Build response
            processing_time = time.time() - start_time
            
            product_data = {
                "title": prediction_result.get("title", "Unknown Product"),
                "brand": prediction_result.get("brand", ""),
                "category": prediction_result.get("category", "General"),
                "subcategory": "",
                "size": prediction_result.get("size", ""),
                "unit": prediction_result.get("unit", ""),
                "description": ""
            }
            
            # Add product metadata if found
            if product_metadata:
                product_data.update(product_metadata)
            
            response = ProductRegistrationResponse(
                success=True,
                message=f"Product registered successfully: {product_data['title']}",
                product=product_data,
                confidence=prediction_result.get("confidence", 0.0),
                image_url=image_url,
                sku=prediction_result.get("sku"),
                processing_time=processing_time,
                detection_method=prediction_result.get("detection_method", "automl")
            )
            
            logger.info(f"Product registration completed in {processing_time:.2f}s")
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in product registration: {e}")
            processing_time = time.time() - start_time
            
            return ProductRegistrationResponse(
                success=False,
                message=f"Product registration failed: {str(e)}",
                processing_time=processing_time
            )
    
    async def process_chat_transaction(self, request: TransactionRequest) -> TransactionResponse:
        """
        Process a chat-based transaction or stock inquiry
        
        Process:
        1. Check if message is a stock inquiry
        2. If stock inquiry: return inventory information  
        3. If transaction: Parse free-form transaction text
        4. Look up products and validate stock
        5. Compute receipt with tax
        6. Update stock levels
        7. Persist transaction
        8. Return formatted response
        """
        try:
            logger.info(f"Processing message for user: {request.user_id}")
            logger.info(f"Message: {request.message}")
            
            # Step 1: Check if this is a stock inquiry
            if self.helper.is_stock_inquiry(request.message):
                logger.info("Detected stock inquiry")
                stock_result = await self.helper.handle_stock_inquiry(request.message, request.user_id)
                
                return TransactionResponse(
                    success=stock_result.get("success", True),
                    message=stock_result.get("message", "Stock information retrieved"),
                    receipt=None,
                    frontend_receipt=None,
                    chat_response=stock_result.get("message", "Stock information retrieved"),
                    errors=None if stock_result.get("success") else [stock_result.get("message", "Error retrieving stock")],
                    warnings=None,
                    confirmation_required=False,
                    pending_transaction_id=None
                )
            
            # Step 2: Process as regular transaction
            # Parse transaction message
            parsed_result = await self.helper.parse_cart_message(request.message)
            
            logger.info(f"Parsed result: {parsed_result.get('success')}, items: {len(parsed_result.get('items', []))}, confidence: {parsed_result.get('parsing_confidence', 0)}")
            
            if not parsed_result.get("success"):
                # Parsing failed - provide helpful error message
                error_msg = parsed_result.get("error", "Could not understand your message")
                suggestions = parsed_result.get("suggestions", [])
                
                return TransactionResponse(
                    success=False,
                    message=f"I couldn't understand what you want to buy/sell. {error_msg}",
                    errors=[error_msg],
                    pending_transaction_id=None,
                    chat_response=f"""I'm having trouble understanding your transaction. Here are some ways you can tell me about your sales:

**Examples that work well:**
• `2 bread, 1 milk` (I'll look up prices)
• `2 bread @1.50, 1 milk @0.75` (with your prices)
• `sold 3 apples` (simple format)

**Your message:** "{request.message}"

**Suggestions:**
{chr(10).join(f'• {suggestion}' for suggestion in suggestions)}

Please try again with a clearer format!"""
                )
            
            items = parsed_result.get("items", [])
            if not items:
                # No items found - provide specific guidance
                available_products = await self.helper._get_available_products(request.user_id, limit=5)
                
                return TransactionResponse(
                    success=False,
                    message="No products found in your message",
                    errors=["No products could be identified in your message"],
                    pending_transaction_id=None,
                    chat_response=f"""I couldn't find any products in your message: "{request.message}"

**Available products in your store:**
{chr(10).join(f'• {product}' for product in available_products)}

**Try these formats:**
• `2 bread, 1 milk` 
• `sold 3 apples by 2.50` 
• `1 cooking oil @4.75`

What would you like to record?"""
                )
            
            # Step 2: Compute receipt and validate
            receipt_result = await self.helper.compute_receipt(
                items, 
                request.user_id,
                request.customer_name or "Walk-in Customer"
            )
            
            errors = receipt_result.get("errors", [])
            warnings = receipt_result.get("warnings", [])
            
            if not receipt_result.get("success"):
                # Receipt computation failed - provide detailed feedback
                suggestions = receipt_result.get("suggestions", [])
                
                return TransactionResponse(
                    success=False,
                    message="Transaction could not be completed",
                    errors=errors,
                    warnings=warnings,
                    pending_transaction_id=None,
                    chat_response=f"""I found some issues with your transaction:

**Problems:**
{chr(10).join(f'• {error}' for error in errors)}

**Suggestions:**
{chr(10).join(f'• {suggestion}' for suggestion in suggestions)}

Please check your product names and try again!"""
                )
            
            # Step 3: Save as pending transaction (requiring confirmation)
            receipt_data = receipt_result["receipt"]
            pending_saved = await self.helper.save_pending_transaction(receipt_data)
            
            if not pending_saved:
                raise HTTPException(status_code=500, detail="Failed to save pending transaction")
            
            # Step 4: Format confirmation request
            receipt_obj = Receipt(**receipt_data)
            confirmation_message = self.helper.format_confirmation_request(receipt_data)
            
            response = TransactionResponse(
                success=True,
                message="Transaction registered and awaiting confirmation",
                receipt=receipt_obj,
                chat_response=confirmation_message,
                errors=errors if errors else None,
                warnings=warnings if warnings else None,
                pending_transaction_id=receipt_data['transaction_id'],
                confirmation_required=True
            )
            
            logger.info(f"Transaction {receipt_data['transaction_id']} registered and awaiting confirmation")
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing transaction: {e}")
            return TransactionResponse(
                success=False,
                message=f"Transaction processing failed: {str(e)}",
                errors=[str(e)],
                pending_transaction_id=None
            )


def create_product_transaction_server() -> FastAPI:
    """Create FastAPI server for Product Transaction Agent"""
    
    agent = ProductTransactionAgent()
    
    # Create custom endpoints
    async def register_product_endpoint(request: ProductRegistrationRequest = Body(...)):
        """POST /register-product-image endpoint"""
        return await agent.register_product_image(request)
    
    async def chat_transaction_endpoint(request: TransactionRequest = Body(...)):
        """POST /chat/transaction endpoint"""
        return await agent.process_chat_transaction(request)
    
    # Define custom endpoints
    custom_endpoints = {
        "register-product-image": register_product_endpoint,
        "chat/transaction": chat_transaction_endpoint
    }
    
    # Create server using common infrastructure
    # Note: We need a simple task manager for the server
    class SimpleTaskManager:
        async def process_task(self, message: str, context: Dict[str, Any], session_id: Optional[str] = None):
            # This is a placeholder - the real endpoints will be used directly
            return {
                "message": "Use specific endpoints: /register-product-image or /chat/transaction",
                "status": "info"
            }
    
    task_manager = SimpleTaskManager()
    
    app = create_agent_server(
        name=agent.name,
        description=agent.description,
        task_manager=task_manager,
        endpoints=custom_endpoints
    )
    
    return app


# Create the FastAPI app
app = create_product_transaction_server()

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting Product Transaction Agent Server...")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
