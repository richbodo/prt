"""TUI widgets for the PRT application - Refactored (Issue #120)."""

# Base widgets
from .base import ModeAwareWidget
from .bottomnav import BottomNav
from .dropdown import DropdownMenu

# Existing widgets that may be useful
from .progress_indicator import ChatProgressIndicator

# New simplified navigation widgets
from .topnav import TopNav

__all__ = [
    # Base
    "ModeAwareWidget",
    # Navigation
    "TopNav",
    "BottomNav",
    "DropdownMenu",
    # Utility
    "ChatProgressIndicator",
]

# Old widgets kept for reference during refactoring:
# - contact_detail, contact_list, navigation_menu, relationship, search_filter, settings
# These will be evaluated and potentially reimplemented as needed
