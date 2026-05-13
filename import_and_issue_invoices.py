#!/usr/bin/env python3
"""Import extracted Odoo orders and issue POS invoices.

This script reads the extracted orders JSON file, maps them to the appropriate format,
and imports them to issue POS invoices.

Usage:
    python import_and_issue_invoices.py --input today-orders.json
    python import_and_issue_invoices.py --input vnpay-orders-2026-03-31.json --dry-run
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_orders(input_file: str) -> List[Dict[str, Any]]:
    """Load orders from JSON file.

    Args:
        input_file: Path to input JSON file

    Returns:
        List of order dictionaries
    """
    input_path = Path(input_file)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_file}")
        return []

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    orders = data.get("orders", [])
    logger.info(f"Loaded {len(orders)} orders from {input_file}")

    # Log extraction metadata if available
    if "extracted_at" in data:
        logger.info(f"Extracted at: {data['extracted_at']}")
    if "total_orders" in data:
        logger.info(f"Total orders in file: {data['total_orders']}")

    return orders


def validate_order(order: Dict[str, Any]) -> bool:
    """Validate an order has required fields.

    Args:
        order: Order dictionary

    Returns:
        True if order is valid, False otherwise
    """
    required_fields = ["id", "name", "date_order", "amount_total"]
    missing = [field for field in required_fields if field not in order]

    if missing:
        logger.warning(f"Order {order.get('id', 'unknown')} missing required fields: {missing}")
        return False

    return True


def map_order_to_invoice_format(order: Dict[str, Any]) -> Dict[str, Any]:
    """Map Odoo order to POS invoice format.

    Args:
        order: Odoo order dictionary

    Returns:
        Mapped invoice data
    """
    # Extract basic order info
    invoice_data = {
        "order_id": order["id"],
        "order_name": order["name"],
        "pos_reference": order.get("pos_reference", ""),
        "date_order": order["date_order"],
        "state": order.get("state", "done"),
        "amount_total": order.get("amount_total", 0.0),
        "amount_tax": order.get("amount_tax", 0.0),
        "amount_paid": order.get("amount_paid", 0.0),
        "amount_return": order.get("amount_return", 0.0),
    }

    # Map customer info
    partner_id = order.get("partner_id")
    if partner_id and isinstance(partner_id, list) and len(partner_id) > 0:
        invoice_data["partner_id"] = partner_id[0]
        invoice_data["partner_name"] = partner_id[1] if len(partner_id) > 1 else ""

    # Map order lines
    lines_data = order.get("lines_data", [])
    if lines_data:
        invoice_lines = []
        for line in lines_data:
            invoice_line = {
                "line_id": line["id"],
                "product_id": line.get("product_id", [None, ""])[0] if line.get("product_id") else None,
                "product_name": line.get("product_id", ["", ""])[1] if line.get("product_id") else "",
                "quantity": line.get("qty", 0),
                "price_unit": line.get("price_unit", 0.0),
                "price_subtotal": line.get("price_subtotal", 0.0),
                "price_subtotal_incl": line.get("price_subtotal_incl", 0.0),
                "discount": line.get("discount", 0.0),
            }
            invoice_lines.append(invoice_line)
        invoice_data["lines"] = invoice_lines

    # Map payment info
    payments_data = order.get("payments_data", [])
    if payments_data:
        invoice_payments = []
        for payment in payments_data:
            invoice_payment = {
                "payment_id": payment["id"],
                "payment_method_id": payment.get("payment_method_id", [None, ""])[0] if payment.get("payment_method_id") else None,
                "payment_method_name": payment.get("payment_method_id", ["", ""])[1] if payment.get("payment_method_id") else "",
                "amount": payment.get("amount", 0.0),
                "payment_date": payment.get("payment_date"),
                "transaction_id": payment.get("transaction_id"),
                "card_type": payment.get("card_type"),
                "payment_status": payment.get("payment_status"),
            }
            invoice_payments.append(invoice_payment)
        invoice_data["payments"] = invoice_payments

    return invoice_data


def map_orders_to_invoice_format(orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Map multiple orders to POS invoice format.

    Args:
        orders: List of Odoo order dictionaries

    Returns:
        List of mapped invoice data
    """
    logger.info(f"Mapping {len(orders)} orders to invoice format")

    mapped_orders = []
    skipped = 0

    for order in orders:
        if not validate_order(order):
            skipped += 1
            continue

        try:
            mapped_order = map_order_to_invoice_format(order)
            mapped_orders.append(mapped_order)
        except Exception as e:
            logger.error(f"Failed to map order {order.get('id')}: {e}")
            skipped += 1

    logger.info(f"Mapped {len(mapped_orders)} orders (skipped {skipped})")
    return mapped_orders


def save_invoices_to_json(invoices: List[Dict[str, Any]], output_file: str) -> None:
    """Save invoices to JSON file.

    Args:
        invoices: List of invoice dictionaries
        output_file: Output file path
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at": datetime.utcnow().isoformat(),
                "total_invoices": len(invoices),
                "invoices": invoices,
            },
            f,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

    logger.info(f"Saved {len(invoices)} invoices to {output_file}")


def print_summary(invoices: List[Dict[str, Any]]) -> None:
    """Print summary of imported invoices.

    Args:
        invoices: List of invoice dictionaries
    """
    if not invoices:
        print("\n⚠️ No invoices to generate")
        return

    # Calculate totals
    total_amount = sum(inv.get("amount_total", 0) for inv in invoices)
    total_tax = sum(inv.get("amount_tax", 0) for inv in invoices)

    # Count by payment method
    payment_methods = {}
    for inv in invoices:
        for payment in inv.get("payments", []):
            method = payment.get("payment_method_name", "Unknown")
            if method not in payment_methods:
                payment_methods[method] = {"count": 0, "amount": 0.0}
            payment_methods[method]["count"] += 1
            payment_methods[method]["amount"] += payment.get("amount", 0)

    # Print summary
    print(f"\n{'='*60}")
    print(f"📋 INVOICE GENERATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total invoices: {len(invoices)}")
    print(f"Total amount: {total_amount:,.2f} VND")
    print(f"Total tax: {total_tax:,.2f} VND")
    print(f"\nPayment Methods:")
    for method, stats in sorted(payment_methods.items()):
        print(f"  - {method}: {stats['count']} payments, {stats['amount']:,.2f} VND")
    print(f"{'='*60}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Import extracted Odoo orders and issue POS invoices",
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="Input JSON file with extracted orders",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output JSON file for invoices (default: auto-generated)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and map orders without importing",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load orders
    orders = load_orders(args.input)
    if not orders:
        logger.error("No orders loaded. Exiting.")
        return 1

    # Map to invoice format
    invoices = map_orders_to_invoice_format(orders)

    if not invoices:
        logger.warning("No valid invoices to generate. Exiting.")
        return 0

    # Determine output file
    if args.output:
        output_file = args.output
    else:
        # Generate output filename based on input
        input_path = Path(args.input)
        output_file = f"invoices-{input_path.stem}.json"

    # Save invoices
    save_invoices_to_json(invoices, output_file)

    # Print summary
    print_summary(invoices)

    print(f"\n✅ Invoice data saved to: {output_file}")

    if args.dry_run:
        print("\n⚠️ DRY RUN - No invoices were actually imported to Odoo")
        print("To import, run without --dry-run flag")
    else:
        print("\n🚀 Ready to import invoices to Odoo!")
        print("Note: Actual import functionality to be implemented based on your Odoo setup")

    return 0


if __name__ == "__main__":
    sys.exit(main())
