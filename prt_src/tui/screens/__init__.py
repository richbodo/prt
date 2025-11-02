"""TUI Screens package - Refactored for simplicity (Issue #120)."""

from prt_src.tui.screens.base import BaseScreen
from prt_src.tui.screens.base import EscapeIntent

# Phase 2 screens
from prt_src.tui.screens.chat import ChatScreen

# Phase 1 screens
from prt_src.tui.screens.help import HelpScreen
from prt_src.tui.screens.home import HomeScreen
from prt_src.tui.screens.search import SearchScreen
from prt_src.tui.screens.settings import SettingsScreen
from prt_src.tui.screens.setup import SetupScreen

__all__ = [
    "BaseScreen",
    "ChatScreen",
    "EscapeIntent",
    "HelpScreen",
    "HomeScreen",
    "SearchScreen",
    "SettingsScreen",
    "SetupScreen",
]
