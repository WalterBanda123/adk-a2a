"""
Product Transaction Tool for the coordinator sub-agent system
Integrates the standalone Product Transaction Agent capabilities into the sub-agent pattern
"""
import os
import sys
import re
import logging
from typing import Dict, Any, Optional
from google.adk.tools import FunctionTool

# Add project root to Python path  
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

# Import the helper class from the standalone agent
try:
    from agents.product_transaction_agent.helpers import ProductTransactionHelper
    from agents.product_transaction_agent.models import (
        ProductRegistrationRequest, TransactionRequest
    )
except ImportError as e:
    logging.warning(f"Could not import product transaction components: {e}")
    ProductTransactionHelper = None

logger = logging.getLogger(__name__)

def create_product_transaction_tool():
    """Create the product transaction tool for the sub-agent"""
    
    async def process_product_transaction(
        operation_type: str = "auto_detect",
        user_id: str = "default_user",
        store_id: Optional[str] = None,
        image_data: Optional[str] = None,
        is_url: bool = False,
        enhance_image: bool = True,
        transaction_text: Optional[str] = None,
        message: Optional[str] = None,
        transaction_id: Optional[str] = None,
        action: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process product transactions including image registration, text-based sales, and confirmations
        
        Args:
            operation_type: "register_image", "process_transaction", "confirm_transaction", or "auto_detect"
            user_id: User identifier
            store_id: Store identifier (default: store_{user_id})
            image_data: Base64 encoded image or URL (for image registration)
            is_url: Whether image_data is a URL or base64 string
            enhance_image: Whether to upload image to GCS
            transaction_text: Natural language transaction text (for transactions)
            message: Raw message from user (used for auto-detection)
            transaction_id: Transaction ID (for confirmations)
            action: Action for confirmations ("confirm" or "cancel")
            **kwargs: Additional parameters
            
        Returns:
            Dict containing the operation result
        """
        try:
            if not ProductTransactionHelper:
                return {
                    "success": False,
                    "error": "Product transaction functionality not available",
                    "message": "The product transaction system is not properly configured."
                }
            
            helper = ProductTransactionHelper()
            
            # Default store_id if not provided
            if not store_id:
                store_id = f"store_{user_id}"
            
            # Auto-detect operation type if not specified
            if operation_type == "auto_detect":
                operation_type = _detect_operation_type(message, image_data, transaction_text, transaction_id, action)
            
            # Use message as transaction_text if not provided
            if not transaction_text and message:
                transaction_text = message
            
            logger.info(f"Processing operation: {operation_type} for user: {user_id}")
            
            if operation_type == "register_image":
                return await _handle_image_registration(
                    helper, user_id, image_data, is_url, enhance_image
                )
            elif operation_type == "process_transaction":
                return await _handle_transaction_processing(
                    helper, user_id, store_id, transaction_text
                )
            elif operation_type == "confirm_transaction":
                return await _handle_transaction_confirmation(
                    helper, user_id, store_id, transaction_id, action
                )
            elif operation_type == "price_inquiry":
                return await _handle_price_inquiry(
                    helper, user_id, message or transaction_text
                )
            else:
                return {
                    "success": False,
                    "error": f"Unknown operation type: {operation_type}",
                    "message": f"Supported operations: 'register_image', 'process_transaction', 'confirm_transaction', 'price_inquiry'. Got: {operation_type}"
                }
                
        except Exception as e:
            logger.error(f"Error in product transaction tool: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "An error occurred while processing your request."
            }
    
    def _detect_operation_type(message: Optional[str], image_data: Optional[str], transaction_text: Optional[str], transaction_id: Optional[str] = None, action: Optional[str] = None) -> str:
        """Auto-detect the operation type based on input"""
        if image_data:
            return "register_image"
        
        # Check for confirmation operations
        if transaction_id and action:
            return "confirm_transaction"
            
        if message:
            message_lower = message.lower()
            
            # Check for confirmation keywords
            if any(keyword in message_lower for keyword in ["confirm", "cancel"]) and "txn_" in message_lower:
                return "confirm_transaction"
            
            # Check for price inquiries
            price_keywords = ["what's the price", "price of", "how much", "cost of", "price for"]
            if any(keyword in message_lower for keyword in price_keywords):
                return "price_inquiry"
            
            # Transaction indicators
            transaction_keywords = [
                "sold", "sell", "sale", "bought", "buy", "customer", "transaction",
                "receipt", "total", "@", "at $", "for $", "each", "x ", " x"
            ]
            
            # Simple quantity + item patterns (new intelligent format)
            quantity_patterns = [
                r'\d+\s+\w+',      # "2 bread"
                r'\d+\s*x\s*\w+',  # "2x bread"
            ]
            
            # Image registration indicators  
            image_keywords = [
                "register", "scan", "image", "photo", "picture", "extract",
                "identify", "automl", "sku"
            ]
            
            # Check for simple quantity patterns first (new intelligent mode)
            if any(re.search(pattern, message_lower) for pattern in quantity_patterns):
                return "process_transaction"
            elif any(keyword in message_lower for keyword in transaction_keywords):
                return "process_transaction"
            elif any(keyword in message_lower for keyword in image_keywords):
                return "register_image"
        
        # Default to transaction processing if we have text
        if transaction_text or message:
            return "process_transaction"
        
        return "register_image"
    
    async def _handle_image_registration(
        helper,
        user_id: str,
        image_data: Optional[str],
        is_url: bool,
        enhance_image: bool
    ) -> Dict[str, Any]:
        """Handle product image registration"""
        if not image_data:
            return {
                "success": False,
                "error": "Missing image data",
                "message": "Please provide image data for product registration."
            }
        
        try:
            # Preprocess image
            image_bytes = await helper.preprocess_image(image_data, is_url)
            if not image_bytes:
                return {
                    "success": False,
                    "error": "Invalid image data",
                    "message": "Could not process the provided image. Please check the format."
                }
            
            # Call AutoML model
            prediction_result = await helper.call_automl_model(image_bytes, user_id)
            
            if not prediction_result.get("success"):
                return {
                    "success": False,
                    "error": "Image analysis failed",
                    "message": "Could not analyze the product image.",
                    "details": prediction_result
                }
            
            # Look up product metadata if SKU found
            product_metadata = None
            if prediction_result.get("sku"):
                product_metadata = await helper.lookup_product_by_sku(
                    prediction_result["sku"], user_id
                )
            
            # Upload to GCS if requested
            image_url = None
            if enhance_image:
                image_url = await helper.upload_to_gcs(image_bytes, user_id)
            
            # Build comprehensive response
            return {
                "success": True,
                "message": f"Successfully analyzed product image! Detected: {prediction_result.get('title', 'Unknown Product')}",
                "product_data": {
                    "title": prediction_result.get("title", "Unknown Product"),
                    "brand": prediction_result.get("brand", ""),
                    "category": prediction_result.get("category", "General"),
                    "size": prediction_result.get("size", ""),
                    "unit": prediction_result.get("unit", ""),
                    "confidence": prediction_result.get("confidence", 0.0),
                    "sku": prediction_result.get("sku"),
                    "detection_method": prediction_result.get("detection_method", "automl")
                },
                "metadata": product_metadata,
                "image_url": image_url,
                "processing_info": {
                    "user_id": user_id,
                    "enhanced": enhance_image,
                    "confidence": prediction_result.get("confidence", 0.0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in image registration: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to register product from image."
            }
    
    async def _handle_transaction_processing(
        helper,
        user_id: str,
        store_id: str,
        transaction_text: Optional[str]
    ) -> Dict[str, Any]:
        """Handle natural language transaction processing with confirmation flow"""
        if not transaction_text:
            return {
                "success": False,
                "error": "Missing transaction text",
                "message": "Please provide transaction details to process."
            }
        
        try:
            # Parse transaction text using the cart message parser
            parsed_result = await helper.parse_cart_message(transaction_text)
            
            if not parsed_result.get("success"):
                return {
                    "success": False,
                    "error": "Transaction parsing failed",
                    "message": f"Could not parse transaction: {parsed_result.get('error', 'Unknown error')}",
                    "details": parsed_result
                }
            
            # Compute receipt with stock validation (include store_id)
            receipt_result = await helper.compute_receipt(
                parsed_result["items"], user_id, store_id
            )
            
            if not receipt_result.get("success"):
                return {
                    "success": False,
                    "error": "Receipt computation failed",
                    "message": f"Could not process transaction: {', '.join(receipt_result.get('errors', ['Unknown error']))}",
                    "details": receipt_result
                }
            
            # Save as pending transaction (awaiting confirmation)
            pending_success = await helper.save_pending_transaction(receipt_result["receipt"])
            
            if not pending_success:
                return {
                    "success": False,
                    "error": "Could not save pending transaction",
                    "message": "Transaction processing failed."
                }
            
            # Generate frontend-compatible receipt
            try:
                frontend_receipt = helper.convert_to_frontend_receipt(
                    receipt_result["receipt"], None  # Pass None for user_profile
                )
            except Exception as e:
                logger.error(f"Error converting to frontend receipt: {e}")
                frontend_receipt = {}
            
            # Format confirmation request
            confirmation_message = helper.format_confirmation_request(receipt_result["receipt"])
            
            return {
                "success": True,
                "message": confirmation_message,
                "transaction_data": {
                    "transaction_id": receipt_result["receipt"]["transaction_id"],
                    "items": receipt_result["receipt"]["items"],
                    "totals": {
                        "subtotal": receipt_result["receipt"]["subtotal"],
                        "tax": receipt_result["receipt"]["tax_amount"],
                        "total": receipt_result["receipt"]["total"]
                    },
                    "receipt": receipt_result["receipt"],
                    "frontend_receipt": frontend_receipt,  # Frontend-compatible format
                    "errors": receipt_result.get("errors", []),
                    "warnings": receipt_result.get("warnings", [])
                },
                "confirmation_required": True,
                "pending_transaction_id": receipt_result["receipt"]["transaction_id"],
                "chat_response": {
                    "confirmation_request": confirmation_message,
                    "summary": f"Transaction ready for confirmation - {len(receipt_result['receipt']['items'])} items",
                    "total_amount": receipt_result['receipt']['total'],
                    "tax_amount": receipt_result['receipt']['tax_amount'],
                    "items_pending": [f"{item['quantity']}x {item['name']}" for item in receipt_result['receipt']['items']]
                }
            }
            
        except Exception as e:
            logger.error(f"Error in transaction processing: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process transaction."
            }
    
    async def _handle_transaction_confirmation(
        helper,
        user_id: str,
        store_id: str,
        transaction_id: Optional[str],
        action: Optional[str]
    ) -> Dict[str, Any]:
        """Handle transaction confirmation or cancellation"""
        if not transaction_id or not action:
            return {
                "success": False,
                "error": "Missing transaction ID or action",
                "message": "Please provide transaction ID and action (confirm/cancel)."
            }
        
        try:
            # Handle confirmation
            confirmation_result = await helper.confirm_transaction(
                transaction_id, user_id, store_id, action
            )
            
            if not confirmation_result.get("success"):
                return {
                    "success": False,
                    "error": confirmation_result.get("error", "Confirmation failed"),
                    "message": f"Could not {action} transaction: {confirmation_result.get('error', 'Unknown error')}"
                }
            
            # Format response message
            response_message = helper.format_confirmation_response(confirmation_result)
            
            # Generate frontend receipt if confirmed
            frontend_receipt = None
            if action.lower() == "confirm" and confirmation_result.get("receipt"):
                try:
                    frontend_receipt = helper.convert_to_frontend_receipt(
                        confirmation_result["receipt"], None
                    )
                except Exception as e:
                    logger.error(f"Error converting to frontend receipt: {e}")
                    frontend_receipt = {}
            
            return {
                "success": True,
                "message": response_message,
                "confirmation_data": {
                    "transaction_id": transaction_id,
                    "action": action,
                    "status": confirmation_result.get("action", action),
                    "receipt": confirmation_result.get("receipt"),
                    "frontend_receipt": frontend_receipt
                },
                "chat_response": {
                    "confirmation_result": response_message,
                    "action_taken": confirmation_result.get("action", action),
                    "transaction_id": transaction_id
                }
            }
            
        except Exception as e:
            logger.error(f"Error in transaction confirmation: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to {action} transaction."
            }
    
    async def _handle_price_inquiry(
        helper,
        user_id: str,
        query: Optional[str]
    ) -> Dict[str, Any]:
        """Handle price inquiry requests"""
        if not query:
            return {
                "success": False,
                "error": "Missing query",
                "message": "Please specify which product you'd like to know the price of."
            }
        
        try:
            # Handle price inquiry
            inquiry_result = await helper.handle_price_inquiry(query, user_id)
            
            if inquiry_result.get("success"):
                return {
                    "success": True,
                    "message": inquiry_result.get("message", "Price inquiry processed"),
                    "price_data": {
                        "product_name": inquiry_result.get("product_name"),
                        "price": inquiry_result.get("price"),
                        "stock": inquiry_result.get("stock"),
                        "sku": inquiry_result.get("sku"),
                        "category": inquiry_result.get("category")
                    },
                    "chat_response": {
                        "price_info": inquiry_result.get("message"),
                        "product_found": True
                    }
                }
            else:
                return {
                    "success": False,
                    "message": inquiry_result.get("message", "Product not found"),
                    "error": inquiry_result.get("error"),
                    "chat_response": {
                        "price_info": inquiry_result.get("message"),
                        "product_found": False
                    }
                }
                
        except Exception as e:
            logger.error(f"Error in price inquiry: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process price inquiry."
            }

    # Create the tool
    return FunctionTool(func=process_product_transaction)
