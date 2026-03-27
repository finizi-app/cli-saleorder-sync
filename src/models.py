"""Data models for POS orders."""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


def parse_product_name(full_name: str) -> Tuple[str, str]:
    """
    Parse product name to extract code and name.

    Args:
        full_name: Full product name like "[D_SD_003] Aquafina 500ml"

    Returns:
        Tuple of (code, name) e.g., ("D_SD_003", "Aquafina 500ml")
    """
    if not full_name:
        return ("", "")
    match = re.match(r"\[([^\]]+)\]\s*(.*)", full_name)
    if match:
        return (match.group(1), match.group(2).strip())
    return ("", full_name)


@dataclass
class PosOrderLine:
    """Represents a single line item in a POS order."""

    id: int
    product_id: Optional[Tuple[int, str]] = None
    product_code: str = ""
    product_name: str = ""
    name: str = ""
    qty: float = 0.0
    price_unit: float = 0.0
    discount: float = 0.0
    price_subtotal: float = 0.0
    price_subtotal_incl: float = 0.0
    uom_id: Optional[Tuple[int, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        # Parse product code and name from the full product display name
        full_name = self.product_id[1] if self.product_id else self.product_name
        code, name = parse_product_name(full_name)

        return {
            "id": self.id,
            "product_id": self.product_id[0] if self.product_id else None,
            "product_code": code or self.product_code,
            "product_name": name or self.product_name,
            "name": self.name,
            "qty": self.qty,
            "price_unit": self.price_unit,
            "discount": self.discount,
            "price_subtotal": self.price_subtotal,
            "price_subtotal_incl": self.price_subtotal_incl,
            "uom_id": self.uom_id[0] if self.uom_id else None,
            "uom_name": self.uom_id[1] if self.uom_id else "",
        }


@dataclass
class PosOrderPayment:
    """Represents a payment in a POS order."""

    id: int
    name: str = ""
    amount: float = 0.0
    payment_method_id: Optional[Tuple[int, str]] = None
    payment_date: str = ""
    is_change: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "amount": self.amount,
            "payment_method_id": self.payment_method_id[0] if self.payment_method_id else None,
            "payment_method_name": self.payment_method_id[1] if self.payment_method_id else "",
            "payment_date": self.payment_date,
            "is_change": self.is_change,
        }


@dataclass
class PosOrder:
    """Represents a complete POS order with lines and payments."""

    id: int
    name: str = ""
    date_order: str = ""
    pos_reference: str = ""
    partner_id: Optional[Tuple[int, str]] = None
    state: str = ""
    amount_total: float = 0.0
    amount_tax: float = 0.0
    amount_paid: float = 0.0
    amount_return: float = 0.0
    user_id: Optional[Tuple[int, str]] = None
    session_id: Optional[Tuple[int, str]] = None
    lines: List[PosOrderLine] = field(default_factory=list)
    payments: List[PosOrderPayment] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "date_order": self.date_order,
            "pos_reference": self.pos_reference,
            "partner_id": self.partner_id[0] if self.partner_id else None,
            "partner_name": self.partner_id[1] if self.partner_id else "",
            "state": self.state,
            "amount_total": self.amount_total,
            "amount_tax": self.amount_tax,
            "amount_paid": self.amount_paid,
            "amount_return": self.amount_return,
            "user_id": self.user_id[0] if self.user_id else None,
            "user_name": self.user_id[1] if self.user_id else "",
            "session_id": self.session_id[0] if self.session_id else None,
            "session_name": self.session_id[1] if self.session_id else "",
            "lines": [line.to_dict() for line in self.lines],
            "payments": [payment.to_dict() for payment in self.payments],
        }
