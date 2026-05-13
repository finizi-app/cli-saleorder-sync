# Odoo POS to B4B Sale Order Sync CLI

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A Python CLI tool to synchronize POS sale orders from Odoo to B4B API with tax-aware pricing and VNPayQR invoice generation.

## Features

- **Odoo POS Import**: Export POS orders from Odoo via XML-RPC
- **Tax-Aware Pricing**: Map Odoo orders to B4B tax-aware format (`unit_price_without_tax`, `unit_price_with_tax`, `vat_rate`)
- **B4B Integration**: Import formatted orders to B4B REST API
- **VNPayQR Invoices**: Generate VNPayQR invoices for POS orders
- **Multiple Output Formats**: JSON, JSONL, CSV output for Odoo orders
- **CLI Interface**: Easy-to-use command line interface
- **Logging & Error Handling**: Comprehensive logging and error handling

## Quick Start

### Installation

```bash
pip install -e .
```

### Basic Usage

#### 1. Export Odoo POS Orders

```bash
# Export orders for a specific date
python -m src.cli --url https://odoo.example.com --db mydb \
    --username admin --password secret --date 2026-03-11

# Use environment variables
export ODOO_URL=https://odoo.example.com
export ODOO_DB=mydb
export ODOO_USERNAME=admin
export ODOO_PASSWORD=secret
python -m src.cli --date 2026-03-11

# Export to file with CSV format
python -m src.cli --date 2026-03-11 --output orders.csv --format csv
```

#### 2. Import to B4B

```bash
# Using environment variables
export B4B_API_URL=http://localhost:8000
export B4B_TOKEN=your-jwt-token
export B4B_ENTITY_ID=c7601608-766d-452f-975e-184bef0da5e7

# Import orders from JSON file
python -m src.b4b_import_cli --input orders.json

# Dry run preview (no actual import)
python -m src.b4b_import_cli --input orders.json --dry-run

# Limit imports and skip existing
python -m src.b4b_import_cli --input orders.json --limit 100 --skip-existing
```

## Project Structure

```
odoo-sync/
├── src/
│   ├── __init__.py
│   ├── cli.py              # Odoo export CLI
│   ├── b4b_import_cli.py   # B4B import CLI
│   ├── client.py           # Odoo XML-RPC client
│   ├── importer.py         # Odoo POS order importer
│   ├── b4b_client.py       # B4B REST API client
│   ├── order_mapper.py     # Odoo to B4B order mapping
│   ├── models.py           # Data models (PosOrder, PosOrderLine, etc.)
│   ├── formatters.py       # Output formatters (JSON, CSV, JSONL)
│   └── timezone_utils.py   # Timezone conversion utilities
├── tests/
│   ├── __init__.py
│   └── test_odoo_importer.py
├── docs/                   # Documentation
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Configuration

### Environment Variables

**Odoo Connection:**
- `ODOO_URL`: Odoo server URL (e.g., https://odoo.example.com)
- `ODOO_DB`: Database name
- `ODOO_USERNAME`: Odoo username
- `ODOO_PASSWORD`: Password or API key

**B4B Connection:**
- `B4B_API_URL`: B4B API base URL (e.g., http://localhost:8000)
- `B4B_TOKEN`: JWT Bearer token
- `B4B_ENTITY_ID`: Entity UUID

### CLI Arguments

**Odoo Export CLI:**
- `--url`: Odoo server URL
- `--db`: Database name
- `--username`: Odoo username
- `--password`: Password or API key
- `--date`: Order date (YYYY-MM-DD format)
- `--timezone`: Timezone for date interpretation (default: Asia/Ho_Chi_Minh)
- `--state`: Filter by order state (draft, paid, done, invoiced, cancel)
- `--payment-method`: Filter by payment method name
- `--output`: Output file path
- `--format`: Output format (json, jsonl, csv)

**B4B Import CLI:**
- `--input`: Input JSON file path
- `--url`: B4B API base URL
- `--token`: JWT Bearer token
- `--entity-id`: B4B entity ID
- `--dry-run`: Preview without uploading
- `--limit`: Number of orders to import
- `--skip-existing`: Skip already processed orders
- `--no-invoice`: Skip VNPay invoice generation

## API Integration

### Odoo XML-RPC Integration

The tool connects to Odoo via XML-RPC to:
- Search and read POS orders
- Fetch order lines and payments
- Handle timezone conversions (ICT to UTC)

### B4B REST API Integration

The tool integrates with B4B API to:
- Create sale orders with tax-aware pricing
- Generate VNPayQR invoices
- Handle error responses and logging

### Tax-Aware Pricing Format

The mapper converts Odoo orders to B4B tax-aware format:

```python
{
    "description": "Product A",
    "quantity": 10,
    "unit_price_without_tax": 100000.00,  # Required
    "unit_price_with_tax": 110000.00,      # Optional (auto-calculated)
    "vat_rate": 0.10,                      # Decimal rate
    "discount_amount": 0
}
```

## Examples

### Complete Workflow

```bash
# 1. Export orders from Odoo
python -m src.cli \
    --url https://odoo.example.com \
    --db production_db \
    --username admin \
    --password secret \
    --date 2026-03-13 \
    --output orders.json

# 2. Preview import to B4B
python -m src.b4b_import_cli \
    --input orders.json \
    --dry-run

# 3. Import to B4B with invoice generation
python -m src.b4b_import_cli \
    --input orders.json \
    --url https://api.b4b.example.com \
    --token your-jwt-token \
    --entity-id your-entity-id
```

### Advanced Options

```bash
# Filter by payment method (VNPayQR)
python -m src.cli \
    --date 2026-03-13 \
    --payment-method "VNPayQR"

# Import with limited orders and skip existing
python -m src.b4b_import_cli \
    --input orders.json \
    --limit 50 \
    --skip-existing \
    --log import-log.jsonl

# Skip invoice generation
python -m src.b4b_import_cli \
    --input orders.json \
    --no-invoice
```

### Automated Daily Sync

For daily operations, use the automated sync scripts:

```bash
# Quick daily sync (today's VNPay/VNPayQR orders → B4B → Invoices)
./sync-daily.sh

# Full control with options
./sync-odoo-to-b4b.py                          # Today, default methods
./sync-odoo-to-b4b.py --date 2026-04-01        # Specific date
./sync-odoo-to-b4b.py --dry-run                # Preview only
./sync-odoo-to-b4b.py --payment-methods VNPay VNPayQR Thẻ ATM  # Custom
```

**Automated workflow:**
1. Exports Odoo POS orders (handles multiple payment methods)
2. Combines exports into single JSON file
3. Imports to B4B as sale orders
4. Generates POS invoices (auto-released, signed, tax-sent)

## Error Handling

The tool includes comprehensive error handling for:
- Connection failures to Odoo/B4B
- Authentication errors
- Data validation errors
- API rate limits
- Network timeouts

Logs are written to stdout with timestamps and detailed error messages.

## Development

### Running Tests

```bash
python -m pytest tests/ -v
```

### Code Formatting

```bash
black src/
ruff check src/
```

### Adding New Features

1. Follow the existing modular structure
2. Add unit tests for new functionality
3. Update documentation
4. Follow the established error handling patterns

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request