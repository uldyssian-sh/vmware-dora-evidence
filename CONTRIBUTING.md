# Contributing to VMware DORA Evidence

Thank you for your interest in contributing to VMware DORA Evidence! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Process](#contributing-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Security](#security)

## Code of Conduct

This project adheres to a code of conduct that promotes a welcoming and inclusive environment. By participating, you agree to uphold these standards.

### Our Standards

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- VMware vCenter access (for testing)
- Basic understanding of DORA metrics

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/vmware-dora-evidence.git
   cd vmware-dora-evidence
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Install Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

5. **Run Tests**
   ```bash
   pytest
   ```

## Contributing Process

### 1. Create an Issue

Before starting work, create an issue to discuss:
- Bug reports
- Feature requests
- Documentation improvements
- Performance enhancements

### 2. Fork and Branch

```bash
# Fork the repository on GitHub
git checkout -b feature/your-feature-name
# or
git checkout -b bugfix/issue-number
```

### 3. Make Changes

- Write clean, readable code
- Follow coding standards
- Add tests for new functionality
- Update documentation as needed

### 4. Test Your Changes

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
mypy src/
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: add new DORA metric calculation"
```

**Commit Message Format:**
- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation changes
- `style:` formatting changes
- `refactor:` code refactoring
- `test:` adding tests
- `chore:` maintenance tasks

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Create a pull request with:
- Clear title and description
- Reference to related issues
- Screenshots (if applicable)
- Testing instructions

## Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications:

- Line length: 88 characters (Black formatter)
- Use type hints for all functions
- Docstrings for all public methods
- Meaningful variable and function names

### Code Organization

```
src/
├── collectors/          # Data collection modules
├── analyzers/           # Metrics analysis
├── reporters/           # Report generation
├── integrations/        # External system integrations
└── utils/              # Utility functions
```

### Example Code Style

```python
from typing import List, Dict, Any, Optional
from datetime import datetime

def collect_deployment_data(
    start_date: datetime,
    end_date: datetime,
    max_records: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Collect deployment data from VMware environment.

    Args:
        start_date: Start date for data collection
        end_date: End date for data collection
        max_records: Maximum number of records to collect

    Returns:
        List of deployment records

    Raises:
        ValueError: If date range is invalid
        ConnectionError: If VMware connection fails
    """
    if start_date >= end_date:
        raise ValueError("Start date must be before end date")

    # Implementation here
    return []
```

## Testing Guidelines

### Test Structure

```
tests/
├── unit/               # Unit tests
├── integration/        # Integration tests
└── fixtures/          # Test data and fixtures
```

### Writing Tests

```python
import pytest
from unittest.mock import Mock, patch
from src.collectors.deployment_collector import DeploymentCollector

class TestDeploymentCollector:
    """Test suite for DeploymentCollector."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.collector = DeploymentCollector(self.mock_client)

    def test_collect_deployments_success(self):
        """Test successful deployment collection."""
        # Arrange
        expected_deployments = [{"id": "test-1", "status": "success"}]
        self.mock_client.get_events.return_value = expected_deployments

        # Act
        result = self.collector.collect_deployments(
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 31)
        )

        # Assert
        assert len(result) == 1
        assert result[0]["id"] == "test-1"

    def test_collect_deployments_empty_result(self):
        """Test deployment collection with no results."""
        # Arrange
        self.mock_client.get_events.return_value = []

        # Act
        result = self.collector.collect_deployments(
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 31)
        )

        # Assert
        assert len(result) == 0
```

### Test Coverage

- Aim for >90% code coverage
- Test both success and failure scenarios
- Include edge cases and boundary conditions
- Mock external dependencies

## Documentation

### Code Documentation

- Use docstrings for all public functions and classes
- Include type hints
- Provide usage examples
- Document exceptions

### User Documentation

- Update README.md for new features
- Add tutorials for complex functionality
- Include configuration examples
- Update API documentation

### Documentation Format

```python
def calculate_dora_metrics(
    deployments: List[Dict[str, Any]],
    incidents: List[Dict[str, Any]]
) -> Dict[str, float]:
    """
    Calculate DORA metrics from deployment and incident data.

    This function computes the four key DORA metrics:
    - Deployment Frequency
    - Lead Time for Changes
    - Change Failure Rate
    - Time to Restore Service

    Args:
        deployments: List of deployment records with timestamps and status
        incidents: List of incident records with resolution times

    Returns:
        Dictionary containing calculated DORA metrics:
        {
            'deployment_frequency': float,
            'lead_time_for_changes': float,
            'change_failure_rate': float,
            'time_to_restore_service': float
        }

    Raises:
        ValueError: If input data is invalid or insufficient

    Example:
        >>> deployments = [{'timestamp': '2023-01-01', 'status': 'success'}]
        >>> incidents = [{'resolution_time': 30}]
        >>> metrics = calculate_dora_metrics(deployments, incidents)
        >>> print(metrics['deployment_frequency'])
        1.0
    """
```

## Security

### Security Guidelines

- Never commit credentials or sensitive data
- Use environment variables for configuration
- Validate all inputs
- Follow secure coding practices
- Run security scans regularly

### Reporting Security Issues

Please report security vulnerabilities privately by emailing the maintainers. Do not create public issues for security problems.

### Security Checklist

- [ ] No hardcoded credentials
- [ ] Input validation implemented
- [ ] Secure communication protocols
- [ ] Error messages don't leak sensitive information
- [ ] Dependencies are up to date

## Review Process

### Pull Request Review

All contributions go through code review:

1. **Automated Checks**: CI/CD pipeline runs tests and quality checks
2. **Peer Review**: At least one maintainer reviews the code
3. **Testing**: Changes are tested in development environment
4. **Documentation**: Documentation is updated if needed

### Review Criteria

- Code quality and style
- Test coverage
- Performance impact
- Security considerations
- Documentation completeness

## Release Process

### Versioning

We use Semantic Versioning (SemVer):
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes (backward compatible)

### Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version number bumped
- [ ] Security scan completed
- [ ] Performance benchmarks run

## Getting Help

### Resources

- [Project Documentation](docs/)
- [API Reference](docs/api.md)
- [Tutorials](docs/tutorials/)
- [FAQ](docs/faq.md)

### Communication

- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: General questions and ideas
- Email: For security issues and private matters

### Community

- Be patient and respectful
- Search existing issues before creating new ones
- Provide detailed information in bug reports
- Help others when possible

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing to VMware DORA Evidence!