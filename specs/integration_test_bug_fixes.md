# Integration Test Bug Fixes - Plan 1

## Overview
This plan addresses 7 critical bugs in integration tests that are causing failures and violating timing contracts. These bugs prevent reliable CI/CD execution and mask real issues.

## Problem Analysis

### Current State
- **7 test failures** out of 74 integration tests
- **Timing violations**: Tests marked `@pytest.mark.integration` (< 5s limit) taking 6-11+ seconds
- **Method signature mismatches**: Tests calling async methods synchronously
- **Mock setup errors**: Incorrect parameter passing in test mocks

### Impact
- CI/CD unreliability due to flaky tests
- False negatives hiding real LLM issues
- Slow feedback loop for developers
- Reduced confidence in test suite

## Detailed Bug Analysis & Fixes

### 🐛 **Bug 1 & 2: Async/Await Issues**
**Files**: `tests/integration/test_llm_network_validation.py`
**Failing Tests**:
- `test_health_check_with_validation`
- `test_health_check_validation_fails`

**Root Cause**:
```python
# Current (WRONG):
result = self.llm.health_check()  # Calling async method synchronously
assert result is True  # Gets coroutine object, not boolean

# Method signature:
async def health_check(self, timeout: float = 2.0) -> bool:
```

**Fix Strategy**:
```python
# Fixed:
@pytest.mark.asyncio
async def test_health_check_with_validation(self):
    result = await self.llm.health_check()
    assert result is True
```

**Implementation Steps**:
1. Add `@pytest.mark.asyncio` decorator to both test methods
2. Add `async` keyword to test function definitions
3. Add `await` keyword before `self.llm.health_check()` calls
4. Verify mock patching still works with async context

**Acceptance Criteria**:
- Both tests pass without coroutine warnings
- Tests complete in < 1s (no real network calls)
- Mock assertions still validate correctly

---

### 🐛 **Bug 3 & 4: Method Signature Mismatches**
**Files**: `tests/integration/test_llm_network_validation.py`
**Failing Tests**:
- `test_preload_model_with_validation`
- `test_preload_model_validation_fails`

**Root Cause**:
```python
# Current (WRONG):
result = self.llm.preload_model("test-model")  # Extra parameter

# Method signature:
async def preload_model(self) -> bool:  # Takes no model parameter
```

**Fix Strategy**:
```python
# Fixed:
@pytest.mark.asyncio
async def test_preload_model_with_validation(self):
    result = await self.llm.preload_model()  # No model parameter
    assert result is True
```

**Implementation Steps**:
1. Remove model parameter from `preload_model()` calls
2. Add `@pytest.mark.asyncio` and `async/await` patterns
3. Update mock expectations to match correct signature
4. Verify model name comes from LLM instance config, not parameter

**Acceptance Criteria**:
- Tests call `preload_model()` with correct signature (no parameters)
- Async execution works properly with mocks
- Mock validation confirms correct API usage

---

### 🐛 **Bug 5: Chat Method Signature Mismatch**
**Files**: `tests/integration/test_llm_network_validation.py`
**Failing Test**: `test_chat_with_validation`

**Root Cause**:
```python
# Current (WRONG):
response = self.llm.chat(messages, "test-model")  # Wrong signature

# Method signature:
def chat(self, message: str) -> str:  # Takes single string message
```

**Fix Strategy**:
```python
# Fixed:
response = self.llm.chat("Hello")  # Single string message
```

**Implementation Steps**:
1. Change `chat()` call to use single string message parameter
2. Remove model parameter (model comes from LLM instance config)
3. Update test expectations to match string response format
4. Verify mock setup returns string, not dict

**Acceptance Criteria**:
- Test calls `chat()` with correct signature (single string)
- Mock returns string response matching real method behavior
- Test validates string response content correctly

---

### 🐛 **Bug 6: Content-Type Validation Error**
**Files**: `tests/integration/test_llm_network_validation.py`
**Failing Test**: `test_validate_response_large_response_warning`

**Root Cause**:
```python
# Current issue:
mock_response.headers = {"Content-Length": "6000000"}  # Missing Content-Type
# Validation expects Content-Type header, gets empty string ''
```

**Fix Strategy**:
```python
# Fixed:
mock_response.headers = {
    "Content-Type": "application/json",  # Add required header
    "Content-Length": "6000000"
}
```

**Implementation Steps**:
1. Add `"Content-Type": "application/json"` to mock response headers
2. Verify validation accepts the Content-Type
3. Ensure test still triggers large response warning path
4. Add test comment explaining header requirements

**Acceptance Criteria**:
- Test passes Content-Type validation step
- Large response warning is still triggered and tested
- Mock response headers match real Ollama API responses

---

### 🐛 **Bug 7: Placeholder Test Implementation**
**Files**: `tests/integration/test_llm_phase4_tools.py`
**Failing Test**: `test_generate_directory`

**Root Cause**:
```python
# Current (PLACEHOLDER):
def test_generate_directory(self):
    """Test directory generation from contacts with images."""
    assert False is True  # Placeholder assertion
```

**Fix Strategy**:
Implement real test that validates directory generation workflow:

```python
def test_generate_directory(self):
    """Test directory generation from contacts with images."""
    # Use test fixtures with known contact data
    # Mock file system operations to avoid actual file creation
    # Verify tool chain: save_contacts_with_images -> generate_directory
    # Assert expected return structure and success status
```

