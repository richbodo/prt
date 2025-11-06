# Integration Test Categorization & Infrastructure Upgrade - Plan 2

## Overview
This plan implements proper test categorization, creates a mock LLM service for fast integration tests, and adds timeout protection for real LLM contract tests. This ensures fast CI/CD feedback loops while maintaining comprehensive testing coverage.

## Current Problem

### Miscategorized Tests
- Tests marked `@pytest.mark.integration` (< 5s limit) are taking **6-11+ seconds**
- Real LLM calls in integration tier violate project testing contracts
- Slow tests block CI/CD and developer productivity
- No distinction between mocked integration tests and real LLM contract tests

### Missing Infrastructure
- No mock LLM service for deterministic, fast testing
- No timeout protection for long-running real LLM tests
- No CI strategy to separate fast vs. slow test execution

## Solution Architecture

### Test Categorization Strategy
```
┌─ UNIT TESTS (< 1s) ─────────────────────────────────────┐
│ • Pure functions, data structures, utils                │
│ • No external dependencies                              │
│ • @pytest.mark.unit                                     │
└─────────────────────────────────────────────────────────┘

┌─ INTEGRATION TESTS (< 5s) ──────────────────────────────┐
│ • Component interactions with MockLLMService            │
│ • Database operations with test fixtures                │
│ • @pytest.mark.integration                              │
│ • Fast, deterministic, reliable                         │
└─────────────────────────────────────────────────────────┘

┌─ CONTRACT TESTS (1-5 min) ──────────────────────────────┐
│ • Real LLM behavior validation                          │
│ • Tool calling with actual Ollama                       │
│ • @pytest.mark.contract @pytest.mark.requires_llm      │
│ • @pytest.mark.timeout(300)                             │
│ • Run nightly or on release branches                    │
└─────────────────────────────────────────────────────────┘

┌─ E2E TESTS (< 10s) ─────────────────────────────────────┐
│ • Full user workflows with mocked external services     │
│ • TUI interactions with MockLLMService                  │
│ • @pytest.mark.e2e                                      │
└─────────────────────────────────────────────────────────┘
```

## Detailed Implementation Plan

---

## Component 1: Mock LLM Service

### Design Specification

**File**: `tests/mocks/mock_llm_service.py`

```python
class MockOllamaLLM:
    """High-fidelity mock of OllamaLLM for fast, deterministic testing."""

    def __init__(self, api: PRTAPI, **kwargs):
        self.api = api
        self.conversation_history = []
        self.tools = self._create_tools()  # Same as real LLM
        self.response_overrides = {}  # Injectable responses

    def set_response(self, query_pattern: str, response: str):
        """Inject specific response for testing scenarios."""

    def chat(self, message: str) -> str:
        """Return deterministic responses based on message patterns."""

    async def health_check(self, timeout: float = 2.0) -> bool:
        """Always return True for testing."""

    async def preload_model(self) -> bool:
        """Always return True for testing."""
```

**Key Features**:
1. **Drop-in replacement** for OllamaLLM in tests
2. **Deterministic responses** based on input patterns
3. **Tool calling simulation** without real LLM processing
4. **Response injection** for specific test scenarios
5. **Fast execution** (< 100ms per operation)

### Response Pattern Matching
```python
class ResponsePatterns:
    PATTERNS = {
        r"how many contacts": "You have {contact_count} contacts in your database.",
        r"list.*contacts": "Here are your contacts: {contact_list}",
        r"search.*john": "Found {john_count} contacts matching 'John'",
        r"create.*directory": "Directory created successfully at {output_path}",
        # ... more patterns
    }
```

### Tool Call Simulation
```python
def _simulate_tool_call(self, tool_name: str, arguments: dict) -> dict:
    """Simulate tool execution with realistic responses."""
    if tool_name == "get_database_stats":
        return {"contacts": len(self.api.list_all_contacts()), "relationships": 7}
    elif tool_name == "search_contacts":
        # Return subset of test fixtures based on query
        return self._search_test_contacts(arguments.get("query", ""))
    # ... handle other tools
```

---

## Component 2: Test Reclassification

### Phase 2A: Identify Tests for Reclassification

