"""
Tests for LLM query optimization patterns added to the system prompt.

This module tests that the LLM system prompt contains the necessary guidance
for generating optimized SQL queries for large databases.
"""

from unittest.mock import MagicMock

import pytest

from prt_src.llm_ollama import OllamaLLM


class TestQueryOptimizationPrompts:
    """Test that LLM system prompt contains query optimization guidance."""

    def test_system_prompt_contains_optimization_section(self):
        """Test that the system prompt contains the SQL optimization section."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api)
        system_prompt = llm._create_system_prompt()

        # Should contain the optimization section header
        assert "SQL QUERY OPTIMIZATION PATTERNS" in system_prompt
        assert "Critical for Large Databases" in system_prompt

    def test_system_prompt_contains_limit_pattern(self):
        """Test that the system prompt contains guidance on using LIMIT."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api)
        system_prompt = llm._create_system_prompt()

        # Should contain LIMIT guidance
        assert "LIMIT LARGE QUERIES" in system_prompt
        assert "LIMIT" in system_prompt
        assert "prevent overwhelming results" in system_prompt

        # Should have specific examples
        assert "LIMIT 50" in system_prompt or "LIMIT 100" in system_prompt

    def test_system_prompt_contains_count_before_select_pattern(self):
        """Test that the system prompt contains COUNT before SELECT guidance."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api)
        system_prompt = llm._create_system_prompt()

        # Should contain COUNT guidance
        assert "COUNT BEFORE SELECTING" in system_prompt
        assert "COUNT(*)" in system_prompt
        assert "check result size" in system_prompt

    def test_system_prompt_contains_exclude_binary_data_pattern(self):
        """Test that the system prompt contains guidance on excluding binary data."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api)
        system_prompt = llm._create_system_prompt()

        # Should contain binary data guidance
        assert "EXCLUDE BINARY DATA" in system_prompt
        assert "profile_image" in system_prompt
        assert "binary" in system_prompt.lower()

        # Should warn against SELECT *
        assert "SELECT *" in system_prompt

    def test_system_prompt_contains_indexed_columns_pattern(self):
        """Test that the system prompt contains guidance on using indexed columns."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api)
        system_prompt = llm._create_system_prompt()

        # Should contain index guidance
        assert "USE INDEXED COLUMNS" in system_prompt
        assert "indexed" in system_prompt.lower()
        assert "performance" in system_prompt.lower()

        # Should mention specific indexed fields
        assert "name" in system_prompt
        assert "email" in system_prompt

    def test_system_prompt_contains_sampling_pattern(self):
        """Test that the system prompt contains guidance on data sampling."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api)
        system_prompt = llm._create_system_prompt()

        # Should contain sampling guidance
        assert "SAMPLE FOR EXPLORATION" in system_prompt
        assert "RANDOM()" in system_prompt
        assert "exploration" in system_prompt.lower()

    def test_system_prompt_contains_performance_note(self):
        """Test that the system prompt contains performance notes about available indexes."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api)
        system_prompt = llm._create_system_prompt()

        # Should mention available indexes
        assert "Performance Note" in system_prompt
        assert "indexes on:" in system_prompt

        # Should list the key indexes
        expected_indexes = ["name", "email", "profile_image", "created_at", "contact_metadata"]
        for index_name in expected_indexes:
            assert index_name in system_prompt, f"Should mention {index_name} index"

    def test_optimization_patterns_are_numbered(self):
        """Test that the 5 optimization patterns are clearly numbered."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api)
        system_prompt = llm._create_system_prompt()

        # Should have 5 numbered patterns
        for i in range(1, 6):
            pattern_marker = f"**{i}."
            assert pattern_marker in system_prompt, f"Should have numbered pattern {i}"

    def test_optimization_patterns_have_sql_examples(self):
        """Test that each optimization pattern includes SQL examples."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api)
        system_prompt = llm._create_system_prompt()

        # Should contain SQL code blocks
        assert "```sql" in system_prompt, "Should contain SQL code examples"

        # Should have multiple SQL examples (at least one per pattern)
        sql_blocks = system_prompt.count("```sql")
        assert sql_blocks >= 5, f"Should have at least 5 SQL examples, found {sql_blocks}"

    def test_optimization_guidance_mentions_large_database_context(self):
        """Test that optimization guidance specifically mentions large database context."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api)
        system_prompt = llm._create_system_prompt()

        # Should mention the context that triggered these optimizations
        database_size_indicators = ["1000+", "large", "timeout", "performance"]
        found_indicators = [
            indicator
            for indicator in database_size_indicators
            if indicator in system_prompt.lower()
        ]

        assert (
            len(found_indicators) >= 2
        ), f"Should mention large database context. Found: {found_indicators}"

    def test_good_vs_bad_examples_provided(self):
        """Test that the prompt provides both good and bad query examples."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api)
        system_prompt = llm._create_system_prompt()

        # Should have contrasting examples
        contrast_markers = ["Instead of:", "Use:", "Good:", "Avoid:", "Fast:", "Slower:"]
        found_markers = [marker for marker in contrast_markers if marker in system_prompt]

        assert (
            len(found_markers) >= 3
        ), f"Should provide contrasting examples. Found markers: {found_markers}"


class TestPromptIntegration:
    """Test that the optimization prompts integrate well with the existing system prompt."""

    def test_optimization_section_placement(self):
        """Test that optimization section is placed appropriately in the prompt."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api)
        system_prompt = llm._create_system_prompt()

        # Find the position of optimization section
        opt_section_start = system_prompt.find("SQL QUERY OPTIMIZATION PATTERNS")
        important_reminders_start = system_prompt.find("## IMPORTANT REMINDERS")

        # Optimization section should come before final reminders
        assert (
            opt_section_start < important_reminders_start
        ), "Optimization patterns should come before final reminders"

        # Should not be at the very beginning
        assert opt_section_start > 1000, "Optimization section should not be at the beginning"

    def test_optimization_section_doesnt_break_existing_content(self):
        """Test that adding optimization section doesn't break existing prompt content."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api)
        system_prompt = llm._create_system_prompt()

        # Should still contain key existing sections
        existing_sections = [
            "ABOUT PRT",
            "YOUR ROLE",
            "AVAILABLE TOOLS",
            "IMPORTANT REMINDERS",
            "CRITICAL SECURITY RULES",
        ]

        for section in existing_sections:
            assert section in system_prompt, f"Should still contain {section} section"

    def test_optimization_section_consistent_formatting(self):
        """Test that optimization section uses consistent formatting with rest of prompt."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api)
        system_prompt = llm._create_system_prompt()

        # Find the optimization section
        opt_start = system_prompt.find("SQL QUERY OPTIMIZATION PATTERNS")
        reminders_start = system_prompt.find("## IMPORTANT REMINDERS")
        opt_section = system_prompt[opt_start:reminders_start]

        # Should use consistent header formatting
        assert "##" in opt_section, "Should use ## for section headers"

        # Should use consistent bold formatting
        assert "**" in opt_section, "Should use ** for bold text"

        # Should use code block formatting
        assert "```sql" in opt_section, "Should use code blocks for SQL examples"

    def test_schema_info_still_included(self):
        """Test that schema information is still included despite optimization additions."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api)
        system_prompt = llm._create_system_prompt()

        # Should still contain database schema information
        schema_indicators = ["contacts", "tags", "notes", "table", "column"]
        found_indicators = [
            indicator for indicator in schema_indicators if indicator in system_prompt.lower()
        ]

        assert (
            len(found_indicators) >= 4
        ), f"Should still contain schema information. Found: {found_indicators}"

    @pytest.mark.integration
    def test_complete_system_prompt_is_valid(self):
        """Integration test that the complete system prompt is well-formed."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api)
        system_prompt = llm._create_system_prompt()

        # Basic validation checks
        assert len(system_prompt) > 5000, "System prompt should be substantial"
        assert len(system_prompt) < 50000, "System prompt should not be excessively long"

        # Should not have formatting errors
        assert "None" not in system_prompt, "Should not contain 'None' from failed operations"
        assert "Error:" not in system_prompt, "Should not contain error messages"

        # Should end properly
        assert system_prompt.endswith('"""'), "Should end with proper string termination"


