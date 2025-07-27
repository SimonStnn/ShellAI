"""
ShellAI - Natural language to safe bash commands.

This package provides tools for converting natural language instructions
into explainable, testable shell scripts, and for querying system information
using natural language.
"""

from .ask import SystemQueryEngine
from .collect_info import SystemInfoCollector

__version__ = "0.1.0"
__all__ = ["SystemInfoCollector", "SystemQueryEngine"]
