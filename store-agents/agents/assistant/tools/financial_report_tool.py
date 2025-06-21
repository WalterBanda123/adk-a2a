import os
import json
import base64
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from google.adk.tools import FunctionTool
import sys

logger = logging.getLogger(__name__)

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from common.financial_service import FinancialService
from common.pdf_report_generator import PDFReportGenerator
from common.user_service import UserService
from common.firebase_storage_service import FirebaseStorageService

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

        # Initialize Firebase Storage Service
        firebase_storage = FirebaseStorageService(user_id)

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
        
        # Use a temporary directory for the PDF file
        import tempfile
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        business_name = store_info.get('name', 'Business') if store_info else 'Business'
        safe_business_name = "".join(c for c in business_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_business_name = safe_business_name.replace(' ', '_')
        
        filename = f"{safe_business_name}_{period.replace(' ', '_')}_{timestamp}.pdf"
        
        # Create a temporary file
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, filename)
        
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
        
        # Upload the PDF report to Firebase Storage
        upload_result = await firebase_storage.upload_report(output_path, report_type="financial")
        
        if not upload_result.get("success"):
            return {
                "success": False,
                "error": upload_result.get("error", "File upload failed"),
                "message": "Failed to upload PDF report to Firebase Storage"
            }
        
        # Get the public URL of the uploaded PDF
        firebase_url = upload_result.get("public_url") if upload_result and upload_result.get("success") else None
        
        # Clean up temporary file after successful upload
        if firebase_url and os.path.exists(output_path):
            try:
                os.remove(output_path)
                logger.info(f"Temporary file {output_path} removed successfully")
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {output_path}: {e}")
        
        # Both download_url and firebase_url should be the same Firebase URL
        download_url = firebase_url
        
        # Prepare summary with just the necessary information (metrics for logging)
        metrics = financial_data.get('data', {}).get('metrics', {})
        
        # Create a simple summary for status messages
        summary = {
            "business_name": business_name,
            "period": period,
            "download_url": download_url,
            "firebase_url": firebase_url
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
        
        # Create a user-friendly message for the frontend
        # Make sure the message only references the Firebase URL
        status_msg = summary.get('status_message', '')
        
        # Create a user-friendly message that only mentions the Firebase URL
        user_message = (
            f"✅ Financial report generated successfully! {status_msg}\n\n"
            f"Your report is available for viewing and download at this Firebase URL: {firebase_url}\n\n"
            f"IMPORTANT: Please use the firebase_url for accessing your report. This URL works directly in browsers "
            f"and with download managers."
        )
        
        # Return only the essential fields needed by the frontend
        # Ensure both download_url and firebase_url are the Firebase URL
        # and message contains user-friendly information
        return {
            "success": True,
            "download_url": firebase_url,  # Firebase URL for backward compatibility
            "firebase_url": firebase_url,  # Firebase URL is the primary access method
            "message": user_message,
            "report_type": "financial",
            "storage_location": "firebase"  # Flag to indicate this is in Firebase Storage
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
