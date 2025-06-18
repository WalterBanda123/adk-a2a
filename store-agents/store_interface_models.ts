/**
 * Store Interface Models for Frontend Integration
 * Based on the store-agents system architecture and database structure
 */

// =====================
// Core Store Models
// =====================

export interface StoreProfile {
  store_id: string;                    // Unique store identifier
  user_id: string;                     // Owner's user ID (Firebase Auth UID)
  store_name: string;                  // Store display name
  business_type: 'grocery' | 'pharmacy' | 'electronics' | 'clothing' | 'general' | 'other';
  description?: string;                // Store description
  
  // Location & Contact
  location: {
    country: string;                   // e.g., "Zimbabwe"
    city?: string;                     // e.g., "Harare"
    address?: string;                  // Physical address
    coordinates?: {
      latitude: number;
      longitude: number;
    };
  };
  
  contact?: {
    phone?: string;
    email?: string;
    whatsapp?: string;
  };
  
  // Business Details
  currency: 'USD' | 'ZIG' | 'ZWL' | string;  // Primary currency
  tax_rate: number;                    // Default tax rate (e.g., 0.05 for 5%)
  business_size: 'small' | 'medium' | 'large';
  
  // System Fields
  created_at: string;                  // ISO date string
  updated_at: string;                  // ISO date string
  status: 'active' | 'inactive' | 'suspended';
  
  // Business Profile for AI Enhancement
  industry_profile: {
    common_brands: string[];           // Frequently sold brands
    product_categories: string[];      // Main product categories
    custom_brands?: string[];          // User-added brands
    size_patterns?: string[];          // Common size formats
  };
}

// =====================
// Product Models
// =====================

export interface Product {
  id: string;                          // Firestore document ID
  sku?: string;                        // Product SKU/barcode
  product_name: string;                // Product display name
  category: string;                    // Product category
  subcategory?: string;                // Product subcategory
  brand?: string;                      // Product brand
  
  // Pricing
  unit_price: number;                  // Selling price
  cost_price?: number;                 // Purchase/cost price
  
  // Inventory
  stock_quantity: number;              // Current stock level
  reorder_point: number;               // Minimum stock before reorder
  unit_of_measure: string;             // "units", "kg", "liters", etc.
  
  // Supplier Information
  supplier?: string;                   // Supplier name
  supplier_contact?: string;           // Supplier contact
  
  // Dates
  last_restocked?: string;             // ISO date string
  expiry_date?: string;                // ISO date string for perishables
  
  // Store Association
  store_owner_id: string;              // Links to user_id
  store_id?: string;                   // Optional store_id for multi-store users
  
  // Additional Fields
  description?: string;                // Product description
  size?: string;                       // Product size/variant
  barcode?: string;                    // Product barcode
  image_url?: string;                  // Product image URL
  
  // System Fields
  created_at: string;                  // ISO date string
  updated_at: string;                  // ISO date string
  status: 'active' | 'inactive' | 'discontinued';
}

// =====================
// Stock Analytics
// =====================

export interface StockOverview {
  total_products: number;
  total_inventory_value: number;
  
  healthy_stock: {
    count: number;
    products: Product[];
  };
  
  low_stock: {
    count: number;
    products: Product[];
  };
  
  out_of_stock: {
    count: number;
    products: Product[];
  };
  
  analytics: {
    categories: Array<{
      name: string;
      count: number;
      value: number;
    }>;
    top_brands: Array<{
      name: string;
      count: number;
      value: number;
    }>;
    reorder_suggestions: Product[];
  };
  
  requires_attention: boolean;
}

// =====================
// Transaction Models (Frontend Compatible)
// =====================

export interface Customer {
  name?: string;
  email?: string;
  phone?: string;
}

export interface CartItem {
  id: string;
  name: string;
  quantity: number;
  unitPrice: number;                   // Note: camelCase for frontend
  totalPrice: number;                  // Note: camelCase for frontend
  barcode?: string;
  category?: string;
}

