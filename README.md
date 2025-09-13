# VMware DORA Evidence

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Security: bandit](https://img.shields.io/badge/security-bandit-green.svg)](https://github.com/PyCQA/bandit)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

A comprehensive tool for collecting and analyzing DORA (DevOps Research and Assessment) metrics from VMware environments, providing insights into deployment frequency, lead time, change failure rate, and recovery time.

**Author**: LT - [GitHub Profile](https://github.com/uldyssian-sh)

## 🚀 Features

- **Automated DORA Metrics Collection**: Seamlessly gather deployment frequency, lead time for changes, change failure rate, and time to restore service
- **VMware Integration**: Native support for vCenter, vSphere, and VMware Cloud environments
- **Real-time Monitoring**: Continuous tracking of deployment pipelines and infrastructure changes
- **Comprehensive Reporting**: Generate detailed reports with visualizations and trend analysis
- **Security First**: Built with security best practices, no hardcoded credentials
- **Extensible Architecture**: Plugin-based system for custom integrations

## 📊 DORA Metrics Supported

| Metric | Description | Implementation |
|--------|-------------|----------------|
| **Deployment Frequency** | How often deployments occur | Tracks VMware deployment events and CI/CD pipeline executions |
| **Lead Time for Changes** | Time from commit to production | Measures code commit to deployment completion |
| **Change Failure Rate** | Percentage of deployments causing failures | Monitors rollbacks, hotfixes, and incident correlation |
| **Time to Restore Service** | Recovery time from incidents | Tracks incident detection to resolution |

## 🏗️ Architecture

```
vmware-dora-evidence/
├── src/
│   ├── collectors/          # Data collection modules
│   ├── analyzers/           # Metrics analysis engines
│   ├── reporters/           # Report generation
│   └── integrations/        # VMware API integrations
├── tests/                   # Comprehensive test suite
├── docs/                    # Documentation and tutorials
├── config/                  # Configuration templates
└── examples/                # Usage examples
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- VMware vCenter access
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/uldyssian-sh/vmware-dora-evidence.git
cd vmware-dora-evidence

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

### Configuration

```bash
# Copy configuration template
cp config/config.template.yaml config/config.yaml

# Edit configuration with your VMware environment details
# Note: Never commit actual credentials to version control
```

### Basic Usage

```python
from src.dora_evidence import DORACollector

# Initialize collector
collector = DORACollector(config_path="config/config.yaml")

# Collect metrics
metrics = collector.collect_all_metrics()

# Generate report
report = collector.generate_report(metrics)
print(report)
```

## 📖 Documentation

- [Installation Guide](docs/installation.md)
- [Configuration Reference](docs/configuration.md)
- [API Documentation](docs/api.md)
- [Tutorials](docs/tutorials/)
- [Contributing Guidelines](CONTRIBUTING.md)

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run security checks
bandit -r src/

# Run linting
flake8 src/
black --check src/
```

## 🔒 Security

This project follows security best practices:

- No hardcoded credentials or sensitive data
- Secure configuration management
- Regular security scanning with Bandit
- Input validation and sanitization
- Encrypted communication with VMware APIs

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- VMware for providing excellent APIs and documentation
- The DORA research team for defining these crucial metrics
- The open-source community for inspiration and tools

## 📞 Support

- 📚 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/uldyssian-sh/vmware-dora-evidence/issues)
- 💬 [Discussions](https://github.com/uldyssian-sh/vmware-dora-evidence/discussions)

---

**Note**: This tool is designed for monitoring and analysis purposes. Always ensure compliance with your organization's security policies and VMware licensing terms.