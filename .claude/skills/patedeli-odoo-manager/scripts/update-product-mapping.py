#!/usr/bin/env python3
"""Update product mapping memory for receipt matching."""

import argparse
import json
import sys
from pathlib import Path


def load_mapping(mapping_file: Path) -> dict:
    """Load existing product mapping."""
    if mapping_file.exists():
        with open(mapping_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"receipt_items": {}, "last_updated": None}


def save_mapping(mapping: dict, mapping_file: Path) -> None:
    """Save product mapping."""
    from datetime import datetime
    mapping["last_updated"] = datetime.now().isoformat()
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)


def add_mapping(mapping: dict, receipt_item: str, odoo_product_id: int, odoo_product_name: str) -> None:
    """Add or update product mapping."""
    mapping["receipt_items"][receipt_item] = {
        "odoo_product_id": odoo_product_id,
        "odoo_product_name": odoo_product_name
    }


def main():
    parser = argparse.ArgumentParser(
        description="Update product mapping memory for receipt scanning"
    )
    parser.add_argument(
        "--receipt-item",
        required=True,
        help="Receipt item name (exact text from receipt)"
    )
    parser.add_argument(
        "--odoo-product-id",
        required=True,
        type=int,
        help="Odoo product ID"
    )
    parser.add_argument(
        "--odoo-product-name",
        required=True,
        help="Odoo product name"
    )
    parser.add_argument(
        "--mapping-file",
        default=".claude/skills/patedeli-odoo-manager/assets/product-mapping.json",
        help="Path to product mapping JSON file"
    )

    args = parser.parse_args()

    mapping_file = Path(args.mapping_file)
    mapping_file.parent.mkdir(parents=True, exist_ok=True)

    mapping = load_mapping(mapping_file)
    add_mapping(mapping, args.receipt_item, args.odoo_product_id, args.odoo_product_name)
    save_mapping(mapping, mapping_file)

    print(f"✓ Added mapping: '{args.receipt_item}' → {args.odoo_product_name} (ID: {args.odoo_product_id})")
    print(f"✓ Mapping file updated: {mapping_file}")
    print(f"✓ Total mappings: {len(mapping['receipt_items'])}")


if __name__ == "__main__":
    main()
