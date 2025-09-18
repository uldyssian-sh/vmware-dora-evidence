"""
DORA metrics analyzer for calculating key DevOps metrics.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from statistics import mean, median

from ..utils.logger import setup_logger


class MetricsAnalyzer:
    """Analyzer for calculating DORA metrics from collected data."""
    
    def __init__(self):
        """Initialize the metrics analyzer."""
        self.logger = setup_logger(__name__)
    
    def calculate_dora_metrics(
        self, 
        deployments: List[Dict[str, Any]], 
        incidents: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Calculate all DORA metrics from deployment and incident data.
        
        Args:
            deployments: List of deployment records
            incidents: List of incident records
            
        Returns:
            Dictionary containing calculated DORA metrics
        """
        self.logger.info("Calculating DORA metrics")
        
        metrics = {
            'deployment_frequency': self._calculate_deployment_frequency(deployments),
            'lead_time_for_changes': self._calculate_lead_time(deployments),
            'change_failure_rate': self._calculate_change_failure_rate(deployments, incidents),
            'time_to_restore_service': self._calculate_recovery_time(incidents)
        }
        
        self.logger.info(f"Calculated DORA metrics: {metrics}")
        return metrics
    
    def _calculate_deployment_frequency(self, deployments: List[Dict[str, Any]]) -> float:
        """
        Calculate deployment frequency (deployments per day).
        
        Args:
            deployments: List of deployment records
            
        Returns:
            Deployment frequency as deployments per day
        """
        if not deployments:
            return 0.0
        
        # Get date range
        dates = [d.get('timestamp') for d in deployments if d.get('timestamp')]
        if not dates:
            return 0.0
        
        # Convert to datetime objects if they're strings
        datetime_objects = []
        for date in dates:
            if isinstance(date, str):
                try:
                    datetime_objects.append(datetime.fromisoformat(date.replace('Z', '+00:00')))
                except ValueError:
                    continue
            elif isinstance(date, datetime):
                datetime_objects.append(date)
        
        if len(datetime_objects) < 2:
            return len(deployments)  # If only one deployment, return count
        
        # Calculate time span in days
        min_date = min(datetime_objects)
        max_date = max(datetime_objects)
        time_span = (max_date - min_date).days
        
        if time_span == 0:
            time_span = 1  # At least one day
        
        frequency = len(deployments) / time_span
        self.logger.debug(f"Deployment frequency: {frequency} deployments/day")
        return frequency
    
    def _calculate_lead_time(self, deployments: List[Dict[str, Any]]) -> float:
        """
        Calculate lead time for changes (hours).
        
        Args:
            deployments: List of deployment records
            
        Returns:
            Average lead time in hours
        """
        lead_times = []
        
        for deployment in deployments:
            start_time = deployment.get('start_time')
            end_time = deployment.get('end_time')
            
            if start_time and end_time:
                # Convert to datetime if strings
                if isinstance(start_time, str):
                    try:
                        start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    except ValueError:
                        continue
                
                if isinstance(end_time, str):
                    try:
                        end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    except ValueError:
                        continue
                
                if isinstance(start_time, datetime) and isinstance(end_time, datetime):
                    lead_time_hours = (end_time - start_time).total_seconds() / 3600
                    if lead_time_hours >= 0:  # Ensure positive lead time
                        lead_times.append(lead_time_hours)
        
        if not lead_times:
            # Default lead time if no data available
            return 24.0  # 1 day default
        
        avg_lead_time = mean(lead_times)
        self.logger.debug(f"Average lead time: {avg_lead_time} hours")
        return avg_lead_time
    
    def _calculate_change_failure_rate(
        self, 
        deployments: List[Dict[str, Any]], 
        incidents: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate change failure rate (percentage).
        
        Args:
            deployments: List of deployment records
            incidents: List of incident records
            
        Returns:
            Change failure rate as percentage (0-100)
        """
        if not deployments:
            return 0.0
        
        # Count failed deployments
        failed_deployments = 0
        deployment_related_incidents = 0
        
        # Count deployments marked as failed
        for deployment in deployments:
            status = deployment.get('status', '').lower()
            if status in ['failed', 'error', 'failure']:
                failed_deployments += 1
        
        # Count incidents related to deployments (within 24 hours of deployment)
        for incident in incidents:
            incident_time = incident.get('timestamp')
            if not incident_time:
                continue
            
            # Convert to datetime if string
            if isinstance(incident_time, str):
                try:
                    incident_time = datetime.fromisoformat(incident_time.replace('Z', '+00:00'))
                except ValueError:
                    continue
            
            # Check if incident occurred within 24 hours of any deployment
            for deployment in deployments:
                deploy_time = deployment.get('timestamp')
                if not deploy_time:
                    continue
                
                if isinstance(deploy_time, str):
                    try:
                        deploy_time = datetime.fromisoformat(deploy_time.replace('Z', '+00:00'))
                    except ValueError:
                        continue
                
                if isinstance(deploy_time, datetime) and isinstance(incident_time, datetime):
                    time_diff = incident_time - deploy_time
                    if timedelta(0) <= time_diff <= timedelta(hours=24):
                        deployment_related_incidents += 1
                        break
        
        total_failures = failed_deployments + deployment_related_incidents
        failure_rate = (total_failures / len(deployments)) * 100
        
        self.logger.debug(f"Change failure rate: {failure_rate}%")
        return failure_rate
    
    def _calculate_recovery_time(self, incidents: List[Dict[str, Any]]) -> float:
        """
        Calculate mean time to recovery (hours).
        
        Args:
            incidents: List of incident records
            
        Returns:
            Average recovery time in hours
        """
        recovery_times = []
        
        for incident in incidents:
            start_time = incident.get('start_time') or incident.get('timestamp')
            end_time = incident.get('end_time') or incident.get('resolved_time')
            
            if start_time and end_time:
                # Convert to datetime if strings
                if isinstance(start_time, str):
                    try:
                        start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    except ValueError:
                        continue
                
                if isinstance(end_time, str):
                    try:
                        end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    except ValueError:
                        continue
                
                if isinstance(start_time, datetime) and isinstance(end_time, datetime):
                    recovery_time_hours = (end_time - start_time).total_seconds() / 3600
                    if recovery_time_hours >= 0:  # Ensure positive recovery time
                        recovery_times.append(recovery_time_hours)
        
        if not recovery_times:
            # Default recovery time if no data available
            return 4.0  # 4 hours default
        
        avg_recovery_time = mean(recovery_times)
        self.logger.debug(f"Average recovery time: {avg_recovery_time} hours")
        return avg_recovery_time
    
    def get_performance_classification(self, metrics: Dict[str, float]) -> Dict[str, str]:
        """
        Classify DORA metrics performance according to industry standards.
        
        Args:
            metrics: Dictionary of calculated DORA metrics
            
        Returns:
            Dictionary with performance classifications
        """
        classifications = {}
        
        # Deployment Frequency Classification
        freq = metrics.get('deployment_frequency', 0)
        if freq >= 1:  # Multiple times per day
            classifications['deployment_frequency'] = 'Elite'
        elif freq >= 0.14:  # Once per week
            classifications['deployment_frequency'] = 'High'
        elif freq >= 0.033:  # Once per month
            classifications['deployment_frequency'] = 'Medium'
        else:
            classifications['deployment_frequency'] = 'Low'
        
        # Lead Time Classification
        lead_time = metrics.get('lead_time_for_changes', 0)
        if lead_time <= 24:  # Less than one day
            classifications['lead_time_for_changes'] = 'Elite'
        elif lead_time <= 168:  # Less than one week
            classifications['lead_time_for_changes'] = 'High'
        elif lead_time <= 720:  # Less than one month
            classifications['lead_time_for_changes'] = 'Medium'
        else:
            classifications['lead_time_for_changes'] = 'Low'
        
        # Change Failure Rate Classification
        failure_rate = metrics.get('change_failure_rate', 0)
        if failure_rate <= 15:  # 0-15%
            classifications['change_failure_rate'] = 'Elite'
        elif failure_rate <= 30:  # 16-30%
            classifications['change_failure_rate'] = 'High'
        elif failure_rate <= 45:  # 31-45%
            classifications['change_failure_rate'] = 'Medium'
        else:
            classifications['change_failure_rate'] = 'Low'
        
        # Recovery Time Classification
        recovery_time = metrics.get('time_to_restore_service', 0)
        if recovery_time <= 1:  # Less than one hour
            classifications['time_to_restore_service'] = 'Elite'
        elif recovery_time <= 24:  # Less than one day
            classifications['time_to_restore_service'] = 'High'
        elif recovery_time <= 168:  # Less than one week
            classifications['time_to_restore_service'] = 'Medium'
        else:
            classifications['time_to_restore_service'] = 'Low'
        
        return classifications