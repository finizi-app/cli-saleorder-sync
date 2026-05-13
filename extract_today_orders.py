#!/usr/bin/env python3
"""Extract today's orders from Odoo for VNPay, VNPayQR, and Thẻ ATM payment methods.

This script connects to Odoo, fetches today's POS orders with the specified payment
methods (VNPay, VNPayQR, Thẻ ATM), and saves them to a JSON file for import.

Usage:
    python extract_today_orders.py --output today-orders.json
    python extract_today_orders.py --date 2026-03-31 --output vnpay-orders-2026-03-31.json
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Payment methods to extract
PAYMENT_METHODS = ["VNPay", "VNPayQR", "Thẻ ATM"]


def get_odoo_config() -> Dict[str, str]:
    """Get Odoo connection configuration from environment variables."""
    return {
        "url": os.environ.get("ODOO_URL", "http://localhost:8069"),
        "db": os.environ.get("ODOO_DB", "prod"),
        "username": os.environ.get("ODOO_USERNAME", "admin"),
        "password": os.environ.get("ODOO_PASSWORD", "admin"),
    }


def get_date_range(date_str: Optional[str] = None) -> tuple[str, str]:
    """Get date range for querying orders.

    Args:
        date_str: Date string in YYYY-MM-DD format (default: today UTC)

    Returns:
        Tuple of (date_from, date_to) in Odoo datetime format
    """
    if date_str:
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        target_date = datetime.utcnow()

    # Create date range for the entire day
    date_from = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    date_to = date_from + timedelta(days=1)

    # Format for Odoo
    date_from_str = date_from.strftime("%Y-%m-%d %H:%M:%S")
    date_to_str = date_to.strftime("%Y-%m-%d %H:%M:%S")

    logger.info(f"Date range: {date_from_str} to {date_to_str}")
    return date_from_str, date_to_str


def fetch_payment_method_ids(client, payment_methods: List[str]) -> Dict[str, int]:
    """Fetch payment method IDs from Odoo.

    Args:
        client: Odoo XML-RPC client
        payment_methods: List of payment method names

    Returns:
        Dictionary mapping payment method names to IDs
    """
    logger.info(f"Fetching payment method IDs for: {payment_methods}")

    try:
        # Search for payment methods
        methods = client.execute_kw(
            "pos.payment.method",
            "search_read",
            [[["name", "in", payment_methods]]],
            {"fields": ["id", "name", "active"]},
        )

        method_map = {m["name"]: m["id"] for m in methods if m.get("active", True)}
        logger.info(f"Found payment methods: {method_map}")

        # Check for missing methods
        missing = [pm for pm in payment_methods if pm not in method_map]
        if missing:
            logger.warning(f"Payment methods not found: {missing}")

        return method_map

    except Exception as e:
        logger.error(f"Failed to fetch payment methods: {e}")
        return {}


def fetch_today_orders(
    client,
    payment_method_ids: Dict[str, int],
    date_from: str,
    date_to: str,
    limit: int = 1000,
) -> List[Dict[str, Any]]:
    """Fetch today's POS orders with specified payment methods.

    Args:
        client: Odoo XML-RPC client
        payment_method_ids: Dictionary of payment method IDs
        date_from: Start date (Odoo datetime format)
        date_to: End date (Odoo datetime format)
        limit: Maximum number of orders to fetch

    Returns:
        List of order dictionaries
    """
    logger.info(f"Fetching orders from {date_from} to {date_to}")

    try:
        # Build domain for today's paid/done orders
        domain = [
            ["date_order", ">=", date_from],
            ["date_order", "<", date_to],
            ["state", "in", ["done", "paid", "invoiced"]],
        ]

        # Fetch orders
        orders = client.execute_kw(
            "pos.order",
            "search_read",
            [domain],
            {
                "fields": [
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
                    "user_id",
                    "session_id",
                    "company_id",
                    "pricelist_id",
                    "fiscal_position_id",
                    "invoice_ids",
                    "statement_ids",
                    "lines",
                ],
                "limit": limit,
                "order": "date_order DESC",
            },
        )

        logger.info(f"Found {len(orders)} orders")

        # Filter by payment method
        if payment_method_ids:
            filtered_orders = []
            for order in orders:
                # Check statement_ids (payment lines)
                statement_ids = order.get("statement_ids", [])
                if statement_ids:
                    # Fetch payment details
                    statements = client.execute_kw(
                        "pos.payment",
                        "read",
                        [statement_ids],
                        {"fields": ["id", "payment_method_id", "amount"]},
                    )

                    # Check if any payment uses our target methods
                    for stmt in statements:
                        method_id = stmt.get("payment_method_id", [])
                        if method_id and isinstance(method_id, list) and len(method_id) > 0:
                            method_id = method_id[0]
                            if method_id in payment_method_ids.values():
                                filtered_orders.append(order)
                                break

            logger.info(f"Filtered to {len(filtered_orders)} orders with payment methods: {list(payment_method_ids.keys())}")
            return filtered_orders

        return orders

    except Exception as e:
        logger.error(f"Failed to fetch orders: {e}")
        return []


def fetch_order_lines(client, order_ids: List[int]) -> Dict[int, List[Dict[str, Any]]]:
    """Fetch order lines for multiple orders.

    Args:
        client: Odoo XML-RPC client
        order_ids: List of order IDs

    Returns:
        Dictionary mapping order IDs to their lines
    """
    logger.info(f"Fetching lines for {len(order_ids)} orders")

    try:
        # Search for all order lines
        lines = client.execute_kw(
            "pos.order.line",
            "search_read",
            [[["order_id", "in", order_ids]]],
            {
                "fields": [
                    "id",
                    "order_id",
                    "product_id",
                    "qty",
                    "price_unit",
                    "price_subtotal",
                    "price_subtotal_incl",
                    "discount",
                    "tax_ids",
                    "tax_ids_after_fiscal_position",
                ],
            },
        )

        # Group lines by order
        order_lines: Dict[int, List[Dict[str, Any]]] = {}
        for line in lines:
            order_id = line.get("order_id", [])
            if order_id and isinstance(order_id, list) and len(order_id) > 0:
                order_id = order_id[0]
                if order_id not in order_lines:
                    order_lines[order_id] = []
                order_lines[order_id].append(line)

        return order_lines

    except Exception as e:
        logger.error(f"Failed to fetch order lines: {e}")
        return {}


def enrich_orders(client, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Enrich orders with complete data including lines and payments.

    Args:
        client: Odoo XML-RPC client
        orders: List of order dictionaries

    Returns:
        Enriched list of order dictionaries
    """
    logger.info(f"Enriching {len(orders)} orders")

    # Extract order IDs
    order_ids = [order["id"] for order in orders]

    # Fetch order lines
    order_lines = fetch_order_lines(client, order_ids)

    # Enrich each order
    enriched_orders = []
    for order in orders:
        order_id = order["id"]

        # Add lines
        order["lines_data"] = order_lines.get(order_id, [])

        # Fetch payment details
        statement_ids = order.get("statement_ids", [])
        if statement_ids:
            try:
                payments = client.execute_kw(
                    "pos.payment",
                    "read",
                    [statement_ids],
                    {"fields": ["id", "payment_method_id", "amount", "payment_date", "transaction_id", "card_type", "payment_status"]},
                )
                order["payments_data"] = payments
            except Exception as e:
                logger.warning(f"Failed to fetch payments for order {order_id}: {e}")
                order["payments_data"] = []

        enriched_orders.append(order)

    return enriched_orders


