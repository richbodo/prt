"""Search screen - Search for contacts, relationships, tags, and notes."""

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.containers import Horizontal
from textual.containers import VerticalScroll
from textual.widgets import Button
from textual.widgets import Static
from textual.widgets import TextArea

from prt_src.logging_config import get_logger
from prt_src.tui.constants import WidgetIDs
from prt_src.tui.screens.base import BaseScreen
from prt_src.tui.widgets import BottomNav
from prt_src.tui.widgets import DropdownMenu
from prt_src.tui.widgets import TopNav

logger = get_logger(__name__)


class SearchTextArea(TextArea):
    """Custom TextArea that intercepts Enter key to execute search instead of inserting newline.

    Key bindings:
    - Enter: Execute search
    - Ctrl+J: Insert newline (carriage return)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parent_screen = None

    async def _on_key(self, event: events.Key) -> None:
        """Override key handler to intercept Enter for search execution and Ctrl+J for newline."""
        key = event.key

        # Ctrl+J = insert newline
        if key == "ctrl+j":
            logger.info("[SearchTextArea] CTRL+J detected - inserting newline")
            self.insert("\n")
            event.prevent_default()
            event.stop()
            return

        # Plain Enter = execute search
        if key == "enter" and self._parent_screen:
            logger.info("[SearchTextArea] Plain ENTER detected - executing search")
            handled = await self._parent_screen._handle_textarea_submit()
            if handled:
                event.prevent_default()
                event.stop()
                return

        # All other keys - let TextArea handle
        await super()._on_key(event)


def search_contacts_stub(query: str) -> list[dict]:
    """Stub function - returns test contact search results.

    TODO Phase 2B: Replace with real DataService integration.

    Args:
        query: Search query string

    Returns:
        List of contact dictionaries
    """
    return [
        {"id": 1, "name": "Test Contact 1", "email": "test1@example.com"},
        {"id": 2, "name": "Test Contact 2", "email": "test2@example.com"},
        {"id": 3, "name": "Test Contact 3", "email": "test3@example.com"},
    ]


def search_relationships_stub(query: str) -> list[dict]:
    """Stub function - returns test relationship search results.

    TODO Phase 2B: Replace with real DataService integration.
    """
    return [
        {"id": 1, "from": "Alice", "to": "Bob", "type": "Friend"},
        {"id": 2, "from": "Bob", "to": "Carol", "type": "Colleague"},
    ]


def search_relationship_types_stub(query: str) -> list[dict]:
    """Stub function - returns test relationship type search results.

    TODO Phase 2B: Replace with real DataService integration.
    """
    return [
        {"id": 1, "key": "friend", "label": "Friend"},
        {"id": 2, "key": "colleague", "label": "Colleague"},
        {"id": 3, "key": "family", "label": "Family Member"},
    ]


def search_notes_stub(query: str) -> list[dict]:
    """Stub function - returns test note search results.

    TODO Phase 2B: Replace with real DataService integration.
    """
    return [
        {"id": 1, "title": "Meeting Notes", "content": "Discussed project timeline"},
        {"id": 2, "title": "Follow-up", "content": "Send email about proposal"},
    ]


def search_tags_stub(query: str) -> list[dict]:
    """Stub function - returns test tag search results.

    TODO Phase 2B: Replace with real DataService integration.
    """
    return [
        {"id": 1, "name": "work"},
        {"id": 2, "name": "personal"},
        {"id": 3, "name": "important"},
    ]


class SearchScreen(BaseScreen):
    """Search screen with search box, type buttons, and results display.

    Per spec:
    - Top Nav
    - Search input box (3 lines, editable)
    - Five buttons for search types
    - Results display area (scrollable)
    - Bottom Nav
    """

    # Search type constants
    SEARCH_CONTACTS = "contacts"
    SEARCH_RELATIONSHIPS = "relationships"
    SEARCH_RELATIONSHIP_TYPES = "relationship_types"
    SEARCH_NOTES = "notes"
    SEARCH_TAGS = "tags"

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
        """Initialize Search screen."""
        super().__init__(**kwargs)
        self.screen_title = "SEARCH"
        self.current_search_type = self.SEARCH_CONTACTS
        self._processing_enter = False  # Flag to prevent double-processing
        self.search_functions = {
            self.SEARCH_CONTACTS: search_contacts_stub,
            self.SEARCH_RELATIONSHIPS: search_relationships_stub,
            self.SEARCH_RELATIONSHIP_TYPES: search_relationship_types_stub,
            self.SEARCH_NOTES: search_notes_stub,
            self.SEARCH_TAGS: search_tags_stub,
        }

    def compose(self) -> ComposeResult:
        """Compose the search screen layout."""
        # Top navigation bar
        self.top_nav = TopNav(self.screen_title, id=WidgetIDs.TOP_NAV)
        yield self.top_nav

        # Main content container
        with Container(id=WidgetIDs.SEARCH_CONTENT):
            # Search input box - using custom TextArea subclass
            self.search_input = SearchTextArea(
                id=WidgetIDs.SEARCH_INPUT,
                placeholder="Enter search text...",
            )
            self.search_input.styles.height = 3
            self.search_input._parent_screen = self  # Link to parent for ENTER handling
            yield self.search_input

            # Hint text
            self.input_hint = Static(
                "Enter to send, Ctrl+J inserts carriage return",
                id="search-input-hint",
            )
            yield self.input_hint

            # Search type buttons
            with Horizontal(id=WidgetIDs.SEARCH_BUTTONS):
                yield Button("(1) Contacts", id="btn-contacts", variant="primary")
                yield Button("(2) Relationships", id="btn-relationships")
                yield Button("(3) Relationship Types", id="btn-relationship-types")
                yield Button("(4) Notes", id="btn-notes")
                yield Button("(5) Tags", id="btn-tags")

            # Results display (scrollable container)
            with VerticalScroll(id=WidgetIDs.SEARCH_RESULTS) as self.results_display:
                self.results_display.can_focus = True
                self.results_content = Static(
                    "Enter a search query and select a search type.",
                    id="search-results-content",
                )
                yield self.results_content

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
        logger.info("Search screen mounted")

        # Start in EDIT mode since search input is the primary purpose
        from prt_src.tui.types import AppMode

        self.app.current_mode = AppMode.EDIT
        self.top_nav.set_mode(AppMode.EDIT)
        # Focus the search input box
        self.search_input.focus()
        logger.debug("Search screen: Set mode to EDIT on mount and focused input")

    async def _handle_textarea_submit(self) -> bool:
        """Handle Enter key from SearchTextArea for search execution.

        Returns:
            True if handled and search executed
        """
        from prt_src.tui.types import AppMode

        # Only process if in EDIT mode
        if self.app.current_mode != AppMode.EDIT:
            return False

        if self._processing_enter:
            return False

        self._processing_enter = True

        # Execute the search
        logger.info("[SEARCH] ENTER pressed - calling action_execute_search")
        self.action_execute_search()
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
            elif key in ["1", "2", "3", "4", "5"]:
                # Number keys only work in NAV mode (not EDIT) to allow phone number searches
                self.action_select_search_type(key)
                event.prevent_default()
            elif self.dropdown.display:
                # When menu is open, check for menu actions
                action = self.dropdown.get_action(key)
                if action:
                    action()
                    event.prevent_default()

    def on_button_pressed(self, event) -> None:
        """Handle button press events.

        Args:
            event: Button pressed event
        """
        button_id = event.button.id
        search_type_map = {
            "btn-contacts": self.SEARCH_CONTACTS,
            "btn-relationships": self.SEARCH_RELATIONSHIPS,
            "btn-relationship-types": self.SEARCH_RELATIONSHIP_TYPES,
            "btn-notes": self.SEARCH_NOTES,
            "btn-tags": self.SEARCH_TAGS,
        }

        if button_id in search_type_map:
            self.current_search_type = search_type_map[button_id]
            self._update_button_highlights()
            self.action_execute_search()
            logger.info(f"Search type selected via button: {self.current_search_type}")

    def action_select_search_type(self, key: str) -> None:
        """Select search type based on number key.

        Args:
            key: Number key pressed (1-5)
        """
        type_map = {
            "1": self.SEARCH_CONTACTS,
            "2": self.SEARCH_RELATIONSHIPS,
            "3": self.SEARCH_RELATIONSHIP_TYPES,
            "4": self.SEARCH_NOTES,
            "5": self.SEARCH_TAGS,
        }

        if key in type_map:
            self.current_search_type = type_map[key]
            self._update_button_highlights()
            self.action_execute_search()
            logger.info(f"Search type selected: {self.current_search_type}")

    def action_execute_search(self) -> None:
        """Execute search with current query and type."""
        query = self.search_input.text.strip()

        if not query:
            self.results_content.update("Please enter a search query.")
            self.bottom_nav.show_status("Please enter a search query")
            return

        logger.info(f"Executing {self.current_search_type} search for: {query}")

        # Show searching status
        self.bottom_nav.show_status(f"Searching {self.current_search_type} for '{query}'...")
        self.results_content.update(f"Searching {self.current_search_type}...\n\n(Using stub data)")

        # Get stub results
        search_func = self.search_functions[self.current_search_type]
        results = search_func(query)

        # Format and display results
        if not results:
            self.results_content.update(
                f"No {self.current_search_type} found matching '{query}'\n\n(Stub search - would search real database)"
            )
            self.bottom_nav.show_status(f"No results found for '{query}'")
        else:
            result_text = f"Search Results ({len(results)} found) - STUB DATA:\n\n"
            for item in results:
                result_text += self._format_result_item(item) + "\n"
            result_text += "\n(These are stub results. Phase 2B will connect to real database.)"
            self.results_content.update(result_text)
            self.bottom_nav.show_status(f"Found {len(results)} stub results for '{query}'")

    def _format_result_item(self, item: dict) -> str:
        """Format a single result item for display.

        Args:
            item: Result dictionary

        Returns:
            Formatted string
        """
        if self.current_search_type == self.SEARCH_CONTACTS:
            return f"• {item['name']} - {item['email']}"
        elif self.current_search_type == self.SEARCH_RELATIONSHIPS:
            return f"• {item['from']} → {item['to']} ({item['type']})"
        elif self.current_search_type == self.SEARCH_RELATIONSHIP_TYPES:
            return f"• {item['label']} ({item['key']})"
        elif self.current_search_type == self.SEARCH_NOTES:
            return f"• {item['title']}: {item['content']}"
        elif self.current_search_type == self.SEARCH_TAGS:
            return f"• {item['name']}"
        return str(item)

    def _update_button_highlights(self) -> None:
        """Update button styling to highlight the currently selected search type."""
        # Map search types to button IDs
        button_map = {
            self.SEARCH_CONTACTS: "btn-contacts",
            self.SEARCH_RELATIONSHIPS: "btn-relationships",
            self.SEARCH_RELATIONSHIP_TYPES: "btn-relationship-types",
            self.SEARCH_NOTES: "btn-notes",
            self.SEARCH_TAGS: "btn-tags",
        }

        # Update all buttons - set primary variant only for selected type
        for search_type, button_id in button_map.items():
            try:
                button = self.query_one(f"#{button_id}", Button)
                if search_type == self.current_search_type:
                    button.variant = "primary"
                else:
                    button.variant = "default"
            except Exception as e:
                logger.debug(f"Could not update button {button_id}: {e}")

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
                logger.debug("[SEARCH] Closed dropdown menu when switching to EDIT mode")

            # Focus the input box
            self.search_input.focus()
            logger.info("[SEARCH] Focused search input after mode change to EDIT")

        elif mode == AppMode.NAVIGATION:
            # Close dropdown menu if open
            if self.dropdown.display:
                self.dropdown.hide()
                self.top_nav.menu_open = False
                self.top_nav.refresh_display()
                logger.debug("[SEARCH] Closed dropdown menu when switching to NAV mode")

            # Focus the results area for scrolling
            self.results_display.focus()
            logger.info("[SEARCH] Focused results area after mode change to NAV")

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
        logger.info("Navigating to home from search screen")
        self.app.navigate_to("home")

    def action_go_back(self) -> None:
        """Go back to previous screen."""
        self.dropdown.hide()
        self.top_nav.menu_open = False
        self.top_nav.refresh_display()
        logger.info("Going back from search screen")
        self.app.pop_screen()

    # Scroll actions for NAV mode
    def action_scroll_down(self) -> None:
        """Scroll results area down (j key or down arrow in NAV mode)."""
        if self.results_display.has_focus:
            self.results_display.scroll_down()

    def action_scroll_up(self) -> None:
        """Scroll results area up (k key or up arrow in NAV mode)."""
        if self.results_display.has_focus:
            self.results_display.scroll_up()

    def action_page_down(self) -> None:
        """Scroll results area one page down (PageDown in NAV mode)."""
        if self.results_display.has_focus:
            self.results_display.scroll_page_down()

    def action_page_up(self) -> None:
        """Scroll results area one page up (PageUp in NAV mode)."""
        if self.results_display.has_focus:
            self.results_display.scroll_page_up()

    def action_scroll_top(self) -> None:
        """Scroll results area to top (Home key in NAV mode)."""
        if self.results_display.has_focus:
            self.results_display.scroll_home()

    def action_scroll_bottom(self) -> None:
        """Scroll results area to bottom (End key in NAV mode)."""
        if self.results_display.has_focus:
            self.results_display.scroll_end()

    def on_focus(self, event) -> None:
        """Handle focus changes - close dropdown menu when focus changes."""
        # Close dropdown menu when focus changes to any widget
        if self.dropdown.display:
            self.dropdown.hide()
            self.top_nav.menu_open = False
            self.top_nav.refresh_display()
            logger.debug("[SEARCH] Closed dropdown menu on focus change")
