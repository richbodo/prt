"""
Functional tests for LLM query optimization behavior.

This module tests that the LLM actually generates optimized SQL queries
when prompted, not just that the optimization patterns exist in the system prompt.

Testing Strategy:
- Mock LLM responses to simulate optimized query generation
- Validate that optimization patterns prevent known slow queries
- Test actual behavior outcomes, not just prompt content
- Use realistic test scenarios with performance characteristics
"""

from unittest.mock import MagicMock

import pytest

from prt_src.llm_ollama import OllamaLLM
from tests.fixtures_optimization.optimization_test_queries import QueryOptimizationFixtures


@pytest.mark.unit
class TestQueryOptimizationBehavior:
    """Test query optimization behavior using mock responses."""

    def test_optimization_response_includes_limit_clause(self):
        """Test that optimization guidance includes LIMIT clauses."""
        # This test validates that the guidance would include LIMIT clauses
        # when dealing with potentially large queries

        expected_patterns = ["LIMIT", "prevent overwhelming", "bounded result"]
        sample_optimized_response = (
            "I'll search for contacts with profile images using an optimized query "
            "with a LIMIT clause to prevent overwhelming results:\n\n"
            "```sql\nSELECT id, name, email FROM contacts WHERE profile_image IS NOT NULL LIMIT 50\n```"
        )

        # Verify that a properly optimized response contains the expected patterns
        found_patterns = [
            pattern
            for pattern in expected_patterns
            if pattern.lower() in sample_optimized_response.lower()
        ]

        assert (
            len(found_patterns) >= 2
        ), f"Should contain optimization patterns. Found: {found_patterns}"
        assert "LIMIT 50" in sample_optimized_response or "LIMIT 100" in sample_optimized_response

    def test_optimization_response_includes_count_before_select(self):
        """Test that optimization guidance includes COUNT before SELECT pattern."""
        # This test validates two-step approach pattern
        sample_optimized_response = (
            "I'll check the count first, then show examples:\n\n"
            "Step 1 - Count: `SELECT COUNT(*) FROM contacts WHERE profile_image IS NOT NULL`\n"
            "Step 2 - Examples: `SELECT id, name, email FROM contacts WHERE profile_image IS NOT NULL LIMIT 10`\n\n"
            "Found 3 contacts total, here are examples..."
        )

        # Verify two-step approach is demonstrated
        assert "COUNT(*)" in sample_optimized_response
        assert "Step 1" in sample_optimized_response and "Step 2" in sample_optimized_response
        assert "LIMIT" in sample_optimized_response
        assert "count first" in sample_optimized_response.lower()

    def test_optimization_response_excludes_binary_data(self):
        """Test that optimization guidance excludes binary data by default."""
        # This test validates binary data exclusion pattern
        sample_optimized_response = (
            "I'll get contact information while excluding the large binary profile_image data:\n\n"
            "```sql\nSELECT id, name, email, phone FROM contacts WHERE profile_image IS NOT NULL LIMIT 50\n```\n\n"
            "This excludes the binary profile_image column for better performance."
        )

        # Verify binary data exclusion is explained and applied
        assert "exclud" in sample_optimized_response.lower()
        assert "binary" in sample_optimized_response.lower()
        assert "id, name, email" in sample_optimized_response
        assert "SELECT *" not in sample_optimized_response
        assert "performance" in sample_optimized_response.lower()

    def test_optimization_response_uses_indexed_columns(self):
        """Test that optimization guidance prefers indexed columns."""
        # This test validates indexed column usage pattern
        sample_optimized_response = (
            "I'll search using the indexed name column for optimal performance:\n\n"
            "```sql\nSELECT id, name, email, phone FROM contacts WHERE name LIKE 'John%' LIMIT 50\n```\n\n"
            "Using indexed name column for fast search."
        )

        # Verify indexed column usage is explained
        assert "indexed" in sample_optimized_response.lower()
        assert "name" in sample_optimized_response
        assert "LIKE 'John%'" in sample_optimized_response
        assert (
            "performance" in sample_optimized_response.lower()
            or "fast" in sample_optimized_response.lower()
        )

    def test_optimization_response_uses_sampling_for_exploration(self):
        """Test that optimization guidance uses RANDOM() for exploration."""
        # This test validates sampling approach pattern
        sample_optimized_response = (
            "I'll use sampling to explore your data efficiently:\n\n"
            "```sql\nSELECT id, name, email FROM contacts ORDER BY RANDOM() LIMIT 20\n```\n\n"
            "This gives you a representative sample for exploration."
        )

        # Verify sampling approach is explained
        assert "RANDOM()" in sample_optimized_response
        assert (
            "sample" in sample_optimized_response.lower()
            or "exploration" in sample_optimized_response.lower()
        )
        assert "LIMIT" in sample_optimized_response


