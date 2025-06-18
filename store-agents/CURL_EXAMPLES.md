# Product Transaction Agent - cURL Examples

## Server Information
- **Base URL**: `http://localhost:8001`
- **Port**: 8001 (different from main agent on 8000)

## 🚀 Start the Server
```bash
./start_product_transaction_agent.sh
```

## 📋 cURL Commands

### 1. Check Server Status
```bash
curl -X GET "http://localhost:8001/.well-known/agent.json" \
  -H "Accept: application/json"
```

### 2. Product Registration via Image

#### Upload Base64 Image
```bash
curl -X POST "http://localhost:8001/register-product-image" \
  -H "Content-Type: application/json" \
  -d '{
    "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD//gASTWljcm9zb2Z0IE9mZmljZQD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/AD//2Q==",
    "user_id": "user123",
    "is_url": false,
    "enhance_image": true
  }'
```

#### Upload Image from URL
```bash
curl -X POST "http://localhost:8001/register-product-image" \
  -H "Content-Type: application/json" \
  -d '{
    "image_data": "https://example.com/product-image.jpg",
    "user_id": "user123", 
    "is_url": true,
    "enhance_image": true
  }'
```

### 3. Chat-Based Transactions

#### Simple Transaction
```bash
curl -X POST "http://localhost:8001/chat/transaction" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "2 bread @1.25, 1 milk @2.50",
    "user_id": "user123",
    "customer_name": "John Doe",
    "payment_method": "cash"
  }'
```

#### Complex Transaction
```bash
curl -X POST "http://localhost:8001/chat/transaction" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "3x maputi @0.5, 2 soap @1.2, 1 cooking oil @4.75, 5 eggs @0.25",
    "user_id": "user123",
    "customer_name": "Jane Smith",
    "payment_method": "cash"
  }'
```

#### Transaction with Various Formats
```bash
curl -X POST "http://localhost:8001/chat/transaction" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "2 bread @ 1.25, 1x milk @2.50, 3 eggs @ 0.25",
    "user_id": "user123"
  }'
```

## 📝 Request Body Formats

### Product Registration Request
```json
{
  "image_data": "base64_string_or_url",
  "user_id": "string",
  "is_url": false,
  "enhance_image": true
}
```

### Transaction Request
```json
{
  "message": "quantity product @price, ...",
  "user_id": "string",
  "customer_name": "string (optional)",
  "payment_method": "cash (default)"
}
```

## 📊 Expected Responses

### Product Registration Success
```json
{
  "success": true,
  "message": "Product registered successfully: Hullets Brown Sugar",
  "product": {
    "title": "Hullets Brown Sugar",
    "brand": "Hullets",
    "category": "Staples",
    "subcategory": "",
    "size": "2kg",
    "unit": "kg",
    "description": "",
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

### Transaction Success
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
        "name": "Bread",
        "quantity": 2,
        "unit_price": 1.25,
        "line_total": 2.50,
        "sku": "BRD001",
        "category": "Bakery"
      },
      {
        "name": "Milk",
        "quantity": 1,
        "unit_price": 2.50,
        "line_total": 2.50,
        "sku": "MLK001", 
        "category": "Dairy"
      }
    ],
    "subtotal": 5.00,
    "tax_rate": 0.05,
    "tax_amount": 0.25,
    "total": 5.25,
    "payment_method": "cash",
    "created_at": "2025-06-11T10:30:15Z"
  },
  "chat_response": "🧾 **Transaction Complete!**\n\n**Receipt ID:** TXN_user123_1625098765\n**Date:** 2025-06-11 10:30:15\n**Customer:** John Doe\n\n**Items:**\n• 2x Bread @ $1.25 = $2.50\n• 1x Milk @ $2.50 = $2.50\n\n**Subtotal:** $5.00\n**Tax (5%):** $0.25\n**Total:** $5.25\n\nThank you for your business! 🙏",
  "warnings": []
}
```

## 🚨 Error Examples

### Invalid Product Registration
```bash
curl -X POST "http://localhost:8001/register-product-image" \
  -H "Content-Type: application/json" \
  -d '{
    "image_data": "",
    "user_id": ""
  }'
```

### Invalid Transaction
```bash
curl -X POST "http://localhost:8001/chat/transaction" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "",
    "user_id": ""
  }'
```

## 🔧 Testing Script

Run the automated test suite:
```bash
python test_product_transaction_agent.py
```

## 🌐 Frontend Integration

### JavaScript Fetch Example
```javascript
// Product Registration
const registerProduct = async (imageBase64, userId) => {
  const response = await fetch('http://localhost:8001/register-product-image', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      image_data: `data:image/jpeg;base64,${imageBase64}`,
      user_id: userId,
      is_url: false,
      enhance_image: true
    })
  });
  
  return await response.json();
};

// Chat Transaction
const processTransaction = async (message, userId, customerName = null) => {
  const response = await fetch('http://localhost:8001/chat/transaction', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: message,
      user_id: userId,
      customer_name: customerName,
      payment_method: 'cash'
    })
  });
  
  return await response.json();
};
```

### React Example
```jsx
import React, { useState } from 'react';

const ProductTransactionApp = () => {
  const [transactionMessage, setTransactionMessage] = useState('');
  const [result, setResult] = useState(null);

  const handleTransaction = async () => {
    try {
      const response = await fetch('http://localhost:8001/chat/transaction', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: transactionMessage,
          user_id: 'user123',
          customer_name: 'Customer'
        })
      });
      
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Transaction failed:', error);
    }
  };

  return (
    <div>
      <input
        type="text"
        value={transactionMessage}
        onChange={(e) => setTransactionMessage(e.target.value)}
        placeholder="Enter transaction: 2 bread @1.25, 1 milk @2.50"
      />
      <button onClick={handleTransaction}>Process Transaction</button>
      
      {result && (
        <div>
          <h3>Result:</h3>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};
```

## 🎯 Usage Tips

1. **Image Quality**: Use clear, well-lit images for better product recognition
2. **Transaction Format**: Consistent formatting improves parsing accuracy
3. **Error Handling**: Always check the `success` field in responses
4. **Timeout**: Set appropriate timeouts (image processing: 30s, transactions: 15s)
5. **Rate Limiting**: Implement client-side rate limiting for better performance
