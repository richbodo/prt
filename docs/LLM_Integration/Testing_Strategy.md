# LLM Integration Testing Strategy

**Date:** October 10, 2025
**Status:** Phase 3 - Testing Infrastructure
**Focus:** Search contacts only (simple tool calling)

## Overview

This document defines a **three-layer testing strategy** for the simplified LLM integration, focusing exclusively on `search_contacts` tool calling. The strategy prioritizes reliability, debuggability, and fast feedback while building confidence in real LLM behavior.

## Core Principles

1. **Test real behavior, not mocks** - Use actual LLM calls for contract/integration tests
2. **Fast feedback loop** - Unit tests in seconds, contract tests in minutes
3. **Clear failure diagnosis** - Each test failure should point to exact problem
4. **Evidence-based expansion** - Only add tests for observed failure modes
5. **CI-friendly** - Tests must be deterministic and reliable in CI environment

## Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Integration Tests                                  │
│ • Full stack (DB + LLM + Tools)                            │
│ • Real contact counts and data                             │
│ • Validate complete user workflows                         │
│ • Run: Nightly / On-demand                                 │
│ • Time: 2-5 minutes                                        │
└─────────────────────────────────────────────────────────────┘
                            ▲
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Contract Tests (Promptfoo)                        │
│ • Real LLM calls with tool schemas                         │
│ • Validate tool selection and parameters                   │
│ • Test response quality                                    │
│ • Run: Every PR                                            │
│ • Time: 30-90 seconds                                      │
└─────────────────────────────────────────────────────────────┘
                            ▲
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Unit Tests (Pytest)                               │
│ • Mocked LLM responses                                     │
│ • Test orchestration logic                                 │
│ • Test tool execution and error handling                   │
│ • Run: Every commit                                        │
│ • Time: < 5 seconds                                        │
└─────────────────────────────────────────────────────────────┘
```

## Layer 1: Unit Tests (Python Pytest)

### Purpose
Test the orchestration layer, tool execution, and error handling **without making actual LLM API calls**.

### What We Test
- Tool registration and schema validation
- Tool execution with mocked results
- Error handling (network failures, invalid parameters, database errors)
- Response formatting and history management
- Conversation state management

### Example Tests

```python
# tests/unit/test_llm_orchestration.py

def test_search_contacts_tool_execution(mock_api):
    """Verify search_contacts tool executes correctly."""
    mock_api.search_contacts.return_value = [
        {"id": 1, "name": "Alice", "email": "alice@example.com"}
    ]

    llm = OllamaLLM(api=mock_api)
    result = llm.execute_tool("search_contacts", {"query": "Alice"})

    assert len(result) == 1
    assert result[0]["name"] == "Alice"
    mock_api.search_contacts.assert_called_once_with("Alice")

def test_tool_error_handling(mock_api):
    """Verify graceful handling of tool execution errors."""
    mock_api.search_contacts.side_effect = Exception("Database connection failed")

    llm = OllamaLLM(api=mock_api)
    response = llm.chat("Find Alice")

    assert "error" in response.lower()
    assert "unable to search" in response.lower()

def test_conversation_history_maintained():
    """Verify conversation history is maintained correctly."""
    llm = OllamaLLM()

    llm.chat("Hello")
    llm.chat("Find Alice")

    assert len(llm.conversation_history) == 4  # 2 user + 2 assistant
    assert llm.conversation_history[0]["role"] == "user"
    assert llm.conversation_history[1]["role"] == "assistant"
```

### Run Command
```bash
./prt_env/bin/pytest tests/unit/test_llm_*.py -v
```

### Success Criteria
- All tests pass in < 5 seconds
- 100% code coverage of orchestration logic
- Clear error messages on failure

---

## Layer 2: Contract Tests (Promptfoo)

### Purpose
Test the **LLM's ability to use tools correctly** with real API calls. Validate that the model:
1. Correctly decides when to use `search_contacts`
2. Extracts appropriate parameters from natural language
3. Formats responses appropriately

### What We Test
- Tool selection accuracy (does it pick search_contacts?)
- Parameter extraction (correct query strings)
- Response quality (answers the question)
- Edge cases (empty results, ambiguous queries)

### Architecture

```
User Query → System Prompt → LLM (Ollama) → Tool Call
                                              ↓
                                        Validate:
                                        • Correct tool?
                                        • Valid parameters?
                                        • Response quality?