class TestOptimizationPatternContent:
    """Test the specific content of each optimization pattern."""

    def test_pattern_1_limit_queries_content(self):
        """Test that pattern 1 (LIMIT queries) has appropriate content."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api)
        system_prompt = llm._create_system_prompt()

        # Find pattern 1 section
        pattern_start = system_prompt.find("**1. LIMIT LARGE QUERIES**")
        assert pattern_start != -1, "Should find pattern 1"

        # Should mention specific limits
        pattern_section = system_prompt[pattern_start : pattern_start + 500]
        limit_values = ["50", "100"]
        assert any(
            limit in pattern_section for limit in limit_values
        ), "Pattern 1 should mention specific LIMIT values"

    def test_pattern_2_count_before_select_content(self):
        """Test that pattern 2 (COUNT before SELECT) has appropriate content."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api)
        system_prompt = llm._create_system_prompt()

        pattern_start = system_prompt.find("**2. COUNT BEFORE SELECTING**")
        assert pattern_start != -1, "Should find pattern 2"

        # Should show the two-step approach
        pattern_section = system_prompt[pattern_start : pattern_start + 500]
        assert "First:" in pattern_section, "Should show first step"
        assert "Then:" in pattern_section, "Should show second step"

    def test_pattern_3_exclude_binary_data_content(self):
        """Test that pattern 3 (exclude binary data) has appropriate content."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api)
        system_prompt = llm._create_system_prompt()

        pattern_start = system_prompt.find("**3. EXCLUDE BINARY DATA**")
        assert pattern_start != -1, "Should find pattern 3"

        # Should specifically mention profile_image
        pattern_section = system_prompt[pattern_start : pattern_start + 500]
        assert "profile_image" in pattern_section, "Should mention profile_image specifically"

    def test_pattern_4_indexed_columns_content(self):
        """Test that pattern 4 (use indexed columns) has appropriate content."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api)
        system_prompt = llm._create_system_prompt()

        pattern_start = system_prompt.find("**4. USE INDEXED COLUMNS**")
        assert pattern_start != -1, "Should find pattern 4"

        # Should show fast vs slower examples
        pattern_section = system_prompt[pattern_start : pattern_start + 500]
        assert "Fast" in pattern_section, "Should show fast examples"
        assert "Slower" in pattern_section, "Should show slower examples"

    def test_pattern_5_sampling_content(self):
        """Test that pattern 5 (sampling) has appropriate content."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api)
        system_prompt = llm._create_system_prompt()

        pattern_start = system_prompt.find("**5. SAMPLE FOR EXPLORATION**")
        assert pattern_start != -1, "Should find pattern 5"

        # Should mention RANDOM() and exploration
        pattern_section = system_prompt[pattern_start : pattern_start + 500]
        assert "RANDOM()" in pattern_section, "Should mention RANDOM() function"
        assert "exploration" in pattern_section.lower(), "Should mention exploration use case"
