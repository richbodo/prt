# Bug: LLM Query Optimization Test Reliability and Functional Validation

## Bug Description
The test suite `tests/test_llm_query_optimization_prompts.py` was failing due to brittle string matching and lacks functional validation of the SQL optimization patterns. While the tests are currently passing after recent fixes, the testing strategy needs improvement to ensure reliability and relevance. The tests only validate that optimization text exists in the system prompt but don't verify that the LLM actually follows these optimization patterns when generating SQL queries.

## Problem Statement
1. **Brittle String Matching**: Tests rely on exact string matches that break when formatting changes (e.g., "SQL QUERY OPTIMIZATION PATTERNS" vs "## SQL QUERY OPTIMIZATION PATTERNS")
2. **No Functional Testing**: Tests only check prompt content existence, not actual LLM behavior
3. **Limited Test Coverage**: No validation that optimization patterns actually improve query performance
4. **Maintenance Burden**: String-based tests require updates whenever prompt formatting changes

## Solution Statement
Implement a robust, multi-layered testing strategy that includes:
1. **Flexible Content Validation**: Use regex/semantic matching instead of exact strings
2. **Functional Integration Tests**: Validate that LLM generates optimized queries
3. **Performance Regression Tests**: Ensure optimization patterns prevent known slow queries
4. **Mock-based Unit Tests**: Test optimization logic independently from LLM calls

## Steps to Reproduce
1. Run `./prt_env/bin/pytest tests/test_llm_query_optimization_prompts.py -v`
2. Tests now pass, but previously failed due to formatting changes
3. No functional testing exists to validate actual query optimization behavior

## Root Cause Analysis
1. **String Brittleness**: Tests used exact string matching like `assert "SQL QUERY OPTIMIZATION PATTERNS" in system_prompt` which broke when headers were changed to include markdown formatting `## SQL QUERY OPTIMIZATION PATTERNS`
2. **Missing Functional Layer**: Tests validate prompt content but don't test if the LLM actually generates optimized queries
3. **No Performance Validation**: No tests verify that the optimization patterns actually prevent performance issues
4. **Inadequate Test Design**: Tests focus on implementation details (prompt text) rather than behavior outcomes

## Relevant Files
Use these files to fix the bug:

- `tests/test_llm_query_optimization_prompts.py` - Current test suite that needs reliability improvements
- `prt_src/llm_ollama.py` - Contains `_create_system_prompt()` method with optimization patterns
- `prt_src/schema_info.py` - Database schema information used in prompts
- `tests/integration/test_llm_phase4_tools.py` - Integration tests for LLM tool calling (for functional test patterns)
- `tests/mocks/mock_llm_service.py` - Mock LLM for testing optimization logic

### New Files
- `tests/test_llm_query_optimization_functional.py` - New functional tests for optimization behavior
- `tests/fixtures/optimization_test_queries.py` - Test query fixtures for optimization validation

## Step by Step Tasks

### Step 1: Make String-Based Tests More Robust
- Replace exact string matching with regex patterns that are formatting-agnostic
- Use semantic validation that checks for key concepts rather than exact text
- Add test documentation explaining what each assertion validates

### Step 2: Create Functional Optimization Tests
- Add integration tests that validate LLM generates optimized SQL
- Test scenarios: large result sets, binary data exclusion, indexed column usage
- Use mock database with performance characteristics to validate optimization impact

### Step 3: Add Performance Regression Tests
- Create test fixtures with known slow queries and their optimized equivalents
- Validate that optimization patterns prevent generation of problematic queries
- Add timing-based tests to ensure optimization patterns improve query performance

### Step 4: Implement Mock-Based Unit Tests
- Test optimization logic independently from actual LLM calls
- Validate prompt construction includes all required optimization patterns
- Test edge cases and error handling in optimization guidance

### Step 5: Update Test Documentation and Strategy
- Document the multi-layered testing approach in test files
- Add clear comments explaining what each test validates
- Create testing guidelines for future optimization pattern additions

### Step 6: Add Continuous Integration Validation
- Ensure functional tests run in CI pipeline
- Add performance benchmarks to catch optimization regressions
- Include test reliability checks in pull request validation

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `./prt_env/bin/pytest tests/test_llm_query_optimization_prompts.py -v` - Verify original tests still pass
- `./prt_env/bin/pytest tests/test_llm_query_optimization_functional.py -v` - Run new functional tests
- `./prt_env/bin/pytest -m integration tests/` - Ensure integration tests pass
- `./prt_env/bin/pytest tests/ -k "optimization" -v` - Run all optimization-related tests
- `./prt_env/bin/ruff check tests/test_llm_query_optimization* --fix` - Lint new test files
- `./prt_env/bin/black tests/test_llm_query_optimization*` - Format new test files

## Notes
- **Current Status**: Tests are passing after recent formatting fixes, but reliability issues remain
- **Priority**: Focus on functional testing over string matching - behavior matters more than prompt text
- **Performance**: Use realistic test data volumes (1000+ contacts) to validate optimization effectiveness
- **Maintenance**: New testing approach should be resilient to prompt formatting changes
- **Documentation**: Include clear examples of what constitutes "optimized" vs "unoptimized" queries in test comments