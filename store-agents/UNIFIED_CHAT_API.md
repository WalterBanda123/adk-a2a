# Unified Chat API Integration Guide

## Overview

The new unified `/run` endpoint consolidates all store management interactions into a single chat interface. Instead of multiple endpoints, everything goes through one intelligent routing system.

## Single Endpoint

**URL:** `POST http://localhost:8000/run`

## Request Format

```typescript
interface ChatRequest {
  message: string;          // User's natural language message
  user_id: string;          // User identifier  
  session_id?: string;      // Optional session tracking
  context?: object;         // Additional context
  image_data?: string;      // Base64 image for product registration
  is_url?: boolean;         // Whether image_data is a URL
}
```

## Response Format

```typescript
interface ChatResponse {
  message: string;          // Agent's response message
  agent_used: string;       // Which sub-agent handled the request
  status: string;           // "success" | "error" | "info"
  data: object;            // Additional response data
  session_id?: string;      // Session identifier
}
```

## Frontend Implementation

### Basic Chat Message

```javascript
const sendMessage = async (message, userId) => {
  const response = await fetch('http://localhost:8000/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: message,
      user_id: userId
    })
  });
  
  const result = await response.json();
  return result;
};

// Examples:
await sendMessage("Check low stock items", "user123");
await sendMessage("Sold 2 apples at $1.50 each", "user123");
await sendMessage("Petty cash $20 for office supplies", "user123");
```

### Image-Based Product Registration

```javascript
const registerProduct = async (imageFile, userId) => {
  // Convert image to base64
  const base64 = await fileToBase64(imageFile);
  
  const response = await fetch('http://localhost:8000/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: "Register this product",
      user_id: userId,
      image_data: base64,
      is_url: false
    })
  });
  
  const result = await response.json();
  return result;
};

const fileToBase64 = (file) => {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.readAsDataURL(file);
  });
};
```

### Session Management

```javascript
class StoreAssistant {
  constructor(userId) {
    this.userId = userId;
    this.sessionId = `session_${Date.now()}`;
  }
  
  async sendMessage(message, imageData = null) {
    const request = {
      message: message,
      user_id: this.userId,
      session_id: this.sessionId
    };
    
    if (imageData) {
      request.image_data = imageData;
      request.is_url = false;
    }
    
    const response = await fetch('http://localhost:8000/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });
    
    return await response.json();
  }
}

// Usage:
const assistant = new StoreAssistant("user123");
const result = await assistant.sendMessage("What can you help me with?");
```

## Supported Interactions

### 1. Product Management
```javascript
// Register product with image
await sendMessage("Register this product", userId, imageData);
await sendMessage("Add product from photo", userId, imageData);
await sendMessage("Scan this item", userId, imageData);
```

### 2. Sales Transactions
```javascript
await sendMessage("Sold 2 apples at $1.50 each", userId);
await sendMessage("Customer bought bread and milk", userId);
await sendMessage("Transaction for John: 3 sodas at $2 each", userId);
```

### 3. Cash Management
```javascript
await sendMessage("Petty cash $25 for office supplies", userId);
await sendMessage("Owner drawing $100 for personal use", userId);
await sendMessage("Deposit $500 cash", userId);
```

### 4. Inventory Queries
```javascript
await sendMessage("Check low stock items", userId);
await sendMessage("How many products do I have?", userId);
await sendMessage("Store analytics", userId);
await sendMessage("Inventory summary", userId);
```

### 5. Store Information
```javascript
await sendMessage("Store information", userId);
await sendMessage("Business details", userId);
await sendMessage("Sales summary", userId);
```

### 6. Help
```javascript
await sendMessage("Help", userId);
await sendMessage("What can you do?", userId);
await sendMessage("Available commands", userId);
```

## Response Handling

```javascript
const handleResponse = (response) => {
  const { message, agent_used, status, data } = response;
  
  // Display message to user
  displayMessage(message, status);
  
  // Handle specific agent responses
  switch (agent_used) {
    case 'product_registration':
      if (data.product) {
        updateProductCatalog(data.product);
      }
      break;
      
    case 'transaction_processor':
      if (data.receipt) {
        displayReceipt(data.receipt);
      }
      break;
      
    case 'inventory_manager':
      if (data.analytics) {
        updateDashboard(data.analytics);
      }
      break;
      
    case 'misc_transactions':
      if (data.transaction_id) {
        updateTransactionHistory(data);
      }
      break;
  }
};
```

## Error Handling

```javascript
const sendMessageWithRetry = async (message, userId, maxRetries = 3) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch('http://localhost:8000/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: message,
          user_id: userId
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      if (result.status === 'error') {
        throw new Error(result.message);
      }
      
      return result;
      
    } catch (error) {
      if (i === maxRetries - 1) {
        return {
          message: "Sorry, I'm having trouble right now. Please try again later.",
          agent_used: "error_handler",
          status: "error"
        };
      }
      
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
};
```

## Migration from Multiple Endpoints

### Before (Multiple Endpoints)
```javascript
// Old way - multiple endpoints
await registerProduct(imageData, userId);     // POST /register-product-image
await processTransaction(message, userId);    // POST /process-transaction  
await checkInventory(userId);                 // GET /inventory
await getPettyCash(userId);                   // GET /petty-cash
```

### After (Single Endpoint)
```javascript
// New way - single endpoint with natural language
await sendMessage("Register this product", userId, imageData);
await sendMessage("Sold 2 apples at $1.50", userId);
await sendMessage("Check inventory", userId);
await sendMessage("Petty cash $20 for supplies", userId);
```

## Available Agents

The system automatically routes to these sub-agents:

- **product_registration** - Image-based product registration
- **transaction_processor** - Sales transactions and receipts
- **misc_transactions** - Petty cash, drawings, deposits
- **inventory_manager** - Stock levels and analytics
- **store_manager** - Store information and business details
- **help_assistant** - General help and feature overview

## Health Check

```javascript
const checkHealth = async () => {
  const response = await fetch('http://localhost:8000/health');
  return await response.json();
};
```

## List Available Agents

```javascript
const getAgents = async () => {
  const response = await fetch('http://localhost:8000/agents');
  return await response.json();
};
```

This unified approach simplifies your frontend integration while providing more natural, conversational interactions with your store management system!
