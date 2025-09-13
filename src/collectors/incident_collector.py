"""
Incident data collector for VMware environments.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from ..integrations.vmware_client import VMwareClient
from ..utils.logger import setup_logger


class IncidentCollector:
    """Collects incident and failure data from VMware infrastructure."""
    
    def __init__(self, vmware_client: VMwareClient):
        """
        Initialize incident collector.
        
        Args:
            vmware_client: VMware API client instance
        """
        self.vmware_client = vmware_client
        self.logger = setup_logger(__name__)
    
    def collect_incidents(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Collect incident events from VMware environment.
        
        Args:
            start_date: Start date for data collection
            end_date: End date for data collection
            
        Returns:
            List of incident records
        """
        self.logger.info(f"Collecting incidents from {start_date} to {end_date}")
        
        incidents = []
        
        try:
            # Collect VM failures
            vm_incidents = self._collect_vm_incidents(start_date, end_date)
            incidents.extend(vm_incidents)
            
            # Collect host failures
            host_incidents = self._collect_host_incidents(start_date, end_date)
            incidents.extend(host_incidents)
            
            # Collect application failures
            app_incidents = self._collect_application_incidents(start_date, end_date)
            incidents.extend(app_incidents)
            
            # Collect network incidents
            network_incidents = self._collect_network_incidents(start_date, end_date)
            incidents.extend(network_incidents)
            
            self.logger.info(f"Successfully collected {len(incidents)} incident records")
            
        except Exception as e:
            self.logger.error(f"Error collecting incidents: {str(e)}")
            raise
        
        return incidents
    
    def _collect_vm_incidents(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Collect VM-related incidents.
        
        Args:
            start_date: Start date for collection
            end_date: End date for collection
            
        Returns:
            List of VM incident records
        """
        self.logger.debug("Collecting VM incidents")
        
        vm_incidents = []
        
        # Get VM failure events from vCenter
        failure_events = self.vmware_client.get_events(
            event_types=[
                'VmFailedToPowerOnEvent',
                'VmFailedToPowerOffEvent',
                'VmSuspendedEvent',
                'VmMigrateFailedEvent'
            ],
            start_time=start_date,
            end_time=end_date
        )
        
        for event in failure_events:
            incident = {
                'id': event.get('key'),
                'type': 'vm_incident',
                'severity': self._determine_severity(event),
                'timestamp': event.get('createdTime'),
                'vm_name': event.get('vm', {}).get('name'),
                'datacenter': event.get('datacenter', {}).get('name'),
                'status': 'detected',
                'resolution_time_minutes': None,
                'root_cause': self._extract_root_cause(event),
                'metadata': {
                    'event_type': event.get('eventTypeId'),
                    'description': event.get('fullFormattedMessage'),
                    'host': event.get('host', {}).get('name')
                }
            }
            
            # Try to find resolution event
            resolution_time = self._find_resolution_time(incident, end_date)
            if resolution_time:
                incident['resolution_time_minutes'] = resolution_time
                incident['status'] = 'resolved'
            
            vm_incidents.append(incident)
        
        return vm_incidents
    
    def _collect_host_incidents(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Collect host-related incidents.
        
        Args:
            start_date: Start date for collection
            end_date: End date for collection
            
        Returns:
            List of host incident records
        """
        self.logger.debug("Collecting host incidents")
        
        host_incidents = []
        
        # Get host failure events
        host_events = self.vmware_client.get_events(
            event_types=[
                'HostDisconnectedEvent',
                'HostConnectionLostEvent',
                'HostNotRespondingEvent'
            ],
            start_time=start_date,
            end_time=end_date
        )
        
        for event in host_events:
            incident = {
                'id': event.get('key'),
                'type': 'host_incident',
                'severity': 'high',  # Host incidents are typically high severity
                'timestamp': event.get('createdTime'),
                'host_name': event.get('host', {}).get('name'),
                'datacenter': event.get('datacenter', {}).get('name'),
                'status': 'detected',
                'resolution_time_minutes': None,
                'root_cause': 'host_failure',
                'metadata': {
                    'event_type': event.get('eventTypeId'),
                    'description': event.get('fullFormattedMessage')
                }
            }
            
            # Try to find resolution
            resolution_time = self._find_resolution_time(incident, end_date)
            if resolution_time:
                incident['resolution_time_minutes'] = resolution_time
                incident['status'] = 'resolved'
            
            host_incidents.append(incident)
        
        return host_incidents
    
    def _collect_application_incidents(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Collect application-related incidents.
        
        Args:
            start_date: Start date for collection
            end_date: End date for collection
            
        Returns:
            List of application incident records
        """
        self.logger.debug("Collecting application incidents")
        
        app_incidents = []
        
        # This would integrate with monitoring systems, APM tools, etc.
        # For now, create sample data
        
        sample_incidents = [
            {
                'id': f'app-incident-{i}',
                'type': 'application_incident',
                'severity': 'medium',
                'timestamp': start_date + timedelta(days=i),
                'application_name': f'sample-app-{i}',
                'environment': 'production',
                'status': 'resolved',
                'resolution_time_minutes': 45,
                'root_cause': 'deployment_failure',
                'metadata': {
                    'error_message': 'Service unavailable',
                    'affected_users': 100
                }
            }
            for i in range(2)  # Sample data
        ]
        
        app_incidents.extend(sample_incidents)
        
        return app_incidents
    
    def _collect_network_incidents(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Collect network-related incidents.
        
        Args:
            start_date: Start date for collection
            end_date: End date for collection
            
        Returns:
            List of network incident records
        """
        self.logger.debug("Collecting network incidents")
        
        network_incidents = []
        
        # Get network-related events
        network_events = self.vmware_client.get_events(
            event_types=[
                'DvsPortLinkDownEvent',
                'DvsPortLinkUpEvent',
                'NetworkRollbackEvent'
            ],
            start_time=start_date,
            end_time=end_date
        )
        
        for event in network_events:
            if 'LinkDown' in event.get('eventTypeId', ''):
                incident = {
                    'id': event.get('key'),
                    'type': 'network_incident',
                    'severity': 'medium',
                    'timestamp': event.get('createdTime'),
                    'network_name': event.get('dvs', {}).get('name'),
                    'datacenter': event.get('datacenter', {}).get('name'),
                    'status': 'detected',
                    'resolution_time_minutes': None,
                    'root_cause': 'network_connectivity',
                    'metadata': {
                        'event_type': event.get('eventTypeId'),
                        'description': event.get('fullFormattedMessage')
                    }
                }
                
                # Try to find corresponding LinkUp event
                resolution_time = self._find_network_resolution(incident, network_events)
                if resolution_time:
                    incident['resolution_time_minutes'] = resolution_time
                    incident['status'] = 'resolved'
                
                network_incidents.append(incident)
        
        return network_incidents
    
    def _determine_severity(self, event: Dict[str, Any]) -> str:
        """
        Determine incident severity based on event type.
        
        Args:
            event: Event data
            
        Returns:
            Severity level (low, medium, high, critical)
        """
        event_type = event.get('eventTypeId', '')
        
        critical_events = ['VmFailedToPowerOnEvent', 'HostConnectionLostEvent']
        high_events = ['VmSuspendedEvent', 'HostDisconnectedEvent']
        medium_events = ['VmMigrateFailedEvent', 'DvsPortLinkDownEvent']
        
        if event_type in critical_events:
            return 'critical'
        elif event_type in high_events:
            return 'high'
        elif event_type in medium_events:
            return 'medium'
        else:
            return 'low'
    
    def _extract_root_cause(self, event: Dict[str, Any]) -> str:
        """
        Extract root cause from event data.
        
        Args:
            event: Event data
            
        Returns:
            Root cause category
        """
        event_type = event.get('eventTypeId', '')
        
        if 'PowerOn' in event_type:
            return 'power_failure'
        elif 'Migrate' in event_type:
            return 'migration_failure'
        elif 'Host' in event_type:
            return 'host_failure'
        elif 'Network' in event_type:
            return 'network_failure'
        else:
            return 'unknown'
    
    def _find_resolution_time(
        self, 
        incident: Dict[str, Any], 
        end_date: datetime
    ) -> Optional[int]:
        """
        Find resolution time for an incident.
        
        Args:
            incident: Incident record
            end_date: End date for search
            
        Returns:
            Resolution time in minutes, or None if not resolved
        """
        # This would search for corresponding resolution events
        # For now, return estimated resolution time based on severity
        
        severity = incident.get('severity', 'medium')
        
        if severity == 'critical':
            return 30  # 30 minutes
        elif severity == 'high':
            return 60  # 1 hour
        elif severity == 'medium':
            return 120  # 2 hours
        else:
            return 240  # 4 hours
    
    def _find_network_resolution(
        self, 
        incident: Dict[str, Any], 
        all_events: List[Dict[str, Any]]
    ) -> Optional[int]:
        """
        Find network incident resolution from LinkUp events.
        
        Args:
            incident: Network incident
            all_events: All network events
            
        Returns:
            Resolution time in minutes
        """
        incident_time = incident.get('timestamp')
        
        # Look for corresponding LinkUp event
        for event in all_events:
            if ('LinkUp' in event.get('eventTypeId', '') and 
                event.get('createdTime') > incident_time):
                
                # Calculate time difference
                time_diff = event.get('createdTime') - incident_time
                return int(time_diff.total_seconds() / 60)
        
        return None
    
    def get_incident_statistics(
        self, 
        incidents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate incident statistics.
        
        Args:
            incidents: List of incident records
            
        Returns:
            Incident statistics
        """
        if not incidents:
            return {
                'total_incidents': 0,
                'resolved_incidents': 0,
                'average_resolution_time_minutes': 0.0,
                'incidents_by_severity': {},
                'incidents_by_type': {}
            }
        
        total = len(incidents)
        resolved = len([i for i in incidents if i.get('status') == 'resolved'])
        
        # Calculate average resolution time
        resolution_times = [
            i.get('resolution_time_minutes', 0) 
            for i in incidents 
            if i.get('resolution_time_minutes') is not None
        ]
        avg_resolution = sum(resolution_times) / len(resolution_times) if resolution_times else 0
        
        # Group by severity
        severity_counts = {}
        for incident in incidents:
            severity = incident.get('severity', 'unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Group by type
        type_counts = {}
        for incident in incidents:
            incident_type = incident.get('type', 'unknown')
            type_counts[incident_type] = type_counts.get(incident_type, 0) + 1
        
        return {
            'total_incidents': total,
            'resolved_incidents': resolved,
            'average_resolution_time_minutes': avg_resolution,
            'incidents_by_severity': severity_counts,
            'incidents_by_type': type_counts
        }