export interface TransactionReceipt {
  id: string;                          // Transaction ID
  amount: number;                      // Total amount
  description: string;                 // Transaction description
  merchant: string;                    // Store name
  date: string;                        // Transaction date
  time: string;                        // Transaction time
  status: 'completed' | 'pending' | 'failed' | 'cancelled';
  category: string;                    // Transaction category
  
  // Receipt Details
  cartItems: CartItem[];
  customer?: Customer;
  paymentMethod: 'cash' | 'mobile_money' | 'card' | 'credit';
  cashierName: string;
  receiptNumber: string;
  
  // Financial Breakdown
  subtotal: number;
  tax: number;
  discount?: number;
  
  // Store Association
  store_id: string;
  
  // Additional Fields
  cartImage?: string;                  // Image of scanned items
  change_due?: number;                 // Cash change
  notes?: string;                      // Additional notes
}

// =====================
// User Profile Models
// =====================

export interface UserProfile {
  user_id: string;                     // Firebase Auth UID
  name: string;
  email: string;
  phone?: string;
  
  // Preferences
  language_preference: 'English' | 'Shona' | 'Ndebele';
  preferred_currency: 'USD' | 'ZIG' | 'ZWL';
  
  // Location
  country: string;
  city?: string;
  location?: string;
  
  // Business Information
  business_owner: boolean;
  business_profile?: {
    industry: string;                  // 'grocery', 'pharmacy', etc.
    business_size: 'small' | 'medium' | 'large';
    years_in_business?: number;
    main_products?: string[];
  };
  
  // System Fields
  created_at: string;
  updated_at: string;
  last_active?: string;
  status: 'active' | 'inactive';
}

// =====================
// API Response Models
// =====================

export interface StoreApiResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
  error?: string;
  timestamp: string;
}

export interface AgentResponse {
  message: string;
  status: 'success' | 'error';
  data: {
    raw_events: any;
    processing_method: string;
  };
  session_id: string;
}

// =====================
// Dashboard Models
// =====================

export interface DashboardData {
  store_overview: StoreOverview;
  recent_transactions: TransactionReceipt[];
  stock_alerts: {
    low_stock: Product[];
    out_of_stock: Product[];
    expiring_soon: Product[];
  };
  performance_metrics: {
    daily_sales: number;
    weekly_sales: number;
    monthly_sales: number;
    total_transactions: number;
  };
}

export interface StoreOverview {
  total_products: number;
  total_inventory_value: number;
  low_stock_count: number;
  out_of_stock_count: number;
  pending_transactions: number;
  daily_revenue: number;
  weekly_revenue: number;
  monthly_revenue: number;
}

// =====================
// Frontend Service Interfaces
// =====================

export interface StoreService {
  // Store Management
  getStoreProfile(userId: string): Promise<StoreProfile>;
  updateStoreProfile(storeProfile: Partial<StoreProfile>): Promise<boolean>;
  
  // Product Management
  getProducts(userId: string): Promise<Product[]>;
  getProduct(productId: string): Promise<Product>;
  addProduct(product: Omit<Product, 'id' | 'created_at' | 'updated_at'>): Promise<string>;
  updateProduct(productId: string, updates: Partial<Product>): Promise<boolean>;
  deleteProduct(productId: string): Promise<boolean>;
  
  // Stock Management
  getStockOverview(userId: string): Promise<StockOverview>;
  getLowStockItems(userId: string): Promise<Product[]>;
  getOutOfStockItems(userId: string): Promise<Product[]>;
  updateStock(productId: string, quantity: number): Promise<boolean>;
  
  // Transactions
  processTransaction(transaction: any): Promise<TransactionReceipt>;
  getTransactionHistory(userId: string, limit?: number): Promise<TransactionReceipt[]>;
  getTransaction(transactionId: string): Promise<TransactionReceipt>;
  
