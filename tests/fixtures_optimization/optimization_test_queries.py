"""
Test query fixtures for optimization validation.

This module provides test queries and their expected optimized equivalents
for validating LLM query optimization behavior.
"""


class QueryOptimizationFixtures:
    """Test fixtures for query optimization validation."""

    # Known problematic queries and their optimized equivalents
    SLOW_QUERIES = {
        "unoptimized_select_all": {
            "query": "SELECT * FROM contacts",
            "problems": ["No LIMIT", "Includes binary data", "Potentially large result set"],
            "optimized": "SELECT id, name, email, phone FROM contacts LIMIT 50",
            "optimizations_applied": [
                "Added LIMIT",
                "Excluded binary profile_image",
                "Selected specific columns",
            ],
        },
        "unoptimized_binary_search": {
            "query": "SELECT * FROM contacts WHERE profile_image IS NOT NULL",
            "problems": ["Loads binary data unnecessarily", "No LIMIT", "SELECT *"],
            "optimized": "SELECT id, name, email FROM contacts WHERE profile_image IS NOT NULL LIMIT 50",
            "optimizations_applied": [
                "Excluded binary data",
                "Added LIMIT",
                "Selected specific columns",
            ],
        },
        "unoptimized_large_scan": {
            "query": "SELECT name, email FROM contacts WHERE phone LIKE '%555%'",
            "problems": [
                "Non-indexed column search",
                "No LIMIT",
                "Potentially slow LIKE operation",
            ],
            "optimized": "SELECT name, email FROM contacts WHERE phone LIKE '%555%' LIMIT 100",
            "optimizations_applied": ["Added LIMIT", "Limited result set"],
        },
        "unoptimized_no_count": {
            "query": "SELECT * FROM contacts WHERE created_at > '2023-01-01'",
            "problems": ["No result size estimation", "Includes binary data", "No LIMIT"],
            "optimized_steps": [
                "SELECT COUNT(*) FROM contacts WHERE created_at > '2023-01-01'",
                "SELECT id, name, email, created_at FROM contacts WHERE created_at > '2023-01-01' LIMIT 50",
            ],
            "optimizations_applied": ["Added COUNT step", "Excluded binary data", "Added LIMIT"],
        },
    }

    # Good query examples that demonstrate optimization patterns
    OPTIMIZED_QUERIES = {
        "good_limited_query": {
            "query": "SELECT id, name, email FROM contacts LIMIT 50",
            "optimizations": ["Uses LIMIT", "Excludes binary data", "Specific columns"],
            "performance_characteristics": [
                "Fast",
                "Bounded result set",
                "Predictable memory usage",
            ],
        },
        "good_indexed_search": {
            "query": "SELECT id, name, email FROM contacts WHERE name LIKE 'John%' LIMIT 50",
            "optimizations": ["Uses indexed column", "Efficient LIKE pattern", "Limited results"],
            "performance_characteristics": [
                "Fast indexed lookup",
                "Bounded results",
                "Prefix search optimization",
            ],
        },
        "good_count_then_select": {
            "query_steps": [
                "SELECT COUNT(*) FROM contacts WHERE profile_image IS NOT NULL",
                "SELECT id, name, email FROM contacts WHERE profile_image IS NOT NULL LIMIT 20",
            ],
            "optimizations": [
                "Two-step approach",
                "Result size estimation",
                "Excludes binary data",
            ],
            "performance_characteristics": [
                "Size-aware querying",
                "Prevents large result sets",
                "Fast execution",
            ],
        },
        "good_sampling_query": {
            "query": "SELECT id, name, email FROM contacts ORDER BY RANDOM() LIMIT 20",
            "optimizations": ["Uses sampling", "Limited result set", "Excludes binary data"],
            "performance_characteristics": [
                "Good for exploration",
                "Bounded execution time",
                "Representative sample",
            ],
        },
        "good_binary_exclusion": {
            "query": "SELECT id, name, email, phone, created_at FROM contacts WHERE profile_image IS NOT NULL LIMIT 50",
            "optimizations": [
                "Excludes profile_image column",
                "Uses indexed condition",
                "Limited results",
            ],
            "performance_characteristics": [
                "Avoids large binary transfer",
                "Fast condition check",
                "Memory efficient",
            ],
        },
    }

    # Test scenarios for different optimization patterns
    TEST_SCENARIOS = {
        "large_result_set": {
            "user_request": "Show me all contacts",
            "expected_optimizations": ["LIMIT clause", "Specific columns", "Binary exclusion"],
            "warning_indicators": ["overwhelming", "large result", "first N"],
            "performance_target": "< 1 second execution",
        },
        "binary_data_request": {
            "user_request": "List contacts with profile images",
            "expected_optimizations": ["Exclude profile_image column", "LIMIT clause"],
            "explanation_required": ["binary data exclusion", "performance reasons"],
            "performance_target": "< 500ms execution",
        },
        "exploration_request": {
            "user_request": "Show me some random contacts to explore the data",
            "expected_optimizations": ["RANDOM() sampling", "LIMIT clause"],
            "explanation_required": ["sampling approach", "exploration purpose"],
            "performance_target": "< 200ms execution",
        },
        "search_request": {
            "user_request": "Find contacts named John",
            "expected_optimizations": [
                "Indexed column usage",
                "Efficient LIKE pattern",
                "LIMIT clause",
            ],
            "explanation_required": ["indexed search", "performance benefit"],
            "performance_target": "< 100ms execution",
        },
        "large_data_check": {
            "user_request": "How many contacts have images and show me some examples",
            "expected_optimizations": [
                "COUNT before SELECT",
                "Two-step approach",
                "Binary exclusion",
            ],
            "explanation_required": ["result size estimation", "efficient approach"],
            "performance_target": "< 300ms total execution",
        },
    }

    # Performance regression test cases
    REGRESSION_TESTS = {
        "prevent_select_star": {
            "anti_pattern": "SELECT * FROM contacts",
            "should_detect": ["binary data inclusion", "unbounded results"],
            "should_suggest": ["specific columns", "LIMIT clause"],
            "performance_issue": "Large memory usage from binary data",
        },
        "prevent_unlimited_large_tables": {
            "anti_pattern": "SELECT name, email FROM contacts",
            "should_detect": ["no result limiting", "potentially large result set"],
            "should_suggest": ["LIMIT clause", "pagination approach"],
            "performance_issue": "Overwhelming result sets",
        },
        "prevent_non_indexed_scans": {
            "anti_pattern": "SELECT * FROM contacts WHERE phone LIKE '%555%'",
            "should_detect": ["non-indexed column", "wildcard search", "binary data"],
            "should_suggest": [
                "indexed columns where possible",
                "LIMIT clause",
                "specific columns",
            ],
            "performance_issue": "Full table scan with pattern matching",
        },
        "prevent_no_size_estimation": {
            "anti_pattern": "Direct large SELECT without COUNT",
            "should_detect": ["no result size estimation"],
            "should_suggest": ["COUNT(*) first", "two-step approach"],
            "performance_issue": "Unexpected large result sets",
        },
    }

    @classmethod
    def get_optimization_test_cases(cls) -> list[dict]:
        """Get all optimization test cases for validation."""
        test_cases = []

        # Add slow query fixes
        for query_id, query_data in cls.SLOW_QUERIES.items():
            test_cases.append(
                {
                    "type": "slow_query_fix",
                    "id": query_id,
                    "original": query_data["query"],
                    "problems": query_data["problems"],
                    "optimized": query_data.get("optimized", query_data.get("optimized_steps")),
                    "optimizations": query_data["optimizations_applied"],
                }
            )

        # Add good query examples
        for query_id, query_data in cls.OPTIMIZED_QUERIES.items():
            test_cases.append(
                {
                    "type": "good_query_example",
                    "id": query_id,
                    "query": query_data.get("query", query_data.get("query_steps")),
                    "optimizations": query_data["optimizations"],
                    "performance": query_data["performance_characteristics"],
                }
            )

        return test_cases

    @classmethod
    def get_performance_scenarios(cls) -> list[dict]:
        """Get performance test scenarios."""
        scenarios = []

        for scenario_id, scenario_data in cls.TEST_SCENARIOS.items():
            scenarios.append(
                {
                    "id": scenario_id,
                    "user_request": scenario_data["user_request"],
                    "expected_optimizations": scenario_data["expected_optimizations"],
                    "required_explanations": scenario_data.get("explanation_required", []),
                    "performance_target": scenario_data["performance_target"],
                    "warning_indicators": scenario_data.get("warning_indicators", []),
                }
            )

        return scenarios

    @classmethod
    def get_regression_tests(cls) -> list[dict]:
        """Get regression test cases."""
        regressions = []

        for regression_id, regression_data in cls.REGRESSION_TESTS.items():
            regressions.append(
                {
                    "id": regression_id,
                    "anti_pattern": regression_data["anti_pattern"],
                    "should_detect": regression_data["should_detect"],
                    "should_suggest": regression_data["should_suggest"],
                    "performance_issue": regression_data["performance_issue"],
                }
            )

        return regressions


# Convenience functions for test usage
def get_slow_query_examples() -> dict[str, str]:
    """Get examples of slow queries for testing."""
    return {
        query_id: data["query"] for query_id, data in QueryOptimizationFixtures.SLOW_QUERIES.items()
    }


def get_optimized_query_examples() -> dict[str, str]:
    """Get examples of optimized queries for testing."""
    return {
        query_id: data.get("query", data.get("query_steps", [""])[0])
        for query_id, data in QueryOptimizationFixtures.OPTIMIZED_QUERIES.items()
    }


def get_optimization_patterns() -> list[str]:
    """Get list of optimization patterns that should be applied."""
    return [
        "LIMIT clause addition",
        "Binary data exclusion",
        "Specific column selection",
        "Indexed column usage",
        "COUNT before SELECT",
        "RANDOM() sampling",
        "Two-step approach",
        "Result size estimation",
    ]
