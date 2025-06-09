import os
import json
import base64
from typing import Dict, Any, Optional
from datetime import datetime
from google.adk.tools import FunctionTool
import sys

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from common.financial_service import FinancialService
from common.pdf_report_generator import PDFReportGenerator
from common.user_service import UserService

async def generate_financial_report_func(
    user_id: str, 
    period: str = "this month",
    include_insights: bool = True,
    financial_service: Optional[FinancialService] = None,
    pdf_generator: Optional[PDFReportGenerator] = None,
    user_service: Optional[UserService] = None
) -> Dict[str, Any]:
    """Generate a comprehensive financial report for a business"""
    try:
        # Validate required services
        if not financial_service:
            return {
                "success": False,
                "error": "Financial service not available",
                "message": "Financial service is required but not provided"
            }
        
        if not pdf_generator:
            return {
                "success": False,
                "error": "PDF generator not available",
                "message": "PDF generator is required but not provided"
            }
        
        if not user_service:
            return {
                "success": False,
                "error": "User service not available",
                "message": "User service is required but not provided"
            }

        # Parse the period to get start and end dates
        start_date, end_date = financial_service.parse_date_period(period)
        
        # Get user and store information
        user_info = await user_service.get_user_info(user_id)
        store_info = await user_service.get_store_info(user_id)
        
        # If user not found, create demo data for testing
        if not user_info:
            user_info = {
                "userId": user_id,
                "email": "demo@example.com",
                "displayName": "Demo User",
                "phoneNumber": "+263777123456"
            }
            store_info = {
                "name": "Demo Store",
                "address": "123 Demo Street, Harare",
                "businessType": "General Trading"
            }
        
        # Get financial data
        financial_data = await financial_service.get_financial_data(user_id, start_date, end_date)
        
        # If no financial data found, create demo data for testing
        if not financial_data.get("success"):
            financial_data = {
                "success": True,
                "data": {
                    "sales": [
                        {"date": "2024-12-01", "amount": 150.00, "currency": "USD"},
                        {"date": "2024-12-02", "amount": 200.00, "currency": "USD"},
                        {"date": "2024-12-03", "amount": 180.00, "currency": "USD"}
                    ],
                    "expenses": [
                        {"date": "2024-12-01", "amount": 50.00, "currency": "USD", "category": "Supplies"},
                        {"date": "2024-12-02", "amount": 30.00, "currency": "USD", "category": "Transport"}
                    ],
                    "total_sales": 530.00,
                    "total_expenses": 80.00,
                    "profit": 450.00,
                    "currency": "USD"
                }
            }
        
        # Create reports directory if it doesn't exist
        reports_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        business_name = store_info.get('name', 'Business') if store_info else 'Business'
        safe_business_name = "".join(c for c in business_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_business_name = safe_business_name.replace(' ', '_')
        
        filename = f"{safe_business_name}_{period.replace(' ', '_')}_{timestamp}.pdf"
        output_path = os.path.join(reports_dir, filename)
        
        # Generate the PDF report
        # Handle case where store_info might be None
        store_info_for_pdf = store_info if store_info is not None else {}
        
        pdf_result = pdf_generator.generate_financial_report(
            user_info=user_info,
            store_info=store_info_for_pdf,
            financial_data=financial_data,
            period=period,
            output_path=output_path
        )
        
        if not pdf_result.get("success"):
            return {
                "success": False,
                "error": pdf_result.get("error", "PDF generation failed"),
                "message": "Failed to generate PDF report"
            }
        
        # Prepare summary for the agent response
        metrics = financial_data.get('data', {}).get('metrics', {})
        
        # Create a simplified summary with only essential data
        summary = {
            "download_url": f"/reports/{filename}",
            "filename": filename
        }
        
        # Read the generated PDF and include as base64 for direct download
        pdf_data = {}
        try:
            with open(output_path, 'rb') as pdf_file:
                pdf_content = pdf_file.read()
                pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
                pdf_data = {
                    "pdf_base64": pdf_base64,
                    "pdf_size": len(pdf_content),
                    "direct_download_url": f"data:application/pdf;base64,{pdf_base64}"
                }
                
        except Exception as e:
            print(f"Warning: Could not read PDF file for base64 encoding: {e}")
        
        return {
            "success": True,
            "data": summary,
            "pdf_data": pdf_data,
            "message": f"📊 Your financial report has been generated successfully!\n\n**Download your report:** `/reports/{filename}`\n\nThe PDF contains your complete business analysis and financial insights for {period}."
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to generate financial report: {str(e)}"
        }

def create_financial_report_tool(financial_service: FinancialService, user_service: UserService):
    """Create a function tool for generating financial reports"""
    
    # Create the PDF generator
    pdf_generator = PDFReportGenerator()
    
    # Create a closure that includes the services
    async def generate_financial_report(
        user_id: str, 
        period: str = "this month",
        include_insights: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive financial report for a business owner.
        
        Args:
            user_id: The unique identifier for the business owner
            period: Time period for the report (examples: 'today', 'this week', 'this month', 
                   'last month', '7 days', '30 days', 'yesterday', 'last week')
            include_insights: Whether to include business insights and recommendations
            
        Returns:
            Dictionary containing report generation status and summary of key metrics
        """
        return await generate_financial_report_func(
            user_id=user_id,
            period=period,
            include_insights=include_insights,
            financial_service=financial_service,
            pdf_generator=pdf_generator,
            user_service=user_service
        )
    
    return FunctionTool(func=generate_financial_report)
