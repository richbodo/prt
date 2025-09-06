"""Test autocomplete engine for context-aware suggestions.

TDD approach - writing tests first before implementation.
Tests cover autocomplete with context awareness and integration with existing search.
"""

from unittest.mock import MagicMock

import pytest

# These imports will fail initially - that's expected in TDD
from prt_src.core.components.autocomplete import AutocompleteConfig
from prt_src.core.components.autocomplete import AutocompleteContext
from prt_src.core.components.autocomplete import AutocompleteEngine
from prt_src.core.components.autocomplete import Suggestion
from prt_src.core.components.autocomplete import SuggestionSource


class TestAutocompleteEngine:
    """Test core autocomplete functionality."""

    @pytest.fixture
    def mock_search_api(self):
        """Create a mock UnifiedSearchAPI."""
        mock = MagicMock()
        mock._search_history = [
            ("John Doe", 1704067200),
            ("Jane Smith", 1704067100),
            ("Alice Johnson", 1704067000),
        ]
        mock._popular_searches = {
            "john": 5,
            "jane": 3,
            "alice": 2,
            "bob": 1,
        }
        return mock

    @pytest.fixture
    def mock_contact_cache(self):
        """Create a mock ContactSearchCache."""
        mock = MagicMock()
        mock.autocomplete = MagicMock(
            return_value=[
                ("John Doe", 1),
                ("John Smith", 2),
                ("Johnny Appleseed", 3),
            ]
        )
        return mock

    def test_basic_autocomplete(self, mock_search_api, mock_contact_cache):
        """Test basic autocomplete functionality."""
        engine = AutocompleteEngine(search_api=mock_search_api, contact_cache=mock_contact_cache)

        suggestions = engine.get_suggestions("joh")

        assert len(suggestions) > 0
        # Should include results from cache
        assert any(s.text == "John Doe" for s in suggestions)
        assert any(s.text == "John Smith" for s in suggestions)

    def test_empty_query(self):
        """Test that empty query returns no suggestions."""
        engine = AutocompleteEngine()

        suggestions = engine.get_suggestions("")
        assert suggestions == []

        suggestions = engine.get_suggestions("   ")
        assert suggestions == []

    def test_min_query_length(self):
        """Test minimum query length requirement."""
        engine = AutocompleteEngine(min_query_length=3)

        # Too short
        suggestions = engine.get_suggestions("jo")
        assert suggestions == []

        # Long enough
        suggestions = engine.get_suggestions("joh")
        assert suggestions is not None  # May be empty but not None

    def test_max_suggestions_limit(self, mock_search_api, mock_contact_cache):
        """Test that suggestions are limited to max count."""
        engine = AutocompleteEngine(
            search_api=mock_search_api, contact_cache=mock_contact_cache, max_suggestions=5
        )

        # Mock cache to return many results
        mock_contact_cache.autocomplete.return_value = [(f"Contact {i}", i) for i in range(20)]

        suggestions = engine.get_suggestions("con")
        assert len(suggestions) <= 5


class TestContextAwareSuggestions:
    """Test context-aware suggestion generation."""

    @pytest.fixture
    def mock_search_api(self):
        """Create a mock UnifiedSearchAPI."""
        mock = MagicMock()
        mock._search_history = [
            ("John Doe", 1704067200),
            ("Jane Smith", 1704067100),
            ("Alice Johnson", 1704067000),
        ]
        mock._popular_searches = {
            "john": 5,
            "jane": 3,
            "alice": 2,
            "bob": 1,
        }
        return mock

    @pytest.fixture
    def mock_contact_cache(self):
        """Create a mock ContactSearchCache."""
        mock = MagicMock()
        mock.autocomplete = MagicMock(
            return_value=[
                ("John Doe", 1),
                ("John Smith", 2),
                ("Johnny Appleseed", 3),
            ]
        )
        return mock

    def test_entity_type_context(self, mock_search_api):
        """Test suggestions based on entity type context."""
        engine = AutocompleteEngine(search_api=mock_search_api)

        # Context for contact search
        contact_context = AutocompleteContext(entity_type="contact", current_field="name")
        suggestions = engine.get_suggestions("joh", context=contact_context)
        # Should include results from history and popular (no cache without mock_contact_cache)
        assert len(suggestions) > 0
        assert any(s.source == SuggestionSource.HISTORY for s in suggestions)

        # Context for tag search
        tag_context = AutocompleteContext(entity_type="tag", current_field="name")
        suggestions = engine.get_suggestions("fam", context=tag_context)
        # Should prioritize tag-related suggestions

    def test_search_history_context(self, mock_search_api):
        """Test using search history for suggestions."""
        engine = AutocompleteEngine(search_api=mock_search_api)

        context = AutocompleteContext(entity_type="contact", include_history=True)

        suggestions = engine.get_suggestions("ali", context=context)

        # Should include Alice from history
        assert any("Alice" in s.text for s in suggestions)

    def test_popular_searches_context(self, mock_search_api):
        """Test using popular searches for suggestions."""
        engine = AutocompleteEngine(search_api=mock_search_api)

        context = AutocompleteContext(entity_type="contact", include_popular=True)

        suggestions = engine.get_suggestions("j", context=context)

        # Should prioritize "john" over "jane" (5 searches vs 3)
        john_suggestions = [s for s in suggestions if "john" in s.text.lower()]
        jane_suggestions = [s for s in suggestions if "jane" in s.text.lower()]

        if john_suggestions and jane_suggestions:
            # John should appear before Jane due to popularity
            john_index = suggestions.index(john_suggestions[0])
            jane_index = suggestions.index(jane_suggestions[0])
            assert john_index < jane_index

    def test_current_selections_context(self):
        """Test excluding already selected items from suggestions."""
        engine = AutocompleteEngine()

        # Context with already selected items
        context = AutocompleteContext(
            entity_type="contact",
            exclude_ids=[1, 2, 3],
            current_selections=["John Doe", "Jane Smith"],
        )

        # Mock some suggestions
        all_suggestions = [
            Suggestion("John Doe", SuggestionSource.CACHE, entity_id=1),
            Suggestion("Jane Smith", SuggestionSource.CACHE, entity_id=2),
            Suggestion("Bob Wilson", SuggestionSource.CACHE, entity_id=4),
        ]

        # Filter based on context
        filtered = engine.filter_suggestions(all_suggestions, context)

        # Should exclude already selected
        assert not any(s.text == "John Doe" for s in filtered)
        assert not any(s.text == "Jane Smith" for s in filtered)
        assert any(s.text == "Bob Wilson" for s in filtered)