  // Agent Integration
  queryAgent(message: string, userId: string, sessionId?: string): Promise<AgentResponse>;
  
  // Dashboard
  getDashboardData(userId: string): Promise<DashboardData>;
}

// =====================
// API Endpoints Configuration
// =====================

export const API_ENDPOINTS = {
  AGENT_BASE: 'http://localhost:8003',
  AGENT_RUN: '/run',
  
  // Standard REST endpoints (if you add them later)
  STORES: '/api/stores',
  PRODUCTS: '/api/products',
  TRANSACTIONS: '/api/transactions',
  USERS: '/api/users',
} as const;

// =====================
// Frontend Integration Helpers
// =====================

export interface AgentQueryParams {
  message: string;
  context: {
    user_id: string;
    store_id?: string;
  };
  session_id?: string;
}

// Example usage queries for the agent
export const STOCK_QUERIES = {
  OVERVIEW: "What's my stock levels?",
  ALL_PRODUCTS: "Show me all my products",
  LOW_STOCK: "Which products are running low?",
  OUT_OF_STOCK: "What's out of stock?",
  ANALYTICS: "Give me inventory analytics",
} as const;

export const TRANSACTION_QUERIES = {
  PROCESS_SALE: "I sold {items}",
  PRICE_CHECK: "What's the price of {product}?",
  TRANSACTION_HISTORY: "Show me recent sales",
} as const;

// =====================
// Type Guards
// =====================

export function isStoreProfile(obj: any): obj is StoreProfile {
  return obj && typeof obj.store_id === 'string' && typeof obj.user_id === 'string';
}

export function isProduct(obj: any): obj is Product {
  return obj && typeof obj.id === 'string' && typeof obj.product_name === 'string';
}

export function isTransactionReceipt(obj: any): obj is TransactionReceipt {
  return obj && typeof obj.id === 'string' && typeof obj.amount === 'number';
}

// =====================
// Enhanced Agent Integration
// =====================

export interface AgentCapabilities {
  user_greeting: boolean;              // Can greet users personally
  product_transaction: boolean;        // Can process sales transactions
  inventory_management: boolean;       // Can manage stock levels
  product_addition: boolean;           // Can add new products via vision
  price_checking: boolean;             // Can check product prices
  analytics: boolean;                  // Can provide business analytics
}

export interface AgentSession {
  session_id: string;
  user_id: string;
  store_id?: string;
  created_at: string;
  last_interaction: string;
  conversation_history: Array<{
    message: string;
    response: string;
    timestamp: string;
    agent_type: 'greeting' | 'transaction' | 'inventory' | 'product' | 'analytics';
  }>;
  context: {
    current_task?: string;
    pending_transactions?: string[];
    last_products_viewed?: string[];
  };
}

// =====================
// Image Processing Models
// =====================

export interface ProductImage {
  id: string;
  product_id?: string;                 // Linked product if recognized
  image_url: string;                   // Firebase Storage URL
  image_base64?: string;               // Base64 for processing
  recognition_status: 'pending' | 'recognized' | 'failed' | 'manual_review';
  
  // AI Recognition Results
  recognized_products?: Array<{
    name: string;
    confidence: number;
    brand?: string;
    category?: string;
    suggested_price?: number;
  }>;
  
  // Processing Metadata
  uploaded_at: string;
  processed_at?: string;
  user_id: string;
  store_id?: string;
}

export interface VisionProcessingResult {
  success: boolean;
  message: string;
  products_recognized: number;
  products_added: number;
  failed_recognitions: Array<{
    area: string;
    reason: string;
  }>;
  suggested_actions: string[];
}

// =====================
// Enhanced Inventory Models
// =====================

export interface InventoryMovement {
  id: string;
  product_id: string;
  movement_type: 'sale' | 'restock' | 'adjustment' | 'waste' | 'return';
  quantity: number;                    // Positive for additions, negative for reductions
  unit_cost?: number;                  // Cost per unit for restocks
  reason?: string;                     // Reason for adjustment
  reference_id?: string;               // Transaction ID or supplier invoice
  
