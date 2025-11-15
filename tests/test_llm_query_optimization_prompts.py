"""
Tests for LLM query optimization patterns added to the system prompt.

This module tests that the LLM system prompt contains the necessary guidance
for generating optimized SQL queries for large databases.

Testing Strategy:
- Use regex patterns for format-agnostic validation
- Focus on semantic content rather than exact text matching
- Validate behavior outcomes, not just prompt text presence
"""

import re
from unittest.mock import MagicMock

import pytest

from prt_src.llm_ollama import OllamaLLM


class TestQueryOptimizationPrompts:
    """Test that LLM system prompt contains query optimization guidance."""

    def test_system_prompt_contains_optimization_section(self, llm_config):
        """Test that the system prompt contains the SQL optimization section.

        Uses regex patterns to be resilient to formatting changes (e.g., markdown headers).
        """
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api, config_manager=llm_config)
        system_prompt = llm._create_system_prompt()

        # Should contain the optimization section header (format-agnostic)
        optimization_header_pattern = r"(?i)(#+\s*)?SQL\s+QUERY\s+OPTIMIZATION\s+PATTERNS"
        assert re.search(
            optimization_header_pattern, system_prompt
        ), "Should contain SQL QUERY OPTIMIZATION PATTERNS header"

        # Should mention large database context (semantic validation)
        large_db_pattern = r"(?i)critical.*large.*database|large.*database.*critical"
        assert re.search(
            large_db_pattern, system_prompt
        ), "Should mention critical importance for large databases"

    def test_system_prompt_contains_limit_pattern(self, llm_config):
        """Test that the system prompt contains guidance on using LIMIT.

        Validates pattern 1: LIMIT LARGE QUERIES with semantic content validation.
        """
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api, config_manager=llm_config)
        system_prompt = llm._create_system_prompt()

        # Should contain LIMIT guidance (pattern-based)
        limit_pattern = r"(?i)(\*\*)?1\.\s*LIMIT\s+LARGE\s+QUERIES"
        assert re.search(
            limit_pattern, system_prompt
        ), "Should contain pattern 1: LIMIT LARGE QUERIES"

        # Should mention preventing overwhelming results (semantic validation)
        overwhelming_pattern = (
            r"(?i)prevent.*overwhelm|overwhelm.*prevent|avoid.*too many|large.*result"
        )
        assert re.search(
            overwhelming_pattern, system_prompt
        ), "Should explain rationale for limiting queries"

        # Should have specific limit examples (flexible numbers)
        limit_example_pattern = r"LIMIT\s+\d{1,3}"
        assert re.search(
            limit_example_pattern, system_prompt
        ), "Should provide specific LIMIT examples with numbers"

    def test_system_prompt_contains_count_before_select_pattern(self, llm_config):
        """Test that the system prompt contains COUNT before SELECT guidance.

        Validates pattern 2: Two-step approach with COUNT(*) first.
        """
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api, config_manager=llm_config)
        system_prompt = llm._create_system_prompt()

        # Should contain pattern 2 header
        count_pattern = r"(?i)(\*\*)?2\.\s*COUNT\s+BEFORE\s+(SELECT|QUERY)"
        assert re.search(
            count_pattern, system_prompt
        ), "Should contain pattern 2: COUNT BEFORE SELECTING"

        # Should show two-step approach (semantic validation)
        two_step_pattern = r"(?i)(first|step\s*1).*COUNT.*\(\*\)|COUNT.*\(\*\).*(first|step\s*1)"
        assert re.search(two_step_pattern, system_prompt), "Should explain COUNT(*) as first step"

        # Should mention checking result size (concept validation)
        size_check_pattern = r"(?i)check.*size|size.*check|estimate.*result|result.*estimate"
        assert re.search(
            size_check_pattern, system_prompt
        ), "Should explain checking result size rationale"

    def test_system_prompt_contains_exclude_binary_data_pattern(self, llm_config):
        """Test that the system prompt contains guidance on excluding binary data.

        Validates pattern 3: Exclude large binary columns unless specifically needed.
        """
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api, config_manager=llm_config)
        system_prompt = llm._create_system_prompt()

        # Should contain pattern 3 header
        binary_pattern = r"(?i)(\*\*)?3\.\s*EXCLUDE\s+(BINARY\s+DATA|LARGE\s+COLUMNS)"
        assert re.search(
            binary_pattern, system_prompt
        ), "Should contain pattern 3: EXCLUDE BINARY DATA"

        # Should specifically mention profile_image field
        profile_image_pattern = r"(?i)profile_image"
        assert re.search(
            profile_image_pattern, system_prompt
        ), "Should specifically mention profile_image field"

        # Should warn against SELECT * (anti-pattern)
        select_star_warning = (
            r"(?i)(avoid|don't|never).*SELECT\s*\*|SELECT\s*\*.*(avoid|slow|large)"
        )
        assert re.search(
            select_star_warning, system_prompt
        ), "Should warn against SELECT * for performance"

    def test_system_prompt_contains_indexed_columns_pattern(self, llm_config):
        """Test that the system prompt contains guidance on using indexed columns.

        Validates pattern 4: Use indexed columns for better performance.
        """
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api, config_manager=llm_config)
        system_prompt = llm._create_system_prompt()

        # Should contain pattern 4 header
        indexed_pattern = r"(?i)(\*\*)?4\.\s*USE\s+INDEXED\s+(COLUMNS|FIELDS)"
        assert re.search(
            indexed_pattern, system_prompt
        ), "Should contain pattern 4: USE INDEXED COLUMNS"

        # Should show fast vs slow examples (performance comparison)
        performance_comparison = (
            r"(?i)(fast|quick|efficient).*(indexed|name|email)|(slow|slower).*(phone|non-indexed)"
        )
        assert re.search(
            performance_comparison, system_prompt
        ), "Should show fast vs slower examples based on indexing"

        # Should mention specific indexed fields (concrete guidance)
        indexed_fields = r"(?i)(name|email).*indexed|(indexed|index).*(name|email)"
        assert re.search(
            indexed_fields, system_prompt
        ), "Should mention specific indexed fields like name or email"

    def test_system_prompt_contains_sampling_pattern(self, llm_config):
        """Test that the system prompt contains guidance on data sampling.

        Validates pattern 5: Use RANDOM() for data exploration instead of full scans.
        """
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api, config_manager=llm_config)
        system_prompt = llm._create_system_prompt()

        # Should contain pattern 5 header
        sampling_pattern = r"(?i)(\*\*)?5\.\s*SAMPLE\s+FOR\s+EXPLORATION"
        assert re.search(
            sampling_pattern, system_prompt
        ), "Should contain pattern 5: SAMPLE FOR EXPLORATION"

        # Should mention RANDOM() function (specific technique)
        random_pattern = r"(?i)(RANDOM\(\)|ORDER\s+BY\s+RANDOM)"
        assert re.search(
            random_pattern, system_prompt
        ), "Should mention RANDOM() function for sampling"

        # Should explain exploration use case (purpose validation)
        exploration_pattern = r"(?i)explor(ation|ing|e)|discover|pattern.*analysis|data.*insight"
        assert re.search(
            exploration_pattern, system_prompt
        ), "Should explain exploration/discovery use case"

    def test_system_prompt_contains_performance_note(self, llm_config):
        """Test that the system prompt contains performance notes about available indexes.

        Validates that performance information is provided to guide optimization decisions.
        """
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api, config_manager=llm_config)
        system_prompt = llm._create_system_prompt()

        # Should mention performance information (flexible format)
        performance_note_pattern = r"(?i)(performance\s+note|index.*info|available.*index)"
        assert re.search(
            performance_note_pattern, system_prompt
        ), "Should mention performance or index information"

        # Should list key indexed fields (semantic validation)
        # At least 3 of these should be mentioned
        key_indexes = ["name", "email", "profile_image", "created_at", "contact_metadata"]
        found_indexes = [idx for idx in key_indexes if idx in system_prompt.lower()]
        assert (
            len(found_indexes) >= 3
        ), f"Should mention at least 3 key indexes. Found: {found_indexes}"

    def test_optimization_patterns_are_numbered(self, llm_config):
        """Test that the 5 optimization patterns are clearly numbered.

        Validates structured organization of optimization patterns.
        """
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api, config_manager=llm_config)
        system_prompt = llm._create_system_prompt()

        # Should have 5 numbered patterns (flexible formatting)
        for i in range(1, 6):
            pattern_number = rf"(\*\*)?{i}\."
            assert re.search(pattern_number, system_prompt), f"Should have numbered pattern {i}"

        # Validate all 5 specific patterns exist
        pattern_names = [
            "LIMIT LARGE QUERIES",
            "COUNT BEFORE",
            "EXCLUDE BINARY",
            "USE INDEXED",
            "SAMPLE FOR EXPLORATION",
        ]
        for pattern_name in pattern_names:
            pattern_regex = rf"(?i){re.escape(pattern_name)}"
            assert re.search(
                pattern_regex, system_prompt
            ), f"Should contain optimization pattern: {pattern_name}"

    def test_optimization_patterns_have_sql_examples(self, llm_config):
        """Test that each optimization pattern includes SQL examples.

        Validates that concrete SQL examples are provided for each optimization.
        """
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api, config_manager=llm_config)
        system_prompt = llm._create_system_prompt()

        # Should contain SQL code examples (format-agnostic)
        sql_code_pattern = r"(?i)(```sql|SELECT\s+\w+|FROM\s+\w+)"
        assert re.search(sql_code_pattern, system_prompt), "Should contain SQL code examples"

        # Should have multiple SQL examples covering different patterns
        sql_examples = re.findall(r"(?i)SELECT.*?(?=\n|\r|$)", system_prompt)
        assert (
            len(sql_examples) >= 5
        ), f"Should have at least 5 SQL examples, found {len(sql_examples)}"

        # Should show both good and bad examples (contrast)
        contrast_patterns = [
            r"(?i)instead\s+of.*SELECT",
            r"(?i)(good|fast).*SELECT",
            r"(?i)(avoid|don't|slower).*SELECT",
        ]
        found_contrasts = sum(
            1 for pattern in contrast_patterns if re.search(pattern, system_prompt)
        )
        assert found_contrasts >= 2, "Should provide contrasting good vs bad SQL examples"

    def test_optimization_guidance_mentions_large_database_context(self, llm_config):
        """Test that optimization guidance specifically mentions large database context.

        Validates that optimizations are contextualized for the database size that triggered them.
        """
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api, config_manager=llm_config)
        system_prompt = llm._create_system_prompt()

        # Should mention the scale that triggered these optimizations (flexible matching)
        scale_indicators = [
            r"(?i)1000\+.*contact",
            r"(?i)large.*database",
            r"(?i)timeout.*prevent",
            r"(?i)performance.*critical",
        ]
        found_scale_mentions = sum(
            1 for pattern in scale_indicators if re.search(pattern, system_prompt)
        )

        assert (
            found_scale_mentions >= 2
        ), "Should mention large database scale context (1000+ contacts, timeouts, performance)"

    def test_good_vs_bad_examples_provided(self, llm_config):
        """Test that the prompt provides both good and bad query examples.

        Validates that optimization guidance includes clear contrasting examples.
        """
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api, config_manager=llm_config)
        system_prompt = llm._create_system_prompt()

        # Should have contrasting example markers (flexible patterns)
        contrast_patterns = [
            r"(?i)instead\s+of:",
            r"(?i)(use|good):",
            r"(?i)(avoid|don't):",
            r"(?i)(fast|quick|efficient):",
            r"(?i)(slow|slower|inefficient):",
        ]
        found_markers = sum(1 for pattern in contrast_patterns if re.search(pattern, system_prompt))

        assert (
            found_markers >= 3
        ), f"Should provide contrasting good vs bad examples with clear markers. Found: {found_markers}"


