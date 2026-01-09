"""Fixture service for TUI.

Provides async interface for loading test fixture data.
"""

import asyncio
import contextlib
from typing import Any

from prt_src.db import Database
from prt_src.logging_config import get_logger
from tests.fixtures import get_fixture_spec
from tests.fixtures import setup_test_database

logger = get_logger(__name__)


class FixtureService:
    """Service for managing fixture data in TUI."""

    def __init__(self, db: Database):
        """Initialize the fixture service.

        Args:
            db: Database instance for operations
        """
        self.db = db
        self.logger = get_logger(__name__)

    def get_fixture_summary(self) -> dict[str, Any]:
        """Get summary of fixture data without loading.

        Returns:
            Dictionary with fixture counts and info
        """
        spec = get_fixture_spec()
        return {
            "contacts": spec["contacts"]["count"],
            "tags": spec["tags"]["count"],
            "notes": spec["notes"]["count"],
            "relationships": spec["relationships"]["count"],
            "has_images": True,
            "description": "Demo data with realistic sample contacts, tags, and notes",
        }

    async def clear_database(self) -> bool:
        """Clear all data from database (destructive operation!).

        This removes all contacts, tags, notes, and relationships.
        Use with caution!

        Returns:
            True if successful, False otherwise
        """
        import time

        start_time = time.time()
        self.logger.warning("[FIXTURE] Starting database clear - destructive operation!")

        loop = asyncio.get_event_loop()
        try:

            def _clear():
                """Clear all tables in the database."""
                # Import here to avoid circular imports
                from prt_src.models import Contact
                from prt_src.models import ContactMetadata
                from prt_src.models import ContactRelationship
                from prt_src.models import Note
                from prt_src.models import Relationship
                from prt_src.models import RelationshipType
                from prt_src.models import Tag
                from prt_src.models import metadata_notes
                from prt_src.models import metadata_tags

                # Log current counts before deletion
                contact_count = self.db.session.query(Contact).count()
                tag_count = self.db.session.query(Tag).count()
                note_count = self.db.session.query(Note).count()
                self.logger.debug(
                    f"[FIXTURE] Current DB state: {contact_count} contacts, "
                    f"{tag_count} tags, {note_count} notes"
                )

                # Delete in reverse dependency order
                # Start with join tables (many-to-many relationships)
                self.db.session.execute(metadata_notes.delete())
                self.db.session.execute(metadata_tags.delete())
                # Then delete records that depend on contacts
                self.db.session.query(ContactRelationship).delete()
                self.db.session.query(ContactMetadata).delete()
                # Delete the main entities
                self.db.session.query(Relationship).delete()
                self.db.session.query(Note).delete()
                self.db.session.query(Tag).delete()
                self.db.session.query(Contact).delete()
                self.db.session.query(RelationshipType).delete()
                self.db.session.commit()
                # Remove all objects from identity map to prevent conflicts on reload
                self.db.session.expunge_all()
                self.logger.debug("[FIXTURE] All tables cleared and session identity map flushed")

            await loop.run_in_executor(None, _clear)

            elapsed = time.time() - start_time
            self.logger.info(f"[FIXTURE] Database cleared successfully in {elapsed:.2f}s")
            return True

        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(
                f"[FIXTURE] Error clearing database after {elapsed:.2f}s: {e}", exc_info=True
            )
            with contextlib.suppress(Exception):
                self.db.session.rollback()
            return False

    async def load_fixtures(self) -> dict[str, Any]:
        """Load fixture data into database.

        Note: This does NOT clear the database first. Call clear_database()
        first if you want to replace existing data.

        Returns:
            Dictionary with loaded data summary
        """
        import time

        start_time = time.time()
        self.logger.info("[FIXTURE] Starting fixture data load")

        loop = asyncio.get_event_loop()
        try:
            # Run setup_test_database in executor
            self.logger.debug("[FIXTURE] Calling setup_test_database()...")
            fixtures = await loop.run_in_executor(None, setup_test_database, self.db)

            elapsed = time.time() - start_time

            # Build summary
            summary = {
                "success": True,
                "contacts": len(fixtures["contacts"]),
                "tags": len(fixtures["tags"]),
                "notes": len(fixtures["notes"]),
                "relationships": len(fixtures["relationships"]),
                "load_time": elapsed,
                "message": f"Loaded {len(fixtures['contacts'])} contacts with demo data",
            }

            self.logger.info(
                f"[FIXTURE] Load complete: {summary['contacts']} contacts, "
                f"{summary['tags']} tags, {summary['notes']} notes in {elapsed:.2f}s"
            )
            self.logger.debug(f"[FIXTURE] Full summary: {summary}")
            return summary

        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = f"Error loading fixtures: {e}"
            self.logger.error(f"[FIXTURE] Load failed after {elapsed:.2f}s: {e}", exc_info=True)
            return {
                "success": False,
                "contacts": 0,
                "tags": 0,
                "notes": 0,
                "relationships": 0,
                "error": error_msg,
                "message": error_msg,
            }

    async def clear_and_load_fixtures(self) -> dict[str, Any]:
        """Clear database and load fresh fixture data.

        This is a convenience method that combines clear_database() and
        load_fixtures() into a single operation.

        Returns:
            Dictionary with loaded data summary or error info
        """
        import time

        total_start = time.time()
        self.logger.info("[FIXTURE] Starting clear and load operation")

        # Clear first
        clear_start = time.time()
        clear_success = await self.clear_database()
        clear_elapsed = time.time() - clear_start

        if not clear_success:
            self.logger.error(f"[FIXTURE] Clear failed after {clear_elapsed:.2f}s")
            return {
                "success": False,
                "error": "Failed to clear database",
                "message": "Failed to clear database before loading fixtures",
            }

        self.logger.debug(f"[FIXTURE] Clear completed in {clear_elapsed:.2f}s")

        # Then load
        load_start = time.time()
        result = await self.load_fixtures()
        load_elapsed = time.time() - load_start

        total_elapsed = time.time() - total_start

        if result.get("success"):
            self.logger.info(
                f"[FIXTURE] Clear and load complete: {result['contacts']} contacts in {total_elapsed:.2f}s "
                f"(clear: {clear_elapsed:.2f}s, load: {load_elapsed:.2f}s)"
            )
            # Add timing breakdown to result
            result["clear_time"] = clear_elapsed
            result["total_time"] = total_elapsed
        else:
            self.logger.error(
                f"[FIXTURE] Load failed after {load_elapsed:.2f}s: {result.get('error')}",
                extra={"result": result},
            )

        return result
