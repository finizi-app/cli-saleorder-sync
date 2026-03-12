"""Map Odoo POS orders to B4B Sale Order format (Tax-Aware).

B4B API Tax-Aware Format:
    - unit_price_without_tax: Price excluding VAT (required)
    - unit_price_with_tax: Price including VAT (optional, can be derived)
    - vat_rate: Decimal VAT rate (B4B resolves to vat_rate_id from master data)
    - Legacy fields: unit_price, subtotal, vat_amount, total_amount still supported

The mapper provides both explicit tax-aware fields and legacy fields for compatibility.
"""

from datetime import datetime
from typing import Any, Dict, List


def calculate_vat_rate(price_subtotal: float, price_subtotal_incl: float) -> float:
    """Calculate VAT rate from pre-tax and inclusive prices."""
    if price_subtotal <= 0:
        return 0.0
    return (price_subtotal_incl / price_subtotal) - 1.0


def map_order_line(odoo_line: Dict[str, Any], line_number: int = 1) -> Dict[str, Any]:
    """Map Odoo order line to B4B tax-aware line format.

    Tax-Aware Pricing:
    - unit_price_without_tax: Price excluding VAT (required)
    - unit_price_with_tax: Price including VAT (auto-calculated by B4B)
    - vat_rate: Decimal VAT rate (B4B will resolve to vat_rate_id)

    Odoo provides price_subtotal (excl. tax) and price_subtotal_incl (incl. tax).
    """
    price_subtotal = odoo_line.get("price_subtotal", 0.0)
    price_subtotal_incl = odoo_line.get("price_subtotal_incl", price_subtotal)
    qty = odoo_line.get("qty", 1.0)

    # Calculate unit price excluding tax
    unit_price_excl_tax = price_subtotal / qty if qty > 0 else 0.0

    # Calculate unit price including tax (for completeness, B4B can also derive this)
    unit_price_incl_tax = price_subtotal_incl / qty if qty > 0 else 0.0

    return {
        "line_number": line_number,
        "item_code": odoo_line.get("product_code") or None,
        "item_name": odoo_line.get("product_name") or None,
        "description": odoo_line.get("name", ""),
        "quantity": qty,
        # Tax-aware pricing (explicit naming)
        "unit_price_without_tax": round(unit_price_excl_tax, 2),
        "unit_price_with_tax": round(unit_price_incl_tax, 2),
        "discount_amount": odoo_line.get("discount", 0.0),
        # VAT rate as decimal (B4B will resolve to vat_rate_id)
        "vat_rate": round(calculate_vat_rate(price_subtotal, price_subtotal_incl), 4),
    }


def extract_date(datetime_str: str) -> str:
    """Extract date portion from datetime string."""
    if not datetime_str:
        return datetime.utcnow().strftime("%Y-%m-%d")
    # Handle both ISO format and space-separated
    return datetime_str.split("T")[0].split(" ")[0]


def map_status(odoo_state: str) -> str:
    """Map Odoo state to B4B status."""
    mapping = {
        "done": "completed",
        "paid": "paid",
        "draft": "draft",
        "invoiced": "invoiced",
        "cancel": "cancelled",
    }
    return mapping.get(odoo_state, "draft")


def map_order(odoo_order: Dict[str, Any]) -> Dict[str, Any]:
    """Map Odoo POS order to B4B SaleOrder format."""
    # Map lines
    lines = [
        map_order_line(line, idx + 1)
        for idx, line in enumerate(odoo_order.get("lines", []))
    ]

    # Get payment method from first payment
    payments = odoo_order.get("payments", [])
    payment_method = payments[0].get("payment_method_name") if payments else None

    return {
        "order_number": odoo_order.get("name", ""),
        "reference_number": odoo_order.get("pos_reference") or None,
        "order_date": extract_date(odoo_order.get("date_order", "")),
        "status": map_status(odoo_order.get("state", "draft")),
        "currency": "VND",
        "payment_method": payment_method,
        "customer_name": odoo_order.get("partner_name") or None,
        "lines": lines,
    }


def map_orders(odoo_orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Map multiple Odoo orders to B4B format."""
    return [map_order(order) for order in odoo_orders]