**Current Integration Tests Requiring Real LLM** (to be reclassified):
```python
# tests/integration/test_llm_one_query.py
@pytest.mark.integration  # REMOVE
@pytest.mark.contract     # ADD
@pytest.mark.requires_llm # ADD
@pytest.mark.timeout(300) # ADD
def test_count_contacts_integration():
    """Real LLM contract test for contact counting."""

@pytest.mark.integration  # REMOVE
@pytest.mark.contract     # ADD
@pytest.mark.requires_llm # ADD
@pytest.mark.timeout(300) # ADD
def test_debug_tool_execution():
    """Real LLM contract test for tool calling."""
```

**Tests to Keep as Integration** (using MockLLMService):
```python
# tests/integration/test_llm_network_validation.py
@pytest.mark.integration  # KEEP - will use mocks
def test_validate_response_valid_json():
    """Test response validation with mocked responses."""

@pytest.mark.integration  # KEEP - will use mocks
def test_chat_with_validation():
    """Test chat method with MockLLMService."""
```

### Phase 2B: Create New Fast Integration Tests

**File**: `tests/integration/test_llm_integration_mocked.py`

```python
@pytest.mark.integration
class TestLLMIntegrationMocked:
    """Fast integration tests using MockLLMService."""

    def setup_method(self):
        self.mock_llm = MockOllamaLLM(api=self.test_api)

    def test_contact_count_query_fast(self):
        """Test contact counting with deterministic mock response."""
        # Set expected response
        self.mock_llm.set_response(
            "how many contacts",
            "You have 7 contacts in your database."
        )

        response = self.mock_llm.chat("How many contacts do I have?")

        assert "7 contacts" in response
        assert len(self.mock_llm.conversation_history) == 2
        # Completes in < 100ms

    def test_tool_calling_workflow_fast(self):
        """Test tool calling without real LLM processing."""
        # Mock will simulate get_database_stats tool call
        response = self.mock_llm.chat("How many contacts?")

        # Verify tool was "called" in simulation
        assert self.mock_llm.last_tool_called == "get_database_stats"
        assert "contacts" in response.lower()
        # Completes in < 100ms
```

### Phase 2C: Update Existing Integration Tests

**Migration Strategy**:
1. **Replace OllamaLLM with MockOllamaLLM** in integration tests
2. **Keep test logic identical** but use deterministic responses
3. **Add timing assertions** to ensure < 5s compliance
4. **Preserve validation patterns** for mock behavior

```python
# Before:
def test_llm_method(self):
    llm = OllamaLLM(api=self.api)  # Real LLM - slow
    response = llm.chat("test")
    # Takes 6-11 seconds

# After:
def test_llm_method(self):
    llm = MockOllamaLLM(api=self.api)  # Mock LLM - fast
    response = llm.chat("test")
    # Takes < 100ms
    assert response_time < 1.0  # Timing assertion
```

---

## Component 3: Timeout Protection for Contract Tests

### Timeout Decorator Implementation
```python
import pytest
import signal
from contextlib import contextmanager

@contextmanager
def timeout_context(seconds):
    """Provide timeout context for long-running tests."""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Test exceeded {seconds}s timeout")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
```

### Contract Test Pattern
```python
@pytest.mark.contract
@pytest.mark.requires_llm
@pytest.mark.timeout(300)  # 5-minute timeout
@pytest.mark.skipif(not is_ollama_available(), reason="Ollama not available")
def test_real_llm_contract():
    """Contract test with real LLM - includes timeout protection."""

    with timeout_context(300):
        # Test implementation
        llm = OllamaLLM(api=self.api)
        response = llm.chat("How many contacts?")

        # Contract validation
        assert isinstance(response, str)
        assert len(response) > 0
        assert "contact" in response.lower()
```

### Retry Logic for Flaky LLM Tests
```python
@pytest.mark.flaky(reruns=2, reruns_delay=5)  # Retry flaky tests
@pytest.mark.contract
@pytest.mark.requires_llm
def test_llm_with_retry():
    """LLM test with automatic retry for transient failures."""
    # Test implementation with retry protection
```

---

## Component 4: CI/CD Integration Strategy

### GitHub Actions Workflow Separation

**File**: `.github/workflows/fast-tests.yml`
```yaml
name: Fast Tests (Unit + Integration)
on: [push, pull_request]

jobs:
  fast-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Fast Tests
        run: |
          pytest -m "unit or integration" --maxfail=5 --timeout=30
          # Expected: ~30s total, all tests use mocks
```

