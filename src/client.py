"""Odoo XML-RPC client wrapper."""

import functools
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from xmlrpc.client import Fault, ServerProxy

logger = logging.getLogger(__name__)


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator for retrying failed operations.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except (ConnectionError, TimeoutError, Fault) as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
            raise last_exception
        return wrapper
    return decorator


class OdooClient:
    """XML-RPC client for Odoo server communication."""

    def __init__(self, url: str, db: str, username: str, password: str):
        """
        Initialize the Odoo client.

        Args:
            url: Odoo server URL (e.g., https://odoo.example.com)
            db: Database name
            username: Odoo username
            password: Password or API key
        """
        self.url = url.rstrip("/")
        self.db = db
        self.username = username
        self.password = password
        self.uid: Optional[int] = None
        self._models: Optional[ServerProxy] = None

    @retry(max_attempts=3)
    def connect(self) -> int:
        """
        Authenticate with Odoo server.

        Returns:
            User ID on successful authentication

        Raises:
            ConnectionError: If unable to connect to server
            ValueError: If authentication fails
        """
        common = ServerProxy(f"{self.url}/xmlrpc/2/common")

        # Get server version (also tests connection)
        version = common.version()
        logger.info(f"Connected to Odoo {version.get('server_version', 'unknown')}")

        # Authenticate
        uid = common.authenticate(self.db, self.username, self.password, {})
        if not uid:
            raise ValueError("Authentication failed: invalid credentials")

        self.uid = uid
        self._models = ServerProxy(f"{self.url}/xmlrpc/2/object")
        logger.info(f"Authenticated as user ID: {uid}")
        return uid

    def _ensure_connected(self) -> None:
        """Ensure client is connected before making API calls."""
        if not self.uid or not self._models:
            raise ConnectionError("Not connected. Call connect() first.")

    @retry(max_attempts=3)
    def search_read(
        self,
        model: str,
        domain: List[Any],
        fields: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        order: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search and read records from Odoo model.

        Args:
            model: Odoo model name (e.g., 'pos.order')
            domain: Search domain (e.g., [('state', '=', 'done')])
            fields: List of fields to read (None = all fields)
            limit: Maximum number of records to return
            offset: Number of records to skip
            order: Sort order (e.g., 'date_order desc')

        Returns:
            List of dictionaries with record data
        """
        self._ensure_connected()

        kwargs = {"domain": domain}
        if fields:
            kwargs["fields"] = fields
        if limit:
            kwargs["limit"] = limit
        if offset:
            kwargs["offset"] = offset
        if order:
            kwargs["order"] = order

        result = self._models.execute_kw(
            self.db,
            self.uid,
            self.password,
            model,
            "search_read",
            [],
            kwargs,
        )
        return result if result else []

    @retry(max_attempts=3)
    def search(
        self,
        model: str,
        domain: List[Any],
        limit: Optional[int] = None,
        offset: int = 0,
        order: Optional[str] = None,
    ) -> List[int]:
        """
        Search for record IDs matching domain.

        Args:
            model: Odoo model name
            domain: Search domain
            limit: Maximum number of records
            offset: Number of records to skip
            order: Sort order

        Returns:
            List of record IDs
        """
        self._ensure_connected()

        kwargs = {}
        if limit:
            kwargs["limit"] = limit
        if offset:
            kwargs["offset"] = offset
        if order:
            kwargs["order"] = order

        result = self._models.execute_kw(
            self.db,
            self.uid,
            self.password,
            model,
            "search",
            [domain],
            kwargs,
        )
        return result if result else []

    @retry(max_attempts=3)
    def read(
        self,
        model: str,
        ids: List[int],
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Read records by IDs.

        Args:
            model: Odoo model name
            ids: List of record IDs
            fields: List of fields to read (None = all fields)

        Returns:
            List of dictionaries with record data
        """
        self._ensure_connected()

        if not ids:
            return []

        kwargs = {}
        if fields:
            kwargs["fields"] = fields

        result = self._models.execute_kw(
            self.db,
            self.uid,
            self.password,
            model,
            "read",
            [ids],
            kwargs,
        )
        return result if result else []