  // Metadata
  created_by: string;                  // User ID
  created_at: string;
  notes?: string;
}

export interface StockAlert {
  id: string;
  product_id: string;
  product_name: string;
  alert_type: 'low_stock' | 'out_of_stock' | 'expiring_soon' | 'overstock';
  current_quantity: number;
  threshold_quantity?: number;
  expiry_date?: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  
  // Alert Management
  status: 'active' | 'acknowledged' | 'resolved';
  created_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
  acknowledged_by?: string;
}

// =====================
// Enhanced Transaction Models
// =====================

export interface PaymentMethod {
  type: 'cash' | 'mobile_money' | 'card' | 'credit' | 'bank_transfer';
  details?: {
    // Mobile Money
    phone_number?: string;
    network?: 'ecocash' | 'onemoney' | 'telecash';
    
    // Card
    last_four_digits?: string;
    card_type?: 'visa' | 'mastercard' | 'local';
    
    // Bank Transfer
    bank_name?: string;
    reference_number?: string;
  };
  amount_paid: number;
  transaction_fee?: number;
  status: 'pending' | 'completed' | 'failed' | 'refunded';
}

export interface EnhancedTransaction extends TransactionReceipt {
  // Enhanced payment details
  payment_methods: PaymentMethod[];   // Support multiple payment methods
  
  // Customer loyalty
  customer_id?: string;
  loyalty_points_earned?: number;
  loyalty_points_redeemed?: number;
  
  // Advanced features
  delivery_info?: {
    type: 'pickup' | 'delivery';
    address?: string;
    delivery_date?: string;
    delivery_fee?: number;
    delivery_status?: 'pending' | 'in_transit' | 'delivered';
  };
  
  // Returns and exchanges
  return_deadline?: string;
  exchange_allowed: boolean;
  
  // Business analytics
  profit_margin?: number;
  cost_of_goods_sold?: number;
}

// =====================
// Business Analytics Models
// =====================

export interface SalesAnalytics {
  period: 'daily' | 'weekly' | 'monthly' | 'yearly';
  start_date: string;
  end_date: string;
  
  financial_metrics: {
    total_revenue: number;
    total_profit: number;
    average_transaction_value: number;
    total_transactions: number;
    total_items_sold: number;
    profit_margin_percentage: number;
  };
  
  product_performance: Array<{
    product_id: string;
    product_name: string;
    quantity_sold: number;
    revenue: number;
    profit: number;
  }>;
  
  category_performance: Array<{
    category: string;
    quantity_sold: number;
    revenue: number;
    profit: number;
  }>;
  
  trends: {
    revenue_trend: 'increasing' | 'decreasing' | 'stable';
    best_selling_day: string;
    peak_hours: string[];
    seasonal_patterns?: string[];
  };
}

export interface BusinessInsights {
  recommendations: Array<{
    type: 'inventory' | 'pricing' | 'marketing' | 'operational';
    priority: 'low' | 'medium' | 'high';
    title: string;
    description: string;
    estimated_impact: string;
    action_items: string[];
  }>;
  
  performance_scores: {
    inventory_efficiency: number;      // 0-100
    pricing_optimization: number;     // 0-100
    customer_satisfaction: number;    // 0-100
    profit_optimization: number;      // 0-100
  };
  
  growth_opportunities: string[];
  risk_factors: string[];
}

// =====================
// Enhanced API Models
// =====================

export interface BulkOperationResult<T> {
  success: boolean;
  total_items: number;
  successful_items: number;
  failed_items: number;
  results: Array<{
    item: T;
    success: boolean;
    error?: string;
  }>;
  summary: string;
}

export interface SearchFilters {
  categories?: string[];
  brands?: string[];
  price_range?: {
    min: number;
    max: number;
  };
  stock_status?: 'in_stock' | 'low_stock' | 'out_of_stock';
  date_range?: {
    start: string;
    end: string;
  };
}

