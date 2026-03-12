"""CLI for importing Odoo orders to B4B."""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Set

import httpx

from .b4b_client import B4BClient
from .order_mapper import map_orders

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="b4b-import",
        description="Import Odoo POS orders to B4B API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
API Endpoint:
  POST /api/v1/entities/{entity_id}/sale-orders
  Content-Type: application/json
  Authorization: Bearer <token>

Tax-Aware Line Item Format:
  {
    "description": "Product A",
    "quantity": 10,
    "unit_price_without_tax": 100000.00,
    "unit_price_with_tax": 110000.00,
    "vat_rate": 0.10,  # B4B resolves to vat_rate_id
    "discount_amount": 0
  }

Environment Variables:
  B4B_API_URL      API base URL (e.g., http://localhost:8000)
  B4B_TOKEN        JWT Bearer token
  B4B_ENTITY_ID    Entity UUID

Examples:
  # Using environment variables
  export B4B_API_URL=http://localhost:8000
  export B4B_TOKEN=your-jwt-token
  export B4B_ENTITY_ID=c7601608-766d-452f-975e-184bef0da5e7
  python -m src.b4b_import_cli --input orders.json

  # Dry-run preview
  python -m src.b4b_import_cli --input orders.json --dry-run

  # Override with CLI args
  python -m src.b4b_import_cli --input orders.json --url http://api.example.com --token xxx
        """,
    )

    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input JSON file path (Odoo export)",
    )
    parser.add_argument(
        "--url",
        required=False,
        help="B4B API base URL (or set B4B_API_URL env var)",
    )
    parser.add_argument(
        "--token",
        required=False,
        help="JWT Bearer token (or set B4B_TOKEN env var)",
    )
    parser.add_argument(
        "--entity-id",
        required=False,
        help="B4B entity ID (or set B4B_ENTITY_ID env var)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview orders without uploading",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit number of orders to import (0 = all)",
    )
    parser.add_argument(
        "--log",
        default="import-log.jsonl",
        help="Log file for processed orders (default: import-log.jsonl)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip orders already in the log file",
    )
    parser.add_argument(
        "--no-invoice",
        action="store_true",
        help="Skip VNPay invoice generation",
    )

    return parser


def load_orders(file_path: str) -> List[Dict[str, Any]]:
    """Load orders from JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("orders", [])


def load_processed_orders(log_path: str) -> Set[str]:
    """Load set of already processed order numbers from log file."""
    processed = set()
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        if entry.get("order_number"):
                            processed.add(entry["order_number"])
                    except json.JSONDecodeError:
                        continue
    return processed


def append_log_entry(log_path: str, entry: Dict[str, Any]) -> None:
    """Append a log entry to the log file."""
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main(argv: List[str] = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Get credentials from args or env
    url = args.url or os.environ.get("B4B_API_URL")
    token = args.token or os.environ.get("B4B_TOKEN")
    entity_id = args.entity_id or os.environ.get("B4B_ENTITY_ID")

    if not url:
        logger.error("URL required: --url or B4B_API_URL env var")
        return 1
    if not token and not args.dry_run:
        logger.error("Token required: --token or B4B_TOKEN env var")
        return 1
    if not entity_id:
        logger.error("Entity ID required: --entity-id or B4B_ENTITY_ID env var")
        return 1

    # Load orders
    try:
        odoo_orders = load_orders(args.input)
    except FileNotFoundError:
        logger.error(f"File not found: {args.input}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        return 1

    # Apply limit
    if args.limit > 0:
        odoo_orders = odoo_orders[:args.limit]

    logger.info(f"Loaded {len(odoo_orders)} orders from {args.input}")

    # Map to B4B format
    b4b_orders = map_orders(odoo_orders)
    logger.info(f"Mapped {len(b4b_orders)} orders to B4B format")

    # Dry run: just print and exit
    if args.dry_run:
        print(json.dumps(b4b_orders, indent=2, ensure_ascii=False))
        logger.info("Dry run complete - no orders uploaded")
        return 0

    # Load processed orders for skip logic
    processed_orders: Set[str] = set()
    if args.skip_existing:
        processed_orders = load_processed_orders(args.log)
        if processed_orders:
            logger.info(f"Loaded {len(processed_orders)} previously processed orders from {args.log}")

    # Import to B4B
    success_count = 0
    error_count = 0
    skip_count = 0
    invoice_count = 0
    invoice_error_count = 0

    with B4BClient(url, token, entity_id) as client:
        for idx, order in enumerate(b4b_orders, 1):
            order_number = order["order_number"]
            timestamp = datetime.utcnow().isoformat() + "Z"

            # Skip already processed
            if args.skip_existing and order_number in processed_orders:
                skip_count += 1
                logger.info(f"[{idx}/{len(b4b_orders)}] Skipped (already processed): {order_number}")
                continue

            try:
                result = client.create_sale_order(order)
                order_id = result.get("id")
                success_count += 1
                logger.info(f"[{idx}/{len(b4b_orders)}] Created: {order_number} (id={order_id})")

                # Generate VNPay invoice (skip if --no-invoice)
                invoice_status = "skipped" if args.no_invoice else "pending"
                if order_id and not args.no_invoice:
                    try:
                        client.generate_vnpay_invoice(order_id)
                        invoice_count += 1
                        invoice_status = "generated"
                        logger.info(f"[{idx}/{len(b4b_orders)}] VNPay invoice generated for: {order_number}")
                    except Exception as inv_e:
                        invoice_error_count += 1
                        invoice_status = f"failed: {inv_e}"
                        logger.warning(f"[{idx}/{len(b4b_orders)}] Invoice failed for {order_number}: {inv_e}")

                # Log success
                append_log_entry(args.log, {
                    "timestamp": timestamp,
                    "order_number": order_number,
                    "status": "success",
                    "b4b_order_id": order_id,
                    "invoice_status": invoice_status,
                })

            except httpx.HTTPStatusError as e:
                error_count += 1
                detail = e.response.text if e.response else str(e)
                logger.error(f"[{idx}/{len(b4b_orders)}] Failed: {order_number} - {e.response.status_code}: {detail}")
                # Log failure
                append_log_entry(args.log, {
                    "timestamp": timestamp,
                    "order_number": order_number,
                    "status": "failed",
                    "b4b_order_id": None,
                    "invoice_status": None,
                    "error": f"{e.response.status_code}: {detail}",
                })
            except Exception as e:
                error_count += 1
                logger.error(f"[{idx}/{len(b4b_orders)}] Failed: {order_number} - {e}")
                # Log failure
                append_log_entry(args.log, {
                    "timestamp": timestamp,
                    "order_number": order_number,
                    "status": "failed",
                    "b4b_order_id": None,
                    "invoice_status": None,
                    "error": str(e),
                })

    logger.info(f"Import complete: {success_count} orders, {invoice_count} invoices, {skip_count} skipped, {error_count} order errors, {invoice_error_count} invoice errors")
    return 0 if error_count == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