**Implementation Steps**:
1. Review `_generate_directory()` method in `llm_ollama.py` to understand expected behavior
2. Create test with proper fixtures (contacts with images)
3. Mock file system operations (`tempfile`, `shutil`, `pathlib`)
4. Mock `DirectoryGenerator` class to avoid actual HTML generation
5. Verify tool returns expected success response structure
6. Test both search_query and memory_id code paths

**Acceptance Criteria**:
- Test validates directory generation logic without file I/O
- Both `search_query` and `memory_id` parameters are tested
- Mock assertions verify correct tool chain execution
- Test completes in < 1s using mocks

---

## Instrumentation & Diagnostics

### Enhanced Test Logging
Add comprehensive logging to diagnose timing and execution issues:

```python
import time
import logging

def test_with_instrumentation(self):
    start_time = time.time()
    logger = logging.getLogger(__name__)

    logger.info(f"[TEST_START] {self._testMethodName}")

    try:
        # Test execution
        result = await self.method_under_test()
        execution_time = time.time() - start_time

        logger.info(f"[TEST_SUCCESS] {self._testMethodName} completed in {execution_time:.3f}s")
        assert execution_time < 1.0, f"Test exceeded 1s limit: {execution_time:.3f}s"

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"[TEST_FAILURE] {self._testMethodName} failed after {execution_time:.3f}s: {e}")
        raise
```

### Mock Validation Framework
Add systematic mock validation to catch signature mismatches:

```python
class MockValidator:
    @staticmethod
    def validate_method_call(mock_obj, method_name, expected_signature):
        """Validate mock was called with correct signature."""
        actual_calls = mock_obj.call_args_list
        for call in actual_calls:
            args, kwargs = call
            # Validate against expected signature
            # Log mismatches with clear error messages
```

### Performance Monitoring
Add timing assertions to prevent regression:

```python
@pytest.mark.performance_check
def test_method_with_timing_assertion(self):
    with pytest.raises(AssertionError, match="exceeded time limit"):
        # Any test taking > integration limit should fail
        pass
```

## Implementation Plan

### Phase 1: Setup & Validation (1-2 hours)
1. **Create test branch**: `fix/integration-test-bugs`
2. **Run failing tests individually** to confirm current failure modes
3. **Set up enhanced logging** for diagnostic information
4. **Create backup of current test files** before modifications

### Phase 2: Fix Async/Await Issues (1 hour)
1. Fix `test_health_check_with_validation`
2. Fix `test_health_check_validation_fails`
3. Verify async mocking still works correctly
4. Run tests to confirm fixes

### Phase 3: Fix Method Signature Issues (1.5 hours)
1. Fix `test_preload_model_with_validation`
2. Fix `test_preload_model_validation_fails`
3. Fix `test_chat_with_validation`
4. Update all mock expectations
5. Verify correct API usage patterns

### Phase 4: Fix Content-Type & Placeholder Tests (1 hour)
1. Fix `test_validate_response_large_response_warning`
2. Implement `test_generate_directory` with proper mocks
3. Add comprehensive test coverage for edge cases

### Phase 5: Validation & Documentation (0.5 hours)
1. **Run full integration test suite** - should see 7 fewer failures
2. **Verify timing improvements** - all tests < 5s limit
3. **Update test documentation** with new patterns
4. **Create test pattern examples** for future development

## Success Metrics

### Before Fix
- ❌ 7/74 integration tests failing
- ❌ 2 tests taking 6-11+ seconds (timing violations)
- ❌ Async/await errors in logs
- ❌ Method signature TypeError exceptions

### After Fix
- ✅ 0/74 integration tests failing (or 67/74 if excluding LLM tests to be reclassified)
- ✅ All integration tests complete in < 5s
- ✅ No async/await warnings in test output
- ✅ No TypeError exceptions from incorrect method calls
- ✅ Clear test output with proper logging
- ✅ Consistent mock validation patterns

## Risk Assessment

### Low Risk
- **Async/await fixes**: Standard pytest patterns, well-documented
- **Method signature fixes**: Clear parameter removal, no logic changes

### Medium Risk
- **Mock updates**: Could break if mock expectations are incorrect
- **Directory generation test**: New implementation needs thorough validation

### Mitigation Strategies
- **Incremental fixes**: Fix one bug at a time, validate each step
- **Backup & rollback**: Keep original test files for quick revert
- **Comprehensive validation**: Run tests multiple times to ensure stability

## Dependencies

### Prerequisites
- Working pytest environment with asyncio support
- Access to test fixtures and mock frameworks
- Understanding of current LLM API signatures

### No External Dependencies
- All fixes use existing test infrastructure
- No new packages or external services required
- Mocks prevent network calls during testing

## Validation Plan

### Automated Validation
```bash
# Run fixed tests specifically
pytest tests/integration/test_llm_network_validation.py::TestLLMNetworkValidation::test_health_check_with_validation -v

# Run all integration tests with timing
pytest tests/integration/ --durations=10 -v

# Verify no async warnings
pytest tests/integration/ -W error::DeprecationWarning
```

### Manual Validation
1. **Review test output logs** for clean execution
2. **Verify mock assertions** are meaningful and correct
3. **Confirm timing improvements** with multiple test runs
4. **Check CI pipeline compatibility** with async test patterns

This plan provides a systematic approach to eliminating the 7 critical test failures while adding robust instrumentation to prevent future regressions.