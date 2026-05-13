---
name: patedeli-odoo-manager
description: Manage PateDeli Odoo POS operations: export/import orders, match receipts to products, sync with B4B. Trigger with "Use my patedeli odoo" or Odoo/POS/B4B keywords. Maintains product matching memory via JSON lookup for receipt scanning and purchase order imports.
allowed-tools: []
license: MIT
metadata:
  version: 1.0.0
  author: PateDeli
  odoo-version: "16.0"
  requires-env: true
---

# PateDeli Odoo Manager

## Iron Law
**NEVER import purchase orders without user approval.** Always show summary and ask "Should I proceed with import?" before creating any Odoo records. Product matching errors must halt execution and ask user — never guess.

## Quick Start Checklist

- [ ] ⛔ Verify `.env` file has Odoo credentials (ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)
- [ ] ⛔ Verify B4B credentials if syncing (B4B_API_URL, B4B_TOKEN, B4B_ENTITY_ID)
- [ ] ⛔ Check product matching memory exists: `.claude/skills/patedeli-odoo-manager/assets/product-mapping.json`
- [ ] Read main workflow below before executing

## Main Workflow

### Step 1: Understand Request ⚠️ REQUIRED
What operation is requested?

**A. Export POS Orders**
- Export today's orders to JSON
- Filter by payment method (VNPAY, VNPayQR, ATM, Cash, etc.)
- Filter by date range
- Output: JSON file for downstream operations

**B. Import to B4B**
- Read exported orders JSON
- Map to B4B tax-aware format
- Create sale orders
- Generate POS invoices

**C. Import Purchase Order from Invoice**
- Extract invoice data (PDF/image)
- Match vendor to Odoo partner
- Match line items to Odoo products
- Show summary for approval
- Create purchase order in Odoo

**D. Match Receipt to Products**
- Scan receipt/image
- Extract line items
- Match to products using memory lookup
- Ask for unmatched items
- Update product mapping memory

**E. Analyze Sales Data**
- Calculate total sales by payment method
- Show order statistics
- Export analysis report

### Step 2: Execute Operation

**For Exporting Orders:**
1. Load `references/odoo-export-workflow.md` for field mappings
2. Use `scripts/export_orders.py` with appropriate filters
3. Output to project root (e.g., `odoo-orders-2026-03-26-vnpay.json`)
4. Report order count and total amount

**For Importing to B4B:**
1. Load `references/b4b-mapping-guide.md` for tax-aware format
2. Use existing `src/b4b_import_cli.py`
3. Generate POS invoices unless `--no-invoice` flag
4. Log to `import-log-YYYY-MM-DD.jsonl`

**For Purchase Order Import:**
1. Load `references/purchase-order-workflow.md`
2. Extract invoice data (use ai-multimodal skill for images)
3. Match vendor:
   - Search Odoo partners by name/tax ID
   - If multiple found: Ask user "Found N vendors: [list]. Which one?"
   - If not found: Ask "Create new vendor '[name]'?"
4. Match products:
   - Check `assets/product-mapping.json` first
   - For unmatched items: Search Odoo products by name/code
   - If multiple found: Ask user to select
   - If not found: Ask "Skip item '[name]' or create new product?"
5. Build summary: vendor, line items, totals, unmatched items
6. Ask: "Should I proceed with import?"
7. If approved: Use `scripts/create_purchase_order.py`

**For Receipt Matching:**
1. Use ai-multimodal skill to extract line items from receipt
2. For each item:
   - Check `assets/product-mapping.json` for exact match
   - If not found: Search Odoo products by name
   - If 1 match: Auto-confirm and update mapping
   - If multiple: Ask user to select, then update mapping
   - If none: Ask user to skip or create product
3. Save updated mapping to `assets/product-mapping.json`

### Step 3: Confirmation Gates ⚠️ REQUIRED

**MUST ASK before:**
- Creating purchase orders: "Import N purchase order items from [vendor] for [total]? (y/n)"
- Creating new vendors: "Create new vendor '[name]' with tax ID [id]? (y/n)"
- Creating new products: "Create new product '[name]' with default category? (y/n)"
- Modifying product mapping: "Add mapping '[receipt item]' → '[odoo product]'? (y/n)"

**NEED NOT ASK for:**
- Reading data from Odoo
- Exporting orders to JSON
- Searching/matching operations
- Showing summaries/reports

### Step 4: Update Memory

After each product matching operation:
```bash
# Update product mapping memory
python3 .claude/skills/patedeli-odoo-manager/scripts/update_product_mapping.py \
  --receipt-item "Cà phê sữa đá" \
  --odoo-product-id 2489 \
  --odoo-product-name "(D7) Cà Phê Sữa Đá"
```

Memory file location: `assets/product-mapping.json`

### Step 5: Report Results

Always provide:
- Operation performed
- Number of records processed
- Total amounts (if applicable)
- Any errors or warnings
- Next steps (if applicable)

## Command Reference

