# Code Standards
## Odoo POS to B4B Sale Order Sync CLI

This document outlines the coding standards and conventions used in the Odoo POS to B4B Sale Order Sync CLI project. These standards ensure code quality, maintainability, and consistency across the codebase.

## Overview

The project follows modern Python development practices with emphasis on type safety, readability, and maintainability. All code must adhere to these standards to ensure consistent quality throughout the codebase.

## General Principles

### YAGNI (You Aren't Gonna Need It)
- Only implement features that are currently needed
- Avoid over-engineering solutions for hypothetical future requirements
- Keep code simple and focused on current requirements

### KISS (Keep It Simple, Stupid)
- Prefer simple, straightforward solutions over complex ones
- Code should be easy to understand and modify
- Avoid unnecessary abstractions and design patterns

### DRY (Don't Repeat Yourself)
- Eliminate code duplication through abstraction and reuse
- Create reusable modules and functions
- Maintain single source of truth for common functionality

## File Structure

### Directory Organization
```
src/
├── __init__.py                  # Package initialization
├── cli.py                       # Odoo export CLI
├── b4b_import_cli.py           # B4B import CLI
├── client.py                   # Odoo XML-RPC client
├── importer.py                 # Odoo POS order importer
├── b4b_client.py               # B4B REST API client
├── order_mapper.py             # Order mapping logic
├── models.py                   # Data models
├── formatters.py               # Output formatters
└── timezone_utils.py           # Timezone utilities

tests/
├── __init__.py                 # Package initialization
└── test_odoo_importer.py       # Unit tests

docs/                          # Documentation
├── project-overview-pdr.md     # Product Development Requirements
├── codebase-summary.md         # Codebase overview
├── code-standards.md           # This file
├── system-architecture.md      # Architecture documentation
├── project-roadmap.md          # Development roadmap
└── deployment-guide.md         # Deployment instructions
```

### File Naming Conventions
- Use kebab-case for Python files: `order_mapper.py`
- Use snake_case for internal variables: `user_id`
- Use PascalCase for class names: `PosOrder`
- Use UPPER_CASE for constants: `MAX_RETRIES`

## Python Coding Standards

### Version Requirements
- **Python 3.10+** is required
- Use modern Python features appropriately
- Follow PEP 632 for typing standards

### Import Standards

#### Import Ordering
1. Standard library imports
2. Third-party imports
3. Local imports

```python
# Standard library
import json
import logging
import sys
from typing import Optional, Dict, List

# Third-party imports
import httpx
import pytz
from xmlrpc.client import Fault, ServerProxy

# Local imports
from .client import OdooClient
from .models import PosOrder
from .formatters import format_orders_as_json
```

#### Import Best Practices
- Always use specific imports: `from typing import Dict, List`
- Avoid wildcard imports: `import *`
- Use relative imports for local modules: `from .models import PosOrder`
- Group imports logically with blank lines between groups

### Function and Class Standards

#### Function Structure
```python
def function_name(
    param1: str,
    param2: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Brief description of function purpose.

    Args:
        param1: Description of first parameter
        param2: Description of second parameter (optional)

    Returns:
        Description of return value

    Raises:
        ValueError: When parameter validation fails
        ConnectionError: When network connection fails
    """
    # Implementation
    return result
```

#### Class Structure
```python
@dataclass
class ClassName:
    """
    Brief description of class purpose.

    Attributes:
        attribute1: Description of attribute1
        attribute2: Description of attribute2
    """

    attribute1: str
    attribute2: Optional[int] = None

    def method_name(self, param: str) -> bool:
        """
        Brief description of method purpose.

        Args:
            param: Description of parameter

        Returns:
            Description of return value
        """
        # Implementation
        return result
```

### Type Hints

#### Required Type Hints
- All function parameters and return values must have type hints
- Use `Optional[T]` for nullable parameters
- Use `List[T]`, `Dict[K, V]`, etc. for collection types

```python
def get_orders_by_date(
    date_str: str,
    timezone: str = "Asia/Ho_Chi_Minh",
    state: Optional[str] = None,
) -> List[PosOrder]:
    """Function with comprehensive type hints."""
    return orders
```

