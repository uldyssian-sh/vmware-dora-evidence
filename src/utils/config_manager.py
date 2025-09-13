"""
Configuration management utilities.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from .logger import setup_logger


class ConfigManager:
    """Manages application configuration from files and environment variables."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file
        """
        self.logger = setup_logger(__name__)
        self.config_path = config_path or self._find_config_file()
        self.config = self._load_config()
    
    def _find_config_file(self) -> str:
        """
        Find configuration file in standard locations.
        
        Returns:
            Path to configuration file
        """
        possible_paths = [
            'config/config.yaml',
            'config.yaml',
            os.path.expanduser('~/.vmware-dora-evidence/config.yaml'),
            '/etc/vmware-dora-evidence/config.yaml'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.logger.info(f"Found configuration file: {path}")
                return path
        
        # Return default path if none found
        default_path = 'config/config.yaml'
        self.logger.warning(f"No configuration file found, using default: {default_path}")
        return default_path
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file and environment variables.
        
        Returns:
            Configuration dictionary
        """
        config = {}
        
        # Load from file if it exists
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    file_config = yaml.safe_load(f) or {}
                    config.update(file_config)
                    self.logger.info(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                self.logger.error(f"Error loading config file {self.config_path}: {str(e)}")
        else:
            self.logger.warning(f"Configuration file not found: {self.config_path}")
        
        # Override with environment variables
        env_config = self._load_from_environment()
        config.update(env_config)
        
        # Apply default values
        default_config = self._get_default_config()
        for key, value in default_config.items():
            if key not in config:
                config[key] = value
        
        # Validate configuration
        self._validate_config(config)
        
        return config
    
    def _load_from_environment(self) -> Dict[str, Any]:
        """
        Load configuration from environment variables.
        
        Returns:
            Configuration dictionary from environment
        """
        env_config = {}
        
        # VMware configuration
        vmware_config = {}
        if os.getenv('VMWARE_VCENTER_HOST'):
            vmware_config['vcenter_host'] = os.getenv('VMWARE_VCENTER_HOST')
        if os.getenv('VMWARE_USERNAME'):
            vmware_config['username'] = os.getenv('VMWARE_USERNAME')
        if os.getenv('VMWARE_PASSWORD'):
            vmware_config['password'] = os.getenv('VMWARE_PASSWORD')
        if os.getenv('VMWARE_PORT'):
            vmware_config['port'] = int(os.getenv('VMWARE_PORT'))
        if os.getenv('VMWARE_IGNORE_SSL'):
            vmware_config['ignore_ssl_errors'] = os.getenv('VMWARE_IGNORE_SSL').lower() == 'true'
        
        if vmware_config:
            env_config['vmware'] = vmware_config
        
        # Database configuration
        database_config = {}
        if os.getenv('DATABASE_URL'):
            database_config['url'] = os.getenv('DATABASE_URL')
        if os.getenv('DATABASE_TYPE'):
            database_config['type'] = os.getenv('DATABASE_TYPE')
        
        if database_config:
            env_config['database'] = database_config
        
        # Logging configuration
        if os.getenv('LOG_LEVEL'):
            env_config['logging'] = {'level': os.getenv('LOG_LEVEL')}
        
        # Collection configuration
        collection_config = {}
        if os.getenv('COLLECTION_INTERVAL'):
            collection_config['interval_minutes'] = int(os.getenv('COLLECTION_INTERVAL'))
        if os.getenv('COLLECTION_RETENTION_DAYS'):
            collection_config['retention_days'] = int(os.getenv('COLLECTION_RETENTION_DAYS'))
        
        if collection_config:
            env_config['collection'] = collection_config
        
        if env_config:
            self.logger.info("Loaded configuration from environment variables")
        
        return env_config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration values.
        
        Returns:
            Default configuration dictionary
        """
        return {
            'vmware': {
                'port': 443,
                'ignore_ssl_errors': False,
                'timeout_seconds': 30
            },
            'database': {
                'type': 'sqlite',
                'url': 'sqlite:///dora_evidence.db'
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'collection': {
                'interval_minutes': 60,
                'retention_days': 90,
                'max_events_per_collection': 1000
            },
            'reporting': {
                'output_directory': 'reports',
                'include_charts': True,
                'chart_format': 'png'
            }
        }
    
    def _validate_config(self, config: Dict[str, Any]):
        """
        Validate configuration values.
        
        Args:
            config: Configuration dictionary to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate VMware configuration
        vmware_config = config.get('vmware', {})
        required_vmware_fields = ['vcenter_host', 'username', 'password']
        
        for field in required_vmware_fields:
            if not vmware_config.get(field):
                self.logger.warning(f"Missing VMware configuration: {field}")
        
        # Validate port
        port = vmware_config.get('port', 443)
        if not isinstance(port, int) or port < 1 or port > 65535:
            raise ValueError(f"Invalid VMware port: {port}")
        
        # Validate collection interval
        collection_config = config.get('collection', {})
        interval = collection_config.get('interval_minutes', 60)
        if not isinstance(interval, int) or interval < 1:
            raise ValueError(f"Invalid collection interval: {interval}")
        
        # Validate retention days
        retention = collection_config.get('retention_days', 90)
        if not isinstance(retention, int) or retention < 1:
            raise ValueError(f"Invalid retention days: {retention}")
        
        self.logger.info("Configuration validation completed")
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get complete configuration.
        
        Returns:
            Configuration dictionary
        """
        return self.config.copy()
    
    def get_vmware_config(self) -> Dict[str, Any]:
        """
        Get VMware-specific configuration.
        
        Returns:
            VMware configuration dictionary
        """
        return self.config.get('vmware', {})
    
    def get_database_config(self) -> Dict[str, Any]:
        """
        Get database configuration.
        
        Returns:
            Database configuration dictionary
        """
        return self.config.get('database', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get logging configuration.
        
        Returns:
            Logging configuration dictionary
        """
        return self.config.get('logging', {})
    
    def get_collection_config(self) -> Dict[str, Any]:
        """
        Get collection configuration.
        
        Returns:
            Collection configuration dictionary
        """
        return self.config.get('collection', {})
    
    def update_config(self, updates: Dict[str, Any]):
        """
        Update configuration with new values.
        
        Args:
            updates: Dictionary of configuration updates
        """
        self._deep_update(self.config, updates)
        self._validate_config(self.config)
        self.logger.info("Configuration updated")
    
    def _deep_update(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]):
        """
        Deep update dictionary with another dictionary.
        
        Args:
            base_dict: Base dictionary to update
            update_dict: Dictionary with updates
        """
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def save_config(self, output_path: Optional[str] = None):
        """
        Save current configuration to file.
        
        Args:
            output_path: Output file path (defaults to current config path)
        """
        output_path = output_path or self.config_path
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Remove sensitive information before saving
            safe_config = self._sanitize_config(self.config)
            
            with open(output_path, 'w') as f:
                yaml.dump(safe_config, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Configuration saved to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {str(e)}")
            raise
    
    def _sanitize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove sensitive information from configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Sanitized configuration dictionary
        """
        safe_config = config.copy()
        
        # Remove sensitive VMware credentials
        if 'vmware' in safe_config:
            vmware_config = safe_config['vmware'].copy()
            if 'password' in vmware_config:
                vmware_config['password'] = '<REDACTED>'
            safe_config['vmware'] = vmware_config
        
        # Remove database passwords
        if 'database' in safe_config:
            database_config = safe_config['database'].copy()
            if 'url' in database_config and 'password' in database_config['url']:
                # This is a simple approach - in production, use proper URL parsing
                database_config['url'] = '<REDACTED>'
            safe_config['database'] = database_config
        
        return safe_config