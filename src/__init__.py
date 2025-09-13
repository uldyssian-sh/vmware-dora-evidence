"""
VMware DORA Evidence - A comprehensive tool for collecting and analyzing DORA metrics.

This package provides tools for collecting DevOps Research and Assessment (DORA) metrics
from VMware environments, including deployment frequency, lead time for changes,
change failure rate, and time to restore service.
"""

__version__ = "1.0.0"
__author__ = "VMware DORA Evidence Team"
__email__ = "support@example.com"

from .dora_evidence import DORACollector, DORAAnalyzer, DORAReporter

__all__ = ["DORACollector", "DORAAnalyzer", "DORAReporter"]