#### Type Aliases for Complex Types
```python
from typing import Dict, List, Any

OrderData = Dict[str, Any]
OrderList = List[OrderData]
ApiResult = Dict[str, Union[str, int, List]]
```

### Variable Naming

#### Variable Standards
- Use snake_case for variable names
- Use descriptive names that explain purpose
- Avoid abbreviations unless widely understood
- Use `_` for private variables

```python
# Good naming
order_id = 123
customer_name = "John Doe"
processed_orders_count = 0

# Avoid abbreviations
# Instead of: ord_id, cust_nm, proc_cnt
# Use: order_id, customer_name, processed_orders_count
```

#### Constants
```python
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30.0
API_BASE_URL = "https://api.example.com"
```

### Error Handling

#### Exception Handling Pattern
```python
try:
    # Attempt operation
    result = risky_operation()
except ConnectionError as e:
    logger.error(f"Network connection failed: {e}")
    raise
except ValueError as e:
    logger.error(f"Invalid input: {e}")
    raise ValueError(f"Invalid input: {e}") from e
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise RuntimeError(f"Operation failed: {e}") from e
```

#### Custom Exceptions
```python
class SyncError(Exception):
    """Base exception for sync operations."""
    pass

class OdooConnectionError(SyncError):
    """Exception for Odoo connection failures."""
    pass

class B4BApiError(SyncError):
    """Exception for B4B API failures."""
    pass
```

### Logging Standards

#### Logging Configuration
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
```

#### Logging Levels and Patterns
```python
# DEBUG - Detailed information for debugging
logger.debug(f"Processing order {order_id} with data: {order_data}")

# INFO - General information about operations
logger.info(f"Found {len(orders)} orders for date {date_str}")

# WARNING - Potential issues that don't stop execution
logger.warning(f"Rate limit approaching, throttling requests")

# ERROR - Errors that affect functionality
logger.error(f"Failed to connect to Odoo server: {connection_error}")

# CRITICAL - Critical errors that stop the application
logger.critical(f"Database connection lost, stopping operations")
```

#### Structured Logging
```python
logger.info(
    f"Order processed",
    extra={
        "order_id": order_id,
        "status": "success",
        "timestamp": datetime.utcnow().isoformat(),
    }
)
```

### Documentation Standards

#### Docstring Format
```python
def function_name(param1: str, param2: int) -> Dict[str, Any]:
    """
    Brief description of function purpose.

    Args:
        param1: Description of the first parameter
        param2: Description of the second parameter

    Returns:
        Dictionary containing the function results

    Raises:
        ValueError: When param1 is invalid
        ConnectionError: When network connection fails

    Example:
        >>> result = function_name("test", 123)
        >>> print(result)
        {'status': 'success'}
    """
    # Implementation
    return result
```

#### Module Documentation
```python
"""
Module for Odoo POS order import functionality.

This module provides classes and functions for importing POS orders
from Odoo servers via XML-RPC API, including timezone conversion
and data validation.

Classes:
    OdooClient: XML-RPC client for Odoo communication
    OdooPOSImporter: Order importer with data assembly

Functions:
    import_orders: Import orders for specific date range

Example:
    >>> client = OdooClient(url, db, username, password)
    >>> importer = OdooPOSImporter(client)
    >>> orders = importer.import_orders("2026-03-11")
"""
```

## Testing Standards

### Test File Structure
```python
"""Unit tests for Odoo POS Importer."""

import unittest
from unittest.mock import MagicMock, patch

from src.client import OdooClient
from src.importer import OdooPOSImporter
from src.models import PosOrder


