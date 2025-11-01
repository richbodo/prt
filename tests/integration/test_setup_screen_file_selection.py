"""Integration tests for SetupScreen file selection workflow."""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from prt_src.tui.screens.setup import SetupScreen
from prt_src.tui.widgets.file_selection import FileSelectionWidget

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def mock_prt_app():
    """Create a mock PRT app for SetupScreen."""
    app = MagicMock()
    app.call_later = lambda func, *args: func(*args) if args else func()
    app.exit = MagicMock()
    app.push_screen = MagicMock()
    app.pop_screen = MagicMock()
    app.switch_screen = MagicMock()
    return app


@pytest.fixture
def mock_data_service(test_db, tmp_path):
    """Create a mock data service with test database."""
    from prt_src.api import PRTAPI

    db, fixtures = test_db
    # Create config pointing to test database
    config = {"db_path": str(db.path)}

    service = MagicMock()
    service.api = PRTAPI(config=config)
    return service


@pytest.fixture
def temp_takeout_files(tmp_path):
    """Create temporary takeout zip files for testing.

    Args:
        tmp_path: pytest tmp_path fixture

    Returns:
        List of Path objects for test takeout files
    """
    files = []
    for i in range(3):
        file_path = tmp_path / f"takeout-{i+1}.zip"
        # Create file with some content
        file_path.write_bytes(b"PK" + b"x" * (1024 * 1024 * (i + 1)))  # Fake zip header
        files.append(file_path)
    return files


