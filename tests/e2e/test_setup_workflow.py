"""End-to-end tests for setup workflow in TUI app."""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

# Mark all tests in this module as e2e tests
pytestmark = pytest.mark.e2e


@pytest.fixture
def temp_takeout_file(tmp_path):
    """Create a temporary takeout zip file.

    Args:
        tmp_path: pytest tmp_path fixture

    Returns:
        Path to test takeout file
    """
    file_path = tmp_path / "takeout-test.zip"
    # Create file with fake zip header
    file_path.write_bytes(b"PK" + b"x" * (1024 * 1024))  # 1MB fake zip
    return file_path


@pytest.fixture
def multiple_takeout_files(tmp_path):
    """Create multiple temporary takeout zip files.

    Args:
        tmp_path: pytest tmp_path fixture

    Returns:
        List of Path objects for test takeout files
    """
    files = []
    for i in range(3):
        file_path = tmp_path / f"takeout-{i+1}.zip"
        file_path.write_bytes(b"PK" + b"x" * (1024 * 1024 * (i + 1)))
        files.append(file_path)
    return files


class TestSetupWorkflowE2E:
    """End-to-end tests for complete setup workflows."""

    @pytest.mark.asyncio
    async def test_empty_db_shows_setup_screen_on_start(self, test_db_empty):
        """Test that empty database triggers setup screen automatically."""
        from textual.app import App

        from prt_src.tui.screens.setup import SetupScreen
        from prt_src.tui.services.data import DataService

        # Create a minimal test app that mimics PRTApp behavior
        class TestPRTApp(App):
            def __init__(self):
                super().__init__()
                self.data_service = DataService(api=None)
                self.data_service.api = MagicMock()
                self.data_service.api.db = test_db_empty
                self._setup_shown = False

            def on_mount(self):
                # Simulate empty DB check
                contact_count = 0  # Empty DB
                if contact_count == 0:
                    self.push_screen(SetupScreen(prt_app=self, data_service=self.data_service))
                    self._setup_shown = True

        app = TestPRTApp()
        async with app.run_test() as pilot:
            # Setup screen should be shown
            assert app._setup_shown is True
            assert isinstance(pilot.app.screen, SetupScreen)

    @pytest.mark.asyncio
    async def test_setup_flag_forces_setup_screen(self):
        """Test that --setup flag forces setup screen even with existing data."""
        from textual.app import App

        from prt_src.tui.screens.setup import SetupScreen

        # Create a minimal test app with force_setup flag
        class TestPRTApp(App):
            def __init__(self, force_setup=False):
                super().__init__()
                self.force_setup = force_setup
                self._setup_shown = False

            def on_mount(self):
                if self.force_setup:
                    self.push_screen(SetupScreen(prt_app=self))
                    self._setup_shown = True

        app = TestPRTApp(force_setup=True)
        async with app.run_test() as pilot:
            # Setup screen should be shown due to flag
            assert app._setup_shown is True
            assert isinstance(pilot.app.screen, SetupScreen)

    @pytest.mark.asyncio
    async def test_import_menu_option_triggers_workflow(self, test_db_empty, temp_takeout_file):
        """Test that pressing '1' triggers import workflow initialization."""
        from textual.app import App

        from prt_src.tui.screens.setup import SetupScreen
        from prt_src.tui.services.data import DataService

        class TestPRTApp(App):
            def __init__(self):
                super().__init__()
                self.data_service = DataService(api=None)
                self.data_service.api = MagicMock()
                self.data_service.api.db = test_db_empty
                self.import_triggered = False

                # Track if import workflow was triggered
                def async_call_later(func, *args):
                    if func.__name__ == "_handle_import_takeout":
                        self.import_triggered = True

                self.call_later = async_call_later

            def on_mount(self):
                self.push_screen(SetupScreen(prt_app=self, data_service=self.data_service))

        app = TestPRTApp()
        async with app.run_test() as pilot:
            # Verify we're on setup screen
            assert isinstance(pilot.app.screen, SetupScreen)

            # Press '1' to start import
            await pilot.press("1")
            await pilot.pause()

            # Import workflow should have been triggered
            assert app.import_triggered is True

    @pytest.mark.asyncio
    async def test_multiple_files_triggers_selection_widget(
        self, test_db_empty, multiple_takeout_files
    ):
        """Test that multiple files triggers file selection widget."""
        # Note: This test is covered more thoroughly in integration tests
        # This E2E test just verifies the basic flow starts correctly
        from textual.app import App

        from prt_src.tui.screens.setup import SetupScreen
        from prt_src.tui.services.data import DataService

        class TestPRTApp(App):
            def __init__(self):
                super().__init__()
                self.data_service = DataService(api=None)
                self.data_service.api = MagicMock()
                self.data_service.api.db = test_db_empty

            def on_mount(self):
                self.push_screen(SetupScreen(prt_app=self, data_service=self.data_service))

        # Mock the Google Takeout service
        with patch("prt_src.tui.screens.setup.GoogleTakeoutService") as MockTakeoutService:
            mock_service = AsyncMock()
            mock_service.find_takeout_files = AsyncMock(return_value=multiple_takeout_files)
            MockTakeoutService.return_value = mock_service

            app = TestPRTApp()
            async with app.run_test() as pilot:
                # Verify we're on setup screen
                assert isinstance(pilot.app.screen, SetupScreen)

                # Press '1' to start import
                await pilot.press("1")
                await pilot.pause()

                # Should have searched for files
                assert mock_service.find_takeout_files.called

    @pytest.mark.asyncio
    async def test_fixture_load_workflow_starts(self, test_db_empty):
        """Test that fixture load workflow starts correctly from setup screen."""
        from textual.app import App

        from prt_src.tui.screens.setup import SetupScreen
        from prt_src.tui.services.data import DataService

        class TestPRTApp(App):
            def __init__(self):
                super().__init__()
                self.data_service = DataService(api=None)
                self.data_service.api = MagicMock()
                self.data_service.api.db = test_db_empty
                self.fixture_triggered = False

                def async_call_later(func, *args):
                    self.fixture_triggered = True

                self.call_later = async_call_later

            def on_mount(self):
                self.push_screen(SetupScreen(prt_app=self, data_service=self.data_service))

        # Mock the Fixture service
        with patch("prt_src.tui.screens.setup.FixtureService") as MockFixtureService:
            mock_service = MagicMock()
            mock_service.get_fixture_summary = MagicMock(
                return_value={"contacts": 7, "tags": 8, "notes": 6}
            )
            mock_service.clear_and_load_fixtures = AsyncMock(
                return_value={
                    "success": True,
                    "contacts": 7,
                    "tags": 8,
                    "notes": 6,
                    "total_time": 0.5,
                }
            )
            MockFixtureService.return_value = mock_service

            app = TestPRTApp()
            async with app.run_test() as pilot:
                # Verify we're on setup screen
                assert isinstance(pilot.app.screen, SetupScreen)

                # Press '2' to load fixtures
                await pilot.press("2")
                await pilot.pause()

                # Fixture workflow should have been triggered
                # The actual async execution is tested in integration tests
                assert app.fixture_triggered or mock_service.get_fixture_summary.called

    @pytest.mark.asyncio
    async def test_setup_quit_exits_app(self):
        """Test that pressing 'q' on setup screen exits the app."""
        from textual.app import App

        from prt_src.tui.screens.setup import SetupScreen

        class TestPRTApp(App):
            def __init__(self):
                super().__init__()
                self.exit_called = False

            def on_mount(self):
                self.push_screen(SetupScreen(prt_app=self))

            def exit(self, *args, **kwargs):
                self.exit_called = True

        app = TestPRTApp()
        async with app.run_test() as pilot:
            # Press 'q' to quit
            await pilot.press("q")
            await pilot.pause()

            # Exit should have been called
            assert app.exit_called is True


