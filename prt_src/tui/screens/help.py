"""Help screen - Simple help message placeholder."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static

from prt_src.logging_config import get_logger
from prt_src.tui.screens.base import BaseScreen
from prt_src.tui.widgets import BottomNav
from prt_src.tui.widgets import TopNav

logger = get_logger(__name__)


class HelpScreen(BaseScreen):
    """Help screen with placeholder message.

    Per spec:
    - Top Nav
    - Single line: "Help not implemented yet."
    - Bottom Nav
    """

    def __init__(self, **kwargs):
        """Initialize Help screen."""
        super().__init__(**kwargs)
        self.screen_title = "HELP"

    def compose(self) -> ComposeResult:
        """Compose the help screen layout."""
        # Top navigation bar
        self.top_nav = TopNav(self.screen_title, id="top-nav")
        yield self.top_nav

        # Main content container
        with Container(id="help-content"):
            yield Static("Help not implemented yet.", id="help-message")

        # Bottom navigation/status bar
        self.bottom_nav = BottomNav(id="bottom-nav")
        yield self.bottom_nav

    async def on_mount(self) -> None:
        """Handle screen mount."""
        await super().on_mount()
        logger.info("Help screen mounted")
