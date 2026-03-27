#!/usr/bin/env python3
"""Create purchase order in Odoo from matched invoice data."""

import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add src directory to path
# Script is at: .claude/skills/patedeli-odoo-manager/scripts/create-purchase-order.py
# Project root is 5 levels up
project_root = Path(__file__).parent.parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from client import OdooClient


def create_purchase_order(client: OdooClient, data: dict) -> dict:
    """Create purchase order from validated data.

    Expected data format:
    {
        "vendor_id": int,  # Odoo partner ID
        "order_date": str,  # YYYY-MM-DD
        "lines": [
            {
                "product_id": int,
                "name": str,
                "quantity": float,
                "price_unit": float,
                "uom_id": int,
                "taxes_id": list[int]  # Optional
            }
        ],
        "notes": str  # Optional
    }
    """
    # Create purchase order
    po_values = {
        'partner_id': data['vendor_id'],
        'date_order': f"{data['order_date']} 00:00:00",
        'notes': data.get('notes', ''),
    }

    po_id = client.models['purchase.order'].create(po_values)

    # Create order lines
    for line_data in data['lines']:
        line_values = {
            'order_id': po_id,
            'product_id': line_data['product_id'],
            'name': line_data['name'],
            'product_qty': line_data['quantity'],
            'price_unit': line_data['price_unit'],
            'product_uom': line_data['uom_id'],
            'date_planned': f"{data['order_date']} 00:00:00",
            'taxes_id': [(6, 0, line_data.get('taxes_id', []))],
        }
        client.models['purchase.order.line'].create(line_values)

    # Fetch created PO details
    po = client.models['purchase.order'].read([po_id], ['name', 'amount_total', 'state'])[0]

    return {
        'id': po_id,
        'name': po['name'],
        'amount_total': po['amount_total'],
        'state': po['state']
    }


def main():
    parser = argparse.ArgumentParser(
        description="Create purchase order in Odoo from JSON data"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="JSON file with validated purchase order data"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate data without creating PO"
    )

    args = parser.parse_args()

    # Load input data
    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Validate required fields
    required = ['vendor_id', 'order_date', 'lines']
    for field in required:
        if field not in data:
            print(f"Error: Missing required field: {field}")
            return 1

    if not data['lines']:
        print("Error: No line items in data")
        return 1

    for i, line in enumerate(data['lines']):
        required_line = ['product_id', 'name', 'quantity', 'price_unit', 'uom_id']
        for field in required_line:
            if field not in line:
                print(f"Error: Line {i} missing field: {field}")
                return 1

    if args.dry_run:
        print("✓ Data validation passed")
        print(f"  Vendor ID: {data['vendor_id']}")
        print(f"  Date: {data['order_date']}")
        print(f"  Lines: {len(data['lines'])}")
        print("\nDry run complete - no PO created")
        return 0

    # Get Odoo credentials
    url = os.environ.get("ODOO_URL")
    db = os.environ.get("ODOO_DB")
    username = os.environ.get("ODOO_USERNAME")
    password = os.environ.get("ODOO_PASSWORD")

    if not all([url, db, username, password]):
        print("Error: Missing Odoo credentials")
        return 1

    try:
        client = OdooClient(url=url, db=db, username=username, password=password)
        client.connect()

        result = create_purchase_order(client, data)

        print(f"✓ Purchase order created: {result['name']}")
        print(f"  PO ID: {result['id']}")
        print(f"  Total: {result['amount_total']:,.0f} VND")
        print(f"  State: {result['state']}")

        return 0

    except Exception as e:
        print(f"Error creating purchase order: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