class TestOdooImporter(unittest.TestCase):
    """Test suite for OdooPOSImporter."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = MagicMock()
        self.importer = OdooPOSImporter(self.mock_client)

    def test_import_orders_empty(self):
        """Test import with no orders."""
        self.mock_client.search_read.return_value = []
        orders = self.importer.import_orders("2026-03-11")
        self.assertEqual(len(orders), 0)

    @patch('src.client.ServerProxy')
    def test_connect_success(self, mock_server_proxy):
        """Test successful connection."""
        # Mock setup
        mock_common = MagicMock()
        mock_common.version.return_value = {"server_version": "16.0"}
        mock_common.authenticate.return_value = 1

        # Test implementation
        client = OdooClient("https://test.com", "test_db", "admin", "secret")
        result = client.connect()

        # Assertions
        self.assertEqual(result, 1)
```

### Test Naming
- Use `test_` prefix for test methods
- Use descriptive names that explain what is being tested
- Group related tests in test classes

```python
class TestTimezoneUtils:
    """Test timezone utility functions."""

    def test_date_to_utc_range_ict(self):
        """Test ICT to UTC conversion."""

    def test_date_to_utc_range_dst(self):
        """Test conversion during daylight saving time."""
```

### Assertion Standards
- Use specific, descriptive assertions
- Provide clear assertion messages when needed
- Test both success and failure cases

```python
# Good assertions
self.assertEqual(len(orders), 5, "Expected 5 orders for the given date")
self.assertTrue(order.is_processed, "Order should be marked as processed")
self.assertIsInstance(order, PosOrder, "Should return PosOrder objects")

# Avoid generic assertions
# self.assertEqual(result, True)  # Not descriptive
# Better: self.assertTrue(result.success, "Operation should succeed")
```

## Performance Standards

### Memory Management
- Use generators for large datasets instead of lists
- Clean up resources properly (context managers)
- Avoid unnecessary object creation in loops

```python
# Good - Using generator
def process_large_dataset():
    for item in large_dataset:
        yield process_item(item)

# Avoid - Loading entire dataset into memory
# all_items = list(large_dataset)  # Can cause memory issues
```

### Network Optimization
- Use connection pooling for HTTP requests
- Implement proper timeout handling
- Batch operations when possible

```python
# Good - Context manager for HTTP client
with B4BClient(url, token, entity_id) as client:
    results = [client.create_order(order) for order in orders]

# Avoid - Creating new connections for each request
# for order in orders:
#     client = B4BClient(url, token, entity_id)  # Inefficient
#     result = client.create_order(order)
```

## Security Standards

### Input Validation
```python
def validate_order_data(order_data: Dict[str, Any]) -> None:
    """Validate order data before processing."""
    if not order_data.get("order_number"):
        raise ValueError("Order number is required")

    if not isinstance(order_data.get("lines"), list):
        raise ValueError("Lines must be a list")

    # Additional validation logic
```

### Data Sanitization
- Remove or sanitize sensitive data before logging
- Validate all external inputs
- Use parameterized queries where applicable

```python
# Good - Sanitize logging data
logger.info(f"Processing order {order_id}", extra={"data": sanitize_data(order_data)})

# Avoid - Logging sensitive data
# logger.info(f"Processing order {order_id} with data: {order_data}")  # Risky
```

## Code Review Checklist

### Before Code Review
- [ ] All code follows the established patterns
- [ ] Type hints are complete and correct
- [ ] Error handling is comprehensive
- [ ] Tests cover all new functionality
- [ ] Documentation is up to date
- [ ] Code passes linting and formatting checks

### Review Focus Areas
- [ ] Readability and maintainability
- [ ] Correctness and edge cases
- [ ] Performance implications
- [ ] Security considerations
- [ ] Test coverage and quality
- [ ] Documentation completeness

## Tooling and Automation

### Code Formatting
```bash
# Format code with Black
black src/ tests/

# Check formatting
black --check src/ tests/

# Lint with Ruff
ruff check src/ tests/

# Auto-fix linting issues
ruff check src/ tests/ --fix
```

### Testing
```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific test file
python -m pytest tests/test_odoo_importer.py -v

# Run specific test method
python -m pytest tests/test_odoo_importer.py::TestTimezoneUtils::test_date_to_utc_range_ict -v
```

## Continuous Integration

### Pre-commit Hooks
- Black formatting check
- Ruff linting
- Test suite execution
- Type checking (mypy)

### Quality Gates
- Code coverage must be 80%+
- No linting errors allowed
- All tests must pass
- Security scan must pass

---

*These standards should be followed by all contributors to maintain code quality and consistency. Regular updates may be made to reflect new best practices and evolving requirements.*