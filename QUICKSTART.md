# 🚀 Quick Start Guide - Odoo VNPay Order Sync

This guide will help you quickly sync VNPay, VNPayQR, and Thẻ ATM orders from Odoo and issue POS invoices.

## ⚡ 5-Minute Setup

### Step 1: Configure Odoo Connection

Create a `.env` file in the project directory:

```bash
cat > .env << 'ENV'
ODOO_URL=http://your-odoo-server:8069
ODOO_DB=your-database-name
ODOO_USERNAME=your-username
ODOO_PASSWORD=your-password
ENV
```

### Step 2: Install Dependencies

```bash
pip install xmlrpc.client
```

### Step 3: Run Your First Sync

```bash
# Option 1: Use the shell wrapper (easiest)
./run-sync.sh

# Option 2: Use Python directly
python sync_vnpay_orders.py

# Option 3: Dry run to test
python sync_vnpay_orders.py --dry-run --verbose
```

That's it! 🎉

## 📋 Common Tasks

### Sync Today's Orders

```bash
./run-sync.sh
```

### Sync Specific Date

```bash
./run-sync.sh --date 2026-03-31
```

### Dry Run (Test Without Importing)

```bash
./run-sync.sh --dry-run --verbose
```

### Extract Only (No Invoice Generation)

```bash
./run-sync.sh --extract-only
```

### Import Existing File

```bash
./run-sync.sh --import-only --input orders-extracted.json
```

## 📊 What Happens?

The sync process will:

1. ✅ **Connect** to your Odoo server
2. 🔍 **Find** orders with VNPay, VNPayQR, and Thẻ ATM payments
3. 📦 **Extract** order details (customer, products, payments)
4. 📄 **Generate** invoice data ready for import
5. 💾 **Save** everything to JSON files

### Output Files

- `orders-extracted.json` - Raw orders from Odoo
- `invoices-orders-extracted.json` - Mapped invoice data

## 🔧 Customization

### Change Payment Methods

```bash
./run-sync.sh --payment-methods "VNPay" "VNPayQR" "Thẻ ATM" "Momo"
```

### Specify Output File

```bash
./run-sync.sh --output my-orders.json
```

### Verbose Output

```bash
./run-sync.sh --verbose
```

## 🐛 Troubleshooting

### Connection Failed

```bash
# Test Odoo connection
curl http://your-odoo-server:8069/xmlrpc/2/common

# Check environment variables
cat .env
```

### No Orders Found

```bash
# Enable verbose logging
./run-sync.sh --verbose

# Check if payment methods exist in Odoo
# Go to: POS → Configuration → Payment Methods
```

## 📚 More Information

See [README_VNPAY_SYNC.md](README_VNPAY_SYNC.md) for detailed documentation.

## 🤝 Need Help?

1. Check the logs with `--verbose`
2. Review the output JSON files
3. Verify your Odoo configuration
4. Check payment methods exist in Odoo

---

**Happy syncing!** 🎊