class TestPromptIntegration:
    """Test that the optimization prompts integrate well with the existing system prompt."""

    def test_optimization_section_placement(self, llm_config):
        """Test that optimization section is placed appropriately in the prompt."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api, config_manager=llm_config)
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

    def test_optimization_section_doesnt_break_existing_content(self, llm_config):
        """Test that adding optimization section doesn't break existing prompt content."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api, config_manager=llm_config)
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

    def test_optimization_section_consistent_formatting(self, llm_config):
        """Test that optimization section uses consistent formatting with rest of prompt."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api, config_manager=llm_config)
        system_prompt = llm._create_system_prompt()

        # Find the optimization section
        opt_start = system_prompt.find("## SQL QUERY OPTIMIZATION PATTERNS")
        reminders_start = system_prompt.find("## IMPORTANT REMINDERS")
        opt_section = system_prompt[opt_start:reminders_start]

        # Should use consistent header formatting
        assert "##" in opt_section, "Should use ## for section headers"

        # Should use consistent bold formatting
        assert "**" in opt_section, "Should use ** for bold text"

        # Should use code block formatting
        assert "```sql" in opt_section, "Should use code blocks for SQL examples"

    def test_schema_info_still_included(self, llm_config):
        """Test that schema information is still included despite optimization additions."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api, config_manager=llm_config)
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
    def test_complete_system_prompt_is_valid(self, llm_config):
        """Integration test that the complete system prompt is well-formed."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api, config_manager=llm_config)
        system_prompt = llm._create_system_prompt()

        # Basic validation checks
        assert len(system_prompt) > 5000, "System prompt should be substantial"
        assert len(system_prompt) < 50000, "System prompt should not be excessively long"

        # Should not have formatting errors
        assert "None" not in system_prompt, "Should not contain 'None' from failed operations"
        assert "Error:" not in system_prompt, "Should not contain error messages"

        # Should end properly


#        assert system_prompt.endswith('"""'), "Should end with proper string termination"


