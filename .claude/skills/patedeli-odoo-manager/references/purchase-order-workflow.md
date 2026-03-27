# Purchase Order Import Workflow

## Process Flow

```
Invoice (PDF/Image)
    ↓
Extract Data (ai-multimodal skill)
    ↓
Match Vendor → Search Odoo partners
    ↓
Match Products → Check mapping, then search Odoo
    ↓
Build Summary → Show user for approval
    ↓
Create PO → Odoo API
```

## Step 1: Invoice Data Extraction

### Required Information
- Vendor name (company name on invoice)
- Invoice date
- Line items:
  - Product name/description
  - Quantity
  - Unit price
  - Total (for validation)

### Optional but Helpful
- Vendor tax ID (helps matching)
- Product codes/SKUs
- UOM (unit of measure)

## Step 2: Vendor Matching

### Search Odoo Partners
```python
domain = [
    '|',
    ('name', 'ilike', vendor_name),
    ('vat', '=', vendor_tax_id)  # If tax ID available
]
partner_ids = models['res.partner'].search(domain)
```

### Scenarios

**1. Exact Match Found** (1 result)
- Use this partner
- Confirm: "Matched vendor: [name] (ID: [id])"

**2. Multiple Matches Found** (2+ results)
- Show all matches with IDs
- Ask user: "Found N vendors: [list]. Which one?"
- Use selected partner

**3. No Match Found** (0 results)
- Ask user: "Create new vendor '[name]'?"
- If yes: Create new partner
```python
partner_id = models['res.partner'].create({
    'name': vendor_name,
    'supplier_rank': 1,  # Mark as supplier
    'is_company': True,
    'vat': vendor_tax_id  # If available
})
```

## Step 3: Product Matching

### Check Product Mapping First
```python
# Load mapping from assets/product-mapping.json
mapping = load_product_mapping()

# Check for exact match
if item_name in mapping['receipt_items']:
    product_id = mapping['receipt_items'][item_name]['odoo_product_id']
    # Use this product
else:
    # Search Odoo products
    search_results = search_odoo_products(item_name)
```

### Search Odoo Products
```python
domain = [
    '|',
    '|',
    ('name', 'ilike', item_name),
    ('default_code', 'ilike', item_name),
    ('barcode', '=', item_name)
]
product_ids = models['product.product'].search(domain, limit=10)
```

### Matching Scenarios

**1. Found in Mapping** (exact match)
- Use mapped product
- Confirm: "✓ '[item]' → '[product_name]'"

**2. Single Search Result** (1 product)
- Auto-confirm and update mapping
- Add to product-mapping.json

**3. Multiple Search Results** (2+ products)
- Show all options:
  ```
  Found N matches for '[item]':
  1) [ID] [name] - [code] - [price]
  2) [ID] [name] - [code] - [price]
  ...
  Which one? (1-N or 'skip' or 'create')
  ```
- User selects by number
- Update mapping

**4. No Search Results** (0 products)
- Ask: "Product '[item]' not found. Skip or create new?"
- If create: Get product details from user
```python
product_id = models['product.product'].create({
    'name': item_name,
    'default_code': user_provided_code,  # Optional
    'list_price': unit_price,
    'purchase_ok': True,
    'uom_id': 1  # Default UOM
})
```

## Step 4: Build Summary

### Summary Format
```
PURCHASE ORDER SUMMARY
──────────────────────
Vendor: [vendor_name] (ID: [vendor_id])
Date: [invoice_date]

Line Items:
1. [product_name] × [qty] @ [price] = [total]
2. ...

──────────────────────
Total: [total_amount]

Items to Import: [matched_count]
Items to Skip: [skipped_count]
Skipped Items: [list of skipped items]

Should I proceed with import? (y/n)
```

## Step 5: Create Purchase Order

### Odoo PO Creation
```python
# Create PO
po_values = {
    'partner_id': vendor_id,
    'date_order': f'{invoice_date} 00:00:00',
    'notes': f'Imported from invoice dated {invoice_date}'
}
po_id = models['purchase.order'].create(po_values)

# Create lines
for line in matched_lines:
    line_values = {
        'order_id': po_id,
        'product_id': line['product_id'],
        'name': line['product_name'],
        'product_qty': line['quantity'],
        'price_unit': line['price_unit'],
        'product_uom': line['uom_id'],
        'date_planned': f'{invoice_date} 00:00:00',
    }
    models['purchase.order.line'].create(line_values)
```

### Confirmation
```
✓ Purchase order created: [PO_name]
✓ PO ID: [po_id]
✓ Total: [amount] VND
✓ State: draft
```

## Product Mapping Memory

### File Structure
```json
{
  "receipt_items": {
    "Cà phê sữa đá": {
      "odoo_product_id": 2489,
      "odoo_product_name": "(D7) Cà Phê Sữa Đá",
      "confidence": "exact",
      "last_matched": "2026-03-26"
    }
  },
  "last_updated": "2026-03-26T16:32:18Z"
}
```

### Update Mapping
After each successful match:
1. Add/update entry in receipt_items
2. Set last_matched timestamp
3. Save to assets/product-mapping.json

## Fuzzy Matching

For names that don't match exactly:
- Remove diacritics: "Cà phê" → "Ca phe"
- Remove extra spaces
- Normalize case
- Try partial matches

Example:
```
Receipt: "Ca phe sua da"
Mapping: "Cà phê sữa đá"
→ Match found after normalization
```

## Validation Checks

Before importing, verify:
- [ ] Vendor is valid (not archived)
- [ ] All products are purchase_ok=True
- [ ] All products have UOM set
- [ ] Quantities are positive numbers
- [ ] Prices are positive numbers
- [ ] Total matches invoice total (within tolerance)
- [ ] No duplicate line items

## Error Recovery

**Vendor creation fails:**
- Check if vendor already exists (case insensitive)
- Try alternative name matching

**Product creation fails:**
- Ask user for required fields
- Use default category if not specified
- Set default UOM if not provided

**PO creation fails:**
- Check vendor has supplier_rank > 0
- Verify all line products are active
- Show Odoo error message
