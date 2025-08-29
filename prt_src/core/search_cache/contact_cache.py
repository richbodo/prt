"""Contact search cache with autocomplete support.

This module provides an LRU cache for contact searches and a prefix trie
for fast autocomplete suggestions, optimized for 5000+ contacts.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

import pygtrie
from lru import LRU

from prt_src.logging_config import get_logger


@dataclass
class CachedContact:
    """Represents a cached contact for fast retrieval."""

    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    last_accessed: float = field(default_factory=time.time)
    search_keywords: Set[str] = field(default_factory=set)

    def __post_init__(self):
        """Generate search keywords from contact data."""
        if not self.search_keywords:
            self.search_keywords = self._generate_keywords()

    def _generate_keywords(self) -> Set[str]:
        """Generate searchable keywords from contact fields."""
        keywords = set()

        # Add name parts
        if self.name:
            # Full name and individual words
            keywords.add(self.name.lower())
            for part in self.name.split():
                if part:
                    keywords.add(part.lower())

        # Add email parts
        if self.email:
            keywords.add(self.email.lower())
            # Add username part before @
            username = self.email.split("@")[0]
            keywords.add(username.lower())

        # Add phone (normalized)
        if self.phone:
            # Remove common separators for phone search
            normalized = "".join(c for c in self.phone if c.isdigit())
            if normalized:
                keywords.add(normalized)

        # Add tags
        for tag in self.tags:
            keywords.add(tag.lower())

        return keywords

    def matches(self, query: str) -> bool:
        """Check if contact matches search query."""
        query_lower = query.lower()
        return any(query_lower in keyword for keyword in self.search_keywords)


class ContactSearchCache:
    """High-performance cache for contact searches with autocomplete.

    This cache provides:
    - LRU caching of frequently accessed contacts
    - Prefix trie for fast autocomplete suggestions
    - Efficient search across large contact lists
    - Cache warming for improved initial performance
    """

    def __init__(self, max_cache_size: int = 1000, max_autocomplete_results: int = 10):
        """Initialize the contact search cache.

        Args:
            max_cache_size: Maximum number of contacts to keep in LRU cache
            max_autocomplete_results: Maximum autocomplete suggestions to return
        """
        self.max_cache_size = max_cache_size
        self.max_autocomplete_results = max_autocomplete_results
        self.logger = get_logger(__name__)

        # LRU cache for frequently accessed contacts
        self._lru_cache = LRU(max_cache_size)

        # Prefix trie for autocomplete
        self._name_trie = pygtrie.CharTrie()
        self._email_trie = pygtrie.CharTrie()
        self._phone_trie = pygtrie.CharTrie()

        # All contacts for full search
        self._all_contacts: Dict[int, CachedContact] = {}

        # Cache statistics
        self._stats = {
            "hits": 0,
            "misses": 0,
            "autocomplete_queries": 0,
            "cache_evictions": 0,
            "last_warm": None,
        }

    def add_contact(self, contact: CachedContact) -> None:
        """Add a contact to the cache.

        Args:
            contact: Contact to add to cache
        """
        # Add to all contacts
        self._all_contacts[contact.id] = contact

        # Add to LRU cache
        self._lru_cache[contact.id] = contact

        # Add to tries for autocomplete
        if contact.name:
            # Add full name and each word
            name_lower = contact.name.lower()
            self._name_trie[name_lower] = contact.id

            # Also add by last name first (common search pattern)
            parts = contact.name.split()
            if len(parts) >= 2:
                # Last, First format
                last_first = f"{parts[-1]}, {' '.join(parts[:-1])}".lower()
                self._name_trie[last_first] = contact.id

            # Add individual name parts
            for part in parts:
                if part:
                    part_lower = part.lower()
                    if part_lower not in self._name_trie:
                        self._name_trie[part_lower] = []
                    if isinstance(self._name_trie[part_lower], list):
                        self._name_trie[part_lower].append(contact.id)

        if contact.email:
            email_lower = contact.email.lower()
            self._email_trie[email_lower] = contact.id

            # Also add username part
            username = email_lower.split("@")[0]
            if username not in self._email_trie:
                self._email_trie[username] = []
            if isinstance(self._email_trie[username], list):
                self._email_trie[username].append(contact.id)

        if contact.phone:
            # Normalized phone for search
            normalized = "".join(c for c in contact.phone if c.isdigit())
            if normalized:
                self._phone_trie[normalized] = contact.id

    def get_contact(self, contact_id: int) -> Optional[CachedContact]:
        """Get a contact by ID from cache.

        Args:
            contact_id: ID of contact to retrieve

        Returns:
            Cached contact or None if not found
        """
        # Check LRU cache first
        if contact_id in self._lru_cache:
            self._stats["hits"] += 1
            contact = self._lru_cache[contact_id]
            contact.last_accessed = time.time()
            return contact

        # Check all contacts
        if contact_id in self._all_contacts:
            self._stats["misses"] += 1
            contact = self._all_contacts[contact_id]
            contact.last_accessed = time.time()

            # Add to LRU cache
            if len(self._lru_cache) >= self.max_cache_size:
                self._stats["cache_evictions"] += 1
            self._lru_cache[contact_id] = contact

            return contact

        return None

    def search(self, query: str, limit: int = 50) -> List[CachedContact]:
        """Search for contacts matching query.

        Args:
            query: Search query
            limit: Maximum results to return

        Returns:
            List of matching contacts
        """
        if not query:
            return []

        query_lower = query.lower()
        results = []
        seen_ids = set()

        # First, check exact matches in tries
        # Check name trie
        if query_lower in self._name_trie:
            contact_ids = self._name_trie[query_lower]
            if not isinstance(contact_ids, list):
                contact_ids = [contact_ids]

            for cid in contact_ids:
                if cid not in seen_ids and cid in self._all_contacts:
                    results.append(self._all_contacts[cid])
                    seen_ids.add(cid)

        # Check email trie
        if query_lower in self._email_trie:
            contact_ids = self._email_trie[query_lower]
            if not isinstance(contact_ids, list):
                contact_ids = [contact_ids]

            for cid in contact_ids:
                if cid not in seen_ids and cid in self._all_contacts:
                    results.append(self._all_contacts[cid])
                    seen_ids.add(cid)

        # If we don't have enough results, do a broader search
        if len(results) < limit:
            for contact in self._all_contacts.values():
                if contact.id not in seen_ids and contact.matches(query):
                    results.append(contact)
                    seen_ids.add(contact.id)

                    if len(results) >= limit:
                        break

        # Update access times and cache
        for contact in results[:10]:  # Cache top 10 results
            contact.last_accessed = time.time()
            if len(self._lru_cache) >= self.max_cache_size:
                self._stats["cache_evictions"] += 1
            self._lru_cache[contact.id] = contact

        return results[:limit]

    def autocomplete(self, prefix: str, search_field: str = "name") -> List[Tuple[str, int]]:
        """Get autocomplete suggestions for a prefix.

        Args:
            prefix: Prefix to search for
            search_field: Field to search in ("name", "email", "phone")

        Returns:
            List of (suggestion, contact_id) tuples
        """
        if not prefix:
            return []

        self._stats["autocomplete_queries"] += 1
        prefix_lower = prefix.lower()
        suggestions = []

        # Select the appropriate trie
        if search_field == "name":
            trie = self._name_trie
        elif search_field == "email":
            trie = self._email_trie
        elif search_field == "phone":
            # Normalize phone prefix
            prefix_lower = "".join(c for c in prefix if c.isdigit())
            trie = self._phone_trie
        else:
            return []

        # Get all entries with this prefix
        try:
            items = list(trie.iteritems(prefix=prefix_lower))

            for key, value in items[: self.max_autocomplete_results]:
                if isinstance(value, list):
                    # Multiple contacts for this key
                    for contact_id in value:
                        if contact_id in self._all_contacts:
                            contact = self._all_contacts[contact_id]
                            if search_field == "name":
                                suggestions.append((contact.name, contact_id))
                            elif search_field == "email":
                                suggestions.append((contact.email, contact_id))
                            elif search_field == "phone":
                                suggestions.append((contact.phone, contact_id))
                else:
                    # Single contact for this key
                    if value in self._all_contacts:
                        contact = self._all_contacts[value]
                        if search_field == "name":
                            suggestions.append((contact.name, value))
                        elif search_field == "email":
                            suggestions.append((contact.email, value))
                        elif search_field == "phone":
                            suggestions.append((contact.phone, value))

        except KeyError:
            # No matches for this prefix
            pass

        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion[0] not in seen:
                seen.add(suggestion[0])
                unique_suggestions.append(suggestion)

        return unique_suggestions[: self.max_autocomplete_results]

    def warm_cache(self, contacts: List[Dict[str, Any]]) -> None:
        """Warm the cache with initial contact data.

        Args:
            contacts: List of contact dictionaries to load
        """
        start_time = time.time()

        for contact_data in contacts:
            contact = CachedContact(
                id=contact_data["id"],
                name=contact_data.get("name", ""),
                email=contact_data.get("email"),
                phone=contact_data.get("phone"),
                tags=contact_data.get("tags", []),
            )
            self.add_contact(contact)

        self._stats["last_warm"] = time.time()
        warm_time = time.time() - start_time

        self.logger.info(f"Cache warmed with {len(contacts)} contacts in {warm_time:.2f}s")

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._lru_cache.clear()
        self._name_trie.clear()
        self._email_trie.clear()
        self._phone_trie.clear()
        self._all_contacts.clear()

        # Reset stats except for historical counts
        hits = self._stats["hits"]
        misses = self._stats["misses"]
        queries = self._stats["autocomplete_queries"]

        self._stats = {
            "hits": hits,
            "misses": misses,
            "autocomplete_queries": queries,
            "cache_evictions": 0,
            "last_warm": None,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary of cache statistics
        """
        total_queries = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_queries if total_queries > 0 else 0

        return {
            "cache_size": len(self._lru_cache),
            "total_contacts": len(self._all_contacts),
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": hit_rate,
            "autocomplete_queries": self._stats["autocomplete_queries"],
            "cache_evictions": self._stats["cache_evictions"],
            "last_warm": self._stats["last_warm"],
            "name_trie_size": len(self._name_trie),
            "email_trie_size": len(self._email_trie),
            "phone_trie_size": len(self._phone_trie),
        }

    def get_most_accessed(self, limit: int = 10) -> List[CachedContact]:
        """Get the most recently accessed contacts.

        Args:
            limit: Maximum number of contacts to return

        Returns:
            List of most recently accessed contacts
        """
        # Get contacts from LRU cache (already ordered by access)
        contacts = []
        for contact_id in list(self._lru_cache.keys())[:limit]:
            if contact_id in self._all_contacts:
                contacts.append(self._all_contacts[contact_id])

        return contacts

    def update_contact(self, contact_id: int, **updates) -> bool:
        """Update a cached contact's information.

        Args:
            contact_id: ID of contact to update
            **updates: Fields to update

        Returns:
            True if contact was updated, False if not found
        """
        if contact_id not in self._all_contacts:
            return False

        contact = self._all_contacts[contact_id]

        # Update fields
        for field_name, value in updates.items():
            if hasattr(contact, field_name):
                setattr(contact, field_name, value)

        # Regenerate keywords
        contact.search_keywords = contact._generate_keywords()

        # Re-add to tries with updated info
        # (This is simplified - in production you'd want to remove old entries first)
        if "name" in updates and contact.name:
            self._name_trie[contact.name.lower()] = contact_id

        if "email" in updates and contact.email:
            self._email_trie[contact.email.lower()] = contact_id

        if "phone" in updates and contact.phone:
            normalized = "".join(c for c in contact.phone if c.isdigit())
            if normalized:
                self._phone_trie[normalized] = contact_id

        return True

    def remove_contact(self, contact_id: int) -> bool:
        """Remove a contact from the cache.

        Args:
            contact_id: ID of contact to remove

        Returns:
            True if contact was removed, False if not found
        """
        if contact_id not in self._all_contacts:
            return False

        # Remove from all structures
        if contact_id in self._lru_cache:
            del self._lru_cache[contact_id]

        del self._all_contacts[contact_id]

        # Note: Removing from tries is complex as we'd need to track
        # all keys pointing to this contact. In production, you might
        # want to rebuild tries periodically.

        return True
