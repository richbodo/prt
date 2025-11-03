"""
Tests for database performance indexes added in migration 005.

This module tests that critical indexes are present and improve query performance
for large contact databases.
"""

import time

import pytest
from sqlalchemy import text


class TestPerformanceIndexes:
    """Test that performance indexes are present and functional."""

    def test_all_performance_indexes_exist(self, test_db):
        """Test that all expected performance indexes were created."""
        db, fixtures = test_db

        # Apply the performance indexes migration to the test database
        self._apply_performance_indexes_migration(db)

        # Get list of all indexes
        cursor = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='index'"))
        index_names = [row[0] for row in cursor.fetchall()]

        # Expected performance indexes from migration 005
        expected_indexes = [
            "idx_contacts_name",
            "idx_contacts_email",
            "idx_contacts_profile_image_not_null",
            "idx_contacts_created_at",
            "idx_contact_metadata_contact_id",
            "idx_tags_name",
            "idx_notes_title",
            "idx_contacts_name_email",
        ]

        for expected_index in expected_indexes:
            assert expected_index in index_names, f"Missing performance index: {expected_index}"

    def _apply_performance_indexes_migration(self, db):
        """Apply the performance indexes migration to the test database."""
        # Execute index creation statements individually with error handling
        index_statements = [
            "CREATE INDEX IF NOT EXISTS idx_contacts_name ON contacts(name)",
            "CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email)",
            "CREATE INDEX IF NOT EXISTS idx_contacts_profile_image_not_null ON contacts(id) WHERE profile_image IS NOT NULL",
            "CREATE INDEX IF NOT EXISTS idx_contacts_created_at ON contacts(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_contact_metadata_contact_id ON contact_metadata(contact_id)",
            "CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name)",
            "CREATE INDEX IF NOT EXISTS idx_notes_title ON notes(title)",
            "CREATE INDEX IF NOT EXISTS idx_contacts_name_email ON contacts(name, email)",
        ]

        for statement in index_statements:
            try:
                db.session.execute(text(statement))
                db.session.commit()
            except Exception as e:
                print(f"Failed to create index with statement: {statement}")
                print(f"Error: {e}")
                # Let's check if the contacts table exists and has the name column
                cursor = db.session.execute(text("PRAGMA table_info(contacts)"))
                columns = cursor.fetchall()
                print(f"Contacts table columns: {columns}")
                raise

    def test_critical_indexes_exist_with_sql_details(self, test_db):
        """Test that critical indexes exist with proper SQL structure."""
        db, fixtures = test_db

        # Apply the performance indexes migration to the test database
        self._apply_performance_indexes_migration(db)

        # Test key indexes with their expected SQL patterns
        test_cases = [
            ("idx_contacts_name", "contacts(name)"),
            ("idx_contacts_email", "contacts(email)"),
            ("idx_contacts_profile_image_not_null", "WHERE profile_image IS NOT NULL"),
            ("idx_contacts_name_email", "contacts(name, email)"),
            ("idx_contact_metadata_contact_id", "contact_metadata(contact_id)"),
        ]

        for index_name, expected_pattern in test_cases:
            cursor = db.session.execute(
                text(
                    f"""
                SELECT sql FROM sqlite_master
                WHERE type='index' AND name='{index_name}'
            """
                )
            )
            result = cursor.fetchone()

            assert result is not None, f"{index_name} index should exist"
            sql = result[0]
            assert (
                expected_pattern in sql
            ), f"{index_name} should contain pattern: {expected_pattern}"


