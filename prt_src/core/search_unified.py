"""Unified search API for PRT.

This module provides a unified interface for searching across all entities,
integrating FTS5, the search indexer, and contact cache for optimal performance.
"""

import time
from dataclasses import dataclass
from enum import IntEnum
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple

from prt_src.core.search_cache.contact_cache import ContactSearchCache
from prt_src.core.search_index.indexer import EntityType
from prt_src.core.search_index.indexer import SearchIndexer
from prt_src.core.search_index.indexer import SearchResult
from prt_src.logging_config import get_logger


class SearchPriority(IntEnum):
    """Priority levels for search results."""

    EXACT_MATCH = 100
    PREFIX_MATCH = 80
    CONTAINS_MATCH = 60
    FUZZY_MATCH = 40
    PARTIAL_MATCH = 20


@dataclass
class UnifiedSearchResult:
    """Represents a unified search result with enhanced metadata."""

    entity_type: EntityType
    entity_id: int
    title: str
    subtitle: Optional[str] = None
    snippet: Optional[str] = None
    relevance_score: float = 0.0
    priority: SearchPriority = SearchPriority.PARTIAL_MATCH
    matched_fields: List[str] = None
    metadata: Dict[str, Any] = None
    suggestions: List[str] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.matched_fields is None:
            self.matched_fields = []
        if self.metadata is None:
            self.metadata = {}
        if self.suggestions is None:
            self.suggestions = []

    @classmethod
    def from_search_result(cls, result: SearchResult, priority: SearchPriority = None):
        """Create from a SearchResult object."""
        return cls(
            entity_type=result.entity_type,
            entity_id=result.entity_id,
            title=result.title,
            subtitle=result.subtitle,
            snippet=result.snippet,
            relevance_score=result.relevance_score,
            priority=priority or SearchPriority.PARTIAL_MATCH,
            matched_fields=result.matched_fields,
            metadata=result.metadata,
        )


