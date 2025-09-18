# VMware DORA Evidence Collection

<div align="center">
  
  [![DORA](https://img.shields.io/badge/DORA-Metrics-blue.svg)](https://dora.dev)
  [![DevOps](https://img.shields.io/badge/DevOps-Performance-green.svg)](https://cloud.google.com/blog/products/devops-sre/using-the-four-keys-to-measure-your-devops-performance)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![CI](https://github.com/uldyssian-sh/vmware-dora-evidence/workflows/CI/badge.svg)](https://github.com/uldyssian-sh/vmware-dora-evidence/actions)
</div>

## 📊 Overview

Automated DORA (DevOps Research and Assessment) metrics collection and reporting for VMware infrastructure teams. Measure and improve DevOps performance using the Four Key Metrics.

## 🎯 Four Key Metrics

### 1. Deployment Frequency
- **Definition**: How often code is deployed to production
- **Measurement**: Deployments per day/week/month
- **Elite Performance**: Multiple deployments per day

### 2. Lead Time for Changes
- **Definition**: Time from code commit to production deployment
- **Measurement**: Hours/days from commit to deploy
- **Elite Performance**: Less than one hour

### 3. Change Failure Rate
- **Definition**: Percentage of deployments causing failures
- **Measurement**: Failed deployments / Total deployments
- **Elite Performance**: 0-15%

### 4. Time to Restore Service
- **Definition**: Time to recover from production incidents
- **Measurement**: Hours/days to restore service
- **Elite Performance**: Less than one hour

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/uldyssian-sh/vmware-dora-evidence.git
cd vmware-dora-evidence

# Install dependencies
pip install -r requirements.txt

# Configure VMware connection
cp config/config.template.yaml config/config.yaml
# Edit config.yaml with your VMware credentials

# Collect DORA metrics
python -m src.cli collect --days 30 --format json

# Generate HTML report
python -m src.cli report --days 30 --format html
```



### Docker Deployment

```bash
# Build Docker image
docker build -t vmware-dora-evidence .

# Run container with configuration
docker run -d \
  --name dora-evidence \
  -p 8000:8000 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/reports:/app/reports \
  vmware-dora-evidence
```

## 📖 Documentation

- [Configuration Template](config/config.template.yaml)
- [PowerShell Script](dora-evidence.ps1)
- [Examples Directory](examples/)
- [Installation Guide](docs/installation.md)

## 🔧 Data Sources

### Version Control
- **Git**: Commit frequency and lead time analysis
- **GitHub**: Pull request and merge metrics
- **GitLab**: Pipeline and deployment tracking

### CI/CD Platforms
- **Jenkins**: Build and deployment frequency
- **GitLab CI**: Pipeline success/failure rates
- **GitHub Actions**: Workflow execution metrics

### Monitoring & Incident Management
- **vRealize Operations**: Infrastructure incident tracking
- **ServiceNow**: Change and incident management
- **PagerDuty**: Alert and resolution tracking

## 📊 Report Examples

### Team Performance Report
```json
{
  "team": "Infrastructure Team",
  "period": "2024-Q1",
  "metrics": {
    "deployment_frequency": {
      "value": 2.3,
      "unit": "per_day",
      "performance_level": "high"
    },
    "lead_time": {
      "value": 4.2,
      "unit": "hours",
      "performance_level": "elite"
    },
    "change_failure_rate": {
      "value": 12.5,
      "unit": "percentage",
      "performance_level": "elite"
    },
    "recovery_time": {
      "value": 1.8,
      "unit": "hours",
      "performance_level": "high"
    }
  }
}
```

## 🌐 Resources

- [DORA Research](https://dora.dev)
- [Four Key Metrics Guide](https://cloud.google.com/blog/products/devops-sre/using-the-four-keys-to-measure-your-devops-performance)
- [VMware vSphere API](https://developer.vmware.com/apis/vsphere-automation/latest/)

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.
