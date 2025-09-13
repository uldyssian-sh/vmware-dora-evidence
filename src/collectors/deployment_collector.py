"""
Deployment data collector for VMware environments.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..integrations.vmware_client import VMwareClient
from ..utils.logger import setup_logger


class DeploymentCollector:
    """Collects deployment data from VMware infrastructure."""
    
    def __init__(self, vmware_client: VMwareClient):
        """
        Initialize deployment collector.
        
        Args:
            vmware_client: VMware API client instance
        """
        self.vmware_client = vmware_client
        self.logger = setup_logger(__name__)
    
    def collect_deployments(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Collect deployment events from VMware environment.
        
        Args:
            start_date: Start date for data collection
            end_date: End date for data collection
            
        Returns:
            List of deployment records
        """
        self.logger.info(f"Collecting deployments from {start_date} to {end_date}")
        
        deployments = []
        
        try:
            # Collect VM deployment events
            vm_deployments = self._collect_vm_deployments(start_date, end_date)
            deployments.extend(vm_deployments)
            
            # Collect application deployments
            app_deployments = self._collect_application_deployments(start_date, end_date)
            deployments.extend(app_deployments)
            
            # Collect infrastructure changes
            infra_changes = self._collect_infrastructure_changes(start_date, end_date)
            deployments.extend(infra_changes)
            
            self.logger.info(f"Successfully collected {len(deployments)} deployment records")
            
        except Exception as e:
            self.logger.error(f"Error collecting deployments: {str(e)}")
            raise
        
        return deployments
    
    def _collect_vm_deployments(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Collect VM deployment events.
        
        Args:
            start_date: Start date for collection
            end_date: End date for collection
            
        Returns:
            List of VM deployment records
        """
        self.logger.debug("Collecting VM deployment events")
        
        vm_deployments = []
        
        # Get VM creation events from vCenter
        events = self.vmware_client.get_events(
            event_types=['VmCreatedEvent', 'VmDeployedEvent'],
            start_time=start_date,
            end_time=end_date
        )
        
        for event in events:
            deployment = {
                'id': event.get('key'),
                'type': 'vm_deployment',
                'timestamp': event.get('createdTime'),
                'vm_name': event.get('vm', {}).get('name'),
                'datacenter': event.get('datacenter', {}).get('name'),
                'user': event.get('userName'),
                'status': 'success',
                'duration_minutes': self._calculate_deployment_duration(event),
                'metadata': {
                    'event_type': event.get('eventTypeId'),
                    'description': event.get('fullFormattedMessage')
                }
            }
            vm_deployments.append(deployment)
        
        return vm_deployments
    
    def _collect_application_deployments(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Collect application deployment events.
        
        Args:
            start_date: Start date for collection
            end_date: End date for collection
            
        Returns:
            List of application deployment records
        """
        self.logger.debug("Collecting application deployment events")
        
        app_deployments = []
        
        # Get application deployment events
        # This would integrate with CI/CD systems, VMware vRealize, etc.
        
        # Example implementation - replace with actual integration
        sample_deployments = [
            {
                'id': f'app-deploy-{i}',
                'type': 'application_deployment',
                'timestamp': start_date,
                'application_name': f'sample-app-{i}',
                'version': f'v1.{i}.0',
                'environment': 'production',
                'status': 'success',
                'duration_minutes': 15,
                'commit_sha': f'abc123{i}',
                'metadata': {
                    'pipeline_id': f'pipeline-{i}',
                    'branch': 'main'
                }
            }
            for i in range(5)  # Sample data
        ]
        
        app_deployments.extend(sample_deployments)
        
        return app_deployments
    
    def _collect_infrastructure_changes(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Collect infrastructure change events.
        
        Args:
            start_date: Start date for collection
            end_date: End date for collection
            
        Returns:
            List of infrastructure change records
        """
        self.logger.debug("Collecting infrastructure change events")
        
        infra_changes = []
        
        # Get configuration changes from vCenter
        config_events = self.vmware_client.get_events(
            event_types=['VmReconfiguredEvent', 'HostConfigChangedEvent'],
            start_time=start_date,
            end_time=end_date
        )
        
        for event in config_events:
            change = {
                'id': event.get('key'),
                'type': 'infrastructure_change',
                'timestamp': event.get('createdTime'),
                'target': event.get('objectName'),
                'change_type': event.get('eventTypeId'),
                'user': event.get('userName'),
                'status': 'success',
                'duration_minutes': 5,  # Estimated
                'metadata': {
                    'description': event.get('fullFormattedMessage'),
                    'object_type': event.get('objectType')
                }
            }
            infra_changes.append(change)
        
        return infra_changes
    
    def _calculate_deployment_duration(self, event: Dict[str, Any]) -> int:
        """
        Calculate deployment duration from event data.
        
        Args:
            event: Event data
            
        Returns:
            Duration in minutes
        """
        # This would calculate actual duration based on event data
        # For now, return estimated duration
        return 10  # Default 10 minutes
    
    def get_deployment_statistics(
        self, 
        deployments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate deployment statistics.
        
        Args:
            deployments: List of deployment records
            
        Returns:
            Deployment statistics
        """
        if not deployments:
            return {
                'total_deployments': 0,
                'successful_deployments': 0,
                'failed_deployments': 0,
                'success_rate': 0.0,
                'average_duration_minutes': 0.0
            }
        
        total = len(deployments)
        successful = len([d for d in deployments if d.get('status') == 'success'])
        failed = total - successful
        
        durations = [d.get('duration_minutes', 0) for d in deployments]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            'total_deployments': total,
            'successful_deployments': successful,
            'failed_deployments': failed,
            'success_rate': (successful / total) * 100 if total > 0 else 0.0,
            'average_duration_minutes': avg_duration
        }