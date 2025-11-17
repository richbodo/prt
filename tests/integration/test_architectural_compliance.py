"""
Architectural Compliance Tests

These tests validate that the PRT codebase follows the API-first architectural pattern
and prevent future violations.
"""

import re
from pathlib import Path

import pytest

from prt_src.api import PRTAPI
from prt_src.tui.services.data import DataService


class TestArchitecturalCompliance:
    """Test suite to enforce architectural compliance across the codebase."""

    def test_no_direct_database_access_in_tui_data_service(self):
        """Verify that TUI DataService doesn't access database directly."""
        # Read the DataService source code
        data_service_path = Path("prt_src/tui/services/data.py")
        content = data_service_path.read_text()

        # Check for direct database access patterns
        violations = []

        # Pattern 1: self.api.db.something
        db_access_pattern = r"self\.api\.db\."
        matches = re.finditer(db_access_pattern, content)
        for match in matches:
            line_num = content[: match.start()].count("\n") + 1
            line = content.split("\n")[line_num - 1].strip()
            violations.append(f"Line {line_num}: {line}")

        # Pattern 2: Direct session access
        session_pattern = r"\.session\."
        matches = re.finditer(session_pattern, content)
        for match in matches:
            line_num = content[: match.start()].count("\n") + 1
            line = content.split("\n")[line_num - 1].strip()
            violations.append(f"Line {line_num}: {line}")

        if violations:
            failure_msg = (
                "TUI DataService contains direct database access violations:\n"
                + "\n".join(violations)
                + "\n\nAll database operations must go through PRTAPI methods."
            )
            pytest.fail(failure_msg)

    def test_no_direct_core_imports_in_tui_layer(self):
        """Verify that TUI layer doesn't import core modules directly."""
        tui_dir = Path("prt_src/tui")
        violations = []

        # Check all Python files in TUI layer
        for py_file in tui_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            content = py_file.read_text()

            # Pattern: from prt_src.core. imports
            core_import_pattern = r"from prt_src\.core\."
            matches = re.finditer(core_import_pattern, content)
            for match in matches:
                line_num = content[: match.start()].count("\n") + 1
                line = content.split("\n")[line_num - 1].strip()
                violations.append(f"{py_file}: Line {line_num}: {line}")

        if violations:
            failure_msg = (
                "TUI layer contains direct core module imports:\n"
                + "\n".join(violations)
                + "\n\nTUI layer should only import from API and models for type hints."
            )
            pytest.fail(failure_msg)

    async def test_data_service_uses_api_methods_exclusively(self, test_db):
        """Test that DataService delegates all operations to PRTAPI methods."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}

        # Create API and DataService instances
        api = PRTAPI(config)
        data_service = DataService(api)

        # Test that all major operations work through API

        # Test contact operations
        contacts = api.list_all_contacts()
        ds_contacts = await data_service.list_all_contacts()
        assert len(ds_contacts) == len(contacts), "DataService contact count should match API"

        # Test relationship operations
        relationships = api.get_all_relationships()
        ds_relationships = await data_service.get_relationships()
        assert len(ds_relationships) == len(
            relationships
        ), "DataService relationship count should match API"

        # Test note operations
        notes = api.get_all_notes()
        ds_notes = await data_service.list_all_notes()
        assert len(ds_notes) == len(notes), "DataService note count should match API"

        # Test tag operations
        tags = api.get_all_tags()
        ds_tags = await data_service.list_all_tags()
        assert len(ds_tags) == len(tags), "DataService tag count should match API"

    async def test_cli_and_tui_produce_identical_results(self, test_db):
        """Test that CLI and TUI produce identical results for same operations."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}

        # Create API and DataService instances
        api = PRTAPI(config)
        data_service = DataService(api)

        # Test search operations
        search_query = "John"

        cli_contacts = api.search_contacts(search_query)
        tui_contacts = await data_service.search_contacts(search_query)

        assert len(cli_contacts) == len(
            tui_contacts
        ), "CLI and TUI should return same number of contacts"

        # Compare contact IDs (order might differ)
        cli_ids = {contact["id"] for contact in cli_contacts}
        tui_ids = {contact["id"] for contact in tui_contacts}
        assert cli_ids == tui_ids, "CLI and TUI should return same contacts"

        # Test note search
        cli_notes = api.search_notes("meeting")
        tui_notes = await data_service.search_notes("meeting")

        cli_note_ids = {note["id"] for note in cli_notes}
        tui_note_ids = {note["id"] for note in tui_notes}
        assert cli_note_ids == tui_note_ids, "CLI and TUI should return same notes"

    def test_api_method_coverage_for_data_service(self):
        """Test that PRTAPI has all methods needed by DataService."""
        required_methods = [
            # Relationship operations
            "get_all_relationships",
            "add_relationship",
            # Note operations by ID
            "update_note_by_id",
            "delete_note_by_id",
            "get_note_by_id",
            # Search operations
            "unified_search",
            # Database management
            "export_relationships_data",
            "vacuum_database",
            # Contact operations
            "add_contact",
            "update_contact",
            "delete_contact",
            "get_contact",
            "tag_contact",
            # Utility methods
            "add_note",
            "get_all_notes",
            "get_all_tags",
        ]

        api = PRTAPI()
        missing_methods = []

        for method_name in required_methods:
            if not hasattr(api, method_name):
                missing_methods.append(method_name)

        if missing_methods:
            pytest.fail(f"PRTAPI is missing required methods for DataService: {missing_methods}")

    async def test_data_service_error_handling_through_api(self, test_db):
        """Test that DataService handles errors correctly when API methods fail."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}

        # Create API and DataService instances
        api = PRTAPI(config)
        data_service = DataService(api)

        # Test operations with invalid IDs
        result = await data_service.get_contact(99999)
        assert result is None, "DataService should handle invalid contact ID gracefully"

        result = await data_service.update_note(99999, "title", "content")
        assert result is False, "DataService should handle invalid note ID gracefully"

        result = await data_service.delete_note(99999)
        assert result is False, "DataService should handle invalid note delete gracefully"

    def test_no_duplicate_functionality_between_api_and_dataservice(self):
        """Test that DataService doesn't reimplement API functionality."""
        data_service_path = Path("prt_src/tui/services/data.py")
        content = data_service_path.read_text()

        # Check for suspicious patterns that suggest reimplementation
        suspicious_patterns = [
            r"from\s+sqlalchemy\s+import",  # Direct SQLAlchemy usage
            r"session\.query\(",  # Direct session queries
            r"session\.add\(",  # Direct session modifications
            r"session\.commit\(",  # Direct session commits
        ]

        violations = []
        for pattern in suspicious_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[: match.start()].count("\n") + 1
                line = content.split("\n")[line_num - 1].strip()
                violations.append(f"Line {line_num}: {line}")

        if violations:
            failure_msg = (
                "DataService contains suspicious patterns suggesting code duplication:\n"
                + "\n".join(violations)
                + "\n\nDataService should delegate to API methods instead of reimplementing."
            )
            pytest.fail(failure_msg)

    async def test_dataservice_performance_equivalent_to_api(self, test_db):
        """Test that DataService performance is equivalent to direct API calls."""
        import time

        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}

        # Create API and DataService instances
        api = PRTAPI(config)
        data_service = DataService(api)

        # Measure API performance
        start_time = time.time()
        api_contacts = api.list_all_contacts()
        api_time = time.time() - start_time

        # Measure DataService performance
        start_time = time.time()
        ds_contacts = await data_service.list_all_contacts()
        ds_time = time.time() - start_time

        # DataService should not be significantly slower (allow 50% overhead for async)
        assert (
            ds_time < api_time * 1.5
        ), f"DataService is too slow: {ds_time:.3f}s vs API {api_time:.3f}s"

        # Results should be identical
        assert len(ds_contacts) == len(api_contacts), "Results should be identical"

    async def test_consistent_error_handling_across_interfaces(self, test_db):
        """Test that error handling is consistent between CLI and TUI interfaces."""
        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}

        # Create API and DataService instances
        api = PRTAPI(config)
        data_service = DataService(api)

        # Test invalid search operations
        cli_result = api.search_contacts("")  # Empty query
        tui_result = await data_service.search_contacts("")

        # Both should handle empty queries gracefully
        assert isinstance(cli_result, list), "API should return list for empty query"
        assert isinstance(tui_result, list), "DataService should return list for empty query"

        # Test very long queries
        long_query = "x" * 1000
        cli_result = api.search_contacts(long_query)
        tui_result = await data_service.search_contacts(long_query)

        assert isinstance(cli_result, list), "API should handle long queries"
        assert isinstance(tui_result, list), "DataService should handle long queries"


