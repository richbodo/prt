"""Test contact search cache functionality."""

import time

import pytest

from prt_src.core.search_cache.contact_cache import CachedContact, ContactSearchCache


@pytest.fixture
def sample_contacts():
    """Create sample contacts for testing."""
    return [
        CachedContact(
            id=1,
            name="Alice Johnson",
            email="alice@example.com",
            phone="555-0001",
            tags=["family", "friend"],
        ),
        CachedContact(
            id=2,
            name="Bob Smith",
            email="bob.smith@example.com",
            phone="555-0002",
            tags=["work"],
        ),
        CachedContact(
            id=3,
            name="Charlie Brown",
            email="charlie@example.com",
            phone="555-0003",
            tags=["friend"],
        ),
        CachedContact(
            id=4,
            name="Diana Prince",
            email="diana.prince@example.com",
            phone="555-0004",
            tags=["work", "important"],
        ),
        CachedContact(
            id=5,
            name="Alice Cooper",
            email="acooper@example.com",
            phone="555-0005",
            tags=["music"],
        ),
    ]


@pytest.fixture
def cache():
    """Create a ContactSearchCache instance."""
    return ContactSearchCache(max_cache_size=3, max_autocomplete_results=5)


class TestCachedContact:
    """Test CachedContact class."""

    def test_keyword_generation(self):
        """Test that search keywords are generated correctly."""
        contact = CachedContact(
            id=1, name="John Doe", email="john.doe@example.com", phone="555-1234"
        )

        # Check keywords include name parts
        assert "john" in contact.search_keywords
        assert "doe" in contact.search_keywords
        assert "john doe" in contact.search_keywords

        # Check email keywords
        assert "john.doe@example.com" in contact.search_keywords
        assert "john.doe" in contact.search_keywords

        # Check phone keyword (normalized)
        assert "5551234" in contact.search_keywords

    def test_matches_query(self):
        """Test contact matching against queries."""
        contact = CachedContact(
            id=1, name="Alice Johnson", email="alice@example.com", tags=["family"]
        )

        # Should match name parts
        assert contact.matches("alice")
        assert contact.matches("ALICE")  # Case insensitive
        assert contact.matches("john")
        assert contact.matches("alice johnson")

        # Should match email
        assert contact.matches("alice@")
        assert contact.matches("example.com")

        # Should match tags
        assert contact.matches("family")

        # Should not match unrelated
        assert not contact.matches("bob")
        assert not contact.matches("xyz")

    def test_tag_keywords(self):
        """Test that tags are included in keywords."""
        contact = CachedContact(id=1, name="Test", tags=["family", "friend", "VIP"])

        assert "family" in contact.search_keywords
        assert "friend" in contact.search_keywords
        assert "vip" in contact.search_keywords  # Lowercase


