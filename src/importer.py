"""POS order importer from Odoo."""

import logging
from typing import Any, Dict, List, Optional

from .client import OdooClient
from .models import PosOrder, PosOrderLine, PosOrderPayment
from .timezone_utils import date_to_utc_range, format_utc_datetime

logger = logging.getLogger(__name__)


# Field definitions for Odoo queries
ORDER_FIELDS = [
    "id",
    "name",
    "date_order",
    "pos_reference",
    "partner_id",
    "state",
    "amount_total",
    "amount_tax",
    "amount_paid",
    "amount_return",
    "user_id",
    "session_id",
    "lines",
    "payment_ids",
]

LINE_FIELDS = [
    "id",
    "product_id",
    "name",
    "qty",
    "price_unit",
    "discount",
    "price_subtotal",
    "price_subtotal_incl",
]

PAYMENT_FIELDS = [
    "id",
    "name",
    "amount",
    "payment_method_id",
    "payment_date",
    "is_change",
]


class OdooPOSImporter:
    """Import POS orders from Odoo server."""

    def __init__(self, client: OdooClient):
        """
        Initialize the importer.

        Args:
            client: Authenticated OdooClient instance
        """
        self.client = client

    def import_orders(
        self,
        date_str: str,
        timezone: str = "Asia/Ho_Chi_Minh",
        state: Optional[str] = None,
    ) -> List[PosOrder]:
        """
        Import POS orders for a specific date.

        Args:
            date_str: Date in YYYY-MM-DD format (local timezone)
            timezone: Timezone name for date conversion
            state: Optional state filter (e.g., 'done', 'paid')

        Returns:
            List of PosOrder objects
        """
        # Convert local date to UTC range
        start_utc, end_utc = date_to_utc_range(date_str, timezone)
        logger.info(f"Querying orders from {start_utc} to {end_utc} UTC")

        # Build domain for pos.order
        domain = [
            ("date_order", ">=", start_utc),
            ("date_order", "<=", end_utc),
        ]
        if state:
            domain.append(("state", "=", state))

        # Fetch orders
        order_records = self.client.search_read(
            model="pos.order",
            domain=domain,
            fields=ORDER_FIELDS,
            order="date_order asc",
        )

        if not order_records:
            logger.info(f"No orders found for date {date_str}")
            return []

        logger.info(f"Found {len(order_records)} orders")

        # Collect all line IDs and payment IDs for batch fetching
        all_line_ids: List[int] = []
        all_payment_ids: List[int] = []
        for order in order_records:
            all_line_ids.extend(order.get("lines", []))
            all_payment_ids.extend(order.get("payment_ids", []))

        # Batch fetch lines and payments
        lines_by_id: Dict[int, Dict[str, Any]] = {}
        payments_by_id: Dict[int, Dict[str, Any]] = {}

        if all_line_ids:
            line_records = self.client.read(
                model="pos.order.line",
                ids=all_line_ids,
                fields=LINE_FIELDS,
            )
            lines_by_id = {line["id"]: line for line in line_records}
            logger.info(f"Fetched {len(line_records)} order lines")

        if all_payment_ids:
            payment_records = self.client.read(
                model="pos.payment",
                ids=all_payment_ids,
                fields=PAYMENT_FIELDS,
            )
            payments_by_id = {p["id"]: p for p in payment_records}
            logger.info(f"Fetched {len(payment_records)} payments")

        # Assemble PosOrder objects
        orders: List[PosOrder] = []
        for record in order_records:
            order = self._assemble_order(
                record, lines_by_id, payments_by_id
            )
            orders.append(order)

        return orders

    def _assemble_order(
        self,
        record: Dict[str, Any],
        lines_by_id: Dict[int, Dict[str, Any]],
        payments_by_id: Dict[int, Dict[str, Any]],
    ) -> PosOrder:
        """
        Assemble a PosOrder from record and related data.

        Args:
            record: Order record from Odoo
            lines_by_id: Dictionary of line records by ID
            payments_by_id: Dictionary of payment records by ID

        Returns:
            PosOrder object
        """
        # Create order object
        order = PosOrder(
            id=record["id"],
            name=record.get("name", ""),
            date_order=format_utc_datetime(record.get("date_order", "")),
            pos_reference=record.get("pos_reference", ""),
            partner_id=record.get("partner_id"),
            state=record.get("state", ""),
            amount_total=record.get("amount_total", 0.0),
            amount_tax=record.get("amount_tax", 0.0),
            amount_paid=record.get("amount_paid", 0.0),
            amount_return=record.get("amount_return", 0.0),
            user_id=record.get("user_id"),
            session_id=record.get("session_id"),
        )

        # Add lines
        for line_id in record.get("lines", []):
            if line_id in lines_by_id:
                line_record = lines_by_id[line_id]
                order.lines.append(
                    PosOrderLine(
                        id=line_record["id"],
                        product_id=line_record.get("product_id"),
                        name=line_record.get("name", ""),
                        qty=line_record.get("qty", 0.0),
                        price_unit=line_record.get("price_unit", 0.0),
                        discount=line_record.get("discount", 0.0),
                        price_subtotal=line_record.get("price_subtotal", 0.0),
                        price_subtotal_incl=line_record.get("price_subtotal_incl", 0.0),
                    )
                )

        # Add payments
        for payment_id in record.get("payment_ids", []):
            if payment_id in payments_by_id:
                payment_record = payments_by_id[payment_id]
                order.payments.append(
                    PosOrderPayment(
                        id=payment_record["id"],
                        name=payment_record.get("name", ""),
                        amount=payment_record.get("amount", 0.0),
                        payment_method_id=payment_record.get("payment_method_id"),
                        payment_date=payment_record.get("payment_date", ""),
                        is_change=payment_record.get("is_change", False),
                    )
                )

        return order

    def get_order_by_id(self, order_id: int) -> Optional[PosOrder]:
        """
        Get a single order by ID.

        Args:
            order_id: Order ID

        Returns:
            PosOrder or None if not found
        """
        records = self.client.search_read(
            model="pos.order",
            domain=[("id", "=", order_id)],
            fields=ORDER_FIELDS,
            limit=1,
        )

        if not records:
            return None

        record = records[0]

        # Fetch lines and payments
        lines_by_id: Dict[int, Dict[str, Any]] = {}
        payments_by_id: Dict[int, Dict[str, Any]] = {}

        line_ids = record.get("lines", [])
        if line_ids:
            line_records = self.client.read(
                model="pos.order.line",
                ids=line_ids,
                fields=LINE_FIELDS,
            )
            lines_by_id = {line["id"]: line for line in line_records}

        payment_ids = record.get("payment_ids", [])
        if payment_ids:
            payment_records = self.client.read(
                model="account.bank.statement.line",
                ids=payment_ids,
                fields=PAYMENT_FIELDS,
            )
            payments_by_id = {p["id"]: p for p in payment_records}

        return self._assemble_order(record, lines_by_id, payments_by_id)