**File**: `.github/workflows/contract-tests.yml`
```yaml
name: Contract Tests (Real LLM)
on:
  schedule:
    - cron: "0 2 * * *"  # Nightly at 2 AM
  workflow_dispatch:      # Manual trigger

jobs:
  contract-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Ollama
        run: |
          # Install and configure Ollama
          ollama pull gpt-oss:20b
      - name: Run Contract Tests
        run: |
          pytest -m "contract and requires_llm" --timeout=600 --maxfail=3
          # Expected: 5-10 minutes total, uses real LLM
```

### Local Development Commands
```bash
# Fast feedback loop (every save):
pytest -m "unit or integration" --watch

# Pre-commit validation (< 1 minute):
pytest -m "unit or integration" --maxfail=5

# Full validation before PR (if Ollama available):
pytest -m "unit or integration or (contract and requires_llm)" --timeout=300

# Nightly/weekly comprehensive testing:
pytest --timeout=600  # All tests including slow
```

---

## Implementation Phases

### Phase 1: Infrastructure Setup (2-3 hours)
1. **Create MockOllamaLLM class** with response patterns
2. **Implement tool call simulation** for common operations
3. **Create test fixtures** for deterministic mock responses
4. **Add timeout protection utilities** and decorators

### Phase 2: Test Migration (3-4 hours)
1. **Identify all tests calling real LLM** services
2. **Migrate fast tests to use MockOllamaLLM**
3. **Reclassify slow tests as contract tests** with timeout protection
4. **Create new fast integration tests** for missing coverage

### Phase 3: CI/CD Configuration (1-2 hours)
1. **Update GitHub Actions workflows** for test separation
2. **Configure Ollama setup** for contract test pipeline
3. **Add timeout and retry configuration** for flaky tests
4. **Test both fast and contract pipelines**

### Phase 4: Validation & Documentation (1 hour)
1. **Run full test suite** with new categorization
2. **Verify timing compliance** for each test category
3. **Update testing documentation** with new patterns
4. **Create developer guidelines** for test categorization

## Success Metrics

### Before Implementation
- ❌ Integration tests taking 6-11+ seconds (violates < 5s contract)
- ❌ No distinction between fast integration and slow contract tests
- ❌ CI blocked by slow LLM tests on every PR
- ❌ No timeout protection for long-running tests
- ❌ Flaky tests due to external LLM dependencies

### After Implementation
- ✅ Integration tests complete in < 5s using MockLLMService
- ✅ Contract tests properly categorized with timeout protection
- ✅ Fast CI feedback (30s) for unit + integration tests
- ✅ Separated nightly pipeline for comprehensive contract testing
- ✅ Deterministic test results with mock responses
- ✅ Clear developer guidelines for test categorization

### Performance Targets
```
Unit Tests:        < 1s each    (Total: ~10s for all)
Integration Tests: < 5s each    (Total: ~30s for all)
Contract Tests:    < 5min each  (Total: ~10min for all)
E2E Tests:         < 10s each   (Total: ~60s for all)
```

## Risk Assessment & Mitigation

### High Risk: MockLLMService Behavior Mismatch
**Risk**: Mock responses don't match real LLM behavior
**Mitigation**:
- Create contract tests to validate mock accuracy against real LLM
- Regular comparison of mock vs. real responses
- Version mock responses with LLM model updates

### Medium Risk: Test Coverage Gaps
**Risk**: Missing edge cases when migrating to mocks
**Mitigation**:
- Comprehensive audit of existing test coverage
- Create integration tests for all major LLM workflows
- Maintain contract tests for critical user journeys

### Low Risk: CI Pipeline Complexity
**Risk**: Multiple pipelines increase maintenance burden
**Mitigation**:
- Use shared workflow templates
- Clear documentation for pipeline purposes
- Automated monitoring of pipeline health

## Dependencies & Prerequisites

### Required Components
1. **Working pytest environment** with timeout plugin
2. **Test fixture system** for deterministic data
3. **GitHub Actions access** for CI/CD configuration
4. **Ollama setup** for contract test environment

### Optional Enhancements
1. **pytest-flaky plugin** for retry logic
2. **pytest-timeout plugin** for timeout management
3. **Coverage reporting** for mock vs. real test coverage
4. **Performance monitoring** for test execution times

This plan transforms the integration test suite from a slow, unreliable bottleneck into a fast, reliable foundation for continuous development while preserving comprehensive testing through proper categorization and infrastructure.