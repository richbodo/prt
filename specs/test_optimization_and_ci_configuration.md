# Feature: Test Optimization and CI/CD Configuration

## Feature Description
Implement a comprehensive test optimization and CI/CD configuration system for the PRT project to ensure fast, reliable automated testing in both local development and continuous integration environments. This feature will establish two-tier CI pipelines, fix current test failures, and provide clear developer tools for running tests efficiently.

## User Story
As a developer working on PRT
I want a fast, reliable CI/CD test system with clear local testing tools
So that I can get quick feedback on my changes, deploy with confidence, and maintain high code quality without waiting for slow test suites

## Problem Statement
The current PRT test suite has 889 tests with good categorization but several critical issues prevent reliable CI/CD adoption:
- Integration tests have mock configuration failures causing CI unreliability
- Some tests marked as "integration" actually require external LLM services (30+ second execution)
- No CI/CD workflows exist, preventing automated quality gates
- Developers lack clear guidance on which tests to run locally vs in CI
- Test failures in multiple categories block adoption of automated testing

## Solution Statement
Implement a two-tier CI/CD strategy with fast deterministic tests (unit + mocked integration) for rapid feedback and comprehensive tests (including LLM contract tests) for nightly validation. Fix all current test failures, establish proper test categorization, and provide developer tools for efficient local testing.

## Relevant Files
Use these files to implement the feature:

- `tests/integration/test_llm_network_validation.py` - Contains network validation test with mock setup failure (needs mock.content attribute fix)
- `tests/e2e/test_setup_workflow.py` - Contains E2E test with assertion failure (needs error message handling fix)
- `tests/test_contacts_with_images_performance.py` - Contains performance test with path handling failure
- `tests/integration/test_llm_one_query.py` - Contract test incorrectly marked as integration (requires real LLM)
- `pytest.ini` - Test configuration with excellent marker system (needs CI-specific enhancements)
- `docs/TESTING_STRATEGY.md` - Comprehensive testing strategy documentation (reference for maintaining standards)
- `.pre-commit-config.yaml` - Pre-commit hooks configuration (needs test runner integration)

### New Files
- `.github/workflows/fast-tests.yml` - Fast CI pipeline for unit + integration tests with mocks
- `.github/workflows/comprehensive-tests.yml` - Comprehensive nightly CI pipeline including contract tests
- `scripts/run-ci-tests.sh` - Developer script to run CI-appropriate tests locally
- `scripts/run-local-tests.sh` - Developer script to run full test suite when LLM available
- `docs/RUNNING_TESTS.md` - Clear documentation for test execution patterns

## Implementation Plan

### Phase 1: Foundation
Fix all current test failures to establish a clean baseline for CI implementation. This includes correcting mock configurations, assertion logic, and path handling issues that currently prevent reliable test execution.

### Phase 2: Core Implementation
Implement the two-tier CI/CD pipeline system with fast tests for immediate feedback and comprehensive tests for thorough validation. Create developer tools and scripts for efficient local testing.

### Phase 3: Integration
Integrate the new CI/CD system with existing development workflows, update documentation, and establish clear patterns for future test development.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Fix Network Validation Test Mock Configuration
- Edit `tests/integration/test_llm_network_validation.py`
- Fix mock setup in `test_validate_response_valid_json` method
- Add missing `mock_response.content = b'{"test": "data"}'` attribute
- Add missing `len()` method support for mock content
- Run test to verify fix: `./prt_env/bin/pytest tests/integration/test_llm_network_validation.py::TestLLMNetworkValidation::test_validate_response_valid_json -v`

### Step 2: Fix E2E Test Assertion Logic
- Edit `tests/e2e/test_setup_workflow.py`
- Investigate `test_fixture_load_failure_shows_error` assertion failure
- Update test to match actual error message format or fix error message generation
- Ensure error text contains expected failure indicators
- Run test to verify fix: `./prt_env/bin/pytest tests/e2e/test_setup_workflow.py::TestSetupWorkflowErrorHandling::test_fixture_load_failure_shows_error -v`

### Step 3: Fix Performance Test Path Handling
- Edit `tests/test_contacts_with_images_performance.py`
- Fix `test_tool_chain_performance` path handling issue
- Ensure directory tool receives proper path object instead of None
- Add proper error handling for path creation
- Run test to verify fix: `./prt_env/bin/pytest tests/test_contacts_with_images_performance.py::test_tool_chain_performance -v`

### Step 4: Create Developer Test Scripts
- Create `scripts/` directory if it doesn't exist
- Create `scripts/run-ci-tests.sh` with executable permissions for fast CI-appropriate tests
- Create `scripts/run-local-tests.sh` with executable permissions for full local test suite
- Include Ollama availability detection in local script
- Test both scripts to ensure proper execution

### Step 5: Create Fast CI Pipeline Configuration
- Create `.github/workflows/` directory
- Create `.github/workflows/fast-tests.yml` with Ubuntu runner
- Configure Python 3.11 setup and dependency installation
- Set up unit + integration test execution with proper timeout (30s)
- Add code coverage reporting
- Set execution timeout to 5 minutes total

