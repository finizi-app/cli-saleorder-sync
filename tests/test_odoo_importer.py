"""Unit tests for Odoo POS Importer with mocked XML-RPC responses."""

import json
import unittest
from unittest.mock import MagicMock, patch

from src.client import OdooClient
from src.importer import OdooPOSImporter
from src.models import PosOrder, PosOrderLine, PosOrderPayment
from src.timezone_utils import date_to_utc_range, format_utc_datetime
from src.formatters import format_orders_as_json, format_orders_as_jsonl


class TestTimezoneUtils(unittest.TestCase):
    """Test timezone conversion utilities."""

    def test_date_to_utc_range_ict(self):
        """Test ICT to UTC conversion."""
        start, end = date_to_utc_range("2026-03-11", "Asia/Ho_Chi_Minh")

        # ICT is UTC+7, so 00:00 ICT = 17:00 UTC previous day
        self.assertEqual(start, "2026-03-10 17:00:00")
        self.assertEqual(end, "2026-03-11 16:59:59")

    def test_format_utc_datetime(self):
        """Test datetime formatting."""
        result = format_utc_datetime("2026-03-11 10:30:00")
        self.assertEqual(result, "2026-03-11T10:30:00Z")

    def test_format_utc_datetime_empty(self):
        """Test empty datetime handling."""
        result = format_utc_datetime("")
        self.assertEqual(result, "")


class TestModels(unittest.TestCase):
    """Test data models."""

    def test_pos_order_line_to_dict(self):
        """Test PosOrderLine serialization."""
        line = PosOrderLine(
            id=1,
            product_id=(10, "Test Product"),
            name="Test Line",
            qty=2.0,
            price_unit=100.0,
            discount=10.0,
            price_subtotal=180.0,
            price_subtotal_incl=198.0,
        )
        result = line.to_dict()

        self.assertEqual(result["id"], 1)
        self.assertEqual(result["product_id"], 10)
        self.assertEqual(result["product_name"], "Test Product")
        self.assertEqual(result["qty"], 2.0)

    def test_pos_order_to_dict(self):
        """Test PosOrder serialization."""
        order = PosOrder(
            id=123,
            name="POS/2026/03/11/0001",
            date_order="2026-03-11T10:30:00Z",
            state="done",
            amount_total=150.0,
            user_id=(1, "Admin"),
        )
        result = order.to_dict()

        self.assertEqual(result["id"], 123)
        self.assertEqual(result["user_id"], 1)
        self.assertEqual(result["user_name"], "Admin")


class TestFormatters(unittest.TestCase):
    """Test output formatters."""

    def test_format_orders_as_json(self):
        """Test JSON formatter."""
        orders = [
            PosOrder(
                id=1,
                name="POS/001",
                date_order="2026-03-11T10:00:00Z",
                state="done",
                amount_total=100.0,
                amount_tax=10.0,
                amount_paid=100.0,
            ),
            PosOrder(
                id=2,
                name="POS/002",
                date_order="2026-03-11T11:00:00Z",
                state="done",
                amount_total=200.0,
                amount_tax=20.0,
                amount_paid=200.0,
            ),
        ]

        result = format_orders_as_json(
            orders=orders,
            query_date="2026-03-11",
            timezone="Asia/Ho_Chi_Minh",
        )

        self.assertEqual(result["metadata"]["query_date"], "2026-03-11")
        self.assertEqual(result["metadata"]["total_orders"], 2)
        self.assertEqual(result["metadata"]["total_amount"], 300.0)
        self.assertEqual(len(result["orders"]), 2)

    def test_format_orders_as_jsonl(self):
        """Test JSONL formatter."""
        orders = [
            PosOrder(id=1, name="POS/001", state="done", amount_total=100.0),
        ]

        result = format_orders_as_jsonl(orders)
        lines = result.strip().split("\n")

        self.assertEqual(len(lines), 1)
        parsed = json.loads(lines[0])
        self.assertEqual(parsed["id"], 1)


class TestOdooClientMocked(unittest.TestCase):
    """Test OdooClient with mocked XML-RPC."""

    @patch("src.client.ServerProxy")
    def test_connect_success(self, mock_server_proxy):
        """Test successful connection."""
        mock_common = MagicMock()
        mock_common.version.return_value = {"server_version": "16.0"}
        mock_common.authenticate.return_value = 1

        mock_server_proxy.side_effect = [mock_common, MagicMock()]

        client = OdooClient(
            url="https://test.odoo.com",
            db="test_db",
            username="admin",
            password="secret",
        )
        uid = client.connect()

        self.assertEqual(uid, 1)
        mock_common.authenticate.assert_called_once()

    @patch("src.client.ServerProxy")
    def test_connect_auth_failure(self, mock_server_proxy):
        """Test authentication failure."""
        mock_common = MagicMock()
        mock_common.version.return_value = {"server_version": "16.0"}
        mock_common.authenticate.return_value = False

        mock_server_proxy.return_value = mock_common

        client = OdooClient(
            url="https://test.odoo.com",
            db="test_db",
            username="admin",
            password="wrong",
        )

        with self.assertRaises(ValueError):
            client.connect()


class TestImporterMocked(unittest.TestCase):
    """Test OdooPOSImporter with mocked client."""

    def test_import_orders_empty(self):
        """Test import with no orders found."""
        mock_client = MagicMock()
        mock_client.search_read.return_value = []

        importer = OdooPOSImporter(mock_client)
        orders = importer.import_orders("2026-03-11")

        self.assertEqual(len(orders), 0)

    def test_import_orders_with_data(self):
        """Test import with mocked order data."""
        mock_client = MagicMock()

        # Mock order response
        mock_client.search_read.return_value = [
            {
                "id": 123,
                "name": "POS/2026/03/11/0001",
                "date_order": "2026-03-11 10:30:00",
                "pos_reference": "0011-001-0001",
                "partner_id": (1, "Test Customer"),
                "state": "done",
                "amount_total": 150.0,
                "amount_tax": 15.0,
                "amount_paid": 150.0,
                "amount_return": 0.0,
                "user_id": (1, "Admin"),
                "session_id": (1, "Main Session"),
                "lines": [1, 2],
                "payment_ids": [10],
            }
        ]

        # Mock line response
        mock_client.read.side_effect = [
            # Order lines
            [
                {
                    "id": 1,
                    "product_id": (100, "Product A"),
                    "name": "Product A",
                    "qty": 2.0,
                    "price_unit": 50.0,
                    "discount": 0.0,
                    "price_subtotal": 100.0,
                    "price_subtotal_incl": 110.0,
                },
                {
                    "id": 2,
                    "product_id": (101, "Product B"),
                    "name": "Product B",
                    "qty": 1.0,
                    "price_unit": 40.0,
                    "discount": 0.0,
                    "price_subtotal": 40.0,
                    "price_subtotal_incl": 44.0,
                },
            ],
            # Payments
            [
                {
                    "id": 10,
                    "journal_id": (1, "Cash"),
                    "amount": 150.0,
                    "payment_method_id": (1, "Cash"),
                }
            ],
        ]

        importer = OdooPOSImporter(mock_client)
        orders = importer.import_orders("2026-03-11")

        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0].id, 123)
        self.assertEqual(len(orders[0].lines), 2)
        self.assertEqual(len(orders[0].payments), 1)


if __name__ == "__main__":
    unittest.main()
