#!/bin/bash

# Product Transaction Agent Startup Script
# Starts the FastAPI server for image-based product registration and chat-based transactions

echo "🚀 Starting Product Transaction Agent Server..."
echo "📍 Server will be available at: http://localhost:8001"
echo ""

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check if required environment variables are set
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ] && [ ! -f "firebase-service-account-key.json" ]; then
    echo "⚠️  Warning: Firebase service account key not found"
    echo "   Please ensure 'firebase-service-account-key.json' exists or set GOOGLE_APPLICATION_CREDENTIALS"
fi

# Start the server
python agents/product_transaction_agent/agent.py
