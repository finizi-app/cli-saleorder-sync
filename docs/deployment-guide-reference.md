# Deployment Guide Reference
## Advanced Topics and Configuration
## Odoo POS to B4B Sale Order Sync CLI

This document provides advanced deployment scenarios, performance tuning, and detailed configuration options for production environments.

## Table of Contents

1. [Advanced Configuration](#advanced-configuration)
2. [Performance Tuning](#performance-tuning)
3. [High Availability](#high-availability)
4. [Load Balancing](#load-balancing)
5. [Monitoring and Alerting](#monitoring-and-alerting)
6. [Security Hardening](#security-hardening)
7. [Disaster Recovery](#disaster-recovery)
8. [Scaling Strategies](#scaling-strategies)
9. [Integration Patterns](#integration-patterns)

## Advanced Configuration

### Configuration Management

#### Multi-Environment Configuration

```python
# config_manager.py
import os
import yaml
from typing import Optional, Dict, Any
from pathlib import Path

class AdvancedConfigManager:
    """Advanced configuration manager with multiple environment support."""

    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.config_dir = Path("/etc/odoo-sync")
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from multiple sources."""
        config = {}

        # Load base configuration
        base_config = self._load_yaml_file("base.yaml")
        config.update(base_config)

        # Load environment-specific configuration
        env_config = self._load_yaml_file(f"{self.environment}.yaml")
        config.update(env_config)

        # Load secrets from secure storage
        secrets = self._load_secrets()
        config.update(secrets)

        # Override with environment variables
        env_override = self._load_env_variables()
        config.update(env_override)

        return config

    def _load_yaml_file(self, filename: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        config_path = self.config_dir / filename
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        return {}

    def _load_secrets(self) -> Dict[str, Any]:
        """Load secrets from secure storage."""
        secrets = {}

        # Load from Hashicorp Vault
        if os.path.exists("/etc/vault/secrets.yaml"):
            with open("/etc/vault/secrets.yaml", 'r') as f:
                secrets.update(yaml.safe_load(f))

        # Load from AWS Secrets Manager
        if os.environ.get('AWS_ACCESS_KEY_ID'):
            secrets.update(self._load_aws_secrets())

        return secrets

    def _load_aws_secrets(self) -> Dict[str, Any]:
        """Load secrets from AWS Secrets Manager."""
        import boto3

        client = boto3.client('secretsmanager')
        secrets = {}

        secret_names = [
            'odoo_password',
            'b4b_token',
            'database_password'
        ]

        for secret_name in secret_names:
            try:
                response = client.get_secret_value(SecretId=secret_name)
                secrets[secret_name] = response['SecretString']
            except client.exceptions.ResourceNotFoundException:
                continue

        return secrets

    def _load_env_variables(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        env_mapping = {
            'ODOO_URL': 'ODOO_URL',
            'ODOO_DB': 'ODOO_DB',
            'ODOO_USERNAME': 'ODOO_USERNAME',
            'ODOO_PASSWORD': 'ODOO_PASSWORD',
            'B4B_API_URL': 'B4B_API_URL',
            'B4B_TOKEN': 'B4B_TOKEN',
            'B4B_ENTITY_ID': 'B4B_ENTITY_ID',
        }

        return {
            key: os.getenv(env_mapping[key])
            for key in env_mapping
            if os.getenv(env_mapping[key])
        }

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get configuration value with fallback."""
        return self.config.get(key, default)

    def validate(self) -> None:
        """Validate configuration."""
        required = [
            'ODOO_URL', 'ODOO_DB', 'ODOO_USERNAME', 'ODOO_PASSWORD',
            'B4B_API_URL', 'B4B_TOKEN', 'B4B_ENTITY_ID'
        ]

        missing = [var for var in required if not self.get(var)]
        if missing:
            raise ValueError(f"Missing required variables: {', '.join(missing)}")
```

### Configuration Templates

#### Base Configuration (base.yaml)

```yaml
# Base configuration for all environments
app:
  name: "odoo-sync"
  version: "0.1.0"
  debug: false

odoo:
  timeout: 30
  retry_attempts: 3
  retry_delay: 1.0
  batch_size: 100

b4b:
  timeout: 30
  retry_attempts: 3
  retry_delay: 1.0
  batch_size: 50

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file_path: "/var/log/odoo-sync/odoo-sync.log"
  max_size: "10MB"
  backup_count: 5

monitoring:
  enabled: true
  metrics_port: 8080
  health_check_interval: 30
```

#### Production Configuration (production.yaml)

```yaml
# Production-specific configuration
app:
  debug: false
  log_level: "INFO"

odoo:
  timeout: 60
  retry_attempts: 5
  batch_size: 500

b4b:
  timeout: 60
  retry_attempts: 5
  batch_size: 200

performance:
  max_workers: 4
  use_connection_pool: true
  cache_size: 1000

security:
  enable_ssl: true
  ssl_cert_path: "/etc/ssl/certs/odoo-sync.crt"
  ssl_key_path: "/etc/ssl/private/odoo-sync.key"

monitoring:
  enabled: true
  alert_threshold_cpu: 80
  alert_threshold_memory: 85
  alert_threshold_disk: 90

backup:
  enabled: true
  interval: "daily"
  retention_days: 30
  compression: true
```

## Performance Tuning

### System-Level Optimization

#### Kernel Parameters

```bash
# /etc/sysctl.conf optimization for high performance
fs.file-max = 65536
net.core.somaxconn = 65536
net.ipv4.tcp_max_syn_backlog = 65536
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_probes = 3
net.ipv4.tcp_keepalive_intvl = 30

vm.swappiness = 10
vm.dirty_ratio = 60
vm.dirty_background_ratio = 2

# Apply changes
sysctl -p
```

#### Resource Limits

```bash
# /etc/security/limits.conf
* soft nofile 65536
* hard nofile 65536
* soft nproc 32768
* hard nproc 32768
* soft memlock unlimited
* hard memlock unlimited

# PAM configuration for login
# /etc/pam.d/common-session
session required pam_limits.so
```

### Application-Level Optimization

#### Optimized Client Configuration

```python
# optimized_clients.py
import httpx
import asyncio
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class HighPerformanceB4BClient:
    """High-performance B4B client with connection pooling and async support."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pool_limits = httpx.PoolLimits(
            keepalive_limit=200,
            max_connections=200,
            max_idle_connections=50,
        )

        # Create client with optimized settings
        self.client = httpx.Client(
            base_url=config['B4B_API_URL'],
            headers=self._get_headers(),
            timeout=config.get('timeout', 30),
            limits=self.pool_limits,
            http2=True,  # Enable HTTP/2 for better performance
        )

        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(
            max_workers=config.get('max_workers', 4),
            thread_name_prefix="b4b-sync"
        )

    def _get_headers(self) -> Dict[str, str]:
        """Get optimized headers."""
        return {
            "Authorization": f"Bearer {self.config['B4B_TOKEN']}",
            "Content-Type": "application/json",
            "User-Agent": "odoo-sync/0.1.0",
            "Accept": "application/json",
            "Connection": "keep-alive",
        }

    def batch_create_orders(self, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create orders in parallel batches."""
        results = []
        batch_size = self.config.get('batch_size', 50)

        # Split orders into batches
        order_batches = [
            orders[i:i + batch_size]
            for i in range(0, len(orders), batch_size)
        ]

        # Process batches in parallel
        futures = []
        for batch in order_batches:
            future = self.executor.submit(self._process_batch, batch)
            futures.append(future)

        # Collect results
        for future in as_completed(futures):
            try:
                results.extend(future.result())
            except Exception as e:
                print(f"Batch processing failed: {e}")

        return results

    def _process_batch(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a single batch of orders."""
        results = []

        for order in batch:
            try:
                start_time = time.time()
                response = self.client.post(
                    f"/api/v1/entities/{self.config['B4B_ENTITY_ID']}/sale-orders",
                    json=order,
                    timeout=self.config.get('timeout', 30)
                )
                response.raise_for_status()

                # Add performance metrics
                result = {
                    'order_id': order['order_number'],
                    'status': 'success',
                    'response_time': time.time() - start_time,
                    'b4b_order_id': response.json().get('id')
                }

                # Generate invoice if needed
                if self.config.get('auto_invoice', True):
                    self._generate_invoice(response.json()['id'])

                results.append(result)

            except Exception as e:
                results.append({
                    'order_id': order['order_number'],
                    'status': 'failed',
                    'error': str(e),
                    'response_time': time.time() - start_time
                })

        return results

    def _generate_invoice(self, order_id: str) -> None:
        """Generate invoice for an order."""
        try:
            self.client.post(
                f"/api/v1/entities/{self.config['B4B_ENTITY_ID']}/sale-orders/{order_id}/generate-vnpay-invoice",
                params={"invoice_type": "pos"},
                timeout=self.config.get('timeout', 30)
            )
        except Exception as e:
            print(f"Invoice generation failed for order {order_id}: {e}")

    def close(self):
        """Cleanup resources."""
        self.executor.shutdown(wait=True)
        self.client.close()
```

#### Caching Layer

```python
# cache_manager.py
import time
import hashlib
from typing import Dict, Any, Optional
from dataclasses import dataclass
from threading import Lock

@dataclass
class CacheEntry:
    data: Any
    timestamp: float
    ttl: int

class CacheManager:
    """Thread-safe cache manager with TTL support."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        with self.lock:
            entry = self.cache.get(key)
            if entry:
                if time.time() - entry.timestamp < entry.ttl:
                    return entry.data
                else:
                    del self.cache[key]
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL."""
        with self.lock:
            # Check cache size and evict if needed
            if len(self.cache) >= self.max_size:
                self._evict_expired()

            # If still full, evict oldest
            if len(self.cache) >= self.max_size:
                oldest_key = min(self.cache.keys(),
                               key=lambda k: self.cache[k].timestamp)
                del self.cache[oldest_key]

            # Store new entry
            self.cache[key] = CacheEntry(
                data=value,
                timestamp=time.time(),
                ttl=ttl or self.default_ttl
            )

    def _evict_expired(self) -> None:
        """Evict expired entries."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time - entry.timestamp >= entry.ttl
        ]
        for key in expired_keys:
            del self.cache[key]

    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()

    def get_cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_str = f"{args}:{kwargs}"
        return hashlib.md5(key_str.encode()).hexdigest()
```

## High Availability

### Active-Passive Setup

#### Systemd Configuration

```ini
# /etc/systemd/system/odoo-sync.service
[Unit]
Description=Odoo to B4B Sync Service (Primary)
After=network.target
Wants=network.target

[Service]
Type=simple
User=odoo-sync
Group=odoo-sync
WorkingDirectory=/opt/odoo-sync
Environment=PATH=/opt/odoo-sync/venv/bin
Environment=ENVIRONMENT=production
ExecStart=/opt/odoo-sync/venv/bin/python -m src.cli --date $(date +%Y-%m-%d)
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Health check
ExecStartPre=/usr/bin/systemctl is-active odoo-sync-healthcheck
ExecStopPost=/usr/bin/systemctl is-failed odoo-sync && systemctl restart odoo-sync

[Install]
WantedBy=multi-user.target

# Health check service
[Unit]
Description=Odoo Sync Health Check
After=network.target

[Service]
Type=oneshot
ExecStart=/opt/odoo-sync/venv/bin/python -c "
import sys
sys.path.append('src')
from healthcheck import HealthCheck
hc = HealthCheck()
hc.check_all()
"
```

#### Pacemaker Configuration

```bash
# Install and configure Pacemaker
sudo apt-get install -y pacemaker corosync

# Configure corosync
sudo nano /etc/corosync/corosync.conf

# Sample corosync configuration
cluster_name: odoo-sync-cluster
totem {
    version: 2
    cluster_name: odoo-sync-cluster
    transport: udpu
}

nodelist {
    node {
        ring0_addr: 192.168.1.100
        nodeid: 1
        priority: 100
    }
    node {
        ring0_addr: 192.168.1.101
        nodeid: 2
        priority: 50
    }
}

quorum {
    provider: corosync_votequorum
}

# Configure Pacemaker resources
sudo pcs cluster setup --start --name odoo-sync-cluster 192.168.1.100 192.168.1.101
sudo pcs cluster auth

# Create virtual IP
sudo pcs resource create virtual-ip ocf:heartbeat:IPaddr2 ip=192.168.1.50 cidr_netmask=32

# Create application resource
sudo pcs resource create odoo-sync systemd:odoo-sync \
    --clone clone-max=2 clone-node-max=1 \
    --master master-max=1 master-node-max=1

# Create constraints
sudo pcs constraint colocation add virtual-ip with master odoo-sync INFINITY
sudo pcs constraint order start virtual-ip then odoo-sync-master
```

## Load Balancing

### HAProxy Configuration

```haproxy
# /etc/haproxy/haproxy.conf
global
    log /dev/log local0
    log /dev/log local1 notice
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin
    stats timeout 30s
    user haproxy
    group haproxy
    daemon

    # Performance tuning
    tune.ssl.default-dh-param 2048
    tune.bufsize 65536
    tune.ssl.linger-high 5000
    tune.ssl.linger-low 1000

defaults
    log global
    mode http
    option httplog
    option dontlognull
    option http-server-close
    option forwardfor except 127.0.0.0/8
    option redispatch
    timeout http-request 10s
    timeout queue 1m
    timeout connect 10s
    timeout client 1m
    timeout server 1m
    timeout http-keep-alive 10s
    timeout check 10s
    maxconn 4000

# Frontend for API requests
frontend b4b-api
    bind *:8080
    mode http
    option tcplog
    log-format %ci:%cp\ [%t]\ %ST\ %B\ %Ts\ %Tc\ %Tr\ %Tw\ %Tt\ %HT\ %FT\ %ST\ %B\ %CC\ %CS\ %TR\ %TT\ %AC\ %FC\ %SC\ %RC\ %PC\ %BC\ %BS\ %WS\ %BSC\ %RT\ %QT\ %DT\ %[var(txn_name)]\ %[var(txn_nspath)]\ %[var(txn_parentpath)]

    # SSL termination (if needed)
    # bind *:8443 ssl crt /etc/ssl/certs/b4b-api.pem

    # Health check
    acl is_health_check path /health
    use_backend health-check if is_health_check

    # Load balancing to backend servers
    default_backend b4b-backend

# Backend servers
backend b4b-backend
    mode http
    balance roundrobin
    option httpchk GET /health
    option httplog
    option httpclose
    option forwardfor
    option redispatch

    # Server definitions
    server server1 192.168.1.100:8080 check inter 30s rise 2 fall 3
    server server2 192.168.1.101:8080 check inter 30s rise 2 fall 3
    server server3 192.168.1.102:8080 check inter 30s rise 2 fall 3

    # Health check configuration
    http-check expect status 200
    http-check send meth GET uri /health

    # Performance tuning
    timeout connect 10s
    timeout server 30s
    retries 3
    maxconn 2000

# Health check backend
backend health-check
    mode http
    server localhost 127.0.0.1:80 check
```

## Monitoring and Alerting

### Prometheus Configuration

```yaml
# /etc/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'odoo-sync'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
    scrape_interval: 30s
    scrape_timeout: 10s

  - job_name: 'odoo-sync-health'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/health'
    scrape_interval: 10s
    scrape_timeout: 5s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']
```

### Alert Rules

```yaml
# /etc/prometheus/alert-rules.yml
groups:
  - name: odoo-sync
    rules:
      - alert: OdooSyncDown
        expr: up{job="odoo-sync"} == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Odoo Sync service is down"
          description: "Odoo Sync service has been down for more than 5 minutes"

      - alert: HighResponseTime
        expr: http_request_duration_seconds{quantile="0.95"} > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is above 2 seconds"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 10%"

      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is above 85%"

      - alert: HighDiskUsage
        expr: (node_filesystem_size_bytes{mountpoint="/var/log"} - node_filesystem_free_bytes{mountpoint="/var/log"}) / node_filesystem_size_bytes{mountpoint="/var/log"} * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High disk usage"
          description: "Disk usage is above 85%"
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Odoo Sync Monitoring",
    "panels": [
      {
        "title": "Service Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"odoo-sync\"}",
            "legendFormat": "{{instance}}"
          }
        ]
      },
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{status}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "100 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100)",
            "legendFormat": "Memory Usage"
          }
        ]
      }
    ]
  }
}
```

## Security Hardening

### Firewall Configuration

```bash
# Configure UFW with advanced rules
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow 22/tcp comment "SSH"

# Allow application ports
sudo ufw allow 8080/tcp comment "Odoo Sync API"
sudo ufw allow 8443/tcp comment "Odoo Sync HTTPS"

# Allow monitoring
sudo ufw allow 9090/tcp comment "Prometheus"
sudo ufw allow 3000/tcp comment "Grafana"

# Allow internal network
sudo ufw allow from 192.168.1.0/24 comment "Internal network"

# Enable firewall
sudo ufw enable

# Show status
sudo ufw status verbose
```

### SSL/TLS Configuration

```bash
# Generate SSL certificate
openssl req -x509 -newkey rsa:4096 -keyout /etc/ssl/private/odoo-sync.key \
    -out /etc/ssl/certs/odoo-sync.crt -days 365 -nodes \
    -subj "/C=VN/ST=Ho Chi Minh/L=Ho Chi Minh/O=Odoo Sync/CN=odoo-sync.local"

# Configure Nginx as SSL terminator
cat > /etc/nginx/sites-available/odoo-sync << EOF
server {
    listen 80;
    server_name odoo-sync.example.com;

    # Redirect to HTTPS
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name odoo-sync.example.com;

    ssl_certificate /etc/ssl/certs/odoo-sync.crt;
    ssl_certificate_key /etc/ssl/private/odoo-sync.key;

    # SSL security settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    proxy_pass http://localhost:8080;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;

    # Timeouts
    proxy_connect_timeout 30s;
    proxy_send_timeout 30s;
    proxy_read_timeout 30s;

    # Buffer settings
    proxy_buffering on;
    proxy_buffer_size 4k;
    proxy_buffers 8 4k;
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/odoo-sync /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Disaster Recovery

### Automated Backup Script

```bash
#!/bin/bash
# disaster-recovery.sh

set -e

# Configuration
BACKUP_DIR="/backup/odoo-sync"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/var/log/odoo-sync/backup-$TIMESTAMP.log"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Cleanup old backups
cleanup_old_backups() {
    log "Cleaning up backups older than $RETENTION_DAYS days"
    find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
    log "Cleanup completed"
}

# Backup configuration
backup_config() {
    log "Backing up configuration"
    CONFIG_BACKUP="$BACKUP_DIR/config-$TIMESTAMP"

    # Create backup directory
    mkdir -p "$CONFIG_BACKUP"

    # Backup application configuration
    cp -r /etc/odoo-sync "$CONFIG_BACKUP/"

    # Backup systemd services
    cp /etc/systemd/system/odoo-sync.service "$CONFIG_BACKUP/"

    # Backup SSL certificates
    if [ -f /etc/ssl/certs/odoo-sync.crt ]; then
        cp /etc/ssl/certs/odoo-sync.crt "$CONFIG_BACKUP/"
        cp /etc/ssl/private/odoo-sync.key "$CONFIG_BACKUP/"
    fi

    # Backup database if using local database
    if [ -d /var/lib/mysql/odoo_sync ]; then
        mysqldump -u root -p --single-transaction --routines --triggers odoo_sync > "$CONFIG_BACKUP/database.sql"
    fi

    log "Configuration backup completed"
}

# Backup logs
backup_logs() {
    log "Backing up logs"
    LOGS_BACKUP="$BACKUP_DIR/logs-$TIMESTAMP"

    # Create backup directory
    mkdir -p "$LOGS_BACKUP"

    # Copy application logs
    if [ -d /var/log/odoo-sync ]; then
        cp -r /var/log/odoo-sync "$LOGS_BACKUP/"
    fi

    # Copy system logs
    journalctl -u odoo-sync --since "24 hours ago" > "$LOGS_BACKUP/systemd-logs.txt"

    log "Logs backup completed"
}

# Backup application code
backup_code() {
    log "Backing up application code"
    CODE_BACKUP="$BACKUP_DIR/code-$TIMESTAMP"

    # Create backup directory
    mkdir -p "$CODE_BACKUP"

    # Copy application code
    cp -r /opt/odoo-sync "$CODE_BACKUP/"

    # Remove virtual environment to save space
    rm -rf "$CODE_BACKUP/venv"

    log "Application code backup completed"
}

# Compress backups
compress_backups() {
    log "Compressing backups"
    cd "$BACKUP_DIR"

    # Compress each backup
    tar -czf "config-$TIMESTAMP.tar.gz" "config-$TIMESTAMP"
    tar -czf "logs-$TIMESTAMP.tar.gz" "logs-$TIMESTAMP"
    tar -czf "code-$TIMESTAMP.tar.gz" "code-$TIMESTAMP"

    # Remove uncompressed directories
    rm -rf "config-$TIMESTAMP" "logs-$TIMESTAMP" "code-$TIMESTAMP"

    log "Backup compression completed"
}

# Verify backups
verify_backups() {
    log "Verifying backups"

    for backup_file in "$BACKUP_DIR"/*.tar.gz; do
        if ! tar -tzf "$backup_file" >/dev/null 2>&1; then
            log "ERROR: Backup file $backup_file is corrupted"
            exit 1
        fi
    done

    log "Backup verification completed"
}

# Main backup process
main() {
    log "Starting disaster recovery backup process"

    cleanup_old_backups
    backup_config
    backup_logs
    backup_code
    compress_backups
    verify_backups

    log "Backup process completed successfully"
    log "Backups available in: $BACKUP_DIR"
}

# Run main function
main
```

### Failover Procedure

```bash
#!/bin/bash
# failover.sh

set -e

# Configuration
PRIMARY_SERVER="192.168.1.100"
SECONDARY_SERVER="192.168.1.101"
VIRTUAL_IP="192.168.1.50"
SERVICE_NAME="odoo-sync"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Check server health
check_server_health() {
    local server=$1
    local max_attempts=3
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -s "http://$server:8080/health" >/dev/null 2>&1; then
            log "Server $server is healthy"
            return 0
        fi
        log "Attempt $attempt: Server $server is not responding, waiting..."
        sleep 10
        ((attempt++))
    done

    log "ERROR: Server $server is not responding after $max_attempts attempts"
    return 1
}

# Failover to secondary server
failover() {
    log "Initiating failover from $PRIMARY_SERVER to $SECONDARY_SERVER"

    # Check if primary is down
    if check_server_health "$PRIMARY_SERVER"; then
        log "Primary server is still healthy, no failover needed"
        exit 0
    fi

    # Check if secondary is healthy
    if ! check_server_health "$SECONDARY_SERVER"; then
        log "ERROR: Secondary server is also down, cannot perform failover"
        exit 1
    fi

    # Update DNS records (if using DNS)
    log "Updating DNS records to point to $SECONDARY_SERVER"
    # This would typically be done via DNS API or manual DNS update

    # Update load balancer configuration
    log "Updating load balancer configuration"
    # This would typically be done via HAProxy API or manual configuration

    # Restart service on secondary server
    log "Restarting service on secondary server"
    ssh "$SECONDARY_SERVER" "sudo systemctl restart $SERVICE_NAME"

    # Wait for service to start
    sleep 30

    # Verify service is running
    if check_server_health "$SECONDARY_SERVER"; then
        log "Failover completed successfully"
        log "Service is now running on $SECONDARY_SERVER"
    else
        log "ERROR: Failover failed - service is still not running"
        exit 1
    fi
}

# Failback procedure
failback() {
    log "Initiating failback from $SECONDARY_SERVER to $PRIMARY_SERVER"

    # Check if primary is healthy
    if ! check_server_health "$PRIMARY_SERVER"; then
        log "ERROR: Primary server is not healthy, cannot perform failback"
        exit 1
    fi

    # Update DNS records
    log "Updating DNS records to point to $PRIMARY_SERVER"
    # This would typically be done via DNS API or manual DNS update

    # Update load balancer configuration
    log "Updating load balancer configuration"
    # This would typically be done via HAProxy API or manual configuration

    # Restart service on primary server
    log "Restarting service on primary server"
    ssh "$PRIMARY_SERVER" "sudo systemctl restart $SERVICE_NAME"

    # Wait for service to start
    sleep 30

    # Verify service is running
    if check_server_health "$PRIMARY_SERVER"; then
        log "Failback completed successfully"
        log "Service is now running on $PRIMARY_SERVER"
    else
        log "ERROR: Failback failed - service is still not running"
        exit 1
    fi
}

# Main function
main() {
    case "$1" in
        "failover")
            failover
            ;;
        "failback")
            failback
            ;;
        *)
            echo "Usage: $0 {failover|failback}"
            exit 1
            ;;
    esac
}

# Run main function
main "$1"
```

## Scaling Strategies

### Horizontal Scaling

```python
# scaling_manager.py
import asyncio
import multiprocessing
import time
from typing import List, Dict, Any
from concurrent.futures import ProcessPoolExecutor, as_completed
import psutil

class ScalingManager:
    """Manages horizontal scaling of sync operations."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_workers = config.get('max_workers', multiprocessing.cpu_count() * 2)
        self.min_workers = config.get('min_workers', 2)
        self.current_workers = self.min_workers
        self.load_threshold = config.get('load_threshold', 0.8)

    def monitor_system_load(self) -> Dict[str, float]:
        """Monitor system load metrics."""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'load_average': os.getloadavg()[0],
            'active_connections': self._count_active_connections()
        }

    def _count_active_connections(self) -> int:
        """Count active connections to the application."""
        try:
            # This is a simplified version - in practice, you'd need to implement
            # connection tracking based on your specific application
            return 0
        except Exception:
            return 0

    def should_scale_up(self, metrics: Dict[str, float]) -> bool:
        """Determine if scaling up is needed."""
        return (
            metrics['cpu_percent'] > self.load_threshold * 100 or
            metrics['memory_percent'] > self.load_threshold * 100 or
            metrics['load_average'] > self.load_threshold * multiprocessing.cpu_count()
        )

    def should_scale_down(self, metrics: Dict[str, float]) -> bool:
        """Determine if scaling down is needed."""
        return (
            metrics['cpu_percent'] < (1 - self.load_threshold) * 100 and
            metrics['memory_percent'] < (1 - self.load_threshold) * 100 and
            self.current_workers > self.min_workers
        )

    def scale_workers(self, metrics: Dict[str, float]) -> None:
        """Scale worker processes based on load."""
        if self.should_scale_up(metrics):
            self._scale_up()
        elif self.should_scale_down(metrics):
            self._scale_down()

    def _scale_up(self) -> None:
        """Increase number of worker processes."""
        new_workers = min(self.current_workers + 1, self.max_workers)
        if new_workers > self.current_workers:
            self.current_workers = new_workers
            print(f"Scaled up to {self.current_workers} workers")

    def _scale_down(self) -> None:
        """Decrease number of worker processes."""
        new_workers = max(self.current_workers - 1, self.min_workers)
        if new_workers < self.current_workers:
            self.current_workers = new_workers
            print(f"Scaled down to {self.current_workers} workers")

    def distribute_work(self, orders: List[Dict[str, Any]]) -> List[Any]:
        """Distribute work across multiple workers."""
        chunk_size = max(1, len(orders) // self.current_workers)
        chunks = [
            orders[i:i + chunk_size]
            for i in range(0, len(orders), chunk_size)
        ]

        results = []
        with ProcessPoolExecutor(max_workers=self.current_workers) as executor:
            futures = [
                executor.submit(self._process_chunk, chunk)
                for chunk in chunks
            ]

            for future in as_completed(futures):
                try:
                    results.extend(future.result())
                except Exception as e:
                    print(f"Worker failed: {e}")

        return results

    def _process_chunk(self, chunk: List[Dict[str, Any]]) -> List[Any]:
        """Process a chunk of orders."""
        # This would contain the actual processing logic
        results = []
        for order in chunk:
            # Process order
            result = {
                'order_id': order.get('order_number'),
                'status': 'processed',
                'processed_at': time.time()
            }
            results.append(result)

        return results
```

## Integration Patterns

### Database Integration

```python
# database_integration.py
import sqlite3
import psycopg2
import mysql.connector
from typing import Dict, Any, List, Optional
from contextlib import contextmanager

class DatabaseIntegration:
    """Handles database integration for audit logging and reporting."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_type = config.get('db_type', 'sqlite')
        self.connection_string = config.get('connection_string')

    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup."""
        conn = None
        try:
            if self.db_type == 'sqlite':
                conn = sqlite3.connect(self.connection_string)
            elif self.db_type == 'postgresql':
                conn = psycopg2.connect(self.connection_string)
            elif self.db_type == 'mysql':
                conn = mysql.connector.connect(self.connection_string)

            yield conn

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()

    def log_sync_operation(self, operation: str, status: str, details: Dict[str, Any]) -> None:
        """Log sync operation to database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if self.db_type == 'sqlite':
                cursor.execute('''
                    INSERT INTO sync_operations (operation, status, details, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (operation, status, str(details), time.time()))
            elif self.db_type == 'postgresql':
                cursor.execute('''
                    INSERT INTO sync_operations (operation, status, details, created_at)
                    VALUES (%s, %s, %s, %s)
                ''', (operation, status, str(details), time.time()))
            elif self.db_type == 'mysql':
                cursor.execute('''
                    INSERT INTO sync_operations (operation, status, details, created_at)
                    VALUES (%s, %s, %s, %s)
                ''', (operation, status, str(details), time.time()))

            conn.commit()

    def get_sync_statistics(self, start_time: Optional[float] = None,
                           end_time: Optional[float] = None) -> Dict[str, Any]:
        """Get sync operation statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = '''
                SELECT
                    operation,
                    status,
                    COUNT(*) as count,
                    AVG(created_at) as avg_time,
                    MIN(created_at) as min_time,
                    MAX(created_at) as max_time
                FROM sync_operations
            '''

            params = []
            if start_time:
                query += ' WHERE created_at >= ?'
                params.append(start_time)
            if end_time:
                query += ' AND created_at <= ?' if start_time else ' WHERE created_at <= ?'
                params.append(end_time)

            query += ' GROUP BY operation, status'

            if self.db_type == 'sqlite':
                cursor.execute(query, params)
            elif self.db_type == 'postgresql':
                cursor.execute(query, params)
            elif self.db_type == 'mysql':
                cursor.execute(query, params)

            results = cursor.fetchall()

            return {
                'total_operations': sum(row[2] for row in results),
                'operations': [
                    {
                        'operation': row[0],
                        'status': row[1],
                        'count': row[2],
                        'avg_time': row[3],
                        'min_time': row[4],
                        'max_time': row[5]
                    }
                    for row in results
                ]
            }
```

### Message Queue Integration

```python
# message_queue_integration.py
import pika
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class MessageType(Enum):
    SYNC_ORDER = "sync_order"
    SYNC_RESULT = "sync_result"
    ERROR_NOTIFICATION = "error_notification"
    HEARTBEAT = "heartbeat"

@dataclass
class Message:
    type: MessageType
    payload: Dict[str, Any]
    timestamp: float
    correlation_id: Optional[str] = None

class MessageQueueIntegration:
    """Handles message queue integration for distributed processing."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None
        self.channel = None
        self.queue_name = config.get('queue_name', 'odoo-sync')

    def connect(self) -> None:
        """Connect to message queue."""
        credentials = pika.PlainCredentials(
            self.config.get('username', 'guest'),
            self.config.get('password', 'guest')
        )

        parameters = pika.ConnectionParameters(
            host=self.config.get('host', 'localhost'),
            port=self.config.get('port', 5672),
            credentials=credentials,
            virtual_host=self.config.get('virtual_host', '/'),
            connection_attempts=3,
            retry_delay=5
        )

        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

        # Declare queue
        self.channel.queue_declare(
            queue=self.queue_name,
            durable=True,
            arguments={
                'x-message-ttl': 3600000,  # 1 hour
                'x-dead-letter-exchange': 'odoo-sync-dlx',
                'x-dead-letter-routing-key': 'failed'
            }
        )

        # Declare dead letter queue
        self.channel.queue_declare(
            queue='failed',
            durable=True
        )

    def disconnect(self) -> None:
        """Disconnect from message queue."""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.channel = None

    def send_message(self, message: Message) -> None:
        """Send message to queue."""
        if not self.connection:
            self.connect()

        message_dict = {
            'type': message.type.value,
            'payload': message.payload,
            'timestamp': message.timestamp,
            'correlation_id': message.correlation_id
        }

        self.channel.basic_publish(
            exchange='',
            routing_key=self.queue_name,
            body=json.dumps(message_dict),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
                correlation_id=message.correlation_id
            )
        )

    def receive_message(self, callback: callable, auto_ack: bool = False) -> None:
        """Receive messages from queue."""
        if not self.connection:
            self.connect()

        def on_message(ch, method, properties, body):
            try:
                message_dict = json.loads(body)
                message = Message(
                    type=MessageType(message_dict['type']),
                    payload=message_dict['payload'],
                    timestamp=message_dict['timestamp'],
                    correlation_id=message_dict.get('correlation_id')
                )
                callback(message)
                if auto_ack:
                    ch.basic_ack(method.delivery_tag)
            except Exception as e:
                print(f"Error processing message: {e}")
                ch.basic_nack(method.delivery_tag, requeue=False)

        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=on_message,
            auto_ack=auto_ack
        )

        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()

    def send_sync_order(self, order_data: Dict[str, Any]) -> str:
        """Send sync order message."""
        correlation_id = str(int(time.time() * 1000))
        message = Message(
            type=MessageType.SYNC_ORDER,
            payload=order_data,
            timestamp=time.time(),
            correlation_id=correlation_id
        )
        self.send_message(message)
        return correlation_id

    def wait_for_result(self, correlation_id: str, timeout: int = 300) -> Optional[Dict[str, Any]]:
        """Wait for sync result message."""
        # This is a simplified implementation
        # In practice, you'd want a more sophisticated mechanism
        return None
```

---

*This advanced deployment reference provides comprehensive guidance for production deployment, high availability, scaling, and integration patterns. Always adapt these patterns to your specific environment and requirements.*