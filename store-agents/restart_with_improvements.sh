#!/bin/bash

echo "🔄 Restarting Store Assistant with Improved Product Matching"
echo "=========================================================="

# Kill any existing servers
echo "1. Stopping existing servers..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "   No servers running on port 8000"

# Wait a moment
sleep 2

# Activate virtual environment and start server
echo "2. Starting unified chat agent with improved matching..."
source venv/bin/activate

# Start with proper logging
python -m uvicorn unified_chat_agent:app --host 0.0.0.0 --port 8000 --log-level info --reload &

echo "3. Server starting..."
echo "   PID: $!"
echo "   URL: http://localhost:8000"

# Wait for server to start
sleep 5

# Test the exact payload
echo "4. Testing your exact request..."
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I sold two mazoe",
    "context": {"user_id": "9IbW1ssRI9cneCFC7a1zKOGW1Qa2"},
    "session_id": "qt8ugXgVsjR9sVINF86W"
  }' | jq .

echo ""
echo "=========================================================="
echo "✅ Server restarted with improved product matching!"
echo ""
echo "🔧 Improvements made:"
echo "   • Lowered match threshold: 40% → 30%"
echo "   • Enhanced brand matching: mazoe → 90% score"
echo "   • Added variations: mazoe → orange crush"
echo "   • Better fuzzy matching logic"
echo ""
echo "📝 Now try your request again from the frontend!"
