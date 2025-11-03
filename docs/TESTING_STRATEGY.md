# PRT Testing Strategy

**Last Updated**: 2025-11-04
**Status**: Canonical reference for all PRT testing

> ⚠️ **IMPORTANT UPDATE**: As of November 2025, we have identified critical issues with current integration test categorization. Tests marked as `integration` (< 5s) are violating timing contracts by taking 6-11+ seconds with real LLM calls. New implementation plans in `specs/integration_test_*` address these issues through proper test categorization and MockLLMService infrastructure.

---

## Core Philosophy: Headless First

**ALWAYS write automated, headless tests wherever possible.**

Both LLMs and humans should follow this principle:
- ✅ **Default**: Write headless tests using pytest + Pilot (for TUI) or pytest alone (for non-TUI)
- ⚠️ **Fallback**: Manual testing only when headless testing is impossible
- 📝 **Document**: When manual testing is required, document it in `docs/MANUAL_TESTING.md`

### Why Headless Testing?

1. **Fast feedback**: Tests run in seconds, not minutes
2. **Reproducible**: Same test, same result every time
3. **CI/CD friendly**: Can run in GitHub Actions without human intervention
4. **Catch regressions**: Automated tests prevent bugs from returning
5. **Development velocity**: Tests enable confident refactoring

---

## The 4-Layer Testing Pyramid

We use a layered approach from fast/frequent (bottom) to slow/rare (top):

```
           ┌──────────────────┐
           │   E2E Tests      │  🐢 5-10 min  (manual/nightly)
           │  Real LLM + TUI  │
           └──────────────────┘
                    │
           ┌──────────────────┐
           │ Contract Tests   │  🧪 1-5 min   (nightly/release)
           │  Real LLM APIs   │  @pytest.mark.contract
           └──────────────────┘  @pytest.mark.requires_llm
                    │            @pytest.mark.timeout(300)
           ┌──────────────────┐
           │Integration Tests │  ⚙️  < 5 sec  (every commit)
           │ MockLLMService   │  Real DB + Mock LLM
           └──────────────────┘
                    │
           ┌──────────────────┐
           │   Unit Tests     │  ⚡ < 1 sec   (every save)
           │  No external deps│
           └──────────────────┘
```

> **⚠️ CURRENT ISSUE**: Some tests marked `@pytest.mark.integration` are actually calling real LLM services and taking 6-11+ seconds, violating the < 5s contract. These need reclassification as contract tests and MockLLMService substitution. See implementation plans in `specs/integration_test_*` for fixes.

### Layer 1: Unit Tests ⚡
- **Speed**: < 1 second total
- **Frequency**: Every save (watch mode)
- **What**: Pure functions, formatters, parsers, utilities
- **No**: Database, LLM, TUI rendering

**Example**: `tests/unit/test_results_formatter.py`
```python
def test_numbered_list_formatting():
    formatter = ResultsFormatter()
    contacts = [Contact(id=1, name="Alice"), Contact(id=2, name="Bob")]

    result = formatter.render(contacts, mode='numbered_list')

    assert "[1] Alice" in result
    assert "[2] Bob" in result
```

**Run**: `./prt_env/bin/pytest -m unit`

### Layer 2: Integration Tests ⚙️
- **Speed**: < 5 seconds total
- **Frequency**: Before every commit
- **What**: Component interactions, workflows, screen navigation
- **With**: Real database (fixture), **MockLLMService**, Pilot for TUI

**TUI Example**: `tests/test_home_screen.py`
```python
async def test_home_screen_navigation(pilot_screen):
    """Test navigation using Textual Pilot (headless TUI testing)."""
    async with pilot_screen(HomeScreen) as pilot:
        # Press 'h' to navigate to help
        await pilot.press("h")

        # Verify help screen is pushed
        assert isinstance(pilot.app.screen, HelpScreen)
```

**MockLLM Example**: `tests/integration/test_llm_integration_mocked.py`
```python
@pytest.mark.integration
def test_contact_count_query_fast(test_db):
    """Fast integration test using MockLLMService (< 1s execution)."""
    db, fixtures = test_db
    api = PRTAPI(config=test_db_config)

    # Use MockLLMService instead of real LLM
    mock_llm = MockOllamaLLM(api=api)
    mock_llm.set_response("how many contacts", "You have 7 contacts in your database.")

    response = mock_llm.chat("How many contacts do I have?")

    assert "7 contacts" in response
    # Completes in < 100ms with deterministic response
```

