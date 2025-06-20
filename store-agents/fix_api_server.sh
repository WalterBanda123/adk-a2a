#!/bin/bash

echo "🔧 Fixing Store Assistant API"
echo "=========================================="

# Kill any existing servers on port 8000
echo "1. Stopping any existing servers on port 8000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "   No servers running on port 8000"

# Wait a moment
sleep 2

# Start the unified chat agent
echo "2. Starting Unified Chat Agent..."
echo "   🎯 This will handle all chat interactions through /run endpoint"
echo "   📍 Server: http://localhost:8000"

# Activate venv and start server
source venv/bin/activate
uvicorn unified_chat_agent:app --host 0.0.0.0 --port 8000 --reload &

# Get the PID
SERVER_PID=$!
echo "   ✅ Server started with PID: $SERVER_PID"

# Wait for server to start
echo "3. Waiting for server to initialize..."
sleep 5

# Test the server
echo "4. Testing server endpoints..."
curl -s http://localhost:8000/health | jq . || echo "   ❌ Health check failed"
curl -s http://localhost:8000/agents | jq . || echo "   ❌ Agents endpoint failed"

# Test the exact payload format
echo "5. Testing your exact payload format..."
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "message": "sold two mazoe",
    "context": {"user_id": "9IbW1ssRI9cneCFC7a1zKOGW1Qa2"},
    "session_id": "qt8ugXgVsjR9sVINF86W"
  }' | jq .

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo "📍 Unified Chat Agent running on http://localhost:8000"
echo "🔗 Send all requests to POST /run"
echo ""
echo "💡 Key differences from old system:"
echo "   • Single /run endpoint (not multiple endpoints)"
echo "   • Handles user_id in context object"
echo "   • Routes to appropriate sub-agents automatically"
echo ""
echo "🛑 To stop: kill $SERVER_PID"