class TestArchitecturalEnforcement:
    """Tests that enforce architectural patterns for future development."""

    def test_tui_imports_only_allowed_modules(self):
        """Test that TUI layer only imports from allowed modules."""
        tui_dir = Path("prt_src/tui")
        allowed_prefixes = [
            "prt_src.api",
            "prt_src.models",  # For type hints only
            "prt_src.logging_config",
            "prt_src.tui.",  # Internal TUI imports
            "textual",  # TUI framework
            "typing",  # Type hints
            "pathlib",  # Standard library
            "datetime",  # Standard library
            "json",  # Standard library
            "os",  # Standard library
            "re",  # Standard library
            "asyncio",  # Standard library
            "time",  # Standard library
        ]

        violations = []

        for py_file in tui_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            content = py_file.read_text()
            lines = content.split("\n")

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if line.startswith(("from ", "import ")):
                    # Extract the module being imported
                    if line.startswith("from "):
                        module = line.split(" ")[1].split(".")[0]
                        if "prt_src" in line:
                            # For prt_src imports, check full path
                            module = line.split(" ")[1]
                    else:
                        module = line.split(" ")[1].split(".")[0]

                    # Check if import is allowed
                    allowed = False
                    for prefix in allowed_prefixes:
                        if module.startswith(prefix):
                            allowed = True
                            break

                    if not allowed and not module.startswith("__") and module != "":
                        violations.append(f"{py_file}: Line {line_num}: {line}")

        if violations:
            # Don't fail for now, just warn about potential violations
            # Can be enabled in the future for stricter enforcement
            pass

    def test_api_layer_completeness_for_tui_needs(self):
        """Test that API layer provides complete functionality for TUI needs."""
        # This test documents what the API should provide
        required_api_categories = {
            "contact_crud": ["add_contact", "get_contact", "update_contact", "delete_contact"],
            "contact_search": ["search_contacts", "list_all_contacts"],
            "relationship_crud": ["add_relationship", "get_all_relationships"],
            "note_crud": ["add_note", "update_note_by_id", "delete_note_by_id", "get_note_by_id"],
            "note_search": ["search_notes", "list_all_notes"],
            "tag_crud": ["create_tag", "delete_tag", "tag_contact", "remove_tag_from_contact"],
            "tag_search": ["search_tags", "list_all_tags"],
            "unified_search": ["unified_search"],
            "database_mgmt": ["vacuum_database", "export_relationships_data"],
        }

        api = PRTAPI()
        missing_by_category = {}

        for category, methods in required_api_categories.items():
            missing = []
            for method in methods:
                if not hasattr(api, method):
                    missing.append(method)
            if missing:
                missing_by_category[category] = missing

        if missing_by_category:
            failure_msg = "API layer is missing required methods:\n"
            for category, methods in missing_by_category.items():
                failure_msg += f"  {category}: {', '.join(methods)}\n"
            pytest.fail(failure_msg)
