# VMware DORA Evidence Collection

<div align="center">
  <img src="https://cloud.google.com/static/images/dora-research-logo.png" alt="DORA Metrics" width="300"/>
  
  [![DORA](https://img.shields.io/badge/DORA-Metrics-blue.svg)](https://www.devops-research.com/research.html)
  [![DevOps](https://img.shields.io/badge/DevOps-Performance-green.svg)](https://cloud.google.com/blog/products/devops-sre/using-the-four-keys-to-measure-your-devops-performance)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
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
# Install dependencies
pip install -r requirements.txt

# Configure data sources
cp config/config.example.yml config/config.yml
# Edit config.yml with your tool integrations

# Collect metrics
python dora_collector.py --period 30d --output-format json

# Generate report
python generate_report.py --input metrics.json --format html
```

## 📈 Dashboard Preview

![DORA Dashboard](https://via.placeholder.com/800x500/4A90E2/FFFFFF?text=DORA+Metrics+Dashboard)

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

## 📚 Documentation

- [Setup Guide](https://github.com/uldyssian-sh/vmware-dora-evidence/wiki/Setup)
- [Data Source Configuration](https://github.com/uldyssian-sh/vmware-dora-evidence/wiki/Data-Sources)
- [Report Customization](https://github.com/uldyssian-sh/vmware-dora-evidence/wiki/Reports)

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.
