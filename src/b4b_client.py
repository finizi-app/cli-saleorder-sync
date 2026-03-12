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

    def generate_vnpay_invoice(self, order_id: str, invoice_type: str = "pos") -> Dict[str, Any]:
        """Generate VNPay invoice for a sale order.

        Args:
            order_id: Sale order UUID
            invoice_type: Type of invoice ("pos" for POS orders, default: "pos")
        """
        url = f"/api/v1/entities/{self.entity_id}/sale-orders/{order_id}/generate-vnpay-invoice"
        client = self._get_client()

        # Try query parameter first
        response = client.post(url, params={"invoice_type": invoice_type})
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
