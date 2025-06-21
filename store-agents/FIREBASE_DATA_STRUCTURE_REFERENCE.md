# Firebase Data Structure Reference Guide

## Overview

This document outlines the Firebase authentication and Firestore data structure patterns used in this project. This serves as a reference point to ensure consistent data access patterns across all services and agents.

## Firebase Authentication & User Management

### Authentication Method

- **Primary Authentication**: Firebase Auth
- **User Identification**: Each authenticated user has a unique `user_id` (Firebase UID)

### User Profile Storage

- **Collection**: `user_profiles`
- **Document Structure**: Documents can be found using the `user_id` field
- **Query Pattern**:
  ```javascript
  // Find user profile
  db.collection("user_profiles").where("user_id", "==", user_id);
  ```

### User Profile Schema

```json
{
  "user_id": "9IbW1ssRI9cneCFC7a1zKOGW1Qa2",
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+263777123456",
  "business_owner": true,
  "preferred_currency": "USD",
  "city": "Harare",
  "country": "Zimbabwe",
  "business_type": "General Store",
  "createdAt": "2025-01-15T10:30:00Z"
}
```

## Transaction and Business Data Storage

### Important Field Naming Convention

For all business-related collections (transactions, products, sales, etc.), use **`userId`** (camelCase) instead of `user_id` for filtering:

### Collections Using `userId` Field:

- `transactions`
- `sales`
- `products`
- `inventory`
- `expenses`
- `business_transactions`
- `receipts`
- `reports`

### Query Pattern for Business Data:

```javascript
// Find user's transactions
db.collection("transactions").where("userId", "==", user_id);

// Find user's products
db.collection("products").where("userId", "==", user_id);

// Find user's sales
db.collection("sales").where("userId", "==", user_id);
```

## Data Access Patterns Summary

| Collection Type | Collection Name         | Field for User Filtering | Example                           |
| --------------- | ----------------------- | ------------------------ | --------------------------------- |
| User Profiles   | `user_profiles`         | `user_id`                | `where('user_id', '==', user_id)` |
| Transactions    | `transactions`          | `userId`                 | `where('userId', '==', user_id)`  |
| Products        | `products`              | `userId`                 | `where('userId', '==', user_id)`  |
| Sales           | `sales`                 | `userId`                 | `where('userId', '==', user_id)`  |
| Inventory       | `inventory`             | `userId`                 | `where('userId', '==', user_id)`  |
| Expenses        | `expenses`              | `userId`                 | `where('userId', '==', user_id)`  |
| Business Data   | `business_transactions` | `userId`                 | `where('userId', '==', user_id)`  |

## Service Implementation Guidelines

### UserService

- **Purpose**: Handle user profile retrieval and management
- **Primary Collection**: `user_profiles`
- **Query Field**: `user_id`
- **Fallback Collections**: `profiles` (for legacy support)

### FinancialService

- **Purpose**: Handle financial data (transactions, sales, expenses)
- **Primary Collections**: `transactions`, `sales`, `expenses`, `business_transactions`
- **Query Field**: `userId`
- **Fallback Field**: `user_id` (for backward compatibility)

### Product/Inventory Services

- **Purpose**: Handle product and inventory management
- **Primary Collections**: `products`, `inventory`
- **Query Field**: `userId`

## Code Examples

### UserService Pattern (Correct Implementation)

```python
# Get user profile
user_profiles_ref = self.db.collection('user_profiles').where('user_id', '==', user_id).limit(1)
user_profiles = await asyncio.get_event_loop().run_in_executor(None, user_profiles_ref.get)
```

### FinancialService Pattern (Correct Implementation)

```python
# Get user transactions
transactions_ref = self.db.collection('transactions').where('userId', '==', user_id)
transactions = transactions_ref.where('date', '>=', start_date).where('date', '<=', end_date)
```

### Product Service Pattern (Correct Implementation)

```python
# Get user products
products_ref = self.db.collection('products').where('userId', '==', user_id)
products = products_ref.get()
```

## Common Mistakes to Avoid

### ❌ Wrong Patterns:

```python
# Don't use user_id for business collections
transactions_ref = self.db.collection('transactions').where('user_id', '==', user_id)  # WRONG

# Don't use userId for user_profiles
user_ref = self.db.collection('user_profiles').where('userId', '==', user_id)  # WRONG
```

### ✅ Correct Patterns:

```python
# Use user_id for user_profiles
user_ref = self.db.collection('user_profiles').where('user_id', '==', user_id)  # CORRECT

# Use userId for business collections
transactions_ref = self.db.collection('transactions').where('userId', '==', user_id)  # CORRECT
```

## Debugging Zero Values in Reports

### Common Causes of Zero Values:

1. **Incorrect Field Name**: Using `user_id` instead of `userId` for business collections
2. **Wrong Collection**: Looking in the wrong collection for data
3. **Date Format Mismatch**: Date filtering not matching stored date format
4. **Missing Data**: No actual data exists for the user/date range

### Debug Checklist:

1. ✅ Verify user exists in `user_profiles` with `user_id` field
2. ✅ Check business collections using `userId` field (not `user_id`)
3. ✅ Verify date range and format matches stored data
4. ✅ Check if collections actually contain data
5. ✅ Validate field names in amount calculations (`amount`, `price`, `total`, etc.)

## Service Configuration

### Environment Variables Required:

```env
FIREBASE_SERVICE_ACCOUNT_KEY=/path/to/firebase-service-account-key.json
FIREBASE_PROJECT_ID=your-project-id  # Optional, can be read from service account key
```

### Collections That Should Exist:

- `user_profiles` - User profile information
- `transactions` - Financial transactions
- `sales` - Sales records
- `products` - Product catalog
- `inventory` - Inventory levels
- `expenses` - Business expenses
- `business_transactions` - General business transactions

## Report Generation Guidelines

### User ID Requirements:

- Always require explicit user_id parameter (no hardcoded values)
- Validate user exists in `user_profiles` before generating reports
- Use `userId` field when querying business data collections

### Data Validation:

- Check multiple collections for transaction data (`transactions`, `sales`, `business_transactions`)
- Try multiple field names for amounts (`amount`, `price`, `total`, `value`)
- Implement fallback mechanisms for different data structures

### Firebase Storage:

- All reports should be uploaded to Firebase Storage
- Return Firebase URLs for frontend access
- Clean up local temporary files after upload

## Migration Notes

If you encounter legacy data using different field names:

1. Implement dual-field queries (check both `user_id` and `userId`)
2. Log which field pattern is found for data consistency analysis
3. Gradually migrate to consistent naming patterns
4. Update documentation when patterns change

---

**Note**: This document should be referenced whenever implementing new services or debugging data access issues. Consistent adherence to these patterns will prevent zero-value reports and data access problems.
