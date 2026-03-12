# Deployment Guide
## Odoo POS to B4B Sale Order Sync CLI

## Overview

This deployment guide provides comprehensive instructions for setting up, configuring, and deploying the Odoo POS to B4B Sale Order Sync CLI in various environments. The guide covers development, staging, and production deployments with best practices for security, monitoring, and maintenance.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Configuration](#configuration)
4. [Installation](#installation)
5. [Testing](#testing)
6. [Production Deployment](#production-deployment)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)
9. [Security Considerations](#security-considerations)
10. [Backup & Recovery](#backup--recovery)

## Prerequisites

### System Requirements
- **Python**: 3.10 or higher
- **Memory**: Minimum 512MB RAM (1GB+ recommended)
- **Storage**: 100MB free space for installation
- **Network**: Internet connectivity to Odoo and B4B APIs
- **Operating System**: Linux, macOS, or Windows

### External System Requirements
- **Odoo Server**: Version 14 or higher with XML-RPC API enabled
- **B4B Platform**: Access to B4B REST API v1 endpoints
- **Network**: HTTPS connectivity to both systems
- **DNS**: Proper resolution for all system URLs

### Python Dependencies
```bash
# Core dependencies (auto-installed with pip)
pytz>=2024.1          # Timezone handling
httpx>=0.24.0          # HTTP client for B4B API
xmlrpc.client          # Built-in XML-RPC client

# Development dependencies (optional)
pytest>=7.0            # Testing framework
pytest-cov>=4.0        # Coverage reporting
black>=23.0            # Code formatter
ruff>=0.1.0            # Linter
```

## Environment Setup

### Development Environment

```bash
# 1. Clone the repository
git clone https://github.com/finizi-app/cli-saleorder-sync.git
cd cli-saleorder-sync

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -e .

# 4. Install development dependencies (optional)
pip install -e ".[dev]"

# 5. Verify installation
python -m src.cli --help
python -m src.b4b_import_cli --help
```

### Production Environment

```bash
# 1. Create dedicated user for the application
sudo adduser --system --home /opt/odoo-sync odoo-sync

# 2. Switch to application user
sudo -u odoo-sync

# 3. Set up environment
cd /opt/odoo-sync
python3 -m venv venv
source venv/bin/activate

# 4. Install application
pip install -e .

# 5. Create configuration directory
mkdir -p /etc/odoo-sync
chmod 700 /etc/odoo-sync
```

## Configuration

### Environment Variables

Create a configuration file for your environment:

```bash
# Development environment
cat > .env << EOF
# Odoo Configuration
ODOO_URL=https://dev-odoo.example.com
ODOO_DB=dev_database
ODOO_USERNAME=admin
ODOO_PASSWORD=dev_password

# B4B Configuration
B4B_API_URL=https://api.b4b.example.com
B4B_TOKEN=dev-jwt-token
B4B_ENTITY_ID=dev-entity-id
EOF

# Production environment (system-wide)
sudo nano /etc/odoo-sync/.env
```

### Configuration Options

#### Required Variables
| Variable | Description | Example |
|----------|-------------|---------|
| `ODOO_URL` | Odoo server URL | `https://odoo.example.com` |
| `ODOO_DB` | Odoo database name | `production_db` |
| `ODOO_USERNAME` | Odoo username | `admin` |
| `ODOO_PASSWORD` | Odoo password/API key | `your_secret_password` |
| `B4B_API_URL` | B4B API base URL | `https://api.b4b.example.com` |
| `B4B_TOKEN` | JWT Bearer token | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |
| `B4B_ENTITY_ID` | B4B entity UUID | `c7601608-766d-452f-975e-184bef0da5e7` |

#### Optional Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `ODOO_TIMEZONE` | Timezone for date queries | `Asia/Ho_Chi_Minh` |
| `B4B_TIMEOUT` | B4B API timeout in seconds | `30` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `MAX_RETRIES` | Maximum retry attempts | `3` |

## Installation

### Development Installation

```bash
# 1. Clone and set up development environment
git clone https://github.com/finizi-app/cli-saleorder-sync.git
cd cli-saleorder-sync

# 2. Install in development mode
pip install -e .

# 3. Verify installation
python -m pytest tests/ -v

# 4. Test basic functionality
python -m src.cli --help
python -m src.b4b_import_cli --help
```

### Production Installation

#### Option 1: System Package (Recommended)

```bash
# 1. Create systemd service file
sudo nano /etc/systemd/system/odoo-sync.service

[Unit]
Description=Odoo to B4B Sync Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=odoo-sync
Group=odoo-sync
WorkingDirectory=/opt/odoo-sync
Environment=PATH=/opt/odoo-sync/venv/bin
ExecStart=/opt/odoo-sync/venv/bin/python -m src.cli --date $(date +%Y-%m-%d)
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

#### Option 2: Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY tests/ ./tests/

# Create non-root user
RUN useradd -m -u 1000 odoo-sync
USER odoo-sync

# Set environment variables
ENV PYTHONPATH=/app
ENV ODOO_TIMEZONE=Asia/Ho_Chi_Minh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

CMD ["python", "-m", "src.cli", "--date", "$(date +%Y-%m-%d)"]
```

```bash
# Build Docker image
docker build -t odoo-sync:latest .

# Run Docker container
docker run -d \
  --name odoo-sync \
  --env-file /etc/odoo-sync/.env \
  -v /var/log/odoo-sync:/app/logs \
  odoo-sync:latest
```

## Testing

### Development Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific test file
python -m pytest tests/test_odoo_importer.py -v

# Run tests with verbose output
python -m pytest tests/ -v --tb=short
```

### Production Testing

```bash
# 1. Test configuration
python -c "from config_manager import ConfigManager; ConfigManager().validate()"

# 2. Test Odoo connection
python -m src.cli --url https://odoo.example.com --db test_db \
    --username test_user --password test_pass --date $(date +%Y-%m-%d) --dry-run

# 3. Test B4B connection
python -m src.b4b_import_cli --input test-orders.json --dry-run \
    --url https://api.b4b.example.com --token test-token --entity-id test-entity
```

## Production Deployment

### 1. Pre-Deployment Checklist

```bash
# System requirements check
python3 --version  # Should be 3.10+
free -h           # Should have 1GB+ free memory
df -h             # Should have 100MB+ free space

# Network connectivity
curl -I https://odoo.example.com
curl -I https://api.b4b.example.com

# Configuration validation
python -c "from config_manager import ConfigManager; ConfigManager().validate()"
```

### 2. Deployment Steps

```bash
# 1. Backup current configuration (if exists)
sudo cp -r /etc/odoo-sync /etc/odoo-sync.backup.$(date +%Y%m%d)

# 2. Update application code
sudo -u odoo-sync git -C /opt/odoo-sync pull origin main

# 3. Update dependencies
sudo -u odoo-sync pip install -e .

# 4. Validate configuration
sudo -u odoo-sync python -c "from config_manager import ConfigManager; ConfigManager().validate()"

# 5. Run test import (dry run)
sudo -u odoo-sync python -m src.cli --date $(date +%Y-%m-%d) --output test-import.json --dry-run

# 6. Update systemd service
sudo systemctl daemon-reload

# 7. Restart service
sudo systemctl restart odoo-sync

# 8. Check service status
sudo systemctl status odoo-sync
sudo journalctl -u odoo-sync --since "5 minutes ago" -f
```

## Monitoring & Maintenance

### Logging Configuration

```python
# logging_config.py
import logging
import logging.handlers
from pathlib import Path

def setup_logging():
    """Configure logging for production."""
    log_dir = Path("/var/log/odoo-sync")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "odoo-sync.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
```

### Monitoring Scripts

```bash
# monitor_sync.sh
#!/bin/bash

# Check service status
check_service() {
    if systemctl is-active --quiet odoo-sync; then
        echo "✓ Service is running"
    else
        echo "✗ Service is not running"
        systemctl restart odoo-sync
        echo "✗ Service restarted"
    fi
}

# Check disk space
check_disk() {
    USAGE=$(df /var/log/odoo-sync | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ $USAGE -gt 80 ]; then
        echo "⚠ Disk usage at ${USAGE}%"
    else
        echo "✓ Disk usage OK (${USAGE}%)"
    fi
}

# Main monitoring
check_service
check_disk
```

## Troubleshooting

### Common Issues

#### 1. Connection Errors

**Problem**: `ConnectionError: Unable to connect to Odoo server`
```bash
# Solution: Check network connectivity
ping odoo.example.com
curl -I https://odoo.example.com

# Check firewall
sudo ufw status
sudo iptables -L

# Test with verbose logging
python -m src.cli --verbose --date $(date +%Y-%m-%d)
```

#### 2. Authentication Issues

**Problem**: `ValueError: Authentication failed`
```bash
# Solution: Verify credentials
python -c "
import sys
sys.path.append('src')
from client import OdooClient
client = OdooClient('https://odoo.example.com', 'db', 'user', 'pass')
try:
    client.connect()
    print('Authentication successful')
except Exception as e:
    print(f'Authentication failed: {e}')
"
```

#### 3. API Rate Limiting

**Problem**: `httpx.HTTPStatusError: 429 Too Many Requests`
```bash
# Solution: Add delay between requests
python -m src.b4b_import_cli --input orders.json --limit 10 --log import.log
```

### Debug Mode

```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG

# Test with detailed output
python -m src.cli --verbose --date $(date +%Y-%m-%d)
```

## Security Considerations

### 1. Credential Management

```bash
# Store secrets securely
sudo chmod 600 /etc/odoo-sync/.env

# Use key management service (AWS KMS, Hashicorp Vault)
# Example with environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export KMS_KEY_ID=your_key_id
```

### 2. Network Security

```bash
# Configure firewall
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP (if needed)
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable
```

## Backup & Recovery

### 1. Configuration Backup

```bash
#!/bin/bash
# backup-config.sh

BACKUP_DIR="/backup/odoo-sync"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup configuration
sudo cp -r /etc/odoo-sync "$BACKUP_DIR/config_$TIMESTAMP"

# Backup logs
sudo cp -r /var/log/odoo-sync "$BACKUP_DIR/logs_$TIMESTAMP"

# Compress backup
cd "$BACKUP_DIR"
tar -czf "backup_$TIMESTAMP.tar.gz" "config_$TIMESTAMP" "logs_$TIMESTAMP"

echo "Backup completed: backup_$TIMESTAMP.tar.gz"
```

### 2. Recovery Procedure

```bash
#!/bin/bash
# restore-config.sh

BACKUP_FILE="$1"
BACKUP_DIR="/backup/odoo-sync"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Extract backup
tar -xzf "$BACKUP_FILE" -C "$BACKUP_DIR"

# Restore configuration
sudo cp -r "$BACKUP_DIR/config_*/"* /etc/odoo-sync/

# Restore logs
sudo cp -r "$BACKUP_DIR/logs_/"* /var/log/odoo-sync/

# Restart service
sudo systemctl restart odoo-sync

echo "Recovery completed"
```

## Best Practices

### 1. Deployment Best Practices

- Always test in staging environment first
- Use version control for configuration
- Document all changes and deployments
- Perform regular security audits
- Monitor system health continuously

### 2. Security Best Practices

- Use least privilege principle for service accounts
- Regularly update dependencies and patches
- Implement proper logging and monitoring
- Use encryption for sensitive data
- Regular backup and testing of recovery procedures

### 3. Performance Best Practices

- Use connection pooling for API calls
- Implement batch processing for large datasets
- Monitor memory usage and optimize accordingly
- Use caching where appropriate
- Regular performance testing and optimization

---

*This deployment guide provides comprehensive instructions for setting up and maintaining the Odoo POS to B4B Sale Order Sync CLI. Always adapt the procedures to your specific environment and requirements.*

For advanced deployment scenarios and detailed configuration options, refer to the [deployment-guide-reference.md](./deployment-guide-reference.md) file.