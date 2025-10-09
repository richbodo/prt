"""Chat screen - LLM interaction interface."""

from textual import events
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static
from textual.widgets import TextArea

from prt_src.logging_config import get_logger
from prt_src.tui.constants import WidgetIDs
from prt_src.tui.screens.base import BaseScreen
from prt_src.tui.widgets import BottomNav
from prt_src.tui.widgets import DropdownMenu
from prt_src.tui.widgets import TopNav

logger = get_logger(__name__)


class ChatTextArea(TextArea):
    """Custom TextArea that intercepts Enter key to submit instead of inserting newline.

    Note: In terminals, Shift+Enter often cannot be distinguished from Enter.
    We detect this by checking the key string.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parent_screen = None

    async def _on_key(self, event: events.Key) -> None:
        """Override key handler to intercept Enter for submission."""
        key = event.key

        # Check if this is a plain Enter (not Shift+Enter, not Ctrl+Enter, etc.)
        # In terminals, shift modifiers are often encoded in the key string
        if key == "enter" and self._parent_screen:
            # Plain Enter = submit message
            logger.info("[ChatTextArea] Plain ENTER detected - submitting")
            handled = await self._parent_screen._handle_textarea_submit()
            if handled:
                event.prevent_default()
                event.stop()
                return

        # All other keys (including shift+enter if terminal supports it) - let TextArea handle
        await super()._on_key(event)


def get_llm_status_stub() -> dict:
    """Stub function - returns test LLM status.

    TODO Phase 2B: Replace with real LLMStatusService integration.

    Returns:
        Dict with LLM status information
    """
    return {"status": "online", "model": "test-model", "ready": True}


async def send_to_llm_stub(message: str) -> str:
    """Stub function - returns test LLM response.

    TODO Phase 2B: Replace with real Ollama integration.

    Args:
        message: User message

    Returns:
        LLM response string
    """
    return f"Echo (stub): {message}"


class ChatScreen(BaseScreen):
    """Chat screen with LLM interaction.

    Per spec:
    - Top Nav
    - Chat Status Line (LLM status + progress indicator)
    - Chat input box (multi-line, scrollable)
    - Response display area (scrollable, 64KB limit)
    - Bottom Nav
    """

    # Response buffer limit (64KB)
    MAX_RESPONSE_SIZE = 64 * 1024

    def __init__(self, **kwargs):
        """Initialize Chat screen."""
        super().__init__(**kwargs)
        self.screen_title = "CHAT"
        self.response_buffer = ""
        self._processing_enter = False  # Flag to prevent double-processing

    def compose(self) -> ComposeResult:
        """Compose the chat screen layout."""
        # Top navigation bar
        self.top_nav = TopNav(self.screen_title, id=WidgetIDs.TOP_NAV)
        yield self.top_nav

        # Main content container
        with Container(id=WidgetIDs.CHAT_CONTENT):
            # Chat status line
            status = get_llm_status_stub()
            status_icon = "✅" if status["ready"] else "⏳"
            status_text = f"{status_icon} LLM: {status['status'].upper()} │ READY"
            self.chat_status = Static(status_text, id=WidgetIDs.CHAT_STATUS)
            yield self.chat_status

            # Chat input box - using custom TextArea subclass
            self.chat_input = ChatTextArea(
                id=WidgetIDs.CHAT_INPUT,
                placeholder="Enter your prompt here...",
            )
            self.chat_input.styles.height = 5
            self.chat_input._parent_screen = self  # Link to parent for ENTER handling
            yield self.chat_input

            # Response display area
            self.chat_response = Static(
                "LLM responses will appear here.\n\nPress ENTER (in Edit mode) to send your message.",
                id=WidgetIDs.CHAT_RESPONSE,
            )
            yield self.chat_response

        # Dropdown menu (hidden by default)
        self.dropdown = DropdownMenu(
            [
                ("H", "Home", self.action_go_home),
                ("B", "Back", self.action_go_back),
            ],
            id=WidgetIDs.DROPDOWN_MENU,
        )
        self.dropdown.display = False
        yield self.dropdown

        # Bottom navigation/status bar
        self.bottom_nav = BottomNav(id=WidgetIDs.BOTTOM_NAV)
        yield self.bottom_nav

    async def on_mount(self) -> None:
        """Handle screen mount."""
        await super().on_mount()
        logger.info("Chat screen mounted")

        # Start in EDIT mode since chat input is the primary purpose
        from prt_src.tui.types import AppMode

        self.app.current_mode = AppMode.EDIT
        self.top_nav.set_mode(AppMode.EDIT)
        # Focus the chat input box
        self.chat_input.focus()
        logger.debug("Chat screen: Set mode to EDIT on mount and focused input")

    async def _handle_textarea_submit(self) -> bool:
        """Handle Enter key from ChatTextArea for submission.

        Returns:
            True if handled and message sent
        """
        from prt_src.tui.types import AppMode

        # Only process if in EDIT mode
        if self.app.current_mode != AppMode.EDIT:
            return False

        if self._processing_enter:
            return False

        self._processing_enter = True

        # Send the message
        logger.info("[CHAT] ENTER pressed - calling action_send_message")
        await self.action_send_message()
        self._processing_enter = False
        return True

    def on_key(self, event) -> None:
        """Handle key presses.

        Args:
            event: Key event
        """
        from prt_src.tui.types import AppMode

        key = event.key.lower()

        # When ESC is pressed, it will toggle mode via app-level binding
        # After mode changes to EDIT, we want to focus the input
        if key == "escape":
            # Schedule focus after the mode toggle completes
            self.call_after_refresh(self._refocus_if_edit_mode)

        # In NAV mode, handle keys
        if self.app.current_mode == AppMode.NAVIGATION:
            if key == "n":
                self.action_toggle_menu()
                event.prevent_default()
            elif self.dropdown.display:
                # When menu is open, check for menu actions
                action = self.dropdown.get_action(key)
                if action:
                    action()
                    event.prevent_default()

    async def action_send_message(self) -> None:
        """Send message to LLM and display response."""
        message = self.chat_input.text.strip()

        if not message:
            self.bottom_nav.show_status("Please enter a message")
            return

        logger.info(f"Sending message to LLM: {message[:50]}...")

        # Show processing status
        self.chat_status.update("⏳ LLM: PROCESSING │ Waiting for response...")
        self.bottom_nav.show_status("Sending message to LLM...")

        try:
            # Get stub response
            response = await send_to_llm_stub(message)

            # Add to response buffer
            self._add_to_response_buffer(f"\n> You: {message}\n\n{response}\n")

            # Update display
            self.chat_response.update(self.response_buffer)

            # Reset status
            status_icon = "✅"
            self.chat_status.update(f"{status_icon} LLM: ONLINE │ READY")
            self.bottom_nav.show_status("Message sent successfully (stub response)")

            # Clear input
            self.chat_input.clear()

            logger.info("LLM response received and displayed")

        except Exception as e:
            logger.error(f"Error sending message to LLM: {e}", exc_info=True)
            self.chat_status.update("❌ LLM: ERROR │ Failed to get response")
            self.bottom_nav.show_status(f"Error: {e}")

    def _add_to_response_buffer(self, text: str) -> None:
        """Add text to response buffer with 64KB limit.

        Args:
            text: Text to add to buffer
        """
        self.response_buffer += text

        # Enforce 64KB limit
        if len(self.response_buffer) > self.MAX_RESPONSE_SIZE:
            # Keep most recent content
            overflow = len(self.response_buffer) - self.MAX_RESPONSE_SIZE
            self.response_buffer = (
                "[... earlier messages truncated ...]\n" + self.response_buffer[overflow:]
            )
            logger.debug(f"Response buffer truncated, removed {overflow} bytes")

    def on_mode_changed(self, mode) -> None:
        """Handle mode changes - focus input when entering EDIT mode.

        Args:
            mode: The new AppMode
        """
        from prt_src.tui.types import AppMode

        super().on_mode_changed(mode)

        if mode == AppMode.EDIT:
            # Close dropdown menu if open
            if self.dropdown.display:
                self.dropdown.hide()
                self.top_nav.menu_open = False
                self.top_nav.refresh_display()
                logger.debug("[CHAT] Closed dropdown menu when switching to EDIT mode")

            # Focus the input box
            self.chat_input.focus()
            logger.info("[CHAT] Focused chat input after mode change to EDIT")

    def _refocus_if_edit_mode(self) -> None:
        """Refocus input box if we're in EDIT mode (called after ESC key).

        Also closes dropdown menu if open, as per UX pattern:
        dropdown open + ESC = close menu and enter first edit box.
        """
        from prt_src.tui.types import AppMode

        if self.app.current_mode == AppMode.EDIT:
            # Close dropdown menu if open
            if self.dropdown.display:
                self.dropdown.hide()
                self.top_nav.menu_open = False
                self.top_nav.refresh_display()
                logger.debug("Closed dropdown menu when switching to EDIT mode")

            # Focus the input box
            self.chat_input.focus()
            logger.debug("Refocused chat input after mode toggle to EDIT")

    def action_toggle_menu(self) -> None:
        """Toggle dropdown menu visibility."""
        if self.dropdown.display:
            self.dropdown.hide()
            self.top_nav.menu_open = False
        else:
            self.dropdown.show()
            self.top_nav.menu_open = True
        self.top_nav.refresh_display()

    def action_go_home(self) -> None:
        """Navigate to home screen."""
        self.dropdown.hide()
        self.top_nav.menu_open = False
        self.top_nav.refresh_display()
        logger.info("Navigating to home from chat screen")
        self.app.navigate_to("home")

    def action_go_back(self) -> None:
        """Go back to previous screen."""
        self.dropdown.hide()
        self.top_nav.menu_open = False
        self.top_nav.refresh_display()
        logger.info("Going back from chat screen")
        self.app.pop_screen()
