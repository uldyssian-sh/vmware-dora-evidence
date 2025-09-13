"""
Unit tests for DeploymentCollector.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.collectors.deployment_collector import DeploymentCollector


class TestDeploymentCollector:
    """Test suite for DeploymentCollector."""
    
    def test_init(self, mock_vmware_client):
        """Test DeploymentCollector initialization."""
        collector = DeploymentCollector(mock_vmware_client)
        
        assert collector.vmware_client == mock_vmware_client
        assert collector.logger is not None
    
    def test_collect_deployments_success(self, deployment_collector, sample_vmware_events, date_range):
        """Test successful deployment collection."""
        # Arrange
        deployment_collector.vmware_client.get_events.return_value = sample_vmware_events
        
        # Act
        result = deployment_collector.collect_deployments(
            start_date=date_range['start_date'],
            end_date=date_range['end_date']
        )
        
        # Assert
        assert len(result) >= 1
        assert all('id' in deployment for deployment in result)
        assert all('type' in deployment for deployment in result)
        assert all('timestamp' in deployment for deployment in result)
    
    def test_collect_deployments_empty_result(self, deployment_collector, date_range):
        """Test deployment collection with no results."""
        # Arrange
        deployment_collector.vmware_client.get_events.return_value = []
        
        # Act
        result = deployment_collector.collect_deployments(
            start_date=date_range['start_date'],
            end_date=date_range['end_date']
        )
        
        # Assert
        assert len(result) == 0
    
    def test_collect_deployments_exception_handling(self, deployment_collector, date_range):
        """Test deployment collection exception handling."""
        # Arrange
        deployment_collector.vmware_client.get_events.side_effect = Exception("Connection failed")
        
        # Act & Assert
        with pytest.raises(Exception, match="Connection failed"):
            deployment_collector.collect_deployments(
                start_date=date_range['start_date'],
                end_date=date_range['end_date']
            )
    
    def test_collect_vm_deployments(self, deployment_collector, sample_vmware_events, date_range):
        """Test VM deployment collection."""
        # Arrange
        vm_events = [event for event in sample_vmware_events if 'VmCreated' in event['eventTypeId']]
        deployment_collector.vmware_client.get_events.return_value = vm_events
        
        # Act
        result = deployment_collector._collect_vm_deployments(
            start_date=date_range['start_date'],
            end_date=date_range['end_date']
        )
        
        # Assert
        assert len(result) >= 1
        assert all(deployment['type'] == 'vm_deployment' for deployment in result)
        assert all('vm_name' in deployment for deployment in result)
    
    def test_collect_application_deployments(self, deployment_collector, date_range):
        """Test application deployment collection."""
        # Act
        result = deployment_collector._collect_application_deployments(
            start_date=date_range['start_date'],
            end_date=date_range['end_date']
        )
        
        # Assert
        assert isinstance(result, list)
        # Note: This returns sample data in the current implementation
        if result:
            assert all(deployment['type'] == 'application_deployment' for deployment in result)
    
    def test_collect_infrastructure_changes(self, deployment_collector, date_range):
        """Test infrastructure change collection."""
        # Arrange
        config_events = [
            {
                'key': 'event-003',
                'eventTypeId': 'VmReconfiguredEvent',
                'createdTime': datetime.now(),
                'userName': 'admin',
                'fullFormattedMessage': 'VM reconfigured',
                'objectName': 'test-vm',
                'objectType': 'VirtualMachine'
            }
        ]
        deployment_collector.vmware_client.get_events.return_value = config_events
        
        # Act
        result = deployment_collector._collect_infrastructure_changes(
            start_date=date_range['start_date'],
            end_date=date_range['end_date']
        )
        
        # Assert
        assert len(result) >= 1
        assert all(change['type'] == 'infrastructure_change' for change in result)
    
    def test_calculate_deployment_duration(self, deployment_collector):
        """Test deployment duration calculation."""
        # Arrange
        event = {
            'key': 'test-event',
            'eventTypeId': 'VmCreatedEvent',
            'createdTime': datetime.now()
        }
        
        # Act
        duration = deployment_collector._calculate_deployment_duration(event)
        
        # Assert
        assert isinstance(duration, int)
        assert duration > 0
    
    def test_get_deployment_statistics_with_data(self, deployment_collector, sample_deployment_data):
        """Test deployment statistics calculation with data."""
        # Act
        stats = deployment_collector.get_deployment_statistics(sample_deployment_data)
        
        # Assert
        assert stats['total_deployments'] == len(sample_deployment_data)
        assert stats['successful_deployments'] >= 0
        assert stats['failed_deployments'] >= 0
        assert 0 <= stats['success_rate'] <= 100
        assert stats['average_duration_minutes'] >= 0
    
    def test_get_deployment_statistics_empty_data(self, deployment_collector):
        """Test deployment statistics calculation with empty data."""
        # Act
        stats = deployment_collector.get_deployment_statistics([])
        
        # Assert
        assert stats['total_deployments'] == 0
        assert stats['successful_deployments'] == 0
        assert stats['failed_deployments'] == 0
        assert stats['success_rate'] == 0.0
        assert stats['average_duration_minutes'] == 0.0
    
    def test_get_deployment_statistics_all_successful(self, deployment_collector):
        """Test deployment statistics with all successful deployments."""
        # Arrange
        deployments = [
            {'status': 'success', 'duration_minutes': 10},
            {'status': 'success', 'duration_minutes': 20},
            {'status': 'success', 'duration_minutes': 15}
        ]
        
        # Act
        stats = deployment_collector.get_deployment_statistics(deployments)
        
        # Assert
        assert stats['total_deployments'] == 3
        assert stats['successful_deployments'] == 3
        assert stats['failed_deployments'] == 0
        assert stats['success_rate'] == 100.0
        assert stats['average_duration_minutes'] == 15.0
    
    def test_get_deployment_statistics_mixed_results(self, deployment_collector):
        """Test deployment statistics with mixed results."""
        # Arrange
        deployments = [
            {'status': 'success', 'duration_minutes': 10},
            {'status': 'failed', 'duration_minutes': 5},
            {'status': 'success', 'duration_minutes': 20}
        ]
        
        # Act
        stats = deployment_collector.get_deployment_statistics(deployments)
        
        # Assert
        assert stats['total_deployments'] == 3
        assert stats['successful_deployments'] == 2
        assert stats['failed_deployments'] == 1
        assert abs(stats['success_rate'] - 66.67) < 0.1  # Approximately 66.67%
        assert abs(stats['average_duration_minutes'] - 11.67) < 0.1  # Average of 10, 5, 20
    
    @patch('src.collectors.deployment_collector.setup_logger')
    def test_logger_setup(self, mock_setup_logger, mock_vmware_client):
        """Test logger setup during initialization."""
        # Arrange
        mock_logger = Mock()
        mock_setup_logger.return_value = mock_logger
        
        # Act
        collector = DeploymentCollector(mock_vmware_client)
        
        # Assert
        mock_setup_logger.assert_called_once()
        assert collector.logger == mock_logger