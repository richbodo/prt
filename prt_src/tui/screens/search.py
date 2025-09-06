"""Search screen for PRT TUI.

Full-text search with filters and export.
"""

import asyncio
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.containers import Vertical
from textual.events import Key
from textual.widgets import Input

from prt_src.tui.screens import register_screen
from prt_src.tui.screens.base import BaseScreen
from prt_src.tui.screens.base import EscapeIntent
from prt_src.tui.widgets.search_filter import SearchResultList
from prt_src.tui.widgets.search_filter import SearchScopeFilter


class SearchScreen(BaseScreen):
    """Search screen with results and filters."""

    def get_screen_name(self) -> str:
        """Get screen identifier."""
        return "search"

    def __init__(self, *args, **kwargs):
        """Initialize search screen."""
        super().__init__(*args, **kwargs)
        self._has_results = False
        self._current_query = ""
        self._current_scopes = []
        self._search_in_progress = False

    def on_escape(self) -> EscapeIntent:
        """POP if showing results, else HOME."""
        if self._has_results:
            return EscapeIntent.POP
        return EscapeIntent.HOME

    def get_header_config(self) -> Optional[Dict[str, Any]]:
        """Configure header."""
        config = super().get_header_config()
        if config:
            config["title"] = "Search"
        return config

    def get_footer_config(self) -> Optional[Dict[str, Any]]:
        """Configure footer with search tips."""
        config = super().get_footer_config()
        if config:
            tips = [
                "[/] Focus search",
                "[Tab] Cycle filters",
                "[Enter] Select result",
                "[ESC] Back",
            ]
            config["keyHints"] = tips
        return config

    def compose(self) -> ComposeResult:
        """Compose search screen layout."""
        with Vertical(classes="search-screen-container"):
            # Search input at the top
            yield Input(
                placeholder="Enter search query...", id="search-input", classes="search-input"
            )

            # Main content area with filters and results
            with Horizontal(classes="search-content"):
                # Left side - Search scope filters
                self.scope_filter = SearchScopeFilter(on_scope_change=self._on_scope_change)
                yield self.scope_filter

                # Right side - Search results
                self.result_list = SearchResultList(on_result_select=self._on_result_select)
                yield self.result_list

    async def on_mount(self) -> None:
        """Setup when screen is mounted."""
        await super().on_mount()
        # Focus the search input initially
        try:
            search_input = self.query_one("#search-input", Input)
            search_input.focus()
        except Exception:
            pass

    async def on_input_submitted(self, event) -> None:
        """Handle search input submission."""
        if event.input.id == "search-input":
            query = event.value.strip()
            if query:
                await self._perform_search(query)

    async def on_key(self, event: Key) -> None:
        """Handle key presses."""
        # Focus search input on '/'
        if event.key == "/":
            try:
                search_input = self.query_one("#search-input", Input)
                search_input.focus()
                event.prevent_default()
            except Exception:
                pass

        # Navigate results with arrow keys
        elif event.key == "up":
            if self.result_list.navigate_results("up"):
                event.prevent_default()

        elif event.key == "down":
            if self.result_list.navigate_results("down"):
                event.prevent_default()

        # Select result with Enter
        elif event.key == "enter":
            # If search input is focused and has text, search
            try:
                search_input = self.query_one("#search-input", Input)
                if search_input.has_focus and search_input.value.strip():
                    await self._perform_search(search_input.value.strip())
                    event.prevent_default()
                    return
            except Exception:
                pass

            # Otherwise select current result
            if self.result_list.select_current_result():
                event.prevent_default()

        # Cycle through scope filters with Tab
        elif event.key == "tab":
            # This could be enhanced to cycle through checkboxes
            event.prevent_default()

    def _on_scope_change(self, scopes: List[str]) -> None:
        """Handle scope filter changes."""
        self._current_scopes = scopes

        # Re-run search if we have a current query
        if self._current_query and not self._search_in_progress:
            asyncio.create_task(self._perform_search(self._current_query))

    def _on_result_select(self, entity_type: str, result_data: Any) -> None:
        """Handle result selection."""
        if not self.nav_service:
            return

        try:
            # Navigate to appropriate detail screen based on entity type
            if entity_type == "contacts":
                contact_id = getattr(result_data, "entity_id", None)
                if contact_id:
                    self.nav_service.push_screen("contact_detail", contact_id=contact_id)

            elif entity_type == "relationships":
                # Could navigate to a relationship detail screen
                # For now, show a notification
                if self.notification_service:
                    self.notification_service.show_info(
                        f"Selected relationship: {getattr(result_data, 'title', 'Unknown')}"
                    )

            elif entity_type in ["notes", "tags"]:
                # Could navigate to metadata screens or show details
                if self.notification_service:
                    title = getattr(result_data, "title", "Unknown")
                    self.notification_service.show_info(f"Selected {entity_type[:-1]}: {title}")

        except Exception as e:
            if self.notification_service:
                self.notification_service.show_error(f"Error navigating to result: {e}")

    async def _perform_search(self, query: str) -> None:
        """Perform search with current query and scope."""
        if self._search_in_progress:
            return

        self._search_in_progress = True
        self._current_query = query

        try:
            if not self.data_service:
                if self.notification_service:
                    await self.notification_service.show_error("Data service not available")
                return

            # Show searching status
            empty_results = {
                "query": query,
                "results": {},
                "total": 0,
                "suggestions": [],
                "stats": {
                    "search_time": 0.0,
                    "cache_used": False,
                    "fts_used": False,
                    "sources": [],
                },
            }
            self.result_list.update_results(empty_results)

            # Perform the search
            search_results = await self.data_service.unified_search(
                query=query,
                entity_types=self._current_scopes if self._current_scopes else None,
                limit=100,
            )

            # Update results display
            self.result_list.update_results(search_results)

            # Update internal state
            self._has_results = search_results.get("total", 0) > 0

            # Show notification for search completion
            if self.notification_service:
                total = search_results.get("total", 0)
                search_time = search_results.get("stats", {}).get("search_time", 0.0)
                await self.notification_service.show_info(
                    f"Search completed: {total} results in {search_time:.2f}s"
                )

        except Exception as e:
            # Show error
            if self.notification_service:
                await self.notification_service.show_error(f"Search failed: {e}")

            # Show empty results
            error_results = {
                "query": query,
                "results": {},
                "total": 0,
                "suggestions": [],
                "stats": {
                    "search_time": 0.0,
                    "cache_used": False,
                    "fts_used": False,
                    "sources": [],
                },
            }
            self.result_list.update_results(error_results)

        finally:
            self._search_in_progress = False


# Register this screen
register_screen("search", SearchScreen)
