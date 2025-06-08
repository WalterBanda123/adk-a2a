#!/bin/bash

# Store Assistant Agent - Deployment Script

echo "🚀 Starting Store Assistant Agent deployment..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check environment configuration
echo "⚙️  Checking configuration..."
if [ ! -f ".env" ]; then
    echo "❌ .env file not found! Please create one with required variables."
    exit 1
fi

if [ ! -f "firebase-service-account-key.json" ]; then
    echo "❌ Firebase service account key not found!"
    exit 1
fi

# Test imports
echo "🧪 Testing imports..."
python -c "from agents.assistant.agent import root_agent; print('✅ Agent imports OK')"
python -c "from agents.assistant.task_manager import TaskManager; print('✅ Task manager imports OK')"
python -c "from common.image_analysis_service import ImageAnalysisService; print('✅ Image service imports OK')"

echo "✅ Deployment checks complete!"
echo ""
echo "🎯 To start the server, run:"
echo "   source venv/bin/activate"
echo "   python -m agents.assistant"
echo ""
echo "🌐 Server will be available at: http://localhost:8003"
