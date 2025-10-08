"""TUI constants for widget IDs and other shared values.

Centralizing these constants helps avoid typos and makes refactoring easier.
"""


# Widget IDs
class WidgetIDs:
    """Widget ID constants to avoid string typos."""

    # TopNav
    TOP_NAV = "top-nav"

    # BottomNav
    BOTTOM_NAV = "bottom-nav"

    # DropdownMenu
    DROPDOWN_MENU = "dropdown-menu"

    # Content containers
    HOME_CONTENT = "home-content"
    HELP_CONTENT = "help-content"
    SETTINGS_CONTENT = "settings-content"
    SEARCH_CONTENT = "search-content"
    CHAT_CONTENT = "chat-content"

    # Confirmation dialogs
    EXIT_CONFIRMATION = "exit-confirmation"

    # Help message
    HELP_MESSAGE = "help-message"

    # Settings widgets
    SETTINGS_DB_STATUS = "settings-db-status"
    SETTINGS_PLACEHOLDER = "settings-placeholder"

    # Search widgets
    SEARCH_INPUT = "search-input"
    SEARCH_BUTTONS = "search-buttons"
    SEARCH_RESULTS = "search-results"

    # Chat widgets
    CHAT_STATUS = "chat-status"
    CHAT_INPUT = "chat-input"
    CHAT_RESPONSE = "chat-response"


# CSS classes
class CSSClasses:
    """CSS class constants."""

    MENU_OPTION = "menu-option"
    SCREEN_PLACEHOLDER = "screen-placeholder"
    CONFIRM_TITLE = "confirm-title"
    CONFIRM_BUTTONS = "confirm-buttons"
