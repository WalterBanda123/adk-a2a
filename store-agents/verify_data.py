#!/usr/bin/env python3
"""
Quick test to verify if our dummy data exists and can be retrieved
"""
import os
import sys
import asyncio
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from common.financial_service import FinancialService
from common.user_service import UserService

async def verify_data():
    """Quick verification of our database data"""
    test_user_id = "test_user_1749461758"
    
    print("🔍 Verifying Database Data")
    print("=" * 50)
    
    user_service = UserService()
    financial_service = FinancialService()
    
    # Test with a very broad date range to catch any data
    start_date = datetime.now() - timedelta(days=90)  # Go back 90 days
    end_date = datetime.now()
    
    print(f"Testing date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"User ID: {test_user_id}")
    
    result = await financial_service.get_financial_data(test_user_id, start_date, end_date)
    
    if result["success"]:
        data = result["data"]
        print(f"\n✅ Data Retrieved Successfully:")
        print(f"   Transactions: {len(data['transactions'])}")
        print(f"   Sales: {len(data['sales'])}")
        print(f"   Expenses: {len(data['expenses'])}")
        print(f"   Metrics: {data['metrics']}")
        
        if data['transactions']:
            print(f"\n📄 Sample Transaction:")
            sample = data['transactions'][0]
            print(f"   Date: {sample.get('date')}")
            print(f"   Amount: {sample.get('amount')}")
            print(f"   Status: {sample.get('status')}")
            print(f"   Description: {sample.get('description')}")
        
        if data['expenses']:
            print(f"\n💸 Sample Expense:")
            sample = data['expenses'][0]
            print(f"   Date: {sample.get('date')}")
            print(f"   Amount: {sample.get('amount')}")
            print(f"   Category: {sample.get('category')}")
            print(f"   Description: {sample.get('description')}")
    else:
        print(f"❌ Error: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(verify_data())
