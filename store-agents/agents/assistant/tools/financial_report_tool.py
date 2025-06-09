import os
import json
from typing import Dict, Any
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
    financial_service: FinancialService = None,
    pdf_generator: PDFReportGenerator = None,
    user_service: UserService = None
) -> Dict[str, Any]:
    """Generate a comprehensive financial report for a business"""
    try:
        # Parse the period to get start and end dates
        start_date, end_date = financial_service.parse_date_period(period)
        
        # Get user and store information
        user_info = await user_service.get_user_info(user_id)
        store_info = await user_service.get_store_info(user_id)
        
        if not user_info:
            return {
                "success": False,
                "error": "User not found",
                "message": f"Could not find user information for user ID: {user_id}"
            }
        
        # Get financial data
        financial_data = await financial_service.get_financial_data(user_id, start_date, end_date)
        
        if not financial_data.get("success"):
            return {
                "success": False,
                "error": financial_data.get("error", "Unknown error"),
                "message": "Failed to retrieve financial data"
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
        pdf_result = pdf_generator.generate_financial_report(
            user_info=user_info,
            store_info=store_info,
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
        
        # Create a human-friendly summary
        summary = {
            "report_generated": True,
            "file_path": output_path,
            "period": period,
            "business_name": business_name,
            "owner_name": user_info.get('name', 'Business Owner'),
            "key_metrics": {
                "total_sales": f"${metrics.get('total_sales', 0):,.2f}",
                "total_expenses": f"${metrics.get('total_expenses', 0):,.2f}",
                "profit_loss": f"${metrics.get('profit_loss', 0):,.2f}",
                "profit_margin": f"{metrics.get('profit_margin', 0):.1f}%",
                "transaction_count": metrics.get('sales_count', 0)
            },
            "date_range": {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d")
            }
        }
        
        # Quick business health assessment
        profit_loss = metrics.get('profit_loss', 0)
        if profit_loss > 0:
            summary["business_status"] = "Profitable"
            summary["status_message"] = f"Your business made a profit of ${profit_loss:,.2f} during this period."
        elif profit_loss < 0:
            summary["business_status"] = "Loss"
            summary["status_message"] = f"Your business had a loss of ${abs(profit_loss):,.2f} during this period."
        else:
            summary["business_status"] = "Break-even"
            summary["status_message"] = "Your business broke even during this period."
        
        return {
            "success": True,
            "data": summary,
            "message": f"Financial report successfully generated for {user_info.get('name', 'Business Owner')}. The report covers {period} and has been saved as a PDF."
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
