"""Chat screen - LLM interaction interface."""

import asyncio

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.containers import Horizontal
from textual.containers import VerticalScroll
from textual.widgets import LoadingIndicator
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

    Key bindings:
    - Enter: Submit message
    - Ctrl+J: Insert newline (carriage return)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parent_screen = None

    async def _on_key(self, event: events.Key) -> None:
        """Override key handler to intercept Enter for submission and Ctrl+J for newline."""
        key = event.key

        # Ctrl+J = insert newline
        if key == "ctrl+j":
            logger.info("[ChatTextArea] CTRL+J detected - inserting newline")
            self.insert("\n")
            event.prevent_default()
            event.stop()
            return

        # Plain Enter = submit message
        if key == "enter" and self._parent_screen:
            logger.info("[ChatTextArea] Plain ENTER detected - submitting")
            handled = await self._parent_screen._handle_textarea_submit()
            if handled:
                event.prevent_default()
                event.stop()
                return

        # All other keys - let TextArea handle
        await super()._on_key(event)


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

    # Key bindings for NAV mode scrolling
    BINDINGS = [
        Binding("j", "scroll_down", "Scroll down", show=False),
        Binding("k", "scroll_up", "Scroll up", show=False),
        Binding("up", "scroll_up", "Scroll up", show=False),
        Binding("down", "scroll_down", "Scroll down", show=False),
        Binding("pageup", "page_up", "Page up", show=False),
        Binding("pagedown", "page_down", "Page down", show=False),
        Binding("home", "scroll_top", "Scroll to top", show=False),
        Binding("end", "scroll_bottom", "Scroll to bottom", show=False),
    ]

    def __init__(self, **kwargs):
        """Initialize Chat screen."""
        super().__init__(**kwargs)
        self.screen_title = "CHAT"
        self.response_buffer = ""
        self._processing_enter = False  # Flag to prevent double-processing
        self.llm_ready = False  # Track LLM availability
        self.queued_message = None  # Queue message if LLM not ready
        # Note: self.llm_service comes from BaseScreen via kwargs

    def compose(self) -> ComposeResult:
        """Compose the chat screen layout.

        Layout (per spec):
        - Top Nav
        - Chat Status Line (immediately below top nav)
        - Response Box (scrollable, takes remaining space)
        - Chat Input Box (sticky at bottom)
        - Hint text
        - Bottom Nav
        """
        # Top navigation bar
        self.top_nav = TopNav(self.screen_title, id=WidgetIDs.TOP_NAV)
        yield self.top_nav

        # Chat status line (immediately below top nav)
        with Horizontal(id=WidgetIDs.CHAT_STATUS):
            self.chat_status_text = Static("LLM: CHECKING...", id="chat-status-text")
            yield self.chat_status_text

            # Loading indicator (hidden by default, shown during processing)
            self.chat_loading = LoadingIndicator(id="chat-loading")
            self.chat_loading.display = False
            yield self.chat_loading

        # Response display area (scrollable container, takes main space)
        with VerticalScroll(id=WidgetIDs.CHAT_RESPONSE) as self.chat_response:
            self.chat_response.can_focus = True
            self.chat_response_content = Static(
                "LLM responses will appear here.\n\nEnter your message below and press ENTER to send.",
                id="chat-response-content",
            )
            yield self.chat_response_content

        # Input container (sticky at bottom)
        with Container(id=WidgetIDs.CHAT_CONTENT):
            # Chat input box - using custom TextArea subclass
            self.chat_input = ChatTextArea(
                id=WidgetIDs.CHAT_INPUT,
                placeholder="Enter your prompt here... (Ctrl+J inserts newline)",
            )
            self.chat_input.styles.height = 5
            self.chat_input._parent_screen = self  # Link to parent for ENTER handling
            yield self.chat_input

            # Hint text
            self.input_hint = Static(
                "Enter to send, Ctrl+J inserts carriage return",
                id="chat-input-hint",
            )
            yield self.input_hint

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
        """Handle screen mount.

        IMPORTANT: Screen renders IMMEDIATELY, LLM loads in background.
        This ensures:
        - User can type in input box right away
        - Esc works to navigate back
        - Loading status is visible
        - No frozen UI while model loads (can take 8-30s)
        """
        await super().on_mount()
        logger.info("[CHAT] Chat screen mounted - starting background LLM initialization")

        # Start in EDIT mode since chat input is the primary purpose
        from prt_src.tui.types import AppMode

        self.app.current_mode = AppMode.EDIT
        self.top_nav.set_mode(AppMode.EDIT)
        # Focus the chat input box
        self.chat_input.focus()
        logger.debug("[CHAT] Set mode to EDIT on mount and focused input")

        # LLM service comes from BaseScreen (injected via kwargs)
        # Check LLM health in BACKGROUND (don't await - screen rendered immediately)
        self.run_worker(self._check_llm_health(), exclusive=False, name="llm_health_check")
        logger.info("[CHAT] Started background worker for LLM health check")

    async def _check_llm_health(self) -> None:
        """Check if Ollama LLM is available and update status."""
        if not self.llm_service:
            self.llm_ready = False
            self.chat_status_text.update("❌ LLM: ERROR │ Service not initialized")
            self.chat_loading.display = False
            logger.error("LLM service is not available")
            return

        try:
            # Check health with timeout
            is_healthy = await self.llm_service.health_check(timeout=2.0)

            if is_healthy:
                # Preload the model into memory to avoid cold start delays
                self.chat_status_text.update("⏳ LLM: LOADING MODEL...")
                self.chat_loading.display = True
                logger.info("LLM health check passed, preloading model...")

                preload_success = await self.llm_service.preload_model()

                if preload_success:
                    self.llm_ready = True
                    self.chat_status_text.update(
                        f"✅ LLM: ONLINE │ READY ({self.llm_service.model})"
                    )
                    self.chat_loading.display = False
                    logger.info("[CHAT] LLM model preloaded successfully")

                    # Process queued message if user sent one while loading
                    if self.queued_message:
                        logger.info("[CHAT] Processing queued message after LLM ready")
                        await self._send_queued_message()
                else:
                    self.llm_ready = True  # Still mark as ready, model will load on first use
                    self.chat_status_text.update("⚠️  LLM: ONLINE │ Model will load on first use")
                    self.chat_loading.display = False
                    logger.warning("[CHAT] LLM model preload failed, but service is available")

                    # Process queued message if any
                    if self.queued_message:
                        logger.info(
                            "[CHAT] Processing queued message (model will load on first use)"
                        )
                        await self._send_queued_message()
            else:
                self.llm_ready = False
                self.chat_status_text.update("❌ LLM: OFFLINE │ Cannot connect to Ollama")
                self.chat_loading.display = False
                logger.warning("LLM health check failed")
        except Exception as e:
            self.llm_ready = False
            self.chat_status_text.update(f"❌ LLM: ERROR │ {str(e)[:40]}")
            self.chat_loading.display = False
            logger.error(f"LLM health check error: {e}")

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

        Note:
            ESC key is handled by app-level priority binding (action_toggle_mode),
            which calls on_mode_changed(). No need to handle ESC here.
        """
        from prt_src.tui.types import AppMode

        key = event.key.lower()

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

    async def _send_queued_message(self) -> None:
        """Send the queued message to LLM."""
        if not self.queued_message:
            return

        message = self.queued_message
        self.queued_message = None  # Clear queue

        # Temporarily restore message to input to show what's being sent
        self.chat_input.text = message

        # Now send it
        await self._send_message_to_llm(message)

    async def _send_message_to_llm(self, message: str) -> None:
        """Internal method to send message to LLM (used by both immediate and queued sends)."""
        logger.info(f"[CHAT] Sending message to LLM: {message[:50]}...")

        # Show processing status with animated loading indicator
        self.chat_status_text.update("⏳ LLM: PROCESSING │ Generating response...")
        self.chat_loading.display = True
        self.bottom_nav.show_status("Sending message to LLM...")

        try:
            # Call LLM chat (it's synchronous, so run in thread pool)
            logger.info(f"[CHAT] Calling LLM via asyncio.to_thread, message length: {len(message)}")
            response = await asyncio.to_thread(self.llm_service.chat, message)
            logger.info(f"[CHAT] Received response from LLM, length: {len(response)}")

            # Add to response buffer
            self._add_to_response_buffer(f"\n> You: {message}\n\n{response}\n")

            # Update display
            self.chat_response_content.update(self.response_buffer)

            # Auto-scroll to bottom to show new response
            self.chat_response.scroll_end(animate=False)

            # Reset status - hide loading indicator
            self.chat_loading.display = False
            self.chat_status_text.update(f"✅ LLM: ONLINE │ READY ({self.llm_service.model})")
            self.bottom_nav.show_status("Message sent successfully")

            # Clear input
            self.chat_input.clear()
        except Exception as e:
            logger.error(f"[CHAT] Error sending message to LLM: {e}")
            self.bottom_nav.show_status(f"Error: {str(e)[:50]}")
            self.chat_loading.display = False
            self.chat_status_text.update(f"❌ LLM: ERROR │ {str(e)[:40]}")

    async def action_send_message(self) -> None:
        """Send message to LLM and display response."""
        message = self.chat_input.text.strip()

        if not message:
            self.bottom_nav.show_status("Please enter a message")
            return

        # Check if LLM is ready
        if not self.llm_ready or not self.llm_service:
            # Queue the message for when LLM is ready
            self.queued_message = message
            self.bottom_nav.show_status("⏳ Message queued - LLM is still loading...")
            logger.info(f"[CHAT] Message queued (LLM not ready): {message[:50]}...")
            # Clear input to show it was accepted
            self.chat_input.clear()
            return

        # LLM is ready - send immediately
        await self._send_message_to_llm(message)
        logger.info("[CHAT] Message sent successfully")

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
        """Handle mode changes - focus appropriate widget based on mode.

        Called by app's action_toggle_mode() after mode changes.

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

        elif mode == AppMode.NAVIGATION:
            # Close dropdown menu if open
            if self.dropdown.display:
                self.dropdown.hide()
                self.top_nav.menu_open = False
                self.top_nav.refresh_display()
                logger.debug("[CHAT] Closed dropdown menu when switching to NAV mode")

            # Focus the response area for scrolling
            self.chat_response.focus()
            logger.info("[CHAT] Focused response area after mode change to NAV")

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

    # Scroll actions for NAV mode
    def action_scroll_down(self) -> None:
        """Scroll response area down (j key or down arrow in NAV mode)."""
        if self.chat_response.has_focus:
            self.chat_response.scroll_down()

    def action_scroll_up(self) -> None:
        """Scroll response area up (k key or up arrow in NAV mode)."""
        if self.chat_response.has_focus:
            self.chat_response.scroll_up()

    def action_page_down(self) -> None:
        """Scroll response area one page down (PageDown in NAV mode)."""
        if self.chat_response.has_focus:
            self.chat_response.scroll_page_down()

    def action_page_up(self) -> None:
        """Scroll response area one page up (PageUp in NAV mode)."""
        if self.chat_response.has_focus:
            self.chat_response.scroll_page_up()

    def action_scroll_top(self) -> None:
        """Scroll response area to top (Home key in NAV mode)."""
        if self.chat_response.has_focus:
            self.chat_response.scroll_home()

    def action_scroll_bottom(self) -> None:
        """Scroll response area to bottom (End key in NAV mode)."""
        if self.chat_response.has_focus:
            self.chat_response.scroll_end()

    def on_focus(self, event) -> None:
        """Handle focus changes - close dropdown menu when focus changes."""
        # Close dropdown menu when focus changes to any widget
        if self.dropdown.display:
            self.dropdown.hide()
            self.top_nav.menu_open = False
            self.top_nav.refresh_display()
            logger.debug("[CHAT] Closed dropdown menu on focus change")
