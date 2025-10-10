# Phase 3: LLM Testing Infrastructure

**Date:** October 10, 2025
**Branch:** refactor-tui-issue-120
**Status:** 🚧 READY TO TEST

## What We Built

### The Goal
Create comprehensive, reliable testing infrastructure for the simplified LLM integration that focuses exclusively on `search_contacts` tool calling. The tests must:
1. Validate real LLM behavior (not mocks)
2. Run in both CI and development environments
3. Provide fast feedback (< 5 minutes total)
4. Be easy to debug when failures occur

### The Solution: Three-Layer Testing Strategy

We designed a pyramid approach with three distinct layers:

```
┌─────────────────────────────────────┐
│ Layer 3: Integration Tests         │  Real DB + LLM
│ • 5 tests                          │  Validate end-to-end
│ • ~3 minutes                       │
└─────────────────────────────────────┘
              ▲
┌─────────────────────────────────────┐
│ Layer 2: Contract Tests            │  Real LLM calls
│ • 15 tests (promptfoo)            │  Validate tool calling
│ • ~90 seconds                      │
└─────────────────────────────────────┘
              ▲
┌─────────────────────────────────────┐
│ Layer 1: Unit Tests                │  Mocked LLM
│ • 10 tests                         │  Test orchestration
│ • < 5 seconds                      │
└─────────────────────────────────────┘
```

## Files Created

### Documentation
1. **`Testing_Strategy.md`** - Comprehensive 500+ line testing guide covering:
   - Three-layer architecture with rationale
   - Example tests for each layer
   - CI/Development workflow
   - Debugging procedures
   - Success metrics and expansion strategy

### Contract Test Files (Promptfoo)
2. **`system_prompt_search_only.txt`** - Simplified system prompt for search-only functionality:
   - Clear tool description
   - Usage examples
   - Response guidelines
   - Replaces the DEPRECATED 312-line intent-based prompt

3. **`promptfooconfig_search_only.yaml`** - Promptfoo configuration with 15 comprehensive tests:
   - **Basic queries** (4 tests): Count, search by name/email/phone
   - **Conversational queries** (3 tests): Natural language variations
   - **Tag searches** (2 tests): Tag-based filtering, multi-criteria
   - **Edge cases** (3 tests): Short queries, special characters, ambiguous inputs
   - **Negative cases** (3 tests): Greetings, general questions (should NOT call tool)

## Test Coverage

### Layer 2 (Contract Tests) - What We Test

**15 tests covering:**

✅ **Tool Selection Accuracy**
- Does LLM call `search_contacts` when appropriate?
- Does LLM avoid calling tools for greetings/general questions?

✅ **Parameter Extraction**
- Correct extraction of names, emails, phones from natural language
- Handling of empty queries (for "all contacts")
- Multi-criteria queries (e.g., "work contacts named John")

✅ **Edge Cases**
- Very short queries ("Find Jo")
- Special characters ("Find O'Brien")
- Ambiguous queries ("Show me everyone")

✅ **Negative Cases**
- "Hello! How are you?" → Should respond conversationally, NOT call tool
- "What can you help me with?" → Should describe capabilities, NOT call tool
- "Thank you!" → Should acknowledge, NOT call tool

### Example Test: Count All Contacts

```yaml
- description: "Count all contacts - should call search_contacts with empty query"
  vars:
    user_query: "How many contacts do I have?"
  assert:
    - type: javascript
      value: |
        // Verify tool was called
        const toolCalls = output.tool_calls || [];
        const searchCall = toolCalls.find(t => t.name === 'search_contacts');

        if (!searchCall) {
          return { pass: false, reason: 'Did not call search_contacts' };
        }

        // Verify query is empty (to get all contacts)
        const query = searchCall.parameters.query;
        if (query && query.trim() !== '') {
          return { pass: false, reason: `Expected empty query, got: "${query}"` };
        }

        return { pass: true };
```

## Running the Tests

### Prerequisites

```bash
# 1. Ensure Ollama is running with llama3.2:3b
ollama list | grep llama3.2:3b

# If not installed:
ollama pull llama3.2:3b

# 2. Ensure Node.js is available (for promptfoo)
node --version  # Should be v18+

# 3. Activate virtual environment
source ./init.sh
```