```

### Example Configuration

```yaml
# tests/llm_contracts/promptfooconfig_search_only.yaml

description: "Contract tests for search_contacts tool calling"

prompts:
  - file://system_prompt_search_only.txt

providers:
  - id: ollama:llama3.2:3b
    config:
      tools:
        - name: search_contacts
          description: "Search contacts by name, email, phone, or tags"
          parameters:
            type: object
            properties:
              query:
                type: string
                description: "Natural language search query"
            required: []

tests:
  # Basic counting
  - description: "Count all contacts"
    vars:
      user_query: "How many contacts do I have?"
    assert:
      - type: javascript
        value: |
          // Check if tool was called
          const toolCalls = output.tool_calls || [];
          const searchCall = toolCalls.find(t => t.name === 'search_contacts');
          if (!searchCall) return { pass: false, reason: 'Did not call search_contacts' };

          // Parameter should be empty or null for "all contacts"
          const query = searchCall.parameters.query;
          if (query && query.trim() !== '') {
            return { pass: false, reason: `Expected empty query, got: "${query}"` };
          }

          return { pass: true };

  # Name search
  - description: "Search by name"
    vars:
      user_query: "Find contacts named Alice"
    assert:
      - type: javascript
        value: |
          const toolCalls = output.tool_calls || [];
          const searchCall = toolCalls.find(t => t.name === 'search_contacts');
          if (!searchCall) return { pass: false, reason: 'Did not call search_contacts' };

          const query = searchCall.parameters.query.toLowerCase();
          if (!query.includes('alice')) {
            return { pass: false, reason: `Query missing "alice": "${query}"` };
          }

          return { pass: true };

  # Email search
  - description: "Search by email"
    vars:
      user_query: "Who has the email alice@example.com?"
    assert:
      - type: javascript
        value: |
          const toolCalls = output.tool_calls || [];
          const searchCall = toolCalls.find(t => t.name === 'search_contacts');
          if (!searchCall) return { pass: false, reason: 'Did not call search_contacts' };

          const query = searchCall.parameters.query.toLowerCase();
          if (!query.includes('alice@example.com')) {
            return { pass: false, reason: `Query missing email: "${query}"` };
          }

          return { pass: true };

  # Conversational
  - description: "Handle conversational query"
    vars:
      user_query: "Can you help me find John's contact info?"
    assert:
      - type: javascript
        value: |
          const toolCalls = output.tool_calls || [];
          const searchCall = toolCalls.find(t => t.name === 'search_contacts');
          if (!searchCall) return { pass: false, reason: 'Did not call search_contacts' };

          const query = searchCall.parameters.query.toLowerCase();
          if (!query.includes('john')) {
            return { pass: false, reason: `Query missing "john": "${query}"` };
          }

          return { pass: true };

  # Edge case: Empty result handling
  - description: "Handle search with no results gracefully"
    vars:
      user_query: "Find contacts named Zaphod"
    assert:
      - type: javascript
        value: |
          const toolCalls = output.tool_calls || [];
          const searchCall = toolCalls.find(t => t.name === 'search_contacts');
          if (!searchCall) return { pass: false, reason: 'Did not call search_contacts' };

          // Just verify it called the tool - orchestration handles empty results
          return { pass: true };

  # Edge case: Ambiguous query
  - description: "Handle ambiguous query with reasonable interpretation"
    vars:
      user_query: "Show me everyone"
    assert:
      - type: javascript
        value: |
          const toolCalls = output.tool_calls || [];
          const searchCall = toolCalls.find(t => t.name === 'search_contacts');
          if (!searchCall) return { pass: false, reason: 'Did not call search_contacts' };

          // Empty query is reasonable for "everyone"
          return { pass: true };

  # Negative case: Non-search query
  - description: "Don't call search for greeting"
    vars:
      user_query: "Hello! How are you?"
    assert:
      - type: javascript
        value: |
          const toolCalls = output.tool_calls || [];
          const searchCall = toolCalls.find(t => t.name === 'search_contacts');
          if (searchCall) {
            return { pass: false, reason: 'Should not call search_contacts for greeting' };
          }
          return { pass: true };
