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
        Process a chat-based transaction
        
        Process:
        1. Parse free-form transaction text
        2. Look up products and validate stock
        3. Compute receipt with tax
        4. Update stock levels
        5. Persist transaction
        6. Return formatted response
        """
        try:
            logger.info(f"Processing transaction for user: {request.user_id}")
            logger.info(f"Transaction message: {request.message}")
            
            # Step 1: Parse transaction message
            parsed_result = await self.helper.parse_cart_message(request.message)
            
            if not parsed_result.get("success") or not parsed_result.get("items"):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Could not parse transaction message: {request.message}"
                )
            
            # Step 2: Compute receipt and validate
            receipt_result = await self.helper.compute_receipt(
                parsed_result["items"], 
                request.user_id,
                request.customer_name or "Walk-in Customer"
            )
            
            errors = receipt_result.get("errors", [])
            warnings = receipt_result.get("warnings", [])
            
            if not receipt_result.get("success"):
                return TransactionResponse(
                    success=False,
                    message="Transaction validation failed",
                    errors=errors,
                    warnings=warnings
                )
            
            # Step 3: Persist transaction
            receipt_data = receipt_result["receipt"]
            persistence_success = await self.helper.persist_transaction(receipt_data)
            
            if not persistence_success:
                raise HTTPException(status_code=500, detail="Failed to save transaction")
            
            # Step 4: Format response
            receipt_obj = Receipt(**receipt_data)
            chat_response = self.helper.format_chat_response(receipt_data, errors, warnings)
            
            response = TransactionResponse(
                success=True,
                message="Transaction processed successfully",
                receipt=receipt_obj,
                chat_response=chat_response,
                errors=errors if errors else None,
                warnings=warnings if warnings else None
            )
            
            logger.info(f"Transaction {receipt_data['transaction_id']} completed successfully")
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing transaction: {e}")
            return TransactionResponse(
                success=False,
                message=f"Transaction processing failed: {str(e)}",
                errors=[str(e)]
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
