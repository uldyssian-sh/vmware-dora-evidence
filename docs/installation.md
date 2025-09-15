# Installation Guide

This guide provides detailed instructions for installing and setting up VMware DORA Evidence.

## Table of Contents

- [System Requirements](#system-requirements)
- [Installation Methods](#installation-methods)
- [Configuration](#configuration)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements

- **Operating System**: Linux, macOS, or Windows
- **Python**: 3.8 or higher
- **Memory**: 2 GB RAM
- **Storage**: 1 GB free space
- **Network**: Access to VMware vCenter Server

### Recommended Requirements

- **Operating System**: Linux (Ubuntu 20.04+ or CentOS 8+)
- **Python**: 3.10 or higher
- **Memory**: 4 GB RAM
- **Storage**: 5 GB free space
- **Network**: Dedicated network connection to VMware infrastructure

### VMware Environment Requirements

- **vCenter Server**: 6.7 or higher
- **ESXi Hosts**: 6.7 or higher
- **Permissions**: Read access to vCenter events and inventory
- **Network**: HTTPS (443) access to vCenter Server

## Installation Methods

### Method 1: pip Installation (Recommended)

```bash
# Install from PyPI (when available)
pip install vmware-dora-evidence

# Or install from source
pip install git+https://github.com/uldyssian-sh/vmware-dora-evidence.git
```

### Method 2: Source Installation

```bash
# Clone the repository
git clone https://github.com/uldyssian-sh/vmware-dora-evidence.git
cd vmware-dora-evidence

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Method 3: Docker Installation

```bash
# Pull the Docker image
docker pull ghcr.io/uldyssian-sh/vmware-dora-evidence:latest

# Run the container
docker run -d \
  --name dora-evidence \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/data:/app/data \
  ghcr.io/uldyssian-sh/vmware-dora-evidence:latest
```

### Method 4: Kubernetes Deployment

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

## Configuration

### Step 1: Create Configuration File

```bash
# Copy the template
cp config/config.template.yaml config/config.yaml

# Edit the configuration
nano config/config.yaml
```

### Step 2: Configure VMware Connection

```yaml
vmware:
  vcenter_host: "your-vcenter.example.com"
  username: "your-username"
  password: "your-password"  # Use environment variables in production
  port: 443
  ignore_ssl_errors: false
```

### Step 3: Environment Variables (Recommended)

Create a `.env` file or set environment variables:

```bash
# VMware Configuration
export VMWARE_VCENTER_HOST="your-vcenter.example.com"
export VMWARE_USERNAME="your-username"
export VMWARE_PASSWORD="your-password"
export VMWARE_PORT="443"
export VMWARE_IGNORE_SSL="false"

# Database Configuration
export DATABASE_URL="sqlite:///dora_evidence.db"

# Logging Configuration
export LOG_LEVEL="INFO"
```

### Step 4: Database Setup

#### SQLite (Default)
```bash
# No additional setup required
# Database file will be created automatically
```

#### PostgreSQL
```bash
# Install PostgreSQL client
pip install psycopg2-binary

# Create database
createdb dora_evidence

# Update configuration
export DATABASE_URL="postgresql://user:password@localhost:5432/dora_evidence"
```

#### MySQL
```bash
# Install MySQL client
pip install PyMySQL

# Create database
mysql -u root -p -e "CREATE DATABASE dora_evidence;"

# Update configuration
export DATABASE_URL="mysql://user:password@localhost:3306/dora_evidence"
```

## Verification

### Step 1: Test VMware Connection

```bash
# Test connection
python -c "
from src.integrations.vmware_client import VMwareClient
from src.utils.config_manager import ConfigManager

config = ConfigManager().get_vmware_config()
client = VMwareClient(config)
print('Connection successful!' if client.test_connection() else 'Connection failed!')
"
```

### Step 2: Run Basic Collection

```bash
# Run a basic data collection
python -c "
from src.dora_evidence import DORACollector

collector = DORACollector()
metrics = collector.collect_all_metrics(days=7)
print(f'Collected metrics: {metrics}')
"
```

### Step 3: Generate Test Report

```bash
# Generate a test report
python -c "
from src.dora_evidence import DORACollector

collector = DORACollector()
metrics = collector.collect_all_metrics(days=7)
report = collector.generate_report(metrics)
print('Report generated successfully!')
"
```

## Advanced Configuration

### SSL Certificate Configuration

For environments with custom SSL certificates:

```yaml
vmware:
  vcenter_host: "your-vcenter.example.com"
  username: "your-username"
  password: "your-password"
  port: 443
  ignore_ssl_errors: false
  ssl_cert_path: "/path/to/certificate.pem"
  ssl_key_path: "/path/to/private.key"
```

### Proxy Configuration

For environments behind a proxy:

```bash
export HTTP_PROXY="http://proxy.example.com:8080"
export HTTPS_PROXY="http://proxy.example.com:8080"
export NO_PROXY="localhost,127.0.0.1"
```

### Performance Tuning

```yaml
performance:
  parallel_processing:
    enabled: true
    max_workers: 4

  cache:
    enabled: true
    ttl_seconds: 3600
    max_size_mb: 100

  database:
    connection_pool_size: 10
    query_timeout_seconds: 30
```

## Service Installation

### Systemd Service (Linux)

Create `/etc/systemd/system/dora-evidence.service`:

```ini
[Unit]
Description=VMware DORA Evidence Collector
After=network.target

[Service]
Type=simple
User=dora-evidence
Group=dora-evidence
WorkingDirectory=/opt/vmware-dora-evidence
Environment=PATH=/opt/vmware-dora-evidence/venv/bin
ExecStart=/opt/vmware-dora-evidence/venv/bin/python -m src.cli daemon
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable dora-evidence
sudo systemctl start dora-evidence
sudo systemctl status dora-evidence
```

### Windows Service

Install as Windows service using `pywin32`:

```bash
pip install pywin32

# Install service
python scripts/windows_service.py install

# Start service
python scripts/windows_service.py start
```

## Docker Configuration

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  dora-evidence:
    image: ghcr.io/uldyssian-sh/vmware-dora-evidence:latest
    container_name: dora-evidence
    environment:
      - VMWARE_VCENTER_HOST=${VMWARE_VCENTER_HOST}
      - VMWARE_USERNAME=${VMWARE_USERNAME}
      - VMWARE_PASSWORD=${VMWARE_PASSWORD}
      - DATABASE_URL=postgresql://postgres:password@db:5432/dora_evidence
    volumes:
      - ./config:/app/config
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:13
    container_name: dora-evidence-db
    environment:
      - POSTGRES_DB=dora_evidence
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

Run with Docker Compose:

```bash
docker-compose up -d
```

## Troubleshooting

### Common Issues

#### 1. VMware Connection Failed

**Error**: `Connection to vCenter failed`

**Solutions**:
- Verify vCenter hostname and port
- Check network connectivity: `telnet vcenter-host 443`
- Verify credentials
- Check SSL certificate settings

#### 2. Permission Denied

**Error**: `Permission denied accessing vCenter events`

**Solutions**:
- Verify user has read permissions on vCenter
- Check user role assignments
- Ensure user can access event logs

#### 3. Database Connection Failed

**Error**: `Database connection failed`

**Solutions**:
- Verify database URL format
- Check database server is running
- Verify credentials and database exists
- Check network connectivity to database

#### 4. Import Errors

**Error**: `ModuleNotFoundError: No module named 'pyVmomi'`

**Solutions**:
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or install specific package
pip install pyvmomi
```

#### 5. SSL Certificate Errors

**Error**: `SSL certificate verification failed`

**Solutions**:
```yaml
# Temporarily ignore SSL errors (not recommended for production)
vmware:
  ignore_ssl_errors: true

# Or provide custom certificate
vmware:
  ssl_cert_path: "/path/to/certificate.pem"
```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
export LOG_LEVEL="DEBUG"

# Or in configuration file
logging:
  level: "DEBUG"
```

### Log Files

Check log files for detailed error information:

```bash
# Default log location
tail -f logs/dora-evidence.log

# Or check system logs
journalctl -u dora-evidence -f
```

### Health Check

Run health check to verify installation:

```bash
python -m src.cli health-check
```

## Getting Help

If you encounter issues not covered in this guide:

1. Search [existing issues](https://github.com/uldyssian-sh/vmware-dora-evidence/issues)
2. Create a [new issue](https://github.com/uldyssian-sh/vmware-dora-evidence/issues/new)
3. Join our [discussions](https://github.com/uldyssian-sh/vmware-dora-evidence/discussions)

## Next Steps

After successful installation, you can start using the VMware DORA Evidence tool to collect and analyze metrics from your VMware environment.