#!/usr/bin/env python3
"""Sync VNPay, VNPayQR, and Thẻ ATM orders from Odoo and issue POS invoices.

This is the main orchestration script that:
1. Extracts today's orders from Odoo for VNPay, VNPayQR, and Thẻ ATM payment methods
2. Imports and processes the orders
3. Issues POS invoices

Usage:
    python sync_vnpay_orders.py
    python sync_vnpay_orders.py --date 2026-03-31
    python sync_vnpay_orders.py --dry-run --verbose
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

# Payment methods to sync
PAYMENT_METHODS = ["VNPay", "VNPayQR", "Thẻ ATM"]


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration.

    Args:
        verbose: Enable verbose logging
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.getLogger().setLevel(log_level)


def print_banner() -> None:
    """Print application banner."""
    banner = """
╔════════════════════════════════════════════════════════════╗
║  Odoo VNPay Order Sync - POS Invoice Generator            ║
║  Extract VNPay, VNPayQR, Thẻ ATM orders and issue invoices ║
╚════════════════════════════════════════════════════════════╝
    """
    print(banner)


def extract_orders(
    date: Optional[str] = None,
    output_file: Optional[str] = None,
    payment_methods: List[str] = PAYMENT_METHODS,
    verbose: bool = False,
) -> bool:
    """Extract orders from Odoo.

    Args:
        date: Date to extract orders for (YYYY-MM-DD format, default: today)
        output_file: Output file path
        payment_methods: List of payment methods
        verbose: Enable verbose logging

    Returns:
        True if successful, False otherwise
    """
    logger.info("📥 Step 1: Extracting orders from Odoo...")

    # Import extraction module
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from extract_today_orders import (
            fetch_today_orders,
            fetch_payment_method_ids,
            get_date_range,
            get_odoo_config,
            save_orders_to_json,
        )
        import xmlrpc.client
        from src import OdooClient
    except ImportError as e:
        logger.error(f"Failed to import extraction modules: {e}")
        return False

    # Get configuration
    config = get_odoo_config()
    logger.info(f"🔌 Connecting to Odoo at {config['url']}")

    try:
        # Create client
        client = OdooClient(
            url=config["url"],
            db=config["db"],
            username=config["username"],
            password=config["password"],
        )
        client.connect()

        # Get date range
        date_from, date_to = get_date_range(date)

        # Fetch payment method IDs
        payment_method_ids = fetch_payment_method_ids(client, payment_methods)
        if not payment_method_ids:
            logger.error("❌ No payment methods found")
            return False

        # Fetch orders
        orders = fetch_today_orders(
            client,
            payment_method_ids,
            date_from,
            date_to,
        )

        if not orders:
            logger.warning("⚠️  No orders found for the specified criteria")
            # Create empty output file
            output_file = output_file or "orders-extracted.json"
            save_orders_to_json([], output_file)
            return True

        # Save to JSON
        output_file = output_file or "orders-extracted.json"
        save_orders_to_json(orders, output_file)

        print(f"\n✅ Extraction complete!")
        print(f"   📦 Orders extracted: {len(orders)}")
        print(f"   💰 Total amount: {sum(o.get('amount_total', 0) for o in orders):,.2f} VND")
        print(f"   📄 Saved to: {output_file}")

        return True

    except Exception as e:
        logger.error(f"❌ Extraction failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


def import_and_issue_invoices(
    input_file: str,
    dry_run: bool = False,
    verbose: bool = False,
) -> bool:
    """Import orders and issue POS invoices.

    Args:
        input_file: Input file path with extracted orders
        dry_run: Dry run mode
        verbose: Enable verbose logging

    Returns:
        True if successful, False otherwise
    """
    logger.info("📤 Step 2: Importing orders and issuing invoices...")

    # Import invoice module
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from import_and_issue_invoices import (
            load_orders,
            map_orders_to_invoice_format,
            print_summary,
            save_invoices_to_json,
        )
    except ImportError as e:
        logger.error(f"Failed to import invoice modules: {e}")
        return False

    # Load orders
    orders = load_orders(input_file)
    if not orders:
        logger.error("❌ No orders loaded")
        return False

    # Map to invoice format
    invoices = map_orders_to_invoice_format(orders)

    if not invoices:
        logger.warning("⚠️  No valid invoices to generate")
        return True

    # Determine output file
    input_path = Path(input_file)
    output_file = f"invoices-{input_path.stem}.json"

    # Save invoices
    save_invoices_to_json(invoices, output_file)

    # Print summary
    print_summary(invoices)

    if dry_run:
        print("\n⚠️  DRY RUN - No invoices were actually imported to Odoo")
        print("🚀 To import for real, run without --dry-run flag")
    else:
        print("\n🚀 Invoice data prepared and ready!")
        print("📝 Next steps:")
        print("   1. Review the invoice data in the output file")
        print("   2. Import to Odoo using your preferred method")
        print("   3. Issue invoices through Odoo POS interface")

    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Sync VNPay orders from Odoo and issue POS invoices",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sync today's orders
  python sync_vnpay_orders.py

  # Sync orders for a specific date
  python sync_vnpay_orders.py --date 2026-03-31

  # Dry run (extract and validate without importing)
  python sync_vnpay_orders.py --dry-run

  # Verbose output
  python sync_vnpay_orders.py --verbose

  # Extract only (skip invoice generation)
  python sync_vnpay_orders.py --extract-only

  # Import from existing file
  python sync_vnpay_orders.py --input orders-extracted.json --import-only
        """,
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Date to sync orders for (YYYY-MM-DD format, default: today)",
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        help="Input file with pre-extracted orders (for --import-only)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file path",
    )
    parser.add_argument(
        "--payment-methods",
        type=str,
        nargs="+",
        default=PAYMENT_METHODS,
        help=f"Payment methods to sync (default: {' '.join(PAYMENT_METHODS)})",
    )
    parser.add_argument(
        "--extract-only",
        action="store_true",
        help="Only extract orders, skip invoice generation",
    )
    parser.add_argument(
        "--import-only",
        action="store_true",
        help="Only import from existing file, skip extraction",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and prepare without actual import to Odoo",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Setup
    setup_logging(args.verbose)
    print_banner()

    # Validate arguments
    if args.extract_only and args.import_only:
        logger.error("❌ Cannot specify both --extract-only and --import-only")
        return 1

    # Import only mode
    if args.import_only:
        if not args.input:
            logger.error("❌ --input required when using --import-only")
            return 1
        return import_and_issue_invoices(args.input, args.dry_run, args.verbose)

    # Extract (and optionally import)
    output_file = args.output or "orders-extracted.json"
    success = extract_orders(
        date=args.date,
        output_file=output_file,
        payment_methods=args.payment_methods,
        verbose=args.verbose,
    )

    if not success:
        logger.error("❌ Extraction failed. Exiting.")
        return 1

    # If extract-only, we're done
    if args.extract_only:
        print("\n✅ Extraction complete!")
        return 0

    # Continue to invoice generation
    success = import_and_issue_invoices(output_file, args.dry_run, args.verbose)

    if success:
        print("\n" + "="*60)
        print("🎉 SYNC COMPLETE!")
        print("="*60)
        return 0
    else:
        logger.error("❌ Invoice generation failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