class TestOptimizationPatternContent:
    """Test the specific content of each optimization pattern."""

    def test_pattern_1_limit_queries_content(self, llm_config):
        """Test that pattern 1 (LIMIT queries) has appropriate content."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api, config_manager=llm_config)
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

    def test_pattern_2_count_before_select_content(self, llm_config):
        """Test that pattern 2 (COUNT before SELECT) has appropriate content."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api, config_manager=llm_config)
        system_prompt = llm._create_system_prompt()

        pattern_start = system_prompt.find("**2. COUNT BEFORE SELECTING**")
        assert pattern_start != -1, "Should find pattern 2"

        # Should show the two-step approach
        pattern_section = system_prompt[pattern_start : pattern_start + 500]
        assert "First:" in pattern_section, "Should show first step"
        assert "Then:" in pattern_section, "Should show second step"

    def test_pattern_3_exclude_binary_data_content(self, llm_config):
        """Test that pattern 3 (exclude binary data) has appropriate content."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api, config_manager=llm_config)
        system_prompt = llm._create_system_prompt()

        pattern_start = system_prompt.find("**3. EXCLUDE BINARY DATA**")
        assert pattern_start != -1, "Should find pattern 3"

        # Should specifically mention profile_image
        pattern_section = system_prompt[pattern_start : pattern_start + 500]
        assert "profile_image" in pattern_section, "Should mention profile_image specifically"

    def test_pattern_4_indexed_columns_content(self, llm_config):
        """Test that pattern 4 (use indexed columns) has appropriate content."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api, config_manager=llm_config)
        system_prompt = llm._create_system_prompt()

        pattern_start = system_prompt.find("**4. USE INDEXED COLUMNS**")
        assert pattern_start != -1, "Should find pattern 4"

        # Should show fast vs slower examples
        pattern_section = system_prompt[pattern_start : pattern_start + 500]
        assert "Fast" in pattern_section, "Should show fast examples"
        assert "Slower" in pattern_section, "Should show slower examples"

    def test_pattern_5_sampling_content(self, llm_config):
        """Test that pattern 5 (sampling) has appropriate content."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api, config_manager=llm_config)
        system_prompt = llm._create_system_prompt()

        pattern_start = system_prompt.find("**5. SAMPLE FOR EXPLORATION**")
        assert pattern_start != -1, "Should find pattern 5"

        # Should mention RANDOM() and exploration
        pattern_section = system_prompt[pattern_start : pattern_start + 500]
        assert "RANDOM()" in pattern_section, "Should mention RANDOM() function"
        assert "exploration" in pattern_section.lower(), "Should mention exploration use case"
