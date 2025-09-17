"""Custom Progress Indicator Widget for PRT TUI.

Provides animated progress indication with fun messages and spinning ASCII symbols,
inspired by Claude Code's progress display.
"""

import random

from textual.app import ComposeResult
from textual.widgets import Static

from prt_src.logging_config import get_logger

logger = get_logger(__name__)


class ChatProgressIndicator(Static):
    """Animated progress indicator with fun messages and ASCII spinner."""

    # Fun progress messages inspired by Claude Code
    PROGRESS_MESSAGES = [
        "🤔 Pondering your request...",
        "🧠 Consulting the knowledge base...",
        "💭 Formulating response...",
        "🔍 Searching through contacts...",
        "📝 Crafting the perfect reply...",
        "🎯 Targeting relevant information...",
        "⚡ Processing at light speed...",
        "🔮 Divining insights...",
        "🎨 Painting with words...",
        "🚀 Launching query rockets...",
        "🔬 Analyzing data patterns...",
        "🎪 Juggling information...",
        "🌟 Sprinkling AI magic...",
        "🎭 Rehearsing the response...",
        "🏗️ Constructing answer architecture...",
        "🎵 Composing data symphony...",
        "🔄 Spinning up the neurons...",
        "⚙️ Calibrating response engines...",
    ]

    # ASCII spinner characters
    SPINNER_CHARS = ["/", "-", "\\", "|"]

    def __init__(self, classes: str = "chat-progress", **kwargs):
        """Initialize progress indicator.

        Args:
            classes: CSS classes for styling
            **kwargs: Additional widget arguments
        """
        super().__init__(classes=classes, **kwargs)
        self.message_label = None
        self.spinner_label = None
        self._spinner_timer = None
        self._message_timer = None
        self._spinner_index = 0
        self._message_index = 0
        self._is_animating = False

    def compose(self) -> ComposeResult:
        """Compose the progress indicator layout."""
        # Don't update content here - do it after mounting
        return super().compose()

    async def on_mount(self) -> None:
        """Called when widget is mounted - safe to update content here."""
        # Now it's safe to update content
        initial_content = f"{self.SPINNER_CHARS[0]} {self.PROGRESS_MESSAGES[0]}"
        self.update(initial_content)
        logger.info(f"🔥 PROGRESS WIDGET: Mounted and updated content to: {initial_content}")

    async def start_animation(self) -> None:
        """Start the progress animation."""
        logger.info("start_animation called - using Static widget update")
        if self._is_animating:
            logger.info("Already animating, returning early")
            return

        logger.info("Setting _is_animating=True and display=True")
        self._is_animating = True
        self.display = True

        # Update the Static widget content directly
        message = random.choice(self.PROGRESS_MESSAGES)
        spinner = random.choice(self.SPINNER_CHARS)
        content = f"{spinner} {message}"

        logger.info(f"Updating Static widget content to: {content}")
        self.update(content)

        # Start animation timer if possible
        try:
            if hasattr(self, "set_interval") and callable(self.set_interval):
                self._spinner_timer = self.set_interval(0.5, self._update_content)
                logger.info("Started animation timer")
            else:
                logger.warning("set_interval not available - showing static content")
        except Exception as e:
            logger.error(f"Failed to start animation timer: {e}")
            logger.info("Showing static progress indicator")

    async def stop_animation(self) -> None:
        """Stop the progress animation."""
        self._is_animating = False
        self.display = False

        # Stop timer
        if self._spinner_timer:
            self._spinner_timer.stop()
            self._spinner_timer = None

        logger.debug("Stopped progress animation")

    def _update_content(self) -> None:
        """Update the progress content with new spinner and message."""
        if not self._is_animating:
            return

        # Rotate spinner
        self._spinner_index = (self._spinner_index + 1) % len(self.SPINNER_CHARS)

        # Occasionally change message
        if self._spinner_index == 0:  # Change message when spinner completes a cycle
            self._message_index = (self._message_index + 1) % len(self.PROGRESS_MESSAGES)

        # Update Static widget content
        spinner = self.SPINNER_CHARS[self._spinner_index]
        message = self.PROGRESS_MESSAGES[self._message_index]
        content = f"{spinner} {message}"
        self.update(content)

    def set_message(self, message: str) -> None:
        """Set a custom progress message.

        Args:
            message: Custom message to display
        """
        spinner = self.SPINNER_CHARS[self._spinner_index]
        content = f"{spinner} {message}"
        self.update(content)

    def set_random_message(self) -> None:
        """Set a random progress message."""
        message = random.choice(self.PROGRESS_MESSAGES)
        self.set_message(message)
