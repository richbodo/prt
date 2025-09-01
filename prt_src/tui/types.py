"""Common types for the TUI application."""

from enum import Enum


class AppMode(Enum):
    """Application mode enumeration."""

    NAVIGATION = "NAV"
    EDIT = "EDIT"