class TestContactSearchCache:
    """Test ContactSearchCache class."""

    def test_add_and_get_contact(self, cache, sample_contacts):
        """Test adding and retrieving contacts."""
        contact = sample_contacts[0]
        cache.add_contact(contact)

        # Should be retrievable
        retrieved = cache.get_contact(1)
        assert retrieved is not None
        assert retrieved.name == "Alice Johnson"
        assert retrieved.id == 1

        # Should track as a hit
        stats = cache.get_stats()
        assert stats["hits"] == 1

    def test_lru_eviction(self, cache, sample_contacts):
        """Test LRU cache eviction when size limit reached."""
        # Add 4 contacts (cache size is 3)
        for contact in sample_contacts[:4]:
            cache.add_contact(contact)

        # First contact should be evicted from LRU (but still in all_contacts)
        assert 1 not in cache._lru_cache
        assert 1 in cache._all_contacts

        # Getting it should cause a miss
        contact = cache.get_contact(1)
        assert contact is not None

        stats = cache.get_stats()
        assert stats["misses"] == 1
        assert stats["cache_evictions"] > 0

    def test_search_contacts(self, cache, sample_contacts):
        """Test searching for contacts."""
        # Add all sample contacts
        for contact in sample_contacts:
            cache.add_contact(contact)

        # Search for "alice" should return both Alices
        results = cache.search("alice")
        assert len(results) == 2
        names = {r.name for r in results}
        assert "Alice Johnson" in names
        assert "Alice Cooper" in names

        # Search for "work" tag
        results = cache.search("work")
        assert len(results) == 2
        names = {r.name for r in results}
        assert "Bob Smith" in names
        assert "Diana Prince" in names

        # Search by phone
        results = cache.search("0003")
        assert len(results) == 1
        assert results[0].name == "Charlie Brown"

    def test_autocomplete_name(self, cache, sample_contacts):
        """Test name autocomplete functionality."""
        # Add contacts
        for contact in sample_contacts:
            cache.add_contact(contact)

        # Autocomplete for "ali"
        suggestions = cache.autocomplete("ali", search_field="name")
        assert len(suggestions) >= 2
        names = {s[0] for s in suggestions}
        assert "Alice Johnson" in names or "Alice Cooper" in names

        # Autocomplete for "bob"
        suggestions = cache.autocomplete("bob", search_field="name")
        assert len(suggestions) >= 1
        assert any("Bob" in s[0] for s in suggestions)

    def test_autocomplete_email(self, cache, sample_contacts):
        """Test email autocomplete functionality."""
        for contact in sample_contacts:
            cache.add_contact(contact)

        # Autocomplete for email prefix
        suggestions = cache.autocomplete("alice", search_field="email")
        assert len(suggestions) >= 1
        emails = {s[0] for s in suggestions}
        assert "alice@example.com" in emails

        # Autocomplete for username part
        suggestions = cache.autocomplete("diana", search_field="email")
        assert len(suggestions) >= 1
        assert any("diana" in s[0].lower() for s in suggestions)

    def test_autocomplete_phone(self, cache, sample_contacts):
        """Test phone autocomplete functionality."""
        for contact in sample_contacts:
            cache.add_contact(contact)

        # Autocomplete for phone prefix
        suggestions = cache.autocomplete("555000", search_field="phone")
        assert len(suggestions) >= 1
        # Should match contacts with phones starting with 555-000

    def test_warm_cache(self, cache):
        """Test cache warming with bulk data."""
        contacts_data = [
            {"id": i, "name": f"Contact {i}", "email": f"contact{i}@example.com", "tags": []}
            for i in range(100)
        ]

        cache.warm_cache(contacts_data)

        # All contacts should be loaded
        assert len(cache._all_contacts) == 100

        # Stats should show warming
        stats = cache.get_stats()
        assert stats["last_warm"] is not None
        assert stats["total_contacts"] == 100

    def test_clear_cache(self, cache, sample_contacts):
        """Test clearing the cache."""
        # Add contacts
        for contact in sample_contacts:
            cache.add_contact(contact)

        # Do some operations to generate stats
        cache.get_contact(1)  # This will be a hit since it's in LRU
        cache.get_contact(2)  # This will also be a hit
        cache.search("alice")

        # Record stats before clearing
        stats_before = cache.get_stats()
        hits_before = stats_before["hits"]

        # Clear cache
        cache.clear_cache()

        # Everything should be empty
        assert len(cache._all_contacts) == 0
        assert len(cache._lru_cache) == 0
        assert len(cache._name_trie) == 0

        # But stats should be preserved
        stats = cache.get_stats()
        assert stats["hits"] == hits_before

    def test_get_most_accessed(self, cache, sample_contacts):
        """Test getting most accessed contacts."""
        # Add contacts
        for contact in sample_contacts:
            cache.add_contact(contact)

        # Access some contacts
        cache.get_contact(2)  # Bob
        time.sleep(0.01)
        cache.get_contact(1)  # Alice J
        time.sleep(0.01)
        cache.get_contact(3)  # Charlie

        # Most accessed should reflect LRU order
        most_accessed = cache.get_most_accessed(2)
        assert len(most_accessed) == 2
        # Most recent accesses should be first

    def test_update_contact(self, cache, sample_contacts):
        """Test updating a cached contact."""
        contact = sample_contacts[0]
        cache.add_contact(contact)

        # Update the contact
        success = cache.update_contact(1, email="newemail@example.com", phone="555-9999")
        assert success is True

        # Changes should be reflected
        updated = cache.get_contact(1)
        assert updated.email == "newemail@example.com"
        assert updated.phone == "555-9999"

        # Keywords should be regenerated
        assert "newemail@example.com" in updated.search_keywords
        assert "5559999" in updated.search_keywords

    def test_remove_contact(self, cache, sample_contacts):
        """Test removing a contact from cache."""
        contact = sample_contacts[0]
        cache.add_contact(contact)

        # Remove the contact
        success = cache.remove_contact(1)
        assert success is True

        # Should not be retrievable
        assert cache.get_contact(1) is None
        assert 1 not in cache._all_contacts
        assert 1 not in cache._lru_cache

        # Removing again should fail
        success = cache.remove_contact(1)
        assert success is False

    def test_cache_statistics(self, cache, sample_contacts):
        """Test cache statistics tracking."""
        # Add contacts
        for contact in sample_contacts[:3]:
            cache.add_contact(contact)

        # Generate some activity
        cache.get_contact(1)  # Hit
        cache.get_contact(2)  # Hit
        cache.get_contact(99)  # Miss (not found)
        cache.autocomplete("ali", "name")
        cache.search("test")

        stats = cache.get_stats()

        assert stats["cache_size"] <= 3
        assert stats["total_contacts"] == 3
        assert stats["hits"] == 2
        assert stats["misses"] == 0  # 99 doesn't exist, so no miss recorded
        assert stats["autocomplete_queries"] == 1
        assert stats["hit_rate"] == 1.0  # 2 hits, 0 misses

    def test_search_limit(self, cache):
        """Test that search respects limit parameter."""
        # Add many contacts
        for i in range(100):
            contact = CachedContact(id=i, name=f"Contact {i}", email=f"c{i}@example.com")
            cache.add_contact(contact)

        # Search with limit
        results = cache.search("contact", limit=10)
        assert len(results) == 10

    def test_empty_search(self, cache, sample_contacts):
        """Test that empty search returns empty results."""
        for contact in sample_contacts:
            cache.add_contact(contact)

        assert cache.search("") == []
        assert cache.search(None) == []

    def test_autocomplete_max_results(self, cache):
        """Test that autocomplete respects max results."""
        # Add many similar contacts
        for i in range(20):
            contact = CachedContact(id=i, name=f"Alice {i}", email=f"alice{i}@example.com")
            cache.add_contact(contact)

        # Autocomplete should respect limit (5)
        suggestions = cache.autocomplete("alice", "name")
        assert len(suggestions) <= 5

    def test_case_insensitive_search(self, cache, sample_contacts):
        """Test that searches are case insensitive."""
        for contact in sample_contacts:
            cache.add_contact(contact)

        # Different cases should work
        assert len(cache.search("ALICE")) > 0
        assert len(cache.search("Alice")) > 0
        assert len(cache.search("alice")) > 0
        assert len(cache.search("aLiCe")) > 0

    def test_partial_matches(self, cache, sample_contacts):
        """Test partial string matching in search."""
        for contact in sample_contacts:
            cache.add_contact(contact)

        # Partial matches should work
        results = cache.search("john")  # Part of "Johnson"
        assert len(results) == 1
        assert results[0].name == "Alice Johnson"

        results = cache.search("@example")  # Part of email
        assert len(results) == 5  # All have @example.com

    def test_access_time_updates(self, cache, sample_contacts):
        """Test that access times are updated."""
        contact = sample_contacts[0]
        cache.add_contact(contact)

        initial_time = contact.last_accessed

        # Wait a bit and access
        time.sleep(0.01)
        retrieved = cache.get_contact(1)

        assert retrieved.last_accessed > initial_time
