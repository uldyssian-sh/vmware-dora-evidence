"""
Logging utilities for the application.
"""

import logging
import sys
from typing import Optional
import structlog


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Set up structured logger for the application.
    
    Args:
        name: Logger name (typically __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Get logger
    logger = structlog.get_logger(name)
    
    # Set log level
    if level:
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        logging.getLogger(name).setLevel(numeric_level)
    
    return logger


def configure_root_logger(level: str = "INFO", format_string: Optional[str] = None):
    """
    Configure the root logger for the application.
    
    Args:
        level: Log level
        format_string: Custom format string
    """
    # Default format
    if not format_string:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=format_string,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("pyVmomi").setLevel(logging.WARNING)