### Step 6: Create Comprehensive CI Pipeline Configuration
- Create `.github/workflows/comprehensive-tests.yml` for nightly/release testing
- Configure Ollama installation and model setup for contract tests
- Set up full test suite execution with longer timeouts (600s for contract tests)
- Configure to run on schedule (daily 2 AM), manual trigger, and releases
- Set execution timeout to 20 minutes total

### Step 7: Enhance pytest Configuration
- Edit `pytest.ini` to add CI-specific marker combinations
- Add `ci_fast` and `ci_comprehensive` markers for test selection
- Ensure strict marker enforcement
- Update timeout configurations for different test categories

### Step 8: Create Test Documentation
- Create `docs/RUNNING_TESTS.md` with clear test execution patterns
- Document CI vs local testing differences
- Include quick command reference for developers
- Add troubleshooting section for common test issues

### Step 9: Update Pre-commit Hooks
- Edit `.pre-commit-config.yaml` to integrate fast test execution
- Add pre-push hook to run fast test suite
- Configure to prevent push if fast tests fail
- Ensure hook uses new test scripts

### Step 10: Validate Complete Implementation
- Run all validation commands to ensure zero regressions
- Test both CI scripts locally
- Verify all previously failing tests now pass
- Confirm test categorization is correct

## Testing Strategy

### Unit Tests
- Fix existing unit test suite (113 tests) to maintain < 1 second total execution time
- Ensure unit tests cover pure functions, formatters, parsers, and utilities without external dependencies
- Verify unit tests use proper mocking for any external service calls

### Integration Tests
- Fix integration test suite (211 tests) to execute reliably with mocked external dependencies
- Ensure integration tests cover component interactions, workflows, and screen navigation
- Validate MockLLMService usage for deterministic LLM behavior testing
- Maintain < 5 seconds total execution time for CI reliability

### Edge Cases
- Database connection failures during test execution
- Mock service unavailability scenarios
- Network timeout conditions in validation tests
- Path handling edge cases for file operations
- LLM service unavailable during contract test execution
- Large response handling in network validation tests

## Acceptance Criteria

- [ ] All 889 tests categorized correctly with appropriate pytest markers
- [ ] Fast CI pipeline executes unit + integration tests in < 2 minutes with 99%+ reliability
- [ ] Comprehensive CI pipeline executes all tests in < 15 minutes including LLM contract tests
- [ ] Zero external dependencies required for fast CI pipeline (all mocked)
- [ ] Developer scripts provide clear local testing options based on LLM availability
- [ ] All current test failures fixed with proper mock configurations and assertions
- [ ] Pre-commit hooks integrate fast test execution to prevent broken commits
- [ ] Documentation clearly explains CI vs local testing patterns
- [ ] Test coverage maintained at current levels while improving execution speed
- [ ] CI/CD workflows automatically triggered on appropriate events (PR, push, release, schedule)

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `./prt_env/bin/pytest -m unit --tb=short` - Validate all unit tests pass in < 1 second
- `./prt_env/bin/pytest -m integration --tb=short` - Validate all integration tests pass in < 5 seconds
- `./prt_env/bin/pytest tests/integration/test_llm_network_validation.py::TestLLMNetworkValidation::test_validate_response_valid_json -v` - Verify network validation fix
- `./prt_env/bin/pytest tests/e2e/test_setup_workflow.py::TestSetupWorkflowErrorHandling::test_fixture_load_failure_shows_error -v` - Verify E2E test fix
- `./prt_env/bin/pytest tests/test_contacts_with_images_performance.py::test_tool_chain_performance -v` - Verify performance test fix
- `scripts/run-ci-tests.sh` - Validate fast CI script executes successfully in < 2 minutes
- `scripts/run-local-tests.sh` - Validate local test script handles LLM availability correctly
- `./prt_env/bin/pytest --collect-only -q | wc -l` - Verify total test count remains 889
- `./prt_env/bin/pytest -m "unit or integration" --timeout=120 --tb=short` - Verify CI-appropriate tests complete within timeout
- `./prt_env/bin/pytest --markers` - Verify all test markers are properly defined and documented

## Notes

- The existing test infrastructure is excellent with proper categorization already in place
- MockLLMService provides deterministic LLM testing capabilities avoiding network dependencies
- GitHub Actions workflows should use Python 3.11 to match local development environment
- Contract tests requiring real LLM services should only run in comprehensive pipeline, not fast CI
- Test scripts should detect Ollama availability to gracefully handle local development scenarios
- Consider adding test execution time monitoring to catch tests that exceed category time limits
- The two-tier CI approach balances fast feedback (fast pipeline) with comprehensive validation (nightly pipeline)
- Pre-commit hooks should run fast tests only on pre-push, not pre-commit to avoid slowing development
- Future test additions should follow established patterns and use appropriate markers for proper CI execution