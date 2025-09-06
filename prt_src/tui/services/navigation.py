"""Navigation service for PRT TUI.

Provides push/pop stack navigation with breadcrumb support
and navigation history tracking.
"""

from collections import deque
from dataclasses import dataclass
from typing import Any
from typing import Deque
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from prt_src.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class NavEntry:
    """Single navigation history entry."""

    screen_name: str
    title: str
    params: Dict[str, Any]
    has_unsaved: bool = False


class NavigationService:
    """Service for managing screen navigation.

    Provides push/pop stack navigation with history tracking
    and breadcrumb generation.
    """

    def __init__(self, max_history: int = 15, max_stack_depth: int = 20):
        """Initialize navigation service.

        Args:
            max_history: Maximum number of history entries to keep
            max_stack_depth: Maximum depth of navigation stack
        """
        # Navigation stack (current navigation path)
        self._stack: List[NavEntry] = []
        self._max_stack_depth = max_stack_depth

        # Navigation history ring buffer
        self._history: Deque[NavEntry] = deque(maxlen=max_history)

        # Current screen reference
        self._current_screen = None

        # Home screen name
        self._home_screen = "home"

    def push(self, screen_name: str, params: Optional[Dict[str, Any]] = None) -> None:
        """Push a new screen onto the navigation stack.

        Args:
            screen_name: Name of the screen to navigate to
            params: Optional parameters to pass to the screen
        """
        params = params or {}

        # Check stack depth limit
        if len(self._stack) >= self._max_stack_depth:
            logger.warning(
                f"Navigation stack depth limit ({self._max_stack_depth}) reached. "
                "Clearing old entries from bottom of stack."
            )
            # Remove oldest entries to make room
            while len(self._stack) >= self._max_stack_depth:
                self._stack.pop(0)

        # Create navigation entry
        entry = NavEntry(
            screen_name=screen_name,
            title=self._get_screen_title(screen_name),
            params=params,
            has_unsaved=False,
        )

        # Add to stack
        self._stack.append(entry)

        # Add to history
        self._history.append(entry)

        logger.info(f"Navigated to {screen_name} (stack depth: {len(self._stack)})")

    def pop(self) -> Optional[str]:
        """Pop the current screen and return to previous.

        Returns:
            Name of the screen we're returning to, or None if stack is empty
        """
        if len(self._stack) <= 1:
            logger.warning("Cannot pop - at bottom of navigation stack")
            return None

        # Remove current screen
        popped = self._stack.pop()
        logger.info(f"Popped {popped.screen_name} from navigation stack")

        # Return to previous screen
        if self._stack:
            previous = self._stack[-1]
            return previous.screen_name

        return None

    def go_home(self) -> None:
        """Navigate directly to home screen, clearing the stack."""
        logger.info("Navigating to home screen")

        # Clear stack except home
        self._stack = [
            NavEntry(
                screen_name=self._home_screen,
                title="Home",
                params={},
                has_unsaved=False,
            )
        ]

    def replace(self, screen_name: str, params: Optional[Dict[str, Any]] = None) -> None:
        """Replace current screen with a new one (no back navigation).

        Args:
            screen_name: Name of the screen to navigate to
            params: Optional parameters to pass to the screen
        """
        params = params or {}

        # Remove current if exists
        if self._stack:
            old = self._stack.pop()
            logger.info(f"Replacing {old.screen_name} with {screen_name}")

        # Push new screen
        self.push(screen_name, params)

    def get_stack(self) -> List[str]:
        """Get the current navigation stack.

        Returns:
            List of screen names in the stack
        """
        return [entry.screen_name for entry in self._stack]

    def has_back_stack(self) -> bool:
        """Check if there's a screen to go back to.

        Returns:
            True if we can pop the stack
        """
        return len(self._stack) > 1

    def get_breadcrumb(self) -> List[str]:
        """Get breadcrumb trail for current navigation.

        Returns:
            List of screen titles in navigation order
        """
        return [entry.title for entry in self._stack]

    def get_history(self) -> List[NavEntry]:
        """Get navigation history.

        Returns:
            List of recent navigation entries (newest first)
        """
        return list(reversed(self._history))

    def mark_unsaved(self, screen_name: Optional[str] = None) -> None:
        """Mark a screen as having unsaved changes.

        Args:
            screen_name: Screen to mark, or current if None
        """
        screen_name = screen_name or self.get_current_screen()

        # Mark in stack
        for entry in self._stack:
            if entry.screen_name == screen_name:
                entry.has_unsaved = True
                logger.debug(f"Marked {screen_name} as having unsaved changes")
                break

        # Mark in history
        for entry in self._history:
            if entry.screen_name == screen_name:
                entry.has_unsaved = True

    def clear_unsaved(self, screen_name: Optional[str] = None) -> None:
        """Clear unsaved changes marker for a screen.

        Args:
            screen_name: Screen to clear, or current if None
        """
        screen_name = screen_name or self.get_current_screen()

        # Clear in stack
        for entry in self._stack:
            if entry.screen_name == screen_name:
                entry.has_unsaved = False
                logger.debug(f"Cleared unsaved changes for {screen_name}")
                break

        # Clear in history
        for entry in self._history:
            if entry.screen_name == screen_name:
                entry.has_unsaved = False

    def get_current_screen(self) -> Optional[str]:
        """Get the name of the current screen.

        Returns:
            Current screen name or None
        """
        if self._stack:
            return self._stack[-1].screen_name
        return None

    def get_current_params(self) -> Dict[str, Any]:
        """Get parameters for the current screen.

        Returns:
            Current screen parameters or empty dict
        """
        if self._stack:
            return self._stack[-1].params
        return {}

    def set_home_screen(self, screen_name: str) -> None:
        """Set the home screen name.

        Args:
            screen_name: Name of the home screen
        """
        self._home_screen = screen_name
        logger.info(f"Home screen set to: {screen_name}")

    def _get_screen_title(self, screen_name: str) -> str:
        """Get display title for a screen.

        Args:
            screen_name: Screen name

        Returns:
            Human-readable title
        """
        # Convert snake_case to Title Case
        return screen_name.replace("_", " ").title()

    def get_history_with_unsaved(self) -> List[Tuple[str, bool]]:
        """Get history with unsaved markers for breadcrumb dropdown.

        Returns:
            List of (title, has_unsaved) tuples
        """
        result = []
        for entry in self.get_history()[:10]:  # Limit to 10 most recent
            result.append((entry.title, entry.has_unsaved))
        return result

    def clear(self) -> None:
        """Clear all navigation state."""
        self._stack.clear()
        self._history.clear()
        logger.info("Navigation state cleared")