// =====================
// Enhanced Service Interface
// =====================

export interface EnhancedStoreService extends StoreService {
  // Image Processing
  uploadProductImage(image: File | string, userId: string): Promise<ProductImage>;
  processProductImage(imageId: string): Promise<VisionProcessingResult>;
  getProductImages(productId: string): Promise<ProductImage[]>;
  
  // Advanced Inventory
  recordInventoryMovement(movement: Omit<InventoryMovement, 'id' | 'created_at'>): Promise<string>;
  getInventoryMovements(productId: string, limit?: number): Promise<InventoryMovement[]>;
  getStockAlerts(userId: string): Promise<StockAlert[]>;
  acknowledgeStockAlert(alertId: string): Promise<boolean>;
  
  // Enhanced Transactions
  processEnhancedTransaction(transaction: Partial<EnhancedTransaction>): Promise<EnhancedTransaction>;
  refundTransaction(transactionId: string, reason: string): Promise<boolean>;
  
  // Analytics
  getSalesAnalytics(userId: string, period: SalesAnalytics['period']): Promise<SalesAnalytics>;
  getBusinessInsights(userId: string): Promise<BusinessInsights>;
  
  // Bulk Operations
  bulkAddProducts(products: Omit<Product, 'id' | 'created_at' | 'updated_at'>[]): Promise<BulkOperationResult<Product>>;
  bulkUpdatePrices(updates: Array<{ product_id: string; new_price: number }>): Promise<BulkOperationResult<Product>>;
  
  // Search and Filtering
  searchProducts(query: string, filters?: SearchFilters): Promise<Product[]>;
  getProductsByCategory(category: string, userId: string): Promise<Product[]>;
  
  // Agent Sessions
  createAgentSession(userId: string): Promise<AgentSession>;
  getAgentSession(sessionId: string): Promise<AgentSession>;
  updateAgentSession(sessionId: string, updates: Partial<AgentSession>): Promise<boolean>;
}

// =====================
// Enhanced Query Patterns
// =====================

export const ENHANCED_AGENT_QUERIES = {
  // Image Processing
  ADD_PRODUCTS_FROM_IMAGE: "I have a photo of products to add to my inventory",
  RECOGNIZE_PRODUCT: "What product is this in the image?",
  
  // Advanced Inventory
  RESTOCK_PRODUCT: "I restocked {quantity} units of {product}",
  ADJUST_INVENTORY: "Adjust {product} inventory by {quantity} due to {reason}",
  CHECK_EXPIRING: "What products are expiring soon?",
  
  // Analytics
  SALES_REPORT: "Give me a sales report for {period}",
  BEST_SELLERS: "What are my best selling products?",
  PROFIT_ANALYSIS: "Analyze my profit margins",
  BUSINESS_INSIGHTS: "What business insights do you have for me?",
  
  // Advanced Features
  CUSTOMER_HISTORY: "Show me customer {name}'s purchase history",
  PRICE_COMPARISON: "Compare prices of {product} with market rates",
  BULK_OPERATIONS: "I need to update prices for all {category} products",
} as const;

// =====================
// Export Enhanced Types
// =====================

export type {
  AgentCapabilities,
  AgentSession,
  ProductImage,
  VisionProcessingResult,
  InventoryMovement,
  StockAlert,
  PaymentMethod,
  EnhancedTransaction,
  SalesAnalytics,
  BusinessInsights,
  BulkOperationResult,
  SearchFilters,
  EnhancedStoreService,
};

// =====================
// Export Everything
// =====================

export type {
  StoreProfile,
  Product,
  StockOverview,
  Customer,
  CartItem,
  TransactionReceipt,
  UserProfile,
  StoreApiResponse,
  AgentResponse,
  DashboardData,
  StoreOverview as StoreOverviewType,
  StoreService,
  AgentQueryParams,
};
