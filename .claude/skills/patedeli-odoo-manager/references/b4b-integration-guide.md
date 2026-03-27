# B4B Integration Guide

## API Endpoint

```
POST /api/v1/entities/{entity_id}/sale-orders
Authorization: Bearer {token}
Content-Type: application/json
```

## Tax-Aware Line Item Format

### Required Fields
```json
{
  "description": "Product Name",
  "quantity": 10,
  "unit_price_without_tax": 100000.00,
  "vat_rate": 0.10
}
```

### Optional Fields
```json
{
  "unit_price_with_tax": 110000.00,  // Auto-calculated if omitted
  "discount_amount": 0
}
```

### Calculation Rules

- **unit_price_with_tax** = unit_price_without_tax × (1 + vat_rate)
- If only unit_price_with_tax provided: B4B auto-calculates without_tax
- If only unit_price_without_tax provided: B4B auto-calculates with_tax
- Best practice: Provide both to avoid rounding errors

## VAT Rate Mapping

| VAT Rate | Decimal | Common Products |
|----------|---------|-----------------|
| 10% | 0.10 | Coffee, tea, food (standard) |
| 5% | 0.05 | Some essentials |
| 0% | 0.00 | Exempt items |

## Sale Order Structure

```json
{
  "order_number": "S02/143318",
  "order_date": "2026-03-25T23:57:27Z",
  "customer": {
    "name": "Khách lẻ",
    "phone": null,
    "email": null
  },
  "lines": [
    {
      "description": "(D7) Cà Phê Sữa Đá",
      "quantity": 1,
      "unit_price_without_tax": 26852.0,
      "unit_price_with_tax": 29000.0,
      "vat_rate": 0.08,
      "discount_amount": 0
    }
  ],
  "payments": [
    {
      "amount": 29000.0,
      "method": "VNPAY"
    }
  ]
}
```

## Invoice Generation

### POS Invoice Endpoint
```
POST /api/v1/entities/{entity_id}/sale-orders/{order_id}/generate-vnpay-invoice
?invoice_type=pos
&auto_release=true
&auto_sign=true
&auto_send_tax=true
```

### Parameters
- `invoice_type`: "pos" for POS invoices
- `auto_release`: Automatically release invoice after generation
- `auto_sign`: Digitally sign the invoice
- `auto_send_tax`: Submit to tax authority

### Response
```json
{
  "id": "invoice_uuid",
  "invoice_number": "1K000123",
  "status": "released",
  "pdf_url": "https://..."
}
```

## Error Handling

### Common Errors

**400 Bad Request - Invalid Data**
```json
{
  "error": "Invalid line item: missing required field 'description'"
}
```
Solution: Check all required fields are present

**404 Not Found - Entity Not Found**
```json
{
  "error": "Entity not found"
}
```
Solution: Verify B4B_ENTITY_ID is correct

**422 Unprocessable Entity - Validation Error**
```json
{
  "error": "VAT rate 0.15 not supported"
}
```
Solution: Use supported VAT rates (0, 0.05, 0.10)

## Logging

Import log format (JSONL):
```json
{
  "timestamp": "2026-03-26T16:32:18Z",
  "order_number": "S02/143318",
  "status": "success",
  "b4b_order_id": "db69453b-a399-4db5-aba6-56b7b0609f78",
  "invoice_status": "generated"
}
```

## Best Practices

1. **Always use dry-run first**: Preview orders before actual import
2. **Check log files**: Review import-log-*.jsonl for errors
3. **Skip existing orders**: Use --skip-existing for re-runs
4. **Provide both prices**: Include unit_price_without_tax AND unit_price_with_tax
5. **Handle rounding**: B4B calculates with 2 decimal places
6. **Validate before import**: Use JSON schema validation if possible