### Layer 2: Contract Tests (Start Here!)

```bash
# Run all 15 contract tests
npx promptfoo@latest eval -c tests/llm_contracts/promptfooconfig_search_only.yaml

# Expected output:
# ✓ Count all contacts - should call search_contacts with empty query
# ✓ Search by name - should extract name from query
# ✓ Search by email - should extract email address
# ... (15 tests total)
#
# 15/15 passed (100%)
# Time: ~90 seconds

# View detailed results in browser
npx promptfoo@latest view
```

### Run Specific Test

```bash
# Test just one case for debugging
npx promptfoo@latest eval \
  -c tests/llm_contracts/promptfooconfig_search_only.yaml \
  --filter-description "Count all contacts"
```

### Debugging Failed Tests

```bash
# Run with verbose output
npx promptfoo@latest eval \
  -c tests/llm_contracts/promptfooconfig_search_only.yaml \
  --verbose

# Check what the LLM actually returned
cat tests/llm_contracts/promptfoo_results_search_only.json | jq '.results[0]'
```

## Expected Results (First Run)

### Success Criteria

**Green (All tests pass):**
- ✅ 15/15 tests passing
- ✅ 100% tool selection accuracy
- ✅ No false positives (tools called for greetings)
- ✅ Complete in < 90 seconds

**Yellow (Some failures expected on first run):**
- ⚠️ 12-14/15 tests passing (80-93%)
- ⚠️ Common failure modes:
  - LLM calls tool for greetings (over-calling)
  - LLM doesn't extract all parameters (under-specifying)
  - LLM formats query unexpectedly

**Red (System broken):**
- ❌ < 12/15 tests passing (< 80%)
- ❌ LLM never calls tools correctly
- ❌ System errors (Ollama not running, config issues)

### What to Do with Failures

**If 12-14/15 passing (Yellow):**
1. Run tests 3 times to check for flakiness
2. Document consistent failures
3. Analyze if system prompt needs refinement
4. Consider if test assertions are too strict

**If < 12/15 passing (Red):**
1. Check Ollama is running: `ollama list`
2. Check model is correct: `ollama run llama3.2:3b "test"`
3. Check logs: `tail -f prt_data/prt.log`
4. Check promptfoo config syntax
5. Test manually via TUI chat screen

## Next Steps After First Run

### 1. Document Baseline
```bash
# Run tests and save results
npx promptfoo@latest eval \
  -c tests/llm_contracts/promptfooconfig_search_only.yaml \
  > test_results_baseline.txt

# Document in docs/LLM_Integration/Phase3_Results.md:
# - Pass rate (e.g., 13/15 = 87%)
# - Failure modes observed
# - Time to run
# - Any surprises
```

### 2. Create Layer 1 (Unit Tests)
Once contract tests establish baseline, create unit tests for fast feedback:
```python
# tests/unit/test_llm_orchestration.py
def test_search_contacts_tool_execution(mock_api):
    """Verify search_contacts tool executes correctly."""
    # Test orchestration logic without real LLM calls
```

### 3. Create Layer 3 (Integration Tests)
After unit tests prove orchestration works, test end-to-end:
```python
# tests/integration/test_llm_search_integration.py
def test_count_all_contacts(llm_with_real_db):
    """Integration: Count all contacts matches database."""
    # Test with real database + real LLM + real tool
```

### 4. Set Up CI Pipeline
Once all 3 layers pass locally, add to GitHub Actions:
```yaml
# .github/workflows/llm_tests.yml
jobs:
  contract-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Install Ollama
        run: curl https://ollama.ai/install.sh | sh
      - name: Pull model
        run: ollama pull llama3.2:3b
      - name: Run contract tests
        run: promptfoo eval -c tests/llm_contracts/promptfooconfig_search_only.yaml
```

## Key Design Decisions

### 1. Why Promptfoo for Contract Tests?
- **Real LLM behavior**: Tests actual model responses, not mocks
- **Flexible assertions**: JavaScript for complex validation logic
- **Multiple models**: Easy to test llama3.2:3b, mistral, etc.
- **Built-in UI**: Visual results browser for debugging

