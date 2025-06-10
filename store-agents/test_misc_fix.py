#!/usr/bin/env python3
"""
Test script to verify the misc transactions tool fix
"""
import os
import sys
import asyncio

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from agents.assistant.tools.misc_transactions_tool import create_misc_transactions_tool

async def test_misc_transactions_fix():
    """Test that the misc transactions tool works correctly after the fix"""
    try:
        # Create the tool
        misc_tool = create_misc_transactions_tool()
        
        # Test transaction history request
        print("Testing transaction history request...")
        result = await misc_tool(
            request="show me transaction history",
            user_id="test_user_12345",
            limit=5
        )
        
        print(f"✅ Transaction history test successful!")
        print(f"Result: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False

async def main():
    """Main test function"""
    print("🧪 Testing misc transactions tool fix...")
    
    success = await test_misc_transactions_fix()
    
    if success:
        print("\n✅ All tests passed! The fix is working correctly.")
    else:
        print("\n❌ Tests failed. Check the error messages above.")

if __name__ == "__main__":
    asyncio.run(main())