> **⚠️ BAD EXAMPLE** (violates < 5s contract):
> ```python
> # DON'T DO THIS in integration tests:
> llm = OllamaLLM(api=api)  # Real LLM - takes 6-11+ seconds
> response = llm.chat("test")  # This belongs in contract tests
> ```

**Run**: `./prt_env/bin/pytest -m integration`

### Layer 3: Contract Tests 🧪
- **Speed**: 1-5 minutes
- **Frequency**: Nightly or before release
- **What**: Real LLM behavior validation with actual Ollama models
- **With**: Real LLM + timeout protection + skip when unavailable

**Real LLM Example**: `tests/contracts/test_llm_real_behavior.py`
```python
@pytest.mark.contract
@pytest.mark.requires_llm
@pytest.mark.timeout(300)  # 5-minute timeout protection
@pytest.mark.skipif(not is_ollama_available(), reason="Ollama not available")
def test_count_contacts_contract(test_db):
    """Contract test validating real LLM tool calling behavior."""
    db, fixtures = test_db
    api = PRTAPI(config=test_db_config)

    # Use real OllamaLLM for contract validation
    llm = OllamaLLM(api=api)

    # Contract: LLM should use get_database_stats tool and return count
    response = llm.chat("How many contacts do I have?")

    # Validate contract behavior (not just mock responses)
    assert isinstance(response, str)
    assert len(response) > 0
    assert "7" in response or "seven" in response.lower()
    assert "contact" in response.lower()
```

**CI Strategy**:
- **Fast CI (every PR)**: Skip contract tests, run integration with mocks
- **Nightly CI**: Run contract tests with real Ollama setup
- **Local development**: Run contract tests when Ollama available

**Legacy Promptfoo**: Contract testing files exist in `tests/llm_contracts/` but are not currently maintained. The new approach uses pytest with real LLM integration for more reliable validation.

### Layer 4: E2E / Manual Tests 🐢
- **Speed**: 5-10 minutes
- **Frequency**: Before release or for specific scenarios
- **What**: Visual validation, performance, accessibility, complex workflows
- **How**: Manual testing with real TUI + real LLM

**See**: `docs/MANUAL_TESTING.md` for scenarios requiring manual testing

---

## Technology-Specific Guidance

### TUI Testing with Textual Pilot

**Pilot enables headless TUI testing** - you can simulate user input and verify screen state without rendering to a terminal.

**Key Textual Testing Resources**:
- **Primary Guide**: `EXTERNAL_DOCS/textual/docs/guide/testing.md`
- **PRT Patterns**: `docs/TUI/TUI_Dev_Tips.md`
- **Chat Testing**: `docs/TUI/Chat_Screen_Testing_Strategy.md`

**Common Pilot Patterns**:
```python
# Screen mounting and navigation
async with pilot_screen(HomeScreen) as pilot:
    await pilot.press("n")  # Press 'n' key
    await pilot.press("h")  # Navigate to help
    assert isinstance(pilot.app.screen, HelpScreen)

# Widget interaction
async with app.run_test() as pilot:
    await pilot.click("#save-button")
    assert pilot.app.query_one("#status").renderable == "Saved!"

# Text input
async with app.run_test() as pilot:
    await pilot.press("tab")  # Focus input
    await pilot.press(*"Hello World")  # Type text
    await pilot.press("enter")
```

**When Pilot Is NOT Enough** (require manual testing):
- Visual regression (colors, alignment, responsive layout)
- Performance/memory profiling
- Accessibility (screen readers, keyboard-only navigation)
- Platform-specific rendering issues

### LLM Testing

**Principle**: Use the lightest test that proves the behavior.

**Unit Tests**: Test parsing, formatting, context building (no LLM calls)
```python
def test_command_extraction():
    parser = CommandParser()
    text = 'The command is {"action": "search", "query": "Alice"} and done.'

    command = parser.extract_json(text)

    assert command["action"] == "search"
    assert command["query"] == "Alice"
```

