# Odoo POS Export Workflow

## Field Mappings

### Order Fields
| Odoo Field | B4B Field | Notes |
|------------|-----------|-------|
| `name` | `order_number` | Order reference (e.g., S02/143318) |
| `date_order` | `order_date` | ISO 8601 format |
| `amount_total` | Included in line items | Total with tax |
| `amount_tax` | Calculated from vat_rate | Tax amount |
| `partner_id` | `customer` | Customer info (ID 950 = Khách lẻ) |
| `pos_reference` | Metadata | POS session reference |
| `state` | Metadata | Order state (paid, invoiced, done) |

### Line Item Fields
| Odoo Field | B4B Field | Notes |
|------------|-----------|-------|
| `product_id` | Product lookup | Must exist in B4B |
| `product_name` | `description` | Product display name |
| `qty` | `quantity` | Quantity ordered |
| `price_subtotal_incl` | `unit_price_with_tax` | Price with tax |
| `price_subtotal` | `unit_price_without_tax` | Price without tax |
| `discount` | `discount_amount` | Discount amount |
| `uom_id` / `uom_name` | Metadata | Unit of measure |

### Payment Fields
| Odoo Field | Notes |
|------------|-------|
| `payment_method_id` / `payment_method_name` | VNPAY, VNPayQR, Thẻ ATM, Tiền mặt |
| `amount` | Payment amount |
| `payment_date` | Payment timestamp |

## Tax Calculation

Vietnam VAT rates:
- 10% (standard) - most food & beverages
- 5% (reduced) - some essential goods
- 0% (exempt) - medical, education

Formula: `tax_amount = (price_with_tax - price_without_tax) / (1 + tax_rate)`

## Date Range Handling

When user says "today's orders":
- Query date: 2026-03-26
- Timezone: Asia/Ho_Chi_Minh (ICT)
- UTC range: 2026-03-25 17:00:00 to 2026-03-26 16:59:59

## Common Filters

### By Payment Method
```bash
--payment-method "VNPAY"      # VNPAY wallet
--payment-method "VNPayQR"    # VNPay QR code
--payment-method "Thẻ ATM"    # ATM card
--payment-method "Tiền mặt"  # Cash
```

### By State
```bash
--state paid       # Paid orders
--state invoiced   # Invoiced orders
--state done       # Completed orders
```

## Output Format

JSON structure:
```json
{
  "query_date": "2026-03-26",
  "timezone": "Asia/Ho_Chi_Minh",
  "orders": [
    {
      "id": 176299,
      "name": "S02/143318",
      "date_order": "2026-03-25T23:57:27Z",
      "partner_id": 950,
      "partner_name": "Khách lẻ",
      "amount_total": 29000.0,
      "amount_tax": 2148.0,
      "amount_paid": 29000.0,
      "lines": [...],
      "payments": [...]
    }
  ]
}
```
