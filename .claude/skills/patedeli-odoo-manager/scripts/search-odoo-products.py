#!/usr/bin/env python3
"""Search Odoo products by name or code."""

import argparse
import json
import sys
import os
from pathlib import Path

# Add src directory to path
# Script is at: .claude/skills/patedeli-odoo-manager/scripts/search-odoo-products.py
# Project root is 5 levels up
project_root = Path(__file__).parent.parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from client import OdooClient


def search_products(client: OdooClient, search_term: str, limit: int = 10) -> list:
    """Search products by name or default code."""
    # Search by name or default code
    domain = [
        '|',
        ('name', 'ilike', search_term),
        ('default_code', 'ilike', search_term)
    ]

    fields = ['id', 'name', 'default_code', 'list_price', 'qty_available',
              'uom_id', 'categ_id', 'sale_ok', 'purchase_ok']

    product_ids = client.models['product.product'].search(domain, limit=limit)
    products = client.models['product.product'].read(product_ids, fields)

    return products


def main():
    parser = argparse.ArgumentParser(
        description="Search Odoo products by name or code"
    )
    parser.add_argument(
        "search_term",
        help="Product name or code to search for"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum results (default: 10)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    # Get Odoo credentials from env
    url = os.environ.get("ODOO_URL")
    db = os.environ.get("ODOO_DB")
    username = os.environ.get("ODOO_USERNAME")
    password = os.environ.get("ODOO_PASSWORD")

    if not all([url, db, username, password]):
        print("Error: Missing Odoo credentials. Set ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD")
        return 1

    try:
        client = OdooClient(url=url, db=db, username=username, password=password)
        client.connect()

        products = search_products(client, args.search_term, args.limit)

        if args.json:
            print(json.dumps(products, indent=2, ensure_ascii=False))
        else:
            if not products:
                print(f"No products found for: {args.search_term}")
                return 0

            print(f"Found {len(products)} products for: {args.search_term}")
            print("-" * 80)
            for p in products:
                print(f"ID: {p['id']}")
                print(f"  Name: {p['name']}")
                print(f"  Code: {p.get('default_code', 'N/A')}")
                print(f"  Price: {p.get('list_price', 0):,.0f} VND")
                print(f"  Available: {p.get('qty_available', 0)}")
                print(f"  Sale: {'Yes' if p.get('sale_ok') else 'No'}")
                print(f"  Purchase: {'Yes' if p.get('purchase_ok') else 'No'}")
                print()

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
