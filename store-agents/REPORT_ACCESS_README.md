# Report Access Guide

## Important: Report Storage Changes

All reports are now stored in Firebase Storage instead of the local filesystem. This change improves security, reliability, and accessibility of reports from multiple devices.

## Accessing Reports

### For Frontend Developers

1. **Use Firebase URLs**: Always use the `firebase_url` field from the report response to access reports:

   ```json
   {
     "download_url": "https://storage.googleapis.com/...",
     "firebase_url": "https://storage.googleapis.com/...",
     "message": "Report generated successfully!",
     "success": true
   }
   ```

2. **Avoid Local Paths**: The backend no longer serves files from local paths like `/reports/filename.pdf`. All such requests will receive a `410 Gone` status code.

3. **Update UI References**: If your UI still refers to local file paths like `/reports/filename.pdf`, update them to use the `firebase_url` instead.

### For API Users

The report generation tools now return a simplified response structure:

```json
{
  "success": true,
  "download_url": "https://storage.googleapis.com/...",
  "firebase_url": "https://storage.googleapis.com/...",
  "message": "Report generated successfully!",
  "report_type": "financial",
  "storage_location": "firebase"
}
```

Both `download_url` and `firebase_url` point to the same Firebase Storage URL for backward compatibility.

## Running The Report Generator

Use the command line tool with these arguments:

```bash
python generate_sales_report.py --user_id="<USER_ID>" [--date="YYYY-MM-DD"] [--debug]
```

### Arguments

- `--user_id` or `-u`: User ID to generate the report for (required)
- `--date` or `-d`: Date for the report in YYYY-MM-DD format (defaults to today)
- `--debug`: Enable detailed debug output to help diagnose issues

### Debug Mode

If reports show zero values, run with the `--debug` flag to see:

- Which collections are being queried (transactions, sales, records, business_transactions)
- Which fields are checked for amounts (amount, price, total, value, etc.)
- Sample data from transactions/sales if available
- Detailed breakdown of where values are calculated from

### Common Issues

If reports show zero values, check:

1. User ID is correct and exists in the database
2. Data exists for the specified date
3. Data is stored in the expected collections
4. Amount fields use the expected names
5. Date format in the database matches the expected format

## Report Storage Policy

- Reports are temporarily stored on disk during generation
- After successful upload to Firebase Storage, local files are deleted
- The Firebase Storage URL is the only official way to access reports
- Local file serving has been completely disabled
