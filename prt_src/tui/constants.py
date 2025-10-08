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

    # Confirmation dialogs
    EXIT_CONFIRMATION = "exit-confirmation"

    # Help message
    HELP_MESSAGE = "help-message"


# CSS classes
class CSSClasses:
    """CSS class constants."""

    MENU_OPTION = "menu-option"
    SCREEN_PLACEHOLDER = "screen-placeholder"
    CONFIRM_TITLE = "confirm-title"
    CONFIRM_BUTTONS = "confirm-buttons"
