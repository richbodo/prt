"""Test fixtures for optimization testing."""

# This module provides fixtures specifically for optimization testing
# The main test fixtures are in tests/fixtures.py (not this directory)

from .optimization_test_queries import QueryOptimizationFixtures
from .optimization_test_queries import get_optimization_patterns
from .optimization_test_queries import get_optimized_query_examples
from .optimization_test_queries import get_slow_query_examples

__all__ = [
    "QueryOptimizationFixtures",
    "get_slow_query_examples",
    "get_optimized_query_examples",
    "get_optimization_patterns",
]
