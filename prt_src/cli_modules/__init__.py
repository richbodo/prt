"""
PRT CLI Package

Modular CLI architecture for Personal Relationship Toolkit.
This package contains the command-line interface components organized by concern.
"""

from .help import CLI_OPTIONS
from .help import load_help_text

__all__ = ["CLI_OPTIONS", "load_help_text"]
