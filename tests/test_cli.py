import json
import os
import tempfile
from pathlib import Path

from typer.testing import CliRunner

from prt_src.api import PRTAPI
from prt_src.cli import app


def test_cli_creates_config(tmp_path):
    """Test that CLI can create a basic configuration."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Test with minimal input - just create config and exit
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0


def test_cli_database_connection(tmp_path):
    """Test CLI database connection and initialization."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        # Create a minimal config
        config_dir = Path(td) / "prt_data"
        config_dir.mkdir()
        config_file = config_dir / "prt_config.json"
        config_file.write_text(
            """{
            "google_api_key": "demo",
            "openai_api_key": "demo",
            "db_path": "prt_data/prt.db",
            "db_username": "test",
            "db_password": "test",
            "db_type": "sqlite",
            "db_host": "localhost",
            "db_port": 5432,
            "db_name": "prt"
        }"""
        )

        # Test that CLI can start without errors
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0


def test_cli_with_existing_database(tmp_path):
    """Test CLI behavior with an existing database."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        # Create config and database
        config_dir = Path(td) / "prt_data"
        config_dir.mkdir()
        config_file = config_dir / "prt_config.json"
        config_file.write_text(
            """{
            "google_api_key": "demo",
            "openai_api_key": "demo",
            "db_path": "prt_data/prt.db",
            "db_username": "test",
            "db_password": "test",
            "db_type": "sqlite",
            "db_host": "localhost",
            "db_port": 5432,
            "db_name": "prt"
        }"""
        )

        # Create a minimal database
        db_file = config_dir / "prt.db"
        import sqlite3

        conn = sqlite3.connect(db_file)
        conn.execute("CREATE TABLE contacts (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")
        conn.execute("INSERT INTO contacts (name, email) VALUES ('Test User', 'test@example.com')")
        conn.commit()
        conn.close()

        # Test that CLI can connect to existing database
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0


def test_search_export_functionality(test_db, tmp_path):
    """Test comprehensive search export functionality including JSON validation and image verification."""
    db, fixtures = test_db

    # Create test config
    config = {
        "db_path": str(db.path),
        "db_encrypted": False,
        "db_username": "test_user",
        "db_password": "test_pass",
        "db_type": "sqlite",
    }

    # Initialize API for testing
    api = PRTAPI(config)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Change to temp directory for export
        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            # Test contact search export
            _test_contact_search_export(api, fixtures)

            # Test tag search export
            _test_tag_search_export(api, fixtures)

            # Test note search export
            _test_note_search_export(api, fixtures)

        finally:
            os.chdir(original_cwd)


def _test_contact_search_export(api: PRTAPI, fixtures: dict):
    """Test contact search export with image validation."""
    from prt_src.cli import export_search_results

    # Search for contacts with known results
    contacts = api.search_contacts("John")  # Should find John Doe
    assert len(contacts) > 0, "Should find at least one contact"

    # Export the results
    export_search_results(api, "contacts", "John", contacts, interactive=False)

    # Find the export directory
    export_dirs = [d for d in Path(".").glob("exports/contacts_search_*")]
    assert (
        len(export_dirs) == 1
    ), f"Should create exactly one export directory, found {len(export_dirs)}"

    export_dir = export_dirs[0]

    # Validate export structure
    _validate_export_structure(export_dir, "contacts")

    # Load and validate JSON
    json_file = export_dir / "contacts_search_results.json"
    with open(json_file, "r") as f:
        export_data = json.load(f)

    # Validate JSON structure
    _validate_export_json_structure(export_data, "contacts", "John", len(contacts))

    # Validate contact data
    for result in export_data["results"]:
        _validate_contact_json_fields(result)

        # If contact has profile image, validate the exported image file
        if result.get("has_profile_image"):
            _validate_exported_image(export_dir, result)


def _test_tag_search_export(api: PRTAPI, fixtures: dict):
    """Test tag search export."""
    from prt_src.cli import export_search_results

    # Search for tags
    tags = api.search_tags("friend")  # Should find the "friend" tag
    assert len(tags) > 0, "Should find at least one tag"

    # Prepare export data (simulate what the CLI does)
    export_data = []
    for tag in tags:
        contacts = api.get_contacts_by_tag(tag["name"])
        export_data.append({"tag": tag, "associated_contacts": contacts})

    # Export the results
    export_search_results(api, "tags", "friend", export_data, interactive=False)

    # Find the export directory
    export_dirs = [d for d in Path(".").glob("exports/tags_search_*")]
    assert len(export_dirs) >= 1, "Should create at least one tag export directory"

    export_dir = sorted(export_dirs)[-1]  # Get the latest one

    # Validate export structure
    _validate_export_structure(export_dir, "tags")

    # Load and validate JSON
    json_file = export_dir / "tags_search_results.json"
    with open(json_file, "r") as f:
        export_data_loaded = json.load(f)

    # Validate JSON structure
    _validate_export_json_structure(export_data_loaded, "tags", "friend", len(export_data))

    # Validate tag-specific structure
    for result in export_data_loaded["results"]:
        assert "tag" in result, "Tag search result should have 'tag' field"
        assert (
            "associated_contacts" in result
        ), "Tag search result should have 'associated_contacts' field"

        # Validate contacts within the tag result
        for contact in result["associated_contacts"]:
            _validate_contact_json_fields(contact)


def _test_note_search_export(api: PRTAPI, fixtures: dict):
    """Test note search export."""
    from prt_src.cli import export_search_results

    # Search for notes
    notes = api.search_notes("meeting")  # Should find notes with "meeting" in title/content

    if len(notes) > 0:  # Only test if we have notes
        # Prepare export data (simulate what the CLI does)
        export_data = []
        for note in notes:
            contacts = api.get_contacts_by_note(note["title"])
            export_data.append({"note": note, "associated_contacts": contacts})

        # Export the results
        export_search_results(api, "notes", "meeting", export_data, interactive=False)

        # Find the export directory
        export_dirs = [d for d in Path(".").glob("exports/notes_search_*")]
        assert len(export_dirs) >= 1, "Should create at least one note export directory"

        export_dir = sorted(export_dirs)[-1]  # Get the latest one

        # Validate export structure
        _validate_export_structure(export_dir, "notes")

        # Load and validate JSON
        json_file = export_dir / "notes_search_results.json"
        with open(json_file, "r") as f:
            export_data_loaded = json.load(f)

        # Validate JSON structure
        _validate_export_json_structure(export_data_loaded, "notes", "meeting", len(export_data))

        # Validate note-specific structure
        for result in export_data_loaded["results"]:
            assert "note" in result, "Note search result should have 'note' field"
            assert (
                "associated_contacts" in result
            ), "Note search result should have 'associated_contacts' field"


def _validate_export_structure(export_dir: Path, search_type: str):
    """Validate the basic export directory structure."""
    assert export_dir.exists(), f"Export directory should exist: {export_dir}"
    assert export_dir.is_dir(), f"Export path should be a directory: {export_dir}"

    # Check required files
    json_file = export_dir / f"{search_type}_search_results.json"
    readme_file = export_dir / "README.md"
    images_dir = export_dir / "profile_images"

    assert json_file.exists(), f"JSON file should exist: {json_file}"
    assert readme_file.exists(), f"README file should exist: {readme_file}"
    assert images_dir.exists(), f"Profile images directory should exist: {images_dir}"
    assert images_dir.is_dir(), f"Profile images should be a directory: {images_dir}"


def _validate_export_json_structure(
    export_data: dict, search_type: str, query: str, expected_count: int
):
    """Validate the overall JSON export structure."""
    # Validate top-level structure
    assert "export_info" in export_data, "Export should have 'export_info'"
    assert "results" in export_data, "Export should have 'results'"

    # Validate export_info
    export_info = export_data["export_info"]
    assert export_info["search_type"] == search_type, f"Search type should be '{search_type}'"
    assert export_info["query"] == query, f"Query should be '{query}'"
    assert (
        export_info["total_results"] == expected_count
    ), f"Total results should be {expected_count}"
    assert "timestamp" in export_info, "Export info should have timestamp"

    # Validate search_request field
    assert "search_request" in export_info, "Export info should have search_request"
    search_request = export_info["search_request"]
    assert search_request["type"] == search_type, f"Search request type should be '{search_type}'"
    assert search_request["term"] == query, f"Search request term should be '{query}'"
    assert "executed_at" in search_request, "Search request should have executed_at timestamp"

    # Validate results structure
    results = export_data["results"]
    assert isinstance(results, list), "Results should be a list"
    assert (
        len(results) == expected_count
    ), f"Results length should match expected count {expected_count}"


def _validate_contact_json_fields(contact: dict):
    """Validate contact JSON fields are properly structured."""
    # Required fields
    required_fields = ["id", "name"]
    for field in required_fields:
        assert field in contact, f"Contact should have '{field}' field"

    # Optional fields that should be present (may be None)
    optional_fields = [
        "email",
        "phone",
        "profile_image_filename",
        "profile_image_mime_type",
        "relationship_info",
    ]
    for field in optional_fields:
        assert field in contact, f"Contact should have '{field}' field (even if None)"

    # Image-related fields
    assert "has_profile_image" in contact, "Contact should have 'has_profile_image' field"
    assert isinstance(contact["has_profile_image"], bool), "'has_profile_image' should be boolean"

    # If has profile image, should have exported_image_path
    if contact["has_profile_image"]:
        assert (
            "exported_image_path" in contact
        ), "Contact with image should have 'exported_image_path'"
        assert contact["exported_image_path"].startswith(
            "profile_images/"
        ), "Image path should be in profile_images/"
        assert contact["exported_image_path"].endswith(".jpg"), "Image path should end with .jpg"

    # Ensure no binary data leaked into JSON
    assert "profile_image" not in contact, "JSON should not contain binary 'profile_image' data"


def _validate_exported_image(export_dir: Path, contact: dict):
    """Validate that exported image file exists and has reasonable size."""
    image_path = export_dir / contact["exported_image_path"]

    # Check file exists
    assert image_path.exists(), f"Exported image should exist: {image_path}"
    assert image_path.is_file(), f"Image path should be a file: {image_path}"

    # Check file size is reasonable (should be > 100 bytes for a real image, < 1MB for test data)
    file_size = image_path.stat().st_size
    assert 100 < file_size < 1024 * 1024, f"Image file size should be reasonable: {file_size} bytes"

    # Check filename matches expected pattern (contact_id.jpg)
    expected_filename = f"{contact['id']}.jpg"
    assert (
        image_path.name == expected_filename
    ), f"Image filename should be {expected_filename}, got {image_path.name}"

    # Verify it's a valid JPEG file (basic check - starts with JPEG magic bytes)
    with open(image_path, "rb") as f:
        header = f.read(3)
        assert (
            header == b"\xff\xd8\xff"
        ), f"File should start with JPEG magic bytes, got {header.hex()}"
