"""
Tests for enhanced schema context for profile images and performance guidance.

This module tests that the schema information now provides proper context about
profile images (contact photos) and performance optimization guidance.
"""

from prt_src.schema_info import get_schema_for_llm


class TestEnhancedSchemaContext:
    """Test enhanced schema context for profile images."""

    def test_profile_image_columns_have_context(self):
        """Test that profile image columns include explanatory context."""
        schema = get_schema_for_llm()

        # Should explain what profile_image actually contains
        assert (
            "CONTACT PHOTO/AVATAR" in schema
        ), "Should explain profile_image contains contact photos"
        assert "binary data" in schema.lower(), "Should mention binary data nature"
        assert "50-500KB" in schema, "Should provide size estimates"

        # Should explain related columns
        assert "PHOTO FILENAME" in schema, "Should explain profile_image_filename purpose"
        assert "PHOTO FORMAT" in schema, "Should explain profile_image_mime_type purpose"

    def test_profile_image_query_examples_provided(self):
        """Test that specific profile image query examples are provided."""
        schema = get_schema_for_llm()

        # Should provide examples for common profile image queries
        examples = [
            "WHERE profile_image IS NOT NULL",  # Finding contacts with images
            "WHERE profile_image IS NULL",  # Finding contacts without images
            "COUNT(*) FROM contacts WHERE profile_image IS NOT NULL",  # Counting
        ]

        for example in examples:
            assert example in schema, f"Should provide example: {example}"

    def test_performance_optimization_guidance_included(self):
        """Test that performance optimization guidance is included."""
        schema = get_schema_for_llm()

        # Should include performance optimization section
        assert "PERFORMANCE OPTIMIZATION" in schema, "Should have performance optimization section"
        assert "Essential for 1000+ contacts" in schema, "Should mention large dataset context"

        # Should warn about binary data performance implications
        performance_guidance = [
            "Always use `LIMIT`",
            "Exclude `profile_image` column from SELECT",
            "Use `COUNT(*)` to check result size",
            "Prefer indexed columns",
        ]

        for guidance in performance_guidance:
            assert guidance in schema, f"Should include guidance: {guidance}"

    def test_slow_vs_fast_query_examples(self):
        """Test that slow vs fast query examples are provided."""
        schema = get_schema_for_llm()

        # Should show what NOT to do and what TO do
        assert "❌ SLOW:" in schema, "Should show slow query examples"
        assert "✅ FAST:" in schema, "Should show fast query examples"

        # Should warn against SELECT * with binary data
        assert "SELECT * FROM contacts WHERE profile_image IS NOT NULL" in schema
        assert (
            "SELECT id, name, email, phone FROM contacts WHERE profile_image IS NOT NULL" in schema
        )

    def test_common_user_request_examples(self):
        """Test that common user request examples are provided."""
        schema = get_schema_for_llm()

        # Should include user-friendly query examples
        user_requests = [
            "Find contacts with profile images",
            "Show me contacts without photos",
            "How many contacts have profile pictures",
            "Make a directory of contacts with images",
        ]

        for request in user_requests:
            assert request.lower() in schema.lower(), f"Should include example for: {request}"

    def test_schema_size_increased_appropriately(self):
        """Test that schema size increased but remains reasonable."""
        schema = get_schema_for_llm()

        # Should be larger than before but not excessive
        assert len(schema) > 5000, "Schema should be larger with new context"
        assert len(schema) < 10000, "Schema should not be excessively large"

        # Should have more lines
        lines = schema.split("\n")
        assert len(lines) > 150, "Should have more lines with enhanced context"

    def test_profile_image_context_integration(self):
        """Test that profile image context is well integrated with existing schema."""
        schema = get_schema_for_llm()

        # Should maintain existing structure while adding new context
        assert "## PRT DATABASE SCHEMA" in schema, "Should keep existing schema header"
        assert "Table: `contacts`" in schema, "Should keep existing table documentation"
        assert "COMMON SQL QUERY PATTERNS" in schema, "Should keep existing query patterns"

        # New profile image context should be well-placed
        profile_section_start = schema.find("Profile Images (Contact Photos/Avatars)")
        query_patterns_start = schema.find("COMMON SQL QUERY PATTERNS")

        assert (
            profile_section_start > query_patterns_start
        ), "Profile image section should come after basic query patterns"

    def test_binary_data_performance_warnings(self):
        """Test that binary data performance warnings are clear."""
        schema = get_schema_for_llm()

        # Should clearly warn about binary data implications
        warnings = [
            "binary photo data",
            "50-500KB each",
            "Exclude `profile_image` column",
            "large datasets",
        ]

        for warning in warnings:
            assert warning in schema, f"Should include warning about: {warning}"

    def test_indexed_column_guidance(self):
        """Test that guidance about indexed columns is provided."""
        schema = get_schema_for_llm()

        # Should mention which columns are indexed for better performance
        indexed_columns = ["name", "email", "created_at"]

        for column in indexed_columns:
            assert f"`{column}`" in schema, f"Should mention indexed column: {column}"

        assert "Prefer indexed columns" in schema, "Should provide indexed column guidance"

    def test_user_friendly_language(self):
        """Test that the schema uses user-friendly language."""
        schema = get_schema_for_llm()

        # Should use emojis and friendly indicators
        friendly_elements = ["🔍", "⚡", "✅", "❌"]

        for element in friendly_elements:
            assert element in schema, f"Should include friendly element: {element}"

        # Should use clear, non-technical language for explanations
        user_friendly_terms = ["contact photos", "profile pictures", "photos", "avatars"]

        schema_lower = schema.lower()
        found_terms = [term for term in user_friendly_terms if term in schema_lower]
        assert len(found_terms) >= 2, "Should use user-friendly terms for profile images"
