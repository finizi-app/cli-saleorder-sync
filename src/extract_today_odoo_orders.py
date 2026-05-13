#!/usr/bin/env python3
"""Extract today's orders from Odoo for VNPay, VNPayQR, and Thẻ ATM payment methods."""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.client import OdooClient
from src.order_mapper import map_orders


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Payment methods to extract
PAYMENT_METHODS = ["VNPay", "VNPayQR", "Thẻ ATM"]


def get_today_date_range() -> tuple[str, str]:
    """Get today's date range in UTC for Odoo query."""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    # Format for Odoo datetime fields
    today_str = today.strftime("%Y-%m-%d 00:00:00")
    tomorrow_str = tomorrow.strftime("%Y-%m-%d 00:00:00")

    return today_str, tomorrow_str


def connect_to_odoo() -> OdooClient:
    """Create and connect to Odoo client."""
    url = os.environ.get("ODOO_URL", "http://localhost:8069")
    db = os.environ.get("ODOO_DB", "prod")
    username = os.environ.get("ODOO_USERNAME", "admin")
    password = os.environ.get("ODOO_PASSWORD", "admin")

    client = OdooClient(url, db, username, password)
    client.connect()

    logger.info(f"Connected to Odoo: {url}")
    return client


def fetch_payment_methods(client: OdooClient) -> Dict[str, int]:
    """Fetch payment method IDs for VNPay, VNPayQR, and Thẻ ATM."""
    # Search for payment methods
    payment_methods = client.search_read(
        model="pos.payment.method",
        domain=[("name", "in", PAYMENT_METHODS)],
        fields=["id", "name"],
    )

    method_map = {pm["name"]: pm["id"] for pm in payment_methods}
    logger.info(f"Found payment methods: {method_map}")

    # Check if all methods were found
    missing = [method for method in PAYMENT_METHODS if method not in method_map]
    if missing:
        logger.warning(f"Missing payment methods: {missing}")

    return method_map


def fetch_today_orders(
    client: OdooClient,
    payment_method_ids: List[int],
    date_from: str,
    date_to: str,
) -> List[Dict[str, Any]]:
    """Fetch today's POS orders with specified payment methods."""
    logger.info(f"Fetching orders from {date_from} to {date_to}")

    # Build domain for today's orders with specified payment methods
    domain = [
        ("date_order", ">=", date_from),
        ("date_order", "<", date_to),
        ("state", "in", ["done", "paid", "invoiced"]),
        ("payment_ids", "!=", False),
    ]

    # Search for orders
    orders = client.search_read(
        model="pos.order",
        domain=domain,
        fields=[
            "id",
            "name",
            "pos_reference",
            "date_order",
            "state",
            "amount_total",
            "amount_paid",
            "amount_tax",
            "amount_return",
            "partner_id",
            "lines",
            "payment_ids",
            "company_id",
            "pricelist_id",
            "fiscal_position_id",
            "session_id",
            "user_id",
            "invoice_ids",
        ],
        limit=1000,  # Adjust as needed
    )

    logger.info(f"Found {len(orders)} orders for today")

    # Filter orders by payment method
    filtered_orders = []
    for order in orders:
        # Fetch payment details for this order
        if order.get("payment_ids"):
            payments = client.read(
                model="pos.payment",
                ids=order["payment_ids"],
                fields=["id", "payment_method_id", "amount", "payment_date"],
            )

            # Check if order has any of the target payment methods
            payment_method_names = []
            for payment in payments:
                if payment.get("payment_method_id"):
                    method_id = payment["payment_method_id"][0]
                    # Fetch payment method name
                    method = client.read(
                        model="pos.payment.method",
                        ids=[method_id],
                        fields=["name"],
                    )
                    if method:
                        payment_method_names.append(method[0]["name"])

            # Check if any payment method matches
            if any(method in PAYMENT_METHODS for method in payment_method_names):
                # Add payment details to order
                order["payments"] = payments
                order["payment_methods"] = payment_method_names
                filtered_orders.append(order)

    logger.info(f"Filtered to {len(filtered_orders)} orders with payment methods: {PAYMENT_METHODS}")
    return filtered_orders


