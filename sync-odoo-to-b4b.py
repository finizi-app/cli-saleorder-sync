#!/usr/bin/env python3
"""Automated script to sync Odoo POS orders to B4B with invoice generation.

This script automates the complete workflow:
1. Export today's Odoo POS orders with specified payment methods
2. Import to B4B as sale orders
3. Generate POS invoices

Usage:
    python sync-odoo-to-b4b.py
    python sync-odoo-to-b4b.py --date 2026-04-01
    python sync-odoo-to-b4b.py --payment-methods VNPay VNPayQR --dry-run
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Default payment methods to sync
DEFAULT_PAYMENT_METHODS = ["VNPay", "VNPayQR"]


def run_command(cmd: list, description: str) -> bool:
    """Run a command and log the result.

    Args:
        cmd: Command list to execute
        description: Description of the command

    Returns:
        True if command succeeded, False otherwise
    """
    logger.info(f"Running: {description}")
    logger.debug(f"Command: {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )

    if result.returncode != 0:
        logger.error(f"Failed: {description}")
        logger.error(result.stderr)
        return False

    # Log output lines
    for line in result.stdout.strip().split("\n"):
        if line.strip():
            logger.info(line)

    return True


def export_orders(
    date: str,
    payment_methods: list,
    output_file: str,
) -> bool:
    """Export orders from Odoo.

    Args:
        date: Date string (YYYY-MM-DD)
        payment_methods: List of payment method names
        output_file: Output JSON file path

    Returns:
        True if export succeeded, False otherwise
    """
    logger.info(f"Exporting orders for {date} with payment methods: {payment_methods}")

    # Export for each payment method and combine
    temp_files = []

    for method in payment_methods:
        temp_file = f"temp-{method}-{date}.json"
        temp_files.append(temp_file)

        cmd = [
            sys.executable,
            "-m",
            "src.cli",
            "--date", date,
            "--payment-method", method,
            "--output", temp_file,
        ]

        if not run_command(cmd, f"Export {method} orders"):
            return False

    # Combine all exported files
    logger.info("Combining exported orders...")
    all_orders = []
    seen_ids = set()

    for temp_file in temp_files:
        try:
            with open(temp_file, "r") as f:
                data = json.load(f)
                orders = data.get("orders", [])

                for order in orders:
                    order_id = order.get("id")
                    if order_id and order_id not in seen_ids:
                        seen_ids.add(order_id)
                        all_orders.append(order)

            # Clean up temp file
            Path(temp_file).unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Failed to process {temp_file}: {e}")

    # Write combined output
    output = {
        "query_date": date,
        "timezone": "Asia/Ho_Chi_Minh",
        "payment_methods": payment_methods,
        "total_orders": len(all_orders),
        "orders": all_orders,
    }

    with open(output_file, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    logger.info(f"Exported {len(all_orders)} unique orders to {output_file}")
    return True


def import_to_b4b(
    input_file: str,
    dry_run: bool = False,
) -> bool:
    """Import orders to B4B and generate invoices.

    Args:
        input_file: Input JSON file path
        dry_run: If True, preview without importing

    Returns:
        True if import succeeded, False otherwise
    """
    cmd = [
        sys.executable,
        "-m",
        "src.b4b_import_cli",
        "--input", input_file,
    ]

    if dry_run:
        cmd.append("--dry-run")

    return run_command(cmd, "Import to B4B and generate invoices")


def print_summary(input_file: str) -> None:
    """Print summary of exported orders.

    Args:
        input_file: Input JSON file path
    """
    try:
        with open(input_file, "r") as f:
            data = json.load(f)

        orders = data.get("orders", [])
        total_amount = sum(o.get("amount_total", 0) for o in orders)

        print(f"\n{'='*60}")
        print(f"📊 EXPORT SUMMARY")
        print(f"{'='*60}")
        print(f"Date:        {data.get('query_date')} (ICT)")
        print(f"Payment:     {', '.join(data.get('payment_methods', []))}")
        print(f"Orders:      {len(orders)}")
        print(f"Total:       {total_amount:,.2f} VND")
        print(f"File:        {input_file}")
        print(f"{'='*60}\n")
    except Exception as e:
        logger.warning(f"Failed to print summary: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Automated sync of Odoo POS orders to B4B with invoice generation",
    )
    parser.add_argument(
        "--date", "-d",
        type=str,
        default=None,
        help="Date to sync (YYYY-MM-DD format, default: today)",
    )
    parser.add_argument(
        "--payment-methods",
        type=str,
        nargs="+",
        default=DEFAULT_PAYMENT_METHODS,
        help=f"Payment methods to sync (default: {' '.join(DEFAULT_PAYMENT_METHODS)})",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output JSON file path (default: auto-generated)",
    )
    parser.add_argument(
        "--export-only",
        action="store_true",
        help="Only export from Odoo, skip B4B import",
    )
    parser.add_argument(
        "--import-only",
        action="store_true",
        help="Only import to B4B (requires --input)",
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        help="Input JSON file for import (use with --import-only)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview import without creating orders/invoices",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Determine date
    if args.date:
        date_str = args.date
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")

    # Determine output file
    if args.output:
        output_file = args.output
    else:
        methods_slug = "-".join(args.payment_methods).lower().replace(" ", "-")
        output_file = f"odoo-orders-{date_str}-{methods_slug}.json"

    start_time = datetime.now()
    logger.info(f"{'='*60}")
    logger.info(f"Starting Odoo to B4B sync for {date_str}")
    logger.info(f"Payment methods: {args.payment_methods}")
    logger.info(f"{'='*60}")

    success = True

    # Import-only mode
    if args.import_only:
        if not args.input:
            logger.error("--input required when using --import-only")
            return 1

        print_summary(args.input)
        success = import_to_b4b(args.input, args.dry_run)

    # Full sync mode
    else:
        # Step 1: Export from Odoo
        if not export_orders(date_str, args.payment_methods, output_file):
            logger.error("Export failed!")
            return 1

        print_summary(output_file)

        # Step 2: Import to B4B (unless export-only)
        if not args.export_only:
            success = import_to_b4b(output_file, args.dry_run)

    # Summary
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"{'='*60}")
    if success:
        logger.info(f"✅ Sync completed in {elapsed:.1f}s")
    else:
        logger.error(f"❌ Sync failed after {elapsed:.1f}s")
    logger.info(f"{'='*60}")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
