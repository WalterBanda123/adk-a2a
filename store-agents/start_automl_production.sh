#!/bin/bash
# AutoML Production Startup Script

echo "🚀 Starting AutoML Production System..."

# Check environment
if [ ! -f ".env" ]; then
    echo "❌ .env file not found"
    exit 1
fi

if [ ! -f "vision-api-service.json" ]; then
    echo "❌ Google credentials not found"
    exit 1
fi

# Start the vision server with AutoML support
echo "🤖 Starting Vision Server with AutoML..."
python direct_vision_server.py

echo "✅ AutoML Production System started!"
