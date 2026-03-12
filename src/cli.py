"""CLI entry point for Odoo POS Importer."""

import argparse
import json
import logging
import sys
from typing import Optional

from .client import OdooClient
from .formatters import format_orders_as_json, format_orders_as_jsonl, format_orders_as_csv
from .importer import OdooPOSImporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="odoo-pos-import",
        description="Import POS sale orders from Odoo server via XML-RPC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import orders for a specific date
  python -m src.cli --url https://odoo.example.com --db mydb \\
      --username admin --password secret --date 2026-03-11

  # Use environment variables for credentials
  export ODOO_URL=https://odoo.example.com
  export ODOO_DB=mydb
  export ODOO_USERNAME=admin
  export ODOO_PASSWORD=secret
  python -m src.cli --date 2026-03-11

  # Save output to file
  python -m src.cli ... --output orders.json
        """,
    )

    # Connection arguments
    parser.add_argument(
        "--url",
        required=False,
        help="Odoo server URL (e.g., https://odoo.example.com)",
    )
    parser.add_argument(
        "--db",
        required=False,
        help="Database name",
    )
    parser.add_argument(
        "--username",
        required=False,
        help="Odoo username",
    )
    parser.add_argument(
        "--password",
        required=False,
        help="Password or API key",
    )

    # Query arguments
    parser.add_argument(
        "--date",
        required=True,
        help="Order date in YYYY-MM-DD format (ICT timezone)",
    )
    parser.add_argument(
        "--timezone",
        default="Asia/Ho_Chi_Minh",
        help="Timezone for date interpretation (default: Asia/Ho_Chi_Minh)",
    )
    parser.add_argument(
        "--state",
        choices=["draft", "paid", "done", "invoiced", "cancel"],
        help="Filter by order state",
    )
    parser.add_argument(
        "--payment-method",
        help="Filter orders containing payments with this method name (e.g., 'VNPayQR', 'Tiền mặt')",
    )

    # Output arguments
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "jsonl", "csv"],
        default="json",
        help="Output format (default: json)",
    )

    # Verbosity
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress all output except errors",
    )

    return parser


def get_connection_args(args: argparse.Namespace) -> dict:
    """Get connection arguments from CLI args or environment variables."""
    import os

    url = args.url or os.environ.get("ODOO_URL")
    db = args.db or os.environ.get("ODOO_DB")
    username = args.username or os.environ.get("ODOO_USERNAME")
    password = args.password or os.environ.get("ODOO_PASSWORD")

    if not all([url, db, username, password]):
        missing = []
        if not url:
            missing.append("--url or ODOO_URL")
        if not db:
            missing.append("--db or ODOO_DB")
        if not username:
            missing.append("--username or ODOO_USERNAME")
        if not password:
            missing.append("--password or ODOO_PASSWORD")

        raise ValueError(f"Missing required arguments: {', '.join(missing)}")

    return {
        "url": url,
        "db": db,
        "username": username,
        "password": password,
    }


def main(argv: Optional[list] = None) -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)

    # Configure logging level
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Get connection parameters
        conn_args = get_connection_args(args)

        # Create and connect client
        logger.info(f"Connecting to {conn_args['url']}...")
        client = OdooClient(**conn_args)
        client.connect()

        # Import orders
        logger.info(f"Importing orders for {args.date} ({args.timezone})...")
        importer = OdooPOSImporter(client)
        orders = importer.import_orders(
            date_str=args.date,
            timezone=args.timezone,
            state=args.state,
        )

        # Filter by payment method if specified
        if args.payment_method:
            filter_method = args.payment_method.lower()
            orders = [
                order for order in orders
                if any(
                    p.payment_method_id and p.payment_method_id[1].lower() == filter_method
                    for p in order.payments
                )
            ]
            logger.info(f"Filtered to {len(orders)} orders with payment method '{args.payment_method}'")

        logger.info(f"Imported {len(orders)} orders")

        # Format output
        if args.format == "json":
            output = format_orders_as_json(
                orders=orders,
                query_date=args.date,
                timezone=args.timezone,
            )
            output_str = json.dumps(output, indent=2, ensure_ascii=False)
        elif args.format == "jsonl":
            output_str = format_orders_as_jsonl(orders)
        else:  # csv
            output_str = format_orders_as_csv(orders)

        # Write output
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output_str)
            logger.info(f"Output written to {args.output}")
        else:
            print(output_str)

        return 0

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except ConnectionError as e:
        logger.error(f"Connection error: {e}")
        return 2
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 3


if __name__ == "__main__":
    sys.exit(main())
