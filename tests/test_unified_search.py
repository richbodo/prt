"""Test unified search API functionality."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from prt_src.core.search_index.indexer import EntityType
from prt_src.core.search_index.indexer import SearchResult
from prt_src.core.search_unified import SearchPriority
from prt_src.core.search_unified import UnifiedSearchAPI
from prt_src.core.search_unified import UnifiedSearchResult


@pytest.fixture
def mock_db():
    """Create a mock database with session."""
    db = MagicMock()
    db.session = MagicMock()
    return db


@pytest.fixture
def unified_api(mock_db):
    """Create UnifiedSearchAPI with mock database."""
    return UnifiedSearchAPI(mock_db, enable_cache=True)


@pytest.fixture
def sample_search_results():
    """Create sample search results for testing."""
    return [
        SearchResult(
            entity_type=EntityType.CONTACT,
            entity_id=1,
            title="Alice Johnson",
            subtitle="alice@example.com",
            snippet="<b>Alice</b> Johnson",
            relevance_score=0.9,
            matched_fields=["name"],
            metadata={"phone": "555-0001"},
        ),
        SearchResult(
            entity_type=EntityType.NOTE,
            entity_id=10,
            title="Meeting Notes",
            subtitle=None,
            snippet="Discussed project with <b>Alice</b>",
            relevance_score=0.7,
            matched_fields=["content"],
            metadata={},
        ),
        SearchResult(
            entity_type=EntityType.TAG,
            entity_id=5,
            title="important",
            subtitle="3 contacts",
            snippet=None,
            relevance_score=0.5,
            matched_fields=["name"],
            metadata={"contact_count": 3},
        ),
    ]


class TestUnifiedSearchResult:
    """Test UnifiedSearchResult dataclass."""

    def test_from_search_result(self, sample_search_results):
        """Test creating unified result from search result."""
        search_result = sample_search_results[0]
        unified = UnifiedSearchResult.from_search_result(search_result, SearchPriority.EXACT_MATCH)

        assert unified.entity_type == EntityType.CONTACT
        assert unified.entity_id == 1
        assert unified.title == "Alice Johnson"
        assert unified.priority == SearchPriority.EXACT_MATCH
        assert unified.relevance_score == 0.9

    def test_default_values(self):
        """Test default values for UnifiedSearchResult."""
        result = UnifiedSearchResult(entity_type=EntityType.CONTACT, entity_id=1, title="Test")

        assert result.matched_fields == []
        assert result.metadata == {}
        assert result.suggestions == []
        assert result.priority == SearchPriority.PARTIAL_MATCH


class TestUnifiedSearchAPI:
    """Test UnifiedSearchAPI class."""

    def test_empty_search(self, unified_api):
        """Test that empty search returns empty results."""
        results = unified_api.search("")
        assert results["total"] == 0
        assert results["results"] == {}

        results = unified_api.search("   ")
        assert results["total"] == 0

    def test_search_with_cache_hit(self, unified_api):
        """Test search that hits the cache."""
        # Mock cache search
        mock_contacts = [
            MagicMock(
                id=1, name="Alice Johnson", email="alice@example.com", phone="555-0001", tags=[]
            )
        ]
        unified_api.contact_cache.search = MagicMock(return_value=mock_contacts)

        # Mock FTS search (should not be called if cache has results)
        unified_api.indexer.search = MagicMock(return_value=[])

        results = unified_api.search("alice", limit=10)

        assert results["total"] > 0
        assert "contacts" in results["results"]
        assert results["stats"]["cache_used"] is True
        assert unified_api._metrics["cache_hits"] == 1

    def test_search_with_fts(self, unified_api, sample_search_results):
        """Test search using FTS indexer."""
        # Mock cache to return nothing
        unified_api.contact_cache.search = MagicMock(return_value=[])

        # Mock FTS to return results
        unified_api.indexer.search = MagicMock(return_value=sample_search_results)

        results = unified_api.search("alice")

        assert results["total"] == 3
        assert "contacts" in results["results"]
        assert "notes" in results["results"]
        assert "tags" in results["results"]
        assert results["stats"]["fts_used"] is True
        assert unified_api._metrics["fts_searches"] == 1

    def test_search_result_ranking(self, unified_api):
        """Test that results are properly ranked."""
        # Create results with different priorities
        results_to_rank = [
            UnifiedSearchResult(
                entity_type=EntityType.CONTACT,
                entity_id=1,
                title="Alice",
                relevance_score=0.5,
                priority=SearchPriority.PARTIAL_MATCH,
            ),
            UnifiedSearchResult(
                entity_type=EntityType.CONTACT,
                entity_id=2,
                title="Alice Johnson",
                relevance_score=0.9,
                priority=SearchPriority.EXACT_MATCH,
            ),
            UnifiedSearchResult(
                entity_type=EntityType.CONTACT,
                entity_id=3,
                title="Bob Alice",
                relevance_score=0.6,
                priority=SearchPriority.CONTAINS_MATCH,
            ),
        ]

        ranked = unified_api._rank_results(results_to_rank, "alice")

        # Exact match should be first
        assert ranked[0].entity_id == 2
        assert ranked[0].metadata["composite_score"] > ranked[1].metadata["composite_score"]

    def test_result_grouping(self, unified_api):
        """Test that results are grouped by entity type."""
        results = [
            UnifiedSearchResult(entity_type=EntityType.CONTACT, entity_id=1, title="Contact 1"),
            UnifiedSearchResult(entity_type=EntityType.NOTE, entity_id=2, title="Note 1"),
            UnifiedSearchResult(entity_type=EntityType.CONTACT, entity_id=3, title="Contact 2"),
            UnifiedSearchResult(entity_type=EntityType.TAG, entity_id=4, title="Tag 1"),
        ]

        grouped = unified_api._group_results(results)

        assert len(grouped["contacts"]) == 2
        assert len(grouped["notes"]) == 1
        assert len(grouped["tags"]) == 1
        assert "relationships" not in grouped  # Empty groups removed

    def test_result_deduplication(self, unified_api):
        """Test that duplicate results are removed."""
        cache_results = [
            UnifiedSearchResult(entity_type=EntityType.CONTACT, entity_id=1, title="Alice"),
            UnifiedSearchResult(entity_type=EntityType.CONTACT, entity_id=2, title="Bob"),
        ]

        fts_results = [
            UnifiedSearchResult(
                entity_type=EntityType.CONTACT, entity_id=1, title="Alice"
            ),  # Duplicate
            UnifiedSearchResult(entity_type=EntityType.CONTACT, entity_id=3, title="Charlie"),
        ]

        merged = unified_api._merge_results(cache_results, fts_results)

        assert len(merged) == 3  # Not 4
        # Check that IDs are unique
        ids = [r.entity_id for r in merged]
        assert len(ids) == len(set(ids))

    def test_autocomplete(self, unified_api):
        """Test autocomplete functionality."""
        # Mock cache autocomplete
        unified_api.contact_cache.autocomplete = MagicMock(
            return_value=[("Alice Johnson", 1), ("Alice Cooper", 2)]
        )

        suggestions = unified_api.autocomplete("ali", field="name")

        assert len(suggestions) == 2
        assert suggestions[0]["text"] == "Alice Johnson"
        assert suggestions[0]["entity_type"] == "contact"
        assert suggestions[0]["field"] == "name"

    def test_search_suggestions(self, unified_api):
        """Test search suggestion generation."""
        # Add some search history
        unified_api._add_to_history("alice johnson")
        unified_api._add_to_history("alice email")
        unified_api._add_to_history("johnson")

        suggestions = unified_api.get_suggestions("alice", context=None)

        assert "alice johnson" in suggestions
        assert "alice email" in suggestions

    def test_search_history_tracking(self, unified_api):
        """Test that search history is tracked."""
        unified_api.search("test query 1")
        unified_api.search("test query 2")
        unified_api.search("test query 1")  # Repeat

        stats = unified_api.get_stats()

        assert "test query 1" in stats["recent_searches"]
        assert "test query 2" in stats["recent_searches"]
        assert stats["popular_searches"]["test query 1"] == 2

    def test_search_metrics(self, unified_api):
        """Test that search metrics are tracked."""
        # Mock to control timing - need more values for time.time() calls
        with patch("time.time") as mock_time:
            # Each search calls time.time() multiple times:
            # 1. Start time, 2. History timestamp, 3. End time
            mock_time.side_effect = [0.0, 0.0, 0.1, 0.1, 0.1, 0.2]

            unified_api.search("query1")
            unified_api.search("query2")

        assert unified_api._metrics["total_searches"] == 2
        assert unified_api._metrics["avg_search_time"] == 0.1

    def test_warm_cache(self, unified_api):
        """Test cache warming."""
        contacts = [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
        ]

        unified_api.contact_cache.warm_cache = MagicMock()
        unified_api.warm_cache(contacts)

        unified_api.contact_cache.warm_cache.assert_called_once_with(contacts)

    def test_rebuild_index(self, unified_api):
        """Test index rebuilding."""
        unified_api.indexer.rebuild_index = MagicMock(return_value=True)

        result = unified_api.rebuild_index()

        assert result is True
        unified_api.indexer.rebuild_index.assert_called_once()

    def test_optimize_index(self, unified_api):
        """Test index optimization."""
        unified_api.indexer.optimize_index = MagicMock(return_value=True)

        result = unified_api.optimize_index()

        assert result is True
        unified_api.indexer.optimize_index.assert_called_once()

    def test_clear_cache(self, unified_api):
        """Test cache clearing."""
        unified_api.contact_cache.clear_cache = MagicMock()

        unified_api.clear_cache()

        unified_api.contact_cache.clear_cache.assert_called_once()

    def test_get_stats(self, unified_api):
        """Test getting comprehensive statistics."""
        # Mock component stats
        unified_api.indexer.get_index_stats = MagicMock(
            return_value={"fts_available": True, "indexed_counts": {"contacts": 100}}
        )
        unified_api.contact_cache.get_stats = MagicMock(
            return_value={"cache_size": 50, "hit_rate": 0.8}
        )

        # Do some searches to generate stats
        unified_api.search("test")

        stats = unified_api.get_stats()

        assert "metrics" in stats
        assert "indexer" in stats
        assert "cache" in stats
        assert "popular_searches" in stats
        assert "recent_searches" in stats

    def test_search_with_entity_type_filter(self, unified_api, sample_search_results):
        """Test searching specific entity types."""
        unified_api.indexer.search = MagicMock(return_value=[sample_search_results[0]])

        _ = unified_api.search("alice", entity_types=[EntityType.CONTACT])

        # Should only search contacts
        from unittest.mock import ANY

        unified_api.indexer.search.assert_called_with("alice", [EntityType.CONTACT], ANY)

    def test_priority_determination(self, unified_api):
        """Test priority determination logic."""
        assert unified_api._determine_priority("alice", "Alice") == SearchPriority.EXACT_MATCH
        assert unified_api._determine_priority("ali", "Alice") == SearchPriority.PREFIX_MATCH
        assert unified_api._determine_priority("ice", "Alice") == SearchPriority.CONTAINS_MATCH
        assert unified_api._determine_priority("xyz", "Alice") == SearchPriority.PARTIAL_MATCH

    def test_search_suggestions_with_results(self, unified_api):
        """Test suggestion generation when results exist."""
        results = [
            UnifiedSearchResult(
                entity_type=EntityType.CONTACT,
                entity_id=1,
                title="Alice",
                matched_fields=["name", "email"],
            ),
            UnifiedSearchResult(
                entity_type=EntityType.NOTE,
                entity_id=2,
                title="Note",
                matched_fields=["content"],
            ),
        ]

        suggestions = unified_api._generate_suggestions("alice", results)

        # Should suggest entity-specific searches
        assert any("contacts:" in s for s in suggestions)
        assert any("email:" in s for s in suggestions)

    def test_search_suggestions_no_results(self, unified_api):
        """Test suggestion generation when no results."""
        suggestions = unified_api._generate_suggestions("alice johnson smith", [])

        # Should suggest simpler queries
        assert "alice" in suggestions  # First word
        assert "alice johnson" in suggestions  # Remove last word

    def test_search_without_cache(self):
        """Test search with cache disabled."""
        db = MagicMock()
        api = UnifiedSearchAPI(db, enable_cache=False)

        assert api.contact_cache is None

        # Should still work with FTS only - mock to return at least one result
        from prt_src.core.search_index.indexer import EntityType
        from prt_src.core.search_index.indexer import SearchResult

        api.indexer.search = MagicMock(
            return_value=[SearchResult(entity_type=EntityType.CONTACT, entity_id=1, title="Test")]
        )
        results = api.search("test")

        assert results["stats"]["cache_used"] is False
        assert results["stats"]["fts_used"] is True

    def test_search_sources_tracking(self, unified_api):
        """Test that search sources are properly tracked."""
        # Mock both cache and FTS to return results
        unified_api.contact_cache.search = MagicMock(
            return_value=[MagicMock(id=1, name="Alice", email="", phone="", tags=[])]
        )
        unified_api.indexer.search = MagicMock(
            return_value=[SearchResult(entity_type=EntityType.NOTE, entity_id=2, title="Note")]
        )

        results = unified_api.search("test")

        assert "cache" in results["stats"]["sources"]
        assert "fts" in results["stats"]["sources"]

    def test_popular_searches_limit(self, unified_api):
        """Test that popular searches are limited in stats."""
        # Add many different searches
        for i in range(20):
            unified_api._add_to_history(f"query{i}")

        stats = unified_api.get_stats()

        # Should only show top 10
        assert len(stats["popular_searches"]) <= 10

    def test_search_history_limit(self, unified_api):
        """Test that search history has a limit."""
        # Add more than 100 searches
        for i in range(150):
            unified_api._add_to_history(f"query{i}")

        assert len(unified_api._search_history) == 100  # Limited to 100

    def test_cache_search_error_handling(self, unified_api):
        """Test that cache search errors are handled gracefully."""
        # Mock the cache to raise an exception
        unified_api.contact_cache.search = MagicMock(
            side_effect=Exception("Database connection lost")
        )

        # Search should still work (falling back to FTS)
        results = unified_api.search("test query")

        # Should get results from FTS even though cache failed
        assert results is not None
        assert results["total"] >= 0
        assert "results" in results

    def test_fts_search_error_handling(self, unified_api):
        """Test that FTS search errors are handled gracefully."""
        # Mock the indexer to raise an exception
        unified_api.indexer.search = MagicMock(side_effect=Exception("FTS index corrupted"))

        # Mock cache to return some results
        if unified_api.contact_cache:
            unified_api.contact_cache.search = MagicMock(
                return_value=[
                    MagicMock(
                        id=1,
                        name="Cache Result",
                        email="cache@example.com",
                        phone="555-0001",
                        tags=[],
                    )
                ]
            )

        # Search should still work with cache results only
        results = unified_api.search("test")

        # Should get results from cache even though FTS failed
        assert results is not None
        assert results["total"] >= 0

    def test_popular_searches_memory_management(self, unified_api):
        """Test that popular searches memory is bounded."""
        # Add more searches than MAX_POPULAR_SEARCHES
        for i in range(1500):
            unified_api._add_to_history(f"unique_query_{i}")

        # Popular searches should be bounded
        assert len(unified_api._popular_searches) <= unified_api.MAX_POPULAR_SEARCHES

        # Should keep the most popular ones (those with higher counts)
        # Add repeated searches to ensure they're kept
        for _ in range(10):
            unified_api._add_to_history("frequent_query")

        assert "frequent_query" in unified_api._popular_searches
        assert unified_api._popular_searches["frequent_query"] == 10

    def test_both_search_sources_fail(self, unified_api):
        """Test graceful handling when both cache and FTS fail."""
        # Mock both to fail
        if unified_api.contact_cache:
            unified_api.contact_cache.search = MagicMock(side_effect=Exception("Cache error"))
        unified_api.indexer.search = MagicMock(side_effect=Exception("FTS error"))

        # Search should return empty results but not crash
        results = unified_api.search("test")

        assert results is not None
        assert results["total"] == 0
        assert results["results"] == {}
        assert "stats" in results
