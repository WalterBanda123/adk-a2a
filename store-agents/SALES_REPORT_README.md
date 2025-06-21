# Sales Report Generator

This tool generates daily sales reports for users and uploads them to Firebase Storage.

## Features

- Generates detailed financial reports with sales, expenses, and metrics
- Supports different data formats and field names
- Uploads reports to Firebase Storage for accessibility
- Includes detailed debug output to help diagnose data issues
- Works with various Firestore collection structures
- Supports both `user_id` and `userId` field formats

## Command-Line Usage

```bash
python generate_sales_report.py --user_id=USER_ID [--date=YYYY-MM-DD] [--debug]
```

### Required Arguments

- `--user_id` or `-u`: User ID to generate the report for (required)

### Optional Arguments

- `--date` or `-d`: Date in YYYY-MM-DD format (defaults to today)
- `--debug`: Enable verbose debug output to diagnose issues

## Examples

Generate a report for today:

```bash
python generate_sales_report.py --user_id=user_123
```

Generate a report for a specific date with debug output:

```bash
python generate_sales_report.py --user_id=user_123 --date=2025-06-20 --debug
```

## Data Collection

The report generator looks for data in the following Firestore collections:

- `transactions`: Main transactions collection
- `sales`: Sales-specific records
- `records`: Alternative transaction records
- `business_transactions`: Business-specific transactions

The script checks both `user_id` and `userId` fields to ensure it finds all relevant records.

## Debugging Zero Values

If your report shows zero values, use the `--debug` flag to diagnose issues:

```bash
python generate_sales_report.py --user_id=user_123 --debug
```

Common causes for zero values:

1. Incorrect user ID
2. No data for the specified date
3. Data using different field names than expected
4. Data stored in different collections
5. Data format not matching the expected structure

The debug output will help pinpoint the exact issue.

## File Output

All reports are uploaded to Firebase Storage and temporary local files are removed. The script returns:

- A JSON URL for API access
- A PDF URL for human-readable reports
- A frontend summary URL for integration

## Integration with Frontend

Frontend applications should use the `firebase_url` or `download_url` fields in the API response:

```json
{
  "download_url": "https://storage.googleapis.com/...",
  "firebase_url": "https://storage.googleapis.com/...",
  "message": "Report generated successfully"
}
```

## Troubleshooting

If you encounter issues:

1. Check user ID is correct
2. Verify Firestore connection is working
3. Use --debug flag to get detailed output
4. Ensure Firebase Storage configuration is correct
5. Check that data exists for the specified date range
