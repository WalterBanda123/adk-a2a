# Stock Level Integration Guide for Frontend

## Overview
Your store agent system now supports comprehensive stock level queries through the Product Management Agent. The system uses `store_owner_id` (which equals `user_id`) to filter products for each user's store.

## Available Stock Level Queries

### 1. Stock Overview (`stock_overview`)
**Best for: Dashboard summaries and main inventory view**

**Request Example:**
```json
{
  "message": "What's my stock levels?",
  "context": {"user_id": "your_user_id"},
  "session_id": "optional_session_id"
}
```

**Response Structure:**
```json
{
  "success": true,
  "message": "✅ **Stock Overview for Your Store**\n\n📦 **Total Products:** 8\n💰 **Total Inventory Value:** $234.50\n\n✅ **Healthy Stock:** 5 products\n⚠️ **Low Stock:** 2 products\n🚨 **Out of Stock:** 1 products",
  "overview": {
    "total_products": 8,
    "healthy_stock": {
      "count": 5,
      "products": [...]
    },
    "low_stock": {
      "count": 2,
      "products": [...]
    },
    "out_of_stock": {
      "count": 1,
      "products": [...]
    },
    "total_inventory_value": 234.50,
    "analytics": {...}
  },
  "requires_attention": true
}
```

### 2. All Products (`all`)
**Best for: Complete product listings and catalog views**

**Request:**
```json
{
  "message": "Show me all my products",
  "context": {"user_id": "your_user_id"}
}
```

**Response:**
```json
{
  "success": true,
  "message": "Retrieved 8 products from your store",
  "products": [
    {
      "id": "product_id",
      "product_name": "Mealie Meal (10kg)",
      "category": "Staples",
      "brand": "Gold Leaf",
      "unit_price": 8.50,
      "stock_quantity": 15,
      "reorder_point": 5,
      "supplier": "OK Zimbabwe",
      "cost_price": 7.20,
      "store_owner_id": "your_user_id"
    }
  ],
  "count": 8
}
```

### 3. Low Stock Items (`low_stock`)
**Best for: Reorder alerts and inventory management**

**Request:**
```json
{
  "message": "Which products are running low?",
  "context": {"user_id": "your_user_id"}
}
```

**Response:**
```json
{
  "success": true,
  "message": "Found 2 products that need restocking",
  "low_stock_products": [...],
  "count": 2,
  "threshold": 3,
  "advice": "Consider restocking these items soon to avoid running out of stock."
}
```

### 4. Out of Stock Items (`out_of_stock`)
**Best for: Critical stock alerts**

**Request:**
```json
{
  "message": "What's out of stock?",
  "context": {"user_id": "your_user_id"}
}
```

### 5. Analytics (`analytics`)
**Best for: Detailed inventory analytics and insights**

**Request:**
```json
{
  "message": "Give me inventory analytics",
  "context": {"user_id": "your_user_id"}
}
```

## Frontend Integration Examples

### Dashboard Widget
```javascript
// Get stock overview for dashboard
const getStockOverview = async (userId) => {
  const response = await fetch('/run', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      message: "What's my stock levels?",
      context: { user_id: userId }
    })
  });
  
  const data = await response.json();
  if (data.status === 'success') {
    return data.data.overview; // Use for dashboard display
  }
};
```

### Inventory Management Page
```javascript
// Get all products for inventory management
const getAllProducts = async (userId) => {
  const response = await fetch('/run', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      message: "Show me all my products",
      context: { user_id: userId }
    })
  });
  
  const data = await response.json();
  return data.data.products; // Array of all products
};
```

### Alert System
```javascript
// Check for items needing attention
const checkStockAlerts = async (userId) => {
  const response = await fetch('/run', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      message: "Stock overview",
      context: { user_id: userId }
    })
  });
  
  const data = await response.json();
  if (data.data.requires_attention) {
    // Show alerts for low/out of stock items
    const overview = data.data.overview;
    showStockAlerts(overview.low_stock, overview.out_of_stock);
  }
};
```

## Natural Language Queries Supported

The agent understands various ways to ask about stock:

- "What's my stock levels?"
- "Show me my inventory"
- "Which products are running low?"
- "What's out of stock?"
- "Give me a stock overview"
- "What products need restocking?"
- "Show me all my products"
- "Check inventory status"

## Data Structure Notes

### Product Object Structure
Each product contains:
```json
{
  "id": "unique_firestore_id",
  "store_owner_id": "user_id", // Links product to user
  "product_name": "Product Name",
  "category": "Category",
  "brand": "Brand Name",
  "unit_price": 0.00,
  "stock_quantity": 0,
  "reorder_point": 5,
  "supplier": "Supplier Name",
  "cost_price": 0.00,
  "last_restocked": "2025-06-05T10:00:00Z",
  "expiry_date": "2025-12-01",
  "unit_of_measure": "units",
  "barcode": "123456789"
}
```

## Server Endpoint
- **URL:** `http://localhost:8003/run` (or your configured host/port)
- **Method:** POST
- **Headers:** `Content-Type: application/json`
- **CORS:** Enabled for localhost:8100

## Session Management
- Include `user_id` in context for all requests
- Optionally include `session_id` for conversation continuity
- The agent maintains conversation state across requests

## Error Handling
```javascript
const handleStockQuery = async (message, userId) => {
  try {
    const response = await fetch('/run', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        message: message,
        context: { user_id: userId }
      })
    });
    
    const data = await response.json();
    
    if (data.status === 'success') {
      return data.data;
    } else {
      console.error('Agent error:', data.message);
      return null;
    }
  } catch (error) {
    console.error('Network error:', error);
    return null;
  }
};
```

This setup ensures your frontend can seamlessly query stock levels and get comprehensive inventory information using the user_id from your session management system.
