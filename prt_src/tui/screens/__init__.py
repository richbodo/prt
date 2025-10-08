"""TUI Screens package - Refactored for simplicity (Issue #120)."""

from prt_src.tui.screens.base import BaseScreen
from prt_src.tui.screens.base import EscapeIntent
from prt_src.tui.screens.help import HelpScreen

# Phase 1 screens
from prt_src.tui.screens.home import HomeScreen

__all__ = [
    "BaseScreen",
    "EscapeIntent",
    "HomeScreen",
    "HelpScreen",
]

# Phase 2 screens (to be implemented):
# - chat, search, settings
