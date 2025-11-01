"""Unit tests for GoogleTakeoutService."""

from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from prt_src.tui.services.google_takeout import GoogleTakeoutService


@pytest.mark.unit
class TestGoogleTakeoutService:
    """Test suite for GoogleTakeoutService."""

    @pytest.fixture
    def mock_api(self):
        """Create a mock PRTAPI instance."""
        return Mock()

    @pytest.fixture
    def service(self, mock_api):
        """Create a GoogleTakeoutService instance."""
        return GoogleTakeoutService(mock_api)

    async def test_find_takeout_files_returns_empty_when_no_files(self, service):
        """Test find_takeout_files returns empty list when no files found."""
        with patch("prt_src.tui.services.google_takeout.find_takeout_files") as mock_find:
            mock_find.return_value = []

            files = await service.find_takeout_files()

            assert files == []

    async def test_find_takeout_files_returns_found_files(self, service, tmp_path):
        """Test find_takeout_files returns files when found."""
        fake_file1 = tmp_path / "takeout1.zip"
        fake_file2 = tmp_path / "takeout2.zip"

        with patch("prt_src.tui.services.google_takeout.find_takeout_files") as mock_find:
            mock_find.return_value = [fake_file1, fake_file2]

            files = await service.find_takeout_files()

            assert len(files) == 2
            assert fake_file1 in files
            assert fake_file2 in files

    async def test_find_takeout_files_removes_duplicates(self, service, tmp_path):
        """Test find_takeout_files removes duplicate file paths."""
        fake_file = tmp_path / "takeout.zip"

        with patch("prt_src.tui.services.google_takeout.find_takeout_files") as mock_find:
            # Simulate finding same file in multiple locations
            mock_find.return_value = [fake_file, fake_file, fake_file]

            files = await service.find_takeout_files()

            assert len(files) == 1
            assert files[0] == fake_file

    async def test_validate_file_fails_for_nonexistent_file(self, service):
        """Test validate_file returns False for nonexistent file."""
        nonexistent = Path("/nonexistent/file.zip")

        is_valid, message = await service.validate_file(nonexistent)

        assert is_valid is False
        assert "not found" in message.lower()

    async def test_validate_file_fails_for_non_zip_file(self, service, tmp_path):
        """Test validate_file returns False for non-zip files."""
        text_file = tmp_path / "not_a_zip.txt"
        text_file.write_text("hello")

        is_valid, message = await service.validate_file(text_file)

        assert is_valid is False
        assert "zip file" in message.lower()

    async def test_validate_file_succeeds_for_valid_takeout(self, service, tmp_path):
        """Test validate_file returns True for valid takeout zip."""
        zip_file = tmp_path / "takeout.zip"
        zip_file.touch()  # Create empty file

        with patch("prt_src.tui.services.google_takeout.GoogleTakeoutParser") as MockParser:
            mock_parser = Mock()
            mock_parser.validate_takeout_file.return_value = (True, "Valid file")
            MockParser.return_value = mock_parser

            is_valid, message = await service.validate_file(zip_file)

            assert is_valid is True
            assert message == "Valid file"

    async def test_validate_file_handles_parser_exceptions(self, service, tmp_path):
        """Test validate_file handles exceptions gracefully."""
        zip_file = tmp_path / "bad.zip"
        zip_file.touch()

        with patch("prt_src.tui.services.google_takeout.GoogleTakeoutParser") as MockParser:
            MockParser.side_effect = Exception("Parser error")

            is_valid, message = await service.validate_file(zip_file)

            assert is_valid is False
            assert "error" in message.lower()

    async def test_get_preview_returns_preview_info(self, service, tmp_path):
        """Test get_preview returns preview information."""
        zip_file = tmp_path / "takeout.zip"
        zip_file.touch()

        expected_preview = {
            "valid": True,
            "contact_count": 10,
            "image_count": 5,
            "contacts_with_images": 5,
            "sample_contacts": [{"name": "John Doe", "has_image": True}],
            "message": "Found 10 contacts",
        }

        with patch("prt_src.tui.services.google_takeout.GoogleTakeoutParser") as MockParser:
            mock_parser = Mock()
            mock_parser.get_preview_info.return_value = expected_preview
            MockParser.return_value = mock_parser

            preview = await service.get_preview(zip_file)

            assert preview == expected_preview

    async def test_get_preview_handles_exceptions(self, service, tmp_path):
        """Test get_preview handles exceptions gracefully."""
        zip_file = tmp_path / "bad.zip"
        zip_file.touch()

        with patch("prt_src.tui.services.google_takeout.GoogleTakeoutParser") as MockParser:
            MockParser.side_effect = Exception("Read error")

            preview = await service.get_preview(zip_file)

            assert preview["valid"] is False
            assert "error" in preview["error"].lower()
            assert preview["contact_count"] == 0

    async def test_import_contacts_success(self, service, mock_api, tmp_path):
        """Test successful contact import."""
        zip_file = tmp_path / "takeout.zip"
        zip_file.touch()

        mock_contacts = [
            {"first": "John", "last": "Doe", "emails": ["john@example.com"]},
            {"first": "Jane", "last": "Smith", "emails": ["jane@example.com"]},
        ]
        mock_info = {
            "contact_count": 2,
            "image_count": 1,
            "contacts_with_images": 1,
        }

        with patch("prt_src.tui.services.google_takeout.parse_takeout_contacts") as mock_parse:
            mock_parse.return_value = (mock_contacts, mock_info)
            mock_api.insert_contacts.return_value = True

            success, message, info = await service.import_contacts(zip_file)

            assert success is True
            assert "imported 2 contacts" in message.lower()
            assert info == mock_info
            mock_api.insert_contacts.assert_called_once_with(mock_contacts)

    async def test_import_contacts_fails_on_parse_error(self, service, mock_api, tmp_path):
        """Test import fails when parsing returns error."""
        zip_file = tmp_path / "bad.zip"
        zip_file.touch()

        with patch("prt_src.tui.services.google_takeout.parse_takeout_contacts") as mock_parse:
            mock_parse.return_value = ([], {"error": "Invalid zip file"})

            success, message, info = await service.import_contacts(zip_file)

            assert success is False
            assert "error" in message.lower()
            mock_api.insert_contacts.assert_not_called()

    async def test_import_contacts_fails_when_no_contacts_found(self, service, mock_api, tmp_path):
        """Test import fails when no contacts in file."""
        zip_file = tmp_path / "empty.zip"
        zip_file.touch()

        with patch("prt_src.tui.services.google_takeout.parse_takeout_contacts") as mock_parse:
            mock_parse.return_value = ([], {"contact_count": 0})

            success, message, info = await service.import_contacts(zip_file)

            assert success is False
            assert "no contacts" in message.lower()
            mock_api.insert_contacts.assert_not_called()

    async def test_import_contacts_fails_on_database_error(self, service, mock_api, tmp_path):
        """Test import fails when database insert fails."""
        zip_file = tmp_path / "takeout.zip"
        zip_file.touch()

        mock_contacts = [{"first": "John", "last": "Doe"}]
        mock_info = {"contact_count": 1}

        with patch("prt_src.tui.services.google_takeout.parse_takeout_contacts") as mock_parse:
            mock_parse.return_value = (mock_contacts, mock_info)
            mock_api.insert_contacts.return_value = False

            success, message, info = await service.import_contacts(zip_file)

            assert success is False
            assert "failed to import" in message.lower()

    async def test_import_contacts_handles_exceptions(self, service, mock_api, tmp_path):
        """Test import handles unexpected exceptions."""
        zip_file = tmp_path / "takeout.zip"
        zip_file.touch()

        with patch("prt_src.tui.services.google_takeout.parse_takeout_contacts") as mock_parse:
            mock_parse.side_effect = Exception("Unexpected error")

            success, message, info = await service.import_contacts(zip_file)

            assert success is False
            assert "error" in message.lower()
            assert info is None

    def test_get_search_instructions_returns_string(self, service):
        """Test get_search_instructions returns formatted instructions."""
        instructions = service.get_search_instructions()

        assert isinstance(instructions, str)
        assert "takeout.google.com" in instructions.lower()
        assert "downloads" in instructions.lower()
        assert "prt_data" in instructions.lower()