```

### System Prompt (Simplified)

```
# tests/llm_contracts/system_prompt_search_only.txt

You are a helpful assistant that helps users search their personal contact database.

You have access to one tool:
- search_contacts: Search contacts by name, email, phone, or tags

When the user asks about contacts, use the search_contacts tool.
When the user asks general questions or greetings, respond conversationally without tools.

Examples:

User: "How many contacts do I have?"
→ Use search_contacts with empty query to get all contacts, then count them

User: "Find Alice"
→ Use search_contacts with query="Alice"

User: "Who has the email john@example.com?"
→ Use search_contacts with query="john@example.com"

User: "Hello!"
→ Respond conversationally, don't use tools

Be concise and helpful. If search returns no results, say so clearly.
```

### Run Commands

```bash
# Run all contract tests
npx promptfoo@latest eval -c tests/llm_contracts/promptfooconfig_search_only.yaml

# Run with specific model
npx promptfoo@latest eval -c tests/llm_contracts/promptfooconfig_search_only.yaml \
  --provider ollama:llama3.2:3b

# View results in browser
npx promptfoo@latest view
```

### Success Criteria
- 100% pass rate on tool selection (always calls search_contacts when appropriate)
- 95%+ pass rate on parameter extraction (correct query strings)
- No false positives (doesn't call search for greetings/general questions)
- Runs in < 90 seconds

### Common Failure Modes to Watch For

1. **Wrong tool selected** - LLM doesn't call search_contacts
2. **Missing parameters** - query field is empty when it shouldn't be
3. **Over-calling** - Calls search for non-search queries
4. **Poor parameter extraction** - Doesn't extract key terms from natural language

---

## Layer 3: Integration Tests (Full Stack)

### Purpose
Test the **complete user workflow** with real database, real LLM, and real tool execution. Validate that the system produces correct results end-to-end.

### What We Test
- Correct contact counts from real database
- Search results match database state
- Multi-turn conversations maintain context
- Error recovery (network failures, database issues)
- Performance (response time < 3 seconds for simple queries)

### Example Tests

```python
# tests/integration/test_llm_search_integration.py

import pytest
from prt_src.llm_ollama import OllamaLLM
from prt_src.api import PRTAPI

@pytest.fixture
def llm_with_real_db():
    """Create LLM instance with real test database."""
    api = PRTAPI()  # Uses test database
    llm = OllamaLLM(api=api)
    return llm, api

def test_count_all_contacts(llm_with_real_db):
    """Integration: Count all contacts matches database."""
    llm, api = llm_with_real_db

    # Get actual count from database
    all_contacts = api.list_all_contacts()
    expected_count = len(all_contacts)

    # Ask LLM
    response = llm.chat("How many contacts do I have in the database right now, please?")

    # Verify response mentions correct count
    assert str(expected_count) in response, \
        f"Expected count {expected_count} not found in response: {response}"

def test_search_by_name_accuracy(llm_with_real_db):
    """Integration: Search by name returns correct contacts."""
    llm, api = llm_with_real_db

    # Create test contact
    contact = api.create_contact(name="Zaphod Beeblebrox", email="zaphod@universe.com")

    # Search via LLM
    response = llm.chat("Find Zaphod")

    # Verify response contains contact info
    assert "Zaphod" in response
    assert "zaphod@universe.com" in response or "universe.com" in response

    # Cleanup
    api.delete_contact(contact.id)

