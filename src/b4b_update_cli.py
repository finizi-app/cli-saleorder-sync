"""CLI for updating sale orders in B4B."""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict

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
        prog="b4b-update",
        description="Update sale orders in B4B API",
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
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--order-id",
        help="Specific B4B order ID to update (if not provided, uses order_number lookup)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview updates without applying",
    )
    parser.add_argument(
        "--unlink-invoice",
        action="store_true",
        help="Remove linked invoice from sale order",
    )
    return parser


def load_orders(file_path: str) -> list:
    """Load orders from JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("orders", [])


def main(argv: list = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

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

    odoo_orders = load_orders(args.input)
    logger.info(f"Loaded {len(odoo_orders)} orders from {args.input}")

    b4b_orders = map_orders(odoo_orders)
    logger.info(f"Mapped {len(b4b_orders)} orders to B4B format")

    if args.dry_run:
        print(json.dumps(b4b_orders, indent=2, ensure_ascii=False))
        logger.info("Dry run complete - no updates applied")
        return 0

    success_count = 0
    error_count = 0

    with B4BClient(url, token, entity_id) as client:
        for idx, order in enumerate(b4b_orders, 1):
            order_number = order["order_number"]

            if args.order_id:
                # Use provided order ID directly
                b4b_order_id = args.order_id
            else:
                # Would need to implement lookup by order_number
                logger.error(f"[{idx}] Order number lookup not implemented: {order_number}")
                error_count += 1
                continue

            try:
                result = client.update_sale_order(b4b_order_id, order, unlink_invoice=args.unlink_invoice)
                success_count += 1
                logger.info(f"[{idx}/{len(b4b_orders)}] Updated: {order_number}" + (f" (invoice unlinked)" if args.unlink_invoice else ""))
            except httpx.HTTPStatusError as e:
                error_count += 1
                detail = e.response.text if e.response else str(e)
                logger.error(f"[{idx}/{len(b4b_orders)}] Failed: {order_number} - {e.response.status_code}: {detail}")
            except Exception as e:
                error_count += 1
                logger.error(f"[{idx}/{len(b4b_orders)}] Failed: {order_number} - {e}")

    logger.info(f"Update complete: {success_count} updated, {error_count} errors")
    return 0 if error_count == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
