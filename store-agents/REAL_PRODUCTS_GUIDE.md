# Real Product Management Guide

## Overview

The system was previously using **hardcoded demo data** for development purposes. This guide shows you how to set up **real product data** for your store.

## Why Products Were Hardcoded

The products in `common/product_service.py` were hardcoded as **demo data** for:

- Development and testing
- Showing how the system works
- Providing sample data structure

In a real application, products should come from:

- User input through your frontend
- Image-based product registration
- CSV imports
- Integration with supplier databases

## Setting Up Real Products

### Method 1: Interactive Setup Script

Run the interactive setup script:

```bash
cd /Users/walterbanda/Desktop/AI/adk-a2a/store-agents
python setup_products.py
```

This will guide you through:

- Adding individual products
- Importing from CSV
- Setting up sample data for testing
- Viewing current inventory

### Method 2: CSV Import

1. Create a CSV template:

```bash
python setup_products.py --create-template
```

2. Edit `product_template.csv` with your products:

```csv
product_name,category,brand,unit_price,stock_quantity,cost_price,reorder_point,unit_of_measure,supplier,barcode,description
Bread (Loaf),Bakery,Local Bakery,1.25,10,1.00,5,loaves,Bakery Supplier,1234567890,Fresh baked bread
Milk (1L),Dairy,Dairibord,1.80,8,1.45,6,1L cartons,Dairy Supplier,0987654321,Fresh milk
```

3. Import using the setup script

### Method 3: REST API

Start the product management API:

```bash
python product_management_api.py
```

API endpoints available at `http://localhost:8002`:

#### Add Product

```bash
curl -X POST "http://localhost:8002/products/YOUR_USER_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Bread (Loaf)",
    "category": "Bakery",
    "unit_price": 1.25,
    "stock_quantity": 10,
    "brand": "Local Bakery",
    "reorder_point": 5
  }'
```

#### Get Products

```bash
curl "http://localhost:8002/products/YOUR_USER_ID"
```

#### Update Stock

```bash
curl -X PUT "http://localhost:8002/products/YOUR_USER_ID/PRODUCT_ID/stock" \
  -H "Content-Type: application/json" \
  -d '{
    "new_quantity": 15,
    "movement_type": "restock"
  }'
```

### Method 4: Image Registration

Use the existing image-based product registration:

```bash
# Start the product transaction agent
./start_product_transaction_agent.sh
```

Then send product images to register new products automatically.

## Frontend Integration

Your frontend should integrate with the product management API to:

### 1. Product Catalog Management

```javascript
// Add product
const addProduct = async (userId, productData) => {
  const response = await fetch(`/api/products/${userId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(productData),
  });
  return response.json();
};

// Get products
const getProducts = async (userId) => {
  const response = await fetch(`/api/products/${userId}`);
  return response.json();
};
```

### 2. Inventory Management

```javascript
// Update stock
const updateStock = async (userId, productId, newQuantity) => {
  const response = await fetch(`/api/products/${userId}/${productId}/stock`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      new_quantity: newQuantity,
      movement_type: "adjustment",
    }),
  });
  return response.json();
};
```

### 3. Search and Analytics

```javascript
// Search products
const searchProducts = async (userId, searchTerm) => {
  const response = await fetch(
    `/api/products/${userId}/search?q=${searchTerm}`
  );
  return response.json();
};

// Get analytics
const getAnalytics = async (userId) => {
  const response = await fetch(`/api/products/${userId}/analytics`);
  return response.json();
};
```

## Database Schema

Products are stored in Firestore with this structure:

```json
{
  "store_owner_id": "user123", // Links to user
  "product_name": "Bread (Loaf)", // Required
  "category": "Bakery", // Required
  "unit_price": 1.25, // Required
  "stock_quantity": 10, // Required
  "brand": "Local Bakery", // Optional
  "supplier": "Bakery Supplier", // Optional
  "cost_price": 1.0, // Optional
  "reorder_point": 5, // Default: 5
  "unit_of_measure": "loaves", // Default: "units"
  "barcode": "1234567890", // Optional
  "description": "Fresh bread", // Optional
  "size": "500g", // Optional
  "expiry_date": "2025-06-20", // Optional
  "created_at": "2025-06-18T10:00:00Z",
  "updated_at": "2025-06-18T10:00:00Z",
  "status": "active" // "active" or "inactive"
}
```

## Migration from Demo Data

To migrate from the hardcoded demo data:

1. **Export existing demo data** (if needed):

   ```python
   from common.product_service import ProductService
   service = ProductService()
   products = await service.get_store_products("your_user_id")
   ```

2. **Set up real products** using one of the methods above

3. **Update your frontend** to use the new product management API

4. **Remove demo data** by replacing `ProductService` with `RealProductService`

## Best Practices

### 1. Data Validation

- Always validate required fields
- Check for duplicate products
- Verify price and stock values

### 2. User Permissions

- Products are isolated by `store_owner_id`
- Users can only access their own products
- Implement proper authentication

### 3. Inventory Tracking

- Use inventory movements for audit trail
- Track stock changes (sales, restocks, adjustments)
- Set appropriate reorder points

### 4. Performance

- Implement pagination for large inventories
- Use search/filtering for product lookup
- Cache frequently accessed data

## Troubleshooting

### "No products found"

- Check that you're using the correct `user_id`
- Verify products have `status: "active"`
- Ensure Firebase connection is working

### "Database connection unavailable"

- Check Firebase credentials
- Verify `FIREBASE_SERVICE_ACCOUNT_KEY` environment variable
- Test database connectivity

### CSV Import Issues

- Verify CSV column headers match expected fields
- Check data types (prices as numbers, not text)
- Ensure required fields are present

## Next Steps

1. **Set up your real product data** using this guide
2. **Update your frontend** to use the product management API
3. **Test the transaction system** with your real products
4. **Remove or disable** the hardcoded demo data

The transaction agent will now work with your real product inventory instead of hardcoded demo data!
