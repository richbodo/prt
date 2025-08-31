"""Test Navigation Menu Widget for the Textual TUI.

Comprehensive tests for the home screen navigation menu.
"""

from prt_src.tui.widgets.navigation_menu import MenuItem, NavigationMenu


class TestMenuItem:
    """Test the MenuItem data class."""

    def test_menu_item_creation(self):
        """Test that MenuItem can be created with required fields."""
        item = MenuItem(
            key="c",
            label="Contacts",
            description="Manage contacts",
            action="contacts",
        )

        assert item.key == "c"
        assert item.label == "Contacts"
        assert item.description == "Manage contacts"
        assert item.action == "contacts"

    def test_menu_item_with_icon(self):
        """Test MenuItem with optional icon."""
        item = MenuItem(
            key="r",
            label="Relationships",
            description="Manage relationships",
            action="relationships",
            icon="👥",
        )

        assert item.icon == "👥"

    def test_menu_item_disabled(self):
        """Test MenuItem disabled state."""
        item = MenuItem(
            key="x",
            label="Disabled",
            description="Not available",
            action="disabled",
            disabled=True,
        )

        assert item.disabled is True

    def test_menu_item_display_text(self):
        """Test MenuItem display text formatting."""
        item = MenuItem(key="s", label="Search", description="Search contacts", action="search")

        # Should format as "[s] Search"
        assert item.display_text == "[s] Search"

    def test_menu_item_display_text_with_icon(self):
        """Test MenuItem display text with icon."""
        item = MenuItem(
            key="d",
            label="Database",
            description="Database management",
            action="database",
            icon="💾",
        )

        # Should format as "💾 [d] Database"
        assert item.display_text == "💾 [d] Database"


class TestNavigationMenu:
    """Test the NavigationMenu widget."""

    def test_navigation_menu_creation(self):
        """Test that NavigationMenu can be created."""
        menu = NavigationMenu()
        assert menu is not None
        assert hasattr(menu, "selected_index")
        assert hasattr(menu, "menu_items")

    def test_navigation_menu_default_items(self):
        """Test default menu items are loaded."""
        menu = NavigationMenu()

        # Should have the standard menu items
        assert len(menu.menu_items) >= 8  # c, r, s, d, m, t, ?, q

        # Check key mappings
        keys = [item.key for item in menu.menu_items]
        assert "c" in keys  # Contacts
        assert "r" in keys  # Relationships
        assert "s" in keys  # Search
        assert "d" in keys  # Database
        assert "m" in keys  # Metadata
        assert "t" in keys  # Chat
        assert "?" in keys  # Help
        assert "q" in keys  # Quit

    def test_navigation_menu_custom_items(self):
        """Test creating menu with custom items."""
        custom_items = [
            MenuItem("a", "Add", "Add new contact", "add"),
            MenuItem("e", "Edit", "Edit contact", "edit"),
        ]

        menu = NavigationMenu(items=custom_items)
        assert len(menu.menu_items) == 2
        assert menu.menu_items[0].key == "a"
        assert menu.menu_items[1].key == "e"

    def test_navigation_menu_selection(self):
        """Test menu item selection."""
        menu = NavigationMenu()

        # Initial selection should be 0
        assert menu.selected_index == 0

        # Select next item
        menu.select_next()
        assert menu.selected_index == 1

        # Select previous item
        menu.select_previous()
        assert menu.selected_index == 0

    def test_navigation_menu_wrap_around(self):
        """Test selection wrapping at boundaries."""
        menu = NavigationMenu()
        menu_count = len(menu.menu_items)

        # Wrap from first to last
        menu.selected_index = 0
        menu.select_previous()
        assert menu.selected_index == menu_count - 1

        # Wrap from last to first
        menu.selected_index = menu_count - 1
        menu.select_next()
        assert menu.selected_index == 0

    def test_navigation_menu_select_by_key(self):
        """Test selecting menu item by key."""
        menu = NavigationMenu()

        # Select Contacts with 'c'
        result = menu.select_by_key("c")
        assert result is not None
        assert result.action == "contacts"

        # Select Search with 's'
        result = menu.select_by_key("s")
        assert result is not None
        assert result.action == "search"

        # Invalid key returns None
        result = menu.select_by_key("z")
        assert result is None

    def test_navigation_menu_disabled_items(self):
        """Test that disabled items cannot be activated."""
        items = [
            MenuItem("a", "Active", "Active item", "active"),
            MenuItem("d", "Disabled", "Disabled item", "disabled", disabled=True),
        ]

        menu = NavigationMenu(items=items)

        # Can select active item
        result = menu.select_by_key("a")
        assert result is not None

        # Cannot activate disabled item
        result = menu.select_by_key("d")
        assert result is None  # Returns None for disabled items

    def test_navigation_menu_vim_navigation(self):
        """Test vim-style j/k navigation."""
        menu = NavigationMenu()

        # 'j' moves down
        menu.selected_index = 0
        handled = menu.handle_key("j")
        assert handled is True
        assert menu.selected_index == 1

        # 'k' moves up
        handled = menu.handle_key("k")
        assert handled is True
        assert menu.selected_index == 0

        # 'G' goes to last item
        handled = menu.handle_key("G")
        assert handled is True
        assert menu.selected_index == len(menu.menu_items) - 1

        # 'g' goes to first item
        handled = menu.handle_key("g")
        assert handled is True
        assert menu.selected_index == 0

    def test_navigation_menu_enter_activation(self):
        """Test Enter key activates selected item."""
        activation_called = False
        activated_item = None

        def on_activate(item):
            nonlocal activation_called, activated_item
            activation_called = True
            activated_item = item

        menu = NavigationMenu(on_activate=on_activate)
        menu.selected_index = 0

        # Enter should activate current item
        handled = menu.handle_key("enter")
        assert handled is True
        assert activation_called is True
        assert activated_item is not None
        assert activated_item.key == menu.menu_items[0].key

    def test_navigation_menu_direct_key_activation(self):
        """Test direct key activation (c, r, s, etc.)."""
        activation_called = False
        activated_item = None

        def on_activate(item):
            nonlocal activation_called, activated_item
            activation_called = True
            activated_item = item

        menu = NavigationMenu(on_activate=on_activate)

        # Direct key 'c' should activate Contacts
        handled = menu.handle_key("c")
        assert handled is True
        assert activation_called is True
        assert activated_item is not None
        assert activated_item.action == "contacts"

    def test_navigation_menu_get_selected(self):
        """Test getting currently selected item."""
        menu = NavigationMenu()

        menu.selected_index = 0
        selected = menu.get_selected()
        assert selected is not None
        assert selected == menu.menu_items[0]

        menu.selected_index = 2
        selected = menu.get_selected()
        assert selected == menu.menu_items[2]

    def test_navigation_menu_highlight_current(self):
        """Test highlighting specific menu items."""
        menu = NavigationMenu()

        # Highlight contacts section
        menu.highlight_section("contacts")
        # The widget should have a way to indicate this visually

        # Highlight search section
        menu.highlight_section("search")
        # The widget should update visual indication
