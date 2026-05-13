"""Odoo POS Sale Order Import CLI."""

__version__ = "0.1.0"

# Import OdooClient for easy access
from .client import OdooClient

__all__ = ["OdooClient"]