def save_orders_to_json(orders: List[Dict[str, Any]], output_file: str) -> None:
    """Save orders to JSON file.

    Args:
        orders: List of order dictionaries
        output_file: Output file path
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "extracted_at": datetime.utcnow().isoformat(),
                "total_orders": len(orders),
                "orders": orders,
            },
            f,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

    logger.info(f"Saved {len(orders)} orders to {output_file}")


def main():
    """Main entry point."""
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
        default="today-orders.json",
        help="Output JSON file path (default: today-orders.json)",
    )
    parser.add_argument(
        "--payment-methods",
        type=str,
        nargs="+",
        default=PAYMENT_METHODS,
        help=f"Payment methods to extract (default: {' '.join(PAYMENT_METHODS)})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Maximum number of orders to fetch (default: 1000)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        import xmlrpc.client
        from src import OdooClient

        # Get configuration
        config = get_odoo_config()
        logger.info(f"Connecting to Odoo at {config['url']}")

        # Create client
        client = OdooClient(
            url=config["url"],
            db=config["db"],
            username=config["username"],
            password=config["password"],
        )
        client.connect()

        # Get date range
        date_from, date_to = get_date_range(args.date)

        # Fetch payment method IDs
        payment_method_ids = fetch_payment_method_ids(client, args.payment_methods)
        if not payment_method_ids:
            logger.error("No payment methods found. Please check the payment method names.")
            return 1

        # Fetch orders
        orders = fetch_today_orders(
            client,
            payment_method_ids,
            date_from,
            date_to,
            args.limit,
        )

        if not orders:
            logger.warning("No orders found for the specified criteria.")
            # Still create empty output file
            save_orders_to_json([], args.output)
            return 0

        # Enrich orders with lines and payment details
        enriched_orders = enrich_orders(client, orders)

        # Save to JSON
        save_orders_to_json(enrich_orders, args.output)

        # Print summary
        total_amount = sum(order.get("amount_total", 0) for order in enriched_orders)
        print(f"\n✅ Successfully extracted {len(enriched_orders)} orders")
        print(f"💰 Total amount: {total_amount:,.2f} VND")
        print(f"📄 Output saved to: {args.output}")

        return 0

    except ImportError:
        logger.error("Failed to import required modules. Please ensure dependencies are installed.")
        logger.error("Try: pip install xmlrpc.client")
        return 1
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