def test_multi_turn_conversation(llm_with_real_db):
    """Integration: Multi-turn conversation maintains context."""
    llm, api = llm_with_real_db

    # Turn 1: Initial search
    response1 = llm.chat("Find contacts named Alice")
    assert "Alice" in response1

    # Turn 2: Follow-up (should maintain context)
    response2 = llm.chat("What's her email?")
    assert "@" in response2  # Should return email address

    # Verify history maintained
    assert len(llm.conversation_history) >= 4  # 2 turns = 4 messages

def test_empty_search_handling(llm_with_real_db):
    """Integration: Gracefully handle search with no results."""
    llm, api = llm_with_real_db

    response = llm.chat("Find contacts named XYZ_NONEXISTENT_NAME_12345")

    # Should indicate no results found
    assert any(phrase in response.lower() for phrase in [
        "no contacts", "not found", "no results", "couldn't find", "no matches"
    ])

def test_performance_simple_query(llm_with_real_db):
    """Integration: Simple query completes in < 3 seconds."""
    import time
    llm, api = llm_with_real_db

    start = time.time()
    response = llm.chat("How many contacts?")
    elapsed = time.time() - start

    assert elapsed < 3.0, f"Query took {elapsed:.2f}s, expected < 3.0s"
    assert len(response) > 0
```

### Run Commands

```bash
# Run all integration tests
./prt_env/bin/pytest tests/integration/test_llm_*.py -v

# Run with detailed output
./prt_env/bin/pytest tests/integration/test_llm_*.py -v -s

# Run specific test
./prt_env/bin/pytest tests/integration/test_llm_search_integration.py::test_count_all_contacts -v
```

### Success Criteria
- All tests pass with real database
- Response time < 3 seconds for simple queries
- No flaky failures (deterministic results)
- Clear error messages on failure

### Common Failure Modes to Watch For

1. **Incorrect counts** - LLM response doesn't match database state
2. **Missing information** - Search results incomplete
3. **Context loss** - Multi-turn conversations lose previous context
4. **Performance degradation** - Queries taking > 3 seconds

---

## CI/Development Workflow

### Development Workflow

```bash
# Step 1: Make changes to llm_ollama.py or related code
vim prt_src/llm_ollama.py

# Step 2: Run unit tests (fast feedback)
./prt_env/bin/pytest tests/unit/test_llm_*.py -v

# Step 3: If unit tests pass, run contract tests
npx promptfoo@latest eval -c tests/llm_contracts/promptfooconfig_search_only.yaml

# Step 4: If contract tests pass, run integration tests
./prt_env/bin/pytest tests/integration/test_llm_*.py -v

# Step 5: Commit and push
git add .
git commit -m "Improve search_contacts parameter extraction"
git push
```

### CI Pipeline (GitHub Actions)

```yaml
# .github/workflows/llm_tests.yml

name: LLM Integration Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run unit tests
        run: pytest tests/unit/test_llm_*.py -v

  contract-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install Ollama
        run: |
          curl https://ollama.ai/install.sh | sh
          ollama pull llama3.2:3b
      - name: Install promptfoo
        run: npm install -g promptfoo
      - name: Run contract tests
        run: promptfoo eval -c tests/llm_contracts/promptfooconfig_search_only.yaml

  integration-tests:
    runs-on: ubuntu-latest
    needs: contract-tests
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Install Ollama
        run: |
          curl https://ollama.ai/install.sh | sh
          ollama pull llama3.2:3b
      - name: Create test database
        run: python tests/fixtures.py
      - name: Run integration tests
        run: pytest tests/integration/test_llm_*.py -v
