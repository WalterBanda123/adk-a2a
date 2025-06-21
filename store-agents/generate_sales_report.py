#!/usr/bin/env python3
"""
Generate a sales report for today for the specified user and upload to Firebase Storage
"""
import asyncio
import sys
import os
import tempfile
import argparse
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the store-agents directory to the Python path
sys.path.append('/Users/walterbanda/Desktop/AI/adk-a2a/store-agents')

from common.financial_service import FinancialService
from common.user_service import UserService
from common.pdf_report_generator import PDFReportGenerator
from common.firebase_storage_service import FirebaseStorageService

async def generate_sales_report(user_id=None, date=None, debug=False):
    """
    Generate a comprehensive sales report and upload to Firebase Storage
    
    Args:
        user_id (str): User ID to generate report for
        date (str): Date to generate report for (YYYY-MM-DD format), defaults to today
        debug (bool): Whether to print additional debug information
    
    Returns:
        dict: Report summary with Firebase URLs for frontend
    """
    
    if not user_id:
        raise ValueError("User ID is required")
        
    today = date if date else datetime.now().strftime("%Y-%m-%d")
    
    print(f"📊 Generating Sales Report for {today}")
    print("=" * 60)
    
    # Initialize services
    financial_service = FinancialService()
    user_service = UserService()
    pdf_generator = PDFReportGenerator()
    
    try:
        # Get user information
        print("👤 Getting user information...")
        user_info = await user_service.get_user_info(user_id)
        if not user_info:
            print("❌ User not found")
            return
        
        print(f"✅ User: {user_info.get('name', 'Unknown')}")
        
        # Get financial data for today
        print(f"\n💰 Getting financial data for {today}...")
        print(f"   User ID: {user_id}")
        print(f"   Date Range: {today} 00:00:00 to {today} 23:59:59")
        print(f"   Collections to query: transactions, sales, records, business_transactions")
        print(f"   Fields: user_id and userId will both be checked")
        
        start_dt = datetime.strptime(f"{today} 00:00:00", "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(f"{today} 23:59:59", "%Y-%m-%d %H:%M:%S")
        
        # Get transactions for today
        financial_data = await financial_service.get_financial_data(
            user_id=user_id,
            start_date=start_dt,
            end_date=end_dt
        )
        
        if debug:
            print("\n🔍 DEBUG: Raw financial data response:")
            print(json.dumps(financial_data, indent=2, default=str)[:1000] + "...")  # Print first 1000 chars
        
        # Check for success
        if not financial_data.get('success'):
            print(f"\n❌ Error retrieving financial data: {financial_data.get('error', 'Unknown error')}")
            
        # Extract data from the response
        data = financial_data.get('data', {})
        transactions = data.get('transactions', [])
        sales = data.get('sales', [])
        expenses = data.get('expenses', [])
        metrics = data.get('metrics', {})
        
        # Detailed debugging to find where the data might be
        if debug:
            print("\n🔍 DEBUG: All keys in financial_data:")
            print(f"   Financial data top-level keys: {list(financial_data.keys())}")
            print(f"   Data object keys: {list(data.keys())}")
            print(f"   Metrics object keys: {list(metrics.keys())}")
            
            # Check various possible locations for sales data
            possible_sales_locations = ['sales', 'revenue', 'income', 'transactions']
            for key in possible_sales_locations:
                if key in data:
                    print(f"   Found potential sales data in data['{key}']")
                    print(f"   Count: {len(data.get(key, []))}")
        
        # Print major metrics for both debug and normal mode
        print(f"\n📈 Financial data retrieved:")
        print(f"   Total Revenue: ${metrics.get('total_revenue', 0):.2f}")
        print(f"   Total Expenses: ${metrics.get('total_expenses', 0):.2f}")
        print(f"   Profit/Loss: ${metrics.get('profit_loss', 0):.2f}")
        print(f"   Profit Margin: {metrics.get('profit_margin', 0):.1f}%")
        print(f"   Transactions: {len(transactions)}")
        print(f"   Sales: {len(sales)}")
        print(f"   Expenses: {len(expenses)}")
        
        # Print sources of data
        if transactions:
            collections = set(t.get('collection', 'unknown') for t in transactions)
            print(f"\n📊 Found transactions in collections: {', '.join(collections)}")
        
        # Print detailed sample data for debugging
        if debug and transactions:
            print("\n🔍 DEBUG: Sample transaction:")
            print(json.dumps(transactions[0], indent=2, default=str))
            
            # Show all fields in transactions to help diagnose where values might be
            all_fields = set()
            for t in transactions[:5]:  # Check first 5 transactions
                all_fields.update(t.keys())
            print(f"\n🔍 DEBUG: All fields found in transactions: {sorted(all_fields)}")
            
            # Check for amount fields with different names
            amount_fields = ['amount', 'price', 'total', 'value', 'sale_amount', 'transaction_amount']
            for field in amount_fields:
                values = [t.get(field) for t in transactions if field in t]
                if values:
                    print(f"   Found {len(values)} transactions with '{field}' field")
                    print(f"   Sample values: {values[:3]}")
        
        if debug and sales:
            print("\n🔍 DEBUG: Sample sale:")
            print(json.dumps(sales[0], indent=2, default=str))
            
            # Show all fields in sales to help diagnose
            all_fields = set()
            for s in sales[:5]:  # Check first 5 sales
                all_fields.update(s.keys())
            print(f"\n🔍 DEBUG: All fields found in sales: {sorted(all_fields)}")
        
        if debug and not transactions and not sales:
            print("\n⚠️ WARNING: No transactions or sales data found!")
            print("   This will likely result in a report with zero values")
            print("   Possible causes:")
            print("   1. User ID might be incorrect")
            print("   2. No data exists for the specified date")
            print("   3. Data might use different field names (not user_id or userId)")
            print("   4. Data might be in different collections than expected")
            print("   5. Data format might not match expected format")
            
        # Extract all required metrics from the financial data
        # Get metrics, use calculated values if the metrics are missing
        metrics = data.get('metrics', {})
        total_revenue = metrics.get('total_revenue', 0)
        total_expenses = metrics.get('total_expenses', 0)
        profit_loss = metrics.get('profit_loss', 0)
        profit_margin = metrics.get('profit_margin', 0)
        
        # Use data from transactions if metrics are not available
        if total_revenue == 0 and transactions:
            # Sum up transaction amounts if available
            transaction_totals = [float(t.get('amount', 0)) for t in transactions if 'amount' in t]
            if transaction_totals:
                total_revenue = sum(transaction_totals)
                print(f"🔄 Calculated total_revenue from transactions: ${total_revenue:.2f}")
        
        # Calculate transaction count from actual transactions
        transaction_count = len(transactions)
        
        # Create a detailed report data structure
        report_data = {
            "report_type": "daily_sales",
            "date": today, 
            "period": f"Daily Report - {today}",
            "user_info": user_info,
            "business_name": user_info.get('business_name', user_info.get('name', 'Business')),
            "currency": user_info.get('currency', 'USD'),
            "financial_summary": {
                "total_sales": total_revenue,
                "total_expenses": total_expenses,
                "net_profit": profit_loss,
                "gross_profit_margin": profit_margin,
                "transaction_count": transaction_count,
                "avg_transaction_value": (total_revenue / transaction_count) if transaction_count > 0 else 0
            },
            "transactions": transactions,
            "sales": sales,
            "top_products": data.get('top_products', []),
            "expense_breakdown": data.get('expense_breakdown', {}),
            "recommendations": []
        }
        
        # Add some basic recommendations
        if report_data["financial_summary"]["net_profit"] > 0:
            report_data["recommendations"].append("✅ Positive profit for today - great job!")
        else:
            report_data["recommendations"].append("⚠️ Consider reviewing expenses to improve profitability")
            
        if report_data["financial_summary"]["transaction_count"] > 0:
            avg_transaction = report_data["financial_summary"]["total_sales"] / report_data["financial_summary"]["transaction_count"]
            report_data["recommendations"].append(f"💡 Average transaction value: ${avg_transaction:.2f}")
        
        # Create temporary files for JSON and PDF
        temp_dir = tempfile.gettempdir()
        json_filename = os.path.join(temp_dir, f"sales_report_{today}.json")
        pdf_filename = os.path.join(temp_dir, f"sales_report_{today}.pdf")
        
        # Save JSON report to temp folder
        with open(json_filename, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        print(f"\n💾 JSON report saved to temporary location: {json_filename}")
        
        # Initialize Firebase Storage
        firebase_storage = FirebaseStorageService(user_id)
        
        # Generate PDF report
        print(f"\n📄 Generating PDF report...")
        pdf_result = pdf_generator.generate_financial_report(
            user_info=user_info,
            financial_data=financial_data,
            period=f"Daily Report - {today}",
            store_info={"name": "Store Name", "address": "Store Address"},  # Example store info
            output_path=pdf_filename
        )
        
        firebase_pdf_url = None
        firebase_json_url = None
        
        if pdf_result.get("success"):
            print(f"✅ PDF report generated: {pdf_filename}")
            
            # Upload PDF to Firebase Storage
            print(f"\n☁️ Uploading PDF report to Firebase Storage...")
            pdf_upload_result = await firebase_storage.upload_report(pdf_filename, report_type="daily_sales")
            
            if pdf_upload_result.get("success"):
                firebase_pdf_url = pdf_upload_result.get("public_url")
                print(f"✅ PDF uploaded to Firebase: {firebase_pdf_url}")
            else:
                print(f"❌ PDF upload failed: {pdf_upload_result.get('error')}")
                
            # Upload JSON to Firebase Storage
            print(f"\n☁️ Uploading JSON report to Firebase Storage...")
            json_upload_result = await firebase_storage.upload_report(json_filename, report_type="daily_sales_json")
            
            if json_upload_result.get("success"):
                firebase_json_url = json_upload_result.get("public_url")
                print(f"✅ JSON uploaded to Firebase: {firebase_json_url}")
            else:
                print(f"❌ JSON upload failed: {json_upload_result.get('error')}")
        else:
            print(f"❌ PDF generation failed: {pdf_result.get('message')}")
            
        # Create a summary for frontend comparison
        frontend_summary = {
            "report_type": "daily_sales",
            "date": today,
            "user_id": user_id,
            "summary": {
                "total_sales": report_data["financial_summary"]["total_sales"],
                "total_transactions": report_data["financial_summary"]["transaction_count"],
                "net_profit": report_data["financial_summary"]["net_profit"],
                "top_selling_products": report_data["top_products"][:3] if report_data["top_products"] else [],
            },
            "status": "generated",
            "files": {
                "json_report": firebase_json_url,
                "pdf_report": firebase_pdf_url,
                "download_url": firebase_pdf_url,  # Include the download_url for frontend
                "firebase_url": firebase_pdf_url   # Include the firebase_url for frontend
            }
        }
        
        # Save frontend summary to temp file
        frontend_filename = os.path.join(temp_dir, f"frontend_report_summary_{today}.json")
        with open(frontend_filename, 'w') as f:
            json.dump(frontend_summary, f, indent=2, default=str)
        print(f"\n🌐 Frontend summary saved to temporary location: {frontend_filename}")
        
        # Upload frontend summary to Firebase
        frontend_upload_result = await firebase_storage.upload_report(frontend_filename, report_type="frontend_summary")
        frontend_firebase_url = None
        if frontend_upload_result.get("success"):
            frontend_firebase_url = frontend_upload_result.get("public_url")
            print(f"✅ Frontend summary uploaded to Firebase: {frontend_firebase_url}")
        else:
            print(f"❌ Frontend summary upload failed: {frontend_upload_result.get('error')}")
        
        print(f"\n📋 Report Summary:")
        print(f"   📅 Period: {today}")
        print(f"   💰 Sales: ${report_data['financial_summary']['total_sales']:.2f}")
        print(f"   📊 Transactions: {report_data['financial_summary']['transaction_count']}")
        print(f"   💵 Profit: ${report_data['financial_summary']['net_profit']:.2f}")
        print(f"   📄 Firebase URLs (for frontend):")
        print(f"      • JSON Report: {firebase_json_url}")
        print(f"      • PDF Report: {firebase_pdf_url}")
        print(f"      • Frontend Summary: {frontend_firebase_url}")
        
        # Clean up temporary files
        try:
            for temp_file in [json_filename, pdf_filename, frontend_filename]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            print(f"\n🧹 Temporary files cleaned up successfully")
        except Exception as e:
            print(f"⚠️ Warning: Failed to clean up temporary files: {e}")
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        
        # Print additional debugging information
        print("\n🔍 Debug info:")
        print(f"   • Working directory: {os.getcwd()}")
        print(f"   • User ID: {user_id}")
        print(f"   • Firebase service available: {'Yes' if 'firebase_admin' in sys.modules else 'No'}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate a sales report for a specific user and date')
    parser.add_argument('--user_id', '-u', required=True, 
                        help='User ID to generate report for (required)')
    parser.add_argument('--date', '-d', 
                        help='Date in YYYY-MM-DD format (defaults to today)')
    parser.add_argument('--debug', action='store_true', 
                        help='Enable verbose debug output')
    
    args = parser.parse_args()
    
    # Run the report generator with command line arguments
    asyncio.run(generate_sales_report(
        user_id=args.user_id,
        date=args.date,
        debug=args.debug
    ))
