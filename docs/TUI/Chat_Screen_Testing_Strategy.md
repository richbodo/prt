# Chat Screen Testing Strategy

This document outlines the testing strategy for the Chat screen's LLM-powered database interface.

## The Challenge

**What makes testing LLM-powered UIs hard:**
- 🐌 **Slow**: Local LLM takes 10-30s per call
- 🎲 **Non-deterministic**: Same prompt can produce different outputs
- ♾️ **Infinite input space**: Can't enumerate all possible user messages
- ⚠️ **High-risk**: Wrong parsing could delete data or export wrong information
- 🔄 **Stateful**: Conversation context affects behavior

**What we need:**
- ✅ Fast feedback for development (tests run in seconds, not minutes)
- ✅ Confidence in critical paths (don't break data operations)
- ✅ Regression detection (prompt changes don't break parsing)
- ✅ Representative coverage (test realistic scenarios)

---

## Layered Testing Approach

We use a **four-layer pyramid** of tests, from fast/frequent (bottom) to slow/rare (top):

```
           ┌──────────────────┐
           │   E2E Tests      │  🐢 5-10 min  (manual/nightly)
           │  Real LLM + TUI  │
           └──────────────────┘
                    │
           ┌──────────────────┐
           │ Contract Tests   │  🧪 1-5 min   (before merge)
           │ LLM with Promptfoo│
           └──────────────────┘
                    │
           ┌──────────────────┐
           │Integration Tests │  ⚙️  < 5 sec  (before commit)
           │  Mock LLM        │
           └──────────────────┘
                    │
           ┌──────────────────┐
           │   Unit Tests     │  ⚡ < 1 sec   (every save)
           │  No LLM          │
           └──────────────────┘
```

---

## Layer 1: Unit Tests (No LLM) ⚡

**Speed**: < 1 second
**Frequency**: Every save (watch mode)
**Coverage**: Deterministic components

### What to Test

1. **ResultsFormatter**
   - Numbered lists with indices
   - Selection markers ([ ] and [✓])
   - Table formatting with Rich
   - Card formatting
   - Tree formatting for hierarchies
   - Empty result handling
   - Pagination indicators

2. **DisplayContext**
   - Index resolution (display [1] → database ID)
   - Minimal context generation (< 200 tokens)
   - Detailed context generation (< 2000 tokens)
   - `needs_detailed_context()` heuristic

3. **ChatContextManager**
   - Display updates
   - Conversation history management
   - Prompt building with token limits
   - Context pruning
   - Selection resolution

4. **SelectionService**
   - Selection accumulation
   - Deselection
   - "Select all" / "Select none"
   - Cross-context operations

### Example Test

```python
def test_numbered_list_with_selection():
    """Formatter shows selection markers correctly."""
    contacts = [
        fixture_contact(id=247, name='Alice'),
        fixture_contact(id=89, name='Bob')
    ]
    formatter = ResultsFormatter()

    result = formatter.render(
        contacts,
        result_type='contacts',
        mode='numbered_list',
        show_selection=True,
        selected_ids={247}  # Alice selected
    )

    assert '[✓] [1] Alice' in result
    assert '[ ] [2] Bob' in result
```

### Run Command

```bash
# Run all unit tests
pytest -m unit

# Run with watch mode (re-run on file save)
pytest -m unit --watch

# Run with coverage
pytest -m unit --cov=prt_src/tui --cov-report=term-missing
```

### Exit Criteria
- ✅ All unit tests pass
- ✅ Test suite runs in < 1 second
- ✅ Coverage > 90% for deterministic components

---

## Layer 2: Integration Tests (Mock LLM) ⚙️

**Speed**: < 5 seconds
**Frequency**: Before commit
**Coverage**: Full workflows with fake LLM responses

### What to Test

1. **Complete Workflows**
   - Search → format → display
   - Search → select → export
   - Search → refine → refine → select
   - Error recovery (failed export, permission denied)

2. **LLM Bridge Behavior**
   - Command parsing (JSON extraction)
   - Validation (schema, required fields)
   - Error handling (invalid JSON, unknown intent)
   - Permission checking

3. **Multi-Turn Conversations**
   - Context continuity
   - Refinement chains
   - Selection accumulation

### Mock LLM

```python
class MockLLMService:
    """Mock LLM that returns pre-defined responses."""

    def __init__(self):
        self.responses = {}

    def add_response(self, pattern: str, response: str):
        """Register canned response for a prompt pattern."""
        self.responses[pattern] = response

    def chat(self, prompt: str) -> str:
        """Return canned response matching prompt."""
        for pattern, response in self.responses.items():
            if pattern in prompt:
                return response
        raise ValueError(f"No mock response for: {prompt[:100]}")


@pytest.fixture
def mock_llm():
    """Pre-configured mock LLM."""
    llm = MockLLMService()

    # Standard search
    llm.add_response(
        'tech contacts',
        json.dumps({
            'intent': 'search',
            'parameters': {
                'entity_type': 'contacts',
                'filters': {'tags': ['tech']}
            },
            'explanation': 'Searching for tech contacts'
        })
    )

    # Standard selection
    llm.add_response(
        'select 1, 2, 5',
        json.dumps({
            'intent': 'select',
            'parameters': {
                'selection_type': 'ids',
                'ids': [1, 2, 5]
            },
            'explanation': 'Selected 3 contacts'
        })
    )

    return llm
```

### Example Test

```python
async def test_search_select_export_workflow(mock_llm, test_db):
    """Test complete search → select → export flow."""
    bridge = LLMDatabaseBridge(api=test_db, llm_service=mock_llm)
    workflow = SearchSelectActWorkflow(...)

    # 1. Search
    command = await bridge.parse_user_intent("show tech contacts")
    assert command['intent'] == 'search'

    results = await workflow.execute_search(command['parameters'])
    assert len(results) == 3  # From fixtures

    # 2. Select
    command = await bridge.parse_user_intent("select 1, 2, 5")
    db_ids = context.resolve_selection(command['parameters'])
    assert len(db_ids) == 2  # [5] out of range, only [1,2] valid

    # 3. Export
    command = await bridge.parse_user_intent("export for directory")
    export_path = await workflow.execute_action('export', format='directory')
    assert os.path.exists(export_path)
```

### Run Command

```bash
# Run all integration tests
pytest -m integration

# Run with verbose output
pytest -m integration -v

# Run specific test file
pytest tests/integration/test_chat_workflow.py -v
```

### Exit Criteria
- ✅ All integration tests pass
- ✅ Test suite runs in < 5 seconds
- ✅ Coverage > 80% of workflow logic

---

## Layer 3: LLM Contract Tests (Promptfoo) 🧪

**Speed**: 1-5 minutes
**Frequency**: Before merge (weekly in CI)
**Coverage**: Real LLM behavior validation

### What to Test

1. **Intent Classification**
   - Search intent variants
   - Selection intent variants
   - Export intent variants
   - Refinement intent variants

2. **Parameter Extraction**
   - Tags ("tech", "python", "AI")
   - Locations ("SF", "San Francisco", "bay area")
   - Dates ("this year", "2024", "last month")
   - IDs ([1,2,3], "1 and 2", "first 5")

3. **JSON Schema Validation**
   - Well-formed JSON (100% required)
   - Required fields present
   - Correct data types

4. **Safety Properties**
   - No hallucinated data (mustn't make up contact names)
   - No made-up IDs
   - No invented operations

5. **Edge Cases**
   - Empty/ambiguous queries
   - Very long queries
   - Special characters
   - Multi-language (if supported)

### Promptfoo Configuration

```yaml
# tests/llm_contracts/promptfoo.yaml
description: 'PRT Chat LLM Parsing Contract Tests'

prompts:
  - file://system_prompt.txt

providers:
  - id: ollama:gpt-oss:20b
    config:
      temperature: 0.1  # Low for consistency

tests:
  # Critical: Intent classification
  - description: 'Identifies search intent'
    vars:
      user_message: 'show me all my tech contacts'
    assert:
      - type: is-json
      - type: javascript
        value: JSON.parse(output).intent === 'search'
      - type: javascript
        value: JSON.parse(output).parameters.filters.tags.includes('tech')

  - description: 'Identifies selection intent'
    vars:
      user_message: 'select 1, 2, and 5'
    assert:
      - type: is-json
      - type: javascript
        value: JSON.parse(output).parameters.ids.sort().join(',') === '1,2,5'

  # Critical: No hallucinations
  - description: 'Does not invent contact names'
    vars:
      user_message: 'export the selected contacts'
    assert:
      - type: not-contains
        value: 'Alice'  # Shouldn't make up names
      - type: not-contains
        value: 'Bob'
```

### Run Command

```bash
# Run full suite with local LLM
npx promptfoo eval -c tests/llm_contracts/promptfoo.yaml

# Quick test with faster model (for CI)
npx promptfoo eval -c tests/llm_contracts/promptfoo.yaml -p ollama:llama3.2:3b

# Compare after prompt changes
npx promptfoo eval --config promptfoo.yaml --output results.json
npx promptfoo eval --config promptfoo.yaml --output results_new.json
python tests/llm_contracts/compare_results.py results.json results_new.json
```

### Baseline Tracking

```python
# tests/llm_contracts/compare_results.py

def compare_baseline(new_results, baseline_path='baseline.json'):
    """Compare new results against baseline, flag regressions."""
    with open(baseline_path) as f:
        baseline = json.load(f)

    metrics = {
        'intent_accuracy': calculate_accuracy(new_results, 'intent'),
        'json_validity': calculate_validity(new_results),
        'hallucination_rate': calculate_hallucinations(new_results)
    }

    regressions = []
    if metrics['intent_accuracy'] < baseline['intent_accuracy'] - 0.05:
        regressions.append(f"Intent accuracy dropped: {baseline['intent_accuracy']} → {metrics['intent_accuracy']}")

    if metrics['json_validity'] < 1.0:
        regressions.append(f"JSON validity not 100%: {metrics['json_validity']}")

    if regressions:
        print("⚠️  REGRESSIONS DETECTED:")
        for r in regressions:
            print(f"  - {r}")
        sys.exit(1)
    else:
        print("✅ No regressions detected")
```

### Exit Criteria
- ✅ Intent accuracy > 95%
- ✅ JSON validity = 100%
- ✅ Hallucination rate = 0%
- ✅ Baseline established
- ✅ Regression test runs in CI

---

## Layer 4: End-to-End Tests (Real LLM + TUI) 🐢

**Speed**: 5-10 minutes
**Frequency**: Manual or nightly
**Coverage**: Full system integration

### What to Test

1. **Critical User Journeys**
   - First-time user flow
   - Search → select → export workflow
   - Multi-turn refinement
   - Error recovery

2. **UI Interactions**
   - Keyboard navigation
   - Mode switching (EDIT/NAV)
   - Scrolling through results
   - Confirmation dialogs

### Example Test

```python
@pytest.mark.e2e
@pytest.mark.requires_llm
async def test_complete_search_workflow_with_real_llm():
    """Full integration test with real LLM and TUI."""
    async with PRTApp().run_test() as pilot:
        # Navigate to chat
        await pilot.press("c")
        await pilot.pause()

        # Type search query
        chat_input = pilot.app.screen.query_one("#chat-input")
        await pilot.press(*"show me tech contacts")
        await pilot.press("enter")

        # Wait for LLM (slow!)
        await pilot.pause(30)

        # Verify results appeared
        response = pilot.app.screen.query_one("#chat-response-content")
        assert "Found" in str(response.renderable)
        assert "[1]" in str(response.renderable)
```

### Run Command

```bash
# Run manually (slow!)
pytest -m e2e -m requires_llm

# Or run specific test
pytest tests/e2e/test_chat_screen_e2e.py::test_complete_search_workflow -v
```

### Exit Criteria
- ✅ Critical workflows work end-to-end
- ✅ No crashes or hangs
- ✅ UI updates correctly

**Note**: These tests are intentionally slow and should NOT run in regular CI. Use for:
- Major releases
- Debugging weird issues
- Validating big refactors

---

## Test Markers & Organization

### Pytest Markers

```python
# pytest.ini
[pytest]
markers =
    unit: Fast unit tests (< 1 second)
    integration: Integration tests with mocks (< 5 seconds)
    contract: LLM contract tests with real LLM (1-5 minutes)
    e2e: End-to-end tests (5-10 minutes)
    requires_llm: Requires real LLM connection
```

### Directory Structure

```
tests/
├── unit/
│   ├── conftest.py               # Unit test fixtures
│   ├── test_results_formatter.py # 20-30 tests
│   ├── test_context_manager.py   # 15-20 tests
│   └── test_selection_service.py # 10-15 tests
├── integration/
│   ├── conftest.py               # Mock LLM fixtures
│   ├── test_llm_bridge.py        # 30-40 tests
│   ├── test_chat_workflow.py     # 20-30 tests
│   └── test_permissions.py       # 10-15 tests
├── llm_contracts/
│   ├── promptfoo.yaml            # 60-80 test cases
│   ├── system_prompt.txt         # System prompt file
│   ├── baseline.json             # Baseline results
│   └── compare_results.py        # Comparison script
└── e2e/
    ├── conftest.py               # E2E fixtures
    └── test_chat_screen_e2e.py   # 5-10 tests
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Test Chat Screen

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
      - name: Install dependencies
        run: |
          python -m pip install -e .
          pip install pytest pytest-cov
      - name: Run unit tests
        run: pytest -m unit --cov --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
      - name: Install dependencies
        run: |
          python -m pip install -e .
          pip install pytest
      - name: Run integration tests
        run: pytest -m integration --maxfail=3

  llm-contract-tests:
    runs-on: ubuntu-latest
    # Only run weekly or on manual trigger
    if: github.event.schedule || github.event_name == 'workflow_dispatch'
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node
        uses: actions/setup-node@v3
      - name: Install Ollama
        run: curl -fsSL https://ollama.com/install.sh | sh
      - name: Pull model
        run: ollama pull llama3.2:3b  # Fast model for CI
      - name: Install promptfoo
        run: npm install -g promptfoo
      - name: Run contract tests
        run: |
          cd tests/llm_contracts
          npx promptfoo eval -c promptfoo.yaml -p ollama:llama3.2:3b
      - name: Check for regressions
        run: python tests/llm_contracts/compare_results.py
```

---

## Test Coverage Goals

| Component | Target Coverage | Test Layer |
|-----------|----------------|------------|
| ResultsFormatter | 95%+ | Unit |
| DisplayContext | 90%+ | Unit |
| ChatContextManager | 90%+ | Unit |
| SelectionService | 90%+ | Unit |
| LLMDatabaseBridge | 85%+ | Integration |
| SearchSelectActWorkflow | 80%+ | Integration |
| ChatScreen | 70%+ | Integration + E2E |
| LLM Intent Parsing | 95%+ | Contract |

**Overall target**: 85%+ code coverage for testable components

---

## Metrics to Track

### Quality Metrics
- **Intent accuracy**: % of queries correctly classified
- **Parameter accuracy**: % of parameters correctly extracted
- **JSON validity**: % of responses that are valid JSON
- **Hallucination rate**: % of responses with made-up data

### Performance Metrics
- **Test suite speed**: Time to run unit + integration tests
- **Token usage**: Tokens per query (minimal/adaptive/detailed)
- **Response time**: LLM response time (p50, p95, p99)

### Code Quality Metrics
- **Test coverage**: Line coverage for deterministic code
- **Test count**: Number of tests per component
- **Defect density**: Bugs per 1000 lines

---

## Testing Best Practices

### 1. Test Naming Convention

```python
# Good: Descriptive, action-oriented
def test_formatter_shows_selection_markers_for_selected_items():
    ...

# Bad: Vague
def test_formatter():
    ...
```

### 2. Arrange-Act-Assert Pattern

```python
def test_context_resolution():
    # Arrange
    context = ChatContextManager()
    context.update_display(results=[...])

    # Act
    db_ids = context.resolve_selection({'ids': [1, 2]})

    # Assert
    assert db_ids == [247, 89]
```

### 3. Use Fixtures for Common Setup

```python
@pytest.fixture
def populated_context():
    """Context with 10 contacts."""
    context = ChatContextManager()
    contacts = [fixture_contact() for _ in range(10)]
    context.update_display(...)
    return context
```

### 4. Test Error Paths

```python
def test_formatter_handles_empty_results():
    """Formatter shouldn't crash on empty list."""
    formatter = ResultsFormatter()
    result = formatter.render([], 'contacts', mode='list')
    assert "No results" in result or result == ""
```

### 5. Isolate External Dependencies

```python
# Good: Mock LLM
async def test_with_mock_llm(mock_llm):
    bridge = LLMDatabaseBridge(llm_service=mock_llm)
    ...

# Bad: Real LLM in integration test
async def test_with_real_llm():
    bridge = LLMDatabaseBridge(llm_service=OllamaLLM())  # Slow!
    ...
```

---

## Summary: Testing Philosophy

**Test the right things at the right layer:**

1. ⚡ **Unit tests** → Deterministic logic (formatters, context, selection)
2. ⚙️ **Integration tests** → Workflows and error handling (with mocks)
3. 🧪 **Contract tests** → LLM behavior and regressions (with promptfoo)
4. 🐢 **E2E tests** → Critical user journeys (sparingly, manually)

**Fast feedback loop:**
- Write test → implement → run unit tests (< 1s)
- Commit → run integration tests (< 5s)
- Merge → run contract tests (1-5m, CI)
- Release → run E2E tests (manual)

**Confidence without slowness:**
- 95% confidence from fast tests (unit + integration)
- 5% confidence from slow tests (contract + E2E)
- Total confidence: High, total time: Low

This strategy gives you the benefits of comprehensive testing without waiting 30 seconds for every test run!
