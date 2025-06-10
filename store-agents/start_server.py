#!/usr/bin/env python3
"""
Start Enhanced Direct Vision Server
"""
import os
import sys
import subprocess

def start_enhanced_server():
    """Start the enhanced direct vision server"""
    
    print("🚀 STARTING ENHANCED DIRECT VISION SERVER")
    print("=" * 50)
    
    # Set environment variables
    env = os.environ.copy()
    env['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/walterbanda/Desktop/AI/adk-a2a/store-agents/vision-api-service.json'
    
    print(f"🔑 Credentials: {env['GOOGLE_APPLICATION_CREDENTIALS']}")
    
    # Check if credentials file exists
    if not os.path.exists(env['GOOGLE_APPLICATION_CREDENTIALS']):
        print("❌ Credentials file not found!")
        return False
    
    print("✅ Credentials file found")
    
    # Check if enhanced processor is available
    try:
        from enhanced_add_product_vision_tool_clean import EnhancedProductVisionProcessor
        print("✅ Enhanced processor available")
    except ImportError as e:
        print(f"❌ Enhanced processor not available: {e}")
        return False
    
    # Start the server
    print("\n🌐 Starting server on http://localhost:8000")
    print("📋 Available endpoints:")
    print("   POST /analyze_image - Enhanced product analysis")
    print("   GET  /            - Health check")
    print("\n💡 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Start the server process
        subprocess.run([
            sys.executable, 
            'direct_vision_server.py'
        ], env=env, cwd='/Users/walterbanda/Desktop/AI/adk-a2a/store-agents')
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        return True
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        return False

if __name__ == "__main__":
    start_enhanced_server()