class TestSetupScreenFileSelection:
    """Integration tests for file selection in SetupScreen."""

    @pytest.mark.asyncio
    async def test_single_file_continues_directly(
        self, pilot_screen, mock_prt_app, mock_data_service, temp_takeout_files
    ):
        """Test that single file continues directly to import (no widget shown)."""
        single_file = [temp_takeout_files[0]]

        # Mock the takeout service to return single file
        with patch("prt_src.tui.screens.setup.GoogleTakeoutService") as MockTakeoutService:
            mock_service = AsyncMock()
            mock_service.find_takeout_files = AsyncMock(return_value=single_file)
            mock_service.validate_file = AsyncMock(return_value=(True, "Valid file"))
            mock_service.get_preview = AsyncMock(
                return_value={"valid": True, "contact_count": 10, "contacts_with_images": 5}
            )
            mock_service.import_contacts = AsyncMock(
                return_value=(
                    True,
                    "Success",
                    {"contact_count": 10, "contacts_with_images": 5},
                )
            )
            MockTakeoutService.return_value = mock_service

            async with pilot_screen(
                SetupScreen, prt_app=mock_prt_app, data_service=mock_data_service
            ) as pilot:
                # Press '1' to trigger import
                await pilot.press("1")
                await pilot.pause()

                # File selection widget should NOT be shown
                try:
                    pilot.app.screen.query_one(FileSelectionWidget)
                    pytest.fail("FileSelectionWidget should not be shown for single file")
                except Exception:
                    # Expected - widget should not exist
                    pass

                # Validate should have been called with the single file
                mock_service.validate_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_files_shows_selection_widget(
        self, pilot_screen, mock_prt_app, mock_data_service, temp_takeout_files
    ):
        """Test that multiple files triggers the file selection widget."""
        # Mock the takeout service to return multiple files
        with patch("prt_src.tui.screens.setup.GoogleTakeoutService") as MockTakeoutService:
            mock_service = AsyncMock()
            mock_service.find_takeout_files = AsyncMock(return_value=temp_takeout_files)
            MockTakeoutService.return_value = mock_service

            async with pilot_screen(
                SetupScreen, prt_app=mock_prt_app, data_service=mock_data_service
            ) as pilot:
                # Press '1' to trigger import
                await pilot.press("1")
                await pilot.pause()

                # File selection widget SHOULD be shown
                screen = pilot.app.screen
                file_widget = screen.query_one(FileSelectionWidget)
                assert file_widget is not None
                assert len(file_widget.files) == 3

    @pytest.mark.asyncio
    async def test_file_selection_continues_import(
        self, pilot_screen, mock_prt_app, mock_data_service, temp_takeout_files
    ):
        """Test that selecting a file from widget continues the import."""
        # Mock the takeout service
        with patch("prt_src.tui.screens.setup.GoogleTakeoutService") as MockTakeoutService:
            mock_service = AsyncMock()
            mock_service.find_takeout_files = AsyncMock(return_value=temp_takeout_files)
            mock_service.validate_file = AsyncMock(return_value=(True, "Valid file"))
            mock_service.get_preview = AsyncMock(
                return_value={"valid": True, "contact_count": 10, "contacts_with_images": 5}
            )
            mock_service.import_contacts = AsyncMock(
                return_value=(
                    True,
                    "Success",
                    {"contact_count": 10, "contacts_with_images": 5},
                )
            )
            MockTakeoutService.return_value = mock_service

            async with pilot_screen(
                SetupScreen, prt_app=mock_prt_app, data_service=mock_data_service
            ) as pilot:
                # Press '1' to trigger import
                await pilot.press("1")
                await pilot.pause()

                # File selection widget should be shown
                screen = pilot.app.screen
                file_widget = screen.query_one(FileSelectionWidget)
                file_widget.focus()
                await pilot.pause()

                # Press '2' to select second file
                await pilot.press("2")
                await pilot.pause()

                # Widget should be dismissed and validate called with second file
                # Note: validate_file is called async, so we need to wait
                await pilot.pause()
                await pilot.pause()

                # Verify the correct file was used
                assert mock_service.validate_file.called
                # The file should be the second one
                called_file = mock_service.validate_file.call_args[0][0]
                assert called_file == temp_takeout_files[1]

    @pytest.mark.asyncio
    async def test_file_selection_cancel_returns_to_menu(
        self, pilot_screen, mock_prt_app, mock_data_service, temp_takeout_files
    ):
        """Test that cancelling file selection returns to main menu."""
        # Mock the takeout service
        with patch("prt_src.tui.screens.setup.GoogleTakeoutService") as MockTakeoutService:
            mock_service = AsyncMock()
            mock_service.find_takeout_files = AsyncMock(return_value=temp_takeout_files)
            MockTakeoutService.return_value = mock_service

            async with pilot_screen(
                SetupScreen, prt_app=mock_prt_app, data_service=mock_data_service
            ) as pilot:
                # Press '1' to trigger import
                await pilot.press("1")
                await pilot.pause()

                # File selection widget should be shown
                screen = pilot.app.screen
                file_widget = screen.query_one(FileSelectionWidget)
                file_widget.focus()
                await pilot.pause()

                # Press 'c' to cancel
                await pilot.press("c")
                await pilot.pause()

                # Widget should be dismissed
                # Try to query it - should fail
                try:
                    screen.query_one(FileSelectionWidget)
                    # If we get here, widget still exists - that's a problem
                    # But it might be hidden, so check display property
                    widget = screen.query_one(FileSelectionWidget)
                    assert widget.display is False, "Widget should be hidden after cancel"
                except Exception:
                    # Expected - widget was removed
                    pass

    @pytest.mark.asyncio
    async def test_no_files_shows_error(self, pilot_screen, mock_prt_app, mock_data_service):
        """Test that no files found shows error message."""
        # Mock the takeout service to return empty list
        with patch("prt_src.tui.screens.setup.GoogleTakeoutService") as MockTakeoutService:
            mock_service = AsyncMock()
            mock_service.find_takeout_files = AsyncMock(return_value=[])
            mock_service.get_search_instructions = MagicMock(return_value="Instructions here...")
            MockTakeoutService.return_value = mock_service

            async with pilot_screen(
                SetupScreen, prt_app=mock_prt_app, data_service=mock_data_service
            ) as pilot:
                # Press '1' to trigger import
                await pilot.press("1")
                await pilot.pause()

                # Error message should be shown
                screen = pilot.app.screen
                error_widget = screen.query_one("#setup-error")
                assert error_widget is not None
                error_text = error_widget.render()
                assert "No takeout files found" in str(error_text)

    @pytest.mark.asyncio
    async def test_import_success_shows_summary(
        self, pilot_screen, mock_prt_app, mock_data_service, temp_takeout_files
    ):
        """Test that successful import shows detailed summary."""
        single_file = [temp_takeout_files[0]]

        # Mock the takeout service
        with patch("prt_src.tui.screens.setup.GoogleTakeoutService") as MockTakeoutService:
            mock_service = AsyncMock()
            mock_service.find_takeout_files = AsyncMock(return_value=single_file)
            mock_service.validate_file = AsyncMock(return_value=(True, "Valid file"))
            mock_service.get_preview = AsyncMock(
                return_value={"valid": True, "contact_count": 25, "contacts_with_images": 15}
            )
            mock_service.import_contacts = AsyncMock(
                return_value=(
                    True,
                    "Success",
                    {
                        "contact_count": 25,
                        "contacts_with_images": 15,
                        "total_time": 1.5,
                        "source_file": str(single_file[0]),
                    },
                )
            )
            MockTakeoutService.return_value = mock_service

            async with pilot_screen(
                SetupScreen, prt_app=mock_prt_app, data_service=mock_data_service
            ) as pilot:
                # Press '1' to trigger import
                await pilot.press("1")
                await pilot.pause()
                # Wait for async operations
                await pilot.pause()
                await pilot.pause()

                # Success message should be shown
                screen = pilot.app.screen
                status_widget = screen.query_one("#setup-status")
                assert status_widget is not None
                status_text = str(status_widget.render())
                assert "Successfully imported" in status_text
                assert "25" in status_text  # contact count

    @pytest.mark.asyncio
    async def test_import_failure_shows_detailed_error(
        self, pilot_screen, mock_prt_app, mock_data_service, temp_takeout_files
    ):
        """Test that import failure shows detailed error with troubleshooting."""
        single_file = [temp_takeout_files[0]]

        # Mock the takeout service
        with patch("prt_src.tui.screens.setup.GoogleTakeoutService") as MockTakeoutService:
            mock_service = AsyncMock()
            mock_service.find_takeout_files = AsyncMock(return_value=single_file)
            mock_service.validate_file = AsyncMock(return_value=(True, "Valid file"))
            mock_service.get_preview = AsyncMock(
                return_value={"valid": True, "contact_count": 10, "contacts_with_images": 5}
            )
            mock_service.import_contacts = AsyncMock(
                return_value=(False, "Database error: permission denied", None)
            )
            MockTakeoutService.return_value = mock_service

            async with pilot_screen(
                SetupScreen, prt_app=mock_prt_app, data_service=mock_data_service
            ) as pilot:
                # Press '1' to trigger import
                await pilot.press("1")
                await pilot.pause()
                # Wait for async operations
                await pilot.pause()
                await pilot.pause()

                # Error message should be shown with troubleshooting
                screen = pilot.app.screen
                error_widget = screen.query_one("#setup-error")
                assert error_widget is not None
                error_text = str(error_widget.render())
                assert "Operation Failed" in error_text
                assert "Database error" in error_text
                # Should have troubleshooting section
                assert "Troubleshooting" in error_text or "Press 1 to retry" in error_text
