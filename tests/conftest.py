"""
Pytest configuration and shared fixtures.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List

from src.integrations.vmware_client import VMwareClient
from src.collectors.deployment_collector import DeploymentCollector
from src.collectors.incident_collector import IncidentCollector
from src.dora_evidence import DORACollector


@pytest.fixture
def mock_vmware_config():
    """Mock VMware configuration."""
    return {
        'vcenter_host': 'test-vcenter.example.com',
        'username': 'test-user',
        'password': 'test-password',
        'port': 443,
        'ignore_ssl_errors': True
    }


@pytest.fixture
def mock_vmware_client(mock_vmware_config):
    """Mock VMware client."""
    client = Mock(spec=VMwareClient)
    client.config = mock_vmware_config
    client.test_connection.return_value = True
    return client


@pytest.fixture
def deployment_collector(mock_vmware_client):
    """Deployment collector with mocked VMware client."""
    return DeploymentCollector(mock_vmware_client)


@pytest.fixture
def incident_collector(mock_vmware_client):
    """Incident collector with mocked VMware client."""
    return IncidentCollector(mock_vmware_client)


@pytest.fixture
def sample_deployment_data():
    """Sample deployment data for testing."""
    base_time = datetime(2023, 1, 1, 10, 0, 0)
    
    return [
        {
            'id': 'deploy-001',
            'type': 'vm_deployment',
            'timestamp': base_time,
            'vm_name': 'test-vm-001',
            'datacenter': 'DC1',
            'user': 'admin',
            'status': 'success',
            'duration_minutes': 15,
            'metadata': {
                'event_type': 'VmCreatedEvent',
                'description': 'VM created successfully'
            }
        },
        {
            'id': 'deploy-002',
            'type': 'application_deployment',
            'timestamp': base_time + timedelta(hours=2),
            'application_name': 'web-app',
            'version': 'v1.2.0',
            'environment': 'production',
            'status': 'success',
            'duration_minutes': 25,
            'commit_sha': 'abc123def',
            'metadata': {
                'pipeline_id': 'pipeline-001',
                'branch': 'main'
            }
        },
        {
            'id': 'deploy-003',
            'type': 'infrastructure_change',
            'timestamp': base_time + timedelta(hours=4),
            'target': 'network-config',
            'change_type': 'VmReconfiguredEvent',
            'user': 'admin',
            'status': 'failed',
            'duration_minutes': 5,
            'metadata': {
                'description': 'Network configuration failed',
                'object_type': 'VirtualMachine'
            }
        }
    ]


@pytest.fixture
def sample_incident_data():
    """Sample incident data for testing."""
    base_time = datetime(2023, 1, 1, 12, 0, 0)
    
    return [
        {
            'id': 'incident-001',
            'type': 'vm_incident',
            'severity': 'high',
            'timestamp': base_time,
            'vm_name': 'test-vm-001',
            'datacenter': 'DC1',
            'status': 'resolved',
            'resolution_time_minutes': 45,
            'root_cause': 'power_failure',
            'metadata': {
                'event_type': 'VmFailedToPowerOnEvent',
                'description': 'VM failed to power on',
                'host': 'esxi-host-001'
            }
        },
        {
            'id': 'incident-002',
            'type': 'host_incident',
            'severity': 'critical',
            'timestamp': base_time + timedelta(hours=1),
            'host_name': 'esxi-host-002',
            'datacenter': 'DC1',
            'status': 'resolved',
            'resolution_time_minutes': 120,
            'root_cause': 'host_failure',
            'metadata': {
                'event_type': 'HostDisconnectedEvent',
                'description': 'Host disconnected from vCenter'
            }
        },
        {
            'id': 'incident-003',
            'type': 'application_incident',
            'severity': 'medium',
            'timestamp': base_time + timedelta(hours=2),
            'application_name': 'web-app',
            'environment': 'production',
            'status': 'resolved',
            'resolution_time_minutes': 30,
            'root_cause': 'deployment_failure',
            'metadata': {
                'error_message': 'Service unavailable',
                'affected_users': 100
            }
        }
    ]


@pytest.fixture
def sample_vmware_events():
    """Sample VMware events for testing."""
    base_time = datetime(2023, 1, 1, 9, 0, 0)
    
    return [
        {
            'key': 'event-001',
            'eventTypeId': 'VmCreatedEvent',
            'createdTime': base_time,
            'userName': 'admin',
            'fullFormattedMessage': 'Virtual machine test-vm-001 was created',
            'objectName': 'test-vm-001',
            'objectType': 'VirtualMachine',
            'vm': {
                'name': 'test-vm-001',
                'moId': 'vm-001'
            },
            'datacenter': {
                'name': 'DC1',
                'moId': 'datacenter-001'
            }
        },
        {
            'key': 'event-002',
            'eventTypeId': 'VmFailedToPowerOnEvent',
            'createdTime': base_time + timedelta(hours=3),
            'userName': 'system',
            'fullFormattedMessage': 'Virtual machine test-vm-002 failed to power on',
            'objectName': 'test-vm-002',
            'objectType': 'VirtualMachine',
            'vm': {
                'name': 'test-vm-002',
                'moId': 'vm-002'
            },
            'host': {
                'name': 'esxi-host-001',
                'moId': 'host-001'
            }
        }
    ]


@pytest.fixture
def mock_config():
    """Mock application configuration."""
    return {
        'vmware': {
            'vcenter_host': 'test-vcenter.example.com',
            'username': 'test-user',
            'password': 'test-password',
            'port': 443,
            'ignore_ssl_errors': True
        },
        'database': {
            'type': 'sqlite',
            'url': 'sqlite:///:memory:'
        },
        'logging': {
            'level': 'DEBUG'
        },
        'collection': {
            'interval_minutes': 60,
            'retention_days': 30,
            'max_events_per_collection': 100
        }
    }


@pytest.fixture
def dora_collector(mock_config):
    """DORA collector with mocked configuration."""
    with pytest.mock.patch('src.dora_evidence.ConfigManager') as mock_config_manager:
        mock_config_manager.return_value.get_config.return_value = mock_config
        
        with pytest.mock.patch('src.dora_evidence.VMwareClient') as mock_client:
            mock_client.return_value.test_connection.return_value = True
            
            collector = DORACollector()
            return collector


@pytest.fixture
def date_range():
    """Standard date range for testing."""
    return {
        'start_date': datetime(2023, 1, 1),
        'end_date': datetime(2023, 1, 31)
    }


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    return Mock()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add unit marker to all tests by default
        if not any(marker.name in ['integration', 'slow'] for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)
        
        # Add slow marker to tests that might be slow
        if 'integration' in item.nodeid or 'slow' in item.name:
            item.add_marker(pytest.mark.slow)