**Integration Tests**: Use MockLLMService for fast, deterministic testing
```python
@pytest.mark.integration
def test_search_workflow_with_mock_llm(test_db):
    """Fast integration test using MockLLMService."""
    db, fixtures = test_db
    api = PRTAPI(config=test_db_config)

    # MockLLMService provides deterministic responses
    mock_llm = MockOllamaLLM(api=api)
    mock_llm.set_response("find Alice", "I found 1 contact named Alice Johnson.")

    response = mock_llm.chat("find Alice")

    assert "Alice" in response
    assert "found" in response.lower()
    # Completes in < 100ms
```

**Contract Tests**: Real LLM with timeout protection
```python
@pytest.mark.contract
@pytest.mark.requires_llm
@pytest.mark.timeout(300)
@pytest.mark.skipif(not is_ollama_available(), reason="Ollama not available")
def test_real_llm_tool_calling(test_db):
    """Validate real LLM behavior with actual Ollama."""
    db, fixtures = test_db
    api = PRTAPI(config=test_db_config)

    # Real OllamaLLM for contract validation
    llm = OllamaLLM(api=api)
    response = llm.chat("How many contacts?")

    # Contract validation - real LLM should call tools correctly
    assert isinstance(response, str)
    assert len(response) > 0
    # May take 1-5 minutes but validates real behavior
```

**MockLLMService Features**:
- **Pattern matching**: Set responses based on query patterns
- **Tool simulation**: Simulates tool calls without real LLM processing
- **Deterministic**: Same input always produces same output
- **Fast**: < 100ms per operation vs 6-11s for real LLM

### Database Testing

**Principle**: Use real SQLite with fixtures, no mocking needed.

**Fixture Pattern**:
```python
@pytest.fixture
def test_db():
    """Create isolated test database with fixture data."""
    from tests.fixtures import setup_test_database

    db_path = Path(tempfile.mkdtemp()) / "test.db"
    db = create_database(db_path)
    fixtures = setup_test_database(db)

    yield db, fixtures

    db.session.close()
    db_path.unlink()
```

**Fixture Specification Pattern** (single source of truth):
```python
from tests.fixtures import get_fixture_spec

def test_contact_count(test_db):
    db, fixtures = test_db
    spec = get_fixture_spec()  # Returns {"contacts": {"count": 7, ...}}

    contacts = db.list_contacts()

    assert len(contacts) == spec["contacts"]["count"]
```

**Why No Mocking?**: SQLite is fast enough for tests (<< 1ms per query), and testing with real DB catches SQL bugs.

---

## Running Tests

### Quick Commands

```bash
# Activate environment
source ./init.sh

# Fast feedback loop (every commit) - uses MockLLMService
./prt_env/bin/pytest -m "unit or integration" --maxfail=5
# Expected: ~30s total, all deterministic

# Run unit tests only (< 1 sec each)
./prt_env/bin/pytest -m unit

# Run integration tests only (< 5 sec each, uses mocks)
./prt_env/bin/pytest -m integration

# Run contract tests (real LLM, if available)
./prt_env/bin/pytest -m "contract and requires_llm" --timeout=600

# Run all tests including contract (when Ollama available)
./prt_env/bin/pytest -m "unit or integration or (contract and requires_llm)"

# Run specific test file
./prt_env/bin/pytest tests/test_home_screen.py -v

# Run specific test
./prt_env/bin/pytest tests/test_home_screen.py::test_screen_mounts -v

# Run with coverage
./prt_env/bin/pytest tests/ --cov=prt_src --cov-report=html --cov-report=term

# Watch mode (re-run on file save) - fast tests only
./prt_env/bin/pytest -m "unit or integration" --watch
```

### Test Markers

Tests are marked for selective execution:
```python
@pytest.mark.unit              # Fast (< 1s), no external dependencies
@pytest.mark.integration       # Fast (< 5s), real DB + MockLLMService + Pilot
@pytest.mark.contract          # Slow (1-5min), real LLM validation
@pytest.mark.requires_llm      # Requires Ollama running (skips in CI)
@pytest.mark.timeout(300)      # 5-minute timeout for contract tests
@pytest.mark.slow             # Very slow (5-10min), manual/nightly only
```

**Common Combinations**:
```python
# Fast integration test with mock LLM
@pytest.mark.integration

# Real LLM contract test with timeout protection
@pytest.mark.contract
@pytest.mark.requires_llm
@pytest.mark.timeout(300)
@pytest.mark.skipif(not is_ollama_available(), reason="Ollama not available")
```

### Debug Mode Testing

