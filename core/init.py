"""
Core Module
Orchestratore principale e componenti centrali
"""

from .engine import CopilotEngine
from .scheduler import MonitorScheduler
from .dependency_injection import Container

__all__ = ['CopilotEngine', 'MonitorScheduler', 'Container']