### 2. Why Start with Contract Tests (Layer 2)?
- **Fastest path to value**: Proves LLM can actually use tools correctly
- **Catches fundamental issues early**: If LLM can't call tools, nothing else matters
- **Informs other layers**: Failure modes guide unit/integration test design

### 3. Why Only 15 Tests Initially?
- **Focus on coverage, not quantity**: Cover all major patterns and edge cases
- **Fast feedback**: 15 tests run in ~90 seconds
- **Easy to debug**: Small enough to inspect each test manually
- **Evidence-based growth**: Add tests for observed failures, not speculation

### 4. Why Tool Calling, Not Intent Classification?
- **Simpler architecture**: Leverage Ollama's native tool calling
- **Less custom code**: No JSON parsing, no intent routing
- **More reliable**: Model trained for tool calling, not custom JSON schema
- **Easier testing**: Validate tool calls directly, not intermediate JSON

## Architecture Evolution

### What We Deprecated
```
OLD (Intent-Based):
User → LLM → JSON Intent → Parser → Router → Tool → Response
       312-line prompt   Custom      Custom
       6 intent types    validation  routing
```

### What We Built
```
NEW (Tool-Calling):
User → LLM → Tool Call → Tool → Response
       Simple prompt  Native
       1 tool only    Ollama
```

**Result:**
- **Complexity:** 7 phases (125-169 hours) → 3 phases (44-60 hours) ✅
- **Code:** Custom intent system → Native tool calling ✅
- **Tests:** 45 intent tests (deprecated) → 15 tool tests (active) ✅

## Lessons Learned (So Far)

### 1. Start Simple, Expand Based on Evidence
- We're testing 1 tool, not 15 tools
- We're testing 15 scenarios, not 100 scenarios
- We'll add more based on what actually fails

### 2. Test Real Behavior, Not Mocks
- Contract tests use real LLM calls
- Integration tests use real database
- This catches issues mocks would miss

### 3. Fast Feedback Wins
- Contract tests in 90 seconds (fast enough for PR workflow)
- Unit tests in 5 seconds (fast enough for every commit)
- Integration tests in 3 minutes (fast enough for nightly)

### 4. Clear Failure Messages Are Critical
Example assertion:
```javascript
return {
  pass: false,
  reason: `Query should contain "alice", got: "${searchCall.parameters.query}"`
};
```
This tells you EXACTLY what went wrong, not just "test failed"

## Success Metrics

**Short-term (Next Week):**
- [ ] Run contract tests successfully (12+/15 passing)
- [ ] Document baseline pass rate and failure modes
- [ ] Create 5 unit tests for orchestration layer
- [ ] Create 3 integration tests for end-to-end workflows

**Medium-term (Next Month):**
- [ ] 100% pass rate on contract tests
- [ ] All 3 layers running in CI
- [ ] < 5 minutes total test time
- [ ] Zero flaky tests

**Long-term (Next Quarter):**
- [ ] 60-80 total tests across all layers
- [ ] Performance regression tests
- [ ] Multi-turn conversation tests
- [ ] Load testing (1000+ contacts)

---

## References

- **Testing Strategy:** `docs/LLM_Integration/Testing_Strategy.md` (comprehensive guide)
- **System Prompt:** `tests/llm_contracts/system_prompt_search_only.txt` (what LLM sees)
- **Test Config:** `tests/llm_contracts/promptfooconfig_search_only.yaml` (15 tests)
- **LLM Code:** `prt_src/llm_ollama.py` (orchestration layer)
- **Manual Tests:** `docs/LLM_Integration/Manual_Testing_Guide.md` (human testing)

---

## Ready to Run?

```bash
# Quick start:
ollama list | grep llama3.2:3b  # Verify model available
npx promptfoo@latest eval -c tests/llm_contracts/promptfooconfig_search_only.yaml
npx promptfoo@latest view  # View results in browser

# Report back:
# - Pass rate (X/15)
# - Time to run
# - Any failures
# - Any surprises
```

**Status:** ✅ Phase 3 infrastructure complete - Ready for first test run!
**Time spent:** ~90 minutes (research, design, documentation, implementation)
**Next:** Run contract tests and document baseline results