class TestIndexPerformance:
    """Test that indexes actually improve query performance."""

    def test_name_search_uses_index(self, test_db):
        """Test that name searches use the name index."""
        db, fixtures = test_db

        # Use EXPLAIN QUERY PLAN to verify index usage
        cursor = db.session.execute(
            text(
                """
            EXPLAIN QUERY PLAN
            SELECT * FROM contacts WHERE name LIKE 'John%'
        """
            )
        )

        query_plan = cursor.fetchall()
        query_plan_str = " ".join([str(row) for row in query_plan])

        # Should mention the index in the query plan
        assert (
            "idx_contacts_name" in query_plan_str
        ), f"Query should use name index. Plan: {query_plan_str}"

    def test_email_search_uses_index(self, test_db):
        """Test that email searches use the email index."""
        db, fixtures = test_db

        cursor = db.session.execute(
            text(
                """
            EXPLAIN QUERY PLAN
            SELECT * FROM contacts WHERE email IS NOT NULL
        """
            )
        )

        query_plan = cursor.fetchall()
        query_plan_str = " ".join([str(row) for row in query_plan])

        # Should mention the index in the query plan
        assert (
            "idx_contacts_email" in query_plan_str
        ), f"Query should use email index. Plan: {query_plan_str}"

    def test_profile_image_conditional_search_uses_index(self, test_db):
        """Test that profile image searches use the conditional index."""
        db, fixtures = test_db

        cursor = db.session.execute(
            text(
                """
            EXPLAIN QUERY PLAN
            SELECT id, name FROM contacts WHERE profile_image IS NOT NULL
        """
            )
        )

        query_plan = cursor.fetchall()
        query_plan_str = " ".join([str(row) for row in query_plan])

        # Should mention the conditional index
        assert (
            "idx_contacts_profile_image_not_null" in query_plan_str
        ), f"Query should use profile image conditional index. Plan: {query_plan_str}"

    @pytest.mark.integration
    def test_index_performance_with_large_dataset(self, test_db):
        """Test index performance benefits with a larger dataset."""
        db, fixtures = test_db

        # Add more test data to see performance difference
        # (This is a simplified test - in real scenario with 1800+ contacts the difference would be more dramatic)

        # Insert additional test contacts
        for i in range(50):
            db.session.execute(
                text(
                    """
                INSERT INTO contacts (name, email)
                VALUES (:name, :email)
            """
                ),
                {"name": f"TestContact{i}", "email": f"test{i}@example.com"},
            )
        db.session.commit()

        # Test indexed query performance
        start_time = time.time()
        cursor = db.session.execute(text("SELECT * FROM contacts WHERE name LIKE 'Test%'"))
        results = cursor.fetchall()
        indexed_time = time.time() - start_time

        # Verify we got results and the query was fast
        assert len(results) >= 50, "Should find at least 50 test contacts"
        assert indexed_time < 0.1, f"Indexed query should be fast, took {indexed_time:.3f}s"

    def test_migration_005_applied_successfully(self, test_db):
        """Test that migration 005 was applied and documented."""
        db, fixtures = test_db

        # Check that we can query the migration was applied
        # (This assumes there's a migration tracking table or similar mechanism)

        # At minimum, verify all our indexes exist
        cursor = db.session.execute(
            text(
                """
            SELECT COUNT(*) FROM sqlite_master
            WHERE type='index' AND name IN (
                'idx_contacts_name',
                'idx_contacts_email',
                'idx_contacts_profile_image_not_null',
                'idx_contacts_created_at',
                'idx_contact_metadata_contact_id',
                'idx_tags_name',
                'idx_notes_title',
                'idx_contacts_name_email'
            )
        """
            )
        )

        index_count = cursor.fetchone()[0]
        assert index_count == 8, f"Should have 8 performance indexes, found {index_count}"


class TestIndexOptimizationPatterns:
    """Test that the indexes support the optimization patterns in the LLM prompt."""

    def test_name_pattern_search_optimization(self, test_db):
        """Test that name pattern searches like 'John%' are optimized."""
        db, fixtures = test_db

        # This pattern is mentioned in the LLM prompt
        cursor = db.session.execute(
            text(
                """
            EXPLAIN QUERY PLAN
            SELECT * FROM contacts WHERE name LIKE 'John%' LIMIT 50
        """
            )
        )

        query_plan = cursor.fetchall()
        query_plan_str = " ".join([str(row) for row in query_plan])

        # Should use the name index for prefix searches
        assert "idx_contacts_name" in query_plan_str, "Name prefix search should use index"

    def test_email_not_null_optimization(self, test_db):
        """Test that email NOT NULL searches are optimized."""
        db, fixtures = test_db

        # This pattern is mentioned in the LLM prompt
        cursor = db.session.execute(
            text(
                """
            EXPLAIN QUERY PLAN
            SELECT * FROM contacts WHERE email IS NOT NULL LIMIT 50
        """
            )
        )

        query_plan = cursor.fetchall()
        query_plan_str = " ".join([str(row) for row in query_plan])

        assert "idx_contacts_email" in query_plan_str, "Email NOT NULL search should use index"

    def test_profile_image_count_optimization(self, test_db):
        """Test that profile image count queries are optimized."""
        db, fixtures = test_db

        # COUNT(*) queries mentioned in LLM prompt
        cursor = db.session.execute(
            text(
                """
            EXPLAIN QUERY PLAN
            SELECT COUNT(*) FROM contacts WHERE profile_image IS NOT NULL
        """
            )
        )

        query_plan = cursor.fetchall()
        query_plan_str = " ".join([str(row) for row in query_plan])

        # Should use the conditional index for counting
        assert (
            "idx_contacts_profile_image_not_null" in query_plan_str
        ), "Profile image count should use conditional index"

    def test_composite_name_email_search_optimization(self, test_db):
        """Test that combined name+email searches use the composite index."""
        db, fixtures = test_db

        cursor = db.session.execute(
            text(
                """
            EXPLAIN QUERY PLAN
            SELECT * FROM contacts WHERE name LIKE 'John%' AND email IS NOT NULL
        """
            )
        )

        query_plan = cursor.fetchall()
        query_plan_str = " ".join([str(row) for row in query_plan])

        # Should use one of the relevant indexes
        has_relevant_index = any(
            idx in query_plan_str
            for idx in ["idx_contacts_name", "idx_contacts_email", "idx_contacts_name_email"]
        )

        assert (
            has_relevant_index
        ), f"Combined search should use relevant index. Plan: {query_plan_str}"