class UnifiedSearchAPI:
    """Unified search API integrating all search components.

    This API provides:
    - Integrated search across FTS5, indexer, and cache
    - Smart result ranking and grouping
    - Autocomplete and search suggestions
    - Performance optimization through caching
    - Search history and analytics
    """

    def __init__(self, db, max_results: int = 100, enable_cache: bool = True):
        """Initialize the unified search API.

        Args:
            db: Database connection object
            max_results: Maximum results to return
            enable_cache: Whether to use contact cache
        """
        self.db = db
        self.logger = get_logger(__name__)
        self.max_results = max_results
        self.enable_cache = enable_cache

        # Initialize components
        self.indexer = SearchIndexer(db)
        self.contact_cache = ContactSearchCache() if enable_cache else None

        # Search history for suggestions
        self._search_history: List[Tuple[str, float]] = []
        self._popular_searches: Dict[str, int] = {}

        # Memory management constants
        self.MAX_POPULAR_SEARCHES = 1000
        self.MAX_HISTORY_SIZE = 100

        # Performance metrics
        self._metrics = {
            "total_searches": 0,
            "avg_search_time": 0.0,
            "cache_hits": 0,
            "fts_searches": 0,
        }

    def search(
        self,
        query: str,
        entity_types: Optional[List[EntityType]] = None,
        limit: Optional[int] = None,
        include_suggestions: bool = True,
        use_cache_first: bool = True,
    ) -> Dict[str, Any]:
        """Perform a unified search across all entities.

        Args:
            query: Search query string
            entity_types: Entity types to search (None = all)
            limit: Maximum results (overrides default)
            include_suggestions: Whether to include search suggestions
            use_cache_first: Whether to check cache before FTS

        Returns:
            Dict containing:
                - results: Grouped search results
                - suggestions: Search suggestions
                - stats: Search statistics
        """
        start_time = time.time()
        self._metrics["total_searches"] += 1

        if not query or not query.strip():
            return self._empty_result()

        # Track search for suggestions
        self._add_to_history(query)

        # Determine limit
        limit = limit or self.max_results

        # Get results from different sources
        all_results = []

        # 1. Check contact cache first (if enabled and searching contacts)
        cache_results = []
        if (
            use_cache_first
            and self.contact_cache
            and (entity_types is None or EntityType.CONTACT in entity_types)
        ):
            cache_results = self._search_cache(query, limit // 2)
            if cache_results:
                self._metrics["cache_hits"] += 1

        # 2. Search using FTS5 indexer for comprehensive results
        fts_results = []
        if len(cache_results) < limit:
            remaining_limit = limit - len(cache_results)
            fts_results = self._search_fts(query, entity_types, remaining_limit)
            if fts_results:
                self._metrics["fts_searches"] += 1

        # 3. Merge and deduplicate results
        all_results = self._merge_results(cache_results, fts_results)

        # 4. Rank and sort results
        ranked_results = self._rank_results(all_results, query)

        # 5. Group results by entity type
        grouped_results = self._group_results(ranked_results)

        # 6. Generate suggestions if requested
        suggestions = []
        if include_suggestions:
            suggestions = self._generate_suggestions(query, ranked_results)

        # Calculate search time
        search_time = time.time() - start_time
        self._update_avg_search_time(search_time)

        return {
            "query": query,
            "results": grouped_results,
            "total": len(ranked_results),
            "suggestions": suggestions,
            "stats": {
                "search_time": search_time,
                "cache_used": len(cache_results) > 0,
                "fts_used": len(fts_results) > 0,
                "sources": self._get_sources_used(cache_results, fts_results),
            },
        }

    def autocomplete(
        self, prefix: str, field: str = "name", limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get autocomplete suggestions for a prefix.

        Args:
            prefix: Prefix to complete
            field: Field to search in
            limit: Maximum suggestions

        Returns:
            List of autocomplete suggestions with metadata
        """
        if not prefix:
            return []

        suggestions = []

        # Use contact cache for contact autocomplete
        if self.contact_cache and field in ["name", "email", "phone"]:
            cache_suggestions = self.contact_cache.autocomplete(prefix, field)
            for text, contact_id in cache_suggestions[:limit]:
                suggestions.append(
                    {
                        "text": text,
                        "entity_type": EntityType.CONTACT.value,
                        "entity_id": contact_id,
                        "field": field,
                    }
                )

        # Add popular searches that match prefix
        if field == "query":
            for search_query, count in sorted(
                self._popular_searches.items(), key=lambda x: x[1], reverse=True
            ):
                if search_query.lower().startswith(prefix.lower()):
                    suggestions.append(
                        {
                            "text": search_query,
                            "entity_type": "search_history",
                            "popularity": count,
                            "field": "query",
                        }
                    )
                    if len(suggestions) >= limit:
                        break

        return suggestions[:limit]

    def get_suggestions(self, query: str, context: Optional[List[int]] = None) -> List[str]:
        """Get search suggestions based on query and context.

        Args:
            query: Current search query
            context: Optional list of recently viewed entity IDs

        Returns:
            List of suggested search queries
        """
        suggestions = []

        # Add related searches from history
        for hist_query, _ in self._search_history:
            if query.lower() in hist_query.lower() and hist_query != query:
                suggestions.append(hist_query)

        # Add variations
        words = query.split()
        if len(words) > 1:
            # Suggest individual words
            for word in words:
                if len(word) > 2:
                    suggestions.append(word)

            # Suggest different word orders
            if len(words) == 2:
                suggestions.append(f"{words[1]} {words[0]}")

        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for s in suggestions:
            if s not in seen:
                seen.add(s)
                unique.append(s)

        return unique[:5]

    def warm_cache(self, contacts: List[Dict[str, Any]]) -> None:
        """Warm the contact cache with initial data.

        Args:
            contacts: List of contact dictionaries
        """
        if self.contact_cache:
            self.contact_cache.warm_cache(contacts)

    def rebuild_index(self) -> bool:
        """Rebuild the FTS5 search index.

        Returns:
            True if successful
        """
        return self.indexer.rebuild_index()

    def optimize_index(self) -> bool:
        """Optimize the FTS5 search index.

        Returns:
            True if successful
        """
        return self.indexer.optimize_index()

    def get_stats(self) -> Dict[str, Any]:
        """Get search statistics and metrics.

        Returns:
            Dictionary of search statistics
        """
        stats = {
            "metrics": self._metrics,
            "indexer": self.indexer.get_index_stats(),
            "popular_searches": dict(
                sorted(self._popular_searches.items(), key=lambda x: x[1], reverse=True)[:10]
            ),
            "recent_searches": [q for q, _ in self._search_history[-10:]],
        }

        if self.contact_cache:
            stats["cache"] = self.contact_cache.get_stats()

        return stats

    def clear_cache(self) -> None:
        """Clear all caches."""
        if self.contact_cache:
            self.contact_cache.clear_cache()

    def _search_cache(self, query: str, limit: int) -> List[UnifiedSearchResult]:
        """Search the contact cache.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of unified search results from cache
        """
        results = []
        if not self.contact_cache:
            return results

        try:
            cached_contacts = self.contact_cache.search(query, limit)
        except Exception as e:
            # Log error and return empty results rather than failing the entire search
            # In production, you'd want to log this error
            self.logger.warning(f"Cache search failed: {e}", exc_info=True)
            return results

        for contact in cached_contacts:
            # Determine priority based on match type
            priority = self._determine_priority(query, contact.name)

            result = UnifiedSearchResult(
                entity_type=EntityType.CONTACT,
                entity_id=contact.id,
                title=contact.name,
                subtitle=contact.email,
                relevance_score=0.9,  # Cache results are usually highly relevant
                priority=priority,
                matched_fields=["cache"],
                metadata={"phone": contact.phone, "tags": contact.tags, "source": "cache"},
            )
            results.append(result)

        return results

    def _search_fts(
        self, query: str, entity_types: Optional[List[EntityType]], limit: int
    ) -> List[UnifiedSearchResult]:
        """Search using FTS5 indexer.

        Args:
            query: Search query
            entity_types: Entity types to search
            limit: Maximum results

        Returns:
            List of unified search results from FTS
        """
        try:
            fts_results = self.indexer.search(query, entity_types, limit)
        except Exception as e:
            # Log error and return empty results rather than failing the entire search
            # In production, you'd want to log this error
            self.logger.warning(f"FTS search failed: {e}", exc_info=True)
            return []

        results = []
        for fts_result in fts_results:
            # Determine priority based on relevance score
            if fts_result.relevance_score > 0.8:
                priority = SearchPriority.EXACT_MATCH
            elif fts_result.relevance_score > 0.6:
                priority = SearchPriority.PREFIX_MATCH
            elif fts_result.relevance_score > 0.4:
                priority = SearchPriority.CONTAINS_MATCH
            else:
                priority = SearchPriority.PARTIAL_MATCH

            result = UnifiedSearchResult.from_search_result(fts_result, priority)
            result.metadata["source"] = "fts"
            results.append(result)

        return results

    def _merge_results(
        self, cache_results: List[UnifiedSearchResult], fts_results: List[UnifiedSearchResult]
    ) -> List[UnifiedSearchResult]:
        """Merge and deduplicate results from different sources.

        Args:
            cache_results: Results from cache
            fts_results: Results from FTS

        Returns:
            Merged and deduplicated results
        """
        # Track seen entities to avoid duplicates
        seen: Set[Tuple[EntityType, int]] = set()
        merged = []

        # Add cache results first (usually more relevant)
        for result in cache_results:
            key = (result.entity_type, result.entity_id)
            if key not in seen:
                seen.add(key)
                merged.append(result)

        # Add FTS results that aren't duplicates
        for result in fts_results:
            key = (result.entity_type, result.entity_id)
            if key not in seen:
                seen.add(key)
                merged.append(result)

        return merged

    def _rank_results(
        self, results: List[UnifiedSearchResult], query: str
    ) -> List[UnifiedSearchResult]:
        """Rank results by relevance and priority.

        Args:
            results: Unranked results
            query: Original query

        Returns:
            Ranked results
        """
        # Calculate composite score for each result
        for result in results:
            # Base score from relevance
            score = result.relevance_score * 0.5

            # Boost for priority
            score += result.priority.value / 200.0

            # Boost for exact title match
            if result.title and query.lower() == result.title.lower():
                score += 0.3

            # Boost for title starts with query
            elif result.title and result.title.lower().startswith(query.lower()):
                score += 0.2

            # Store composite score
            result.metadata["composite_score"] = score

        # Sort by composite score
        results.sort(key=lambda r: r.metadata.get("composite_score", 0), reverse=True)

        return results

    def _group_results(
        self, results: List[UnifiedSearchResult]
    ) -> Dict[str, List[UnifiedSearchResult]]:
        """Group results by entity type.

        Args:
            results: Ranked results

        Returns:
            Results grouped by entity type
        """
        grouped = {
            "contacts": [],
            "notes": [],
            "tags": [],
            "relationships": [],
        }

        for result in results:
            if result.entity_type == EntityType.CONTACT:
                grouped["contacts"].append(result)
            elif result.entity_type == EntityType.NOTE:
                grouped["notes"].append(result)
            elif result.entity_type == EntityType.TAG:
                grouped["tags"].append(result)
            elif result.entity_type == EntityType.RELATIONSHIP:
                grouped["relationships"].append(result)

        # Remove empty groups
        return {k: v for k, v in grouped.items() if v}

    def _generate_suggestions(self, query: str, results: List[UnifiedSearchResult]) -> List[str]:
        """Generate search suggestions based on query and results.

        Args:
            query: Original query
            results: Search results

        Returns:
            List of search suggestions
        """
        suggestions = []

        # If we have results, suggest refinements
        if results:
            # Suggest searching in specific entity types
            entity_types = set(r.entity_type for r in results)
            if len(entity_types) > 1:
                if EntityType.CONTACT in entity_types:
                    suggestions.append(f"contacts:{query}")
                if EntityType.NOTE in entity_types:
                    suggestions.append(f"notes:{query}")
                if EntityType.TAG in entity_types:
                    suggestions.append(f"tags:{query}")

            # Suggest related terms from matched fields
            all_matched_fields = set()
            for r in results[:5]:  # Look at top 5 results
                all_matched_fields.update(r.matched_fields)

            if "email" in all_matched_fields:
                suggestions.append(f"email:{query}")
            if "phone" in all_matched_fields:
                suggestions.append(f"phone:{query}")

        # If no results, suggest corrections or broader searches
        else:
            # Suggest removing words for broader search
            words = query.split()
            if len(words) > 1:
                suggestions.append(words[0])  # First word only
                suggestions.append(" ".join(words[:-1]))  # Remove last word

        # Add popular related searches
        for search, _ in sorted(self._popular_searches.items(), key=lambda x: x[1], reverse=True)[
            :3
        ]:
            if query.lower() in search.lower() and search != query:
                suggestions.append(search)

        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for s in suggestions:
            if s not in seen and s != query:
                seen.add(s)
                unique.append(s)

        return unique[:5]

    def _determine_priority(self, query: str, text: str) -> SearchPriority:
        """Determine search priority based on match type.

        Args:
            query: Search query
            text: Text being matched

        Returns:
            Search priority level
        """
        if not text:
            return SearchPriority.PARTIAL_MATCH

        query_lower = query.lower()
        text_lower = text.lower()

        if query_lower == text_lower:
            return SearchPriority.EXACT_MATCH
        elif text_lower.startswith(query_lower):
            return SearchPriority.PREFIX_MATCH
        elif query_lower in text_lower:
            return SearchPriority.CONTAINS_MATCH
        else:
            return SearchPriority.PARTIAL_MATCH

    def _add_to_history(self, query: str) -> None:
        """Add query to search history with memory management.

        Args:
            query: Search query
        """
        # Add to history
        self._search_history.append((query, time.time()))

        # Keep only last MAX_HISTORY_SIZE searches
        if len(self._search_history) > self.MAX_HISTORY_SIZE:
            self._search_history.pop(0)

        # Update popular searches
        query_lower = query.lower()
        self._popular_searches[query_lower] = self._popular_searches.get(query_lower, 0) + 1

        # Manage popular searches memory
        if len(self._popular_searches) > self.MAX_POPULAR_SEARCHES:
            # Keep only the top searches
            sorted_items = sorted(self._popular_searches.items(), key=lambda x: x[1], reverse=True)
            # Keep top 75% of MAX_POPULAR_SEARCHES
            keep_count = int(self.MAX_POPULAR_SEARCHES * 0.75)
            self._popular_searches = dict(sorted_items[:keep_count])

    def _update_avg_search_time(self, search_time: float) -> None:
        """Update average search time metric.

        Args:
            search_time: Time taken for this search
        """
        current_avg = self._metrics["avg_search_time"]
        total_searches = self._metrics["total_searches"]

        # Calculate new average
        new_avg = ((current_avg * (total_searches - 1)) + search_time) / total_searches
        self._metrics["avg_search_time"] = new_avg

    def _get_sources_used(
        self, cache_results: List[UnifiedSearchResult], fts_results: List[UnifiedSearchResult]
    ) -> List[str]:
        """Get list of sources used in search.

        Args:
            cache_results: Results from cache
            fts_results: Results from FTS

        Returns:
            List of source names
        """
        sources = []
        if cache_results:
            sources.append("cache")
        if fts_results:
            sources.append("fts")
        return sources

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty search result structure.

        Returns:
            Empty result dictionary
        """
        return {
            "query": "",
            "results": {},
            "total": 0,
            "suggestions": [],
            "stats": {
                "search_time": 0.0,
                "cache_used": False,
                "fts_used": False,
                "sources": [],
            },
        }