### Export Orders
```bash
# Export all orders for today
python3 -m src.cli --date 2026-03-26 --output odoo-orders-2026-03-26.json

# Export specific payment method
python3 -m src.cli --date 2026-03-26 --payment-method "VNPAY" --output vnpay-orders-2026-03-26.json

# Export date range
python3 -m src.cli --date 2026-03-26 --state paid --output paid-orders.json
```

### Import to B4B
```bash
# Import with invoice generation
python3 -m src.b4b_import_cli --input orders.json

# Dry run (preview only)
python3 -m src.b4b_import_cli --input orders.json --dry-run
```

### Automated Daily Sync (Recommended)
```bash
# Quick sync - today's VNPay/VNPayQR orders → B4B → Invoices
./sync-daily.sh

# Full automation with options
./sync-odoo-to-b4b.py                          # Today, default payment methods
./sync-odoo-to-b4b.py --date 2026-04-01        # Specific date
./sync-odoo-to-b4b.py --dry-run                # Preview only
./sync-odoo-to-b4b.py --export-only            # Export, skip B4B import
./sync-odoo-to-b4b.py --payment-methods VNPay VNPayQR Thẻ ATM  # Custom methods
./sync-odoo-to-b4b.py --import-only --input orders.json  # Import existing file
```

**Automated Workflow:**
1. Exports Odoo POS orders (multiple payment methods supported)
2. Combines exports into single JSON file
3. Imports to B4B as sale orders
4. Generates POS invoices (auto-released, signed, tax-sent)

### Scripts (in this skill)
```bash
# Update product mapping
python3 .claude/skills/patedeli-odoo-manager/scripts/update_product_mapping.py

# Create purchase order
python3 .claude/skills/patedeli-odoo-manager/scripts/create_purchase_order.py

# Search products
python3 .claude/skills/patedeli-odoo-manager/scripts/search_products.py
```

## Anti-Patterns

**What NOT to do:**
- ❌ Import purchase orders without approval summary
- ❌ Guess product matches when multiple options exist
- ❌ Create vendors/products without asking first
- ❌ Modify product mapping without confirmation
- ❌ Skip confirmation gates for "efficiency"
- ❌ Assume first search result is correct match
- ❌ Import partial data without noting what was skipped

**What TO do instead:**
- ✅ Always show summary and ask before importing
- ✅ Ask user when multiple matches found
- ✅ Confirm before creating new vendors/products
- ✅ Update mapping only after user confirmation
- ✅ Follow confirmation gates even for small imports
- ✅ Show all match options and let user choose
- ✅ Clearly report skipped items and why

## Pre-Delivery Checklist

Before reporting completion:
- [ ] All confirmation gates shown and user responded
- [ ] Product mapping updated (if matching performed)
- [ ] JSON output files created with valid format
- [ ] Odoo operations completed without errors
- [ ] Summary includes counts, totals, any issues
- [ ] No placeholder text (TODO, FIXME, xxx) in output
- [ ] File paths are absolute or relative to project root

## Error Handling

**Connection errors:**
- Check `.env` has correct credentials
- Verify Odoo URL is accessible
- Try running CLI command directly to debug

**Product not found:**
- Use search script to find similar products
- Ask user to select or create new
- Document the decision in product mapping

**Multiple matches:**
- Show all options with IDs
- Ask user to select by ID
- Update mapping with confirmed choice

**Purchase order import failure:**
- Check vendor exists in Odoo
- Verify all products are active
- Ensure required fields (price, quantity, uom) are present
- Show Odoo error message to user

## Examples

### Example 1: Export Today's VNPAY Orders
```
User: Export today's VNPAY orders

Agent:
1. Exporting VNPAY orders for 2026-03-26...
2. Found 14 orders, total 551,000 VND
3. Output: vnpay-orders-2026-03-26.json
4. Next: Import to B4B? (or other operation)
```

### Example 2: Import Purchase Order
```
User: Import this invoice: invoice.pdf

Agent:
1. Extracting invoice data...
2. Invoice from: Nhà Cung Cấp ABC
3. Found vendor in Odoo: Partner ID 123 ( Nhà Cung Cấp ABC)
4. Matching 5 line items...
   - Cà phê 1kg → Matched to Product 2489
   - Đường 5kg → Found 2 matches:
     1) Product 3010 (Đường kính trắng 5kg)
     2) Product 3012 (Đường phèn 5kg)
     Which one? (User: 1)
   - Sữa đặc → Not found. Create new product? (User: Skip)

5. SUMMARY:
   Vendor: Nhà Cung Cấp ABC (ID 123)
   Line items: 4 matched, 1 skipped
   Total: 2,500,000 VND

   Should I proceed with import? (y/n)
```

### Example 3: Match Receipt
```
User: Match receipt.jpg to products

Agent:
1. Scanning receipt...
2. Found 8 items:
   - Cà phê sữa đá × 2 → Matched to Product 2489
   - Trà đào × 1 → Not found in mapping
     Searching Odoo...
     Found 1 match: Product 2520 (Trà đào Việt Quất)
     Confirm? (User: y)
   - Bánh mì × 3 → Matched to Product 2100
   ...

3. Mapping updated: 2 new mappings added
4. Total: 245,000 VND
5. All items matched successfully
```
