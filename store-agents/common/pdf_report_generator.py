import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

logger = logging.getLogger(__name__)

class PDFReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the report"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='SubTitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkgreen
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='MetricValue',
            parent=self.styles['Normal'],
            fontSize=12,
            alignment=TA_RIGHT
        ))
    
    def generate_financial_report(self, 
                                user_info: Dict[str, Any], 
                                store_info: Dict[str, Any], 
                                financial_data: Dict[str, Any], 
                                period: str,
                                output_path: str) -> Dict[str, Any]:
        """Generate a comprehensive financial report PDF"""
        try:
            # Create the PDF document
            doc = SimpleDocTemplate(output_path, pagesize=A4, 
                                  rightMargin=72, leftMargin=72, 
                                  topMargin=72, bottomMargin=18)
            
            # Build the story (content)
            story = []
            
            # Title and header
            story.extend(self._create_header(user_info, store_info, period))
            
            # Executive summary
            story.extend(self._create_executive_summary(financial_data))
            
            # Financial metrics overview
            story.extend(self._create_metrics_section(financial_data))
            
            # Detailed breakdowns
            story.extend(self._create_sales_breakdown(financial_data))
            story.extend(self._create_expenses_breakdown(financial_data))
            
            # Insights and recommendations
            story.extend(self._create_insights_section(financial_data, user_info))
            
            # Footer
            story.extend(self._create_footer())
            
            # Build the PDF
            doc.build(story)
            
            return {
                "success": True,
                "file_path": output_path,
                "message": f"Financial report generated successfully for {user_info.get('name', 'Business Owner')}"
            }
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to generate PDF report"
            }
    
    def _create_header(self, user_info: Dict, store_info: Dict, period: str) -> list:
        """Create the report header"""
        story = []
        
        # Main title
        story.append(Paragraph("Business Financial Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        # Business information
        business_name = store_info.get('name', 'Your Business') if store_info else 'Your Business'
        owner_name = user_info.get('name', 'Business Owner')
        
        story.append(Paragraph(f"<b>Business:</b> {business_name}", self.styles['Normal']))
        story.append(Paragraph(f"<b>Owner:</b> {owner_name}", self.styles['Normal']))
        story.append(Paragraph(f"<b>Report Period:</b> {period}", self.styles['Normal']))
        story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", self.styles['Normal']))
        
        if store_info:
            if store_info.get('location'):
                story.append(Paragraph(f"<b>Location:</b> {store_info.get('location')}", self.styles['Normal']))
            if store_info.get('type'):
                story.append(Paragraph(f"<b>Business Type:</b> {store_info.get('type')}", self.styles['Normal']))
        
        story.append(Spacer(1, 30))
        
        return story
    
    def _create_executive_summary(self, financial_data: Dict) -> list:
        """Create executive summary section"""
        story = []
        metrics = financial_data.get('data', {}).get('metrics', {})
        
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        
        # Key metrics summary
        total_sales = metrics.get('total_sales', 0)
        total_expenses = metrics.get('total_expenses', 0)
        profit_loss = metrics.get('profit_loss', 0)
        profit_margin = metrics.get('profit_margin', 0)
        
        # Format currency (assuming USD, but can be adapted)
        currency_symbol = "$"
        
        summary_text = f"""
        <b>Financial Performance Overview:</b><br/>
        Your business generated <b>{currency_symbol}{total_sales:,.2f}</b> in total sales during this period.
        Operating expenses totaled <b>{currency_symbol}{total_expenses:,.2f}</b>, resulting in a 
        {'<font color="green"><b>profit</b></font>' if profit_loss >= 0 else '<font color="red"><b>loss</b></font>'} 
        of <b>{currency_symbol}{abs(profit_loss):,.2f}</b>.<br/><br/>
        
        Your profit margin is <b>{profit_margin:.1f}%</b>, which means for every dollar you earn, 
        you keep {abs(profit_margin)/100:.2f} cents as profit after covering expenses.
        """
        
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_metrics_section(self, financial_data: Dict) -> list:
        """Create financial metrics section with table"""
        story = []
        metrics = financial_data.get('data', {}).get('metrics', {})
        
        story.append(Paragraph("Key Financial Metrics", self.styles['SectionHeader']))
        
        # Create metrics table
        data = [
            ['Metric', 'Value', 'What This Means'],
            ['Total Sales', f"${metrics.get('total_sales', 0):,.2f}", 'Money earned from selling products/services'],
            ['Total Expenses', f"${metrics.get('total_expenses', 0):,.2f}", 'Money spent on business operations'],
            ['Profit/Loss', f"${metrics.get('profit_loss', 0):,.2f}", 'Money left after paying all expenses'],
            ['Profit Margin', f"{metrics.get('profit_margin', 0):.1f}%", 'Percentage of sales kept as profit'],
            ['Number of Sales', str(metrics.get('sales_count', 0)), 'Total number of sales transactions'],
            ['Average Sale', f"${metrics.get('average_transaction_value', 0):,.2f}", 'Average amount per sale'],
        ]
        
        table = Table(data, colWidths=[2*inch, 1.5*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_sales_breakdown(self, financial_data: Dict) -> list:
        """Create sales breakdown section"""
        story = []
        sales_data = financial_data.get('data', {}).get('sales', [])
        
        story.append(Paragraph("Sales Breakdown", self.styles['SectionHeader']))
        
        if not sales_data:
            story.append(Paragraph("No sales data available for this period.", self.styles['Normal']))
            story.append(Spacer(1, 20))
            return story
        
        # Create sales summary table
        story.append(Paragraph(f"Total of {len(sales_data)} sales transactions recorded:", self.styles['Normal']))
        story.append(Spacer(1, 10))
        
        # Sample sales data (show first 10 transactions)
        sample_sales = sales_data[:10]
        sales_table_data = [['Date', 'Description', 'Amount']]
        
        for sale in sample_sales:
            date = sale.get('date', 'N/A')
            if isinstance(date, datetime):
                date = date.strftime('%m/%d/%Y')
            
            description = sale.get('description', sale.get('product', sale.get('item', 'Sale')))
            amount = sale.get('amount', sale.get('total', sale.get('value', 0)))
            
            sales_table_data.append([
                str(date),
                str(description)[:30] + ('...' if len(str(description)) > 30 else ''),
                f"${amount:,.2f}" if isinstance(amount, (int, float)) else str(amount)
            ])
        
        if len(sales_data) > 10:
            sales_table_data.append(['...', f'and {len(sales_data) - 10} more transactions', '...'])
        
        sales_table = Table(sales_table_data, colWidths=[1.5*inch, 3*inch, 1.5*inch])
        sales_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        story.append(sales_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_expenses_breakdown(self, financial_data: Dict) -> list:
        """Create expenses breakdown section"""
        story = []
        expenses_data = financial_data.get('data', {}).get('expenses', [])
        
        story.append(Paragraph("Expenses Breakdown", self.styles['SectionHeader']))
        
        if not expenses_data:
            story.append(Paragraph("No expense data available for this period.", self.styles['Normal']))
            story.append(Spacer(1, 20))
            return story
        
        # Create expenses summary table
        story.append(Paragraph(f"Total of {len(expenses_data)} expense transactions recorded:", self.styles['Normal']))
        story.append(Spacer(1, 10))
        
        # Sample expenses data (show first 10 transactions)
        sample_expenses = expenses_data[:10]
        expenses_table_data = [['Date', 'Description', 'Amount']]
        
        for expense in sample_expenses:
            date = expense.get('date', 'N/A')
            if isinstance(date, datetime):
                date = date.strftime('%m/%d/%Y')
            
            description = expense.get('description', expense.get('category', expense.get('item', 'Expense')))
            amount = expense.get('amount', expense.get('total', expense.get('value', 0)))
            
            expenses_table_data.append([
                str(date),
                str(description)[:30] + ('...' if len(str(description)) > 30 else ''),
                f"${amount:,.2f}" if isinstance(amount, (int, float)) else str(amount)
            ])
        
        if len(expenses_data) > 10:
            expenses_table_data.append(['...', f'and {len(expenses_data) - 10} more transactions', '...'])
        
        expenses_table = Table(expenses_table_data, colWidths=[1.5*inch, 3*inch, 1.5*inch])
        expenses_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.mistyrose),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        story.append(expenses_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_insights_section(self, financial_data: Dict, user_info: Dict) -> list:
        """Create business insights and recommendations"""
        story = []
        metrics = financial_data.get('data', {}).get('metrics', {})
        
        story.append(Paragraph("Business Insights & Recommendations", self.styles['SectionHeader']))
        
        profit_loss = metrics.get('profit_loss', 0)
        profit_margin = metrics.get('profit_margin', 0)
        sales_count = metrics.get('sales_count', 0)
        avg_transaction = metrics.get('average_transaction_value', 0)
        
        insights = []
        
        # Profitability insights
        if profit_loss > 0:
            insights.append(f"✅ <b>Good News!</b> Your business is profitable with ${profit_loss:,.2f} in profit.")
            if profit_margin > 20:
                insights.append("✅ <b>Excellent!</b> Your profit margin is very healthy at {:.1f}%.".format(profit_margin))
            elif profit_margin > 10:
                insights.append("✅ <b>Good!</b> Your profit margin of {:.1f}% is solid.".format(profit_margin))
            else:
                insights.append("⚠️ <b>Watch Out:</b> Your profit margin of {:.1f}% could be improved.".format(profit_margin))
        else:
            insights.append(f"❌ <b>Attention Needed:</b> Your business had a loss of ${abs(profit_loss):,.2f}.")
            insights.append("💡 <b>Recommendation:</b> Review your expenses and consider ways to increase sales or reduce costs.")
        
        # Sales insights
        if sales_count > 0:
            insights.append(f"📊 You completed {sales_count} sales with an average of ${avg_transaction:,.2f} per transaction.")
            if avg_transaction < 10:
                insights.append("💡 <b>Opportunity:</b> Consider bundling products or upselling to increase average transaction value.")
            elif avg_transaction > 50:
                insights.append("✅ <b>Great!</b> Your average transaction value is quite good.")
        else:
            insights.append("❌ <b>No sales recorded</b> for this period. Focus on marketing and customer acquisition.")
        
        # General recommendations
        insights.extend([
            "",
            "<b>General Recommendations for Small Business Success:</b>",
            "• Keep detailed records of all income and expenses",
            "• Review your reports weekly to track progress",
            "• Focus on your most profitable products or services",
            "• Build relationships with regular customers",
            "• Consider seasonal trends in your planning",
            "• Set aside money for emergencies and growth",
        ])
        
        for insight in insights:
            if insight:
                story.append(Paragraph(insight, self.styles['Normal']))
                story.append(Spacer(1, 8))
        
        return story
    
    def _create_footer(self) -> list:
        """Create report footer"""
        story = []
        
        story.append(Spacer(1, 30))
        story.append(Paragraph("_" * 80, self.styles['Normal']))
        story.append(Spacer(1, 10))
        
        footer_text = """
        <i>This report was generated by your Smart Business Assistant to help you understand your business performance. 
        The insights provided are based on your recorded data and general business principles. 
        For complex financial decisions, consider consulting with a business advisor.</i>
        """
        
        story.append(Paragraph(footer_text, self.styles['Normal']))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", 
                              self.styles['Normal']))
        
        return story
