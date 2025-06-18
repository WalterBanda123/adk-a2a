# Product Transaction Agent

A FastAPI subagent that handles:
1. **Image-Based Product Registration** via AutoML Vision
2. **Chat-Based Transaction Processing** with natural language parsing

## 🚀 Quick Start

### Start the Server
```bash
./start_product_transaction_agent.sh
```

The server will be available at: `http://localhost:8001`

### API Endpoints

#### 1. Product Registration: `POST /register-product-image`

Register a product by uploading an image. The system uses AutoML Vision to predict product details and optionally uploads the image to Google Cloud Storage.

**Request Body:**
```json
{
    "image_data": "base64_encoded_image_or_url",
    "user_id": "user123",
    "is_url": false,
    "enhance_image": true
}
```

**Response:**
```json
{
    "success": true,
    "message": "Product registered successfully: Hullets Brown Sugar",
    "product": {
        "title": "Hullets Brown Sugar",
        "brand": "Hullets",
        "category": "Staples",
        "size": "2kg",
        "unit_price": 3.50,
        "stock_quantity": 25
    },
    "confidence": 0.92,
    "image_url": "https://storage.googleapis.com/...",
    "sku": "HULBROW2K",
    "processing_time": 1.23,
    "detection_method": "automl"
}
```

#### 2. Chat Transaction: `POST /chat/transaction`

Process a transaction using natural language. Parse items, validate inventory, compute totals with tax, and update stock.

**Request Body:**
```json
{
    "message": "2 maputi @0.5, 1 soap @1.2, 3x bread @1.25",
    "user_id": "user123",
    "customer_name": "John Doe",
    "payment_method": "cash"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Transaction processed successfully",
    "receipt": {
        "transaction_id": "TXN_user123_1625098765",
        "user_id": "user123",
        "customer_name": "John Doe", 
        "date": "2025-06-11",
        "time": "10:30:15",
        "items": [
            {
                "name": "Maputi",
                "quantity": 2,
                "unit_price": 0.5,
                "line_total": 1.0,
                "sku": "MAP001",
                "category": "Snacks"
            }
        ],
        "subtotal": 6.95,
        "tax_rate": 0.05,
        "tax_amount": 0.35,
        "total": 7.30,
        "payment_method": "cash"
    },
    "chat_response": "🧾 **Transaction Complete!**\n\n**Receipt ID:** TXN_user123_1625098765...",
    "warnings": ["Price adjusted for soap: $1.20 → $1.15"]
}
```

## 📋 cURL Examples

### Product Registration
```bash
curl -X POST "http://localhost:8001/register-product-image" \
  -H "Content-Type: application/json" \
  -d '{
    "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...",
    "user_id": "user123",
    "is_url": false,
    "enhance_image": true
  }'
```

### Chat Transaction
```bash
curl -X POST "http://localhost:8001/chat/transaction" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "2 maputi @0.5, 1 soap @1.2, 3x bread @1.25",
    "user_id": "user123",
    "customer_name": "John Doe",
    "payment_method": "cash"
  }'
```

### Check Server Status
```bash
curl -X GET "http://localhost:8001/.well-known/agent.json"
```

## 🔧 Configuration

### Environment Variables
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to Firebase service account key
- `FIREBASE_PROJECT_ID`: Firebase project ID (default: "deve-01")

### Dependencies
- FastAPI
- Pydantic
- Google Cloud AutoML
- Google Cloud Vision
- Google Cloud Storage
- Firebase Admin SDK

## 🎯 Features

### Image Registration
- **AutoML Integration**: Uses trained AutoML Vision models for product recognition
- **Fallback Detection**: Falls back to Google Vision API if AutoML fails
- **SKU Generation**: Automatically generates SKUs from detected product info
- **GCS Upload**: Optionally uploads images to Google Cloud Storage
- **Metadata Lookup**: Fetches canonical product data from Firestore

### Transaction Processing
- **Natural Language Parsing**: Supports various input formats:
  - `"2 maputi @0.5"`
  - `"1 soap @ 1.2"`
  - `"3x bread @1.25"`
- **Inventory Validation**: Checks stock levels and product availability
- **Price Reconciliation**: Uses official prices from inventory when available
- **Tax Calculation**: Automatically adds 5% tax
- **Stock Updates**: Automatically deducts sold items from inventory
- **Receipt Generation**: Creates detailed receipts with transaction IDs

### Error Handling
- **Validation Errors**: Clear messages for invalid input
- **Stock Shortages**: Prevents overselling with detailed error messages
- **Fallback Processing**: Graceful degradation when services are unavailable
- **Detailed Logging**: Comprehensive logs for debugging and monitoring

## 🏗️ Architecture

```
Frontend Request
     ↓
FastAPI Router
     ↓
ProductTransactionAgent
     ↓
ProductTransactionHelper
     ↓
┌─────────────────┬─────────────────┐
│  Image Pipeline │ Transaction     │
│                 │ Pipeline        │
│ 1. Preprocess   │ 1. Parse Text   │
│ 2. AutoML       │ 2. Lookup Items │
│ 3. Fallback     │ 3. Validate     │
│ 4. Metadata     │ 4. Compute Tax  │
│ 5. Upload GCS   │ 5. Update Stock │
└─────────────────┴─────────────────┘
     ↓
Firebase/Firestore
     ↓
JSON Response
```

## 🧪 Testing

### Test Product Registration
```python
import requests
import base64

# Load test image
with open("test_product.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

response = requests.post("http://localhost:8001/register-product-image", json={
    "image_data": f"data:image/jpeg;base64,{image_data}",
    "user_id": "test_user",
    "is_url": False,
    "enhance_image": True
})

print(response.json())
```

### Test Transaction Processing
```python
import requests

response = requests.post("http://localhost:8001/chat/transaction", json={
    "message": "2 bread @1.25, 1 milk @2.50",
    "user_id": "test_user",
    "customer_name": "Test Customer"
})

print(response.json())
```

## 🚨 Error Codes

- **400**: Invalid request data (malformed JSON, missing fields)
- **404**: Product not found, invalid SKU
- **422**: Validation error (negative quantities, invalid prices)
- **500**: Internal server error (database issues, service failures)

## 📊 Monitoring

Check server health:
```bash
curl http://localhost:8001/.well-known/agent.json
```

View logs:
```bash
tail -f product_transaction_agent.log
```

## 🔒 Security

- Input validation on all endpoints
- Rate limiting (configure as needed)
- CORS enabled for frontend integration
- Firebase security rules apply to all data operations

## 💡 Usage Tips

1. **Image Quality**: Use clear, well-lit product images for best recognition accuracy
2. **Transaction Format**: Use consistent formatting for better parsing (e.g., "quantity product @price")
3. **Stock Management**: Regularly update inventory to ensure accurate stock validation
4. **Error Handling**: Always check the `success` field in responses before processing data
5. **Performance**: Image processing may take 1-3 seconds; implement appropriate loading states

## 🤝 Integration

This agent integrates seamlessly with:
- Existing Firebase/Firestore databases
- Google Cloud AutoML models
- Store management systems
- Mobile and web frontends
- POS systems

For questions or support, check the main project documentation or logs.
