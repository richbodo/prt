# Bug: LLM Contacts with Images Test Reliability Issues

## Bug Description
The test `tests/test_llm_contacts_with_images_workflow.py::test_get_contacts_with_images_tool` has been failing intermittently. While the test appears to be passing currently, there are fundamental design issues that make these tests unreliable and not representative of real LLM behavior. The tests need to be refactored to be more reliable, relevant, and better aligned with actual LLM usage patterns.

Key symptoms observed:
- Tests sometimes fail due to LLM availability or response variability
- Test design assumes deterministic LLM responses which is unrealistic
- Tests don't properly validate the most likely LLM response patterns
- Missing proper mocking for consistent test behavior
- Long execution times (81+ seconds for the full suite) indicating inefficiency

## Problem Statement
The LLM contacts with images workflow tests are designed with unrealistic expectations about LLM behavior and lack proper isolation from external dependencies (Ollama), making them flaky and unreliable for CI/CD pipelines.

## Solution Statement
Redesign the test suite to use proper mocking for LLM interactions, create more realistic test scenarios that account for LLM response variability, and separate integration tests from unit tests for better reliability and faster execution.

## Steps to Reproduce
```bash
# Run the failing test multiple times to observe inconsistency
./prt_env/bin/pytest tests/test_llm_contacts_with_images_workflow.py::test_get_contacts_with_images_tool -v
# Sometimes passes, sometimes fails depending on Ollama availability and LLM model state
```

## Root Cause Analysis

### Primary Issues:

1. **LLM Response Unpredictability**: Tests assume LLM will respond deterministically, but LLMs are inherently non-deterministic and may respond conversationally rather than executing tools immediately.

2. **External Dependency Coupling**: Tests depend on Ollama being available and properly configured with models, making them fragile in CI environments.

3. **Insufficient Mocking**: Tests directly call real LLM services instead of mocking responses for consistent behavior.

4. **Unrealistic Expectations**: Tests expect specific tool calling behavior that may not represent how LLMs actually respond to prompts in practice.

5. **Poor Test Design**: Unit tests mixed with integration tests, and missing proper test categories.

### Technical Analysis:

From the system prompt analysis (lines 881-1140 in `prt_src/llm_ollama.py`), the LLM is instructed to:
- Be conversational and helpful
- Ask for clarification when needed
- Only generate directories when explicitly requested by users
- Explain what tools it will use before executing them

This means the most likely LLM responses to "create a directory of contacts with images" would be:
1. **Conversational confirmation**: "I can help you create a directory of contacts with images. Let me first get all contacts that have profile images and then create the directory for you."
2. **Tool execution with explanation**: Actually calling the tools but explaining what it's doing
3. **Clarification questions**: "Would you like me to create a directory showing all your contacts that have profile images?"

The current tests don't account for this realistic LLM behavior.

## Relevant Files
Use these files to fix the bug:

- `tests/test_llm_contacts_with_images_workflow.py` - Main test file that needs refactoring for reliability
- `tests/mocks/timeout_utils.py` - Contains utilities for checking Ollama availability that should be enhanced
- `prt_src/llm_ollama.py` - Contains the LLM system prompt and tool definitions that inform expected behavior
- `tests/fixtures.py` - Contains test data setup with profile image fixtures that tests depend on
- `prt_src/api.py` - Contains the `get_contacts_with_images()` method that's being tested

### New Files
- `tests/unit/test_llm_contacts_with_images_mocked.py` - New unit tests with proper mocking
- `tests/integration/test_llm_contacts_with_images_integration.py` - Separate integration tests for real LLM behavior

## Step by Step Tasks

### Step 1: Create Mocked Unit Tests
- Create `tests/unit/test_llm_contacts_with_images_mocked.py` with comprehensive unit tests
- Mock the LLM responses to test different scenarios (conversational, tool execution, errors)
- Test the `_get_contacts_with_images()` method behavior with various response types
- Ensure fast execution (< 1 second per test)
- Cover edge cases like empty responses, malformed data, etc.

### Step 2: Enhance Integration Test Reliability
- Refactor existing integration tests to be more resilient to LLM response variability
- Add proper skip conditions for when Ollama is unavailable
- Implement timeout handling for long-running LLM requests
- Add response validation that accounts for conversational vs tool-execution responses
- Separate fast integration tests from slow end-to-end tests

### Step 3: Improve Test Data and Fixtures
- Ensure fixture data consistently includes contacts with profile images
- Add validation that test fixtures contain expected image data
- Create helper functions to verify image data integrity in tests
- Document expected fixture state for profile images

### Step 4: Add Response Pattern Validation
- Create test cases for the most likely LLM response patterns based on the system prompt
- Test conversational responses that ask for clarification
- Test tool execution responses with explanations
- Test error handling when LLM provides unexpected responses

### Step 5: Performance and Reliability Improvements
- Set appropriate timeouts for all LLM-dependent tests
- Add circuit breaker patterns for flaky external dependencies
- Implement proper test categorization (@pytest.mark.unit vs @pytest.mark.integration)
- Add performance assertions to prevent regression in test execution time

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

```bash
# Run new unit tests - should be fast and always pass
./prt_env/bin/pytest tests/unit/test_llm_contacts_with_images_mocked.py -v

# Run integration tests - should handle Ollama unavailability gracefully
./prt_env/bin/pytest tests/integration/test_llm_contacts_with_images_integration.py -v

# Run original test file to ensure it still works
./prt_env/bin/pytest tests/test_llm_contacts_with_images_workflow.py -v

# Run unit tests only - should complete quickly
./prt_env/bin/pytest -m unit tests/ -v

# Run integration tests - should handle external dependencies properly
./prt_env/bin/pytest -m integration tests/ -v

# Run all tests to ensure no regressions
./prt_env/bin/pytest tests/ -v

# Performance validation - unit tests should be fast
time ./prt_env/bin/pytest -m unit tests/unit/test_llm_contacts_with_images_mocked.py -v
```

## Notes
- The fundamental issue is that the original tests assumed deterministic LLM behavior, which is unrealistic
- Real LLMs are conversational and non-deterministic by design
- Proper test design should mock LLM responses for unit tests and accept response variability for integration tests
- The system prompt analysis reveals that the LLM is designed to be helpful and ask for clarification, which should be reflected in test expectations
- Performance improvements are critical - unit tests should run in milliseconds, not seconds
- Integration tests should gracefully handle external service unavailability rather than failing hard