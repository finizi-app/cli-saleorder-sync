"""B4B API client for sale order import."""

import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class B4BClient:
    """HTTP client for B4B API."""

    def __init__(
        self,
        base_url: str,
        token: str,
        entity_id: str,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.entity_id = entity_id
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                headers=self._get_headers(),
                timeout=self.timeout,
            )
        return self._client

    def close(self):
        if self._client:
            self._client.close()
            self._client = None

    def create_sale_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a sale order via API."""
        url = f"/api/v1/entities/{self.entity_id}/sale-orders"
        client = self._get_client()

        response = client.post(url, json=order_data)
        response.raise_for_status()
        return response.json()

    def update_sale_order(
        self,
        order_id: str,
        order_data: Dict[str, Any],
        unlink_invoice: bool = False,
    ) -> Dict[str, Any]:
        """Update a sale order via API.

        Args:
            order_id: Sale order UUID
            order_data: Order data to update (partial update supported)
            unlink_invoice: If True, remove linked invoice
        """
        url = f"/api/v1/entities/{self.entity_id}/sale-orders/{order_id}"
        client = self._get_client()

        if unlink_invoice:
            order_data = {**order_data, "generated_invoice_id": None}

        response = client.put(url, json=order_data)
        response.raise_for_status()
        return response.json()

    def generate_vnpay_invoice(
        self,
        order_id: str,
        invoice_type: str = "pos",
        auto_release: bool = True,
        auto_sign: bool = True,
        auto_send_tax: bool = True,
    ) -> Dict[str, Any]:
        """Generate VNPay invoice for a sale order.

        Args:
            order_id: Sale order UUID
            invoice_type: Type of invoice ("vat", "sales", or "pos", default: "pos")
            auto_release: Auto release after creation (default: True)
            auto_sign: Auto digital sign (default: True)
            auto_send_tax: Auto send to tax authority (default: True)
        """
        url = f"/api/v1/entities/{self.entity_id}/sale-orders/{order_id}/generate-vnpay-invoice"
        client = self._get_client()

        params = {
            "invoice_type": invoice_type,
            "auto_release": str(auto_release).lower(),
            "auto_sign": str(auto_sign).lower(),
            "auto_send_tax": str(auto_send_tax).lower(),
        }
        response = client.post(url, params=params)
        response.raise_for_status()
        return response.json()

    def list_sale_orders(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List sale orders."""
        url = f"/api/v1/entities/{self.entity_id}/sale-orders"
        client = self._get_client()

        params = {"limit": limit, "offset": offset}
        response = client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
