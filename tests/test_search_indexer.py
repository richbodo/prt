"""Test search indexer functionality."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import OperationalError

from prt_src.core.search_index.indexer import EntityType, SearchIndexer, SearchResult


@pytest.fixture
def mock_db():
    """Create a mock database with session."""
    db = MagicMock()
    db.session = MagicMock()
    return db


@pytest.fixture
def indexer(mock_db):
    """Create SearchIndexer with mock database."""
    return SearchIndexer(mock_db)


class TestSearchIndexer:
    """Test SearchIndexer class."""

    def test_check_fts_available_true(self, indexer, mock_db):
        """Test FTS availability check when tables exist."""
        # Mock successful queries to FTS tables
        mock_db.session.execute.return_value = MagicMock()

        assert indexer.check_fts_available() is True
        # Should cache the result
        assert indexer._fts_available is True

    def test_check_fts_available_false(self, indexer, mock_db):
        """Test FTS availability check when tables don't exist."""
        # Mock OperationalError for missing tables
        mock_db.session.execute.side_effect = OperationalError("", "", "")

        assert indexer.check_fts_available() is False
        assert indexer._fts_available is False

    def test_search_empty_query(self, indexer):
        """Test search with empty query returns empty results."""
        results = indexer.search("")
        assert results == []

        results = indexer.search("   ")
        assert results == []

    def test_prepare_fts_query_single_term(self, indexer):
        """Test FTS query preparation for single term."""
        query = indexer._prepare_fts_query("alice")
        assert query == "alice*"

    def test_prepare_fts_query_multiple_terms(self, indexer):
        """Test FTS query preparation for multiple terms."""
        query = indexer._prepare_fts_query("alice smith")
        assert query == "alice* OR smith*"

    def test_prepare_fts_query_special_chars(self, indexer):
        """Test FTS query strips special characters."""
        query = indexer._prepare_fts_query('alice "smith" (test)')
        assert '"' not in query
        assert "(" not in query
        assert ")" not in query

    def test_search_contacts(self, indexer, mock_db):
        """Test searching contacts with FTS."""
        # Mock FTS available
        indexer._fts_available = True

        # Mock search results
        mock_results = [
            (1, "Alice Smith", "alice@example.com", "555-0001", -0.5, "<b>Alice</b> Smith", None),
            (
                2,
                "Alice Johnson",
                "alicej@example.com",
                "555-0002",
                -0.3,
                "<b>Alice</b> Johnson",
                None,
            ),
        ]
        mock_db.session.execute.return_value.fetchall.return_value = mock_results

        results = indexer.search("alice", [EntityType.CONTACT])

        assert len(results) == 2
        assert results[0].entity_type == EntityType.CONTACT
        assert results[0].title == "Alice Smith"
        assert results[0].relevance_score == 0.5
        assert "name" in results[0].matched_fields

    def test_search_notes(self, indexer, mock_db):
        """Test searching notes with FTS."""
        indexer._fts_available = True

        mock_results = [
            (1, "Meeting Notes", "Discussed project", -0.7, "<b>Meeting</b> Notes", None),
        ]
        mock_db.session.execute.return_value.fetchall.return_value = mock_results

        results = indexer.search("meeting", [EntityType.NOTE])

        assert len(results) == 1
        assert results[0].entity_type == EntityType.NOTE
        assert results[0].title == "Meeting Notes"
        assert "title" in results[0].matched_fields

    def test_search_tags(self, indexer, mock_db):
        """Test searching tags with FTS."""
        indexer._fts_available = True

        mock_results = [
            (1, "family", "Family members", -0.4, "<b>family</b>", 5),
        ]
        mock_db.session.execute.return_value.fetchall.return_value = mock_results

        results = indexer.search("family", [EntityType.TAG])

        assert len(results) == 1
        assert results[0].entity_type == EntityType.TAG
        assert results[0].title == "family"
        assert results[0].subtitle == "5 contacts"

    def test_search_all_entity_types(self, indexer, mock_db):
        """Test searching across all entity types."""
        indexer._fts_available = True

        # Mock different results for each entity type
        call_count = 0

        def mock_execute(sql, params=None):
            nonlocal call_count
            mock_result = MagicMock()

            if call_count == 0:  # Contacts search
                mock_result.fetchall.return_value = [
                    (1, "Test Contact", "test@example.com", "555-0001", -0.5, "<b>Test</b>", None)
                ]
            elif call_count == 1:  # Notes search
                mock_result.fetchall.return_value = [
                    (1, "Test Note", "Content", -0.3, "<b>Test</b>", None)
                ]
            else:  # Tags search
                mock_result.fetchall.return_value = [
                    (1, "test_tag", "Description", -0.2, "<b>test</b>", 3)
                ]

            call_count += 1
            return mock_result

        mock_db.session.execute = mock_execute

        results = indexer.search("test")

        # Should have results from all entity types
        entity_types = {r.entity_type for r in results}
        assert EntityType.CONTACT in entity_types
        assert EntityType.NOTE in entity_types
        assert EntityType.TAG in entity_types

    def test_search_with_ranking(self, indexer, mock_db):
        """Test search results are ranked by relevance."""
        indexer._fts_available = True

        # Create results with different relevance scores
        mock_results = [
            (1, "Result 1", None, None, -0.2, None, None),
            (2, "Result 2", None, None, -0.8, None, None),
            (3, "Result 3", None, None, -0.5, None, None),
        ]
        mock_db.session.execute.return_value.fetchall.return_value = mock_results

        results = indexer.search("test", [EntityType.CONTACT], rank_by_relevance=True)

        # Results should be sorted by relevance (highest first)
        assert results[0].relevance_score == 0.8
        assert results[1].relevance_score == 0.5
        assert results[2].relevance_score == 0.2

    def test_search_with_pagination(self, indexer, mock_db):
        """Test search pagination."""
        indexer._fts_available = True

        # Create 5 results
        mock_results = [(i, f"Result {i}", None, None, -0.5, None, None) for i in range(1, 6)]
        mock_db.session.execute.return_value.fetchall.return_value = mock_results

        # Get first page
        results = indexer.search("test", [EntityType.CONTACT], limit=2, offset=0)
        assert len(results) == 2
        assert results[0].entity_id == 1

        # Get second page
        results = indexer.search("test", [EntityType.CONTACT], limit=2, offset=2)
        assert len(results) == 2
        assert results[0].entity_id == 3

    def test_fallback_search(self, indexer, mock_db):
        """Test fallback search when FTS is not available."""
        indexer._fts_available = False

        mock_results = [
            (1, "Alice Smith", "alice@example.com", "555-0001"),
        ]
        mock_db.session.execute.return_value.fetchall.return_value = mock_results

        results = indexer.search("alice")

        assert len(results) == 1
        assert results[0].entity_type == EntityType.CONTACT
        assert results[0].title == "Alice Smith"

    def test_update_index_contact(self, indexer, mock_db):
        """Test updating index for a contact."""
        indexer._fts_available = True

        success = indexer.update_index(EntityType.CONTACT, 1)

        assert success is True
        assert mock_db.session.execute.called
        assert mock_db.session.commit.called
        assert indexer._last_index_update is not None

    def test_update_index_failure(self, indexer, mock_db):
        """Test index update failure handling."""
        indexer._fts_available = True
        mock_db.session.execute.side_effect = Exception("Update failed")

        success = indexer.update_index(EntityType.CONTACT, 1)

        assert success is False
        assert mock_db.session.rollback.called

    def test_rebuild_index(self, indexer, mock_db):
        """Test rebuilding the entire index."""
        indexer._fts_available = True

        success = indexer.rebuild_index()

        assert success is True
        # Should have multiple execute calls for deletes and inserts
        assert mock_db.session.execute.call_count >= 6  # 3 deletes + 3 inserts minimum
        assert mock_db.session.commit.called

    def test_get_index_stats(self, indexer, mock_db):
        """Test getting index statistics."""
        indexer._fts_available = True
        indexer._last_index_update = datetime.now()

        # Mock count results
        mock_db.session.execute.return_value.fetchone.side_effect = [
            (100,),  # contacts count
            (50,),  # notes count
            (25,),  # tags count
        ]

        stats = indexer.get_index_stats()

        assert stats["fts_available"] is True
        assert stats["last_update"] is not None
        assert stats["indexed_counts"]["contacts"] == 100
        assert stats["indexed_counts"]["notes"] == 50
        assert stats["indexed_counts"]["tags"] == 25

    def test_optimize_index(self, indexer, mock_db):
        """Test optimizing the FTS index."""
        indexer._fts_available = True

        success = indexer.optimize_index()

        assert success is True
        # Should execute optimize for each FTS table
        assert mock_db.session.execute.call_count == 3  # One optimize per FTS table
        assert mock_db.session.commit.called


