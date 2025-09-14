"""
Command-line interface for VMware DORA Evidence.
"""

import click
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .dora_evidence import DORACollector
from .utils.config_manager import ConfigManager
from .utils.logger import setup_logger, configure_root_logger


@click.group()
@click.option('--config', '-c', help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--quiet', '-q', is_flag=True, help='Suppress output')
@click.pass_context
def cli(ctx, config: Optional[str], verbose: bool, quiet: bool):
    """VMware DORA Evidence - Collect and analyze DORA metrics from VMware environments."""
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Configure logging
    if verbose:
        log_level = "DEBUG"
    elif quiet:
        log_level = "ERROR"
    else:
        log_level = "INFO"
    
    configure_root_logger(level=log_level)
    
    # Store configuration path
    ctx.obj['config_path'] = config
    ctx.obj['verbose'] = verbose
    ctx.obj['quiet'] = quiet


@cli.command()
@click.option('--days', '-d', default=30, help='Number of days to collect data for')
@click.option('--output', '-o', help='Output file path')
@click.option('--format', 'output_format', default='json', 
              type=click.Choice(['json', 'csv', 'yaml']),
              help='Output format')
@click.pass_context
def collect(ctx, days: int, output: Optional[str], output_format: str):
    """Collect DORA metrics data from VMware environment."""
    try:
        collector = DORACollector(config_path=ctx.obj.get('config_path'))
        
        if not ctx.obj.get('quiet'):
            click.echo(f"Collecting DORA metrics for the last {days} days...")
        
        # Collect metrics
        metrics = collector.collect_all_metrics(days=days)
        
        # Output results
        if output:
            # Validate and sanitize output path
            output_path = _safe_path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if output_format == 'json':
                import json
                with open(output_path, 'w') as f:
                    json.dump(metrics.__dict__, f, indent=2, default=str)
            elif output_format == 'yaml':
                import yaml
                with open(output_path, 'w') as f:
                    yaml.dump(metrics.__dict__, f, default_flow_style=False)
            elif output_format == 'csv':
                import pandas as pd
                df = pd.DataFrame([metrics.__dict__])
                df.to_csv(output_path, index=False)
            
            if not ctx.obj.get('quiet'):
                click.echo(f"Results saved to {output_path}")
        else:
            # Print to stdout
            if output_format == 'json':
                import json
                click.echo(json.dumps(metrics.__dict__, indent=2, default=str))
            else:
                click.echo(f"Deployment Frequency: {metrics.deployment_frequency}")
                click.echo(f"Lead Time for Changes: {metrics.lead_time_for_changes}")
                click.echo(f"Change Failure Rate: {metrics.change_failure_rate}")
                click.echo(f"Time to Restore Service: {metrics.time_to_restore_service}")
        
    except Exception as e:
        click.echo(f"Error collecting metrics: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--days', '-d', default=30, help='Number of days to include in report')
@click.option('--output', '-o', help='Output directory for reports')
@click.option('--format', 'output_format', default='html',
              type=click.Choice(['html', 'pdf', 'json']),
              help='Report format')
@click.option('--template', help='Custom report template')
@click.pass_context
def report(ctx, days: int, output: Optional[str], output_format: str, template: Optional[str]):
    """Generate DORA metrics report."""
    try:
        collector = DORACollector(config_path=ctx.obj.get('config_path'))
        
        if not ctx.obj.get('quiet'):
            click.echo(f"Generating {output_format.upper()} report for the last {days} days...")
        
        # Collect metrics
        metrics = collector.collect_all_metrics(days=days)
        
        # Generate report
        report_content = collector.generate_report(metrics, output_format)
        
        # Save report
        if output:
            output_dir = _safe_path(output)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dora_report_{timestamp}.{output_format}"
            report_path = output_dir / filename
            
            with open(report_path, 'w') as f:
                f.write(report_content)
            
            if not ctx.obj.get('quiet'):
                click.echo(f"Report saved to {report_path}")
        else:
            click.echo(report_content)
        
    except Exception as e:
        click.echo(f"Error generating report: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--interval', '-i', default=3600, help='Collection interval in seconds')
@click.option('--daemon', '-d', is_flag=True, help='Run as daemon')
@click.pass_context
def daemon(ctx, interval: int, daemon: bool):
    """Run continuous data collection daemon."""
    import time
    import signal
    import threading
    
    collector = DORACollector(config_path=ctx.obj.get('config_path'))
    logger = setup_logger(__name__)
    
    # Daemon control
    running = threading.Event()
    running.set()
    
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal")
        running.clear()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    def collect_metrics():
        """Collect metrics periodically."""
        while running.is_set():
            try:
                logger.info("Starting metrics collection cycle")
                metrics = collector.collect_all_metrics(days=1)
                logger.info(f"Collection completed: {metrics}")
                
                # Wait for next interval
                running.wait(timeout=interval)
                
            except Exception as e:
                logger.error(f"Error in collection cycle: {str(e)}")
                running.wait(timeout=60)  # Wait 1 minute before retry
    
    if not ctx.obj.get('quiet'):
        click.echo(f"Starting DORA Evidence daemon (interval: {interval}s)")
    
    logger.info(f"Starting daemon with {interval}s interval")
    
    # Start collection thread
    collection_thread = threading.Thread(target=collect_metrics)
    collection_thread.daemon = True
    collection_thread.start()
    
    try:
        # Keep main thread alive
        while running.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Shutting down daemon")
        running.clear()
        collection_thread.join(timeout=10)


@cli.command()
@click.pass_context
def health_check(ctx):
    """Perform health check of the system."""
    try:
        collector = DORACollector(config_path=ctx.obj.get('config_path'))
        
        click.echo("Performing health check...")
        
        # Test VMware connection
        click.echo("Testing VMware connection...", nl=False)
        if collector.vmware_client.test_connection():
            click.echo(" ✓ OK")
        else:
            click.echo(" ✗ FAILED")
            sys.exit(1)
        
        # Test configuration
        click.echo("Checking configuration...", nl=False)
        config = collector.config_manager.get_config()
        if config:
            click.echo(" ✓ OK")
        else:
            click.echo(" ✗ FAILED")
            sys.exit(1)
        
        # Test data collection
        click.echo("Testing data collection...", nl=False)
        try:
            deployments = collector.collect_deployment_data(days=1)
            incidents = collector.collect_incident_data(days=1)
            click.echo(" ✓ OK")
        except Exception as e:
            click.echo(f" ✗ FAILED: {str(e)}")
            sys.exit(1)
        
        click.echo("\nHealth check completed successfully!")
        
    except Exception as e:
        click.echo(f"Health check failed: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=8000, help='Port to bind to')
@click.option('--reload', is_flag=True, help='Enable auto-reload for development')
@click.pass_context
def serve(ctx, host: str, port: int, reload: bool):
    """Start the web API server."""
    try:
        import uvicorn
        from .api.main import app
        
        if not ctx.obj.get('quiet'):
            click.echo(f"Starting web server on {host}:{port}")
        
        uvicorn.run(
            "src.api.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info" if ctx.obj.get('verbose') else "warning"
        )
        
    except ImportError:
        click.echo("Web server dependencies not installed. Install with: pip install 'vmware-dora-evidence[web]'", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error starting web server: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--config-only', is_flag=True, help='Validate configuration only')
@click.pass_context
def validate(ctx, config_only: bool):
    """Validate configuration and setup."""
    try:
        click.echo("Validating configuration...")
        
        config_manager = ConfigManager(config_path=ctx.obj.get('config_path'))
        config = config_manager.get_config()
        
        # Validate VMware configuration
        vmware_config = config.get('vmware', {})
        required_fields = ['vcenter_host', 'username', 'password']
        
        for field in required_fields:
            if not vmware_config.get(field):
                click.echo(f"✗ Missing required VMware configuration: {field}", err=True)
                sys.exit(1)
        
        click.echo("✓ Configuration validation passed")
        
        if not config_only:
            # Test connections
            click.echo("Testing connections...")
            
            collector = DORACollector(config_path=ctx.obj.get('config_path'))
            
            if collector.vmware_client.test_connection():
                click.echo("✓ VMware connection successful")
            else:
                click.echo("✗ VMware connection failed", err=True)
                sys.exit(1)
        
        click.echo("Validation completed successfully!")
        
    except Exception as e:
        click.echo(f"Validation failed: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--output', '-o', help='Output file path')
@click.pass_context
def config_template(ctx, output: Optional[str]):
    """Generate configuration template."""
    template_content = """# VMware DORA Evidence Configuration Template
# Copy this file to config.yaml and update with your environment details

vmware:
  vcenter_host: "your-vcenter-host.example.com"
  username: "your-username"
  password: "your-password"  # Use environment variables in production
  port: 443
  ignore_ssl_errors: false

database:
  type: "sqlite"
  url: "sqlite:///dora_evidence.db"

collection:
  interval_minutes: 60
  retention_days: 90
  max_events_per_collection: 1000

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

reporting:
  output_directory: "reports"
  include_charts: true
  chart_format: "png"
"""
    
    if output:
        output_path = _safe_path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(template_content)
        
        click.echo(f"Configuration template saved to {output_path}")
    else:
        click.echo(template_content)


@cli.command()
@click.pass_context
def version(ctx):
    """Show version information."""
    from . import __version__
    
    click.echo(f"VMware DORA Evidence v{__version__}")
    click.echo("A comprehensive tool for collecting and analyzing DORA metrics from VMware environments")


def _safe_path(user_path: str) -> Path:
    """Safely resolve user-provided path to prevent path traversal."""
    # Convert to Path object
    path = Path(user_path)
    
    # Resolve to absolute path
    resolved_path = path.resolve()
    
    # Get current working directory
    cwd = Path.cwd().resolve()
    
    # Check if the resolved path is within current directory or its subdirectories
    try:
        resolved_path.relative_to(cwd)
    except ValueError:
        # Path is outside current directory, restrict to current directory
        safe_name = os.path.basename(user_path)
        # Remove any remaining path separators
        safe_name = safe_name.replace('/', '_').replace('\\', '_')
        resolved_path = cwd / safe_name
    
    return resolved_path


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()