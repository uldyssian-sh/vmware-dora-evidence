"""
Report generator for DORA metrics.
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from ..utils.logger import setup_logger


class ReportGenerator:
    """Generator for DORA metrics reports in various formats."""
    
    def __init__(self):
        """Initialize the report generator."""
        self.logger = setup_logger(__name__)
    
    def generate_report(self, metrics: Any, output_format: str = "json") -> str:
        """
        Generate report from DORA metrics.
        
        Args:
            metrics: DORA metrics object or dictionary
            output_format: Output format (json, html, csv)
            
        Returns:
            Generated report content as string
        """
        self.logger.info(f"Generating {output_format.upper()} report")
        
        # Convert metrics object to dictionary if needed
        if hasattr(metrics, '__dict__'):
            metrics_dict = metrics.__dict__
        else:
            metrics_dict = metrics
        
        if output_format.lower() == 'json':
            return self._generate_json_report(metrics_dict)
        elif output_format.lower() == 'html':
            return self._generate_html_report(metrics_dict)
        elif output_format.lower() == 'csv':
            return self._generate_csv_report(metrics_dict)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _generate_json_report(self, metrics: Dict[str, Any]) -> str:
        """
        Generate JSON report.
        
        Args:
            metrics: Metrics dictionary
            
        Returns:
            JSON report string
        """
        # Ensure datetime objects are serializable
        serializable_metrics = self._make_serializable(metrics)
        
        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "report_type": "DORA Metrics Report",
                "version": "1.0"
            },
            "metrics": serializable_metrics
        }
        
        return json.dumps(report, indent=2, default=str)
    
    def _generate_html_report(self, metrics: Dict[str, Any]) -> str:
        """
        Generate HTML report.
        
        Args:
            metrics: Metrics dictionary
            
        Returns:
            HTML report string
        """
        # Get performance classifications if analyzer is available
        try:
            from ..analyzers.metrics_analyzer import MetricsAnalyzer
            analyzer = MetricsAnalyzer()
            classifications = analyzer.get_performance_classification(metrics)
        except Exception:
            classifications = {}
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DORA Metrics Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            padding: 30px;
        }}
        .metric-card {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 25px;
            border-left: 5px solid #667eea;
            transition: transform 0.2s ease;
        }}
        .metric-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }}
        .metric-title {{
            font-size: 1.1em;
            font-weight: 600;
            color: #333;
            margin-bottom: 10px;
        }}
        .metric-value {{
            font-size: 2.2em;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 5px;
        }}
        .metric-unit {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
        }}
        .performance-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .elite {{ background: #d4edda; color: #155724; }}
        .high {{ background: #cce5ff; color: #004085; }}
        .medium {{ background: #fff3cd; color: #856404; }}
        .low {{ background: #f8d7da; color: #721c24; }}
        .footer {{
            background: #f8f9fa;
            padding: 20px 30px;
            border-top: 1px solid #dee2e6;
            text-align: center;
            color: #666;
        }}
        .summary {{
            background: #e9ecef;
            padding: 20px 30px;
            border-bottom: 1px solid #dee2e6;
        }}
        .summary h2 {{
            margin-top: 0;
            color: #333;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>DORA Metrics Report</h1>
            <p>DevOps Research and Assessment - Key Performance Indicators</p>
            <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
        
        <div class="summary">
            <h2>Executive Summary</h2>
            <p>This report presents the four key DORA metrics that measure software delivery performance and operational efficiency. These metrics help organizations understand their DevOps maturity and identify areas for improvement.</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-title">Deployment Frequency</div>
                <div class="metric-value">{metrics.get('deployment_frequency', 0):.2f}</div>
                <div class="metric-unit">deployments per day</div>
                <span class="performance-badge {classifications.get('deployment_frequency', 'low').lower()}">
                    {classifications.get('deployment_frequency', 'Unknown')}
                </span>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">Lead Time for Changes</div>
                <div class="metric-value">{metrics.get('lead_time_for_changes', 0):.1f}</div>
                <div class="metric-unit">hours</div>
                <span class="performance-badge {classifications.get('lead_time_for_changes', 'low').lower()}">
                    {classifications.get('lead_time_for_changes', 'Unknown')}
                </span>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">Change Failure Rate</div>
                <div class="metric-value">{metrics.get('change_failure_rate', 0):.1f}%</div>
                <div class="metric-unit">percentage of deployments</div>
                <span class="performance-badge {classifications.get('change_failure_rate', 'low').lower()}">
                    {classifications.get('change_failure_rate', 'Unknown')}
                </span>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">Time to Restore Service</div>
                <div class="metric-value">{metrics.get('time_to_restore_service', 0):.1f}</div>
                <div class="metric-unit">hours</div>
                <span class="performance-badge {classifications.get('time_to_restore_service', 'low').lower()}">
                    {classifications.get('time_to_restore_service', 'Unknown')}
                </span>
            </div>
        </div>
        
        <div class="footer">
            <p>Report generated by VMware DORA Evidence Collector</p>
            <p>For more information about DORA metrics, visit <a href="https://dora.dev">dora.dev</a></p>
        </div>
    </div>
</body>
</html>
        """
        
        return html_content.strip()
    
    def _generate_csv_report(self, metrics: Dict[str, Any]) -> str:
        """
        Generate CSV report.
        
        Args:
            metrics: Metrics dictionary
            
        Returns:
            CSV report string
        """
        csv_lines = [
            "Metric,Value,Unit,Timestamp"
        ]
        
        timestamp = datetime.now().isoformat()
        
        # Add each metric as a row
        csv_lines.append(f"Deployment Frequency,{metrics.get('deployment_frequency', 0):.2f},deployments/day,{timestamp}")
        csv_lines.append(f"Lead Time for Changes,{metrics.get('lead_time_for_changes', 0):.1f},hours,{timestamp}")
        csv_lines.append(f"Change Failure Rate,{metrics.get('change_failure_rate', 0):.1f},percentage,{timestamp}")
        csv_lines.append(f"Time to Restore Service,{metrics.get('time_to_restore_service', 0):.1f},hours,{timestamp}")
        
        return "\\n".join(csv_lines)
    
    def _make_serializable(self, obj: Any) -> Any:
        """
        Make object JSON serializable by converting datetime objects to strings.
        
        Args:
            obj: Object to make serializable
            
        Returns:
            Serializable object
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: self._make_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        else:
            return obj
    
    def save_report(self, content: str, file_path: str) -> None:
        """
        Save report content to file.
        
        Args:
            content: Report content
            file_path: Output file path
        """
        try:
            output_path = Path(file_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"Report saved to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving report: {str(e)}")
            raise