class TestSearchResult:
    """Test SearchResult dataclass."""

    def test_search_result_defaults(self):
        """Test SearchResult default values."""
        result = SearchResult(entity_type=EntityType.CONTACT, entity_id=1, title="Test")

        assert result.subtitle is None
        assert result.snippet is None
        assert result.relevance_score == 0.0
        assert result.matched_fields == []
        assert result.metadata == {}

    def test_search_result_full(self):
        """Test SearchResult with all fields."""
        result = SearchResult(
            entity_type=EntityType.NOTE,
            entity_id=42,
            title="Meeting Notes",
            subtitle="Project Discussion",
            snippet="Discussed the <b>project</b> timeline",
            relevance_score=0.95,
            matched_fields=["title", "content"],
            metadata={"author": "Alice"},
        )

        assert result.entity_type == EntityType.NOTE
        assert result.entity_id == 42
        assert result.title == "Meeting Notes"
        assert result.relevance_score == 0.95
        assert "title" in result.matched_fields
        assert result.metadata["author"] == "Alice"


class TestEntityType:
    """Test EntityType enum."""

    def test_entity_type_values(self):
        """Test EntityType enum values."""
        assert EntityType.CONTACT.value == "contact"
        assert EntityType.NOTE.value == "note"
        assert EntityType.TAG.value == "tag"
        assert EntityType.RELATIONSHIP.value == "relationship"