def fetch_order_lines(client: OdooClient, order: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Fetch order lines with product details."""
    line_ids = order.get("lines", [])
    if not line_ids:
        return []

    lines = client.read(
        model="pos.order.line",
        ids=line_ids,
        fields=[
            "id",
            "product_id",
            "qty",
            "price_unit",
            "price_subtotal",
            "price_subtotal_incl",
            "discount",
            "tax_ids",
            "tax_ids_after_fiscal_position",
        ],
    )

    # Fetch product details for each line
    for line in lines:
        if line.get("product_id"):
            product_id = line["product_id"][0]
            product = client.read(
                model="product.product",
                ids=[product_id],
                fields=[
                    "id",
                    "name",
                    "default_code",
                    "barcode",
                    "list_price",
                    "taxes_id",
                ],
            )
            if product:
                line["product"] = product[0]

    return lines


def enrich_orders(client: OdooClient, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Enrich orders with full details including lines and related data."""
    logger.info(f"Enriching {len(orders)} orders with full details")

    enriched_orders = []
    for idx, order in enumerate(orders, 1):
        logger.debug(f"[{idx}/{len(orders)}] Enriching order {order.get('name')}")

        # Fetch order lines
        lines = fetch_order_lines(client, order)
        order["lines"] = lines

        # Fetch customer details if available
        if order.get("partner_id"):
            partner_id = order["partner_id"][0]
            partner = client.read(
                model="res.partner",
                ids=[partner_id],
                fields=[
                    "id",
                    "name",
                    "email",
                    "phone",
                    "mobile",
                    "street",
                    "city",
                    "country_id",
                    "vat",
                ],
            )
            if partner:
                order["partner"] = partner[0]

        enriched_orders.append(order)

    return enriched_orders


def save_orders_to_file(orders: List[Dict[str, Any]], output_file: str) -> None:
    """Save orders to JSON file."""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"orders": orders}, f, indent=2, ensure_ascii=False, default=str)

    logger.info(f"Saved {len(orders)} orders to {output_path}")


def extract_orders(
    date: str = None,
    output_file: str = None,
    payment_methods: List[str] = None,
    enrich: bool = True,
) -> List[Dict[str, Any]]:
    """
    Extract orders from Odoo for specified date and payment methods.

    Args:
        date: Date to extract orders for (YYYY-MM-DD format, default: today)
        output_file: Output JSON file path (default: auto-generated)
        payment_methods: List of payment method names (default: VNPay, VNPayQR, Thẻ ATM)
        enrich: Whether to enrich orders with full details (default: True)

    Returns:
        List of Odoo orders
    """
    global PAYMENT_METHODS

    # Parse date or use today
    if date:
        target_date = datetime.strptime(date, "%Y-%m-%d")
    else:
        target_date = datetime.utcnow()

    # Get date range for query
    date_from = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    date_from_str = date_from.strftime("%Y-%m-%d 00:00:00")
    date_to = date_from + timedelta(days=1)
    date_to_str = date_to.strftime("%Y-%m-%d 00:00:00")

    # Use custom payment methods if provided
    if payment_methods:
        PAYMENT_METHODS = payment_methods

    logger.info(f"Extracting orders for {date_from.date()} with payment methods: {PAYMENT_METHODS}")

    # Connect to Odoo
    client = connect_to_odoo()

    # Fetch payment methods
    payment_method_ids = fetch_payment_methods(client)

    if not payment_method_ids:
        logger.error("No payment methods found!")
        return []

    # Fetch today's orders
    orders = fetch_today_orders(
        client,
        list(payment_method_ids.values()),
        date_from_str,
        date_to_str,
    )

    if not orders:
        logger.warning("No orders found for today!")
        return []

    # Enrich orders with full details
    if enrich:
        orders = enrich_orders(client, orders)

    # Save to file
    if output_file:
        save_orders_to_file(orders, output_file)
    else:
        # Generate default output filename
        date_str = date_from.strftime("%Y-%m-%d")
        methods_slug = "-".join(PAYMENT_METHODS).lower().replace(" ", "-").replace("ẻ", "e")
        default_output = f"odoo-orders-{date_str}-{methods_slug}.json"
        save_orders_to_file(orders, default_output)

    return orders


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Extract today's orders from Odoo for VNPay, VNPayQR, and Thẻ ATM",
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Date to extract orders for (YYYY-MM-DD format, default: today)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output JSON file path (default: auto-generated)",
    )
    parser.add_argument(
        "--payment-methods",
        type=str,
        nargs="+",
        default=PAYMENT_METHODS,
        help="Payment method names to filter (default: VNPay VNPayQR Thẻ ATM)",
    )
    parser.add_argument(
        "--no-enrich",
        action="store_true",
        help="Skip enriching orders with full details",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Extract orders
    orders = extract_orders(
        date=args.date,
        output_file=args.output,
        payment_methods=args.payment_methods,
        enrich=not args.no_enrich,
    )

    # Print summary
    print(f"\nExtracted {len(orders)} orders")
    if orders:
        total_amount = sum(order.get("amount_total", 0) for order in orders)
        print(f"Total amount: {total_amount:,.2f} VND")


if __name__ == "__main__":
    main()