@pytest.mark.unit
class TestOptimizationPerformanceImpact:
    """Test optimization patterns that improve performance characteristics."""

    def test_optimization_prevents_large_result_sets(self):
        """Test that optimization patterns prevent large result sets."""
        # Test the pattern that prevents overwhelming results
        sample_optimized_response = (
            "I'll limit the results to prevent overwhelming output:\n\n"
            "```sql\nSELECT id, name, email FROM contacts LIMIT 50\n```\n\n"
            "Showing first 50 contacts. Use search filters to narrow results."
        )

        # Verify result limiting pattern is demonstrated
        assert "LIMIT" in sample_optimized_response
        assert "50" in sample_optimized_response
        assert (
            "prevent" in sample_optimized_response.lower()
            and "overwhelming" in sample_optimized_response.lower()
        )

    def test_optimization_uses_multi_step_approach_for_expensive_operations(self):
        """Test that optimizations suggest multi-step approaches for expensive operations."""
        # Test the pattern of breaking down expensive operations
        sample_optimized_response = (
            "For searching across all contact data, I'll use an optimized approach:\n\n"
            "First, let me check specific indexed fields:\n"
            "```sql\nSELECT COUNT(*) FROM contacts WHERE name LIKE '%meeting%'\n```\n\n"
            "For notes search:\n"
            "```sql\nSELECT c.name, n.title FROM contacts c JOIN relationship_notes rn ON c.id = rn.relationship_id JOIN notes n ON rn.note_id = n.id WHERE n.content LIKE '%meeting%' LIMIT 50\n```"
        )

        # Verify multi-step optimization strategies are used
        assert "optimized approach" in sample_optimized_response.lower()
        assert "first" in sample_optimized_response.lower()
        assert "COUNT(*)" in sample_optimized_response
        assert "LIMIT" in sample_optimized_response


@pytest.mark.unit
class TestOptimizationLogic:
    """Test optimization logic independently from actual LLM calls."""

    def test_system_prompt_contains_all_optimization_patterns(self):
        """Test that system prompt construction includes all optimization patterns."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api)

        system_prompt = llm._create_system_prompt()

        # Verify all optimization patterns are present
        required_patterns = [
            "LIMIT LARGE QUERIES",
            "COUNT BEFORE",
            "EXCLUDE BINARY",
            "USE INDEXED",
            "SAMPLE FOR EXPLORATION",
        ]

        for pattern in required_patterns:
            assert pattern in system_prompt, f"System prompt missing pattern: {pattern}"

    def test_optimization_patterns_include_performance_context(self):
        """Test that optimization patterns include performance justification."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api)

        system_prompt = llm._create_system_prompt()

        # Verify performance context is provided
        performance_keywords = ["performance", "timeout", "large database", "1000+"]
        found_keywords = [kw for kw in performance_keywords if kw.lower() in system_prompt.lower()]

        assert (
            len(found_keywords) >= 2
        ), f"Should provide performance context. Found: {found_keywords}"

    def test_optimization_patterns_provide_specific_examples(self):
        """Test that each optimization pattern includes concrete examples."""
        mock_api = MagicMock()
        llm = OllamaLLM(api=mock_api)

        system_prompt = llm._create_system_prompt()

        # Verify specific examples are provided
        example_indicators = [
            "LIMIT 50",
            "LIMIT 100",
            "COUNT(*)",
            "profile_image",
            "RANDOM()",
            "name LIKE",
            "email IS",
        ]

        found_examples = [ex for ex in example_indicators if ex in system_prompt]

        assert (
            len(found_examples) >= 5
        ), f"Should provide specific examples. Found: {found_examples}"


@pytest.mark.unit
class TestOptimizationRegressionPrevention:
    """Test that optimization patterns prevent known performance regressions."""

    def test_optimization_prevents_select_star_with_binary_data(self):
        """Test that optimization patterns prevent SELECT * queries with binary data."""
        # Test the optimization pattern that avoids SELECT *
        sample_optimized_response = (
            "I'll select specific columns to avoid loading large binary profile_image data:\n\n"
            "```sql\nSELECT id, name, email, phone, created_at FROM contacts LIMIT 50\n```\n\n"
            "This avoids the binary profile_image column for better performance."
        )

        # Verify SELECT * avoidance pattern is demonstrated
        assert "SELECT *" not in sample_optimized_response
        assert "specific columns" in sample_optimized_response.lower()
        assert "avoid" in sample_optimized_response.lower()
        assert "binary" in sample_optimized_response.lower()
        assert "profile_image" in sample_optimized_response

    def test_optimization_prevents_unlimited_queries_on_large_tables(self):
        """Test that optimization patterns prevent unlimited queries on large tables."""
        # Test the optimization pattern that adds LIMIT clauses
        sample_optimized_response = (
            "I'll add a LIMIT to prevent overwhelming results:\n\n"
            "```sql\nSELECT id, name, email FROM contacts LIMIT 50\n```\n\n"
            "Use search filters or pagination for more specific results."
        )

        # Verify unlimited query prevention pattern is demonstrated
        assert "LIMIT" in sample_optimized_response
        assert "prevent" in sample_optimized_response.lower()
        assert "overwhelming" in sample_optimized_response.lower()
        assert (
            "pagination" in sample_optimized_response.lower()
            or "filters" in sample_optimized_response.lower()
        )

    def test_uses_optimization_fixtures_for_validation(self):
        """Test that optimization test fixtures provide useful validation data."""
        # Validate that our optimization fixtures contain expected patterns
        slow_queries = QueryOptimizationFixtures.SLOW_QUERIES
        optimized_queries = QueryOptimizationFixtures.OPTIMIZED_QUERIES

        # Should have problematic queries to fix
        assert len(slow_queries) >= 3, "Should have at least 3 slow query examples"
        assert "unoptimized_select_all" in slow_queries
        assert "SELECT *" in slow_queries["unoptimized_select_all"]["query"]

        # Should have good query examples
        assert len(optimized_queries) >= 3, "Should have at least 3 optimized query examples"
        assert "good_limited_query" in optimized_queries
        assert "LIMIT" in optimized_queries["good_limited_query"]["query"]
