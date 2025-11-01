"""Unit tests for FixtureService."""

from unittest.mock import Mock
from unittest.mock import patch

import pytest

from prt_src.tui.services.fixture import FixtureService


@pytest.mark.unit
class TestFixtureService:
    """Test suite for FixtureService."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock Database instance."""
        db = Mock()
        db.session = Mock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create a FixtureService instance."""
        return FixtureService(mock_db)

    def test_get_fixture_summary_returns_correct_counts(self, service):
        """Test get_fixture_summary returns expected fixture counts."""
        with patch("prt_src.tui.services.fixture.get_fixture_spec") as mock_spec:
            mock_spec.return_value = {
                "contacts": {"count": 7},
                "tags": {"count": 8},
                "notes": {"count": 6},
                "relationships": {"count": 10},
            }

            summary = service.get_fixture_summary()

            assert summary["contacts"] == 7
            assert summary["tags"] == 8
            assert summary["notes"] == 6
            assert summary["relationships"] == 10
            assert summary["has_images"] is True
            assert "description" in summary

    async def test_clear_database_deletes_all_data(self, service, mock_db):
        """Test clear_database removes all contacts, tags, notes, relationships."""
        # Mock the query/delete chain
        mock_query = Mock()
        mock_query.delete.return_value = None
        mock_db.session.query.return_value = mock_query

        success = await service.clear_database()

        assert success is True
        # Should query and delete each table
        assert mock_db.session.query.call_count >= 5  # 5 main tables
        mock_db.session.commit.assert_called_once()

    async def test_clear_database_handles_exceptions(self, service, mock_db):
        """Test clear_database handles exceptions gracefully."""
        mock_db.session.query.side_effect = Exception("Database error")

        success = await service.clear_database()

        assert success is False
        mock_db.session.rollback.assert_called_once()

    async def test_load_fixtures_returns_success_summary(self, service, mock_db):
        """Test load_fixtures returns summary of loaded data."""
        mock_fixtures = {
            "contacts": {"c1": Mock(), "c2": Mock(), "c3": Mock()},
            "tags": {"t1": Mock(), "t2": Mock()},
            "notes": {"n1": Mock()},
            "relationships": {"r1": Mock(), "r2": Mock()},
        }

        with patch("prt_src.tui.services.fixture.setup_test_database") as mock_setup:
            mock_setup.return_value = mock_fixtures

            result = await service.load_fixtures()

            assert result["success"] is True
            assert result["contacts"] == 3
            assert result["tags"] == 2
            assert result["notes"] == 1
            assert result["relationships"] == 2
            assert "message" in result
            mock_setup.assert_called_once_with(mock_db)

    async def test_load_fixtures_handles_exceptions(self, service, mock_db):
        """Test load_fixtures handles exceptions gracefully."""
        with patch("prt_src.tui.services.fixture.setup_test_database") as mock_setup:
            mock_setup.side_effect = Exception("Setup failed")

            result = await service.load_fixtures()

            assert result["success"] is False
            assert result["contacts"] == 0
            assert "error" in result
            assert "setup failed" in result["error"].lower()

    async def test_clear_and_load_fixtures_clears_then_loads(self, service, mock_db):
        """Test clear_and_load_fixtures performs both operations."""
        # Mock clear to succeed
        mock_query = Mock()
        mock_query.delete.return_value = None
        mock_db.session.query.return_value = mock_query

        # Mock load to succeed
        mock_fixtures = {
            "contacts": {"c1": Mock()},
            "tags": {"t1": Mock()},
            "notes": {"n1": Mock()},
            "relationships": {"r1": Mock()},
        }

        with patch("prt_src.tui.services.fixture.setup_test_database") as mock_setup:
            mock_setup.return_value = mock_fixtures

            result = await service.clear_and_load_fixtures()

            assert result["success"] is True
            assert result["contacts"] == 1
            # Verify clear was called (commit should be called)
            mock_db.session.commit.assert_called()

    async def test_clear_and_load_fixtures_fails_if_clear_fails(self, service, mock_db):
        """Test clear_and_load_fixtures returns error if clear fails."""
        # Mock clear to fail
        mock_db.session.query.side_effect = Exception("Clear failed")

        result = await service.clear_and_load_fixtures()

        assert result["success"] is False
        assert "error" in result
        assert "clear" in result["error"].lower()


@pytest.mark.integration
class TestFixtureServiceIntegration:
    """Integration tests with real database."""

    async def test_clear_database_with_real_db(self, test_db):
        """Test clearing a real database with fixture data."""
        db, fixtures = test_db
        service = FixtureService(db)

        # Verify DB has data
        from prt_src.models import Contact

        initial_count = db.session.query(Contact).count()
        assert initial_count > 0

        # Clear
        success = await service.clear_database()
        assert success is True

        # Verify empty
        final_count = db.session.query(Contact).count()
        assert final_count == 0

    async def test_load_fixtures_with_real_db(self, test_db_empty):
        """Test loading fixtures into empty database."""
        db = test_db_empty
        service = FixtureService(db)

        # Verify empty
        from prt_src.models import Contact

        initial_count = db.session.query(Contact).count()
        assert initial_count == 0

        # Load
        result = await service.load_fixtures()
        assert result["success"] is True

        # Verify loaded
        final_count = db.session.query(Contact).count()
        assert final_count == result["contacts"]
        assert final_count > 0

    async def test_clear_and_load_with_real_db(self, test_db):
        """Test clear and load with real database."""
        db, fixtures = test_db
        service = FixtureService(db)

        # Get initial count
        from prt_src.models import Contact

        initial_count = db.session.query(Contact).count()
        assert initial_count > 0

        # Clear and reload
        result = await service.clear_and_load_fixtures()

        # Print result for debugging
        if not result["success"]:
            print(f"Error: {result.get('error', 'Unknown error')}")
            print(f"Full result: {result}")

        assert result["success"] is True, f"Failed with error: {result.get('error', 'Unknown')}"

        # Verify reloaded
        final_count = db.session.query(Contact).count()
        assert final_count == result["contacts"]
        assert final_count > 0