class TestFuzzyMatching:
    """Test fuzzy matching capabilities."""

    def test_fuzzy_match_typos(self):
        """Test fuzzy matching handles typos."""
        engine = AutocompleteEngine(enable_fuzzy=True)

        # Add some known items to match against
        engine.set_items(
            [
                {"id": 1, "name": "John Doe"},
                {"id": 2, "name": "Jane Smith"},
                {"id": 3, "name": "Alice Johnson"},
            ]
        )

        # Test with typo
        suggestions = engine.get_suggestions("jhon")  # Typo: jhon instead of john
        assert any("John" in s.text for s in suggestions)

        # Test with missing letter
        suggestions = engine.get_suggestions("alic")  # Missing 'e'
        assert any("Alice" in s.text for s in suggestions)

    def test_fuzzy_threshold(self):
        """Test fuzzy matching threshold configuration."""
        # Strict threshold - requires closer matches
        strict_engine = AutocompleteEngine(enable_fuzzy=True, fuzzy_threshold=0.9)
        strict_engine.set_items([{"id": 1, "name": "Christopher"}])

        suggestions = strict_engine.get_suggestions("chris")
        assert len(suggestions) > 0

        suggestions = strict_engine.get_suggestions("xris")  # Too different
        assert len(suggestions) == 0

        # Loose threshold - allows more distant matches
        loose_engine = AutocompleteEngine(enable_fuzzy=True, fuzzy_threshold=0.5)
        loose_engine.set_items([{"id": 1, "name": "Christopher"}])

        suggestions = loose_engine.get_suggestions("xris")
        assert len(suggestions) > 0  # Should match despite bigger difference


class TestSuggestionRanking:
    """Test suggestion ranking and scoring."""

    @pytest.fixture
    def mock_search_api(self):
        """Create a mock UnifiedSearchAPI."""
        mock = MagicMock()
        mock._search_history = [
            ("John Doe", 1704067200),
            ("Jane Smith", 1704067100),
            ("Alice Johnson", 1704067000),
        ]
        mock._popular_searches = {
            "john": 5,
            "jane": 3,
            "alice": 2,
            "bob": 1,
        }
        return mock

    @pytest.fixture
    def mock_contact_cache(self):
        """Create a mock ContactSearchCache."""
        mock = MagicMock()
        mock.autocomplete = MagicMock(
            return_value=[
                ("John Doe", 1),
                ("John Smith", 2),
                ("Johnny Appleseed", 3),
            ]
        )
        return mock

    def test_suggestion_scoring(self, mock_search_api, mock_contact_cache):
        """Test that suggestions are scored and ranked."""
        engine = AutocompleteEngine(search_api=mock_search_api, contact_cache=mock_contact_cache)

        suggestions = engine.get_suggestions("john")

        # All suggestions should have scores
        assert all(hasattr(s, "score") and s.score is not None for s in suggestions)

        # Should be sorted by score (highest first)
        scores = [s.score for s in suggestions]
        assert scores == sorted(scores, reverse=True)

    def test_source_priority(self):
        """Test that different sources have different priorities."""
        engine = AutocompleteEngine()

        suggestions = [
            Suggestion("John (History)", SuggestionSource.HISTORY, score=0.5),
            Suggestion("John (Cache)", SuggestionSource.CACHE, score=0.5),
            Suggestion("John (Popular)", SuggestionSource.POPULAR, score=0.5),
            Suggestion("John (Database)", SuggestionSource.DATABASE, score=0.5),
        ]

        # Apply source-based scoring adjustments
        ranked = engine.rank_suggestions(suggestions)

        # Cache should typically rank higher than database
        cache_idx = next(i for i, s in enumerate(ranked) if s.source == SuggestionSource.CACHE)
        db_idx = next(i for i, s in enumerate(ranked) if s.source == SuggestionSource.DATABASE)
        assert cache_idx < db_idx

    def test_exact_match_priority(self):
        """Test that exact matches get highest priority."""
        engine = AutocompleteEngine()
        engine.set_items(
            [
                {"id": 1, "name": "John"},
                {"id": 2, "name": "Johnny"},
                {"id": 3, "name": "Johnson"},
                {"id": 4, "name": "John Doe"},
            ]
        )

        suggestions = engine.get_suggestions("john")

        # Exact match "John" should be first
        assert suggestions[0].text == "John"


