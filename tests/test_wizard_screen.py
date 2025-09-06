"""Unit tests for the first-run wizard screen."""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from prt_src.tui.screens.base import EscapeIntent
from prt_src.tui.screens.wizard import WizardScreen


class TestWizardScreen:
    """Test cases for WizardScreen."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing."""
        # Create AsyncMock for notification service since its methods are async
        notification_mock = AsyncMock()
        # Set up common async methods that return coroutines
        notification_mock.show_error = AsyncMock()
        notification_mock.show_success = AsyncMock()
        notification_mock.show_warning = AsyncMock()
        notification_mock.show_info = AsyncMock()
        notification_mock.show_confirm_dialog = AsyncMock()
        
        return {
            "nav_service": MagicMock(),
            "data_service": AsyncMock(),  # Also make data_service async since many methods are async
            "notification_service": notification_mock,
        }

    @pytest.fixture
    def wizard_screen(self, mock_services):
        """Create a WizardScreen instance for testing."""
        return WizardScreen(**mock_services)

    def test_screen_name(self, wizard_screen):
        """Test that screen returns correct name."""
        assert wizard_screen.get_screen_name() == "wizard"

    def test_initial_state(self, wizard_screen):
        """Test wizard initial state."""
        assert wizard_screen.current_step == WizardScreen.STEP_WELCOME
        assert wizard_screen.you_contact_name == ""
        assert wizard_screen.you_contact_created is False

    def test_escape_intent_welcome_step(self, wizard_screen):
        """Test ESC intent on welcome step."""
        wizard_screen.current_step = WizardScreen.STEP_WELCOME
        assert wizard_screen.on_escape() == EscapeIntent.CUSTOM

    def test_escape_intent_other_steps(self, wizard_screen):
        """Test ESC intent on other steps."""
        wizard_screen.current_step = WizardScreen.STEP_CREATE_YOU
        assert wizard_screen.on_escape() == EscapeIntent.HOME

    def test_custom_escape_welcome(self, wizard_screen):
        """Test custom escape behavior from welcome step."""
        wizard_screen.current_step = WizardScreen.STEP_WELCOME

        # Mock the _render_current_step method
        wizard_screen._render_current_step = AsyncMock()

        wizard_screen.handle_custom_escape()

        assert wizard_screen.current_step == WizardScreen.STEP_COMPLETE

    def test_header_config(self, wizard_screen):
        """Test header configuration."""
        config = wizard_screen.get_header_config()
        assert config is not None
        assert config["title"] == "Welcome to PRT"

    def test_footer_config_welcome_step(self, wizard_screen):
        """Test footer configuration for welcome step."""
        wizard_screen.current_step = WizardScreen.STEP_WELCOME
        config = wizard_screen.get_footer_config()

        assert config is not None
        assert "[Enter] Continue" in config["keyHints"]
        assert "[ESC] Skip Setup" in config["keyHints"]

    def test_footer_config_create_you_step(self, wizard_screen):
        """Test footer configuration for create you step."""
        wizard_screen.current_step = WizardScreen.STEP_CREATE_YOU
        config = wizard_screen.get_footer_config()

        assert config is not None
        assert "[Enter] Create" in config["keyHints"]
        assert "[ESC] Skip" in config["keyHints"]

    @pytest.mark.asyncio
    async def test_continue_from_welcome(self, wizard_screen):
        """Test continuing from welcome step."""
        wizard_screen._render_current_step = AsyncMock()

        await wizard_screen._continue_from_welcome()

        assert wizard_screen.current_step == WizardScreen.STEP_CREATE_YOU
        wizard_screen._render_current_step.assert_called_once()

    @pytest.mark.asyncio
    async def test_skip_to_complete(self, wizard_screen):
        """Test skipping to complete step."""
        wizard_screen._render_current_step = AsyncMock()

        await wizard_screen._skip_to_complete()

        assert wizard_screen.current_step == WizardScreen.STEP_COMPLETE
        wizard_screen._render_current_step.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_you_contact_no_name(self, wizard_screen, mock_services):
        """Test creating you contact with no name."""
        # Mock the name input
        wizard_screen.name_input = MagicMock()
        wizard_screen.name_input.value = "  "  # Empty/whitespace string

        await wizard_screen._create_you_contact()

        # Should show warning and not proceed
        mock_services["notification_service"].show_warning.assert_called_with(
            "Please enter your name"
        )

    @pytest.mark.asyncio
    async def test_create_you_contact_success(self, wizard_screen, mock_services):
        """Test successful you contact creation."""
        # Mock the name input
        wizard_screen.name_input = MagicMock()
        wizard_screen.name_input.value = "John Doe"

        # Mock the app's first_run_handler using patch of the specific attribute access
        mock_first_run_handler = MagicMock()
        mock_first_run_handler.create_you_contact.return_value = {"id": 1, "name": "John Doe"}

        # Test the logic by mocking the app interaction via monkey patching
        wizard_screen._render_current_step = AsyncMock()
        
        # Create a mock app object and temporarily assign it
        mock_app = MagicMock()
        mock_app.first_run_handler = mock_first_run_handler
        
        # Temporarily override the app property using setattr
        original_app_property = type(wizard_screen).app
        
        # Create a simple property that returns our mock
        def mock_app_property(self):
            return mock_app
        
        # Temporarily replace the app property
        type(wizard_screen).app = property(mock_app_property)
        
        try:
            await wizard_screen._create_you_contact()

            # Check that contact was created
            assert wizard_screen.you_contact_name == "John Doe"
            assert wizard_screen.you_contact_created is True
            assert wizard_screen.current_step == WizardScreen.STEP_OPTIONS

            mock_services["notification_service"].show_success.assert_called_with(
                "Welcome, John Doe!"
            )
        finally:
            # Restore the original app property
            type(wizard_screen).app = original_app_property

    @pytest.mark.asyncio
    async def test_create_you_contact_fallback_to_data_service(self, wizard_screen, mock_services):
        """Test you contact creation fallback to data service."""
        # Mock the name input
        wizard_screen.name_input = MagicMock()
        wizard_screen.name_input.value = "Jane Smith"

        # Mock app without first_run_handler using monkey patching
        wizard_screen._render_current_step = AsyncMock()
        
        # Mock data service
        mock_services["data_service"].create_contact = AsyncMock(
            return_value={"id": 2, "name": "Jane Smith"}
        )

        # Create mock app without first_run_handler to test fallback
        mock_app = MagicMock()
        # Remove the first_run_handler attribute entirely so hasattr returns False
        if hasattr(mock_app, 'first_run_handler'):
            delattr(mock_app, 'first_run_handler')
        
        # Temporarily replace the app property
        original_app_property = type(wizard_screen).app
        type(wizard_screen).app = property(lambda self: mock_app)
        
        try:
            await wizard_screen._create_you_contact()

            # Check that fallback was used
            assert wizard_screen.you_contact_name == "Jane Smith"
            assert wizard_screen.you_contact_created is True

            # Check data service was called with correct data
            expected_data = {"first_name": "Jane", "last_name": "Smith", "is_you": True}
            mock_services["data_service"].create_contact.assert_called_with(expected_data)
        finally:
            # Restore the original app property
            type(wizard_screen).app = original_app_property

    @pytest.mark.asyncio
    async def test_skip_create_you(self, wizard_screen):
        """Test skipping you contact creation."""
        wizard_screen._render_current_step = AsyncMock()

        await wizard_screen._skip_create_you()

        assert wizard_screen.current_step == WizardScreen.STEP_OPTIONS
        wizard_screen._render_current_step.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_import_takeout(self, wizard_screen, mock_services):
        """Test handling import takeout option."""
        # Mock app.switch_screen using monkey patching
        mock_app = MagicMock()
        mock_app.switch_screen = AsyncMock()
        
        # Temporarily replace the app property
        original_app_property = type(wizard_screen).app
        type(wizard_screen).app = property(lambda self: mock_app)
        
        try:
            await wizard_screen._handle_import_takeout()

            mock_services["notification_service"].show_info.assert_called_with(
                "Navigating to import screen..."
            )
            mock_services["nav_service"].push.assert_called_with("import")
            mock_app.switch_screen.assert_called_with("import")
        finally:
            # Restore the original app property
            type(wizard_screen).app = original_app_property

    @pytest.mark.asyncio
    async def test_handle_load_demo_success(self, wizard_screen, mock_services):
        """Test loading demo data successfully."""
        wizard_screen._render_current_step = AsyncMock()

        # Mock data service and API
        mock_api = MagicMock()
        mock_services["data_service"].api = mock_api
        mock_api.db = MagicMock()

        # Mock fixture creation
        with patch("tests.fixtures.create_fixture_data") as mock_create_fixture:
            mock_create_fixture.return_value = {"contacts": ["contact1", "contact2"]}

            await wizard_screen._handle_load_demo()

        assert wizard_screen.current_step == WizardScreen.STEP_COMPLETE
        mock_services["notification_service"].show_success.assert_called_with(
            "Loaded 2 demo contacts with relationships!"
        )

    @pytest.mark.asyncio
    async def test_handle_load_demo_failure(self, wizard_screen, mock_services):
        """Test loading demo data failure."""
        wizard_screen._render_current_step = AsyncMock()

        # Mock data service without API
        mock_services["data_service"].api = None

        await wizard_screen._handle_load_demo()

        # Should still proceed to complete step even on error
        assert wizard_screen.current_step == WizardScreen.STEP_COMPLETE

    @pytest.mark.asyncio
    async def test_handle_start_empty(self, wizard_screen, mock_services):
        """Test starting with empty database."""
        wizard_screen._render_current_step = AsyncMock()

        await wizard_screen._handle_start_empty()

        assert wizard_screen.current_step == WizardScreen.STEP_COMPLETE
        mock_services["notification_service"].show_info.assert_called_with(
            "Starting with empty database"
        )

    @pytest.mark.asyncio
    async def test_finish_wizard(self, wizard_screen, mock_services):
        """Test finishing the wizard."""
        # Mock app.switch_screen using monkey patching
        mock_app = MagicMock()
        mock_app.switch_screen = AsyncMock()
        
        # Temporarily replace the app property
        original_app_property = type(wizard_screen).app
        type(wizard_screen).app = property(lambda self: mock_app)
        
        try:
            await wizard_screen._finish_wizard()

            mock_services["notification_service"].show_success.assert_called_with(
                "Setup complete! Welcome to PRT!"
            )
            mock_services["nav_service"].go_home.assert_called_once()
            mock_app.switch_screen.assert_called_with("home")
        finally:
            # Restore the original app property
            type(wizard_screen).app = original_app_property

    @pytest.mark.asyncio
    async def test_handle_enter_welcome_step(self, wizard_screen):
        """Test handling Enter key on welcome step."""
        wizard_screen.current_step = WizardScreen.STEP_WELCOME
        wizard_screen._continue_from_welcome = AsyncMock()

        await wizard_screen._handle_enter()

        wizard_screen._continue_from_welcome.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_enter_create_you_step(self, wizard_screen):
        """Test handling Enter key on create you step."""
        wizard_screen.current_step = WizardScreen.STEP_CREATE_YOU
        wizard_screen._create_you_contact = AsyncMock()

        await wizard_screen._handle_enter()

        wizard_screen._create_you_contact.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_enter_complete_step(self, wizard_screen):
        """Test handling Enter key on complete step."""
        wizard_screen.current_step = WizardScreen.STEP_COMPLETE
        wizard_screen._finish_wizard = AsyncMock()

        await wizard_screen._handle_enter()

        wizard_screen._finish_wizard.assert_called_once()

    def test_step_constants(self):
        """Test that step constants are defined correctly."""
        assert WizardScreen.STEP_WELCOME == 0
        assert WizardScreen.STEP_CREATE_YOU == 1
        assert WizardScreen.STEP_OPTIONS == 2
        assert WizardScreen.STEP_COMPLETE == 3

    @pytest.mark.asyncio
    async def test_render_current_step_calls_correct_method(self, wizard_screen):
        """Test that _render_current_step calls the correct render method for each step."""
        # Mock the content container
        wizard_screen.content_container = MagicMock()
        wizard_screen.content_container.remove_children = AsyncMock()

        # Mock all render methods
        wizard_screen._render_welcome_step = AsyncMock()
        wizard_screen._render_create_you_step = AsyncMock()
        wizard_screen._render_options_step = AsyncMock()
        wizard_screen._render_complete_step = AsyncMock()

        # Test each step
        wizard_screen.current_step = WizardScreen.STEP_WELCOME
        await wizard_screen._render_current_step()
        wizard_screen._render_welcome_step.assert_called_once()

        wizard_screen.current_step = WizardScreen.STEP_CREATE_YOU
        await wizard_screen._render_current_step()
        wizard_screen._render_create_you_step.assert_called_once()

        wizard_screen.current_step = WizardScreen.STEP_OPTIONS
        await wizard_screen._render_current_step()
        wizard_screen._render_options_step.assert_called_once()

        wizard_screen.current_step = WizardScreen.STEP_COMPLETE
        await wizard_screen._render_current_step()
        wizard_screen._render_complete_step.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_you_contact_error_handling(self, wizard_screen, mock_services):
        """Test error handling during you contact creation."""
        # Mock the name input
        wizard_screen.name_input = MagicMock()
        wizard_screen.name_input.value = "John Doe"

        # Mock app to raise an exception using monkey patching
        mock_first_run_handler = MagicMock()
        mock_first_run_handler.create_you_contact.side_effect = Exception("Database error")
        
        mock_app = MagicMock()
        mock_app.first_run_handler = mock_first_run_handler
        
        # Temporarily replace the app property
        original_app_property = type(wizard_screen).app
        type(wizard_screen).app = property(lambda self: mock_app)
        
        try:
            await wizard_screen._create_you_contact()

            # Should show error notification
            mock_services["notification_service"].show_error.assert_called_with(
                "Failed to create your profile"
            )
        finally:
            # Restore the original app property
            type(wizard_screen).app = original_app_property

    @pytest.mark.asyncio
    async def test_create_you_contact_single_name(self, wizard_screen, mock_services):
        """Test creating you contact with single name."""
        # Mock the name input
        wizard_screen.name_input = MagicMock()
        wizard_screen.name_input.value = "Madonna"

        # Mock app without first_run_handler (fallback to data service)
        mock_services["data_service"].create_contact = AsyncMock(
            return_value={"id": 1, "name": "Madonna"}
        )
        wizard_screen._render_current_step = AsyncMock()

        # Create mock app without first_run_handler to test fallback
        mock_app = MagicMock()
        # Remove the first_run_handler attribute entirely so hasattr returns False
        if hasattr(mock_app, 'first_run_handler'):
            delattr(mock_app, 'first_run_handler')
        
        # Temporarily replace the app property
        original_app_property = type(wizard_screen).app
        type(wizard_screen).app = property(lambda self: mock_app)
        
        try:
            await wizard_screen._create_you_contact()

            # Check data service was called with single name
            expected_data = {"first_name": "Madonna", "last_name": "", "is_you": True}
            mock_services["data_service"].create_contact.assert_called_with(expected_data)
        finally:
            # Restore the original app property
            type(wizard_screen).app = original_app_property

    @pytest.mark.asyncio
    async def test_on_show_reset_on_first_run(self, wizard_screen):
        """Test that on_show resets to welcome if on complete step and no contact created."""
        wizard_screen.current_step = WizardScreen.STEP_COMPLETE
        wizard_screen.you_contact_created = False
        wizard_screen._render_current_step = AsyncMock()

        await wizard_screen.on_show()

        assert wizard_screen.current_step == WizardScreen.STEP_WELCOME
        wizard_screen._render_current_step.assert_called_once()
