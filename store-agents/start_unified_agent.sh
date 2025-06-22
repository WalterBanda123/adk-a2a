#!/bin/bash

# Unified Store Assistant Startup Script
# Starts the consolidated chat interface that handles all interactions

echo "🚀 Starting Unified Store Assistant..."
echo "📍 Server will be available at: http://localhost:8003"
echo "📋 Single /run endpoint handles all chat interactions:"
echo "   • Product registration (with images)"
echo "   • Sales transactions" 
echo "   • Petty cash & financial transactions"
echo "   • Inventory queries"
echo "   • Store management"
echo "   • General help"
echo ""

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check for Firebase credentials
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ] && [ ! -f "firebase-service-account-key.json" ]; then
    echo "⚠️  Warning: Firebase service account key not found"
    echo "   Please ensure 'firebase-service-account-key.json' exists or set GOOGLE_APPLICATION_CREDENTIALS"
    echo ""
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "💡 Tip: Consider activating your virtual environment first"
    echo ""
fi

echo "🎯 Starting unified chat agent..."
echo "🔗 API endpoints:"
echo "   POST /run         - Main chat interface"
echo "   GET  /health      - Health check"
echo "   GET  /agents      - List available agents"
echo ""

# Start the server
python unified_chat_agent.py