```bash
# Run with fixture database
./prt_env/bin/python -m prt_src.cli --debug

# Run chat with fixtures
./prt_env/bin/python -m prt_src.cli chat --debug --regenerate-fixtures

# Run TUI with fixtures
./prt_env/bin/python -m prt_src --debug
```

---

## Test Organization

```
tests/
├── unit/                  # Layer 1: Pure unit tests (< 1 sec total)
│   ├── test_results_formatter.py
│   ├── test_display_context.py
│   └── test_selection_service.py
│
├── integration/           # Layer 2: Integration tests with real components
│   └── test_llm_one_query.py
│
├── test_home_screen.py    # Layer 2: TUI integration tests (Pilot)
├── test_help_screen.py
├── test_chat_navigation.py
├── test_phase2_screens.py
│
├── test_api.py            # Layer 2: API integration tests
├── test_db.py
├── test_relationships.py
│
├── llm_contracts/         # Layer 3: Contract tests (not currently active)
│   ├── promptfooconfig_search_only.yaml
│   └── promptfooconfig_comprehensive.yaml
│
├── conftest.py            # Shared fixtures (test_db, pilot_screen)
└── fixtures.py            # Test data (SAMPLE_CONTACTS, setup_test_database)
```

---

## Writing New Tests

### Decision Tree: What Type of Test?

```
┌─ Is it a pure function (no side effects)?
│  └─ YES → Write a unit test (tests/unit/)
│  └─ NO  ↓
│
├─ Does it involve TUI rendering?
│  └─ YES → Write a Pilot test (tests/test_*_screen.py)
│  └─ NO  ↓
│
├─ Does it involve LLM calls?
│  └─ YES → Can you mock the LLM response?
│     └─ YES → Write integration test with mock LLM
│     └─ NO  → Write contract test (Promptfoo) or mark @pytest.mark.skipif
│  └─ NO  ↓
│
└─ Does it involve database operations?
   └─ YES → Write integration test with test_db fixture
   └─ NO  → Write unit test
```

### Test Template

```python
"""Test module docstring explaining what's being tested."""

import pytest
from prt_src.api import PRTAPI
from tests.fixtures import get_fixture_spec


@pytest.mark.unit  # or @pytest.mark.integration
def test_specific_behavior(test_db):  # Use appropriate fixture
    """Test description: Given X, when Y, then Z."""
    # ARRANGE - Set up test data
    db, fixtures = test_db
    spec = get_fixture_spec()

    # ACT - Perform the action
    result = function_under_test(db, param)

    # ASSERT - Verify the result
    assert result == expected
    assert result.property == spec["expected_value"]
```

### Pilot Test Template

```python
"""Test TUI screen behavior."""

import pytest
from textual.pilot import Pilot
from prt_src.tui.screens.home import HomeScreen


async def test_screen_navigation(pilot_screen):
    """Test navigation between screens."""
    async with pilot_screen(HomeScreen) as pilot:
        # ARRANGE - Screen is mounted by pilot_screen fixture

        # ACT - Simulate user input
        await pilot.press("h")  # Press 'h' to navigate to help

        # ASSERT - Verify screen changed
        assert pilot.app.screen.__class__.__name__ == "HelpScreen"
```

---

## When Manual Testing Is Required

See `docs/MANUAL_TESTING.md` for comprehensive scenarios.

**Common Cases**:
1. **Visual Regression**: Colors, fonts, alignment, responsive layout
2. **Performance**: Memory usage, render time, large datasets
3. **Accessibility**: Screen readers, keyboard-only navigation, color contrast
4. **Platform-Specific**: Terminal compatibility (iTerm2, Windows Terminal, etc.)
5. **Complex User Flows**: Multi-step wizards, error recovery, edge cases

**Process**:
1. Attempt to write headless test first
2. If headless is impossible, document in `docs/MANUAL_TESTING.md`
3. Include manual test in release checklist

---

## Debugging Failed Tests

### Read the Logs First

Tests output to `prt_data/prt.log`:
```bash
# Watch logs while test runs
tail -f prt_data/prt.log

# Filter by component
tail -f prt_data/prt.log | grep '\[LLM\]'

# Get recent test run logs
tail -200 prt_data/prt.log
```

### Common Issues

**Test hangs indefinitely**:
- Usually an async issue - missing `await` or deadlock
- Add timeout: `@pytest.mark.timeout(10)`