class TestAutocompleteIntegration:
    """Test integration with existing search infrastructure."""

    def test_integration_with_unified_search(self):
        """Test integration with UnifiedSearchAPI."""
        from prt_src.core.search_unified import UnifiedSearchAPI

        # Create real UnifiedSearchAPI with mock database
        mock_db = MagicMock()
        search_api = UnifiedSearchAPI(mock_db)

        # Create autocomplete engine with real search API
        engine = AutocompleteEngine(search_api=search_api)

        # Should be able to get suggestions (even if empty with mock db)
        suggestions = engine.get_suggestions("test")
        assert suggestions is not None

    def test_integration_with_contact_cache(self):
        """Test integration with ContactSearchCache."""
        from prt_src.core.search_cache.contact_cache import ContactSearchCache

        # Create real cache
        cache = ContactSearchCache()

        # Add some contacts
        from prt_src.core.search_cache.contact_cache import CachedContact

        cache.add_contact(CachedContact(id=1, name="John Doe", email="john@example.com"))

        # Create engine with real cache
        engine = AutocompleteEngine(contact_cache=cache)

        suggestions = engine.get_suggestions("joh")
        assert any("John Doe" in s.text for s in suggestions)

    def test_performance_with_large_dataset(self):
        """Test autocomplete performance with many items."""
        engine = AutocompleteEngine(max_suggestions=10)

        # Create large dataset
        large_dataset = [{"id": i, "name": f"Person {i:05d}"} for i in range(5000)]
        engine.set_items(large_dataset)

        # Should return quickly even with large dataset
        import time

        start = time.time()
        suggestions = engine.get_suggestions("Person 001")
        elapsed = time.time() - start

        assert elapsed < 0.1  # Should complete in under 100ms
        assert len(suggestions) <= 10  # Respects limit


class TestAutocompleteConfig:
    """Test autocomplete configuration options."""

    def test_custom_configuration(self):
        """Test custom autocomplete configuration."""
        config = AutocompleteConfig(
            min_query_length=2,
            max_suggestions=20,
            enable_fuzzy=True,
            fuzzy_threshold=0.7,
            include_scores=True,
            debounce_ms=150,
        )

        engine = AutocompleteEngine(config=config)

        assert engine.min_query_length == 2
        assert engine.max_suggestions == 20
        assert engine.enable_fuzzy is True
        assert engine.fuzzy_threshold == 0.7

    def test_field_specific_autocomplete(self):
        """Test autocomplete for specific fields."""
        engine = AutocompleteEngine()

        # Add items with multiple fields
        engine.set_items(
            [
                {"id": 1, "name": "John Doe", "email": "john@example.com", "phone": "555-0001"},
                {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "phone": "555-0002"},
            ]
        )

        # Autocomplete on email field
        context = AutocompleteContext(current_field="email")
        suggestions = engine.get_suggestions("john@", context=context)
        assert any("john@example.com" in s.text for s in suggestions)

        # Autocomplete on phone field
        context = AutocompleteContext(current_field="phone")
        suggestions = engine.get_suggestions("555", context=context)
        assert any("555-0001" in s.text for s in suggestions)

    def test_suggestion_metadata(self):
        """Test that suggestions include useful metadata."""
        engine = AutocompleteEngine()
        engine.set_items(
            [{"id": 1, "name": "John Doe", "email": "john@example.com", "tags": ["friend", "work"]}]
        )

        suggestions = engine.get_suggestions("john")

        # Should include metadata
        john_suggestion = next((s for s in suggestions if "John Doe" in s.text), None)
        assert john_suggestion is not None
        assert john_suggestion.entity_id == 1
        assert hasattr(john_suggestion, "metadata")
        assert john_suggestion.metadata.get("email") == "john@example.com"
