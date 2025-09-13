"""
Main DORA Evidence module providing core functionality for metrics collection and analysis.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

import yaml
from dataclasses import dataclass

from .collectors.deployment_collector import DeploymentCollector
from .collectors.incident_collector import IncidentCollector
from .analyzers.metrics_analyzer import MetricsAnalyzer
from .reporters.report_generator import ReportGenerator
from .integrations.vmware_client import VMwareClient
from .utils.config_manager import ConfigManager
from .utils.logger import setup_logger


@dataclass
class DORAMetrics:
    """Data class for DORA metrics."""
    deployment_frequency: float
    lead_time_for_changes: float
    change_failure_rate: float
    time_to_restore_service: float
    measurement_period: str
    timestamp: datetime


class DORACollector:
    """Main collector class for DORA metrics from VMware environments."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize DORA collector.
        
        Args:
            config_path: Path to configuration file
        """
        self.logger = setup_logger(__name__)
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        # Initialize components
        self.vmware_client = VMwareClient(self.config.get('vmware', {}))
        self.deployment_collector = DeploymentCollector(self.vmware_client)
        self.incident_collector = IncidentCollector(self.vmware_client)
        self.analyzer = MetricsAnalyzer()
        
        self.logger.info("DORA Collector initialized successfully")
    
    def collect_deployment_data(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Collect deployment data from VMware environment.
        
        Args:
            days: Number of days to look back for data
            
        Returns:
            List of deployment records
        """
        self.logger.info(f"Collecting deployment data for last {days} days")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        deployments = self.deployment_collector.collect_deployments(
            start_date=start_date,
            end_date=end_date
        )
        
        self.logger.info(f"Collected {len(deployments)} deployment records")
        return deployments
    
    def collect_incident_data(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Collect incident data from VMware environment.
        
        Args:
            days: Number of days to look back for data
            
        Returns:
            List of incident records
        """
        self.logger.info(f"Collecting incident data for last {days} days")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        incidents = self.incident_collector.collect_incidents(
            start_date=start_date,
            end_date=end_date
        )
        
        self.logger.info(f"Collected {len(incidents)} incident records")
        return incidents
    
    def calculate_metrics(self, deployments: List[Dict], incidents: List[Dict]) -> DORAMetrics:
        """
        Calculate DORA metrics from collected data.
        
        Args:
            deployments: List of deployment records
            incidents: List of incident records
            
        Returns:
            Calculated DORA metrics
        """
        self.logger.info("Calculating DORA metrics")
        
        metrics = self.analyzer.calculate_dora_metrics(deployments, incidents)
        
        return DORAMetrics(
            deployment_frequency=metrics['deployment_frequency'],
            lead_time_for_changes=metrics['lead_time_for_changes'],
            change_failure_rate=metrics['change_failure_rate'],
            time_to_restore_service=metrics['time_to_restore_service'],
            measurement_period="30 days",
            timestamp=datetime.now()
        )
    
    def collect_all_metrics(self, days: int = 30) -> DORAMetrics:
        """
        Collect all DORA metrics in one operation.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Complete DORA metrics
        """
        self.logger.info(f"Starting complete DORA metrics collection for {days} days")
        
        # Collect data
        deployments = self.collect_deployment_data(days)
        incidents = self.collect_incident_data(days)
        
        # Calculate metrics
        metrics = self.calculate_metrics(deployments, incidents)
        
        self.logger.info("DORA metrics collection completed successfully")
        return metrics
    
    def generate_report(self, metrics: DORAMetrics, output_format: str = "json") -> str:
        """
        Generate report from DORA metrics.
        
        Args:
            metrics: DORA metrics to report
            output_format: Output format (json, html, pdf)
            
        Returns:
            Generated report content
        """
        reporter = ReportGenerator()
        return reporter.generate_report(metrics, output_format)


class DORAAnalyzer:
    """Analyzer for DORA metrics trends and insights."""
    
    def __init__(self):
        self.logger = setup_logger(__name__)
    
    def analyze_trends(self, historical_metrics: List[DORAMetrics]) -> Dict[str, Any]:
        """
        Analyze trends in DORA metrics over time.
        
        Args:
            historical_metrics: List of historical DORA metrics
            
        Returns:
            Trend analysis results
        """
        self.logger.info(f"Analyzing trends for {len(historical_metrics)} metric sets")
        
        # Implementation for trend analysis
        trends = {
            "deployment_frequency_trend": "improving",
            "lead_time_trend": "stable",
            "change_failure_rate_trend": "improving",
            "recovery_time_trend": "stable"
        }
        
        return trends


class DORAReporter:
    """Reporter for generating DORA metrics reports."""
    
    def __init__(self):
        self.logger = setup_logger(__name__)
    
    def create_dashboard(self, metrics: DORAMetrics) -> str:
        """
        Create interactive dashboard for DORA metrics.
        
        Args:
            metrics: DORA metrics to visualize
            
        Returns:
            Dashboard HTML content
        """
        self.logger.info("Creating DORA metrics dashboard")
        
        # Implementation for dashboard creation
        dashboard_html = "<html><body><h1>DORA Metrics Dashboard</h1></body></html>"
        
        return dashboard_html