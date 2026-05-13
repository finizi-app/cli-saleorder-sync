# Odoo VNPay Order Sync - POS Invoice Generator

Extract today's orders from Odoo for VNPay, VNPayQR, and Thẻ ATM payment methods and issue POS invoices.

## 📋 Overview

This toolkit consists of three Python scripts that work together to:

1. **Extract** orders from Odoo for specific payment methods (VNPay, VNPayQR, Thẻ ATM)
2. **Import** and process the extracted orders
3. **Issue** POS invoices

## 🚀 Quick Start

### Prerequisites

```bash
# Install dependencies
pip install xmlrpc.client

# Or use the project's requirements
pip install -r requirements.txt
```

### Environment Configuration

Set up your Odoo connection details:

```bash
export ODOO_URL="http://your-odoo-server:8069"
export ODOO_DB="your-database-name"
export ODOO_USERNAME="your-username"
export ODOO_PASSWORD="your-password"
```

Or create a `.env` file:

```bash
# .env
ODOO_URL=http://localhost:8069
ODOO_DB=prod
ODOO_USERNAME=admin
ODOO_PASSWORD=admin
```

## 📜 Scripts

### 1. `extract_today_orders.py`

Extracts today's orders from Odoo for specified payment methods.

```bash
# Extract today's orders
python extract_today_orders.py

# Extract orders for a specific date
python extract_today_orders.py --date 2026-03-31

# Specify custom output file
python extract_today_orders.py --output vnpay-orders-2026-03-31.json

# Specify payment methods
python extract_today_orders.py --payment-methods VNPay VNPayQR

# Verbose output
python extract_today_orders.py --verbose
```

**Output:** JSON file with extracted orders including:
- Order details (ID, name, date, amounts)
- Customer information
- Order lines with products
- Payment details

### 2. `import_and_issue_invoices.py`

Imports extracted orders and generates POS invoice data.

```bash
# Import from extracted orders
python import_and_issue_invoices.py --input orders-extracted.json

# Dry run (validate without importing)
python import_and_issue_invoices.py --input orders-extracted.json --dry-run

# Specify output file
python import_and_issue_invoices.py --input orders-extracted.json --output invoices.json
```

**Output:** JSON file with mapped invoice data ready for import to Odoo.

### 3. `sync_vnpay_orders.py` (Main Script)

Orchestrates the complete workflow: extraction → import → invoice generation.

```bash
# Complete sync (today's orders)
python sync_vnpay_orders.py

# Sync for specific date
python sync_vnpay_orders.py --date 2026-03-31

# Dry run
python sync_vnpay_orders.py --dry-run

# Extract only (skip invoice generation)
python sync_vnpay_orders.py --extract-only

# Import from existing file
python sync_vnpay_orders.py --input orders-extracted.json --import-only

# Verbose output
python sync_vnpay_orders.py --verbose
```

## 📊 Output Files

### Extracted Orders (`orders-extracted.json`)

```json
{
  "extracted_at": "2026-03-31T12:00:00",
  "total_orders": 15,
  "orders": [
    {
      "id": 1234,
      "name": "Order 1234",
      "pos_reference": "POS/2026/03/31/0001",
      "date_order": "2026-03-31 10:30:00",
      "state": "done",
      "amount_total": 500000.0,
      "amount_tax": 50000.0,
      "amount_paid": 500000.0,
      "amount_return": 0.0,
      "partner_id": [123, "Customer Name"],
      "lines_data": [...],
      "payments_data": [...]
    }
  ]
}
```

### Invoice Data (`invoices-orders-extracted.json`)

```json
{
  "generated_at": "2026-03-31T12:05:00",
  "total_invoices": 15,
  "invoices": [
    {
      "order_id": 1234,
      "order_name": "Order 1234",
      "pos_reference": "POS/2026/03/31/0001",
      "date_order": "2026-03-31 10:30:00",
      "state": "done",
      "amount_total": 500000.0,
      "amount_tax": 50000.0,
      "lines": [...],
      "payments": [...]
    }
  ]
}
```

## 🛠️ Configuration

### Payment Methods

Default payment methods: `VNPay`, `VNPayQR`, `Thẻ ATM`

You can customize this list:

```bash
python sync_vnpay_orders.py --payment-methods VNPay VNPayQR "Thẻ ATM" "Momo"
```

### Date Range

- Default: Today (UTC)
- Specific date: `--date YYYY-MM-DD`
- The script extracts all orders from 00:00:00 to 23:59:59 of the specified date

## 📝 Workflow Examples

### Example 1: Daily Sync

```bash
# Run daily sync for today
python sync_vnpay_orders.py

# Or schedule as a cron job
# Run every day at 6 PM
0 18 * * * cd /path/to/odoo-sync && python sync_vnpay_orders.py
```

### Example 2: Backfill Historical Data

```bash
# Extract orders for multiple dates
for date in {2026-03-01..2026-03-31}; do
    python sync_vnpay_orders.py --date $date --output "orders-$date.json"
done
```

### Example 3: Validate Before Importing

```bash
# Extract and validate
python sync_vnpay_orders.py --dry-run --verbose

# Review the output files
# If satisfied, run without --dry-run
python sync_vnpay_orders.py
```

### Example 4: Extract Only

```bash
# Extract orders for manual processing
python sync_vnpay_orders.py --extract-only --output today-orders.json

# Then process manually or with other tools
```

## 🔧 Troubleshooting

### Connection Issues

```bash
# Verify Odoo connection
curl http://your-odoo-server:8069/xmlrpc/2/common

# Check credentials
echo $ODOO_URL
echo $ODOO_DB
echo $ODOO_USERNAME
```

### No Orders Found

```bash
# Enable verbose logging to see what's happening
python sync_vnpay_orders.py --verbose

# Check if payment methods exist in Odoo
# You can verify in Odoo: POS → Configuration → Payment Methods
```

### Import Issues

```bash
# Use dry-run mode first
python import_and_issue_invoices.py --input orders.json --dry-run --verbose

# Check the JSON output for any validation errors
```

## 📚 Additional Resources

- Odoo XML-RPC API: https://www.odoo.com/documentation/master/api/external.html
- Python xmlrpc.client: https://docs.python.org/3/library/xmlrpc.client.html

## 🤝 Contributing

Feel free to extend these scripts for your specific needs:
- Add more payment methods
- Customize invoice formats
- Add additional validation
- Integrate with other systems

## 📄 License

These scripts are provided as-is for your Odoo integration needs.