**Test passes locally, fails in CI**:
- Environment difference (Ollama not available, different Python version)
- Use `@pytest.mark.skipif` for environment-dependent tests

**Pilot test fails with "no screen"**:
- Screen not mounted yet - add `await pilot.pause()`
- Check `pilot.app.screen` to see what's actually mounted

**Database fixture issues**:
- Ensure `test_db` fixture is used
- Check `get_fixture_spec()` for expected values
- Don't hardcode expected counts - use spec

---

## CI/CD Integration

**Two-Pipeline Strategy** for fast feedback and comprehensive validation:

### Fast CI Pipeline (Every PR)
```yaml
# .github/workflows/fast-tests.yml
name: Fast Tests (Unit + Integration)
on: [push, pull_request]

- name: Run Fast Tests
  run: ./prt_env/bin/pytest -m "unit or integration" --maxfail=5 --timeout=30
  # Expected: ~30s total, uses MockLLMService
```

**Characteristics**:
- ✅ **Speed**: ~30 seconds total
- ✅ **Reliability**: No external dependencies (MockLLMService)
- ✅ **Coverage**: All integration workflows with deterministic responses

### Contract Test Pipeline (Nightly)
```yaml
# .github/workflows/contract-tests.yml
name: Contract Tests (Real LLM)
on:
  schedule:
    - cron: "0 2 * * *"  # Nightly at 2 AM
  workflow_dispatch:      # Manual trigger

- name: Setup Ollama
  run: |
    ollama pull gpt-oss:20b
    ollama serve &

- name: Run Contract Tests
  run: ./prt_env/bin/pytest -m "contract and requires_llm" --timeout=600 --maxfail=3
  # Expected: 5-10 minutes, validates real LLM behavior
```

**Exit Criteria for Merge**:
- ✅ All unit tests pass (< 1s each)
- ✅ All integration tests pass (< 5s each, using mocks)
- ✅ Linting passes (ruff + black)
- ✅ No decrease in code coverage
- ℹ️ Contract tests run nightly (not blocking for PRs)

---

## Test Maintenance

### When to Update Tests

1. **Feature changes**: Update tests to match new behavior
2. **Bug fixes**: Add regression test before fixing
3. **Refactoring**: Tests should still pass (if they don't, refactor wasn't safe)
4. **Deprecation**: Remove tests for removed features

### Red-Green-Refactor

Follow TDD cycle where appropriate:
1. **Red**: Write failing test for new feature
2. **Green**: Implement minimal code to pass test
3. **Refactor**: Clean up code while tests stay green

### Test Coverage Goals

- **Unit tests**: > 90% coverage for logic/formatting/parsing
- **Integration tests**: Cover all happy paths + critical error paths
- **Contract tests**: Cover all LLM intents + edge cases
- **Manual tests**: Document but don't overdo it

---

## Implementation Plans & Upgrades

### Current Integration Test Issues
As of November 2025, we have identified critical problems with integration test categorization and performance. Detailed implementation plans are available:

- **`specs/integration_test_bug_fixes.md`**: Fix 7 critical test failures (async/await issues, method signatures, content-type validation)
- **`specs/integration_test_categorization_upgrade.md`**: Implement MockLLMService, reclassify tests, add timeout protection

### Implementation Branch
- **Branch**: `feature/integration-test-upgrades`
- **Status**: Ready for implementation
- **Target**: Transform integration tests from slow/unreliable (45s, 7 failures) to fast/reliable (30s, 0 failures)

## Resources

### PRT-Specific
- **This Document**: Canonical testing strategy
- **Implementation Plans**: `specs/integration_test_*.md` (detailed upgrade roadmap)
- **TUI Testing**: `docs/TUI/TUI_Dev_Tips.md`
- **Chat Testing**: `docs/TUI/Chat_Screen_Testing_Strategy.md`
- **Manual Testing**: `docs/MANUAL_TESTING.md`
- **Fixtures**: `tests/fixtures.py` (SAMPLE_CONTACTS, get_fixture_spec)

### External
- **Textual Testing Guide**: `EXTERNAL_DOCS/textual/docs/guide/testing.md`
- **Pytest Documentation**: https://docs.pytest.org/

---

## Questions?

If this document doesn't answer your testing question:
1. Check if it's documented in a linked resource
2. Ask in GitHub Discussions
3. Propose an update to this document
