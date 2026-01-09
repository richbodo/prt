"""Search indexer for FTS5 full-text search.

This module provides a high-level interface to the FTS5 search capabilities,
including incremental updates, result ranking, and search optimization.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from prt_src.logging_config import get_logger


class EntityType(Enum):
    """Types of entities that can be searched."""

    CONTACT = "contact"
    NOTE = "note"
    TAG = "tag"
    RELATIONSHIP = "relationship"


@dataclass
class SearchResult:
    """Represents a single search result."""

    entity_type: EntityType
    entity_id: int
    title: str
    subtitle: str | None = None
    snippet: str | None = None
    relevance_score: float = 0.0
    matched_fields: list[str] = None
    metadata: dict[str, Any] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.matched_fields is None:
            self.matched_fields = []
        if self.metadata is None:
            self.metadata = {}


class SearchIndexer:
    """Manages FTS5 search indexing and querying."""

    def __init__(self, db):
        """Initialize the search indexer.

        Args:
            db: Database connection object with SQLAlchemy session
        """
        self.db = db
        self._fts_available = None
        self.logger = get_logger(__name__)
        self._last_index_update = None

    def check_fts_available(self) -> bool:
        """Check if FTS5 tables are available.

        Returns:
            True if FTS5 tables exist, False otherwise
        """
        if self._fts_available is not None:
            return self._fts_available

        try:
            # Try to query FTS tables to check if they exist
            self.db.session.execute(text("SELECT 1 FROM contacts_fts LIMIT 1"))
            self.db.session.execute(text("SELECT 1 FROM notes_fts LIMIT 1"))
            self.db.session.execute(text("SELECT 1 FROM tags_fts LIMIT 1"))
            self._fts_available = True
        except OperationalError:
            self._fts_available = False

        return self._fts_available

    def search(
        self,
        query: str,
        entity_types: list[EntityType] | None = None,
        limit: int = 50,
        offset: int = 0,
        rank_by_relevance: bool = True,
    ) -> list[SearchResult]:
        """Perform a full-text search across specified entity types.

        Args:
            query: Search query string (supports FTS5 syntax)
            entity_types: List of entity types to search (None = all)
            limit: Maximum number of results to return
            offset: Number of results to skip
            rank_by_relevance: Whether to sort by relevance score

        Returns:
            List of SearchResult objects
        """
        if not self.check_fts_available():
            return self._fallback_search(query, entity_types, limit, offset)

        if not query or not query.strip():
            return []

        # Prepare query for FTS5
        fts_query = self._prepare_fts_query(query)

        # Determine which entity types to search
        if entity_types is None:
            entity_types = [EntityType.CONTACT, EntityType.NOTE, EntityType.TAG]

        results = []

        # Search each entity type
        if EntityType.CONTACT in entity_types:
            results.extend(self._search_contacts(fts_query, limit))

        if EntityType.NOTE in entity_types:
            results.extend(self._search_notes(fts_query, limit))

        if EntityType.TAG in entity_types:
            results.extend(self._search_tags(fts_query, limit))

        # Rank results if requested
        if rank_by_relevance:
            results.sort(key=lambda r: r.relevance_score, reverse=True)

        # Apply pagination
        return results[offset : offset + limit]

    def _prepare_fts_query(self, query: str) -> str:
        """Prepare a query string for FTS5.

        Args:
            query: Raw search query

        Returns:
            FTS5-formatted query string
        """
        # Remove special characters that might break FTS5
        query = re.sub(r'["\'\(\)\[\]{}]', " ", query)

        # Handle multiple words - by default FTS5 treats spaces as AND
        # We'll make it more flexible by using OR for multiple terms
        terms = query.split()

        if len(terms) == 1:
            # Single term - use prefix matching
            return f"{terms[0]}*"
        else:
            # Multiple terms - search for any of them
            return " OR ".join(f"{term}*" for term in terms)

    def _search_contacts(self, fts_query: str, limit: int) -> list[SearchResult]:
        """Search contacts using FTS5.

        Args:
            fts_query: FTS5-formatted query
            limit: Maximum results

        Returns:
            List of contact search results
        """
        results = []

        try:
            # Search contacts with ranking
            sql = """
                SELECT
                    c.id,
                    c.name,
                    c.email,
                    c.phone,
                    bm25(contacts_fts) as rank,
                    snippet(contacts_fts, 1, '<b>', '</b>', '...', 32) as name_snippet,
                    snippet(contacts_fts, 2, '<b>', '</b>', '...', 32) as email_snippet
                FROM contacts_fts
                JOIN contacts c ON contacts_fts.contact_id = c.id
                WHERE contacts_fts MATCH :query
                ORDER BY rank
                LIMIT :limit
            """

            rows = self.db.session.execute(
                text(sql), {"query": fts_query, "limit": limit}
            ).fetchall()

            for row in rows:
                # Determine which fields matched
                matched_fields = []
                if "<b>" in (row[5] or ""):
                    matched_fields.append("name")
                if "<b>" in (row[6] or ""):
                    matched_fields.append("email")

                # Create search result
                result = SearchResult(
                    entity_type=EntityType.CONTACT,
                    entity_id=row[0],
                    title=row[1] or "Unnamed Contact",
                    subtitle=row[2],  # email
                    snippet=row[5] or row[6],  # Use name snippet if available, else email
                    relevance_score=abs(row[4]),  # bm25 returns negative scores
                    matched_fields=matched_fields,
                    metadata={"phone": row[3]},
                )
                results.append(result)

        except Exception as e:
            # Log error but don't crash
            self.logger.error(f"Error searching contacts: {e}", exc_info=True)

        return results

    def _search_notes(self, fts_query: str, limit: int) -> list[SearchResult]:
        """Search notes using FTS5.

        Args:
            fts_query: FTS5-formatted query
            limit: Maximum results

        Returns:
            List of note search results
        """
        results = []

        try:
            # Search notes with ranking
            sql = """
                SELECT
                    n.id,
                    n.title,
                    n.content,
                    bm25(notes_fts) as rank,
                    snippet(notes_fts, 1, '<b>', '</b>', '...', 32) as title_snippet,
                    snippet(notes_fts, 2, '<b>', '</b>', '...', 64) as content_snippet
                FROM notes_fts
                JOIN notes n ON notes_fts.note_id = n.id
                WHERE notes_fts MATCH :query
                ORDER BY rank
                LIMIT :limit
            """

            rows = self.db.session.execute(
                text(sql), {"query": fts_query, "limit": limit}
            ).fetchall()

            for row in rows:
                # Determine which fields matched
                matched_fields = []
                if "<b>" in (row[4] or ""):
                    matched_fields.append("title")
                if "<b>" in (row[5] or ""):
                    matched_fields.append("content")

                # Create search result
                result = SearchResult(
                    entity_type=EntityType.NOTE,
                    entity_id=row[0],
                    title=row[1] or "Untitled Note",
                    subtitle=None,
                    snippet=row[5] or row[4],  # Prefer content snippet
                    relevance_score=abs(row[3]),
                    matched_fields=matched_fields,
                    metadata={"content_preview": (row[2] or "")[:100]},
                )
                results.append(result)

        except Exception as e:
            self.logger.error(f"Error searching notes: {e}", exc_info=True)

        return results

    def _search_tags(self, fts_query: str, limit: int) -> list[SearchResult]:
        """Search tags using FTS5.

        Args:
            fts_query: FTS5-formatted query
            limit: Maximum results

        Returns:
            List of tag search results
        """
        results = []

        try:
            # Search tags with ranking
            sql = """
                SELECT
                    t.id,
                    t.name,
                    t.description,
                    bm25(tags_fts) as rank,
                    snippet(tags_fts, 1, '<b>', '</b>', '...', 32) as name_snippet,
                    (SELECT COUNT(*) FROM contact_tags WHERE tag_id = t.id) as contact_count
                FROM tags_fts
                JOIN tags t ON tags_fts.tag_id = t.id
                WHERE tags_fts MATCH :query
                ORDER BY rank
                LIMIT :limit
            """

            rows = self.db.session.execute(
                text(sql), {"query": fts_query, "limit": limit}
            ).fetchall()

            for row in rows:
                # Create search result
                result = SearchResult(
                    entity_type=EntityType.TAG,
                    entity_id=row[0],
                    title=row[1] or "Unnamed Tag",
                    subtitle=f"{row[5]} contacts",
                    snippet=row[4],
                    relevance_score=abs(row[3]),
                    matched_fields=["name"] if "<b>" in (row[4] or "") else [],
                    metadata={"description": row[2], "contact_count": row[5]},
                )
                results.append(result)

        except Exception as e:
            self.logger.error(f"Error searching tags: {e}", exc_info=True)

        return results

    def _fallback_search(
        self,
        query: str,
        entity_types: list[EntityType] | None,
        limit: int,
        offset: int,
    ) -> list[SearchResult]:
        """Fallback search when FTS5 is not available.

        Uses LIKE queries as a fallback for basic search functionality.

        Args:
            query: Search query
            entity_types: Entity types to search
            limit: Maximum results
            offset: Result offset

        Returns:
            List of search results
        """
        if not query or not query.strip():
            return []

        query_pattern = f"%{query}%"
        results = []

        if entity_types is None:
            entity_types = [EntityType.CONTACT, EntityType.NOTE, EntityType.TAG]

        # Fallback contact search
        if EntityType.CONTACT in entity_types:
            try:
                sql = """
                    SELECT id, name, email, phone
                    FROM contacts
                    WHERE name LIKE :pattern
                       OR email LIKE :pattern
                       OR phone LIKE :pattern
                    LIMIT :limit OFFSET :offset
                """
                rows = self.db.session.execute(
                    text(sql), {"pattern": query_pattern, "limit": limit, "offset": offset}
                ).fetchall()

                for row in rows:
                    result = SearchResult(
                        entity_type=EntityType.CONTACT,
                        entity_id=row[0],
                        title=row[1] or "Unnamed Contact",
                        subtitle=row[2],
                        relevance_score=1.0,
                        metadata={"phone": row[3]},
                    )
                    results.append(result)
            except Exception:
                pass

        return results

    def update_index(self, entity_type: EntityType, entity_id: int) -> bool:
        """Update the search index for a specific entity.

        This triggers re-indexing of a single entity after changes.

        Args:
            entity_type: Type of entity to update
            entity_id: ID of the entity

        Returns:
            True if successful, False otherwise
        """
        if not self.check_fts_available():
            return False

        try:
            if entity_type == EntityType.CONTACT:
                # Delete and re-insert contact in FTS
                self.db.session.execute(
                    text("DELETE FROM contacts_fts WHERE contact_id = :id"), {"id": entity_id}
                )

                # Re-insert with current data
                sql = """
                    INSERT INTO contacts_fts (contact_id, name, email, phone, address, notes)
                    SELECT
                        c.id,
                        COALESCE(c.name, ''),
                        COALESCE(c.email, ''),
                        COALESCE(c.phone, ''),
                        COALESCE(c.address, ''),
                        COALESCE(GROUP_CONCAT(n.content, ' '), '')
                    FROM contacts c
                    LEFT JOIN contact_notes cn ON c.id = cn.contact_id
                    LEFT JOIN notes n ON cn.note_id = n.id
                    WHERE c.id = :id
                    GROUP BY c.id
                """
                self.db.session.execute(text(sql), {"id": entity_id})

            elif entity_type == EntityType.NOTE:
                # Delete and re-insert note in FTS
                self.db.session.execute(
                    text("DELETE FROM notes_fts WHERE note_id = :id"), {"id": entity_id}
                )

                sql = """
                    INSERT INTO notes_fts (note_id, title, content, contact_names)
                    SELECT
                        n.id,
                        COALESCE(n.title, ''),
                        COALESCE(n.content, ''),
                        COALESCE(GROUP_CONCAT(c.name, ', '), '')
                    FROM notes n
                    LEFT JOIN contact_notes cn ON n.id = cn.note_id
                    LEFT JOIN contacts c ON cn.contact_id = c.id
                    WHERE n.id = :id
                    GROUP BY n.id
                """
                self.db.session.execute(text(sql), {"id": entity_id})

            elif entity_type == EntityType.TAG:
                # Delete and re-insert tag in FTS
                self.db.session.execute(
                    text("DELETE FROM tags_fts WHERE tag_id = :id"), {"id": entity_id}
                )

                sql = """
                    INSERT INTO tags_fts (tag_id, name, description, contact_count)
                    SELECT
                        t.id,
                        COALESCE(t.name, ''),
                        COALESCE(t.description, ''),
                        COUNT(DISTINCT ct.contact_id)
                    FROM tags t
                    LEFT JOIN contact_tags ct ON t.id = ct.tag_id
                    WHERE t.id = :id
                    GROUP BY t.id
                """
                self.db.session.execute(text(sql), {"id": entity_id})

            self.db.session.commit()
            self._last_index_update = datetime.now()
            return True

        except Exception as e:
            self.db.session.rollback()
            self.logger.error(
                f"Error updating index for {entity_type.value} {entity_id}: {e}", exc_info=True
            )
            return False

    def rebuild_index(self) -> bool:
        """Rebuild the entire search index.

        This should be called after bulk imports or if the index gets corrupted.

        Returns:
            True if successful, False otherwise
        """
        if not self.check_fts_available():
            return False

        try:
            # Clear existing FTS data
            self.db.session.execute(text("DELETE FROM contacts_fts"))
            self.db.session.execute(text("DELETE FROM notes_fts"))
            self.db.session.execute(text("DELETE FROM tags_fts"))

            # Re-populate contacts_fts
            sql = """
                INSERT INTO contacts_fts (contact_id, name, email, phone, address, notes)
                SELECT
                    c.id,
                    COALESCE(c.name, ''),
                    COALESCE(c.email, ''),
                    COALESCE(c.phone, ''),
                    COALESCE(c.address, ''),
                    COALESCE(GROUP_CONCAT(n.content, ' '), '')
                FROM contacts c
                LEFT JOIN contact_notes cn ON c.id = cn.contact_id
                LEFT JOIN notes n ON cn.note_id = n.id
                GROUP BY c.id
            """
            self.db.session.execute(text(sql))

            # Re-populate notes_fts
            sql = """
                INSERT INTO notes_fts (note_id, title, content, contact_names)
                SELECT
                    n.id,
                    COALESCE(n.title, ''),
                    COALESCE(n.content, ''),
                    COALESCE(GROUP_CONCAT(c.name, ', '), '')
                FROM notes n
                LEFT JOIN contact_notes cn ON n.id = cn.note_id
                LEFT JOIN contacts c ON cn.contact_id = c.id
                GROUP BY n.id
            """
            self.db.session.execute(text(sql))

            # Re-populate tags_fts
            sql = """
                INSERT INTO tags_fts (tag_id, name, description, contact_count)
                SELECT
                    t.id,
                    COALESCE(t.name, ''),
                    COALESCE(t.description, ''),
                    COUNT(DISTINCT ct.contact_id)
                FROM tags t
                LEFT JOIN contact_tags ct ON t.id = ct.tag_id
                GROUP BY t.id
            """
            self.db.session.execute(text(sql))

            self.db.session.commit()
            self._last_index_update = datetime.now()
            return True

        except Exception as e:
            self.db.session.rollback()
            self.logger.error(f"Error rebuilding index: {e}", exc_info=True)
            return False

    def get_index_stats(self) -> dict[str, Any]:
        """Get statistics about the search index.

        Returns:
            Dictionary with index statistics
        """
        stats = {
            "fts_available": self.check_fts_available(),
            "last_update": self._last_index_update,
            "indexed_counts": {"contacts": 0, "notes": 0, "tags": 0},
        }

        if stats["fts_available"]:
            try:
                # Get counts from FTS tables
                result = self.db.session.execute(
                    text("SELECT COUNT(*) FROM contacts_fts")
                ).fetchone()
                stats["indexed_counts"]["contacts"] = result[0] if result else 0

                result = self.db.session.execute(text("SELECT COUNT(*) FROM notes_fts")).fetchone()
                stats["indexed_counts"]["notes"] = result[0] if result else 0

                result = self.db.session.execute(text("SELECT COUNT(*) FROM tags_fts")).fetchone()
                stats["indexed_counts"]["tags"] = result[0] if result else 0

            except Exception:
                pass

        return stats

    def optimize_index(self) -> bool:
        """Optimize the FTS5 index for better performance.

        This merges index segments and can improve search speed.

        Returns:
            True if successful, False otherwise
        """
        if not self.check_fts_available():
            return False

        try:
            # Optimize each FTS table
            self.db.session.execute(
                text("INSERT INTO contacts_fts(contacts_fts) VALUES('optimize')")
            )
            self.db.session.execute(text("INSERT INTO notes_fts(notes_fts) VALUES('optimize')"))
            self.db.session.execute(text("INSERT INTO tags_fts(tags_fts) VALUES('optimize')"))
            self.db.session.commit()
            return True

        except Exception as e:
            self.db.session.rollback()
            self.logger.error(f"Error optimizing index: {e}", exc_info=True)
            return False
