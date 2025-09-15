"""Tests for import and export screens."""

import importlib
from pathlib import Path
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import mock_open
from unittest.mock import patch

import pytest

from prt_src.tui.screens.base import EscapeIntent

import_screen_module = importlib.import_module("prt_src.tui.screens.import")
export_screen_module = importlib.import_module("prt_src.tui.screens.export")

ImportScreen = import_screen_module.ImportScreen
ExportScreen = export_screen_module.ExportScreen


class TestImportScreen:
    """Test cases for ImportScreen."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing."""
        nav_service = MagicMock()
        data_service = AsyncMock()
        data_service.api = MagicMock()
        notification_service = AsyncMock()
        selection_service = MagicMock()
        validation_service = MagicMock()

        return {
            "nav_service": nav_service,
            "data_service": data_service,
            "notification_service": notification_service,
            "selection_service": selection_service,
            "validation_service": validation_service,
        }

    @pytest.fixture
    def sample_takeout_data(self):
        """Sample Google Takeout data for testing."""
        return {
            "valid": True,
            "contact_count": 25,
            "image_count": 10,
            "contacts_with_images": 8,
            "sample_contacts": [
                {"name": "John Doe", "has_image": True},
                {"name": "Jane Smith", "has_image": False},
                {"name": "Bob Wilson", "has_image": True},
            ],
            "message": "Found 25 contact files and 10 images",
        }

    @pytest.fixture
    def sample_contacts_data(self):
        """Sample processed contacts data."""
        return [
            {
                "first": "John",
                "last": "Doe",
                "emails": ["john@example.com"],
                "phones": ["+1234567890"],
                "profile_image": b"fake_image_data",
                "profile_image_filename": "john_doe.jpg",
                "profile_image_mime_type": "image/jpeg",
            },
            {
                "first": "Jane",
                "last": "Smith",
                "emails": ["jane@example.com"],
                "phones": [],
                "profile_image": None,
                "profile_image_filename": None,
                "profile_image_mime_type": None,
            },
        ]

    def test_screen_initialization(self, mock_services):
        """Test screen initialization."""
        screen = ImportScreen(**mock_services)

        assert screen.get_screen_name() == "import"
        assert screen._import_path is None
        assert screen._preview_info is None
        assert screen._import_complete is False
        assert screen._import_results is None
        assert screen._is_importing is False

    def test_escape_intent_normal(self, mock_services):
        """Test escape intent when not importing."""
        screen = ImportScreen(**mock_services)
        assert screen.on_escape() == EscapeIntent.POP

    def test_escape_intent_during_import(self, mock_services):
        """Test escape intent during import."""
        screen = ImportScreen(**mock_services)
        screen._is_importing = True
        assert screen.on_escape() == EscapeIntent.CUSTOM

    def test_header_config(self, mock_services):
        """Test header configuration."""
        screen = ImportScreen(**mock_services)
        config = screen.get_header_config()

        assert config["title"] == "Import Contacts"

    def test_footer_config_normal(self, mock_services):
        """Test footer configuration in normal state."""
        screen = ImportScreen(**mock_services)
        config = screen.get_footer_config()

        assert "[i]mport" in config["keyHints"]
        assert "[p]review" in config["keyHints"]
        assert "[ESC] Back" in config["keyHints"]

    def test_footer_config_importing(self, mock_services):
        """Test footer configuration during import."""
        screen = ImportScreen(**mock_services)
        screen._is_importing = True
        config = screen.get_footer_config()

        assert "Import in progress..." in config["keyHints"]

    def test_footer_config_complete(self, mock_services):
        """Test footer configuration when import is complete."""
        screen = ImportScreen(**mock_services)
        screen._import_complete = True
        config = screen.get_footer_config()

        assert "[h]ome" in config["keyHints"]
        assert "[c]ontacts" in config["keyHints"]
        assert "[ESC] Back" in config["keyHints"]

    @patch("prt_src.tui.screens.import.Path")
    @pytest.mark.asyncio
    async def test_file_path_validation_nonexistent_file(self, mock_path, mock_services):
        """Test file path validation for non-existent file."""
        # Mock Path behavior
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = False
        mock_path.return_value = mock_path_instance

        screen = ImportScreen(**mock_services)
        # Mock the UI components
        with patch.object(screen, "query_one") as mock_query:
            mock_status = MagicMock()
            mock_query.return_value = mock_status

            # Simulate input change event
            event = MagicMock()
            event.value = "/nonexistent/file.zip"

            await screen.on_file_path_changed(event)

            # Verify error status was shown
            mock_status.update.assert_called_with("❌ File does not exist")

    @patch("prt_src.tui.screens.import.Path")
    @pytest.mark.asyncio
    async def test_file_path_validation_not_zip(self, mock_path, mock_services):
        """Test file path validation for non-zip file."""
        # Mock Path behavior
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.is_file.return_value = True
        mock_path_instance.suffix.lower.return_value = ".txt"
        mock_path.return_value = mock_path_instance

        screen = ImportScreen(**mock_services)
        # Mock the UI components and validation method
        with patch.object(screen, "query_one") as mock_query, patch.object(
            screen, "_validate_takeout_file"
        ):

            mock_status = MagicMock()
            mock_query.return_value = mock_status

            # Simulate input change event
            event = MagicMock()
            event.value = "/path/to/file.txt"

            await screen.on_file_path_changed(event)

            # Verify warning status was shown
            mock_status.update.assert_called_with("⚠️ File should be a ZIP archive")

    @patch("prt_src.tui.screens.import.GoogleTakeoutParser")
    @pytest.mark.asyncio
    async def test_validate_takeout_file_valid(
        self, mock_parser_class, mock_services, sample_takeout_data
    ):
        """Test takeout file validation for valid file."""
        # Mock parser
        mock_parser = MagicMock()
        mock_parser.get_preview_info.return_value = sample_takeout_data
        mock_parser_class.return_value = mock_parser

        screen = ImportScreen(**mock_services)
        screen._import_path = "/path/to/valid.zip"

        # Mock UI components
        with patch.object(screen, "query_one") as mock_query, patch.object(
            screen, "_show_preview"
        ) as mock_show_preview:

            mock_status = MagicMock()
            mock_query.return_value = mock_status

            await screen._validate_takeout_file()

            # Verify success status and preview shown
            mock_status.update.assert_called_with("✅ Valid Google Takeout file")
            mock_show_preview.assert_called_once()
            assert screen._preview_info == sample_takeout_data

    @patch("prt_src.tui.screens.import.GoogleTakeoutParser")
    @pytest.mark.asyncio
    async def test_validate_takeout_file_invalid(self, mock_parser_class, mock_services):
        """Test takeout file validation for invalid file."""
        # Mock parser with invalid result
        invalid_data = {"valid": False, "error": "No Contacts directory found"}
        mock_parser = MagicMock()
        mock_parser.get_preview_info.return_value = invalid_data
        mock_parser_class.return_value = mock_parser

        screen = ImportScreen(**mock_services)
        screen._import_path = "/path/to/invalid.zip"

        # Mock UI components
        with patch.object(screen, "query_one") as mock_query, patch.object(
            screen, "_clear_preview"
        ) as mock_clear_preview:

            mock_status = MagicMock()
            mock_query.return_value = mock_status

            await screen._validate_takeout_file()

            # Verify error status and preview cleared
            mock_status.update.assert_called_with("❌ No Contacts directory found")
            mock_clear_preview.assert_called_once()

    @patch("prt_src.tui.screens.import.parse_takeout_contacts")
    @patch("prt_src.tui.screens.import.asyncio.sleep")
    @pytest.mark.asyncio
    async def test_perform_import_success(
        self, mock_sleep, mock_parse, mock_services, sample_contacts_data
    ):
        """Test successful import operation."""
        # Mock parse_takeout_contacts
        import_info = {
            "contact_count": len(sample_contacts_data),
            "duplicates_removed": 2,
            "raw_contact_count": len(sample_contacts_data) + 2,
        }
        mock_parse.return_value = (sample_contacts_data, import_info)

        # Mock data service
        mock_services["data_service"].api.insert_contacts.return_value = True

        screen = ImportScreen(**mock_services)
        screen._import_path = "/path/to/test.zip"
        screen._preview_info = {"valid": True}

        # Mock UI components
        with patch.object(screen, "query_one") as mock_query, patch.object(
            screen, "_show_import_results"
        ) as mock_show_results:

            mock_progress = MagicMock()
            mock_status = MagicMock()
            mock_progress_section = MagicMock()
            mock_preview_section = MagicMock()

            # Configure query_one to return appropriate mocks
            def query_side_effect(selector, widget_type=None):
                if selector == "#import-progress":
                    return mock_progress
                elif selector == "#progress-status":
                    return mock_status
                elif selector == "#progress-section":
                    return mock_progress_section
                elif selector == "#preview-section":
                    return mock_preview_section
                return MagicMock()

            mock_query.side_effect = query_side_effect

            await screen._perform_import()

            # Verify import was successful
            assert screen._import_complete is True
            assert screen._import_results is not None
            assert screen._import_results["success"] is True
            assert screen._import_results["contacts_imported"] == len(sample_contacts_data)
            mock_show_results.assert_called_once()

    def test_show_preview(self, mock_services, sample_takeout_data):
        """Test showing preview information."""
        screen = ImportScreen(**mock_services)
        screen._preview_info = sample_takeout_data

        with patch.object(screen, "query_one") as mock_query:
            mock_preview_widget = MagicMock()
            mock_section = MagicMock()

            def query_side_effect(selector):
                if selector == "#preview-info":
                    return mock_preview_widget
                elif selector == "#preview-section":
                    return mock_section
                return MagicMock()

            mock_query.side_effect = query_side_effect

            screen._show_preview()

            # Verify preview was updated
            mock_preview_widget.update.assert_called_once()
            assert mock_section.display is True

            # Check preview text contains expected information
            preview_text = mock_preview_widget.update.call_args[0][0]
            assert "Found 25 contacts and 10 images" in preview_text
            assert "John Doe" in preview_text
            assert "Jane Smith" in preview_text

    def test_clear_import_state(self, mock_services):
        """Test clearing import state."""
        screen = ImportScreen(**mock_services)

        # Set some state
        screen._import_path = "/path/to/file.zip"
        screen._preview_info = {"valid": True}
        screen._import_complete = True
        screen._import_results = {"success": True}
        screen._is_importing = True

        with patch.object(screen, "query_one") as mock_query, patch.object(
            screen, "_hide_sections"
        ) as mock_hide:

            mock_input = MagicMock()
            mock_status = MagicMock()

            def query_side_effect(selector):
                if selector == "#file-path-input":
                    return mock_input
                elif selector == "#file-status":
                    return mock_status
                return MagicMock()

            mock_query.side_effect = query_side_effect

            screen._clear_import_state()

            # Verify state was cleared
            assert screen._import_path is None
            assert screen._preview_info is None
            assert screen._import_complete is False
            assert screen._import_results is None
            assert screen._is_importing is False

            # Verify UI was cleared
            mock_input.value = ""
            mock_status.update.assert_called_with("")
            mock_hide.assert_called_once()


