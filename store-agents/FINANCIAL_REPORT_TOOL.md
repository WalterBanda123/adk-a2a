# Financial Report Tool for Store Assistant Agent

## Overview

The Financial Report Tool is a comprehensive PDF report generator that has been integrated into the `store_assistant` agent. It allows business owners in Zimbabwe to generate professional financial reports for their businesses with simple commands.

## Features

### 🔧 Technical Capabilities

- **Flexible Time Periods**: Supports various time periods including 'today', 'this week', 'this month', 'last month', '7 days', '30 days', etc.
- **Comprehensive Data Retrieval**: Automatically fetches sales, expenses, transactions, and inventory data from Firebase
- **Professional PDF Generation**: Creates well-formatted PDF reports using ReportLab
- **Multilingual Support**: Ready for English, Shona, and Ndebele (following user preferences)
- **Error Handling**: Gracefully handles missing data and provides helpful error messages

### 📊 Report Contents

Each generated financial report includes:

1. **Header Section**

   - Business name and owner information
   - Report period and generation date
   - Business type and location

2. **Executive Summary**

   - Plain language overview of financial performance
   - Key insights in simple terms for non-accountants

3. **Financial Metrics Table**

   - Total sales, expenses, profit/loss
   - Profit margin and transaction counts
   - "What this means" explanations for each metric

4. **Detailed Breakdowns**

   - Sales transactions listing
   - Expenses breakdown
   - Sample transactions with dates and descriptions

5. **Business Insights & Recommendations**
   - Personalized advice based on performance
   - General business tips for small traders
   - Actionable recommendations for improvement

## How It Works

### For Users

Users can request reports using natural language:

- "Generate a financial report for this month"
- "I need a report for the last 7 days"
- "How is my business doing this week?"
- "Create a financial summary for today"

### For the Agent

The agent workflow:

1. User requests a financial report
2. Agent uses `get_user_info` tool to get user context
3. Agent calls `generate_financial_report` tool with user_id and period
4. Tool generates PDF and returns summary data
5. Agent provides conversational response with key insights

## Installation & Setup

### Required Dependencies

```bash
pip install reportlab firebase-admin python-dotenv
```

### Files Added/Modified

1. **New Files**:

   - `common/financial_service.py` - Handles database queries and financial calculations
   - `common/pdf_report_generator.py` - Creates professional PDF reports
   - `agents/assistant/tools/financial_report_tool.py` - Tool integration for the agent

2. **Modified Files**:
   - `agents/assistant/agent.py` - Added financial report tool and updated instructions

### Database Collections

The tool queries these Firebase collections:

- `transactions` - General business transactions
- `sales` - Sales records
- `expenses` - Expense records
- `inventory` - Inventory/products data
- `users`/`profiles` - User information
- `stores` - Business/store information

## Usage Examples

### Basic Report Generation

```python
# Through the agent tool
result = await financial_report_tool.func(
    user_id="user123",
    period="this month",
    include_insights=True
)
```

### Supported Time Periods

- `"today"` - Today's transactions
- `"yesterday"` - Yesterday's data
- `"this week"` - Current week (Monday to now)
- `"last week"` - Previous week (Monday to Sunday)
- `"this month"` - Current month (1st to now)
- `"last month"` - Previous month
- `"7 days"` - Last 7 days
- `"30 days"` - Last 30 days
- Custom formats like `"14 days"`, `"60 days"`

## File Storage

### Report Location

- Reports are saved in the `reports/` directory
- Filename format: `{BusinessName}_{period}_{timestamp}.pdf`
- Example: `General_Store_this_month_20250609_092017.pdf`

### Report Access

- PDF files can be shared with users
- Files can be stored for historical reference
- Easy to email or share via messaging apps

## Agent Integration

### Updated Agent Instructions

The agent now includes specific instructions for financial reporting:

- Always ask users for the desired time period
- Use `get_user_info` first to personalize the experience
- Generate reports with `generate_financial_report` tool
- Provide conversational summaries of the results

### Error Handling

- Missing user: Creates basic report with available data
- No financial data: Generates template with guidance
- Database errors: Provides helpful error messages
- Invalid periods: Defaults to last 7 days

## For Business Owners (End Users)

### What You Get

- **Easy-to-understand reports** in simple language
- **Professional PDF format** suitable for sharing
- **Business insights** tailored to your performance
- **Actionable recommendations** for improvement
- **Historical tracking** with saved reports

### Sample Conversations

```
User: "I need to see how my business is doing this month"
Agent: "I'll generate a financial report for this month. Let me get your business information first..."
[Generates report]
Agent: "Your business made $1,250 in sales this month with $980 in expenses, giving you a profit of $270. That's a healthy 21.6% profit margin! I've created a detailed PDF report with insights and recommendations."

User: "Can you create a weekly report?"
Agent: "I'll create a weekly financial report for you..."
[Generates report]
Agent: "This week you had 15 sales totaling $485. Your main expenses were rent ($120) and inventory ($200). You're showing a small profit of $35. The report suggests ways to increase your average sale amount."
```

## Testing

### Test Script

Run the test to verify everything works:

```bash
python test_financial_report.py
```

### Demo Script

See the tool in action:

```bash
python demo_financial_reports.py
```

## Troubleshooting

### Common Issues

1. **Missing Dependencies**: Install reportlab with `pip install reportlab`
2. **Firebase Connection**: Ensure `firebase-service-account-key.json` is in the right location
3. **No Data**: Tool gracefully handles empty datasets and creates informative reports
4. **Permission Errors**: Ensure the `reports/` directory is writable

### Logs

Check logs for detailed error information:

- Firebase connection status
- Data retrieval results
- PDF generation success/failure

## Future Enhancements

### Possible Improvements

- Charts and graphs in PDF reports
- Email delivery of reports
- Scheduled automatic reports
- Comparison with previous periods
- Industry benchmarking
- Multi-currency support (USD/ZIG)

## Support

For issues or questions about the financial report tool, check:

1. Test scripts for troubleshooting
2. Firebase console for data verification
3. Log outputs for detailed error information

---

**The Financial Report Tool is now fully integrated and ready to help informal traders in Zimbabwe track and understand their business performance!** 🇿🇼📊
