"""Output formatters for POS order data."""

import json
from datetime import datetime
from typing import Any, Dict, List

from .models import PosOrder


def format_orders_as_json(
    orders: List[PosOrder],
    query_date: str,
    timezone: str = "Asia/Ho_Chi_Minh",
) -> Dict[str, Any]:
    """
    Format orders as structured JSON output.

    Args:
        orders: List of PosOrder objects
        query_date: Original query date string
        timezone: Timezone used for query

    Returns:
        Dictionary ready for JSON serialization
    """
    # Calculate totals
    total_amount = sum(order.amount_total for order in orders)
    total_tax = sum(order.amount_tax for order in orders)
    total_paid = sum(order.amount_paid for order in orders)

    return {
        "metadata": {
            "query_date": query_date,
            "timezone": timezone,
            "exported_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total_orders": len(orders),
            "total_amount": round(total_amount, 2),
            "total_tax": round(total_tax, 2),
            "total_paid": round(total_paid, 2),
        },
        "orders": [order.to_dict() for order in orders],
    }


def format_orders_as_jsonl(orders: List[PosOrder]) -> str:
    """
    Format orders as JSON Lines (one JSON object per line).

    Args:
        orders: List of PosOrder objects

    Returns:
        String with one JSON object per line
    """
    lines = [json.dumps(order.to_dict()) for order in orders]
    return "\n".join(lines)


def format_orders_as_csv(orders: List[PosOrder]) -> str:
    """
    Format orders as CSV (flat structure, one row per order).

    Args:
        orders: List of PosOrder objects

    Returns:
        CSV string with header and data rows
    """
    if not orders:
        return ""

    # Header
    header = [
        "order_id",
        "order_name",
        "date_order",
        "pos_reference",
        "partner_name",
        "state",
        "amount_total",
        "amount_tax",
        "amount_paid",
        "amount_return",
        "user_name",
        "line_count",
        "payment_count",
    ]

    rows = [",".join(header)]

    # Data rows
    for order in orders:
        row = [
            str(order.id),
            _csv_escape(order.name),
            order.date_order,
            _csv_escape(order.pos_reference),
            _csv_escape(order.partner_id[1] if order.partner_id else ""),
            order.state,
            str(order.amount_total),
            str(order.amount_tax),
            str(order.amount_paid),
            str(order.amount_return),
            _csv_escape(order.user_id[1] if order.user_id else ""),
            str(len(order.lines)),
            str(len(order.payments)),
        ]
        rows.append(",".join(row))

    return "\n".join(rows)


def _csv_escape(value: str) -> str:
    """Escape a value for CSV format."""
    if not value:
        return ""
    # Quote if contains comma, quote, or newline
    if "," in value or '"' in value or "\n" in value:
        return f'"{value.replace(chr(34), chr(34) + chr(34))}"'
    return value
