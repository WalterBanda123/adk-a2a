"""
Pydantic models for Product Transaction Agent
Handles image-based product registration and chat-based transactions
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# =====================
# Product Registration Models
# =====================

class ProductRegistrationRequest(BaseModel):
    """Request model for product registration via image"""
    image_data: str = Field(..., description="Base64 encoded image or image URL")
    user_id: str = Field(..., description="User ID of the store owner")
    is_url: bool = Field(default=False, description="Whether image_data is a URL or base64")
    enhance_image: Optional[bool] = Field(default=True, description="Whether to enhance/annotate the image")

class ProductRegistrationResponse(BaseModel):
    """Response model for product registration"""
    success: bool
    message: str
    product: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    image_url: Optional[str] = None
    sku: Optional[str] = None
    processing_time: Optional[float] = None
    detection_method: Optional[str] = None

# =====================
# Transaction Models
# =====================

class Customer(BaseModel):
    """Customer information for transactions"""
    name: Optional[str] = Field(None, description="Customer name")
    email: Optional[str] = Field(None, description="Customer email")
    phone: Optional[str] = Field(None, description="Customer phone number")

class CartItem(BaseModel):
    """Cart item matching frontend interface"""
    id: str = Field(..., description="Item ID")
    name: str = Field(..., description="Product name")
    quantity: int = Field(..., description="Quantity purchased")
    unitPrice: float = Field(..., description="Unit price", alias="unit_price")
    totalPrice: float = Field(..., description="Total price for this item", alias="line_total")
    barcode: Optional[str] = Field(None, description="Product barcode/SKU")
    category: Optional[str] = Field(None, description="Product category")

class LineItem(BaseModel):
    """Individual line item in a transaction (legacy format)"""
    name: str = Field(..., description="Product name")
    quantity: int = Field(..., description="Quantity purchased")
    unit_price: float = Field(..., description="Unit price")
    line_total: float = Field(..., description="Total for this line (quantity * unit_price)")
    sku: Optional[str] = Field(None, description="Product SKU if found")
    category: Optional[str] = Field(None, description="Product category")

class TransactionRequest(BaseModel):
    """Request model for chat-based transactions"""
    message: str = Field(..., description="Free-form transaction message (e.g., '2 maputi @0.5, 1 soap @1.2')")
    user_id: str = Field(..., description="User ID of the store owner")
    customer_name: Optional[str] = Field(None, description="Customer name if provided")
    payment_method: Optional[str] = Field(default="cash", description="Payment method")

class Receipt(BaseModel):
    """Transaction receipt model"""
    transaction_id: str
    user_id: str
    store_id: str = Field(..., description="Store ID for filtering receipts")
    customer_name: Optional[str] = None
    date: str
    time: str
    items: List[LineItem]
    subtotal: float
    tax_rate: float = Field(default=0.05, description="Tax rate (5%)")
    tax_amount: float
    total: float
    payment_method: str = Field(default="cash")
    change_due: Optional[float] = None
    created_at: datetime
    status: str = Field(default="pending", description="Receipt status: pending, confirmed, cancelled")

class TransactionReceiptInterface(BaseModel):
    """Frontend-compatible transaction receipt interface"""
    id: str = Field(..., description="Transaction ID")
    amount: float = Field(..., description="Total amount")
    description: str = Field(..., description="Transaction description")
    merchant: str = Field(default="Store", description="Merchant/store name")
    date: str = Field(..., description="Transaction date")
    time: str = Field(..., description="Transaction time")
    status: str = Field(default="completed", description="Transaction status: completed, pending, failed")
    category: str = Field(default="General", description="Transaction category")
    cartItems: List[CartItem] = Field(..., description="List of cart items")
    customer: Optional[Customer] = Field(None, description="Customer information (null for anonymous)")
    paymentMethod: str = Field(default="cash", description="Payment method")
    cashierName: str = Field(default="System", description="Cashier name")
    receiptNumber: str = Field(..., description="Receipt number")
    subtotal: float = Field(..., description="Subtotal before tax")
    tax: float = Field(..., description="Tax amount")
    discount: Optional[float] = Field(None, description="Discount amount")
    cartImage: Optional[str] = Field(None, description="Image of the cart/items scanned")
    store_id: str = Field(..., description="Store ID for filtering receipts by store")

    class Config:
        populate_by_name = True

class TransactionResponse(BaseModel):
    """Response model for transactions"""
    success: bool
    message: str
    receipt: Optional[Receipt] = None
    frontend_receipt: Optional[TransactionReceiptInterface] = None  # Frontend-compatible format
    chat_response: Optional[str] = None
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    confirmation_required: bool = Field(default=False, description="Whether confirmation is required before saving")
    pending_transaction_id: Optional[str] = Field(None, description="ID of pending transaction awaiting confirmation")

class ConfirmationRequest(BaseModel):
    """Request model for transaction confirmation"""
    transaction_id: str = Field(..., description="Transaction ID to confirm")
    user_id: str = Field(..., description="User ID")
    action: str = Field(..., description="Action: 'confirm' or 'cancel'")
    store_id: str = Field(..., description="Store ID")

# =====================
# Helper Models
# =====================

class ProductMetadata(BaseModel):
    """Product metadata from Firestore"""
    sku: str
    name: str
    category: str
    subcategory: Optional[str] = None
    size: Optional[str] = None
    unit: Optional[str] = None
    description: Optional[str] = None
    unit_price: float
    stock_quantity: int
    brand: Optional[str] = None

class ParsedTransaction(BaseModel):
    """Parsed transaction from free-form text"""
    items: List[Dict[str, Any]]
    total_items: int
    estimated_total: float
    parsing_confidence: float
    raw_text: str
