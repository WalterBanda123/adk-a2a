#!/usr/bin/env python3
"""
Test the full end-to-end flow with the same payload structure that was failing
"""
import os
import sys
import asyncio
import base64
import json
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.assistant.task_manager import TaskManager
from agents.assistant.agent import create_main_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_end_to_end_image_processing():
    """Test the complete flow from task manager to agent with image data"""
    
    # Path to the image file
    image_path = os.path.join(os.path.dirname(__file__), 'images-mazoe-ruspberry.jpeg')
    
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return False
    
    try:
        # Read and encode the image (just like the frontend would)
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        print(f"✅ Image loaded and encoded ({len(image_data)} characters)")
        
        # Create the agent and task manager
        print("🔄 Initializing agent and task manager...")
        agent, exit_stack = await create_main_agent()
        task_manager = TaskManager(agent)
        
        # Prepare the exact same context structure as the failing request
        context = {
            "image_data": image_data,
            "is_url": False,
            "user_id": "zXUaVlBG05bpsCy5QlGkCNbz4Rm2"
        }
        
        message = "I want to add a new product from this photo. Can you help me extract the product details?"
        
        print("🔄 Processing request through task manager...")
        print(f"Message: {message}")
        print(f"Context keys: {list(context.keys())}")
        print(f"Image data length: {len(context['image_data'])}")
        
        # Process the task
        result = await task_manager.process_task(
            message=message,
            context=context,
            session_id=None
        )
        
        print("\n📋 Raw result:")
        print(json.dumps(result, indent=2))
        print("\n" + "="*60 + "\n")
        
        # Analyze the result
        if result.get("status") == "success":
            response_message = result.get("message", "")
            
            if response_message == "(No response generated)":
                print("❌ ISSUE: Agent generated no response")
                print("This indicates the agent is not calling the vision tool properly")
                
                # Check raw events for more details
                raw_events = result.get("data", {}).get("raw_events")
                if raw_events:
                    print(f"📊 Token usage: {raw_events.get('usage_metadata', {})}")
                    print(f"📝 Agent: {raw_events.get('author', 'unknown')}")
                
                return False
            else:
                print("🎉 SUCCESS: Agent generated a response!")
                print(f"📝 Response: {response_message}")
                return True
        else:
            print(f"❌ Task processing failed: {result.get('message', 'Unknown error')}")
            return False
        
    except Exception as e:
        print(f"❌ Error during end-to-end test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing full end-to-end image processing flow...")
    print("This simulates the exact request that was failing")
    print("="*60)
    
    success = asyncio.run(test_end_to_end_image_processing())
    
    if success:
        print("\n🎉 End-to-end test completed successfully!")
        print("The image processing pipeline is working correctly.")
    else:
        print("\n💥 End-to-end test failed!")
        print("The agent is not properly processing image requests.")
    
    print("="*60)
