"""Autocomplete engine for context-aware suggestions.

Provides intelligent autocomplete with context awareness,
fuzzy matching, and integration with search infrastructure.
"""

from dataclasses import dataclass
from dataclasses import field
from difflib import SequenceMatcher
from enum import Enum
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from prt_src.logging_config import get_logger

logger = get_logger(__name__)


class SuggestionSource(Enum):
    """Source of autocomplete suggestions."""

    CACHE = "cache"
    DATABASE = "database"
    HISTORY = "history"
    POPULAR = "popular"


@dataclass
class AutocompleteContext:
    """Context for autocomplete suggestions."""

    entity_type: Optional[str] = None
    current_field: Optional[str] = None
    include_history: bool = True
    include_popular: bool = True
    exclude_ids: Optional[List[int]] = None
    current_selections: Optional[List[str]] = None


@dataclass
class Suggestion:
    """A single autocomplete suggestion."""

    text: str
    source: SuggestionSource
    score: float = 1.0
    entity_id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AutocompleteConfig:
    """Configuration for autocomplete engine."""

    min_query_length: int = 1
    max_suggestions: int = 10
    enable_fuzzy: bool = False
    fuzzy_threshold: float = 0.6
    include_scores: bool = False
    debounce_ms: int = 100


class AutocompleteEngine:
    """Main autocomplete engine with context awareness."""

    def __init__(
        self,
        search_api=None,
        contact_cache=None,
        config: Optional[AutocompleteConfig] = None,
        min_query_length: Optional[int] = None,
        max_suggestions: Optional[int] = None,
        enable_fuzzy: Optional[bool] = None,
        fuzzy_threshold: Optional[float] = None,
    ):
        """Initialize autocomplete engine.

        Args:
            search_api: UnifiedSearchAPI instance
            contact_cache: ContactSearchCache instance
            config: AutocompleteConfig instance
            min_query_length: Minimum query length
            max_suggestions: Maximum suggestions to return
            enable_fuzzy: Enable fuzzy matching
            fuzzy_threshold: Fuzzy match threshold
        """
        if config:
            self.config = config
        else:
            self.config = AutocompleteConfig()

        # Override config with individual parameters if provided
        if min_query_length is not None:
            self.min_query_length = min_query_length
        else:
            self.min_query_length = self.config.min_query_length

        if max_suggestions is not None:
            self.max_suggestions = max_suggestions
        else:
            self.max_suggestions = self.config.max_suggestions

        if enable_fuzzy is not None:
            self.enable_fuzzy = enable_fuzzy
        else:
            self.enable_fuzzy = self.config.enable_fuzzy

        if fuzzy_threshold is not None:
            self.fuzzy_threshold = fuzzy_threshold
        else:
            self.fuzzy_threshold = self.config.fuzzy_threshold

        self.search_api = search_api
        self.contact_cache = contact_cache
        self._items: List[Dict[str, Any]] = []
        self._last_query_time = 0

    def set_items(self, items: List[Dict[str, Any]]):
        """Set items for autocomplete.

        Args:
            items: List of items to autocomplete from
        """
        self._items = items

    def get_suggestions(
        self, query: str, context: Optional[AutocompleteContext] = None
    ) -> List[Suggestion]:
        """Get autocomplete suggestions for query.

        Args:
            query: Query string
            context: Optional context for suggestions

        Returns:
            List of suggestions
        """
        # Handle empty or whitespace query
        if not query or not query.strip():
            return []

        query = query.strip()

        # Check minimum query length
        if len(query) < self.min_query_length:
            return []

        suggestions = []

        # Get suggestions from various sources
        if self.contact_cache:
            suggestions.extend(self._get_cache_suggestions(query, context))

        if self.search_api and context:
            if context.include_history:
                suggestions.extend(self._get_history_suggestions(query, context))
            if context.include_popular:
                suggestions.extend(self._get_popular_suggestions(query, context))

        # Get suggestions from items
        suggestions.extend(self._get_item_suggestions(query, context))

        # Filter based on context
        if context:
            suggestions = self.filter_suggestions(suggestions, context)

        # Rank and sort suggestions
        suggestions = self.rank_suggestions(suggestions)

        # Apply limit
        return suggestions[: self.max_suggestions]

    def _get_cache_suggestions(
        self, query: str, context: Optional[AutocompleteContext]
    ) -> List[Suggestion]:
        """Get suggestions from contact cache.

        Args:
            query: Query string
            context: Optional context

        Returns:
            List of suggestions from cache
        """
        suggestions = []

        try:
            # Use cache's autocomplete method
            cache_results = self.contact_cache.autocomplete(query)

            for name, contact_id in cache_results[: self.max_suggestions]:
                suggestions.append(
                    Suggestion(
                        text=name, source=SuggestionSource.CACHE, entity_id=contact_id, score=1.0
                    )
                )
        except Exception as e:
            logger.debug(f"Error getting cache suggestions: {e}")

        return suggestions

    def _get_history_suggestions(
        self, query: str, context: AutocompleteContext
    ) -> List[Suggestion]:
        """Get suggestions from search history.

        Args:
            query: Query string
            context: Context for suggestions

        Returns:
            List of suggestions from history
        """
        suggestions = []

        try:
            # Get from search history
            if hasattr(self.search_api, "_search_history"):
                for search_text, _timestamp in self.search_api._search_history:
                    if query.lower() in search_text.lower():
                        suggestions.append(
                            Suggestion(text=search_text, source=SuggestionSource.HISTORY, score=0.8)
                        )
        except Exception as e:
            logger.debug(f"Error getting history suggestions: {e}")

        return suggestions

    def _get_popular_suggestions(
        self, query: str, context: AutocompleteContext
    ) -> List[Suggestion]:
        """Get suggestions from popular searches.

        Args:
            query: Query string
            context: Context for suggestions

        Returns:
            List of suggestions from popular searches
        """
        suggestions = []

        try:
            # Get from popular searches
            if hasattr(self.search_api, "_popular_searches"):
                for search_term, count in self.search_api._popular_searches.items():
                    if query.lower() in search_term.lower():
                        suggestions.append(
                            Suggestion(
                                text=search_term,
                                source=SuggestionSource.POPULAR,
                                score=0.7 + (count * 0.01),  # Higher count = higher score
                            )
                        )
        except Exception as e:
            logger.debug(f"Error getting popular suggestions: {e}")

        return suggestions

    def _get_item_suggestions(
        self, query: str, context: Optional[AutocompleteContext]
    ) -> List[Suggestion]:
        """Get suggestions from stored items.

        Args:
            query: Query string
            context: Optional context

        Returns:
            List of suggestions from items
        """
        suggestions = []
        query_lower = query.lower()

        for item in self._items:
            # Determine which field to search
            if context and context.current_field:
                field_value = str(item.get(context.current_field, ""))
            else:
                # Default to name field
                field_value = str(item.get("name", ""))

            field_value_lower = field_value.lower()

            # Check for match
            if self.enable_fuzzy:
                # Fuzzy matching
                similarity = self._fuzzy_match(query_lower, field_value_lower)
                if similarity >= self.fuzzy_threshold:
                    suggestions.append(
                        Suggestion(
                            text=field_value,
                            source=SuggestionSource.DATABASE,
                            entity_id=item.get("id"),
                            score=similarity,
                            metadata={"email": item.get("email"), "tags": item.get("tags", [])},
                        )
                    )
            else:
                # Prefix matching and substring matching
                if field_value_lower.startswith(query_lower):
                    # Exact match gets highest score
                    score = 1.0 if field_value_lower == query_lower else 0.9
                    suggestions.append(
                        Suggestion(
                            text=field_value,
                            source=SuggestionSource.DATABASE,
                            entity_id=item.get("id"),
                            score=score,
                            metadata={"email": item.get("email"), "tags": item.get("tags", [])},
                        )
                    )
                elif query_lower in field_value_lower:
                    # Substring match gets lower score
                    suggestions.append(
                        Suggestion(
                            text=field_value,
                            source=SuggestionSource.DATABASE,
                            entity_id=item.get("id"),
                            score=0.7,
                            metadata={"email": item.get("email"), "tags": item.get("tags", [])},
                        )
                    )

        return suggestions

    def _fuzzy_match(self, query: str, text: str) -> float:
        """Calculate fuzzy match score.

        Args:
            query: Query string
            text: Text to match against

        Returns:
            Similarity score (0-1)
        """
        # Check for exact match
        if query == text:
            return 1.0

        # Check if query is a substring
        if query in text:
            # Prefix match is better than substring
            if text.startswith(query):
                return 0.95
            return 0.85

        # Check for transposed characters (e.g., "jhon" vs "john")
        if len(query) <= len(text):
            # Check if it's likely a typo by comparing sorted characters
            query_sorted = sorted(query)
            for i in range(len(text) - len(query) + 1):
                substring = text[i : i + len(query)]
                if sorted(substring) == query_sorted:
                    # Found a substring with same characters
                    return 0.75

        # Use SequenceMatcher for general similarity
        matcher = SequenceMatcher(None, query, text)
        ratio = matcher.ratio()

        # Check for close substring matches (e.g., "xris" matching "hris" in "christopher")
        if len(query) >= 3:
            best_substring_ratio = 0
            for i in range(len(text) - len(query) + 1):
                substring = text[i : i + len(query)]
                sub_matcher = SequenceMatcher(None, query, substring)
                sub_ratio = sub_matcher.ratio()
                best_substring_ratio = max(best_substring_ratio, sub_ratio)

            # If we found a good substring match, use it
            if best_substring_ratio >= 0.75:
                return max(
                    ratio, best_substring_ratio * 0.8
                )  # Scale down slightly since it's not exact

        # Boost score if query appears at start of any word in text
        words = text.split()
        for word in words:
            if word.lower().startswith(query):
                return max(ratio, 0.8)

        return ratio

    def filter_suggestions(
        self, suggestions: List[Suggestion], context: AutocompleteContext
    ) -> List[Suggestion]:
        """Filter suggestions based on context.

        Args:
            suggestions: List of suggestions
            context: Context for filtering

        Returns:
            Filtered list of suggestions
        """
        filtered = []

        # Convert current selections to lowercase for comparison
        current_selections_lower = []
        if context.current_selections:
            current_selections_lower = [s.lower() for s in context.current_selections]

        for suggestion in suggestions:
            # Exclude already selected items
            if suggestion.text.lower() in current_selections_lower:
                continue

            # Exclude by ID
            if context.exclude_ids and suggestion.entity_id in context.exclude_ids:
                continue

            filtered.append(suggestion)

        return filtered

    def rank_suggestions(self, suggestions: List[Suggestion]) -> List[Suggestion]:
        """Rank suggestions by score and source priority.

        Args:
            suggestions: List of suggestions

        Returns:
            Ranked list of suggestions
        """
        # Apply source-based score adjustments
        for suggestion in suggestions:
            if suggestion.source == SuggestionSource.CACHE:
                suggestion.score *= 1.2  # Boost cache results
            elif suggestion.source == SuggestionSource.HISTORY:
                suggestion.score *= 1.1  # Slight boost for history
            elif suggestion.source == SuggestionSource.POPULAR:
                suggestion.score *= 1.05  # Small boost for popular

        # Sort by score (highest first)
        return sorted(suggestions, key=lambda s: s.score, reverse=True)