class TestSetupWorkflowErrorHandling:
    """E2E tests for error handling in setup workflows."""

    @pytest.mark.asyncio
    async def test_import_validation_failure_shows_error(self, test_db_empty, temp_takeout_file):
        """Test that validation failure shows proper error."""
        from textual.app import App

        from prt_src.tui.screens.setup import SetupScreen
        from prt_src.tui.services.data import DataService

        class TestPRTApp(App):
            def __init__(self):
                super().__init__()
                self.data_service = DataService(api=None)
                self.data_service.api = MagicMock()
                self.data_service.api.db = test_db_empty

            def on_mount(self):
                self.push_screen(SetupScreen(prt_app=self, data_service=self.data_service))

        with patch("prt_src.tui.screens.setup.GoogleTakeoutService") as MockTakeoutService:
            mock_service = AsyncMock()
            mock_service.find_takeout_files = AsyncMock(return_value=[temp_takeout_file])
            mock_service.validate_file = AsyncMock(return_value=(False, "Invalid zip file"))
            MockTakeoutService.return_value = mock_service

            app = TestPRTApp()
            async with app.run_test() as pilot:
                # Press '1' to start import
                await pilot.press("1")
                await pilot.pause()
                await pilot.pause()

                # Error should be shown
                screen = pilot.app.screen
                error_widget = screen.query_one("#setup-error")
                error_text = str(error_widget.render())
                assert "Invalid" in error_text

    @pytest.mark.asyncio
    async def test_fixture_load_failure_shows_error(self, test_db_empty):
        """Test that fixture load failure shows proper error."""
        from textual.app import App

        from prt_src.tui.screens.setup import SetupScreen
        from prt_src.tui.services.data import DataService

        class TestPRTApp(App):
            def __init__(self):
                super().__init__()
                self.data_service = DataService(api=None)
                self.data_service.api = MagicMock()
                self.data_service.api.db = test_db_empty

            def on_mount(self):
                self.push_screen(SetupScreen(prt_app=self, data_service=self.data_service))

        # Mock the actual function used in setup.py
        with patch("prt_src.fixture_manager.setup_fixture_mode") as mock_setup_fixture, patch(
            "prt_src.fixture_manager.get_fixture_summary"
        ) as mock_summary:
            mock_summary.return_value = {"contacts": 7, "tags": 8, "notes": 6}
            mock_setup_fixture.return_value = None  # Return None to trigger failure

            app = TestPRTApp()
            async with app.run_test() as pilot:
                # Press '2' to load fixtures
                await pilot.press("2")
                await pilot.pause()
                await pilot.pause()

                # Error should be shown
                screen = pilot.app.screen
                error_widget = screen.query_one("#setup-error")
                error_text = str(error_widget.render())
                assert "Failed to create fixture database" in error_text