class TestExportScreen:
    """Test cases for ExportScreen."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing."""
        nav_service = MagicMock()
        data_service = AsyncMock()
        data_service.api = MagicMock()
        notification_service = AsyncMock()
        selection_service = MagicMock()
        validation_service = MagicMock()

        return {
            "nav_service": nav_service,
            "data_service": data_service,
            "notification_service": notification_service,
            "selection_service": selection_service,
            "validation_service": validation_service,
        }

    @pytest.fixture
    def sample_export_data(self):
        """Sample export data for testing."""
        return {
            "contacts": [
                {"id": 1, "name": "John Doe", "email": "john@example.com", "phone": "+1234567890"},
                {
                    "id": 2,
                    "name": "Jane Smith",
                    "email": "jane@example.com",
                    "phone": "+9876543210",
                },
            ],
            "tags": [
                {"id": 1, "name": "friend", "contact_count": 1},
                {"id": 2, "name": "colleague", "contact_count": 1},
            ],
            "notes": [],
            "relationships": [],
            "export_info": {
                "timestamp": "2023-12-01T12:00:00",
                "format": "json",
                "scope": "all",
                "source": "PRT Export Screen",
            },
        }

    def test_screen_initialization(self, mock_services):
        """Test screen initialization."""
        screen = ExportScreen(**mock_services)

        assert screen.get_screen_name() == "export"
        assert screen._export_complete is False
        assert screen._export_results is None
        assert screen._is_exporting is False
        assert screen._current_search_results is None
        assert screen._available_tags == []

    def test_escape_intent_normal(self, mock_services):
        """Test escape intent when not exporting."""
        screen = ExportScreen(**mock_services)
        assert screen.on_escape() == EscapeIntent.POP

    def test_escape_intent_during_export(self, mock_services):
        """Test escape intent during export."""
        screen = ExportScreen(**mock_services)
        screen._is_exporting = True
        assert screen.on_escape() == EscapeIntent.CUSTOM

    def test_header_config(self, mock_services):
        """Test header configuration."""
        screen = ExportScreen(**mock_services)
        config = screen.get_header_config()

        assert config["title"] == "Export Data"

    def test_footer_config_normal(self, mock_services):
        """Test footer configuration in normal state."""
        screen = ExportScreen(**mock_services)
        config = screen.get_footer_config()

        assert "[e]xport" in config["keyHints"]
        assert "[ESC] Back" in config["keyHints"]

    def test_footer_config_exporting(self, mock_services):
        """Test footer configuration during export."""
        screen = ExportScreen(**mock_services)
        screen._is_exporting = True
        config = screen.get_footer_config()

        assert "Export in progress..." in config["keyHints"]

    def test_footer_config_complete(self, mock_services):
        """Test footer configuration when export is complete."""
        screen = ExportScreen(**mock_services)
        screen._export_complete = True
        config = screen.get_footer_config()

        assert "[o]pen folder" in config["keyHints"]
        assert "[e]xport another" in config["keyHints"]
        assert "[ESC] Back" in config["keyHints"]

    @pytest.mark.asyncio
    async def test_load_available_tags(self, mock_services):
        """Test loading available tags."""
        # Mock tags data
        tags_data = [{"name": "friend"}, {"name": "colleague"}, {"name": "family"}]
        mock_services["data_service"].get_tags.return_value = tags_data

        screen = ExportScreen(**mock_services)

        await screen._load_available_tags()

        assert screen._available_tags == ["friend", "colleague", "family"]

    def test_scope_changed_to_tag(self, mock_services):
        """Test scope selection change to tag filtering."""
        screen = ExportScreen(**mock_services)

        with patch.object(screen, "query_one") as mock_query:
            mock_container = MagicMock()
            mock_query.return_value = mock_container

            # Mock event for tag scope selection
            event = MagicMock()
            event.pressed.id = "scope-tag"

            screen.on_scope_changed(event)

            # Verify tag selection container is shown
            assert mock_container.display is True

    def test_scope_changed_to_all(self, mock_services):
        """Test scope selection change to all contacts."""
        screen = ExportScreen(**mock_services)

        with patch.object(screen, "query_one") as mock_query:
            mock_container = MagicMock()
            mock_query.return_value = mock_container

            # Mock event for all scope selection
            event = MagicMock()
            event.pressed.id = "scope-all"

            screen.on_scope_changed(event)

            # Verify tag selection container is hidden
            assert mock_container.display is False

    def test_format_changed_to_html(self, mock_services):
        """Test format selection change to HTML."""
        screen = ExportScreen(**mock_services)

        with patch.object(screen, "query_one") as mock_query:
            mock_checkbox = MagicMock()
            mock_query.return_value = mock_checkbox

            # Mock event for HTML format selection
            event = MagicMock()
            event.pressed.id = "format-html"

            screen.on_format_changed(event)

            # Verify directory generation checkbox is enabled
            assert mock_checkbox.disabled is False

    def test_format_changed_to_json(self, mock_services):
        """Test format selection change to JSON."""
        screen = ExportScreen(**mock_services)

        with patch.object(screen, "query_one") as mock_query:
            mock_checkbox = MagicMock()
            mock_query.return_value = mock_checkbox

            # Mock event for JSON format selection
            event = MagicMock()
            event.pressed.id = "format-json"

            screen.on_format_changed(event)

            # Verify directory generation checkbox is disabled
            assert mock_checkbox.disabled is True
            assert mock_checkbox.value is False

    @pytest.mark.asyncio
    async def test_tag_input_validation_valid(self, mock_services):
        """Test tag input validation for valid tag."""
        screen = ExportScreen(**mock_services)
        screen._available_tags = ["friend", "colleague", "family"]

        with patch.object(screen, "query_one") as mock_query:
            mock_status = MagicMock()
            mock_query.return_value = mock_status

            # Mock event for valid tag input
            event = MagicMock()
            event.value = "friend"

            await screen.on_tag_input_changed(event)

            # Verify success status
            mock_status.update.assert_called_with("✅ Tag found")

    @pytest.mark.asyncio
    async def test_tag_input_validation_invalid(self, mock_services):
        """Test tag input validation for invalid tag."""
        screen = ExportScreen(**mock_services)
        screen._available_tags = ["friend", "colleague", "family"]

        with patch.object(screen, "query_one") as mock_query:
            mock_status = MagicMock()
            mock_query.return_value = mock_status

            # Mock event for invalid tag input
            event = MagicMock()
            event.value = "nonexistent"

            await screen.on_tag_input_changed(event)

            # Verify error status
            mock_status.update.assert_called_with("❌ Tag not found")

    @pytest.mark.asyncio
    async def test_get_export_config_json_all(self, mock_services):
        """Test getting export config for JSON format, all contacts."""
        screen = ExportScreen(**mock_services)

        with patch.object(screen, "query_one") as mock_query:
            # Mock UI components
            mock_format_radio = MagicMock()
            mock_format_radio.pressed.id = "format-json"

            mock_scope_radio = MagicMock()
            mock_scope_radio.pressed.id = "scope-all"

            mock_checkbox_true = MagicMock()
            mock_checkbox_true.value = True

            mock_input = MagicMock()
            mock_input.value = "/test/export/path"

            def query_side_effect(selector, widget_type=None):
                if selector == "#format-selection":
                    return mock_format_radio
                elif selector == "#scope-selection":
                    return mock_scope_radio
                elif selector in [
                    "#include-images",
                    "#generate-directory",
                    "#include-relationships",
                    "#include-metadata",
                ]:
                    return mock_checkbox_true
                elif selector == "#output-path-input":
                    return mock_input
                return MagicMock()

            mock_query.side_effect = query_side_effect

            config = await screen._get_export_config()

            assert config is not None
            assert config["format"] == "json"
            assert config["scope"] == "all"
            assert config["scope_filter"] is None
            assert config["include_images"] is True
            assert config["generate_directory"] is False  # Should be False for JSON
            assert config["include_relationships"] is True
            assert config["include_metadata"] is True
            assert config["output_path"] == "/test/export/path"

    @pytest.mark.asyncio
    async def test_gather_export_data_all_contacts(self, mock_services, sample_export_data):
        """Test gathering export data for all contacts."""
        # Mock data service calls
        mock_services["data_service"].get_contacts.return_value = sample_export_data["contacts"]
        mock_services["data_service"].get_tags.return_value = sample_export_data["tags"]
        mock_services["data_service"].get_notes.return_value = sample_export_data["notes"]
        mock_services["data_service"].get_relationships.return_value = sample_export_data[
            "relationships"
        ]

        screen = ExportScreen(**mock_services)

        config = {
            "format": "json",
            "scope": "all",
            "scope_filter": None,
            "include_metadata": True,
            "include_relationships": True,
        }

        result = await screen._gather_export_data(config)

        assert len(result["contacts"]) == 2
        assert len(result["tags"]) == 2
        assert result["export_info"]["scope"] == "all"
        assert result["export_info"]["format"] == "json"

    @pytest.mark.asyncio
    async def test_gather_export_data_tag_filter(self, mock_services):
        """Test gathering export data with tag filter."""
        # Mock contacts by tag
        tag_contacts = [{"id": 1, "name": "John Doe", "email": "john@example.com"}]
        mock_services["data_service"].api.get_contacts_by_tag.return_value = tag_contacts

        screen = ExportScreen(**mock_services)

        config = {
            "format": "json",
            "scope": "tag",
            "scope_filter": "friend",
            "include_metadata": False,
            "include_relationships": False,
        }

        result = await screen._gather_export_data(config)

        assert len(result["contacts"]) == 1
        assert result["contacts"][0]["name"] == "John Doe"
        assert result["export_info"]["scope"] == "tag"

    def test_reset_form(self, mock_services):
        """Test resetting the form to defaults."""
        screen = ExportScreen(**mock_services)

        with patch.object(screen, "query_one") as mock_query, patch.object(
            screen, "_set_default_output_path"
        ) as mock_set_path:

            # Mock UI components
            mock_json_radio = MagicMock()
            mock_all_radio = MagicMock()
            mock_checkbox = MagicMock()
            mock_container = MagicMock()

            def query_side_effect(selector, widget_type=None):
                if selector == "#format-json":
                    return mock_json_radio
                elif selector == "#scope-all":
                    return mock_all_radio
                elif selector in [
                    "#include-images",
                    "#generate-directory",
                    "#include-relationships",
                    "#include-metadata",
                ]:
                    return mock_checkbox
                elif selector == "#tag-selection-container":
                    return mock_container
                return MagicMock()

            mock_query.side_effect = query_side_effect

            screen._reset_form()

            # Verify form was reset
            assert mock_json_radio.value is True
            assert mock_all_radio.value is True
            assert mock_checkbox.value is True  # All checkboxes set to True
            assert mock_container.display is False
            mock_set_path.assert_called_once()

    def test_reset_export_state(self, mock_services):
        """Test resetting export state."""
        screen = ExportScreen(**mock_services)

        # Set some state
        screen._export_complete = True
        screen._export_results = {"success": True}
        screen._is_exporting = True

        with patch.object(screen, "_hide_sections") as mock_hide:
            screen._reset_export_state()

            # Verify state was reset
            assert screen._export_complete is False
            assert screen._export_results is None
            assert screen._is_exporting is False
            mock_hide.assert_called_once()

    @patch("builtins.open", new_callable=mock_open)
    @pytest.mark.asyncio
    async def test_export_json(self, mock_file, mock_services, sample_export_data):
        """Test JSON export functionality."""
        screen = ExportScreen(**mock_services)
        export_path = Path("/test/export")
        config = {"include_images": False}

        with patch("pathlib.Path.mkdir"):
            files = await screen._export_json(sample_export_data, export_path, config)

            # Verify file was created
            assert len(files) == 1
            assert "export.json" in files[0]
            mock_file.assert_called_once()

    @patch("builtins.open", new_callable=mock_open)
    @pytest.mark.asyncio
    async def test_export_csv(self, mock_file, mock_services, sample_export_data):
        """Test CSV export functionality."""
        screen = ExportScreen(**mock_services)
        export_path = Path("/test/export")
        config = {"include_metadata": True}

        files = await screen._export_csv(sample_export_data, export_path, config)

        # Verify files were created
        assert len(files) >= 1
        assert any("contacts.csv" in f for f in files)

    @patch("builtins.open", new_callable=mock_open)
    @pytest.mark.asyncio
    async def test_export_html(self, mock_file, mock_services, sample_export_data):
        """Test HTML export functionality."""
        screen = ExportScreen(**mock_services)
        export_path = Path("/test/export")
        config = {}

        files = await screen._export_html(sample_export_data, export_path, config)

        # Verify HTML file was created
        assert len(files) == 1
        assert "contacts.html" in files[0]
        mock_file.assert_called_once()

        # Verify HTML content contains contact data
        written_content = mock_file().write.call_args[0][0]
        assert "John Doe" in written_content
        assert "jane@example.com" in written_content


if __name__ == "__main__":
    pytest.main([__file__])