```

### When Tests Run

| Test Layer | Trigger | Time | Failures Block |
|------------|---------|------|----------------|
| Unit | Every commit | < 5s | Commit |
| Contract | Every PR | ~90s | Merge |
| Integration | Every PR + Nightly | ~3min | Merge |

---

## Success Metrics

### Per-Layer Metrics

**Layer 1 (Unit Tests)**
- Target: 100% pass rate
- Coverage: > 90% of orchestration code
- Speed: < 5 seconds total

**Layer 2 (Contract Tests)**
- Target: 100% pass rate on tool selection
- Target: 95%+ pass rate on parameter extraction
- Speed: < 90 seconds total
- Zero false positives on non-search queries

**Layer 3 (Integration Tests)**
- Target: 100% pass rate
- Performance: < 3 seconds per query
- Accuracy: 100% on count/search correctness

### Overall Health Indicators

**Green (Healthy):**
- All 3 layers passing
- No flaky tests
- Fast feedback (< 5 minutes total)

**Yellow (Degraded):**
- Contract tests showing < 90% pass rate
- Integration tests showing occasional failures
- Performance degrading (> 5 seconds per query)

**Red (Broken):**
- Unit tests failing
- Contract tests showing < 80% pass rate
- Integration tests showing consistent failures

---

## Debugging Failed Tests

### Unit Test Failures

```bash
# Run with verbose output
./prt_env/bin/pytest tests/unit/test_llm_orchestration.py -v -s

# Run specific test
./prt_env/bin/pytest tests/unit/test_llm_orchestration.py::test_search_contacts_tool_execution -v

# Run with debugger
./prt_env/bin/pytest tests/unit/test_llm_orchestration.py --pdb
```

**Common causes:**
- Mocking issues (incorrect mock setup)
- Logic errors in orchestration
- Missing error handling

### Contract Test Failures

```bash
# Run with detailed output
npx promptfoo@latest eval -c tests/llm_contracts/promptfooconfig_search_only.yaml --verbose

# View results in browser
npx promptfoo@latest view

# Test single case
npx promptfoo@latest eval -c tests/llm_contracts/promptfooconfig_search_only.yaml \
  --filter-description "Count all contacts"
```

**Common causes:**
- LLM not calling tool (prompt issue)
- Wrong parameters extracted (need better examples in prompt)
- Assertion logic too strict/loose

### Integration Test Failures

```bash
# Run with detailed output
./prt_env/bin/pytest tests/integration/test_llm_search_integration.py -v -s

# Check logs
tail -f prt_data/prt.log

# Test with real TUI
python -m prt_src.tui
# Navigate to chat screen and test manually
```

**Common causes:**
- Database state issues (fixtures not loaded)
- Network issues (Ollama not running)
- Timing issues (query too slow)
- LLM response format changed

---

## Expanding Test Coverage

### When to Add New Tests

**Add unit test when:**
- New orchestration logic added
- New error handling path
- Bug found in tool execution

**Add contract test when:**
- New query pattern observed (user reports)
- LLM consistently fails on specific phrasing
- New edge case discovered

**Add integration test when:**
- New user workflow added
- Performance regression detected
- Bug found in end-to-end flow

### Test Growth Strategy

**Phase 1 (Current): 20-30 tests total**
- 10 unit tests (orchestration, error handling)
- 15 contract tests (tool calling validation)
- 5 integration tests (core workflows)

**Phase 2 (After 1 month): 40-50 tests total**
- Add tests for observed failure modes
- Expand edge case coverage
- Add performance regression tests

**Phase 3 (After 3 months): 60-80 tests total**
- Comprehensive coverage of all query types
- Full error recovery testing
- Load testing (bulk operations)

---

## Next Steps

1. **Create promptfooconfig_search_only.yaml** - New configuration for tool-calling tests
2. **Create system_prompt_search_only.txt** - Simplified prompt for search-only functionality
3. **Write 15 initial contract tests** - Cover basic, edge, and negative cases
4. **Write 5 integration tests** - Count, search, multi-turn, empty results, performance
5. **Set up CI pipeline** - Run all 3 layers on PR
6. **Document first test run** - Baseline metrics and any issues found

## References

- **Existing tests:** `tests/llm_contracts/` (DEPRECATED intent-based architecture)
- **Promptfoo docs:** `EXTERNAL_DOCS/promptfoo/`
- **LLM code:** `prt_src/llm_ollama.py`
- **Manual testing guide:** `docs/LLM_Integration/Manual_Testing_Guide.md`
